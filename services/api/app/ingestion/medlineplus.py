"""MedlinePlus health topic XML: URL checks, download, and parsing.

Only the public-domain health topic summaries are used. The `<site>` records
(links to other organizations) and everything else are ignored, so no
copyrighted MedlinePlus material (encyclopedia, drug monographs, images) is
ever read into a Topic. Rights are recorded in ml/data/source_registry.json.
"""
import re
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime
from urllib.parse import urlsplit

from app.ingestion.html_text import html_to_paragraphs

SOURCE_ID = "medlineplus_health_topics"
LICENSE_TEXT = "U.S. federal government work, not copyrighted (public domain)"
ATTRIBUTION = "Courtesy of MedlinePlus from the National Library of Medicine"
ALLOWED_HOST = "medlineplus.gov"
TOPIC_URL_PREFIX = "https://medlineplus.gov/"
MAX_DOWNLOAD_BYTES = 100 * 1024 * 1024
_XML_PATH = re.compile(r"/xml/mplus_topics_\d{4}-\d{2}-\d{2}\.xml")


@dataclass(frozen=True)
class Topic:
    external_id: str
    title: str
    url: str
    language: str
    date_created: str | None
    meta_desc: str | None
    also_called: tuple[str, ...]
    groups: tuple[str, ...]
    mesh: tuple[str, ...]
    paragraphs: tuple[str, ...]
    credit: str | None


@dataclass
class ParseReport:
    parsed: int = 0
    skipped: Counter = field(default_factory=Counter)
    generated_on: str | None = None


def build_xml_url(day: str) -> str:
    """URL of the health topic XML file for a publication date (YYYY-MM-DD)."""
    try:
        date.fromisoformat(day)
    except ValueError as error:
        raise ValueError("date must look like YYYY-MM-DD") from error
    return f"https://{ALLOWED_HOST}/xml/mplus_topics_{day}.xml"


def validate_xml_url(url: str) -> None:
    """Accept only https://medlineplus.gov/xml/mplus_topics_YYYY-MM-DD.xml. Raises ValueError otherwise."""
    parts = urlsplit(url)
    if parts.scheme != "https":
        raise ValueError("only https URLs are allowed")
    if parts.hostname != ALLOWED_HOST or parts.port is not None or parts.username or parts.password:
        raise ValueError(f"only {ALLOWED_HOST} is allowed")
    if parts.query or parts.fragment or not _XML_PATH.fullmatch(parts.path):
        raise ValueError("URL must be /xml/mplus_topics_YYYY-MM-DD.xml")


def download_xml(url: str, destination, *, transport=None, max_bytes: int = MAX_DOWNLOAD_BYTES) -> int:
    """Download `url` to `destination` (a path). Returns the byte count.

    No redirects are followed, the size is capped, and only the allowed URL
    pattern is accepted.
    """
    import httpx

    validate_xml_url(url)
    written = 0
    timeout = httpx.Timeout(connect=10.0, read=60.0, write=10.0, pool=10.0)
    with httpx.Client(timeout=timeout, follow_redirects=False, transport=transport) as client:
        with client.stream("GET", url) as response:
            if response.status_code != 200:
                raise RuntimeError(
                    f"download failed with HTTP {response.status_code} "
                    "(files are published Tuesday to Saturday; check the date)"
                )
            with open(destination, "wb") as handle:
                for block in response.iter_bytes():
                    written += len(block)
                    if written > max_bytes:
                        raise RuntimeError("download exceeds the size limit")
                    handle.write(block)
    return written


def _iso_from_us_date(value: str | None) -> str | None:
    if not value:
        return None
    for pattern in ("%m/%d/%Y %H:%M:%S", "%m/%d/%Y"):
        try:
            return datetime.strptime(value.strip(), pattern).date().isoformat()
        except ValueError:
            continue
    return None


def _summary_html(element) -> str:
    """The summary may be real child elements or escaped/CDATA text. Handle both."""
    if len(element):
        inner = "".join(ET.tostring(child, encoding="unicode") for child in element)
        return (element.text or "") + inner
    return element.text or ""


def _split_credit(paragraphs: list[str]) -> tuple[list[str], str | None]:
    """Move a trailing 'NIH: ...' credit line out of the searchable text."""
    kept, credit = [], None
    for paragraph in paragraphs:
        if paragraph.startswith("NIH:") and len(paragraph) < 200 and "\n" not in paragraph:
            credit = paragraph
        else:
            kept.append(paragraph)
    return kept, credit


def parse_topics(source, language: str = "English", report: ParseReport | None = None):
    """Yield Topic objects from a MedlinePlus health topic XML file (path or file object)."""
    report = report if report is not None else ParseReport()
    for event, element in ET.iterparse(source, events=("start", "end")):
        if event == "start" and element.tag == "health-topics":
            raw = element.get("date-generated") or element.get("dategenerated")
            report.generated_on = _iso_from_us_date(raw)
            continue
        if event != "end" or element.tag != "health-topic":
            continue

        topic_language = element.get("language", "")
        if topic_language != language:
            report.skipped["other_language"] += 1
            element.clear()
            continue
        url = element.get("url", "")
        external_id = element.get("id", "")
        title = (element.get("title") or "").strip()
        if not (external_id and title) or not url.startswith(TOPIC_URL_PREFIX):
            report.skipped["bad_record_or_url"] += 1
            element.clear()
            continue
        summary = element.find("full-summary")
        if summary is None:
            report.skipped["no_summary"] += 1
            element.clear()
            continue
        paragraphs, credit = _split_credit(html_to_paragraphs(_summary_html(summary)))
        if not paragraphs:
            report.skipped["empty_summary"] += 1
            element.clear()
            continue

        topic = Topic(
            external_id=external_id,
            title=title,
            url=url,
            language=topic_language,
            date_created=_iso_from_us_date(element.get("date-created")),
            meta_desc=(element.get("meta-desc") or None),
            also_called=tuple(t.text.strip() for t in element.findall("also-called") if t.text),
            groups=tuple((g.text or "").strip() for g in element.findall("group") if (g.text or "").strip()),
            mesh=tuple(
                (d.text or "").strip()
                for d in element.findall("mesh-heading/descriptor")
                if (d.text or "").strip()
            ),
            paragraphs=tuple(paragraphs),
            credit=credit,
        )
        report.parsed += 1
        element.clear()
        yield topic
