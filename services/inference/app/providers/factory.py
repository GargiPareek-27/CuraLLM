"""Create a provider from its configured name."""
from app.providers.base import Provider, ProviderConfigError
from app.providers.mock import MockProvider

PLANNED_PROVIDERS = {"ollama", "openai_compatible"}


def create_provider(name: str) -> Provider:
    key = name.strip().lower()
    if key == "mock":
        return MockProvider()
    if key in PLANNED_PROVIDERS:
        raise ProviderConfigError(
            f"Provider '{key}' is planned for Phase 2 and is not implemented yet. "
            "Set INFERENCE_PROVIDER=mock."
        )
    raise ProviderConfigError(f"Unknown provider '{name}'. Available now: mock.")
