from pathlib import Path

MAIN = Path('app/src/main/java/de/minimal/musicplayer/MainActivity.java')
LAYOUT = Path('app/src/main/res/layout/activity_main.xml')
BUILD = Path('app/build.gradle')
PLAYLIST_INDEX = Path('app/src/main/java/de/minimal/musicplayer/PlaylistIndex.java')


def replace_once(text, old, new, label):
    if old not in text:
        raise SystemExit(f'missing anchor: {label}')
    return text.replace(old, new, 1)

main = MAIN.read_text(encoding='utf-8')
layout = LAYOUT.read_text(encoding='utf-8')
build = BUILD.read_text(encoding='utf-8')

main = replace_once(main,
'''    private static final String PREF_REPEAT_ONE = "repeat_one";\n''',
'''    private static final String PREF_REPEAT_ONE = "repeat_one";\n    private static final String PREF_SMOOTH_TRANSITIONS = "smooth_transitions";\n''', 'smooth pref')

main = replace_once(main,
'''    private Button infoSettingsButton;\n    private Button clearSearchButton;\n''',
'''    private Button infoSettingsButton;\n    private Button refreshLibraryButton;\n    private Button smoothTransitionButton;\n    private Button clearSearchButton;\n''', 'settings buttons fields')

main = replace_once(main,
'''    private boolean infoSettingsOpen;\n    private boolean playCountedThisCycle;\n''',
'''    private boolean infoSettingsOpen;\n    private boolean smoothTransitions;\n    private boolean playCountedThisCycle;\n''', 'smooth bool')

main = replace_once(main,
'''    private long lastPlaybackStateSyncRealtimeMs;\n    private volatile int scanGeneration;\n''',
'''    private long lastPlaybackStateSyncRealtimeMs;\n    private int trackTransitionGeneration;\n    private volatile int scanGeneration;\n''', 'transition generation')

main = replace_once(main,
'''        repeatOne = getSharedPreferences(PREFS, MODE_PRIVATE).getBoolean(PREF_REPEAT_ONE, false);\n        playCounts.putAll(PlayHistory.load(this));\n''',
'''        repeatOne = getSharedPreferences(PREFS, MODE_PRIVATE).getBoolean(PREF_REPEAT_ONE, false);\n        smoothTransitions = getSharedPreferences(PREFS, MODE_PRIVATE)\n                .getBoolean(PREF_SMOOTH_TRANSITIONS, false);\n        updateSmoothTransitionButton();\n        playCounts.putAll(PlayHistory.load(this));\n''', 'load smooth setting')

main = replace_once(main,
'''        if (!TextUtils.isEmpty(savedTree)) {\n            scanLibrary(Uri.parse(savedTree), false);\n        } else {\n            showNoFolderState();\n        }\n''',
'''        if (!TextUtils.isEmpty(savedTree)) {\n            loadCachedLibraryOrScan(Uri.parse(savedTree));\n        } else {\n            showNoFolderState();\n        }\n''', 'startup cache load')

main = replace_once(main,
'''        infoSettingsButton = findViewById(R.id.infoSettingsButton);\n        clearSearchButton = findViewById(R.id.clearSearchButton);\n''',
'''        infoSettingsButton = findViewById(R.id.infoSettingsButton);\n        refreshLibraryButton = findViewById(R.id.refreshLibraryButton);\n        smoothTransitionButton = findViewById(R.id.smoothTransitionButton);\n        clearSearchButton = findViewById(R.id.clearSearchButton);\n''', 'bind settings buttons')

main = replace_once(main,
'''        infoSettingsButton.setOnClickListener(v -> openInfoSettings());\n        playlistsButton.setOnClickListener(v -> {\n''',
'''        infoSettingsButton.setOnClickListener(v -> openInfoSettings());\n        refreshLibraryButton.setOnClickListener(v -> {\n            if (currentTreeUri == null) {\n                Toast.makeText(this, "Kein Musikordner ausgewählt.", Toast.LENGTH_SHORT).show();\n            } else {\n                scanLibrary(currentTreeUri, true);\n            }\n        });\n        smoothTransitionButton.setOnClickListener(v -> toggleSmoothTransitions());\n        playlistsButton.setOnClickListener(v -> {\n''', 'settings actions')

