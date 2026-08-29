from pathlib import Path

MAIN = Path("app/src/main/java/de/minimal/musicplayer/MainActivity.java")
PLAYLIST_INDEX = Path("app/src/main/java/de/minimal/musicplayer/PlaylistIndex.java")
LAYOUT = Path("app/src/main/res/layout/activity_main.xml")
GRADLE = Path("app/build.gradle")
README = Path("README.md")

main = MAIN.read_text(encoding="utf-8")
index = PLAYLIST_INDEX.read_text(encoding="utf-8")
layout = LAYOUT.read_text(encoding="utf-8")
gradle = GRADLE.read_text(encoding="utf-8")
readme = README.read_text(encoding="utf-8")

def repl(text, old, new, label, count=1):
    if old not in text:
        raise SystemExit(f"Missing patch target: {label}")
    return text.replace(old, new, count)

# ---- MainActivity: state / views ----
main = repl(main,
'''    private Button infoSettingsButton;\n    private Button refreshLibraryButton;\n    private Button clearSearchButton;''',
'''    private Button infoSettingsButton;\n    private Button refreshLibraryButton;\n    private Button playlistCheckButton;\n    private Button clearSearchButton;''',
"playlist check button field")

main = repl(main,
'''    private TextView currentTime;\n    private TextView totalTime;''',
'''    private TextView currentTime;\n    private TextView totalTime;\n    private TextView versionText;''',
"version text field")

main = repl(main,
'''    private boolean rlYearDetailOpen;\n    private boolean infoSettingsOpen;\n    private boolean playCountedThisCycle;''',
'''    private boolean rlYearDetailOpen;\n    private boolean infoSettingsOpen;\n    private boolean playlistCheckBrowserOpen;\n    private boolean playlistCheckDetailOpen;\n    private boolean playCountedThisCycle;''',
"playlist check state fields")

main = repl(main,
'''        setContentView(R.layout.activity_main);\n        bindViews();\n        initializeGroupFilterRow();''',
'''        setContentView(R.layout.activity_main);\n        bindViews();\n        versionText.setText("Version " + BuildConfig.VERSION_NAME);\n        initializeGroupFilterRow();''',
"version label setup")

main = repl(main,
'''        infoSettingsButton = findViewById(R.id.infoSettingsButton);\n        refreshLibraryButton = findViewById(R.id.refreshLibraryButton);\n        clearSearchButton = findViewById(R.id.clearSearchButton);''',
'''        infoSettingsButton = findViewById(R.id.infoSettingsButton);\n        refreshLibraryButton = findViewById(R.id.refreshLibraryButton);\n        playlistCheckButton = findViewById(R.id.playlistCheckButton);\n        clearSearchButton = findViewById(R.id.clearSearchButton);''',
"bind playlist check button")

main = repl(main,
'''        currentTime = findViewById(R.id.currentTime);\n        totalTime = findViewById(R.id.totalTime);''',
'''        currentTime = findViewById(R.id.currentTime);\n        totalTime = findViewById(R.id.totalTime);\n        versionText = findViewById(R.id.versionText);''',
"bind version text")

# ---- Actions ----
main = repl(main,
'''        topPlayedButton.setOnClickListener(v -> openTopPlayed());\n        infoSettingsButton.setOnClickListener(v -> openInfoSettings());\n        refreshLibraryButton.setOnClickListener(v -> {''',
'''        topPlayedButton.setOnClickListener(v -> openTopPlayed());\n        infoSettingsButton.setOnClickListener(v -> openInfoSettings());\n        playlistCheckButton.setOnClickListener(v -> {\n            if (!playlistScanCompleted) {\n                Toast.makeText(this, "Playlists werden noch geladen.", Toast.LENGTH_SHORT).show();\n            } else if (importedPlaylists.isEmpty()) {\n                Toast.makeText(this, "Keine Playlists gefunden.", Toast.LENGTH_SHORT).show();\n            } else {\n                openPlaylistCheckBrowser();\n            }\n        });\n        refreshLibraryButton.setOnClickListener(v -> {''',
"bind playlist checker")

