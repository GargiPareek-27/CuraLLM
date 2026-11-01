"""Provider interface and typed errors for model backends."""
from dataclasses import dataclass
from typing import Protocol


class ProviderError(Exception):
    """Base class for every provider failure."""


class ProviderConfigError(ProviderError):
    """The provider is misconfigured or not implemented."""


class ProviderUnavailable(ProviderError):
    """The backend could not be reached or is not serving."""


class ProviderTimeout(ProviderError):
    """The backend did not answer in time."""


class ProviderBadResponse(ProviderError):
    """The backend answered, but the answer was unusable."""


@dataclass(frozen=True)
class GenerationRequest:
    prompt: str
    max_tokens: int = 512
    request_id: str | None = None


@dataclass(frozen=True)
class GenerationResult:
    text: str
    model_id: str
    model_revision: str
    is_mock: bool
    prompt_tokens: int | None = None
    completion_tokens: int | None = None


class Provider(Protocol):
    name: str

    async def generate(self, request: GenerationRequest) -> GenerationResult: ...

    async def health(self) -> bool: ...