main = replace_once(main,
'''    private void updateSeasonModeButtons() {\n        styleGroupFilterButton(seasonAnimeButton, "ANIME".equals(seasonCategory));\n        styleGroupFilterButton(seasonRlButton, "RL".equals(seasonCategory));\n    }\n\n    private void applySystemInsets() {\n''',
'''    private void updateSeasonModeButtons() {\n        styleGroupFilterButton(seasonAnimeButton, "ANIME".equals(seasonCategory));\n        styleGroupFilterButton(seasonRlButton, "RL".equals(seasonCategory));\n    }\n\n    private void toggleSmoothTransitions() {\n        smoothTransitions = !smoothTransitions;\n        getSharedPreferences(PREFS, MODE_PRIVATE).edit()\n                .putBoolean(PREF_SMOOTH_TRANSITIONS, smoothTransitions).apply();\n        updateSmoothTransitionButton();\n    }\n\n    private void updateSmoothTransitionButton() {\n        if (smoothTransitionButton == null) return;\n        smoothTransitionButton.setText("SANFTER TRACKWECHSEL · "\n                + (smoothTransitions ? "AN" : "AUS"));\n        smoothTransitionButton.setTextColor(getColor(\n                smoothTransitions ? R.color.accent : R.color.text_secondary));\n    }\n\n    private void loadCachedLibraryOrScan(Uri treeUri) {\n        currentTreeUri = treeUri;\n        final String treeKey = treeUri.toString();\n        final int generation = ++scanGeneration;\n        scanExecutor.execute(() -> {\n            ArrayList<Song> cachedSongs = LibraryIndex.load(this, treeKey);\n            sortSongsByTitle(cachedSongs);\n            PlaylistIndex.Snapshot playlistSnapshot = PlaylistIndex.load(this, treeKey);\n            ArrayList<ImportedPlaylist> cachedPlaylists = playlistSnapshot.valid\n                    ? restoreCachedPlaylists(playlistSnapshot.entries, cachedSongs)\n                    : new ArrayList<>();\n\n            mainHandler.post(() -> {\n                if (generation != scanGeneration) return;\n                if (!cachedSongs.isEmpty()) {\n                    allSongs.clear();\n                    allSongs.addAll(cachedSongs);\n                    importedPlaylists.clear();\n                    importedPlaylists.addAll(cachedPlaylists);\n                    playlistScanCompleted = playlistSnapshot.valid;\n                    if (!playerOpen && !groupOpen && !infoSettingsOpen) selectTab(libraryMode);\n                }\n\n                // v0.14.1 introduces the playlist cache. Existing installs need one\n                // silent migration scan; after that normal launches use only cache.\n                if (cachedSongs.isEmpty() || !playlistSnapshot.valid) {\n                    scanLibrary(treeUri, false);\n                } else if (libraryMode == MODE_OTHER) {\n                    updateOtherPanel();\n                }\n            });\n        });\n    }\n\n    private ArrayList<ImportedPlaylist> restoreCachedPlaylists(\n            List<PlaylistIndex.Entry> entries, List<Song> songs) {\n        HashMap<String, Song> songsByUri = new HashMap<>();\n        for (Song song : songs) songsByUri.put(song.uri.toString(), song);\n        ArrayList<ImportedPlaylist> restored = new ArrayList<>();\n        for (PlaylistIndex.Entry entry : entries) {\n            ArrayList<Song> matched = new ArrayList<>();\n            for (String uri : entry.songUris) {\n                Song song = songsByUri.get(uri);\n                if (song != null) matched.add(song);\n            }\n            restored.add(new ImportedPlaylist(entry.name, entry.sourceRelativePath, matched,\n                    entry.totalEntries, entry.missingEntries));\n        }\n        return restored;\n    }\n\n    private ArrayList<PlaylistIndex.Entry> cachePlaylistEntries(\n            List<ImportedPlaylist> playlists) {\n        ArrayList<PlaylistIndex.Entry> entries = new ArrayList<>();\n        for (ImportedPlaylist playlist : playlists) {\n            ArrayList<String> uris = new ArrayList<>();\n            for (Song song : playlist.songs) uris.add(song.uri.toString());\n            entries.add(new PlaylistIndex.Entry(playlist.name, playlist.sourceRelativePath,\n                    uris, playlist.totalEntries, playlist.missingEntries));\n        }\n        return entries;\n    }\n\n    private void applySystemInsets() {\n''', 'settings/cache helpers')

