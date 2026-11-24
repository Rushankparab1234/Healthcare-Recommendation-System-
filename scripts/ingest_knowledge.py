import argparse
import json
import sys
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.services.knowledge import (
    SOURCE_PATH,
    ingest_html_document,
    ingest_local_sources,
)

parser = argparse.ArgumentParser(
    description="Index curated source text or refresh from its linked source pages."
)
parser.add_argument(
    "--refresh",
    action="store_true",
    help="Download the registered public source pages before indexing.",
)
args = parser.parse_args()

if args.refresh:
    documents = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    refreshed = []
    for document in documents:
        request = Request(
            document["source_url"],
            headers={"User-Agent": "HealthWiseAI-EducationalKnowledgeIngest/1.0"},
        )
        with urlopen(request, timeout=20) as response:
            html = response.read().decode(response.headers.get_content_charset() or "utf-8", errors="replace")
        refreshed.append(ingest_html_document(document, html))
    SOURCE_PATH.write_text(json.dumps(refreshed, ensure_ascii=False, indent=2), encoding="utf-8")

index = ingest_local_sources()
print(f"Indexed {len(index['documents'])} sourced documents into data/knowledge_base/index.json")
