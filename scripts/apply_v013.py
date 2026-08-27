from pathlib import Path

MAIN = Path('app/src/main/java/de/minimal/musicplayer/MainActivity.java')
BUILD = Path('app/build.gradle')


def replace_once(text, old, new, label):
    if new in text:
        print(f'{label}: already applied')
        return text
    if old not in text:
        raise SystemExit(f'{label}: expected source fragment not found')
    print(f'{label}: applied')
    return text.replace(old, new, 1)


def replace_method(text, signature, next_signature, new_body, label):
    start = text.find(signature)
    if start < 0:
        if new_body.strip() in text:
            print(f'{label}: already applied')
            return text
        raise SystemExit(f'{label}: method start not found: {signature}')
    end = text.find(next_signature, start)
    if end < 0:
        raise SystemExit(f'{label}: next method not found: {next_signature}')
    current = text[start:end].strip()
    if current == new_body.strip():
        print(f'{label}: already applied')
        return text
    print(f'{label}: replaced')
    return text[:start] + new_body.rstrip() + '\n\n' + text[end:]


text = MAIN.read_text(encoding='utf-8')

text = replace_once(
    text,
    '''    private final ArrayList<ImportedPlaylist> importedPlaylists = new ArrayList<>();
    private final HashMap<String, Integer> playCounts = new HashMap<>();''',
    '''    private final ArrayList<ImportedPlaylist> importedPlaylists = new ArrayList<>();
    private final HashMap<String, Integer> playCounts = new HashMap<>();
    private final ArrayList<Song> groupBaseSongs = new ArrayList<>();
    private final ArrayList<Song> rlSongsForBrowser = new ArrayList<>();''',
    'group state lists')

text = replace_once(
    text,
    '''    private LinearLayout tabBar;
    private LinearLayout searchRow;
    private LinearLayout miniPlayer;''',
    '''    private LinearLayout tabBar;
    private LinearLayout searchRow;
    private LinearLayout groupFilterRow;
    private LinearLayout miniPlayer;''',
    'group filter row field')

text = replace_once(
    text,
    '''    private Button playlistsButton;
    private Button clearSearchButton;
    private EditText searchInput;''',
    '''    private Button playlistsButton;
    private Button clearSearchButton;
    private Button groupOpFilterButton;
    private Button groupEdFilterButton;
    private EditText searchInput;''',
    'group filter button fields')

text = replace_once(
    text,
    '''    private boolean playlistDetailOpen;
    private boolean playlistScanCompleted;
    private boolean playCountedThisCycle;''',
    '''    private boolean playlistDetailOpen;
    private boolean playlistScanCompleted;
    private boolean groupSearchEnabled;
    private boolean rlYearBrowserOpen;
    private boolean rlYearDetailOpen;
    private boolean playCountedThisCycle;''',
    'group navigation booleans')

text = replace_once(
    text,
    '''    private int lastPlaybackPositionMs;
    private String searchQuery = "";
    private Uri currentTreeUri;''',
    '''    private int lastPlaybackPositionMs;
    private String searchQuery = "";
    private String groupTypeFilter = "";
    private String groupTitle = "";
    private Uri currentTreeUri;''',
    'group filter strings')

text = replace_once(
    text,
    '''        setContentView(R.layout.activity_main);
        bindViews();
        repeatOne = getSharedPreferences(PREFS, MODE_PRIVATE).getBoolean(PREF_REPEAT_ONE, false);''',
    '''        setContentView(R.layout.activity_main);
        bindViews();
        initializeGroupFilterRow();
        repeatOne = getSharedPreferences(PREFS, MODE_PRIVATE).getBoolean(PREF_REPEAT_ONE, false);''',
    'initialize group filter row')

