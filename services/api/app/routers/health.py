"""Liveness and readiness endpoints."""
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from app.db import check_database
from app.deps import get_inference_client
from app.inference_client import InferenceClient

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict:
    """Liveness: the process is up. Checks no dependencies."""
    return {"status": "ok"}


@router.get("/ready")
async def ready(client: InferenceClient = Depends(get_inference_client)) -> JSONResponse:
    """Readiness: the database and the inference service both answer."""
    database = await run_in_threadpool(check_database)
    inference_ok = await client.health()
    is_ready = database.get("database") == "ok" and inference_ok
    body = {
        "status": "ready" if is_ready else "not_ready",
        **database,
        "inference": "ok" if inference_ok else "unavailable",
    }
    return JSONResponse(status_code=200 if is_ready else 503, content=body)
