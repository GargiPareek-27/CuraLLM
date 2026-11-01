import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.providers.base import (
    GenerationRequest,
    ProviderBadResponse,
    ProviderTimeout,
    ProviderUnavailable,
)
from app.providers.mock import MockProvider


class FailingProvider:
    name = "failing"

    def __init__(self, error):
        self.error = error

    async def generate(self, request: GenerationRequest):
        raise self.error

    async def health(self):
        return False


def test_health_ok_with_mock():
    client = TestClient(create_app(MockProvider()))
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "provider": "mock"}


def test_generate_returns_labelled_mock_response():
    client = TestClient(create_app(MockProvider()))
    response = client.post("/v1/generate", json={"prompt": "hello"})
    assert response.status_code == 200
    body = response.json()
    assert body["is_mock"] is True
    assert "DEMO MODE" in body["text"]
    assert body["usage"] is None


@pytest.mark.parametrize(
    "payload",
    [
        {"prompt": ""},
        {"prompt": "x" * 8001},
        {"prompt": "hello", "max_tokens": 0},
        {"prompt": "hello", "max_tokens": 5000},
    ],
)
def test_generate_rejects_invalid_requests(payload):
    client = TestClient(create_app(MockProvider()))
    assert client.post("/v1/generate", json=payload).status_code == 422


@pytest.mark.parametrize(
    "error,status",
    [
        (ProviderTimeout("secret detail"), 504),
        (ProviderUnavailable("secret detail"), 503),
        (ProviderBadResponse("secret detail"), 502),
    ],
)
def test_provider_errors_map_to_http_status_without_leaking_detail(error, status):
    client = TestClient(create_app(FailingProvider(error)))
    response = client.post("/v1/generate", json={"prompt": "hello"})
    assert response.status_code == status
    assert "secret detail" not in response.text


def test_unhealthy_provider_makes_health_fail():
    client = TestClient(create_app(FailingProvider(ProviderUnavailable("x"))))
    assert client.get("/health").status_code == 503
