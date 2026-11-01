import pytest

from app.request_id import resolve_request_id
from app.retry import backoff_delay


def test_backoff_grows_and_is_capped():
    assert backoff_delay(0) == pytest.approx(0.2)
    assert backoff_delay(1) == pytest.approx(0.4)
    assert backoff_delay(2) == pytest.approx(0.8)
    assert backoff_delay(20) == pytest.approx(2.0)


def test_backoff_rejects_negative_attempt():
    with pytest.raises(ValueError):
        backoff_delay(-1)


def test_request_id_rules():
    assert resolve_request_id("abc-123") == "abc-123"
    assert len(resolve_request_id(None)) == 32
    assert resolve_request_id("has space") != "has space"
    assert resolve_request_id("x" * 65) != "x" * 65