main = repl(main,
'''        libraryList.setOnItemClickListener((parent, view, position, id) -> {\n            if (!TextUtils.isEmpty(searchQuery) && !groupOpen) {''',
'''        libraryList.setOnItemClickListener((parent, view, position, id) -> {\n            if (playlistCheckDetailOpen) return;\n            if (playlistCheckBrowserOpen) {\n                if (position >= 0 && position < importedPlaylists.size()) {\n                    checkPlaylist(importedPlaylists.get(position));\n                }\n                return;\n            }\n            if (!TextUtils.isEmpty(searchQuery) && !groupOpen) {''',
"playlist checker list click")

# ---- Playlist cache restore/save ----
main = repl(main,
'''            restored.add(new ImportedPlaylist(entry.name, entry.sourceRelativePath, matched,\n                    entry.totalEntries, entry.missingEntries));''',
'''            restored.add(new ImportedPlaylist(entry.name, entry.sourceRelativePath,\n                    entry.sourceUri, entry.sourceSignature, entry.verified, matched,\n                    entry.totalEntries, entry.missingEntries));''',
"restore playlist source and verification")

main = repl(main,
'''            entries.add(new PlaylistIndex.Entry(playlist.name, playlist.sourceRelativePath,\n                    uris, playlist.totalEntries, playlist.missingEntries));''',
'''            entries.add(new PlaylistIndex.Entry(playlist.name, playlist.sourceRelativePath,\n                    playlist.sourceUri, playlist.sourceSignature, playlist.verified, uris,\n                    playlist.totalEntries, playlist.missingEntries));''',
"cache playlist source and verification")

# ---- Full scan keeps verified state only when playlist contents are unchanged ----
main = repl(main,
'''            ArrayList<Song> cachedSongs = LibraryIndex.load(this, treeKey);\n            HashMap<String, Integer> folderPlayCounts = PlayHistory.loadFromMusicFolder(''',
'''            ArrayList<Song> cachedSongs = LibraryIndex.load(this, treeKey);\n            PlaylistIndex.Snapshot previousPlaylistSnapshot = PlaylistIndex.load(this, treeKey);\n            HashMap<String, Integer> folderPlayCounts = PlayHistory.loadFromMusicFolder(''',
"load previous playlist snapshot")

main = repl(main,
'''                PlaylistImportBatch playlistBatch = importPlaylists(playlistFiles, files, found);''',
'''                PlaylistImportBatch playlistBatch = importPlaylists(playlistFiles, files, found,\n                        previousPlaylistSnapshot.entries);''',
"pass previous playlist verification")

main = repl(main,
'''    private PlaylistImportBatch importPlaylists(List<PendingPlaylist> playlistFiles,\n                                                List<PendingAudio> audioFiles,\n                                                List<Song> songs) {''',
'''    private PlaylistImportBatch importPlaylists(List<PendingPlaylist> playlistFiles,\n                                                List<PendingAudio> audioFiles,\n                                                List<Song> songs,\n                                                List<PlaylistIndex.Entry> previousEntries) {''',
"importPlaylists signature")

main = repl(main,
'''        HashMap<String, Song> songByUri = new HashMap<>();\n        for (Song song : songs) songByUri.put(song.uri.toString(), song);\n\n        ArrayList<ImportedPlaylist> result = new ArrayList<>();''',
'''        HashMap<String, Song> songByUri = new HashMap<>();\n        for (Song song : songs) songByUri.put(song.uri.toString(), song);\n\n        HashMap<String, PlaylistIndex.Entry> previousByPath = new HashMap<>();\n        for (PlaylistIndex.Entry entry : previousEntries) {\n            previousByPath.put(M3uPlaylistReader.key(entry.sourceRelativePath), entry);\n        }\n\n        ArrayList<ImportedPlaylist> result = new ArrayList<>();''',
"previous playlist map")

