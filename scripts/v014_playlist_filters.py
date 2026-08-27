from pathlib import Path
p=Path('app/src/main/java/de/minimal/musicplayer/MainActivity.java')
s=p.read_text()
def r(a,b,n):
    global s
    if a not in s: raise SystemExit('missing '+n)
    s=s.replace(a,b,1)
r('''        groupUsesTrackNumbers = group.albumGroup;
        groupSearchEnabled = !group.playlistGroup && !group.albumGroup
                && (libraryMode == MODE_GENRES || libraryMode == MODE_YEARS);
        groupTypeFiltersEnabled = groupSearchEnabled
                && libraryMode == MODE_GENRES && leadingYear(group.name) >= 0;
''','''        groupUsesTrackNumbers = group.albumGroup;
        groupSearchEnabled = !group.playlistGroup && !group.albumGroup
                && (libraryMode == MODE_GENRES || libraryMode == MODE_YEARS);
        boolean numericAnimeSeason = groupSearchEnabled
                && libraryMode == MODE_GENRES && leadingYear(group.name) >= 0;
        boolean numericPlaylist = group.playlistGroup && startsWithDigit(group.name);
        groupTypeFiltersEnabled = numericAnimeSeason || numericPlaylist;
''','enable playlist filters')
r('''        groupBaseSongs.clear();
        groupBaseSongs.addAll(group.songs);
        if (groupSearchEnabled) sortSongsByAlbum(groupBaseSongs);
''','''        groupBaseSongs.clear();
        groupBaseSongs.addAll(group.songs);
        if (groupSearchEnabled && !group.playlistGroup) sortSongsByAlbum(groupBaseSongs);
''','preserve playlist order')
r('''        if (groupSearchEnabled) {
            searchInput.setText("");
            searchInput.setHint("In dieser Gruppe suchen");
            searchRow.setVisibility(View.VISIBLE);
            groupFilterRow.setVisibility(groupTypeFiltersEnabled ? View.VISIBLE : View.GONE);
            if (groupTypeFiltersEnabled) updateGroupFilterButtons();
        } else {
            searchRow.setVisibility(View.GONE);
            groupFilterRow.setVisibility(View.GONE);
        }
''','''        if (groupSearchEnabled) {
            searchInput.setText("");
            searchInput.setHint("In dieser Gruppe suchen");
            searchRow.setVisibility(View.VISIBLE);
        } else {
            searchRow.setVisibility(View.GONE);
        }
        groupFilterRow.setVisibility(groupTypeFiltersEnabled ? View.VISIBLE : View.GONE);
        if (groupTypeFiltersEnabled) updateGroupFilterButtons();
''','filter row visibility')
r('''    private void toggleGroupTypeFilter(String type) {
        if (!groupSearchEnabled || !groupTypeFiltersEnabled) return;
        groupTypeFilter = type.equals(groupTypeFilter) ? "" : type;
        updateGroupFilterButtons();
        applyGroupSearchAndFilter(SearchMatcher.normalizeQuery(searchInput.getText().toString()));
    }
''','''    private void toggleGroupTypeFilter(String type) {
        if (!groupTypeFiltersEnabled) return;
        groupTypeFilter = type.equals(groupTypeFilter) ? "" : type;
        updateGroupFilterButtons();
        String query = groupSearchEnabled ? SearchMatcher.normalizeQuery(searchInput.getText().toString()) : "";
        applyGroupSearchAndFilter(query);
    }
''','toggle')
r('''    private void applyGroupSearchAndFilter(String query) {
        if (!groupSearchEnabled) return;
''','''    private void applyGroupSearchAndFilter(String query) {
        if (!groupSearchEnabled && !groupTypeFiltersEnabled) return;
''','apply filter without search')
r('''        sortSongsByAlbum(visibleSongs);
        randomPlayButton.setVisibility(visibleSongs.isEmpty() ? View.GONE : View.VISIBLE);
''','''        if (!playlistDetailOpen) sortSongsByAlbum(visibleSongs);
        randomPlayButton.setVisibility(visibleSongs.isEmpty() ? View.GONE : View.VISIBLE);
''','filtered playlist order')
needle='    private static boolean albumMatchesType(Song song, String type) {\n'
add='''    private static boolean startsWithDigit(String value) {
        return value != null && !value.isEmpty() && Character.isDigit(value.charAt(0));
    }

'''
r(needle,add+needle,'digit helper')
p.write_text(s)
