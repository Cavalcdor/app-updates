"""Validate public update metadata using only the Python standard library."""
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
RELEASE_FIELDS = {"enabled", "version", "build_number", "published_at", "notes"}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def read_json(path, max_size=65536):
    require(path.stat().st_size <= max_size, f"Oversized metadata: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict) and type(value.get("schema_version")) is int
            and value["schema_version"] == 1, f"Unsupported schema: {path}")
    return value


def slug(value):
    return isinstance(value, str) and SLUG.fullmatch(value) is not None


def text(value):
    return isinstance(value, str) and bool(value.strip())


def validate_release(release, path):
    require(isinstance(release, dict), f"Invalid release: {path}")
    require(type(release.get("enabled")) is bool, f"Invalid enabled flag: {path}")
    require(text(release.get("version")), f"Missing version: {path}")
    require(type(release.get("build_number")) is int and release["build_number"] > 0,
            f"Invalid build number: {path}")
    published = release.get("published_at")
    require(isinstance(published, str) and date.fromisoformat(published).isoformat() == published,
            f"Invalid date: {path}")
    notes = release.get("notes")
    require(isinstance(notes, list) and notes and all(text(n) for n in notes),
            f"Invalid notes: {path}")
    require(not any(k in release for k in ["download_url", "token", "password", "contact"]),
            f"Private distribution data in public file: {path}")


def validate_history(path, latest, identity):
    history = read_json(path, max_size=1048576)
    require(set(history) == {"schema_version", "app_id", "platform", "channel", "releases"},
            f"Unexpected history fields: {path}")
    for field, value in identity.items():
        require(history.get(field) == value, f"Mismatched history {field}: {path}")
    releases = history.get("releases")
    require(isinstance(releases, list) and releases, f"Missing release history: {path}")
    previous_build = None
    for release in releases:
        validate_release(release, path)
        require(RELEASE_FIELDS <= set(release) <= RELEASE_FIELDS | {"source"},
                f"Unexpected release history fields: {path}")
        require(release.get("source", "private-release") in ["private-release", "local-archive"],
                f"Invalid history source: {path}")
        build = release["build_number"]
        require(previous_build is None or build < previous_build,
                f"History builds must be unique and newest first: {path}")
        previous_build = build
    require({k: releases[0][k] for k in RELEASE_FIELDS} == {k: latest[k] for k in RELEASE_FIELDS},
            f"Latest manifest and history disagree: {path}")


def validate(root=ROOT):
    catalog = read_json(root / "catalog.json")
    categories = catalog.get("categories")
    apps = catalog.get("apps")
    require(isinstance(categories, list) and categories, "Missing categories")
    require(isinstance(apps, list) and apps, "Missing apps")
    category_ids = set()
    for category in categories:
        require(isinstance(category, dict) and slug(category.get("id"))
                and text(category.get("name")), "Invalid category")
        require(category["id"] not in category_ids, "Duplicate category")
        category_ids.add(category["id"])
    app_ids, expected = set(), {root / "catalog.json"}
    release_count = 0
    for app in apps:
        require(isinstance(app, dict) and slug(app.get("app_id")), "Invalid app ID")
        app_id = app["app_id"]
        require(app_id not in app_ids, f"Duplicate app: {app_id}")
        app_ids.add(app_id)
        require(text(app.get("name")) and text(app.get("description")), f"Missing app text: {app_id}")
        require(app.get("category") in category_ids, f"Unknown category: {app_id}")
        require(app.get("status") in ["active", "maintenance", "discontinued"], f"Invalid status: {app_id}")
        require(app.get("distribution") == "private", f"Public packages are not permitted: {app_id}")
        targets = app.get("targets")
        require(isinstance(targets, list) and targets, f"Missing targets: {app_id}")
        seen = set()
        for target in targets:
            require(isinstance(target, dict) and slug(target.get("platform"))
                    and slug(target.get("channel")), f"Invalid target: {app_id}")
            platform, channel = target["platform"], target["channel"]
            require((platform, channel) not in seen, f"Duplicate target: {app_id}")
            seen.add((platform, channel))
            path = root / "apps" / app_id / platform / (channel + ".json")
            expected.add(path)
            release = read_json(path)
            identity = {"app_id": app_id, "platform": platform, "channel": channel}
            for field, value in identity.items():
                require(release.get(field) == value, f"Mismatched {field}: {path}")
            validate_release(release, path)
            history_path = path.with_name(channel + ".history.json")
            expected.add(history_path)
            validate_history(history_path, release, identity)
            release_count += 1
    require(set(root.glob("**/*.json")) == expected, "Undeclared JSON files found")
    allowed = {"LICENSE", "README.md", "README.zh-CN.md", "catalog.json", ".gitignore", "scripts/validate.py", "tests/test_validate.py", ".github/workflows/validate.yml"}
    allowed.update(p.relative_to(root).as_posix() for p in expected)
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if not path.is_file() or any(part in [".git", "__pycache__"] for part in relative.parts):
            continue
        require(relative.as_posix() in allowed, f"Unexpected public file: {relative}")
    return len(apps), release_count


if __name__ == "__main__":
    try:
        apps, releases = validate()
        print(f"PASS: {apps} app(s), {releases} release manifest(s)")
    except (ValueError, KeyError, TypeError, OSError) as error:
        raise SystemExit(f"FAIL: {error}")
