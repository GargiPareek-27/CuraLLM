"""Runtime configuration for the inference service, read from environment variables."""
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    provider: str
    max_concurrency: int


def load_settings() -> Settings:
    provider = os.environ.get("INFERENCE_PROVIDER", "mock")
    raw_concurrency = os.environ.get("INFERENCE_MAX_CONCURRENCY", "4")
    try:
        max_concurrency = int(raw_concurrency)
    except ValueError as exc:
        raise ValueError(
            f"INFERENCE_MAX_CONCURRENCY must be an integer, got {raw_concurrency!r}"
        ) from exc
    if not 1 <= max_concurrency <= 64:
        raise ValueError("INFERENCE_MAX_CONCURRENCY must be between 1 and 64")
    return Settings(provider=provider, max_concurrency=max_concurrency)
