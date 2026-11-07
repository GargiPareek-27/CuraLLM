import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.deps import get_searcher
from app.main import create_app

ROW = {
    "source_id": "medlineplus_health_topics",
    "external_id": "9001",
    "chunk_index": 0,
    "chunk_id": 1,
    "document_id": 1,
    "title": "Sample Topic: Zebra Fever",
    "url": "https://medlineplus.gov/zebrafever.html",
    "language": "English",
    "corpus_version": "2026-01-01",
    "license": "U.S. federal government work, not copyrighted (public domain)",
    "attribution": "Courtesy of MedlinePlus from the National Library of Medicine",
    "text": "Zebra fever is an imaginary condition used only to test software.",
    "score": 0.42,
}


def client_with(searcher):
    app = create_app()
    app.dependency_overrides[get_searcher] = lambda: searcher
    return TestClient(app)


def test_results_are_cited_passages():
    calls = []

    def searcher(query, limit):
        calls.append((query, limit))
        return [ROW]

    response = client_with(searcher).post("/api/v1/search", json={"query": "  zebra fever  ", "limit": 3})
    assert response.status_code == 200
    body = response.json()
    assert calls == [("zebra fever", 3)]
    assert body["retrieval_method"] == "postgres_full_text"
    passage = body["results"][0]
    assert passage["passage_id"] == "medlineplus_health_topics:9001:0"
    assert passage["source_url"] == "https://medlineplus.gov/zebrafever.html"
    assert passage["attribution"].startswith("Courtesy of MedlinePlus")
    assert passage["lexical_score"] == pytest.approx(0.42)
    assert body["request_id"] == response.headers["X-Request-ID"]


def test_no_matches_is_an_empty_list_not_an_error():
    response = client_with(lambda q, n: []).post("/api/v1/search", json={"query": "nothing here"})
    assert response.status_code == 200
    assert response.json()["results"] == []


@pytest.mark.parametrize(
    "payload",
    [
        {"query": ""},
        {"query": "   "},
        {"query": "x" * 501},
        {"query": "ok", "limit": 0},
        {"query": "ok", "limit": 11},
        {},
    ],
)
def test_invalid_requests_are_rejected(payload):
    response = client_with(lambda q, n: [ROW]).post("/api/v1/search", json=payload)
    assert response.status_code == 422


def test_database_errors_become_503_without_details():
    def failing(query, limit):
        raise OperationalError("SELECT secret", {}, Exception("secret detail"))

    response = client_with(failing).post("/api/v1/search", json={"query": "fever"})
    assert response.status_code == 503
    assert "secret" not in response.text
