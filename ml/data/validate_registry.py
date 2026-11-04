"""Validate ml/data/source_registry.json. Standard library only.

Run from the repo root:  python ml/data/validate_registry.py [path-to-registry]
Exit code 0 = valid, 1 = problems found (listed one per line).
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

STATUSES = {"approved", "conditional", "rejected", "unreviewed"}
KINDS = {"corpus", "evaluation"}
USE_KEYS = ("rag", "evaluation", "training", "redistribution")
USE_VALUES = {"yes", "conditional", "no"}
METHODS = {
    "official_page_fetched",
    "official_page_via_search_snippet",
    "dataset_card_via_search_snippet",
    "third_party_dataset_cards_via_search_snippet",
    "github_readme_and_dataset_card_via_search_snippet",
    "none",
}
ID_PATTERN = re.compile(r"[a-z][a-z0-9_]*")


def _is_iso_date(value):
    try:
        date.fromisoformat(value)
        return True
    except (TypeError, ValueError):
        return False


def _is_https_url(value):
    return isinstance(value, str) and value.startswith("https://") and " " not in value


def validate(registry):
    errors = []
    if registry.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if not _is_iso_date(registry.get("verified_on")):
        errors.append("verified_on must be an ISO date")
    sources = registry.get("sources")
    if not isinstance(sources, list) or not sources:
        return errors + ["sources must be a non-empty list"]

    seen = set()
    for index, source in enumerate(sources):
        sid = source.get("id") if isinstance(source, dict) else None
        where = f"source[{index}] ({sid})"
        if not isinstance(source, dict):
            errors.append(f"{where}: must be an object")
            continue
        if not isinstance(sid, str) or not ID_PATTERN.fullmatch(sid):
            errors.append(f"{where}: id must be snake_case")
        elif sid in seen:
            errors.append(f"{where}: duplicate id")
        seen.add(sid)

        for key in ("name", "publisher", "jurisdiction"):
            if not isinstance(source.get(key), str) or not source[key].strip():
                errors.append(f"{where}: {key} is required")
        kind, status = source.get("kind"), source.get("status")
        if kind not in KINDS:
            errors.append(f"{where}: kind must be one of {sorted(KINDS)}")
        if status not in STATUSES:
            errors.append(f"{where}: status must be one of {sorted(STATUSES)}")

        license_info = source.get("license")
        if not isinstance(license_info, dict):
            errors.append(f"{where}: license object is required")
            license_info = {}
        if not isinstance(license_info.get("name"), str) or not license_info["name"].strip():
            errors.append(f"{where}: license.name is required")
        verification = license_info.get("verification")
        if not isinstance(verification, dict):
            errors.append(f"{where}: license.verification is required")
            verification = {}
        if verification.get("method") not in METHODS:
            errors.append(f"{where}: license.verification.method must be one of {sorted(METHODS)}")
        if not _is_iso_date(verification.get("checked_on")):
            errors.append(f"{where}: license.verification.checked_on must be an ISO date")
        if not isinstance(verification.get("notes"), str) or not verification["notes"].strip():
            errors.append(f"{where}: license.verification.notes is required")
        if status != "unreviewed":
            if not _is_https_url(license_info.get("url")):
                errors.append(f"{where}: license.url must be an https URL unless status is unreviewed")
            if verification.get("method") == "none":
                errors.append(f"{where}: a reviewed source cannot have verification.method 'none'")

        allowed = source.get("allowed_uses")
        if not isinstance(allowed, dict) or set(allowed) != set(USE_KEYS):
            errors.append(f"{where}: allowed_uses must have exactly {list(USE_KEYS)}")
            allowed = {}
        for key in USE_KEYS:
            if allowed.get(key) not in USE_VALUES:
                errors.append(f"{where}: allowed_uses.{key} must be one of {sorted(USE_VALUES)}")

        if status in {"rejected", "unreviewed"} and any(v != "no" for v in allowed.values()):
            errors.append(f"{where}: {status} sources must have every allowed use set to 'no'")
        if kind == "evaluation" and allowed.get("training") != "no":
            errors.append(f"{where}: evaluation datasets must never be allowed for training")
        if kind == "evaluation" and allowed.get("rag") != "no":
            errors.append(f"{where}: evaluation datasets must not be used as a RAG corpus")

        uses_text = kind == "corpus" and status in {"approved", "conditional"} and allowed.get("rag") != "no"
        if uses_text:
            if not isinstance(source.get("attribution"), str) or not source["attribution"].strip():
                errors.append(f"{where}: usable corpus sources need an attribution string")
            if not isinstance(source.get("restrictions"), list) or not source["restrictions"]:
                errors.append(f"{where}: usable corpus sources need at least one restriction")
        if not isinstance(source.get("risks"), list) or not source["risks"]:
            errors.append(f"{where}: risks must be a non-empty list")
    return errors


def main(argv):
    path = Path(argv[1]) if len(argv) > 1 else Path("ml/data/source_registry.json")
    try:
        registry = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"ERROR: cannot read {path}: {error}", file=sys.stderr)
        return 1
    errors = validate(registry)
    if errors:
        print(f"{len(errors)} problem(s) in {path}:")
        for message in errors:
            print(f"  - {message}")
        return 1
    count = len(registry["sources"])
    print(f"OK: {count} sources in {path} are structurally valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
