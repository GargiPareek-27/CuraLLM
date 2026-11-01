import pytest
from pydantic import ValidationError

from app.config import Settings
from app.inference_client import (
    InferenceBadResponse,
    InferenceResult,
    InferenceTimeout,
    InferenceUnavailable,
)
from tests.conftest import FakeInferenceClient

GOOD_RESULT = InferenceResult(
    text="[DEMO MODE] hello", model_id="curallm-mock", model_revision="mock-1", is_mock=True
)


def test_health_is_ok(make_client):
    client = make_client(FakeInferenceClient(result=GOOD_RESULT))
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_request_id_is_generated_and_returned(make_client):
    client = make_client(FakeInferenceClient(result=GOOD_RESULT))
    assert client.get("/health").headers["X-Request-ID"]


def test_valid_request_id_is_echoed_and_unsafe_one_is_replaced(make_client):
    client = make_client(FakeInferenceClient(result=GOOD_RESULT))
    assert client.get("/health", headers={"X-Request-ID": "abc-123"}).headers["X-Request-ID"] == "abc-123"
    replaced = client.get("/health", headers={"X-Request-ID": "bad id with spaces"})
    assert replaced.headers["X-Request-ID"] != "bad id with spaces"


def test_chat_returns_labelled_demo_response(make_client):
    client = make_client(FakeInferenceClient(result=GOOD_RESULT))
    response = client.post("/api/v1/chat", json={"message": "What is hypertension?"})
    assert response.status_code == 200
    body = response.json()
    assert body["is_demo"] is True
    assert body["citations"] == []
    assert body["safety_status"] == "not_evaluated"
    assert body["professional_review_recommended"] is True


@pytest.mark.parametrize("message", ["", "   ", "x" * 4001])
def test_chat_rejects_invalid_messages(make_client, message):
    client = make_client(FakeInferenceClient(result=GOOD_RESULT))
    assert client.post("/api/v1/chat", json={"message": message}).status_code == 422


@pytest.mark.parametrize(
    "error,status",
    [
        (InferenceTimeout("secret detail"), 504),
        (InferenceUnavailable("secret detail"), 503),
        (InferenceBadResponse("secret detail"), 502),
    ],
)
def test_inference_errors_map_to_status_without_leaking_detail(make_client, error, status):
    client = make_client(FakeInferenceClient(error=error))
    response = client.post("/api/v1/chat", json={"message": "hello"})
    assert response.status_code == status
    assert "secret detail" not in response.text


def test_ready_ok_when_database_and_inference_are_up(make_client, monkeypatch):
    monkeypatch.setattr(
        "app.routers.health.check_database",
        lambda: {"database": "ok", "pgvector": "installed"},
    )
    client = make_client(FakeInferenceClient(result=GOOD_RESULT))
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_ready_is_503_when_inference_is_down(make_client, monkeypatch):
    monkeypatch.setattr(
        "app.routers.health.check_database",
        lambda: {"database": "ok", "pgvector": "installed"},
    )
    client = make_client(FakeInferenceClient(healthy=False))
    response = client.get("/ready")
    assert response.status_code == 503
    assert response.json()["inference"] == "unavailable"


def test_ready_is_503_when_database_is_down(make_client, monkeypatch):
    monkeypatch.setattr(
        "app.routers.health.check_database",
        lambda: {"database": "error", "detail": "OperationalError"},
    )
    client = make_client(FakeInferenceClient(result=GOOD_RESULT))
    assert client.get("/ready").status_code == 503


def test_wildcard_cors_origin_is_rejected():
    with pytest.raises(ValidationError):
        Settings(database_url="postgresql+psycopg://u:p@h/d", cors_origins="*")