main = repl(main,
'''                ArrayList<String> entries = M3uPlaylistReader.readEntries(\n                        getContentResolver(), playlistFile.uri, playlistFile.fileName);\n                ArrayList<Song> matchedSongs = new ArrayList<>();''',
'''                ArrayList<String> entries = M3uPlaylistReader.readEntries(\n                        getContentResolver(), playlistFile.uri, playlistFile.fileName);\n                String sourceSignature = playlistSignature(entries);\n                PlaylistIndex.Entry previous = previousByPath.get(\n                        M3uPlaylistReader.key(playlistFile.relativePath));\n                boolean verified = previous != null && previous.verified\n                        && sourceSignature.equals(previous.sourceSignature);\n                ArrayList<Song> matchedSongs = new ArrayList<>();''',
"calculate playlist signature")

main = repl(main,
'''                result.add(new ImportedPlaylist(stripExtension(playlistFile.fileName),\n                        playlistFile.relativePath, matchedSongs, entries.size(), missing));''',
'''                result.add(new ImportedPlaylist(stripExtension(playlistFile.fileName),\n                        playlistFile.relativePath, playlistFile.uri.toString(), sourceSignature,\n                        verified, matchedSongs, entries.size(), missing));''',
"construct imported playlist with source")

# Add stable content signature helper before metadata reading.
main = repl(main,
'''    private Song readMetadata(PendingAudio audio) {''',
'''    private static String playlistSignature(List<String> entries) {\n        long hash = 0xcbf29ce484222325L;\n        for (String entry : entries) {\n            String value = entry == null ? "" : entry;\n            for (int i = 0; i < value.length(); i++) {\n                hash ^= value.charAt(i);\n                hash *= 0x100000001b3L;\n            }\n            hash ^= '\\n';\n            hash *= 0x100000001b3L;\n        }\n        return Long.toHexString(hash) + ":" + entries.size();\n    }\n\n    private Song readMetadata(PendingAudio audio) {''',
"playlist signature helper")

# ---- Reset new sub-navigation in top level ----
main = repl(main,
'''        rlYearDetailOpen = false;\n        infoSettingsOpen = false;\n        rlSongsForBrowser.clear();''',
'''        rlYearDetailOpen = false;\n        infoSettingsOpen = false;\n        playlistCheckBrowserOpen = false;\n        playlistCheckDetailOpen = false;\n        rlSongsForBrowser.clear();''',
"reset playlist checker state")

# ---- Info screen and checker screens ----
main = repl(main,
'''    private void openInfoSettings() {\n        infoSettingsOpen = true;\n        groupOpen = false;''',
'''    private void openInfoSettings() {\n        infoSettingsOpen = true;\n        playlistCheckBrowserOpen = false;\n        playlistCheckDetailOpen = false;\n        groupOpen = false;''',
"info resets checker")

