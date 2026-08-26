# Prompt for a new ChatGPT chat

Upload this repository/project ZIP (or provide the GitHub repository if accessible) and say:

> Read `PROJECT_CONTEXT.md`, `DO_NOT_BREAK.md`, `BUILD_VERIFIED.md`, and the current source before changing anything. This is MinimalMusicPlayer v0.12. Preserve existing behavior unless my requested change requires otherwise. After code changes, keep `versionCode` increasing and let the existing GitHub Actions workflow build the update-compatible debug APK. Do not replace or regenerate `app/debug.keystore`.

Critical invariant: numeric-leading Season/Genre strings such as `2012_3.Summer`, `2026_2.Spring`, and `RL_2013` must remain exact text and must never be interpreted as numeric genre IDs.
