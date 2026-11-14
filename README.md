[English](README.md) | [简体中文](README.zh-CN.md)

# App Updates

[![License](https://img.shields.io/badge/License-MIT-64748B?style=flat-square)](LICENSE)

![Format: JSON](https://img.shields.io/badge/Format-JSON-4B5563?style=flat-square) ![Validation: Python](https://img.shields.io/badge/Validation-Python-3776AB?style=flat-square) ![Installers: Private](https://img.shields.io/badge/Installers-Private-6B7280?style=flat-square)

A shared public update-information repository for games and software tools. It publishes application names, categories, versions and release notes. Installers, private source code, task packs, contact details and credentials are kept elsewhere.

## Applications

| Category | Application | Platform | Channel | Distribution |
| --- | --- | --- | --- | --- |
| Games | [Next Square](apps/next-square/android/stable.json) | Android | Stable | Private |
| Utilities | None registered | — | — | — |
| Productivity | None registered | — | — | — |
| Education | None registered | — | — | — |
| Media | None registered | — | — | — |

Register applications as needed; do not create placeholder products.

## Stable URLs and categories

- Application catalog: [`catalog.json`](catalog.json). Categories are maintained here.
- Next Square for Android, stable channel: [`apps/next-square/android/stable.json`](apps/next-square/android/stable.json).
- [Raw update JSON](https://raw.githubusercontent.com/Cavalcdor/app-updates/main/apps/next-square/android/stable.json).
- Release history: [`apps/next-square/android/stable.history.json`](apps/next-square/android/stable.history.json).

Each application has a permanent `app_id`. Update files follow `apps/<app_id>/<platform>/<channel>.json`; categories are not part of the path. Keep the ID and URL when renaming or recategorizing an application. Create files only for platforms and channels that actually ship.

## Schema v1

`catalog.json` contains `schema_version`, `categories` and `apps`. Each application declares its unique `app_id`, display name, category, summary, maintenance status, distribution method and platform/channel `targets`. Distribution is currently private for all applications: `distribution` is `private`.

Maintenance states are `active`, `maintenance` and `discontinued`. Retain catalog entries and version files for discontinued applications rather than deleting them.

| Update field | Meaning |
| --- | --- |
| `schema_version` | Currently `1`; an unknown schema must not be treated as “up to date” |
| `app_id`, `platform`, `channel` | Must match the client's configuration |
| `enabled` | `false` pauses recommendations without removing the URL |
| `version` | Human-readable version, not a string-comparison key |
| `build_number` | Strictly increasing positive integer within an app/platform/channel |
| `published_at` | Release date in `YYYY-MM-DD` format |
| `notes` | Array of plain-text release notes; no executable content |

Optional additions must remain compatible with v1 and retain existing field meanings. Notes should explain changes relevant to users upgrading, rather than listing internal build IDs alone.

## Version history

Each registered platform/channel has two files:

- `<channel>.json` is the compact latest-version manifest used by update checks; existing client URLs and schema remain unchanged.
- `<channel>.history.json` contains the release history for the same `app_id`, `platform` and `channel`, under a `releases` array and `schema_version: 1`.

Every history entry contains `enabled`, `version`, `build_number`, `published_at` and `notes`. Entries are ordered by strictly decreasing build number; gaps are permitted, duplicate build numbers are not. The first entry must match all five release fields in the latest manifest. Dates use the same `YYYY-MM-DD` format as the manifest.

The Next Square history contains 22 distinct Android versions verified from the private APK archive: v3.20.5–v3.20.15 and v3.20.20–v3.20.28, plus v3.21.0–v3.21.1. Nine correspond to private GitHub Releases; thirteen are local archived builds, including the v3.20.22 update-testing build. The generic latest APK is deduplicated by package version and build number. Each APK was checked for package identity, actual version/build and the original signing certificate. Windows executables belong to a separate platform and are not included in Android history.

The optional `source` field distinguishes `private-release` from `local-archive`; omitted values retain the original `private-release` meaning. For archived builds, `published_at` is the version date recorded in the source changelog, not a GitHub publication timestamp. Notes come from published metadata, verified Releases or the matching source changelog. No local machine paths, installer URLs or signing credentials are published.

The archived v3.20.10 APK is a rollback build with actual build number 111, later than v3.20.11 (109) and v3.20.12 (110). History therefore follows build order rather than version-name order. The superseded v3.20.11 and v3.20.12 rollback candidates are retained with `enabled: false`.

`enabled` records whether that entry has been withdrawn; `true` does not recommend installing an older build. Retain withdrawn entries with `enabled: false`. If the latest build is withdrawn, update its manifest and matching history entry together; never silently fall back to an older build.

History documents are limited to 1 MiB, while catalogs and latest manifests retain their 64 KiB limit. History fields are explicitly checked to prevent extra download or credential fields. This public history does not publish installers. The current game's in-app changelog remains bundled with the application; adding this file does not change installed clients.

## Client behavior

Check in the background on startup, at most once a day automatically. Users can disable automatic checks and check manually. Timeouts, invalid data and missing files must not appear as “up to date” or block normal use.

Offer an update only when identity fields match, `enabled=true`, and `build_number` exceeds the installed build. Never downgrade automatically. Remember “Later” per application, platform, channel and target build; manual checks can still display that version. Defer prompts during a game or a running tool task.

Use “Later” and “How to update” actions. For Next Square, the instructions are:

> Contact the publisher to obtain the latest installer.
>
> Install it over the existing app; uninstalling is unnecessary.

Other applications define their own installation instructions. Clients only read update information; they do not execute remote code or embed GitHub access tokens.

## Publishing

1. Build and test in the application's private repository.
2. Upload a private Release and verify the installer signature, version and checksum.
3. Update `<channel>.json` and prepend the same release to `<channel>.history.json` in the same commit, increasing `build_number` for the target. Preserve older entries.
4. Run `python3 -m unittest discover -s tests` and `python3 scripts/validate.py`. Check that no unreleased features, installers, download URLs or sensitive data were added.
5. Push this repository last, enabling client notifications only after the installer is ready.

For a faulty release, set `enabled=false`. Publish the fix with a higher build number; withdrawal must not downgrade newer installations.

Add one catalog entry and the appropriate version file for a new application. New platforms and preview channels require corresponding target declarations and files. Reuse this repository instead of creating a separate public update repository per app.

## Validation

```sh
python3 -m unittest discover -s tests
python3 scripts/validate.py
```

GitHub Actions validates schema, identity, catalog consistency and allowed file scope on pushes and pull requests. Build-number progression and installer readiness still require release-time checks. This repository provides version information; consult each application's release notes to determine whether its client already supports update checks.

## License and rights

Original code, documentation and update metadata in this repository are provided under the [MIT License](LICENSE). This permission does not license the applications listed in the catalog, their source code, installers, task packs, artwork or trademarks. Each application retains its own licensing and distribution terms.
