import uuid

from app.main import app
from app.services.knowledge import (
    build_index,
    extract_html_text,
    ingest_html_document,
    retrieve,
)
from fastapi.testclient import TestClient

client = TestClient(app)


def _token() -> str:
    response = client.post("/api/v1/auth/register", json={
        "email": f"knowledge.{uuid.uuid4()}@example.com",
        "full_name": "Knowledge Test",
        "password": "A-long-secure-password-123",
    })
    return response.json()["access_token"]


def test_knowledge_search_and_detail_return_cited_source():
    response = client.get("/api/v1/knowledge", params={"search": "cough"})
    assert response.status_code == 200
    assert response.json()[0]["id"] == "medlineplus-cough"
    article = client.get("/api/v1/knowledge/medlineplus-cough")
    assert article.status_code == 200
    assert article.json()["source_url"] == "https://medlineplus.gov/cough.html"
    assert "acute coughs" in article.json()["content"].lower()


def test_assistant_retrieves_source_and_declines_out_of_scope_question():
    headers = {"Authorization": f"Bearer {_token()}"}
    grounded = client.post("/api/v1/assistant", headers=headers, json={"question": "How long can an acute cough last?"})
    assert grounded.status_code == 200
    assert grounded.json()["sources"][0]["url"] == "https://medlineplus.gov/cough.html"
    assert grounded.json()["retrieval_status"] == "sources_retrieved"

    specific = client.post(
        "/api/v1/assistant",
        headers=headers,
        json={"question": "What does MedlinePlus say about cough?"},
    )
    assert specific.status_code == 200
    assert [source["title"] for source in specific.json()["sources"]] == ["Cough"]

    unsupported = client.post("/api/v1/assistant", headers=headers, json={"question": "What is the capital of France?"})
    assert unsupported.status_code == 200
    assert unsupported.json()["sources"] == []
    assert unsupported.json()["retrieval_status"] == "no_relevant_source"


def test_ingestion_extracts_html_and_chunks_documents():
    assert extract_html_text("<nav>menu</nav><main><p>Health text</p></main>") == "Health text"
    extracted = ingest_html_document(
        {"source_url": "https://example.org"},
        "<main><p>Health information from a source page with enough readable text.</p>"
        "<p>This second sentence makes this extracted source useful.</p></main>",
    )
    assert "Health information" in extracted["content"]
    index = build_index([{
        "id": "test",
        "title": "Test",
        "category": "Test",
        "source_name": "Test source",
        "source_url": "https://example.org",
        "content": "one two three four",
    }])
    assert index["documents"][0]["chunks"] == ["one two three four"]
    assert retrieve("cough information")


def test_assistant_preserves_emergency_override_without_rag():
    headers = {"Authorization": f"Bearer {_token()}"}
    response = client.post("/api/v1/assistant", headers=headers, json={"question": "I have crushing chest pain"})
    assert response.status_code == 200
    assert response.json()["retrieval_status"] == "emergency-safety"
