"""Inference service: a thin HTTP layer over interchangeable model providers."""
import asyncio
import logging

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from app.config import load_settings
from app.providers.base import (
    GenerationRequest,
    Provider,
    ProviderBadResponse,
    ProviderTimeout,
    ProviderUnavailable,
)
from app.providers.factory import create_provider

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("curallm.inference")


class GenerateRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=8000)
    max_tokens: int = Field(default=512, ge=1, le=1024)
    request_id: str | None = Field(default=None, max_length=64)


class Usage(BaseModel):
    prompt_tokens: int | None = None
    completion_tokens: int | None = None


class GenerateResponse(BaseModel):
    # model_id / model_revision are intentional field names.
    model_config = ConfigDict(protected_namespaces=())

    text: str
    model_id: str
    model_revision: str
    is_mock: bool
    usage: Usage | None = None


def create_app(provider: Provider | None = None) -> FastAPI:
    settings = load_settings()
    active = provider if provider is not None else create_provider(settings.provider)
    semaphore = asyncio.Semaphore(settings.max_concurrency)
    app = FastAPI(title="CuraLLM Inference Service", version="0.1.0")

    @app.get("/health")
    async def health() -> dict:
        if not await active.health():
            raise HTTPException(status_code=503, detail="Provider is not healthy.")
        return {"status": "ok", "provider": active.name}

    @app.post("/v1/generate", response_model=GenerateResponse)
    async def generate(body: GenerateRequest) -> GenerateResponse:
        # Log sizes and ids only, never the prompt itself.
        logger.info(
            "generate request_id=%s prompt_chars=%d provider=%s",
            body.request_id,
            len(body.prompt),
            active.name,
        )
        async with semaphore:
            try:
                result = await active.generate(
                    GenerationRequest(
                        prompt=body.prompt,
                        max_tokens=body.max_tokens,
                        request_id=body.request_id,
                    )
                )
            except ProviderTimeout:
                raise HTTPException(status_code=504, detail="The model provider timed out.")
            except ProviderUnavailable:
                raise HTTPException(status_code=503, detail="The model provider is unavailable.")
            except ProviderBadResponse:
                raise HTTPException(
                    status_code=502, detail="The model provider returned an unusable response."
                )

        usage = None
        if result.prompt_tokens is not None or result.completion_tokens is not None:
            usage = Usage(
                prompt_tokens=result.prompt_tokens,
                completion_tokens=result.completion_tokens,
            )
        return GenerateResponse(
            text=result.text,
            model_id=result.model_id,
            model_revision=result.model_revision,
            is_mock=result.is_mock,
            usage=usage,
        )

    return app


app = create_app()