main = repl(main,
'''        titleText.setText("Infos & Einstellungen");\n        refreshInsets();\n    }\n\n    private void openTopPlayed() {''',
'''        titleText.setText("Infos & Einstellungen");\n        refreshInsets();\n    }\n\n    private void openPlaylistCheckBrowser() {\n        infoSettingsOpen = false;\n        playlistCheckBrowserOpen = true;\n        playlistCheckDetailOpen = false;\n        groupOpen = false;\n        playerOpen = false;\n        playlistBrowserOpen = false;\n        playlistDetailOpen = false;\n        visibleSongs.clear();\n        visibleGroups.clear();\n        for (ImportedPlaylist playlist : importedPlaylists) {\n            visibleGroups.add(GroupRow.playlistCheck(playlist));\n        }\n        infoSettingsPanel.setVisibility(View.GONE);\n        playerPanel.setVisibility(View.GONE);\n        otherPanel.setVisibility(View.GONE);\n        emptyState.setVisibility(View.GONE);\n        libraryList.setVisibility(View.VISIBLE);\n        tabBar.setVisibility(View.GONE);\n        searchRow.setVisibility(View.GONE);\n        if (seasonModeRow != null) seasonModeRow.setVisibility(View.GONE);\n        if (groupFilterRow != null) groupFilterRow.setVisibility(View.GONE);\n        alphabetIndex.setVisibility(View.GONE);\n        randomPlayButton.setVisibility(View.GONE);\n        backButton.setVisibility(View.VISIBLE);\n        titleText.setText("Playlists prüfen");\n        adapter.notifyDataSetChanged();\n        scrollLibraryToTop();\n        refreshInsets();\n    }\n\n    private void checkPlaylist(ImportedPlaylist playlist) {\n        if (playlist == null || TextUtils.isEmpty(playlist.sourceUri)) {\n            Toast.makeText(this, "Playlist-Quelle nicht verfügbar. Bibliothek einmal aktualisieren.",\n                    Toast.LENGTH_LONG).show();\n            return;\n        }\n        final ArrayList<Song> songs = new ArrayList<>(allSongs);\n        titleText.setText("Prüfe · " + playlist.name + " …");\n        scanExecutor.execute(() -> {\n            ArrayList<String> missing = new ArrayList<>();\n            String signature;\n            String error = null;\n            try {\n                String fileName = M3uPlaylistReader.fileName(playlist.sourceRelativePath);\n                ArrayList<String> entries = M3uPlaylistReader.readEntries(\n                        getContentResolver(), Uri.parse(playlist.sourceUri), fileName);\n                signature = playlistSignature(entries);\n\n                HashMap<String, String> uriByRelativePath = new HashMap<>();\n                HashMap<String, String> uniqueUriByFileName = new HashMap<>();\n                for (Song song : songs) {\n                    String uri = song.uri.toString();\n                    String relativePath = relativePathForSong(song);\n                    if (!TextUtils.isEmpty(relativePath)) {\n                        uriByRelativePath.put(M3uPlaylistReader.key(relativePath), uri);\n                    }\n                    String fileKey = M3uPlaylistReader.key(song.fileName);\n                    if (uniqueUriByFileName.containsKey(fileKey)) {\n                        uniqueUriByFileName.put(fileKey, null);\n                    } else {\n                        uniqueUriByFileName.put(fileKey, uri);\n                    }\n                }\n\n                for (String entry : entries) {\n                    String songUri = M3uPlaylistReader.matchSongUri(\n                            entry, uriByRelativePath, uniqueUriByFileName);\n                    if (songUri == null) {\n                        int parentSlash = playlist.sourceRelativePath.lastIndexOf('/');\n                        if (parentSlash > 0) {\n                            String playlistParent = playlist.sourceRelativePath.substring(0, parentSlash);\n                            String relativeToPlaylist = M3uPlaylistReader.normalizeRelativePath(\n                                    playlistParent + "/" + entry);\n                            songUri = M3uPlaylistReader.matchSongUri(\n                                    relativeToPlaylist, uriByRelativePath, uniqueUriByFileName);\n                        }\n                    }\n                    if (songUri == null) missing.add(entry);\n                }\n            } catch (IOException | RuntimeException ex) {\n                signature = playlist.sourceSignature;\n                error = ex.getMessage() == null ? ex.getClass().getSimpleName() : ex.getMessage();\n            }\n\n            final String checkedSignature = signature;\n            final String checkError = error;\n            mainHandler.post(() -> {\n                if (checkError != null) {\n                    playlist.verified = false;\n                    persistPlaylistCheckState();\n                    openPlaylistCheckBrowser();\n                    Toast.makeText(this, "Playlist konnte nicht geprüft werden: " + checkError,\n                            Toast.LENGTH_LONG).show();\n                    return;\n                }\n                playlist.sourceSignature = checkedSignature;\n                playlist.verified = missing.isEmpty();\n                persistPlaylistCheckState();\n                if (missing.isEmpty()) {\n                    openPlaylistCheckBrowser();\n                    Toast.makeText(this, "✓ Keine fehlenden Einträge", Toast.LENGTH_SHORT).show();\n                } else {\n                    openPlaylistCheckResult(playlist, missing);\n                }\n            });\n        });\n    }\n\n    private String relativePathForSong(Song song) {\n        if (song == null || song.uri == null || currentTreeUri == null) return song == null ? "" : song.fileName;\n        try {\n            String rootId = DocumentsContract.getTreeDocumentId(currentTreeUri);\n            String documentId = DocumentsContract.getDocumentId(song.uri);\n            String relative = documentId;\n            if (!TextUtils.isEmpty(rootId) && relative.startsWith(rootId)) {\n                relative = relative.substring(rootId.length());\n            }\n            relative = relative.replace('\\\\', '/');\n            while (relative.startsWith("/") || relative.startsWith(":")) {\n                relative = relative.substring(1);\n            }\n            return M3uPlaylistReader.normalizeRelativePath(relative);\n        } catch (RuntimeException ignored) {\n            return song.fileName;\n        }\n    }\n\n    private void persistPlaylistCheckState() {\n        if (currentTreeUri == null) return;\n        PlaylistIndex.save(this, currentTreeUri.toString(), cachePlaylistEntries(importedPlaylists));\n    }\n\n    private void openPlaylistCheckResult(ImportedPlaylist playlist, List<String> missing) {\n        infoSettingsOpen = false;\n        playlistCheckBrowserOpen = false;\n        playlistCheckDetailOpen = true;\n        groupOpen = false;\n        visibleSongs.clear();\n        visibleGroups.clear();\n        for (String entry : missing) visibleGroups.add(GroupRow.missingPlaylistEntry(entry));\n        infoSettingsPanel.setVisibility(View.GONE);\n        otherPanel.setVisibility(View.GONE);\n        emptyState.setVisibility(View.GONE);\n        libraryList.setVisibility(View.VISIBLE);\n        tabBar.setVisibility(View.GONE);\n        searchRow.setVisibility(View.GONE);\n        if (seasonModeRow != null) seasonModeRow.setVisibility(View.GONE);\n        if (groupFilterRow != null) groupFilterRow.setVisibility(View.GONE);\n        alphabetIndex.setVisibility(View.GONE);\n        randomPlayButton.setVisibility(View.GONE);\n        backButton.setVisibility(View.VISIBLE);\n        titleText.setText(playlist.name + " · " + missing.size() + " nicht gefunden");\n        adapter.notifyDataSetChanged();\n        scrollLibraryToTop();\n        refreshInsets();\n    }\n\n    private void openTopPlayed() {''',
"playlist checker screens")

