import json
from pathlib import Path

import pytest

from app.ingestion.medlineplus import ATTRIBUTION, LICENSE_TEXT, SOURCE_ID


def _find_registry():
    """Search upward for ml/data/source_registry.json; absent inside the container image."""
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "ml" / "data" / "source_registry.json"
        if candidate.exists():
            return candidate
    return None


def test_ingestion_constants_match_the_source_registry():
    registry = _find_registry()
    if registry is None:
        pytest.skip("source registry not available (running inside the container image)")
    sources = {s["id"]: s for s in json.loads(registry.read_text(encoding="utf-8"))["sources"]}
    source = sources[SOURCE_ID]
    assert source["status"] == "approved"
    assert source["allowed_uses"]["rag"] == "yes"
    assert source["license"]["name"] == LICENSE_TEXT
    assert source["attribution"] == ATTRIBUTION
