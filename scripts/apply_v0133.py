from pathlib import Path

main = Path('app/src/main/java/de/minimal/musicplayer/MainActivity.java')
build = Path('app/build.gradle')

text = main.read_text(encoding='utf-8')

# Per-top-level-tab scroll memory. Detail lists intentionally do not use this.
text = text.replace(
    '    private final ArrayList<Song> rlSongsForBrowser = new ArrayList<>();\n',
    '    private final ArrayList<Song> rlSongsForBrowser = new ArrayList<>();\n'
    '    private final int[] topLevelFirstVisible = new int[5];\n'
    '    private final int[] topLevelTopOffset = new int[5];\n'
    '    private final boolean[] topLevelScrollSaved = new boolean[5];\n',
    1,
)

# Save the old top-level tab before switching to another top-level tab.
text = text.replace(
    '    private void selectTab(int mode) {\n        libraryMode = mode;\n',
    '    private void selectTab(int mode) {\n'
    '        int previousMode = libraryMode;\n'
    '        boolean leavingTopLevel = isTopLevelTabVisible();\n'
    '        if (leavingTopLevel && previousMode != mode) saveTopLevelScroll(previousMode);\n'
    '        libraryMode = mode;\n',
    1,
)

# Restore the chosen main tab after it has been rebuilt.
text = text.replace(
    '        adapter.notifyDataSetChanged();\n        updateAlphabetVisibility();\n        refreshInsets();\n    }\n\n    private void applySearch',
    '        adapter.notifyDataSetChanged();\n'
    '        updateAlphabetVisibility();\n'
    '        restoreTopLevelScroll(mode);\n'
    '        refreshInsets();\n'
    '    }\n\n'
    '    private boolean isTopLevelTabVisible() {\n'
    '        return libraryList != null\n'
    '                && libraryList.getVisibility() == View.VISIBLE\n'
    '                && tabBar != null && tabBar.getVisibility() == View.VISIBLE\n'
    '                && !groupOpen && !playerOpen && !playlistBrowserOpen && !playlistDetailOpen\n'
    '                && libraryMode >= MODE_SONGS && libraryMode <= MODE_YEARS\n'
    '                && TextUtils.isEmpty(searchQuery);\n'
    '    }\n\n'
    '    private void saveTopLevelScroll(int mode) {\n'
    '        if (mode < MODE_SONGS || mode > MODE_YEARS || libraryList == null) return;\n'
    '        int first = Math.max(0, libraryList.getFirstVisiblePosition());\n'
    '        View child = libraryList.getChildAt(0);\n'
    '        topLevelFirstVisible[mode] = first;\n'
    '        topLevelTopOffset[mode] = child == null ? 0 : child.getTop();\n'
    '        topLevelScrollSaved[mode] = true;\n'
    '    }\n\n'
    '    private void restoreTopLevelScroll(int mode) {\n'
    '        if (mode < MODE_SONGS || mode > MODE_YEARS || libraryList == null) return;\n'
    '        final int position = topLevelScrollSaved[mode] ? topLevelFirstVisible[mode] : 0;\n'
    '        final int offset = topLevelScrollSaved[mode] ? topLevelTopOffset[mode] : 0;\n'
    '        libraryList.post(() -> {\n'
    '            if (groupOpen || playerOpen || libraryMode != mode) return;\n'
    '            libraryList.setSelectionFromTop(Math.max(0, position), offset);\n'
    '            libraryList.post(this::clearLibraryHighlight);\n'
    '        });\n'
    '    }\n\n'
    '    private void clearLibraryHighlight() {\n'
    '        if (libraryList == null) return;\n'
    '        libraryList.clearChoices();\n'
    '        libraryList.setPressed(false);\n'
    '        libraryList.clearFocus();\n'
    '        for (int i = 0; i < libraryList.getChildCount(); i++) {\n'
    '            View child = libraryList.getChildAt(i);\n'
    '            if (child == null) continue;\n'
    '            child.setPressed(false);\n'
    '            child.setSelected(false);\n'
    '            child.setActivated(false);\n'
    '            child.clearFocus();\n'
    '        }\n'
    '        libraryList.setSelection(ListView.INVALID_POSITION);\n'
    '        libraryList.invalidate();\n'
    '    }\n\n'
    '    private void applySearch',
    1,
)

# Preserve the current top-level scroll before entering a group.
text = text.replace(
    '    private void openGroup(GroupRow group) {\n        if (group.playlistGroup && group.songs.isEmpty()) {',
    '    private void openGroup(GroupRow group) {\n'
    '        if (isTopLevelTabVisible()) saveTopLevelScroll(libraryMode);\n'
    '        if (group.playlistGroup && group.songs.isEmpty()) {',
    1,
)

# Player opened from a main tab should also return to the same main-tab position.
text = text.replace(
    '    private void openPlayer() {\n        if (currentSong == null) return;\n        playerOpen = true;',
    '    private void openPlayer() {\n'
    '        if (currentSong == null) return;\n'
    '        if (isTopLevelTabVisible()) saveTopLevelScroll(libraryMode);\n'
    '        playerOpen = true;',
    1,
)

# Every detail/browser list starts at the top, but main tabs are restored separately.
text = text.replace(
    '        titleText.setText("Playlists");\n        adapter.notifyDataSetChanged();\n        refreshInsets();',
    '        titleText.setText("Playlists");\n        adapter.notifyDataSetChanged();\n        scrollLibraryToTop();\n        refreshInsets();',
    1,
)
text = text.replace(
    '        titleText.setText(title);\n        adapter.notifyDataSetChanged();\n        refreshInsets();',
    '        titleText.setText(title);\n        adapter.notifyDataSetChanged();\n        scrollLibraryToTop();\n        refreshInsets();',
    1,
)

# Detail top helper also clears stale focus/selection highlight after layout.
text = text.replace(
    '    private void scrollLibraryToTop() {\n        libraryList.post(() -> libraryList.setSelection(0));\n    }',
    '    private void scrollLibraryToTop() {\n'
    '        libraryList.post(() -> {\n'
    '            libraryList.setSelectionFromTop(0, 0);\n'
    '            libraryList.post(this::clearLibraryHighlight);\n'
    '        });\n'
    '    }',
    1,
)

main.write_text(text, encoding='utf-8')

b = build.read_text(encoding='utf-8')
b = b.replace('versionCode 16', 'versionCode 17')
b = b.replace("versionName '0.13.2-debug'", "versionName '0.13.3-debug'")
build.write_text(b, encoding='utf-8')
