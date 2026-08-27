from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

main_path = ROOT / "app/src/main/java/de/minimal/musicplayer/MainActivity.java"
text = main_path.read_text(encoding="utf-8")
old = '''        if (!TextUtils.isEmpty(searchInput.getText())) {\n            applySearch(searchInput.getText().toString());\n            return;\n        }\n        searchQuery = "";\n'''
new = '''        // SearchMatcher trims/collapses whitespace. Use the normalized value here too,\n        // otherwise a raw whitespace-only EditText recursively bounces between\n        // selectTab() and applySearch() until the stack overflows.\n        String pendingSearch = searchInput == null ? ""\n                : SearchMatcher.normalizeQuery(searchInput.getText().toString());\n        if (!pendingSearch.isEmpty()) {\n            applySearch(pendingSearch);\n            return;\n        }\n        searchQuery = "";\n'''
if old not in text:
    raise SystemExit("selectTab search block not found")
text = text.replace(old, new, 1)
main_path.write_text(text, encoding="utf-8")

build_path = ROOT / "app/build.gradle"
build = build_path.read_text(encoding="utf-8")
build = build.replace("versionCode 20", "versionCode 21", 1)
build = build.replace("versionName '0.14.2-debug'", "versionName '0.14.3-debug'", 1)
if "versionCode 21" not in build or "0.14.3-debug" not in build:
    raise SystemExit("version patch failed")
build_path.write_text(build, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
readme = readme.replace("`0.14.2-debug` (`versionCode 20`)", "`0.14.3-debug` (`versionCode 21`)", 1)
readme_path.write_text(readme, encoding="utf-8")

workflow_path = ROOT / ".github/workflows/build-debug-apk.yml"
workflow_path.write_text('''name: Build Debug APK\n\non:\n  workflow_dispatch:\n  push:\n    branches:\n      - main\n      - master\n\npermissions:\n  contents: read\n\njobs:\n  build-debug-apk:\n    name: Build v0.14.3 Debug APK\n    runs-on: ubuntu-latest\n    timeout-minutes: 30\n\n    steps:\n      - name: Checkout repository\n        uses: actions/checkout@v4\n\n      - name: Set up JDK 17\n        uses: actions/setup-java@v4\n        with:\n          distribution: temurin\n          java-version: '17'\n\n      - name: Set up Android SDK\n        uses: android-actions/setup-android@v3\n\n      - name: Install Android 16 / API 36 build components\n        shell: bash\n        run: |\n          yes | sdkmanager --licenses >/dev/null || true\n          sdkmanager \\\n            "platform-tools" \\\n            "platforms;android-36" \\\n            "build-tools;36.0.0"\n\n      - name: Install Gradle 8.11.1\n        shell: bash\n        run: |\n          set -euo pipefail\n          GRADLE_VERSION="8.11.1"\n          curl -fsSL "https://services.gradle.org/distributions/gradle-${GRADLE_VERSION}-bin.zip" -o /tmp/gradle.zip\n          sudo mkdir -p /opt/gradle\n          sudo unzip -q /tmp/gradle.zip -d /opt/gradle\n          echo "/opt/gradle/gradle-${GRADLE_VERSION}/bin" >> "$GITHUB_PATH"\n\n      - name: Build debug APK\n        shell: bash\n        run: gradle clean assembleDebug --stacktrace --no-daemon\n\n      - name: Verify APK and signing certificate\n        shell: bash\n        env:\n          EXPECTED_CERT_SHA256: 63df019bdb5fbd06dee0cc7910cc81ed908dcd2d9ae9cfd8cc6e1d1c34404227\n        run: |\n          set -euo pipefail\n          APK="app/build/outputs/apk/debug/app-debug.apk"\n          test -f "$APK"\n          APKSIGNER="$(find "$ANDROID_HOME/build-tools" -type f -name apksigner | sort -V | tail -n 1)"\n          "$APKSIGNER" verify --verbose --print-certs "$APK" | tee apksigner-report.txt\n          ACTUAL_CERT_SHA256="$(sed -n 's/^.*certificate SHA-256 digest: //p' apksigner-report.txt | head -n 1 | tr '[:upper:]' '[:lower:]' | tr -d ':[:space:]')"\n          if [ "$ACTUAL_CERT_SHA256" != "$EXPECTED_CERT_SHA256" ]; then\n            echo "Signing certificate mismatch" >&2\n            echo "Expected: $EXPECTED_CERT_SHA256" >&2\n            echo "Actual:   $ACTUAL_CERT_SHA256" >&2\n            exit 1\n          fi\n\n      - name: Prepare downloadable files\n        shell: bash\n        run: |\n          set -euo pipefail\n          mkdir -p dist\n          cp app/build/outputs/apk/debug/app-debug.apk dist/MinimalMusicPlayer-v0.14.3-debug.apk\n          sha256sum dist/MinimalMusicPlayer-v0.14.3-debug.apk > dist/MinimalMusicPlayer-v0.14.3-debug.apk.sha256\n          cp apksigner-report.txt dist/apksigner-report.txt\n          {\n            echo "MinimalMusicPlayer v0.14.3 debug"\n            echo "Git commit: $GITHUB_SHA"\n            echo "Gradle: 8.11.1"\n            echo "AGP: 8.9.1"\n            echo "compileSdk: 36"\n            echo "targetSdk: 36"\n            echo "build-tools: 36.0.0"\n            echo "Signing cert SHA-256: 63df019bdb5fbd06dee0cc7910cc81ed908dcd2d9ae9cfd8cc6e1d1c34404227"\n          } > dist/build-info.txt\n\n      - name: Upload debug APK\n        uses: actions/upload-artifact@v4\n        with:\n          name: MinimalMusicPlayer-v0.14.3-debug\n          path: dist/\n          if-no-files-found: error\n          retention-days: 30\n''', encoding="utf-8")

# The bootstrap workflow only needs this script for the current run.
Path(__file__).unlink()
