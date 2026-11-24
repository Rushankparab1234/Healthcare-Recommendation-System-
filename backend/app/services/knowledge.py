import json
import math
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
SOURCE_PATH = ROOT / "data" / "knowledge_base" / "source_documents.json"
INDEX_PATH = ROOT / "data" / "knowledge_base" / "index.json"
MIN_RETRIEVAL_SCORE = 0.12
STOP_WORDS = {
    "about", "after", "and", "are", "can", "does", "for", "from", "have", "help",
    "how", "is", "it", "me", "my", "of", "on", "or", "the", "this", "to", "what",
    "when", "with", "you", "medlineplus",
}


def _tokens(text: str) -> list[str]:
    return [
        token
        for token in re.findall(r"[a-z0-9]+", text.casefold())
        if len(token) > 1 and token not in STOP_WORDS
    ]


def extract_html_text(html: str) -> str:
    from html.parser import HTMLParser

    class TextExtractor(HTMLParser):
        def __init__(self) -> None:
            super().__init__(convert_charrefs=True)
            self.parts: list[str] = []
            self.skip_depth = 0

        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            if tag in {"script", "style", "nav", "footer", "header"}:
                self.skip_depth += 1

        def handle_endtag(self, tag: str) -> None:
            if tag in {"script", "style", "nav", "footer", "header"} and self.skip_depth:
                self.skip_depth -= 1

        def handle_data(self, data: str) -> None:
            if self.skip_depth == 0:
                normalized = " ".join(data.split())
                if normalized:
                    self.parts.append(normalized)

    parser = TextExtractor()
    parser.feed(html)
    return " ".join(parser.parts)


def chunk_text(text: str, chunk_size: int = 100) -> list[str]:
    words = text.split()
    return [
        " ".join(words[index:index + chunk_size])
        for index in range(0, len(words), chunk_size)
    ] or [""]


def build_index(documents: list[dict[str, Any]]) -> dict[str, Any]:
    indexed = []
    for document in documents:
        content = str(document.get("content", "")).strip()
        if not content:
            raise ValueError(f"Knowledge document {document.get('id')} has no content")
        indexed.append({
            **document,
            "chunks": chunk_text(content),
        })
    return {"version": 1, "documents": indexed}


def ingest_html_document(document: dict[str, Any], html: str) -> dict[str, Any]:
    extracted = extract_html_text(html)
    if len(extracted) < 80:
        raise ValueError(f"Source page {document.get('source_url')} yielded too little readable text")
    return {**document, "content": extracted}


def ingest_local_sources() -> dict[str, Any]:
    documents = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    index = build_index(documents)
    INDEX_PATH.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    return index


def load_index() -> dict[str, Any]:
    if not INDEX_PATH.exists():
        return ingest_local_sources()
    index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    if not isinstance(index.get("documents"), list):
        raise ValueError("Knowledge index has an invalid document collection")
    return index


def _score(query_tokens: list[str], document: dict[str, Any], document_frequency: dict[str, int],
           document_count: int) -> float:
    content = f"{document['title']} {document['category']} {document['content']}"
    tokens = _tokens(content)
    if not tokens or not query_tokens:
        return 0.0
    frequencies = {token: tokens.count(token) for token in set(tokens)}
    query_weights = {
        token: math.log(1 + document_count / (1 + document_frequency.get(token, 0)))
        for token in set(query_tokens)
    }
    numerator = sum(
        weight * (1 + math.log(frequencies[token]))
        for token, weight in query_weights.items()
        if token in frequencies
    )
    denominator = sum(query_weights.values())
    return numerator / denominator if denominator else 0.0


def list_articles(search: str | None = None, category: str | None = None) -> list[dict[str, Any]]:
    documents = load_index()["documents"]
    query_tokens = _tokens(search or "")
    frequencies: dict[str, int] = {}
    for document in documents:
        for token in set(_tokens(f"{document['title']} {document['category']} {document['content']}")):
            frequencies[token] = frequencies.get(token, 0) + 1
    results = []
    for document in documents:
        if category and document["category"].casefold() != category.casefold():
            continue
        score = _score(query_tokens, document, frequencies, len(documents)) if query_tokens else 0.0
        if query_tokens and score == 0:
            continue
        results.append({
            key: document[key]
            for key in ("id", "title", "category", "source_name", "source_url", "content", "reviewed_at")
        } | {"relevance": round(score, 4)})
    if query_tokens:
        results.sort(key=lambda item: (-item["relevance"], item["title"]))
    else:
        results.sort(key=lambda item: item["title"])
    return results


def get_article(article_id: str) -> dict[str, Any] | None:
    return next((article for article in list_articles() if article["id"] == article_id), None)


def retrieve(question: str, limit: int = 3) -> list[dict[str, Any]]:
    matches = list_articles(search=question)
    return [
        match for match in matches
        if match["relevance"] >= MIN_RETRIEVAL_SCORE
    ][:limit]


def answer_from_sources(question: str) -> dict[str, Any]:
    sources = retrieve(question)
    if not sources:
        return {
            "answer": (
                "I could not find a sufficiently relevant source in the HealthWise knowledge collection. "
                "I cannot answer this from the available material. Please consult a licensed healthcare professional."
            ),
            "sources": [],
            "retrieval_status": "no_relevant_source",
            "generation": "extractive",
        }
    cited_passages = [
        f"[{index}] {source['content']}"
        for index, source in enumerate(sources, start=1)
    ]
    citations = [
        {
            "id": source["id"],
            "title": source["title"],
            "source": source["source_name"],
            "url": source["source_url"],
            "relevance": source["relevance"],
        }
        for source in sources
    ]
    return {
        "answer": "Relevant general information from the retrieved source(s):\n\n" + "\n\n".join(cited_passages),
        "sources": citations,
        "retrieval_status": "sources_retrieved",
        "generation": "extractive",
    }


def related_articles(article_id: str, limit: int = 3) -> list[dict[str, Any]]:
    article = get_article(article_id)
    if article is None:
        return []
    related = list_articles(search=f"{article['title']} {article['content']}")
    return [item for item in related if item["id"] != article_id][:limit]
