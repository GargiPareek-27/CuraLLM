"""Request and response schemas for the public API."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)

    @field_validator("message")
    @classmethod
    def not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("message must not be blank")
        return stripped


class Citation(BaseModel):
    passage_id: str
    title: str
    source_url: str | None = None


class ChatResponse(BaseModel):
    # model_id / model_revision are intentional field names.
    model_config = ConfigDict(protected_namespaces=())

    request_id: str
    answer: str
    # Phase 1 has no retrieval, so this is always empty. Phase 2 fills it from retrieved passages.
    citations: list[Citation] = Field(default_factory=list)
    # Phase 1 has no safety checks. The literal widens when they exist.
    safety_status: Literal["not_evaluated"] = "not_evaluated"
    clarification_required: bool = False
    professional_review_recommended: bool = True
    model_id: str
    model_revision: str
    prompt_version: str
    is_demo: bool
