import os

# Settings need a URL at import time. The engine is created lazily, so no database is contacted.
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://test:test@localhost:5432/test")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.deps import get_inference_client  # noqa: E402
from app.main import create_app  # noqa: E402


class FakeInferenceClient:
    def __init__(self, result=None, error=None, healthy=True):
        self.result = result
        self.error = error
        self.healthy = healthy

    async def generate(self, prompt, max_tokens=512, request_id=None):
        if self.error is not None:
            raise self.error
        return self.result

    async def health(self):
        return self.healthy

    async def aclose(self):
        pass


@pytest.fixture
def make_client():
    def _make(fake):
        app = create_app()
        app.dependency_overrides[get_inference_client] = lambda: fake
        # Not used as a context manager, so the lifespan (and the real client) never starts.
        return TestClient(app)

    return _make