main = replace_once(main,
'''                PlaylistImportBatch playlistBatch = importPlaylists(playlistFiles, files, found);\n                foundPlaylists.addAll(playlistBatch.playlists);\n                playlistReadErrorCount = playlistBatch.readErrors;\n                completed = true;\n''',
'''                PlaylistImportBatch playlistBatch = importPlaylists(playlistFiles, files, found);\n                foundPlaylists.addAll(playlistBatch.playlists);\n                playlistReadErrorCount = playlistBatch.readErrors;\n                PlaylistIndex.save(this, treeKey, cachePlaylistEntries(foundPlaylists));\n                completed = true;\n''', 'save playlist cache')

main = replace_once(main,
'''    private List<GroupRow> buildSeasonGroupsForCategory() {\n        ArrayList<GroupRow> out = new ArrayList<>();\n        for (GroupRow group : buildGroups(false)) {\n            boolean rl = group.name != null && group.name.regionMatches(true, 0, "RL_", 0, 3);\n            if (("RL".equals(seasonCategory) && rl) || (!"RL".equals(seasonCategory) && !rl)) out.add(group);\n        }\n        return out;\n    }\n''',
'''    private List<GroupRow> buildSeasonGroupsForCategory() {\n        ArrayList<GroupRow> out = new ArrayList<>();\n        for (GroupRow group : buildGroups(false)) {\n            String name = group.name == null ? "" : group.name.trim();\n            boolean anime = leadingYear(name) >= 0 || "OST".equalsIgnoreCase(name);\n            if (("ANIME".equals(seasonCategory) && anime)\n                    || ("RL".equals(seasonCategory) && !anime)) {\n                out.add(group);\n            }\n        }\n        return out;\n    }\n''', 'season routing')

main = replace_once(main,
'''    private void hideSearchKeyboard() {\n        if (searchInput != null) searchInput.clearFocus();\n        View decor = getWindow().getDecorView();\n        decor.setFocusableInTouchMode(true);\n        decor.requestFocus();\n        InputMethodManager imm = (InputMethodManager) getSystemService(Context.INPUT_METHOD_SERVICE);\n        if (imm != null) {\n            imm.hideSoftInputFromWindow(decor.getWindowToken(), InputMethodManager.HIDE_NOT_ALWAYS);\n            mainHandler.postDelayed(() -> imm.hideSoftInputFromWindow(decor.getWindowToken(), 0), 120L);\n        }\n    }\n''',
'''    private void hideSearchKeyboard() {\n        View decor = getWindow().getDecorView();\n        if (searchInput != null) {\n            searchInput.clearFocus();\n            // Temporarily removing focusability stops Samsung Keyboard from immediately\n            // reclaiming the EditText after a song is started.\n            searchInput.setFocusable(false);\n        }\n        decor.setFocusableInTouchMode(true);\n        decor.requestFocus();\n        InputMethodManager imm = (InputMethodManager) getSystemService(Context.INPUT_METHOD_SERVICE);\n        if (imm != null) {\n            imm.hideSoftInputFromWindow(decor.getWindowToken(), 0);\n            mainHandler.postDelayed(() -> imm.hideSoftInputFromWindow(decor.getWindowToken(), 0), 120L);\n        }\n        if (searchInput != null) {\n            mainHandler.postDelayed(() -> {\n                searchInput.setFocusableInTouchMode(true);\n                searchInput.setFocusable(true);\n            }, 220L);\n        }\n    }\n''', 'force keyboard hide')

