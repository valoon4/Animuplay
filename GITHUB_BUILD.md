# GitHub Actions build

Workflow: `.github/workflows/build-debug-apk.yml`

Triggers:

- every push to `main` or `master`
- manual `workflow_dispatch`

GitHub installs JDK 17, Android platform 35/build-tools 35.0.0 and Gradle 8.11.1, then runs:

```bash
gradle clean assembleDebug --stacktrace
```

The workflow then verifies the APK with Android `apksigner` and fails if the signing certificate is not:

```text
63df019bdb5fbd06dee0cc7910cc81ed908dcd2d9ae9cfd8cc6e1d1c34404227
```

That is the same certificate fingerprint as the known-working v0.11 APK.

The downloadable Actions artifact contains:

- `MinimalMusicPlayer-v0.12-debug.apk`
- `MinimalMusicPlayer-v0.12-debug.apk.sha256`
- `apksigner-report.txt`
- `build-info.txt`

No local Android SDK is needed when using GitHub Actions.
