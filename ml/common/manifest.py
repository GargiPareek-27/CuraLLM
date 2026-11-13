"""Reproducibility manifest for experiments. Standard library only.

Every experiment run should write one of these next to its results so that the
code version, environment, configuration, data versions and seed are on record.
"""
import hashlib
import json
import platform
import random
import subprocess
import sys
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path


def _git(arguments):
    """Run a git command; return stripped stdout, or None if git or the repository is unavailable."""
    try:
        result = subprocess.run(
            ["git", *arguments], capture_output=True, text=True, timeout=10, check=False
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def package_versions(names):
    """Installed version of each named package, or None when it is not installed."""
    versions = {}
    for name in names:
        try:
            versions[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            versions[name] = None
    return versions


def config_hash(config):
    """Stable SHA-256 of a configuration dict (independent of key order)."""
    raw = json.dumps(config, sort_keys=True, default=str, ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def set_python_seed(seed):
    """Seed Python's random module. Seed numpy, torch or others in the experiment itself."""
    random.seed(seed)


def build_manifest(name, config, *, seed=None, packages=(), dataset_versions=None, notes=None):
    status = _git(["status", "--porcelain"])
    return {
        "schema_version": 1,
        "name": name,
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "git": {
            "commit": _git(["rev-parse", "HEAD"]),
            "uncommitted_changes": None if status is None else bool(status),
        },
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "packages": package_versions(packages),
        "seed": seed,
        "config": config,
        "config_sha256": config_hash(config),
        "dataset_versions": dataset_versions or {},
        "notes": notes,
    }


def write_manifest(manifest, directory):
    """Write manifest.json into `directory` (created if needed) and return its path."""
    folder = Path(directory)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "manifest.json"
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True, default=str), encoding="utf-8")
    return path