old_play = '''    private void playSong(Song song) {\n        releasePlayer(false);\n        if (mediaSession != null) mediaSession.setActive(true);\n        currentSong = song;\n        resetPlayCountCycle();\n        preparing = true;\n        mediaPlayer = new MediaPlayer();\n        mediaPlayer.setAudioAttributes(new AudioAttributes.Builder()\n                .setContentType(AudioAttributes.CONTENT_TYPE_MUSIC)\n                .setUsage(AudioAttributes.USAGE_MEDIA)\n                .build());\n        mediaPlayer.setLooping(repeatOne);\n        mediaPlayer.setOnCompletionListener(this);\n        mediaPlayer.setOnPreparedListener(player -> {\n            preparing = false;\n            if (requestAudioFocus()) {\n                player.start();\n            } else {\n                Toast.makeText(this, "Audio-Fokus konnte nicht übernommen werden.", Toast.LENGTH_SHORT).show();\n            }\n            updatePlayButtons();\n            seekBar.setMax(Math.max(player.getDuration(), 1));\n            totalTime.setText(formatDuration(player.getDuration()));\n        });\n        mediaPlayer.setOnErrorListener((player, what, extra) -> {\n            preparing = false;\n            Toast.makeText(this, "Datei konnte nicht abgespielt werden.", Toast.LENGTH_SHORT).show();\n            updatePlayButtons();\n            return true;\n        });\n        try {\n            mediaPlayer.setDataSource(this, song.uri);\n            mediaPlayer.prepareAsync();\n            miniPlayer.setVisibility(View.VISIBLE);\n            refreshInsets();\n            updatePlayerMetadata();\n            updatePlayButtons();\n        } catch (IOException | SecurityException ex) {\n            preparing = false;\n            Toast.makeText(this, "Kein Zugriff auf diese Audiodatei.", Toast.LENGTH_SHORT).show();\n        }\n    }\n'''
new_play = '''    private void playSong(Song song) {\n        hideSearchKeyboard();\n        int generation = ++trackTransitionGeneration;\n        MediaPlayer active = mediaPlayer;\n        if (smoothTransitions && active != null && !preparing) {\n            try {\n                if (active.isPlaying()) {\n                    fadeOutAndStart(active, song, generation, 0);\n                    return;\n                }\n            } catch (IllegalStateException ignored) { }\n        }\n        startSongImmediately(song, generation);\n    }\n\n    private void fadeOutAndStart(MediaPlayer expected, Song target, int generation, int step) {\n        if (generation != trackTransitionGeneration) return;\n        if (expected != mediaPlayer || step >= 5) {\n            startSongImmediately(target, generation);\n            return;\n        }\n        try {\n            float volume = Math.max(0f, 1f - ((step + 1) / 5f));\n            expected.setVolume(volume, volume);\n        } catch (IllegalStateException ignored) {\n            startSongImmediately(target, generation);\n            return;\n        }\n        mainHandler.postDelayed(() -> fadeOutAndStart(expected, target, generation, step + 1), 70L);\n    }\n\n    private void startSongImmediately(Song song, int generation) {\n        if (generation != trackTransitionGeneration) return;\n        releasePlayer(false);\n        if (mediaSession != null) mediaSession.setActive(true);\n        currentSong = song;\n        resetPlayCountCycle();\n        preparing = true;\n        mediaPlayer = new MediaPlayer();\n        MediaPlayer createdPlayer = mediaPlayer;\n        createdPlayer.setAudioAttributes(new AudioAttributes.Builder()\n                .setContentType(AudioAttributes.CONTENT_TYPE_MUSIC)\n                .setUsage(AudioAttributes.USAGE_MEDIA)\n                .build());\n        createdPlayer.setLooping(repeatOne);\n        createdPlayer.setOnCompletionListener(this);\n        createdPlayer.setOnPreparedListener(player -> {\n            if (generation != trackTransitionGeneration || player != mediaPlayer) return;\n            preparing = false;\n            if (requestAudioFocus()) {\n                if (smoothTransitions) player.setVolume(0f, 0f);\n                else player.setVolume(1f, 1f);\n                player.start();\n                if (smoothTransitions) fadeInPlayer(player, generation, 0);\n            } else {\n                Toast.makeText(this, "Audio-Fokus konnte nicht übernommen werden.", Toast.LENGTH_SHORT).show();\n            }\n            updatePlayButtons();\n            seekBar.setMax(Math.max(player.getDuration(), 1));\n            totalTime.setText(formatDuration(player.getDuration()));\n        });\n        createdPlayer.setOnErrorListener((player, what, extra) -> {\n            preparing = false;\n            Toast.makeText(this, "Datei konnte nicht abgespielt werden.", Toast.LENGTH_SHORT).show();\n            updatePlayButtons();\n            return true;\n        });\n        try {\n            createdPlayer.setDataSource(this, song.uri);\n            createdPlayer.prepareAsync();\n            miniPlayer.setVisibility(View.VISIBLE);\n            refreshInsets();\n            updatePlayerMetadata();\n            updatePlayButtons();\n        } catch (IOException | SecurityException ex) {\n            preparing = false;\n            Toast.makeText(this, "Kein Zugriff auf diese Audiodatei.", Toast.LENGTH_SHORT).show();\n        }\n    }\n\n    private void fadeInPlayer(MediaPlayer player, int generation, int step) {\n        if (generation != trackTransitionGeneration || player != mediaPlayer || step >= 5) return;\n        try {\n            float volume = (step + 1) / 5f;\n            player.setVolume(volume, volume);\n        } catch (IllegalStateException ignored) {\n            return;\n        }\n        mainHandler.postDelayed(() -> fadeInPlayer(player, generation, step + 1), 70L);\n    }\n'''
main = replace_once(main, old_play, new_play, 'playSong fade')

