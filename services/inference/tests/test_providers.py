import asyncio

import pytest

from app.providers.base import GenerationRequest, ProviderConfigError
from app.providers.factory import create_provider
from app.providers.mock import DEMO_NOTICE, MockProvider


def run(coro):
    return asyncio.run(coro)


def test_mock_is_deterministic():
    provider = MockProvider()
    request = GenerationRequest(prompt="What is hypertension?")
    assert run(provider.generate(request)) == run(provider.generate(request))


def test_mock_is_labelled_and_reports_no_token_counts():
    result = run(MockProvider().generate(GenerationRequest(prompt="hello")))
    assert result.is_mock is True
    assert DEMO_NOTICE in result.text
    assert result.prompt_tokens is None and result.completion_tokens is None


def test_factory_returns_mock():
    assert create_provider("mock").name == "mock"
    assert create_provider("  MOCK ").name == "mock"


@pytest.mark.parametrize("name", ["ollama", "openai_compatible"])
def test_factory_rejects_planned_providers_clearly(name):
    with pytest.raises(ProviderConfigError, match="not implemented yet"):
        create_provider(name)


def test_factory_rejects_unknown_provider():
    with pytest.raises(ProviderConfigError, match="Unknown provider"):
        create_provider("nonsense")
