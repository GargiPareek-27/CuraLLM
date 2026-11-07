"""Keyword (PostgreSQL full-text) search over ingested chunks."""
from sqlalchemy import text

from app.db import get_engine
from app.ingestion.medlineplus import SOURCE_ID

# websearch_to_tsquery accepts any user text without syntax errors. Words are combined
# with AND. ts_rank_cd with flag 32 maps the score into 0..1; it is a lexical score,
# not a probability that the passage is correct or relevant.
_SEARCH_SQL = text(
    """
    WITH q AS (SELECT websearch_to_tsquery('english', :q) AS query)
    SELECT c.id AS chunk_id, d.id AS document_id, d.source_id, d.external_id, d.title, d.url,
           d.language, d.corpus_version, d.license, d.attribution,
           c.chunk_index, c.text, ts_rank_cd(c.search_vector, q.query, 32) AS score
    FROM chunks c
    JOIN documents d ON d.id = c.document_id
    CROSS JOIN q
    WHERE d.is_active AND d.source_id = :source AND c.search_vector @@ q.query
    ORDER BY score DESC, c.id
    LIMIT :limit
    """
)


def search_chunks(query: str, limit: int) -> list[dict]:
    with get_engine().connect() as connection:
        rows = connection.execute(
            _SEARCH_SQL, {"q": query, "limit": limit, "source": SOURCE_ID}
        ).mappings().all()
    return [dict(row) for row in rows]