text = replace_once(
    text,
    '''        currentTime = findViewById(R.id.currentTime);
        totalTime = findViewById(R.id.totalTime);
    }

    private void applySystemInsets() {''',
    '''        currentTime = findViewById(R.id.currentTime);
        totalTime = findViewById(R.id.totalTime);
    }

    private void initializeGroupFilterRow() {
        groupFilterRow = new LinearLayout(this);
        groupFilterRow.setOrientation(LinearLayout.HORIZONTAL);
        groupFilterRow.setGravity(Gravity.CENTER_VERTICAL);
        groupFilterRow.setVisibility(View.GONE);

        groupOpFilterButton = makeGroupFilterButton("OP");
        groupEdFilterButton = makeGroupFilterButton("ED");
        groupFilterRow.addView(groupOpFilterButton,
                new LinearLayout.LayoutParams(0, dp(44), 1f));
        LinearLayout.LayoutParams edParams = new LinearLayout.LayoutParams(0, dp(44), 1f);
        edParams.setMarginStart(dp(6));
        groupFilterRow.addView(groupEdFilterButton, edParams);

        LinearLayout.LayoutParams rowParams = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, dp(44));
        rowParams.setMargins(dp(12), dp(4), dp(12), dp(2));
        int searchIndex = rootLayout.indexOfChild(searchRow);
        rootLayout.addView(groupFilterRow, Math.max(0, searchIndex + 1), rowParams);
    }

    private Button makeGroupFilterButton(String label) {
        Button button = new Button(this);
        button.setText(label);
        button.setTextSize(14f);
        button.setTextColor(getColor(R.color.text_secondary));
        button.setTypeface(android.graphics.Typeface.DEFAULT, android.graphics.Typeface.BOLD);
        button.setBackgroundResource(R.drawable.rounded_surface);
        button.setPadding(0, 0, 0, 0);
        return button;
    }

    private void applySystemInsets() {''',
    'dynamic OP/ED filter UI')

text = replace_once(
    text,
    '''        backButton.setOnClickListener(v -> handleBack());
        clearSearchButton.setOnClickListener(v -> searchInput.setText(""));
        alphabetIndex.setOnLetterSelectedListener(this::jumpToLetter);''',
    '''        backButton.setOnClickListener(v -> handleBack());
        clearSearchButton.setOnClickListener(v -> searchInput.setText(""));
        groupOpFilterButton.setOnClickListener(v -> toggleGroupTypeFilter("OP"));
        groupEdFilterButton.setOnClickListener(v -> toggleGroupTypeFilter("ED"));
        alphabetIndex.setOnLetterSelectedListener(this::jumpToLetter);''',
    'OP/ED click actions')

text = replace_once(
    text,
    '''        libraryMode = mode;
        groupOpen = false;
        groupUsesTrackNumbers = false;
        showPlayCounts = false;
        playlistBrowserOpen = false;
        playlistDetailOpen = false;
        playerOpen = false;''',
    '''        libraryMode = mode;
        groupOpen = false;
        groupUsesTrackNumbers = false;
        showPlayCounts = false;
        playlistBrowserOpen = false;
        playlistDetailOpen = false;
        groupSearchEnabled = false;
        groupTypeFilter = "";
        groupTitle = "";
        groupBaseSongs.clear();
        rlYearBrowserOpen = false;
        rlYearDetailOpen = false;
        rlSongsForBrowser.clear();
        if (groupFilterRow != null) groupFilterRow.setVisibility(View.GONE);
        if (searchInput != null) searchInput.setHint("Titel, Interpret oder Album suchen");
        playerOpen = false;''',
    'reset group state on tab selection')

text = replace_once(
    text,
    '''    private void applySearch(String rawQuery) {
        String query = SearchMatcher.normalizeQuery(rawQuery);
        searchQuery = query;
        if (libraryMode == MODE_OTHER || groupOpen || playerOpen) return;''',
    '''    private void applySearch(String rawQuery) {
        String query = SearchMatcher.normalizeQuery(rawQuery);
        searchQuery = query;
        if (groupOpen && groupSearchEnabled && !playerOpen) {
            applyGroupSearchAndFilter(query);
            return;
        }
        if (libraryMode == MODE_OTHER || groupOpen || playerOpen) return;''',
    'group-local search branch')

text = replace_once(
    text,
    '''            ArrayList<Song> songs = entry.getValue();
            if (albums) sortAlbumTracks(songs); else sortSongsByTitle(songs);
            result.add(new GroupRow(entry.getKey(), songs, albums));
        }
        result.sort((a, b) -> a.name.compareToIgnoreCase(b.name));
        return result;''',
    '''            ArrayList<Song> songs = entry.getValue();
            if (albums) sortAlbumTracks(songs); else sortSongsByAlbum(songs);
            result.add(new GroupRow(entry.getKey(), songs, albums));
        }
        if (albums) {
            result.sort((a, b) -> a.name.compareToIgnoreCase(b.name));
        } else {
            result.sort((a, b) -> compareNewestFirst(a.name, b.name));
        }
        return result;''',
    'season ordering and album sorting')

