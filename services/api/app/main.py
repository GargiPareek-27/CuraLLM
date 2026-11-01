"""CuraLLM API application."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.inference_client import InferenceClient
from app.middleware import request_context_middleware
from app.routers import chat, health

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.inference_client = InferenceClient(
        base_url=settings.inference_url,
        connect_timeout=settings.inference_connect_timeout,
        read_timeout=settings.inference_read_timeout,
        max_retries=settings.inference_max_retries,
        max_concurrency=settings.inference_max_concurrency,
    )
    try:
        yield
    finally:
        await app.state.inference_client.aclose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="CuraLLM API", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "X-Request-ID"],
        allow_credentials=False,
    )
    app.middleware("http")(request_context_middleware)
    app.include_router(health.router)
    app.include_router(chat.router, prefix="/api/v1")
    return app


app = create_app()
