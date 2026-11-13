[English](README.md) | [简体中文](README.zh-CN.md)

# App Updates

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
3. Generate or fill in the update JSON from that release, increasing `build_number` for the target.
4. Run `python3 scripts/validate.py`. Check that no unreleased features, installers, download URLs or sensitive data were added.
5. Push this repository last, enabling client notifications only after the installer is ready.

For a faulty release, set `enabled=false`. Publish the fix with a higher build number; withdrawal must not downgrade newer installations.

Add one catalog entry and the appropriate version file for a new application. New platforms and preview channels require corresponding target declarations and files. Reuse this repository instead of creating a separate public update repository per app.

## Validation

```sh
python3 scripts/validate.py
```

GitHub Actions validates schema, identity, catalog consistency and allowed file scope on pushes and pull requests. Build-number progression and installer readiness still require release-time checks. This repository provides version information; consult each application's release notes to determine whether its client already supports update checks.
