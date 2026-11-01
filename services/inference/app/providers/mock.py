"""Deterministic mock provider for development and tests.

It is not a trained model. Every response says so, and it reports no token
counts rather than inventing them.
"""
from app.providers.base import GenerationRequest, GenerationResult

MOCK_MODEL_ID = "curallm-mock"
MOCK_MODEL_REVISION = "mock-1"
DEMO_NOTICE = (
    "[DEMO MODE: deterministic mock response. This is not a trained medical "
    "model and not medical advice.]"
)


class MockProvider:
    name = "mock"

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        text = (
            f"{DEMO_NOTICE} Your message was received "
            f"({len(request.prompt)} characters). No medical knowledge, evidence "
            "retrieval or citations are used in this mode. For health concerns, "
            "please speak with a qualified clinician; in an emergency, contact "
            "your local emergency services."
        )
        return GenerationResult(
            text=text,
            model_id=MOCK_MODEL_ID,
            model_revision=MOCK_MODEL_REVISION,
            is_mock=True,
        )

    async def health(self) -> bool:
        return True
