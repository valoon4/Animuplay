# Build verification status

## Verified in this handoff environment

- Complete Android project structure is present.
- `app/` source/resources are present.
- `gradlew`, `gradlew.bat`, `gradle/wrapper/gradle-wrapper.jar` and wrapper properties are present.
- Project configuration targets:
  - JDK/Java compatibility: 17
  - Gradle: 8.11.1
  - Android Gradle Plugin: 8.9.1
  - compileSdk: 35
  - targetSdk: 35
  - minSdk: 24
  - versionCode: 12
  - versionName: `0.12.0-debug`
- v0.12 source contains the requested `SEASONS` and `JAHR` tabs.
- Year extraction uses Android `MediaMetadataRetriever.METADATA_KEY_YEAR`.
- Search-song selection contains keyboard hiding via `InputMethodManager.hideSoftInputFromWindow(...)`.
- The included `app/debug.keystore` certificate SHA-256 is:
  `63df019bdb5fbd06dee0cc7910cc81ed908dcd2d9ae9cfd8cc6e1d1c34404227`
- The known-working v0.11 APK certificate SHA-256 is the same value.

## Not locally executed here

A full Android `assembleDebug` build of v0.12 was **not** executed in this handoff sandbox because its local Android/Gradle toolchain is unavailable. This package therefore does not falsely claim a local v0.12 APK build.

The GitHub Actions workflow is specifically included to perform that clean build on GitHub-hosted runners and to verify the resulting APK signing certificate before exposing the artifact.