new_year_methods = '''    private List<GroupRow> buildYearGroups() {
        ArrayList<Song> rlSongs = new ArrayList<>();
        ArrayList<Song> regularSongs = new ArrayList<>();
        for (Song song : allSongs) {
            if (isRlSong(song)) rlSongs.add(song);
            else regularSongs.add(song);
        }

        ArrayList<GroupRow> result = new ArrayList<>(buildYearGroupsForSongs(regularSongs));
        if (!rlSongs.isEmpty()) {
            sortSongsByAlbum(rlSongs);
            result.add(0, new GroupRow("RL", rlSongs, false));
        }
        return result;
    }

    private List<GroupRow> buildYearGroupsForSongs(List<Song> source) {
        LinkedHashMap<String, ArrayList<Song>> groups = new LinkedHashMap<>();
        for (Song song : source) {
            String year = valueOr(song.year, "Unbekannt");
            groups.computeIfAbsent(year, key -> new ArrayList<>()).add(song);
        }

        ArrayList<GroupRow> result = new ArrayList<>();
        for (Map.Entry<String, ArrayList<Song>> entry : groups.entrySet()) {
            ArrayList<Song> songs = entry.getValue();
            sortSongsByAlbum(songs);
            result.add(new GroupRow(entry.getKey(), songs, false));
        }
        result.sort((left, right) -> compareNewestFirst(left.name, right.name));
        return result;
    }

    private static int compareNewestFirst(String left, String right) {
        boolean leftUnknown = "Unbekannt".equalsIgnoreCase(left);
        boolean rightUnknown = "Unbekannt".equalsIgnoreCase(right);
        if (leftUnknown != rightUnknown) return leftUnknown ? 1 : -1;
        try {
            return Integer.compare(Integer.parseInt(right), Integer.parseInt(left));
        } catch (NumberFormatException ignored) {
            return right.compareToIgnoreCase(left);
        }
    }

    private boolean isRlSong(Song song) {
        if (song == null || song.uri == null || currentTreeUri == null) return false;
        try {
            String rootId = DocumentsContract.getTreeDocumentId(currentTreeUri);
            String documentId = DocumentsContract.getDocumentId(song.uri);
            String relative = documentId;
            if (!TextUtils.isEmpty(rootId) && relative.startsWith(rootId)) {
                relative = relative.substring(rootId.length());
            }
            relative = relative.replace('\\\\', '/');
            while (relative.startsWith("/") || relative.startsWith(":")) {
                relative = relative.substring(1);
            }
            return relative.toLowerCase(Locale.ROOT).startsWith("songs/");
        } catch (RuntimeException ignored) {
            String decoded = Uri.decode(song.uri.toString()).replace('\\\\', '/').toLowerCase(Locale.ROOT);
            return decoded.contains("/songs/");
        }
    }'''
text = replace_method(
    text,
    '    private List<GroupRow> buildYearGroups() {',
    '    private void openGroup(GroupRow group) {',
    new_year_methods,
    'RL year hierarchy and newest-first years')

