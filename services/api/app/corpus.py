"""Descriptive statistics about the ingested corpus (read-only)."""
from sqlalchemy import text

from app.db import get_engine
from app.ingestion.medlineplus import SOURCE_ID


def corpus_stats(engine=None) -> dict:
    engine = engine or get_engine()
    params = {"s": SOURCE_ID}
    with engine.connect() as connection:
        documents = connection.execute(
            text(
                "SELECT count(*) FILTER (WHERE is_active) AS active, count(*) AS total "
                "FROM documents WHERE source_id = :s"
            ),
            params,
        ).one()
        chunks = connection.execute(
            text(
                """
                SELECT count(*) AS chunks, min(c.token_count) AS min_tokens,
                       percentile_cont(0.5) WITHIN GROUP (ORDER BY c.token_count) AS median_tokens,
                       percentile_cont(0.95) WITHIN GROUP (ORDER BY c.token_count) AS p95_tokens,
                       max(c.token_count) AS max_tokens
                FROM chunks c JOIN documents d ON d.id = c.document_id
                WHERE d.source_id = :s AND d.is_active
                """
            ),
            params,
        ).one()
        multi_chunk = connection.execute(
            text(
                """
                SELECT count(*) FROM (
                    SELECT d.id FROM documents d JOIN chunks c ON c.document_id = d.id
                    WHERE d.source_id = :s AND d.is_active
                    GROUP BY d.id HAVING count(*) > 1
                ) AS t
                """
            ),
            params,
        ).scalar_one()
        versions = connection.execute(
            text(
                "SELECT corpus_version, count(*) AS n FROM documents WHERE source_id = :s "
                "GROUP BY corpus_version ORDER BY corpus_version"
            ),
            params,
        ).all()
        runs = connection.execute(
            text(
                "SELECT id, corpus_version, status, documents_seen, documents_inserted, "
                "documents_updated, documents_unchanged, documents_deactivated, chunks_written, "
                "started_at, finished_at FROM ingestion_runs WHERE source_id = :s "
                "ORDER BY id DESC LIMIT 5"
            ),
            params,
        ).mappings().all()

    def number(value):
        return None if value is None else round(float(value), 1)

    return {
        "source_id": SOURCE_ID,
        "active_documents": documents.active,
        "total_documents": documents.total,
        "active_chunks": chunks.chunks,
        "documents_with_multiple_chunks": multi_chunk,
        "chunk_tokens_approx": {
            "min": chunks.min_tokens,
            "median": number(chunks.median_tokens),
            "p95": number(chunks.p95_tokens),
            "max": chunks.max_tokens,
        },
        "documents_by_corpus_version": {row.corpus_version: row.n for row in versions},
        "recent_ingestion_runs": [dict(row) for row in runs],
    }
