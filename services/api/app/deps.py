"""FastAPI dependencies."""
from collections.abc import Callable

from fastapi import Request

from app.inference_client import InferenceClient
from app.search import search_chunks


def get_inference_client(request: Request) -> InferenceClient:
    return request.app.state.inference_client


def get_searcher() -> Callable[[str, int], list[dict]]:
    return search_chunks