layout = replace_once(layout,
'''            <TextView\n                android:layout_width="match_parent"\n                android:layout_height="wrap_content"\n                android:layout_marginTop="28dp"\n                android:gravity="center"\n                android:text="Developed by Eugen"\n''',
'''            <Button\n                android:id="@+id/refreshLibraryButton"\n                android:layout_width="match_parent"\n                android:layout_height="56dp"\n                android:background="@drawable/rounded_surface"\n                android:text="BIBLIOTHEK AKTUALISIEREN"\n                android:textColor="@color/accent"\n                android:textStyle="bold" />\n\n            <Button\n                android:id="@+id/smoothTransitionButton"\n                android:layout_width="match_parent"\n                android:layout_height="56dp"\n                android:layout_marginTop="12dp"\n                android:background="@drawable/rounded_surface"\n                android:text="SANFTER TRACKWECHSEL · AUS"\n                android:textColor="@color/text_secondary"\n                android:textStyle="bold" />\n\n            <TextView\n                android:layout_width="match_parent"\n                android:layout_height="wrap_content"\n                android:layout_marginTop="28dp"\n                android:gravity="center"\n                android:text="Developed by Eugen"\n''', 'settings layout')

build = replace_once(build, "        versionCode 18\n        versionName '0.14.0-debug'\n",
                     "        versionCode 19\n        versionName '0.14.1-debug'\n", 'version')

