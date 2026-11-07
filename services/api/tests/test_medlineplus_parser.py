from pathlib import Path

import pytest

from app.ingestion.chunking import approx_tokens, chunk_paragraphs
from app.ingestion.medlineplus import (
    ParseReport,
    build_xml_url,
    parse_topics,
    validate_xml_url,
)

FIXTURE = Path(__file__).parent / "fixtures" / "mplus_sample.xml"


def english_topics():
    report = ParseReport()
    return list(parse_topics(FIXTURE, "English", report)), report


def test_english_topics_and_skip_counts():
    topics, report = english_topics()
    assert [t.external_id for t in topics] == ["9001", "9002", "9003"]
    assert report.parsed == 3
    assert dict(report.skipped) == {"other_language": 1, "bad_record_or_url": 1, "no_summary": 1}
    assert report.generated_on == "2026-01-01"


def test_fields_of_a_full_record():
    topic = english_topics()[0][0]
    assert topic.title == "Sample Topic: Zebra Fever"
    assert topic.url == "https://medlineplus.gov/zebrafever.html"
    assert topic.date_created == "2020-03-05"
    assert topic.also_called == ("Striped fever", "Zebra syndrome")
    assert topic.groups == ("Test Group",)
    assert topic.mesh == ("Imaginary Fever",)
    assert topic.meta_desc.startswith("Synthetic test topic")


def test_summary_is_plain_text_and_credit_is_separated():
    topic = english_topics()[0][0]
    assert topic.paragraphs[0].startswith("Zebra fever is an imaginary condition")
    assert "no link to any real illness" in topic.paragraphs[0]
    assert "- Imaginary stripes\n- Invented warmth" in topic.paragraphs
    assert topic.credit == "NIH: Synthetic Test Institute"
    assert all("NIH:" not in p and "<" not in p for p in topic.paragraphs)


def test_external_site_records_are_never_read():
    topic = english_topics()[0][0]
    everything = " ".join(topic.paragraphs) + topic.title + " ".join(topic.also_called)
    assert "Ignored external link" not in everything and "example.org" not in everything


def test_escaped_markup_summary_is_handled():
    topic = english_topics()[0][1]
    assert topic.paragraphs[0] == "Quokka cough is an imaginary condition with escaped markup & entities."
    assert all("<" not in p for p in topic.paragraphs)


def test_spanish_selection():
    report = ParseReport()
    topics = list(parse_topics(FIXTURE, "Spanish", report))
    assert [t.external_id for t in topics] == ["9004"]


def test_long_topic_chunks_within_limits():
    topic = english_topics()[0][2]
    chunks = chunk_paragraphs(list(topic.paragraphs), max_tokens=220, overlap_tokens=40)
    assert len(chunks) >= 2
    assert all(approx_tokens(c) <= 220 for c in chunks)


def test_build_xml_url():
    assert build_xml_url("2026-11-03") == "https://medlineplus.gov/xml/mplus_topics_2026-11-03.xml"
    for bad in ("2026-13-01", "11/03/2026", "x", ""):
        with pytest.raises(ValueError):
            build_xml_url(bad)


def test_url_validation():
    validate_xml_url("https://medlineplus.gov/xml/mplus_topics_2026-11-03.xml")
    bad_urls = [
        "http://medlineplus.gov/xml/mplus_topics_2026-11-03.xml",
        "https://medlineplus.gov.evil.com/xml/mplus_topics_2026-11-03.xml",
        "https://evil.com/xml/mplus_topics_2026-11-03.xml",
        "https://user@medlineplus.gov/xml/mplus_topics_2026-11-03.xml",
        "https://medlineplus.gov:8443/xml/mplus_topics_2026-11-03.xml",
        "https://medlineplus.gov/xml/mplus_topics_2026-11-03.xml?x=1",
        "https://medlineplus.gov/xml/other.xml",
        "https://medlineplus.gov/",
        "file:///etc/passwd",
    ]
    for url in bad_urls:
        with pytest.raises(ValueError):
            validate_xml_url(url)
