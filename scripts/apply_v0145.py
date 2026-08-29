from pathlib import Path
import subprocess

BASE = "1ad564f1612ec4a2ddb94bb135d5cf4cbbb8ea85"
MAIN = Path("app/src/main/java/de/minimal/musicplayer/MainActivity.java")
GRADLE = Path("app/build.gradle")
MANIFEST = Path("app/src/main/AndroidManifest.xml")
WORKFLOW = Path(".github/workflows/build-debug-apk.yml")

# actions/checkout uses a shallow clone; fetch the exact clean v0.14.3 base explicitly.
subprocess.run(["git", "fetch", "--depth=1", "origin", BASE], check=True)


def old(path: str) -> str:
    return subprocess.check_output(["git", "show", f"{BASE}:{path}"], text=True)

# Full rollback to the last clean v0.14.3 source before applying the new approach.
main = old(str(MAIN))
gradle = old(str(GRADLE))
manifest = old(str(MANIFEST))
workflow = old(str(WORKFLOW))

# Explicitly opt in to the modern Android back callback path.
manifest = manifest.replace(
    '        android:theme="@style/AppTheme"\n        android:usesCleartextTraffic="false">',
    '        android:theme="@style/AppTheme"\n        android:enableOnBackInvokedCallback="true"\n        android:usesCleartextTraffic="false">'
)

# Register the API 33+ system back callback. Older Android versions keep onBackPressed().
needle = "        bindActions();\n        libraryList.setAdapter(adapter);"
replacement = "        bindActions();\n        registerSystemBackHandler();\n        libraryList.setAdapter(adapter);"
if needle not in main:
    raise SystemExit("Could not find onCreate registration point")
main = main.replace(needle, replacement, 1)

start = main.index("    private void handleBack() {")
end = main.index("    private void playCurrentListRandomly()", start)
new_back = '''    private void registerSystemBackHandler() {
        if (Build.VERSION.SDK_INT >= 33) {
            getOnBackInvokedDispatcher().registerOnBackInvokedCallback(
                    android.window.OnBackInvokedDispatcher.PRIORITY_DEFAULT,
                    this::handleBack);
        }
    }

    private void handleBack() {
        // Use the actually visible screen first. This avoids stale navigation flags
        // causing Android Back to exit while a detail/player screen is still open.
        if (infoSettingsPanel != null && infoSettingsPanel.getVisibility() == View.VISIBLE) {
            infoSettingsOpen = false;
            selectTab(MODE_OTHER);
            return;
        }
        if (playerPanel != null && playerPanel.getVisibility() == View.VISIBLE) {
            playerOpen = false;
            playerPanel.setVisibility(View.GONE);
            libraryList.setVisibility(View.VISIBLE);
            selectTab(libraryMode);
            return;
        }
        if (playlistDetailOpen) {
            openPlaylistBrowser();
            return;
        }
        if (playlistBrowserOpen) {
            selectTab(MODE_OTHER);
            refreshInsets();
            return;
        }
        if (rlYearDetailOpen) {
            ArrayList<Song> rlSnapshot = new ArrayList<>(rlSongsForBrowser);
            resetGroupSearchUi();
            rlYearBrowserOpen = true;
            rlYearDetailOpen = false;
            openRlYearBrowser(rlSnapshot);
            return;
        }
        if (rlYearBrowserOpen) {
            resetGroupSearchUi();
            selectTab(MODE_YEARS);
            refreshInsets();
            return;
        }
        if (groupOpen) {
            resetGroupSearchUi();
            selectTab(libraryMode);
            refreshInsets();
            return;
        }

        String rawSearch = searchInput == null ? "" : searchInput.getText().toString();
        if (!SearchMatcher.normalizeQuery(rawSearch).isEmpty()) {
            searchInput.setText("");
            searchQuery = "";
            hideSearchKeyboard();
            selectTab(libraryMode);
            refreshInsets();
            return;
        }

        if (libraryMode == MODE_GENRES && "RL".equals(seasonCategory)) {
            setSeasonCategory("ANIME");
            refreshInsets();
            return;
        }

        // Only a real top-level screen is allowed to close the activity.
        finish();
    }

    @Override
    public void onBackPressed() {
        handleBack();
    }

'''
main = main[:start] + new_back + main[end:]

# New installable test version, while the codebase itself is v0.14.3 + only this fix.
gradle = gradle.replace("versionCode 21", "versionCode 23")
gradle = gradle.replace("versionName '0.14.3-debug'", "versionName '0.14.5-debug'")
if "versionCode 23" not in gradle or "versionName '0.14.5-debug'" not in gradle:
    raise SystemExit("Version bump failed")

workflow = workflow.replace("v0.14.3", "v0.14.5")
workflow = workflow.replace("MinimalMusicPlayer-v0.14.3-debug", "MinimalMusicPlayer-v0.14.5-debug")

MAIN.write_text(main, encoding="utf-8")
GRADLE.write_text(gradle, encoding="utf-8")
MANIFEST.write_text(manifest, encoding="utf-8")
WORKFLOW.write_text(workflow, encoding="utf-8")