# ---- Back hierarchy ----
main = repl(main,
'''    private void handleBack() {\n        // Use the actually visible screen first. This avoids stale navigation flags\n        // causing Android Back to exit while a detail/player screen is still open.\n        if (infoSettingsPanel != null && infoSettingsPanel.getVisibility() == View.VISIBLE) {''',
'''    private void handleBack() {\n        // Use the actually visible screen first. This avoids stale navigation flags\n        // causing Android Back to exit while a detail/player screen is still open.\n        if (playlistCheckDetailOpen) {\n            openPlaylistCheckBrowser();\n            return;\n        }\n        if (playlistCheckBrowserOpen) {\n            openInfoSettings();\n            return;\n        }\n        if (infoSettingsPanel != null && infoSettingsPanel.getVisibility() == View.VISIBLE) {''',
"playlist checker back navigation")

# ---- Adapter diagnostics rendering ----
main = repl(main,
'''            if (!TextUtils.isEmpty(searchQuery) && !groupOpen) {\n                SearchResultRow result = searchRows.get(position);''',
'''            holder.icon.setTextColor(getColor(R.color.accent));\n            holder.trailing.setTextColor(getColor(R.color.text_secondary));\n\n            if (!TextUtils.isEmpty(searchQuery) && !groupOpen) {\n                SearchResultRow result = searchRows.get(position);''',
"reset recycled row colors")

