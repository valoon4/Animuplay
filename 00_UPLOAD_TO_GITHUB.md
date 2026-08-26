# 00 — Upload to GitHub

This folder is intentionally prepared so the user can upload/push it to a **private GitHub repository** and let GitHub Actions build the APK.

## Fastest path

1. Create a new **private** GitHub repository.
2. Upload/push **all files and folders from this project root**.
3. Make sure the default branch is `main` (or `master`).
4. Open **Actions → Build Debug APK**.
5. Either wait for the push build or press **Run workflow**.
6. Open the successful workflow run and download the artifact **MinimalMusicPlayer-v0.12-debug**.
7. Inside the artifact is `MinimalMusicPlayer-v0.12-debug.apk`.

No GitHub Secrets are required for this debug build. The fixed test-only debug keystore is deliberately part of this private project so the generated APK keeps the same Android signing identity as v0.11.

## Important security note

`app/debug.keystore` is **test/debug signing material only**. Do not use it for a Play Store/release build. Because possession of this key allows signing updates for this debug application ID, keep the repository private unless you no longer care about that debug update identity.
