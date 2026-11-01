import asyncio

import httpx
import pytest

from app import inference_client as ic
from app.inference_client import (
    InferenceBadResponse,
    InferenceClient,
    InferenceTimeout,
    InferenceUnavailable,
)

GOOD = {
    "text": "[DEMO MODE] hi",
    "model_id": "curallm-mock",
    "model_revision": "mock-1",
    "is_mock": True,
}


def run(coro):
    return asyncio.run(coro)


def make_client(handler, max_retries=2):
    return InferenceClient(
        base_url="http://inference.test",
        connect_timeout=1,
        read_timeout=1,
        max_retries=max_retries,
        max_concurrency=2,
        transport=httpx.MockTransport(handler),
    )


@pytest.fixture(autouse=True)
def no_backoff(monkeypatch):
    monkeypatch.setattr(ic, "backoff_delay", lambda attempt: 0)


def test_success_parses_result():
    client = make_client(lambda request: httpx.Response(200, json=GOOD))
    result = run(client.generate("hello"))
    assert result.model_id == "curallm-mock"
    assert result.is_mock is True


@pytest.mark.parametrize(
    "status,error",
    [
        (503, InferenceUnavailable),
        (504, InferenceTimeout),
        (500, InferenceBadResponse),
        (422, InferenceBadResponse),
    ],
)
def test_error_statuses_map_to_typed_errors(status, error):
    client = make_client(lambda request: httpx.Response(status, json={"detail": "x"}))
    with pytest.raises(error):
        run(client.generate("hello"))


def test_invalid_json_is_a_bad_response():
    client = make_client(lambda request: httpx.Response(200, content=b"not json"))
    with pytest.raises(InferenceBadResponse):
        run(client.generate("hello"))


def test_missing_field_is_a_bad_response():
    incomplete = {k: v for k, v in GOOD.items() if k != "model_id"}
    client = make_client(lambda request: httpx.Response(200, json=incomplete))
    with pytest.raises(InferenceBadResponse):
        run(client.generate("hello"))


def test_wrong_field_type_is_a_bad_response():
    wrong = {**GOOD, "is_mock": "yes"}
    client = make_client(lambda request: httpx.Response(200, json=wrong))
    with pytest.raises(InferenceBadResponse):
        run(client.generate("hello"))


def test_connect_errors_are_retried_then_reported_unavailable():
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        raise httpx.ConnectError("boom")

    client = make_client(handler, max_retries=2)
    with pytest.raises(InferenceUnavailable):
        run(client.generate("hello"))
    assert calls["n"] == 3  # first try plus two retries


def test_connect_error_then_success_recovers():
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        if calls["n"] == 1:
            raise httpx.ConnectError("boom")
        return httpx.Response(200, json=GOOD)

    client = make_client(handler, max_retries=2)
    assert run(client.generate("hello")).model_id == "curallm-mock"
    assert calls["n"] == 2


def test_read_timeout_is_not_retried():
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        raise httpx.ReadTimeout("slow")

    client = make_client(handler, max_retries=2)
    with pytest.raises(InferenceTimeout):
        run(client.generate("hello"))
    assert calls["n"] == 1


def test_health_reflects_status_and_transport_errors():
    assert run(make_client(lambda r: httpx.Response(200, json={})).health()) is True
    assert run(make_client(lambda r: httpx.Response(503, json={})).health()) is False

    def refuse(request):
        raise httpx.ConnectError("boom")

    assert run(make_client(refuse).health()) is False
