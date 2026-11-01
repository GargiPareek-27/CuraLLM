"""Chat endpoint (Phase 1: passes the message to the mock inference service)."""
from fastapi import APIRouter, Depends, HTTPException, Request

from app.deps import get_inference_client
from app.request_id import resolve_request_id
from app.inference_client import (
    InferenceBadResponse,
    InferenceClient,
    InferenceTimeout,
    InferenceUnavailable,
)
from app.schemas import ChatRequest, ChatResponse

router = APIRouter(tags=["chat"])

# Phase 1 sends the raw message. A real versioned prompt arrives with Phase 2.
PROMPT_VERSION = "phase1-passthrough"


@router.post("/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    request: Request,
    client: InferenceClient = Depends(get_inference_client),
) -> ChatResponse:
    request_id = getattr(request.state, "request_id", None) or resolve_request_id(None)
    try:
        result = await client.generate(prompt=body.message, request_id=request_id)
    except InferenceTimeout:
        raise HTTPException(status_code=504, detail="The inference service timed out.")
    except InferenceUnavailable:
        raise HTTPException(status_code=503, detail="The inference service is unavailable.")
    except InferenceBadResponse:
        raise HTTPException(
            status_code=502, detail="The inference service returned an invalid response."
        )
    return ChatResponse(
        request_id=request_id,
        answer=result.text,
        model_id=result.model_id,
        model_revision=result.model_revision,
        prompt_version=PROMPT_VERSION,
        is_demo=result.is_mock,
    )
