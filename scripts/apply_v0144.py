from pathlib import Path

MAIN = Path("app/src/main/java/de/minimal/musicplayer/MainActivity.java")
GRADLE = Path("app/build.gradle")
WORKFLOW = Path(".github/workflows/build-debug-apk.yml")

main = MAIN.read_text(encoding="utf-8")
start = main.index("    private void handleBack() {")
end = main.index("    private void playCurrentListRandomly()", start)

replacement = '''    private void handleBack() {
        if (infoSettingsOpen) {
            infoSettingsOpen = false;
            selectTab(MODE_OTHER);
        } else if (playerOpen) {
            playerOpen = false;
            playerPanel.setVisibility(View.GONE);
            libraryList.setVisibility(View.VISIBLE);
            selectTab(libraryMode);
        } else if (playlistDetailOpen) {
            openPlaylistBrowser();
        } else if (playlistBrowserOpen) {
            selectTab(MODE_OTHER);
            refreshInsets();
        } else if (rlYearDetailOpen) {
            ArrayList<Song> rlSnapshot = new ArrayList<>(rlSongsForBrowser);
            resetGroupSearchUi();
            rlYearBrowserOpen = true;
            rlYearDetailOpen = false;
            openRlYearBrowser(rlSnapshot);
        } else if (rlYearBrowserOpen) {
            resetGroupSearchUi();
            selectTab(MODE_YEARS);
            refreshInsets();
        } else if (groupOpen) {
            resetGroupSearchUi();
            selectTab(libraryMode);
            refreshInsets();
        } else if (!TextUtils.isEmpty(searchQuery)) {
            if (searchInput != null) searchInput.setText("");
            searchQuery = "";
            hideSearchKeyboard();
            selectTab(libraryMode);
            refreshInsets();
        } else if (libraryMode == MODE_GENRES && "RL".equals(seasonCategory)) {
            setSeasonCategory("ANIME");
            refreshInsets();
        }
    }

    @Override
    public void onBackPressed() {
        boolean hasInternalBackTarget = infoSettingsOpen
                || playerOpen
                || playlistDetailOpen
                || playlistBrowserOpen
                || rlYearDetailOpen
                || rlYearBrowserOpen
                || groupOpen
                || !TextUtils.isEmpty(searchQuery)
                || (libraryMode == MODE_GENRES && "RL".equals(seasonCategory));
        if (hasInternalBackTarget) handleBack();
        else super.onBackPressed();
    }

'''

main = main[:start] + replacement + main[end:]
MAIN.write_text(main, encoding="utf-8")

gradle = GRADLE.read_text(encoding="utf-8")
gradle = gradle.replace("versionCode 21", "versionCode 22")
gradle = gradle.replace("versionName '0.14.3-debug'", "versionName '0.14.4-debug'")
if "versionCode 22" not in gradle or "versionName '0.14.4-debug'" not in gradle:
    raise RuntimeError("Could not bump version to v0.14.4")
GRADLE.write_text(gradle, encoding="utf-8")

workflow = WORKFLOW.read_text(encoding="utf-8")
workflow = workflow.replace("v0.14.3", "v0.14.4")
WORKFLOW.write_text(workflow, encoding="utf-8")

print("Applied v0.14.4 hierarchical back navigation patch")
