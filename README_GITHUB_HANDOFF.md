# MinimalMusicPlayer v0.12 — GitHub-ready handoff

Start with `00_UPLOAD_TO_GITHUB.md`.

Useful project continuity files:

- `PROJECT_CONTEXT.md` — complete current behavior/context
- `DO_NOT_BREAK.md` — invariants future edits must preserve
- `BUILD_VERIFIED.md` — what was actually verified in this handoff
- `GITHUB_BUILD.md` — how the automatic APK build works
- `NEXT_CHAT_PROMPT.md` — short prompt for a new chat
- `CHANGELOG_v0.12.md` — v0.12 changes

The current source implements:

- `GENRES` renamed to `SEASONS`
- new `JAHR` tab directly to its right
- grouping by actual Year metadata, with missing values under `Unbekannt`
- keyboard closes when a direct song search result is selected

The fixed debug key matches the installed/known-working v0.11 signing identity and must not be regenerated for subsequent debug updates.