main = repl(main,
'''            } else {\n                GroupRow group = visibleGroups.get(position);\n                holder.icon.setText(group.playlistGroup ? "≡" : (group.albumGroup ? "▣" : "▤"));\n                holder.primary.setText(group.name);\n                holder.secondary.setText(group.subtitle());\n                holder.trailing.setText(group.playlistGroup\n                        ? group.songs.size() + "/" + group.playlistTotalEntries\n                        : group.songs.size() + " Titel");\n            }''',
'''            } else {\n                GroupRow group = visibleGroups.get(position);\n                if (group.playlistCheckGroup) {\n                    holder.icon.setText(group.playlistVerified ? "✓" : "?");\n                    if (group.playlistVerified) holder.icon.setTextColor(Color.rgb(76, 175, 80));\n                    holder.primary.setText(group.name);\n                    holder.secondary.setText(group.subtitle());\n                    holder.trailing.setText("");\n                } else if (group.diagnosticMissing) {\n                    holder.icon.setText("!");\n                    holder.primary.setText(group.name);\n                    holder.secondary.setText("Nicht gefunden");\n                    holder.trailing.setText("");\n                } else {\n                    holder.icon.setText(group.playlistGroup ? "≡" : (group.albumGroup ? "▣" : "▤"));\n                    holder.primary.setText(group.name);\n                    holder.secondary.setText(group.subtitle());\n                    holder.trailing.setText(group.playlistGroup\n                            ? group.songs.size() + "/" + group.playlistTotalEntries\n                            : group.songs.size() + " Titel");\n                }\n            }''',
"render playlist checker rows")

# ---- ImportedPlaylist persistence fields ----
main = repl(main,
'''    private static final class ImportedPlaylist {\n        String name;\n        final String sourceRelativePath;\n        final ArrayList<Song> songs;\n        final int totalEntries;\n        final int missingEntries;\n\n        ImportedPlaylist(String name, String sourceRelativePath, ArrayList<Song> songs,\n                         int totalEntries, int missingEntries) {\n            this.name = name;\n            this.sourceRelativePath = sourceRelativePath;\n            this.songs = songs;\n            this.totalEntries = totalEntries;\n            this.missingEntries = missingEntries;\n        }\n    }''',
'''    private static final class ImportedPlaylist {\n        String name;\n        final String sourceRelativePath;\n        final String sourceUri;\n        String sourceSignature;\n        boolean verified;\n        final ArrayList<Song> songs;\n        final int totalEntries;\n        final int missingEntries;\n\n        ImportedPlaylist(String name, String sourceRelativePath, String sourceUri,\n                         String sourceSignature, boolean verified, ArrayList<Song> songs,\n                         int totalEntries, int missingEntries) {\n            this.name = name;\n            this.sourceRelativePath = sourceRelativePath;\n            this.sourceUri = sourceUri;\n            this.sourceSignature = sourceSignature;\n            this.verified = verified;\n            this.songs = songs;\n            this.totalEntries = totalEntries;\n            this.missingEntries = missingEntries;\n        }\n    }''',
"ImportedPlaylist verification fields")