playlist_index = r'''package de.minimal.musicplayer;

import android.content.Context;
import android.util.AtomicFile;

import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.EOFException;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;

/** Persistent imported-playlist snapshot so normal app launches need no folder walk. */
final class PlaylistIndex {
    private static final int MAGIC = 0x4D4D5050; // MMPP
    private static final int VERSION = 1;
    private static final int MAX_PLAYLISTS = 50_000;
    private static final int MAX_URIS = 1_000_000;
    private static final int MAX_STRING_BYTES = 1024 * 1024;
    private static final String FILE_NAME = "playlist-index.bin";

    private PlaylistIndex() { }

    static final class Entry {
        final String name;
        final String sourceRelativePath;
        final ArrayList<String> songUris;
        final int totalEntries;
        final int missingEntries;

        Entry(String name, String sourceRelativePath, ArrayList<String> songUris,
              int totalEntries, int missingEntries) {
            this.name = name;
            this.sourceRelativePath = sourceRelativePath;
            this.songUris = songUris;
            this.totalEntries = totalEntries;
            this.missingEntries = missingEntries;
        }
    }

    static final class Snapshot {
        final boolean valid;
        final ArrayList<Entry> entries;

        Snapshot(boolean valid, ArrayList<Entry> entries) {
            this.valid = valid;
            this.entries = entries;
        }
    }

    static Snapshot load(Context context, String expectedTreeUri) {
        ArrayList<Entry> entries = new ArrayList<>();
        AtomicFile file = file(context);
        if (!file.getBaseFile().isFile()) return new Snapshot(false, entries);
        try (DataInputStream input = new DataInputStream(
                new BufferedInputStream(file.openRead(), 32 * 1024))) {
            if (input.readInt() != MAGIC || input.readInt() != VERSION) {
                return new Snapshot(false, entries);
            }
            if (!expectedTreeUri.equals(readString(input))) return new Snapshot(false, entries);
            int count = input.readInt();
            if (count < 0 || count > MAX_PLAYLISTS) throw new IOException("Invalid playlist count");
            for (int i = 0; i < count; i++) {
                String name = readString(input);
                String path = readString(input);
                int total = input.readInt();
                int missing = input.readInt();
                int uriCount = input.readInt();
                if (uriCount < 0 || uriCount > MAX_URIS) throw new IOException("Invalid URI count");
                ArrayList<String> uris = new ArrayList<>(uriCount);
                for (int u = 0; u < uriCount; u++) uris.add(readString(input));
                entries.add(new Entry(name, path, uris, total, missing));
            }
            return new Snapshot(true, entries);
        } catch (IOException | RuntimeException ignored) {
            file.delete();
            return new Snapshot(false, new ArrayList<>());
        }
    }

    static void save(Context context, String treeUri, List<Entry> entries) {
        AtomicFile file = file(context);
        FileOutputStream raw = null;
        try {
            raw = file.startWrite();
            DataOutputStream output = new DataOutputStream(new BufferedOutputStream(raw, 32 * 1024));
            output.writeInt(MAGIC);
            output.writeInt(VERSION);
            writeString(output, treeUri);
            output.writeInt(entries.size());
            for (Entry entry : entries) {
                writeString(output, entry.name);
                writeString(output, entry.sourceRelativePath);
                output.writeInt(entry.totalEntries);
                output.writeInt(entry.missingEntries);
                output.writeInt(entry.songUris.size());
                for (String uri : entry.songUris) writeString(output, uri);
            }
            output.flush();
            file.finishWrite(raw);
        } catch (IOException | RuntimeException ignored) {
            if (raw != null) file.failWrite(raw);
        }
    }

    private static AtomicFile file(Context context) {
        return new AtomicFile(new File(context.getFilesDir(), FILE_NAME));
    }

    private static void writeString(DataOutputStream output, String value) throws IOException {
        byte[] bytes = (value == null ? "" : value).getBytes(StandardCharsets.UTF_8);
        output.writeInt(bytes.length);
        output.write(bytes);
    }

    private static String readString(DataInputStream input) throws IOException {
        int length;
        try {
            length = input.readInt();
        } catch (EOFException ex) {
            throw new IOException("Truncated playlist index", ex);
        }
        if (length < 0 || length > MAX_STRING_BYTES) throw new IOException("Invalid string length");
        byte[] bytes = new byte[length];
        input.readFully(bytes);
        return new String(bytes, StandardCharsets.UTF_8);
    }
}
'''

MAIN.write_text(main, encoding='utf-8')
LAYOUT.write_text(layout, encoding='utf-8')
BUILD.write_text(build, encoding='utf-8')
PLAYLIST_INDEX.write_text(playlist_index, encoding='utf-8')
print('v0.14.1 patch applied')
