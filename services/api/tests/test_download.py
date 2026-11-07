import httpx
import pytest

from app.ingestion.medlineplus import download_xml

URL = "https://medlineplus.gov/xml/mplus_topics_2026-11-03.xml"


def test_download_writes_the_file(tmp_path):
    transport = httpx.MockTransport(lambda request: httpx.Response(200, content=b"<x/>"))
    destination = tmp_path / "topics.xml"
    assert download_xml(URL, destination, transport=transport) == 4
    assert destination.read_bytes() == b"<x/>"


def test_non_200_is_an_error(tmp_path):
    transport = httpx.MockTransport(lambda request: httpx.Response(404))
    with pytest.raises(RuntimeError, match="HTTP 404"):
        download_xml(URL, tmp_path / "t.xml", transport=transport)


def test_oversize_download_is_stopped(tmp_path):
    transport = httpx.MockTransport(lambda request: httpx.Response(200, content=b"x" * 100))
    with pytest.raises(RuntimeError, match="size limit"):
        download_xml(URL, tmp_path / "t.xml", transport=transport, max_bytes=50)


def test_redirects_are_not_followed(tmp_path):
    calls = []

    def handler(request):
        calls.append(str(request.url))
        return httpx.Response(302, headers={"location": "https://evil.test/x.xml"})

    with pytest.raises(RuntimeError):
        download_xml(URL, tmp_path / "t.xml", transport=httpx.MockTransport(handler))
    assert calls == [URL]


def test_bad_url_is_rejected_before_any_request(tmp_path):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(200, content=b"x")

    with pytest.raises(ValueError):
        download_xml(
            "https://evil.test/xml/mplus_topics_2026-11-03.xml",
            tmp_path / "t.xml",
            transport=httpx.MockTransport(handler),
        )
    assert calls == []