# ---- GroupRow diagnostic types ----
main = repl(main,
'''        final boolean playlistGroup;\n        final int playlistTotalEntries;\n        final int playlistMissingEntries;\n\n        GroupRow(String name, ArrayList<Song> songs, boolean albumGroup) {\n            this(name, songs, albumGroup, false, songs.size(), 0);\n        }\n\n        private GroupRow(String name, ArrayList<Song> songs, boolean albumGroup,\n                         boolean playlistGroup, int playlistTotalEntries,\n                         int playlistMissingEntries) {\n            this.name = name;\n            this.songs = songs;\n            this.albumGroup = albumGroup;\n            this.playlistGroup = playlistGroup;\n            this.playlistTotalEntries = playlistTotalEntries;\n            this.playlistMissingEntries = playlistMissingEntries;\n        }\n\n        static GroupRow playlist(ImportedPlaylist playlist) {\n            return new GroupRow(playlist.name, playlist.songs, false, true,\n                    playlist.totalEntries, playlist.missingEntries);\n        }\n\n        String subtitle() {\n            if (playlistGroup) {''',
'''        final boolean playlistGroup;\n        final boolean playlistCheckGroup;\n        final boolean playlistVerified;\n        final boolean diagnosticMissing;\n        final int playlistTotalEntries;\n        final int playlistMissingEntries;\n\n        GroupRow(String name, ArrayList<Song> songs, boolean albumGroup) {\n            this(name, songs, albumGroup, false, false, false, false, songs.size(), 0);\n        }\n\n        private GroupRow(String name, ArrayList<Song> songs, boolean albumGroup,\n                         boolean playlistGroup, boolean playlistCheckGroup,\n                         boolean playlistVerified, boolean diagnosticMissing,\n                         int playlistTotalEntries, int playlistMissingEntries) {\n            this.name = name;\n            this.songs = songs;\n            this.albumGroup = albumGroup;\n            this.playlistGroup = playlistGroup;\n            this.playlistCheckGroup = playlistCheckGroup;\n            this.playlistVerified = playlistVerified;\n            this.diagnosticMissing = diagnosticMissing;\n            this.playlistTotalEntries = playlistTotalEntries;\n            this.playlistMissingEntries = playlistMissingEntries;\n        }\n\n        static GroupRow playlist(ImportedPlaylist playlist) {\n            return new GroupRow(playlist.name, playlist.songs, false, true, false, false, false,\n                    playlist.totalEntries, playlist.missingEntries);\n        }\n\n        static GroupRow playlistCheck(ImportedPlaylist playlist) {\n            return new GroupRow(playlist.name, new ArrayList<>(), false, false, true,\n                    playlist.verified, false, playlist.totalEntries, playlist.missingEntries);\n        }\n\n        static GroupRow missingPlaylistEntry(String entry) {\n            return new GroupRow(entry, new ArrayList<>(), false, false, false, false, true, 0, 0);\n        }\n\n        String subtitle() {\n            if (playlistCheckGroup) {\n                return playlistVerified ? "Geprüft · keine fehlenden Einträge" : "Antippen zum Prüfen";\n            }\n            if (diagnosticMissing) return "Nicht gefunden";\n            if (playlistGroup) {''',
"GroupRow playlist diagnostic types")

# ---- PlaylistIndex v2: source URI + content signature + persistent verified state ----
index = repl(index, '    private static final int VERSION = 1;', '    private static final int VERSION = 2;', "playlist cache version")

index = repl(index,
'''        final String sourceRelativePath;\n        final ArrayList<String> songUris;\n        final int totalEntries;\n        final int missingEntries;\n\n        Entry(String name, String sourceRelativePath, ArrayList<String> songUris,\n              int totalEntries, int missingEntries) {\n            this.name = name;\n            this.sourceRelativePath = sourceRelativePath;\n            this.songUris = songUris;\n            this.totalEntries = totalEntries;\n            this.missingEntries = missingEntries;\n        }''',
'''        final String sourceRelativePath;\n        final String sourceUri;\n        final String sourceSignature;\n        final boolean verified;\n        final ArrayList<String> songUris;\n        final int totalEntries;\n        final int missingEntries;\n\n        Entry(String name, String sourceRelativePath, String sourceUri, String sourceSignature,\n              boolean verified, ArrayList<String> songUris, int totalEntries, int missingEntries) {\n            this.name = name;\n            this.sourceRelativePath = sourceRelativePath;\n            this.sourceUri = sourceUri;\n            this.sourceSignature = sourceSignature;\n            this.verified = verified;\n            this.songUris = songUris;\n            this.totalEntries = totalEntries;\n            this.missingEntries = missingEntries;\n        }''',
"PlaylistIndex Entry fields")

index = repl(index,
'''                String name = readString(input);\n                String path = readString(input);\n                int total = input.readInt();\n                int missing = input.readInt();''',
'''                String name = readString(input);\n                String path = readString(input);\n                String sourceUri = readString(input);\n                String sourceSignature = readString(input);\n                boolean verified = input.readBoolean();\n                int total = input.readInt();\n                int missing = input.readInt();''',
"read playlist verification fields")

index = repl(index,
'''                entries.add(new Entry(name, path, uris, total, missing));''',
'''                entries.add(new Entry(name, path, sourceUri, sourceSignature, verified,\n                        uris, total, missing));''',
"load PlaylistIndex Entry")

