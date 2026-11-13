"""Validate public update metadata using only the Python standard library."""
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


def require(ok, message):
    if not ok:
        raise ValueError(message)


def read_json(path):
    require(path.stat().st_size <= 65536, f"Oversized metadata: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict) and type(value.get("schema_version")) is int
            and value["schema_version"] == 1, f"Unsupported schema: {path}")
    return value


def slug(value):
    return isinstance(value, str) and SLUG.fullmatch(value) is not None


def text(value):
    return isinstance(value, str) and bool(value.strip())


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
            for field, value in [("app_id", app_id), ("platform", platform), ("channel", channel)]:
                require(release.get(field) == value, f"Mismatched {field}: {path}")
            require(type(release.get("enabled")) is bool, f"Invalid enabled flag: {path}")
            require(text(release.get("version")), f"Missing version: {path}")
            require(type(release.get("build_number")) is int and release["build_number"] > 0, f"Invalid build number: {path}")
            published = release.get("published_at")
            require(isinstance(published, str) and date.fromisoformat(published).isoformat() == published, f"Invalid date: {path}")
            notes = release.get("notes")
            require(isinstance(notes, list) and notes and all(text(n) for n in notes), f"Invalid notes: {path}")
            require(not any(k in release for k in ["download_url", "token", "password", "contact"]), f"Private distribution data in public file: {path}")
    require(set(root.glob("**/*.json")) == expected, "Undeclared JSON files found")
    allowed = {"README.md", "README.zh-CN.md", "catalog.json", ".gitignore", "scripts/validate.py", ".github/workflows/validate.yml"}
    allowed.update(p.relative_to(root).as_posix() for p in expected)
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if not path.is_file() or any(part in [".git", "__pycache__"] for part in relative.parts):
            continue
        require(relative.as_posix() in allowed, f"Unexpected public file: {relative}")
    return len(apps), len(expected) - 1


if __name__ == "__main__":
    try:
        apps, releases = validate()
        print(f"PASS: {apps} app(s), {releases} release manifest(s)")
    except (ValueError, KeyError, TypeError, OSError) as error:
        raise SystemExit(f"FAIL: {error}")
