"""Retrieval-only search endpoint: returns cited passages, never generated text."""
from collections.abc import Callable
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.exc import SQLAlchemyError
from starlette.concurrency import run_in_threadpool

from app.deps import get_searcher
from app.request_id import resolve_request_id

router = APIRouter(tags=["search"])


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    limit: int = Field(default=5, ge=1, le=10)

    @field_validator("query")
    @classmethod
    def not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("query must not be blank")
        return stripped


class Passage(BaseModel):
    passage_id: str
    source_id: str
    title: str
    source_url: str
    text: str
    chunk_index: int
    language: str
    corpus_version: str
    license: str
    attribution: str
    lexical_score: float


class SearchResponse(BaseModel):
    request_id: str
    query: str
    retrieval_method: Literal["postgres_full_text"] = "postgres_full_text"
    results: list[Passage]


@router.post("/search", response_model=SearchResponse)
async def search(
    body: SearchRequest,
    request: Request,
    searcher: Callable[[str, int], list[dict]] = Depends(get_searcher),
) -> SearchResponse:
    request_id = getattr(request.state, "request_id", None) or resolve_request_id(None)
    try:
        rows = await run_in_threadpool(searcher, body.query, body.limit)
    except SQLAlchemyError:
        raise HTTPException(
            status_code=503,
            detail="Search is unavailable. The database may not be migrated or reachable.",
        )
    passages = [
        Passage(
            passage_id=f"{row['source_id']}:{row['external_id']}:{row['chunk_index']}",
            source_id=row["source_id"],
            title=row["title"],
            source_url=row["url"],
            text=row["text"],
            chunk_index=row["chunk_index"],
            language=row["language"],
            corpus_version=row["corpus_version"],
            license=row["license"],
            attribution=row["attribution"],
            lexical_score=float(row["score"]),
        )
        for row in rows
    ]
    return SearchResponse(request_id=request_id, query=body.query, results=passages)
