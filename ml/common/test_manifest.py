import json
import random
import tempfile
import unittest
from pathlib import Path

from ml.common.manifest import (
    build_manifest,
    config_hash,
    package_versions,
    set_python_seed,
    write_manifest,
)


class ManifestTests(unittest.TestCase):
    def test_config_hash_ignores_key_order_but_detects_changes(self):
        self.assertEqual(config_hash({"a": 1, "b": [1, 2]}), config_hash({"b": [1, 2], "a": 1}))
        self.assertNotEqual(config_hash({"a": 1}), config_hash({"a": 2}))

    def test_package_versions_reports_missing_packages_as_none(self):
        versions = package_versions(["definitely-not-an-installed-package-xyz"])
        self.assertEqual(versions, {"definitely-not-an-installed-package-xyz": None})

    def test_manifest_has_the_required_fields(self):
        config = {"model": "demo", "max_tokens": 5}
        manifest = build_manifest(
            "demo-run", config, seed=7, dataset_versions={"corpus": "2026-11-03"}, notes="x"
        )
        for key in (
            "schema_version", "name", "created_utc", "git", "python", "platform",
            "packages", "seed", "config", "config_sha256", "dataset_versions", "notes",
        ):
            self.assertIn(key, manifest)
        self.assertEqual(manifest["config_sha256"], config_hash(config))
        self.assertEqual(manifest["seed"], 7)
        self.assertIn(manifest["git"]["uncommitted_changes"], (True, False, None))

    def test_write_manifest_round_trips_as_json(self):
        manifest = build_manifest("demo-run", {"k": "v"}, seed=1)
        with tempfile.TemporaryDirectory() as folder:
            path = write_manifest(manifest, Path(folder) / "nested" / "run1")
            self.assertEqual(path.name, "manifest.json")
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["name"], "demo-run")

    def test_python_seed_makes_random_repeatable(self):
        set_python_seed(123)
        first = [random.random() for _ in range(3)]
        set_python_seed(123)
        self.assertEqual(first, [random.random() for _ in range(3)])


if __name__ == "__main__":
    unittest.main()
