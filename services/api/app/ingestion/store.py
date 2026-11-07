"""Write MedlinePlus topics into PostgreSQL: documents, chunks and an ingestion run log.

Idempotent: a topic whose content (and chunking settings) are unchanged is not
rewritten. A changed topic has its chunks replaced inside one transaction.
Only the latest version of each topic is kept; the run log records what each
run did.
"""
import hashlib
import json
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import text

from app.ingestion.chunking import approx_tokens, chunk_paragraphs
from app.ingestion.medlineplus import ATTRIBUTION, LICENSE_TEXT, SOURCE_ID, Topic


@dataclass
class IngestReport:
    run_id: int | None = None
    corpus_version: str = ""
    documents_seen: int = 0
    inserted: int = 0
    updated: int = 0
    unchanged: int = 0
    deactivated: int = 0
    chunks_written: int = 0


def content_hash(topic: Topic, max_tokens: int, overlap_tokens: int) -> str:
    payload = {
        "title": topic.title,
        "url": topic.url,
        "language": topic.language,
        "also_called": topic.also_called,
        "groups": topic.groups,
        "mesh": topic.mesh,
        "paragraphs": topic.paragraphs,
        "chunking": [max_tokens, overlap_tokens],
    }
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def heading_for(topic: Topic) -> str:
    return " | ".join([topic.title, *topic.also_called])


_INSERT_DOCUMENT = text(
    """
    INSERT INTO documents (source_id, external_id, title, url, language, source_created_on,
        corpus_version, retrieved_at, license, attribution, content_sha256, metadata)
    VALUES (:source_id, :external_id, :title, :url, :language, :source_created_on,
        :corpus_version, :retrieved_at, :license, :attribution, :content_sha256,
        CAST(:metadata AS jsonb))
    RETURNING id
    """
)
_UPDATE_DOCUMENT = text(
    """
    UPDATE documents SET title = :title, url = :url, language = :language,
        source_created_on = :source_created_on, corpus_version = :corpus_version,
        retrieved_at = :retrieved_at, license = :license, attribution = :attribution,
        content_sha256 = :content_sha256, metadata = CAST(:metadata AS jsonb),
        is_active = TRUE, updated_at = now()
    WHERE id = :id
    """
)
_TOUCH_DOCUMENT = text(
    """
    UPDATE documents SET corpus_version = :corpus_version, retrieved_at = :retrieved_at,
        is_active = TRUE WHERE id = :id
    """
)
_INSERT_CHUNKS = text(
    """
    INSERT INTO chunks (document_id, chunk_index, heading, text, token_count)
    VALUES (:document_id, :chunk_index, :heading, :text, :token_count)
    """
)


def _write_chunks(connection, document_id: int, topic: Topic, chunks: list[str]) -> int:
    heading = heading_for(topic)
    rows = [
        {
            "document_id": document_id,
            "chunk_index": index,
            "heading": heading,
            "text": chunk,
            "token_count": approx_tokens(chunk),
        }
        for index, chunk in enumerate(chunks)
    ]
    if rows:
        connection.execute(_INSERT_CHUNKS, rows)
    return len(rows)


def _ingest_one(connection, topic, report, corpus_version, retrieved_at, max_tokens, overlap_tokens):
    digest = content_hash(topic, max_tokens, overlap_tokens)
    chunks = chunk_paragraphs(list(topic.paragraphs), max_tokens, overlap_tokens)
    metadata = {
        "also_called": list(topic.also_called),
        "groups": list(topic.groups),
        "mesh_descriptors": list(topic.mesh),
        "meta_description": topic.meta_desc,
        "nih_credit": topic.credit,
    }
    params = {
        "source_id": SOURCE_ID,
        "external_id": topic.external_id,
        "title": topic.title,
        "url": topic.url,
        "language": topic.language,
        "source_created_on": topic.date_created,
        "corpus_version": corpus_version,
        "retrieved_at": retrieved_at,
        "license": LICENSE_TEXT,
        "attribution": ATTRIBUTION,
        "content_sha256": digest,
        "metadata": json.dumps(metadata, ensure_ascii=False),
    }
    existing = connection.execute(
        text("SELECT id, content_sha256 FROM documents WHERE source_id = :s AND external_id = :e"),
        {"s": SOURCE_ID, "e": topic.external_id},
    ).first()

    if existing is None:
        document_id = connection.execute(_INSERT_DOCUMENT, params).scalar_one()
        report.chunks_written += _write_chunks(connection, document_id, topic, chunks)
        report.inserted += 1
    elif existing.content_sha256 == digest:
        connection.execute(
            _TOUCH_DOCUMENT,
            {"id": existing.id, "corpus_version": corpus_version, "retrieved_at": retrieved_at},
        )
        report.unchanged += 1
    else:
        connection.execute(_UPDATE_DOCUMENT, {**params, "id": existing.id})
        connection.execute(text("DELETE FROM chunks WHERE document_id = :id"), {"id": existing.id})
        report.chunks_written += _write_chunks(connection, existing.id, topic, chunks)
        report.updated += 1


def ingest_topics(
    engine,
    topics: Iterable[Topic],
    corpus_version: str,
    *,
    full_run: bool,
    max_tokens: int = 220,
    overlap_tokens: int = 40,
) -> IngestReport:
    """Ingest topics. With `full_run`, topics absent from this file are deactivated afterwards."""
    report = IngestReport(corpus_version=corpus_version)
    retrieved_at = datetime.now(timezone.utc)
    with engine.begin() as connection:
        report.run_id = connection.execute(
            text(
                "INSERT INTO ingestion_runs (source_id, corpus_version, status) "
                "VALUES (:s, :v, 'running') RETURNING id"
            ),
            {"s": SOURCE_ID, "v": corpus_version},
        ).scalar_one()

    try:
        for topic in topics:
            report.documents_seen += 1
            with engine.begin() as connection:
                _ingest_one(
                    connection, topic, report, corpus_version, retrieved_at, max_tokens, overlap_tokens
                )
        # An empty file must never wipe the corpus, so deactivate only after seeing documents.
        if full_run and report.documents_seen > 0:
            with engine.begin() as connection:
                report.deactivated = connection.execute(
                    text(
                        "UPDATE documents SET is_active = FALSE, updated_at = now() "
                        "WHERE source_id = :s AND is_active AND corpus_version <> :v"
                    ),
                    {"s": SOURCE_ID, "v": corpus_version},
                ).rowcount
    except Exception as error:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "UPDATE ingestion_runs SET status = 'failed', finished_at = now(), "
                    "error_type = :t WHERE id = :id"
                ),
                {"t": type(error).__name__, "id": report.run_id},
            )
        raise

    with engine.begin() as connection:
        connection.execute(
            text(
                "UPDATE ingestion_runs SET status = 'completed', finished_at = now(), "
                "documents_seen = :seen, documents_inserted = :ins, documents_updated = :upd, "
                "documents_unchanged = :unc, documents_deactivated = :deact, "
                "chunks_written = :chunks WHERE id = :id"
            ),
            {
                "seen": report.documents_seen,
                "ins": report.inserted,
                "upd": report.updated,
                "unc": report.unchanged,
                "deact": report.deactivated,
                "chunks": report.chunks_written,
                "id": report.run_id,
            },
        )
    return report
