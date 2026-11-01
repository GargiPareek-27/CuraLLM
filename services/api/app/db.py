"""Database access: engine creation and a readiness check."""
from functools import lru_cache

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from app.config import get_settings


@lru_cache
def get_engine() -> Engine:
    return create_engine(
        get_settings().database_url,
        pool_size=5,
        max_overflow=5,
        pool_timeout=5,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 3},
    )


def check_database() -> dict:
    """Return database status. Never includes exception text (it can reveal hosts or users)."""
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
            vector = connection.execute(
                text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
            ).first()
        return {"database": "ok", "pgvector": "installed" if vector else "missing"}
    except Exception as exc:
        return {"database": "error", "detail": type(exc).__name__}