new_open_group = '''    private void openGroup(GroupRow group) {
        if (group.playlistGroup && group.songs.isEmpty()) {
            Toast.makeText(this, "In dieser Playlist wurde kein Titel im Musikordner gefunden.",
                    Toast.LENGTH_LONG).show();
            return;
        }
        if (libraryMode == MODE_YEARS && !rlYearBrowserOpen
                && "RL".equalsIgnoreCase(group.name)) {
            openRlYearBrowser(group.songs);
            return;
        }

        boolean fromRlYearBrowser = libraryMode == MODE_YEARS
                && rlYearBrowserOpen && !rlYearDetailOpen;
        groupOpen = true;
        rlYearDetailOpen = fromRlYearBrowser;
        playlistDetailOpen = group.playlistGroup;
        playlistBrowserOpen = false;
        showPlayCounts = false;
        groupUsesTrackNumbers = group.albumGroup;
        groupSearchEnabled = !group.playlistGroup && !group.albumGroup
                && (libraryMode == MODE_GENRES || libraryMode == MODE_YEARS);
        groupTypeFilter = "";
        groupTitle = group.name;
        groupBaseSongs.clear();
        groupBaseSongs.addAll(group.songs);
        if (groupSearchEnabled) sortSongsByAlbum(groupBaseSongs);

        visibleGroups.clear();
        visibleSongs.clear();
        visibleSongs.addAll(groupBaseSongs);
        tabBar.setVisibility(View.GONE);
        alphabetIndex.setVisibility(View.GONE);
        otherPanel.setVisibility(View.GONE);
        if (groupSearchEnabled) {
            searchInput.setText("");
            searchInput.setHint("In dieser Gruppe suchen");
            searchRow.setVisibility(View.VISIBLE);
            groupFilterRow.setVisibility(View.VISIBLE);
            updateGroupFilterButtons();
        } else {
            searchRow.setVisibility(View.GONE);
            groupFilterRow.setVisibility(View.GONE);
        }
        randomPlayButton.setVisibility(visibleSongs.isEmpty() ? View.GONE : View.VISIBLE);
        backButton.setVisibility(View.VISIBLE);
        titleText.setText(group.name);
        adapter.notifyDataSetChanged();
        scrollLibraryToTop();
        refreshInsets();
    }

    private void openRlYearBrowser(List<Song> songs) {
        resetGroupSearchUi();
        groupOpen = true;
        rlYearBrowserOpen = true;
        rlYearDetailOpen = false;
        playlistBrowserOpen = false;
        playlistDetailOpen = false;
        showPlayCounts = false;
        groupUsesTrackNumbers = false;
        rlSongsForBrowser.clear();
        rlSongsForBrowser.addAll(songs);
        visibleSongs.clear();
        visibleGroups.clear();
        visibleGroups.addAll(buildYearGroupsForSongs(rlSongsForBrowser));
        tabBar.setVisibility(View.GONE);
        searchRow.setVisibility(View.GONE);
        groupFilterRow.setVisibility(View.GONE);
        alphabetIndex.setVisibility(View.GONE);
        otherPanel.setVisibility(View.GONE);
        randomPlayButton.setVisibility(View.GONE);
        backButton.setVisibility(View.VISIBLE);
        titleText.setText("RL");
        adapter.notifyDataSetChanged();
        scrollLibraryToTop();
        refreshInsets();
    }

    private void toggleGroupTypeFilter(String type) {
        if (!groupSearchEnabled) return;
        groupTypeFilter = type.equals(groupTypeFilter) ? "" : type;
        updateGroupFilterButtons();
        applyGroupSearchAndFilter(SearchMatcher.normalizeQuery(searchInput.getText().toString()));
    }

    private void updateGroupFilterButtons() {
        styleGroupFilterButton(groupOpFilterButton, "OP".equals(groupTypeFilter));
        styleGroupFilterButton(groupEdFilterButton, "ED".equals(groupTypeFilter));
    }

    private void styleGroupFilterButton(Button button, boolean selected) {
        if (button == null) return;
        button.setTextColor(getColor(selected ? R.color.accent : R.color.text_secondary));
        button.setBackgroundResource(selected ? R.drawable.tab_selected : R.drawable.rounded_surface);
    }

    private void applyGroupSearchAndFilter(String query) {
        if (!groupSearchEnabled) return;
        visibleGroups.clear();
        visibleSongs.clear();
        for (Song song : groupBaseSongs) {
            if (!TextUtils.isEmpty(groupTypeFilter)
                    && !albumMatchesType(song, groupTypeFilter)) continue;
            if (!query.isEmpty()
                    && !SearchMatcher.contains(song.title, query)
                    && !SearchMatcher.contains(song.artist, query)
                    && !SearchMatcher.contains(song.album, query)) continue;
            visibleSongs.add(song);
        }
        sortSongsByAlbum(visibleSongs);
        randomPlayButton.setVisibility(visibleSongs.isEmpty() ? View.GONE : View.VISIBLE);
        int shown = visibleSongs.size();
        int total = groupBaseSongs.size();
        titleText.setText((query.isEmpty() && TextUtils.isEmpty(groupTypeFilter))
                ? groupTitle : groupTitle + " · " + shown + "/" + total);
        adapter.notifyDataSetChanged();
        scrollLibraryToTop();
    }

    private static boolean albumMatchesType(Song song, String type) {
        if (song == null || TextUtils.isEmpty(song.album) || TextUtils.isEmpty(type)) return false;
        String album = SearchMatcher.normalize(song.album).replaceAll("[^a-z0-9]+", " ").trim();
        String padded = " " + album + " ";
        return padded.contains(" " + type.toLowerCase(Locale.ROOT) + " ");
    }

    private void resetGroupSearchUi() {
        groupSearchEnabled = false;
        groupTypeFilter = "";
        groupTitle = "";
        groupBaseSongs.clear();
        searchQuery = "";
        mainHandler.removeCallbacks(delayedSearch);
        if (searchInput != null) {
            searchInput.setText("");
            searchInput.setHint("Titel, Interpret oder Album suchen");
        }
        if (groupFilterRow != null) groupFilterRow.setVisibility(View.GONE);
    }

    private void scrollLibraryToTop() {
        libraryList.post(() -> libraryList.setSelection(0));
    }'''