index = repl(index,
'''                writeString(output, entry.name);\n                writeString(output, entry.sourceRelativePath);\n                output.writeInt(entry.totalEntries);''',
'''                writeString(output, entry.name);\n                writeString(output, entry.sourceRelativePath);\n                writeString(output, entry.sourceUri);\n                writeString(output, entry.sourceSignature);\n                output.writeBoolean(entry.verified);\n                output.writeInt(entry.totalEntries);''',
"save playlist verification fields")

# ---- Info layout: checker button + automatic version ----
layout = repl(layout,
'''            <Button\n                android:id="@+id/refreshLibraryButton"\n                android:layout_width="match_parent"\n                android:layout_height="56dp"\n                android:background="@drawable/rounded_surface"\n                android:text="BIBLIOTHEK AKTUALISIEREN"\n                android:textColor="@color/accent"\n                android:textStyle="bold" />\n\n            <TextView\n                android:layout_width="match_parent"''',
'''            <Button\n                android:id="@+id/refreshLibraryButton"\n                android:layout_width="match_parent"\n                android:layout_height="56dp"\n                android:background="@drawable/rounded_surface"\n                android:text="BIBLIOTHEK AKTUALISIEREN"\n                android:textColor="@color/accent"\n                android:textStyle="bold" />\n\n            <Button\n                android:id="@+id/playlistCheckButton"\n                android:layout_width="match_parent"\n                android:layout_height="56dp"\n                android:layout_marginTop="12dp"\n                android:background="@drawable/rounded_surface"\n                android:text="PLAYLISTS PRÜFEN"\n                android:textColor="@color/accent"\n                android:textStyle="bold" />\n\n            <TextView\n                android:layout_width="match_parent"''',
"playlist checker info button")

layout = repl(layout,
'''                android:text="Animuplay"\n                android:textColor="@color/accent"\n                android:textSize="22sp"\n                android:textStyle="bold" />\n\n            <TextView\n                android:layout_width="match_parent"\n                android:layout_height="wrap_content"\n                android:layout_marginTop="12dp"\n                android:gravity="center"\n                android:text="Developed by Eugen · @valoon4"''',
'''                android:text="Animuplay"\n                android:textColor="@color/accent"\n                android:textSize="22sp"\n                android:textStyle="bold" />\n\n            <TextView\n                android:id="@+id/versionText"\n                android:layout_width="match_parent"\n                android:layout_height="wrap_content"\n                android:layout_marginTop="6dp"\n                android:gravity="center"\n                android:text="Version"\n                android:textColor="@color/text_secondary"\n                android:textSize="13sp" />\n\n            <TextView\n                android:layout_width="match_parent"\n                android:layout_height="wrap_content"\n                android:layout_marginTop="12dp"\n                android:gravity="center"\n                android:text="Developed by Eugen · @valoon4"''',
"version info label")

# ---- Version / docs ----
gradle = repl(gradle, '        versionCode 26', '        versionCode 27', "version code")
gradle = repl(gradle, "        versionName '0.14.8-debug'", "        versionName '0.14.9-debug'", "version name")

readme = readme.replace('`0.14.8-debug` (`versionCode 26`)', '`0.14.9-debug` (`versionCode 27`)')
readme = readme.replace('This is the final feature-frozen pre-release/debug line before the later v1.0 branding and release-signing pass.',
                        'This is a feature-frozen pre-release/debug line before the later v1.0 branding and release-signing pass.')
needle = '- Recursive `.m3u` / `.m3u8` import with Windows paths, relative paths, URI decoding, Unicode, duplicates and missing-entry counts.\n'
if needle not in readme:
    raise SystemExit('Missing README playlist bullet')
readme = readme.replace(needle, needle + '- **Playlists prüfen** re-checks any imported playlist on demand, lists only entries that cannot be matched, and keeps a persistent green verification check until that playlist file changes on a later library scan.\n', 1)

MAIN.write_text(main, encoding="utf-8")
PLAYLIST_INDEX.write_text(index, encoding="utf-8")
LAYOUT.write_text(layout, encoding="utf-8")
GRADLE.write_text(gradle, encoding="utf-8")
README.write_text(readme, encoding="utf-8")
