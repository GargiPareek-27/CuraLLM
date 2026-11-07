"""documents, chunks and ingestion runs

Revision ID: 0002_documents_and_chunks
Revises: 0001_enable_pgvector
Create Date: 2026-11-05
"""
from alembic import op

revision = "0002_documents_and_chunks"
down_revision = "0001_enable_pgvector"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE ingestion_runs (
            id BIGSERIAL PRIMARY KEY,
            source_id TEXT NOT NULL,
            corpus_version TEXT NOT NULL,
            started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            finished_at TIMESTAMPTZ,
            status TEXT NOT NULL CHECK (status IN ('running', 'completed', 'failed')),
            documents_seen INTEGER NOT NULL DEFAULT 0,
            documents_inserted INTEGER NOT NULL DEFAULT 0,
            documents_updated INTEGER NOT NULL DEFAULT 0,
            documents_unchanged INTEGER NOT NULL DEFAULT 0,
            documents_deactivated INTEGER NOT NULL DEFAULT 0,
            chunks_written INTEGER NOT NULL DEFAULT 0,
            error_type TEXT
        )
        """
    )
    op.execute(
        """
        CREATE TABLE documents (
            id BIGSERIAL PRIMARY KEY,
            source_id TEXT NOT NULL,
            external_id TEXT NOT NULL,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            language TEXT NOT NULL,
            source_created_on DATE,
            corpus_version TEXT NOT NULL,
            retrieved_at TIMESTAMPTZ NOT NULL,
            license TEXT NOT NULL,
            attribution TEXT NOT NULL,
            content_sha256 TEXT NOT NULL,
            metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT documents_source_external_uniq UNIQUE (source_id, external_id)
        )
        """
    )
    op.execute("CREATE INDEX documents_active_idx ON documents (source_id) WHERE is_active")
    op.execute(
        """
        CREATE TABLE chunks (
            id BIGSERIAL PRIMARY KEY,
            document_id BIGINT NOT NULL REFERENCES documents (id) ON DELETE CASCADE,
            chunk_index INTEGER NOT NULL,
            heading TEXT NOT NULL,
            text TEXT NOT NULL,
            token_count INTEGER NOT NULL,
            search_vector TSVECTOR GENERATED ALWAYS AS (
                setweight(to_tsvector('english', heading), 'A') ||
                setweight(to_tsvector('english', text), 'B')
            ) STORED,
            CONSTRAINT chunks_document_index_uniq UNIQUE (document_id, chunk_index)
        )
        """
    )
    op.execute("CREATE INDEX chunks_search_vector_idx ON chunks USING GIN (search_vector)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS chunks")
    op.execute("DROP TABLE IF EXISTS documents")
    op.execute("DROP TABLE IF EXISTS ingestion_runs")