text = replace_method(
    text,
    '    private void openGroup(GroupRow group) {',
    '    private void openSearchGroup(SearchResultRow result) {',
    new_open_group,
    'group search, OP/ED filters, RL browser, scroll reset')

text = replace_once(
    text,
    '''        groupOpen = true;
        playlistBrowserOpen = false;
        playlistDetailOpen = false;
        showPlayCounts = false;''',
    '''        groupOpen = true;
        groupSearchEnabled = false;
        if (groupFilterRow != null) groupFilterRow.setVisibility(View.GONE);
        playlistBrowserOpen = false;
        playlistDetailOpen = false;
        showPlayCounts = false;''',
    'disable filters for search result groups')

text = replace_once(
    text,
    '''        titleText.setText(result.label);
        adapter.notifyDataSetChanged();
        refreshInsets();''',
    '''        titleText.setText(result.label);
        adapter.notifyDataSetChanged();
        scrollLibraryToTop();
        refreshInsets();''',
    'search group scroll reset')

new_handle_back = '''    private void handleBack() {
        if (playerOpen) {
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
        }
    }'''
text = replace_method(
    text,
    '    private void handleBack() {',
    '    @Override\n    public void onBackPressed() {',
    new_handle_back,
    'RL-aware group back navigation')

text = replace_once(
    text,
    '''    private static void sortSongsByTitle(List<Song> songs) {
        songs.sort((a, b) -> {
            int result = a.title.compareToIgnoreCase(b.title);
            if (result != 0) return result;
            return a.artist.compareToIgnoreCase(b.artist);
        });
    }

    private static void sortAlbumTracks(List<Song> songs) {''',
    '''    private static void sortSongsByTitle(List<Song> songs) {
        songs.sort((a, b) -> {
            int result = a.title.compareToIgnoreCase(b.title);
            if (result != 0) return result;
            return a.artist.compareToIgnoreCase(b.artist);
        });
    }

    private static void sortSongsByAlbum(List<Song> songs) {
        songs.sort((a, b) -> {
            int result = a.album.compareToIgnoreCase(b.album);
            if (result != 0) return result;
            result = Integer.compare(normalizedTrack(a.trackNumber), normalizedTrack(b.trackNumber));
            if (result != 0) return result;
            result = a.title.compareToIgnoreCase(b.title);
            if (result != 0) return result;
            return a.artist.compareToIgnoreCase(b.artist);
        });
    }

    private static void sortAlbumTracks(List<Song> songs) {''',
    'album-first song sorting')

# Any screen that already hides the search row must also hide the dynamically inserted filter row.
needle = '        searchRow.setVisibility(View.GONE);\n        alphabetIndex.setVisibility(View.GONE);'
replacement = ('        searchRow.setVisibility(View.GONE);\n'
               '        if (groupFilterRow != null) groupFilterRow.setVisibility(View.GONE);\n'
               '        alphabetIndex.setVisibility(View.GONE);')
text = text.replace(needle, replacement)

# Clean up indentation from the previous v0.12.1 one-time metadata migration.
text = text.replace(
    '''            String rawYear = YearTagReader.readYear(getContentResolver(), audio.uri, audio.fileName);
    String androidYear = retriever.extractMetadata(MediaMetadataRetriever.METADATA_KEY_YEAR);
    String year = valueOr(rawYear, valueOr(androidYear, "Unbekannt"));''',
    '''            String rawYear = YearTagReader.readYear(getContentResolver(), audio.uri, audio.fileName);
            String androidYear = retriever.extractMetadata(MediaMetadataRetriever.METADATA_KEY_YEAR);
            String year = valueOr(rawYear, valueOr(androidYear, "Unbekannt"));''')

MAIN.write_text(text, encoding='utf-8')

build = BUILD.read_text(encoding='utf-8')
build = replace_once(build, "versionCode 13", "versionCode 14", 'versionCode 14')
build = replace_once(build, "versionName '0.12.1-debug'", "versionName '0.13.0-debug'", 'versionName 0.13.0')
BUILD.write_text(build, encoding='utf-8')

print('v0.13 patch complete')
