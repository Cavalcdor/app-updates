"""Regression checks for release-history consistency and public file boundaries."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate import validate


class HistoryValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.target = self.root / "apps/example/android"
        self.target.mkdir(parents=True)
        self.identity = {"schema_version": 1, "app_id": "example", "platform": "android", "channel": "stable"}
        self.latest = dict(self.identity, enabled=True, version="1.1", build_number=2,
                           published_at="2026-11-13", notes=["Example update."])
        self.history = dict(self.identity, releases=[
            {k: self.latest[k] for k in ["enabled", "version", "build_number", "published_at", "notes"]},
            {"enabled": True, "version": "1.0", "build_number": 1,
             "published_at": "2026-11-12", "notes": ["Initial release."]},
        ])
        catalog = {"schema_version": 1, "categories": [{"id": "games", "name": "Games"}], "apps": [{
            "app_id": "example", "name": "Example", "description": "Example app.",
            "category": "games", "status": "active", "distribution": "private",
            "targets": [{"platform": "android", "channel": "stable"}],
        }]}
        self.write(self.root / "catalog.json", catalog)
        self.save()

    def write(self, path, value):
        path.write_text(json.dumps(value), encoding="utf-8")

    def save(self):
        self.write(self.target / "stable.json", self.latest)
        self.write(self.target / "stable.history.json", self.history)

    def rejected(self):
        self.save()
        with self.assertRaises((ValueError, OSError)):
            validate(self.root)

    def test_valid_history(self):
        self.assertEqual(validate(self.root), (1, 1))

    def test_latest_must_match_all_release_fields(self):
        for field, value in [("version", "different"), ("build_number", 3),
                             ("published_at", "2026-11-14"), ("notes", ["Different."]),
                             ("enabled", False)]:
            with self.subTest(field=field):
                original = copy.deepcopy(self.history)
                self.history["releases"][0][field] = value
                self.rejected()
                self.history = original

    def test_duplicates_rejected(self):
        self.history["releases"].append(copy.deepcopy(self.history["releases"][-1]))
        self.rejected()

    def test_oldest_first_rejected(self):
        self.history["releases"].reverse()
        self.rejected()

    def test_identity_mismatch_rejected(self):
        for field, value in [("app_id", "other"), ("platform", "windows"), ("channel", "beta")]:
            with self.subTest(field=field):
                original = self.history[field]
                self.history[field] = value
                self.rejected()
                self.history[field] = original

    def test_unknown_or_private_history_fields_rejected(self):
        for field in ["download_url", "token", "password", "contact", "unexpected"]:
            for container in [self.history, self.history["releases"][1]]:
                with self.subTest(field=field, top_level=container is self.history):
                    container[field] = "example"
                    self.rejected()
                    del container[field]

    def test_invalid_old_records_rejected(self):
        for field, value in [("build_number", True), ("build_number", 0),
                             ("published_at", "2026-02-30"), ("enabled", "true"),
                             ("notes", []), ("notes", [""])]:
            with self.subTest(field=field, value=value):
                original = copy.deepcopy(self.history["releases"][1])
                self.history["releases"][1][field] = value
                self.rejected()
                self.history["releases"][1] = original

    def test_empty_history_rejected(self):
        self.history["releases"] = []
        self.rejected()

    def test_archive_and_release_sources_are_supported(self):
        self.history["releases"][0]["source"] = "private-release"
        self.history["releases"][1]["source"] = "local-archive"
        self.save()
        self.assertEqual(validate(self.root), (1, 1))

    def test_unknown_source_rejected(self):
        self.history["releases"][1]["source"] = "unverified"
        self.rejected()

    def test_rollback_version_names_follow_build_order(self):
        self.latest["version"] = "1.0"
        self.history["releases"][0]["version"] = "1.0"
        self.history["releases"][1]["version"] = "1.1"
        self.history["releases"][1]["source"] = "local-archive"
        self.history["releases"][1]["enabled"] = False
        self.save()
        self.assertEqual(validate(self.root), (1, 1))

    def test_history_required(self):
        (self.target / "stable.history.json").unlink()
        with self.assertRaises(OSError):
            validate(self.root)

    def test_withdrawn_latest_and_older_entry_retained(self):
        self.latest["enabled"] = False
        self.history["releases"][0]["enabled"] = False
        self.history["releases"][1]["enabled"] = False
        self.save()
        self.assertEqual(validate(self.root), (1, 1))

    def test_history_can_exceed_manifest_limit(self):
        self.history["releases"][1]["notes"] = ["x" * 70000]
        self.save()
        self.assertEqual(validate(self.root), (1, 1))
        self.latest["notes"] = ["x" * 70000]
        self.rejected()

    def test_history_size_is_bounded(self):
        self.history["releases"][1]["notes"] = ["x" * 1048576]
        self.rejected()

    def test_undeclared_json_and_installers_rejected(self):
        for name in ["extra.json", "installer.apk"]:
            with self.subTest(name=name):
                path = self.root / name
                path.write_text("{}", encoding="utf-8")
                with self.assertRaises(ValueError):
                    validate(self.root)
                path.unlink()


if __name__ == "__main__":
    unittest.main()
