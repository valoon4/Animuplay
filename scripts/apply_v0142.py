from pathlib import Path
import shutil

MAIN = Path('app/src/main/java/de/minimal/musicplayer/MainActivity.java')
LAYOUT = Path('app/src/main/res/layout/activity_main.xml')
MANIFEST = Path('app/src/main/AndroidManifest.xml')
APP_BUILD = Path('app/build.gradle')
README = Path('README.md')
LICENSE = Path('LICENSE')
GITIGNORE = Path('.gitignore')


def replace_once(text, old, new, label):
    if old not in text:
        raise SystemExit(f'missing anchor: {label}')
    return text.replace(old, new, 1)


def remove_once(text, block, label):
    return replace_once(text, block, '', label)


main = MAIN.read_text(encoding='utf-8')
layout = LAYOUT.read_text(encoding='utf-8')
manifest = MANIFEST.read_text(encoding='utf-8')
app_build = APP_BUILD.read_text(encoding='utf-8')

# --- MainActivity: remove the experimental fade setting completely. ---
main = remove_once(main, 'import android.Manifest;\n', 'Manifest import')
main = replace_once(main, 'import android.content.ContentResolver;\n',
                    'import android.content.ClipData;\nimport android.content.ContentResolver;\n',
                    'ClipData import')
main = remove_once(main, 'import android.content.pm.PackageManager;\n', 'PackageManager import')
main = remove_once(main, '    private static final int REQUEST_NOTIFICATIONS = 21;\n', 'notification request constant')
main = remove_once(main, '    private static final String PREF_SMOOTH_TRANSITIONS = "smooth_transitions";\n', 'smooth pref')
main = remove_once(main, '    private Button smoothTransitionButton;\n', 'smooth button field')
main = remove_once(main, '    private boolean notificationPermissionRequested;\n', 'notification permission state')
main = remove_once(main, '    private boolean smoothTransitions;\n', 'smooth state')
main = remove_once(main, '    private int trackTransitionGeneration;\n', 'transition generation')

main = remove_once(main,
'''        smoothTransitions = getSharedPreferences(PREFS, MODE_PRIVATE)\n                .getBoolean(PREF_SMOOTH_TRANSITIONS, false);\n        updateSmoothTransitionButton();\n''', 'load smooth pref')
main = remove_once(main, '        smoothTransitionButton = findViewById(R.id.smoothTransitionButton);\n', 'bind smooth button')

main = remove_once(main,
'''    private void toggleSmoothTransitions() {\n        smoothTransitions = !smoothTransitions;\n        getSharedPreferences(PREFS, MODE_PRIVATE).edit()\n                .putBoolean(PREF_SMOOTH_TRANSITIONS, smoothTransitions).apply();\n        updateSmoothTransitionButton();\n    }\n\n    private void updateSmoothTransitionButton() {\n        if (smoothTransitionButton == null) return;\n        smoothTransitionButton.setText("SANFTER TRACKWECHSEL · "\n                + (smoothTransitions ? "AN" : "AUS"));\n        smoothTransitionButton.setTextColor(getColor(\n                smoothTransitions ? R.color.accent : R.color.text_secondary));\n    }\n\n''', 'smooth setting methods')
main = remove_once(main, '        smoothTransitionButton.setOnClickListener(v -> toggleSmoothTransitions());\n', 'smooth click')

# Share the actual selected SAF audio document from the now-playing cover.
main = replace_once(main,
'''        findViewById(R.id.playerPrev).setOnClickListener(v -> previousSong());\n        findViewById(R.id.playerNext).setOnClickListener(v -> nextSong());\n\n        seekBar.setOnSeekBarChangeListener''',
'''        findViewById(R.id.playerPrev).setOnClickListener(v -> previousSong());\n        findViewById(R.id.playerNext).setOnClickListener(v -> nextSong());\n        artwork.setOnLongClickListener(v -> {\n            shareCurrentSong();\n            return true;\n        });\n\n        seekBar.setOnSeekBarChangeListener''', 'cover long press')

main = replace_once(main,
'''    private void initializePlaybackSystem() {\n''',
'''    private void shareCurrentSong() {\n        Song song = currentSong;\n        if (song == null || song.uri == null) return;\n\n        String mime = getContentResolver().getType(song.uri);\n        String fileName = song.fileName == null ? "" : song.fileName.toLowerCase(Locale.ROOT);\n        if (TextUtils.isEmpty(mime) || !mime.toLowerCase(Locale.ROOT).startsWith("audio/")) {\n            if (fileName.endsWith(".flac")) mime = "audio/flac";\n            else if (fileName.endsWith(".mp3")) mime = "audio/mpeg";\n            else mime = "audio/*";\n        }\n\n        Intent share = new Intent(Intent.ACTION_SEND);\n        share.setType(mime);\n        share.putExtra(Intent.EXTRA_STREAM, song.uri);\n        share.setClipData(ClipData.newRawUri(\n                TextUtils.isEmpty(song.fileName) ? song.title : song.fileName, song.uri));\n        share.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);\n\n        try {\n            Intent chooser = Intent.createChooser(share, "Song teilen");\n            chooser.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);\n            startActivity(chooser);\n        } catch (RuntimeException ex) {\n            Toast.makeText(this, "Song konnte nicht geteilt werden.", Toast.LENGTH_SHORT).show();\n        }\n    }\n\n    private void initializePlaybackSystem() {\n''', 'share method')

# MediaSession notifications are exempt from Android 13's normal notification permission.
main = remove_once(main,
'''        if (Build.VERSION.SDK_INT >= 33\n                && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {\n            if (!notificationPermissionRequested) {\n                notificationPermissionRequested = true;\n                requestPermissions(new String[] {Manifest.permission.POST_NOTIFICATIONS}, REQUEST_NOTIFICATIONS);\n            }\n            return;\n        }\n''', 'notification permission gate')
main = remove_once(main,
'''    @Override\n    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {\n        super.onRequestPermissionsResult(requestCode, permissions, grantResults);\n        if (requestCode == REQUEST_NOTIFICATIONS && currentSong != null\n                && grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED) {\n            boolean playing = false;\n            if (mediaPlayer != null && !preparing) {\n                try { playing = mediaPlayer.isPlaying(); }\n                catch (IllegalStateException ignored) { }\n            }\n            updateMediaNotification(playing);\n        }\n    }\n\n''', 'notification permission callback')

# Restore direct playback: no fade code, while keeping the global keyboard close on every song start.
start = main.index('    private void playSong(Song song) {\n')
end = main.index('    private void togglePlayback() {\n', start)
replacement = '''    private void playSong(Song song) {\n        hideSearchKeyboard();\n        releasePlayer(false);\n        if (mediaSession != null) mediaSession.setActive(true);\n        currentSong = song;\n        resetPlayCountCycle();\n        preparing = true;\n        mediaPlayer = new MediaPlayer();\n        MediaPlayer createdPlayer = mediaPlayer;\n        createdPlayer.setAudioAttributes(new AudioAttributes.Builder()\n                .setContentType(AudioAttributes.CONTENT_TYPE_MUSIC)\n                .setUsage(AudioAttributes.USAGE_MEDIA)\n                .build());\n        createdPlayer.setLooping(repeatOne);\n        createdPlayer.setOnCompletionListener(this);\n        createdPlayer.setOnPreparedListener(player -> {\n            if (player != mediaPlayer) return;\n            preparing = false;\n            if (requestAudioFocus()) {\n                player.setVolume(1f, 1f);\n                player.start();\n            } else {\n                Toast.makeText(this, "Audio-Fokus konnte nicht übernommen werden.", Toast.LENGTH_SHORT).show();\n            }\n            updatePlayButtons();\n            seekBar.setMax(Math.max(player.getDuration(), 1));\n            totalTime.setText(formatDuration(player.getDuration()));\n        });\n        createdPlayer.setOnErrorListener((player, what, extra) -> {\n            preparing = false;\n            Toast.makeText(this, "Datei konnte nicht abgespielt werden.", Toast.LENGTH_SHORT).show();\n            updatePlayButtons();\n            return true;\n        });\n        try {\n            createdPlayer.setDataSource(this, song.uri);\n            createdPlayer.prepareAsync();\n            miniPlayer.setVisibility(View.VISIBLE);\n            refreshInsets();\n            updatePlayerMetadata();\n            updatePlayButtons();\n        } catch (IOException | SecurityException ex) {\n            preparing = false;\n            Toast.makeText(this, "Kein Zugriff auf diese Audiodatei.", Toast.LENGTH_SHORT).show();\n        }\n    }\n\n'''
main = main[:start] + replacement + main[end:]

# --- Layout: keep the useful manual library refresh, remove the dead fade setting. ---
layout = remove_once(layout,
'''            <Button\n                android:id="@+id/smoothTransitionButton"\n                android:layout_width="match_parent"\n                android:layout_height="56dp"\n                android:layout_marginTop="12dp"\n                android:background="@drawable/rounded_surface"\n                android:text="SANFTER TRACKWECHSEL · AUS"\n                android:textColor="@color/text_secondary"\n                android:textStyle="bold" />\n\n''', 'smooth settings button')

# --- Permissions: this app stays offline and no longer asks for POST_NOTIFICATIONS. ---
manifest = remove_once(manifest,
                       '    <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />\n',
                       'notification manifest permission')

# --- Android 16 / API 36 + next dev version. ---
app_build = replace_once(app_build, '    compileSdk 35\n', '    compileSdk 36\n', 'compile sdk')
app_build = replace_once(app_build, '        targetSdk 35\n', '        targetSdk 36\n', 'target sdk')
app_build = replace_once(app_build, '        versionCode 19\n', '        versionCode 20\n', 'version code')
app_build = replace_once(app_build, "        versionName '0.14.1-debug'\n",
                         "        versionName '0.14.2-debug'\n", 'version name')

MAIN.write_text(main, encoding='utf-8')
LAYOUT.write_text(layout, encoding='utf-8')
MANIFEST.write_text(manifest, encoding='utf-8')
APP_BUILD.write_text(app_build, encoding='utf-8')

# --- Public-project cleanup and documentation. ---
README.write_text('''# Minimal Music Player / Animuplay\n\nA focused offline Android music player for large, personally managed MP3/FLAC libraries.\nThe project grew out of a practical need: browse thousands of anime songs by custom season tags, keep real-life music separate, import existing PC playlists, and avoid accounts, cloud libraries, ads, tracking, and broad storage permissions.\n\n> The final public app name and package ID will be chosen for the v1.0 release. The current Android app label is still **Musikplayer** and the package is `de.minimal.musicplayer`.\n\n**Developed by Eugen.**\n\n## Current development version\n\n`0.14.2-debug` (`versionCode 20`)\n\nThis is still a development build. The fixed debug signing key in the repository is intentionally public so existing test installs can update in place. It is **not** a release key and must never be used for a public production release.\n\n## What it does\n\n- Selects exactly one music root through Android's Storage Access Framework; no broad storage permission.\n- Recursively indexes MP3 and FLAC files and caches metadata for fast later starts.\n- Manual **Bibliothek aktualisieren** action for the rare cases where files or tags changed.\n- Songs A-Z, album view, Seasons view, Year view and Top 50 most played.\n- Season browser split into **ANIME** and **RL**:\n  - Anime = tags beginning with a year (for example `2026_2.Spring`) plus the explicit `OST` tag.\n  - RL = all remaining tags, including `RL_YYYY`, `Special`, `Unbekannt`, etc.\n- Raw MP3/FLAC genre readers preserve custom tags beginning with digits instead of treating them as legacy numeric ID3 genres.\n- Year reader supports common MP3 ID3 and FLAC Vorbis year/date fields.\n- Strict substring search over album, song title and artist.\n- OP/ED filtering for numeric anime Seasons and numeric playlist names.\n- Recursive `.m3u` / `.m3u8` import with Windows paths, relative paths, URI decoding, Unicode, duplicates and missing-entry counts.\n- Imported playlists and music metadata are cached so a normal launch does not walk the full music tree.\n- Playback queue is internal only; no separate queue-management UI.\n- Repeat-one, previous/next, random playback, Audio Focus, MediaSession, lock-screen progress and media controls.\n- Embedded album artwork where available.\n- Long-press the artwork in **Aktuelle Wiedergabe** to share the actual MP3/FLAC file through Android's system share sheet.\n- Play counts increase only after more than 50% was actually listened to; seeking past the threshold does not count.\n- Portable play history at `MinimalMusicPlayer/profile.json` inside the selected music root, with internal fallback.\n\n## Offline and privacy\n\nThe app has **no internet permission** and sends no library, playback or analytics data anywhere. It only accesses the folder explicitly selected by the user.\n\nThe Android media notification is used only for local playback controls. The app does not request `POST_NOTIFICATIONS`; MediaSession playback notifications use Android's media-notification path.\n\nSharing a song happens only after the user long-presses the current cover. Android grants the chosen receiving app temporary read access to that one audio document.\n\n## Library cache\n\nAfter the first complete scan, song metadata and imported playlist mappings are stored in the app's private storage. Normal launches restore those caches directly.\n\nWhen music files or metadata change, use:\n\n**Sonstiges → Infos & Einstellungen → Bibliothek aktualisieren**\n\nIf no valid cache exists (for example on first use), the app scans automatically.\n\n## Playlist compatibility\n\nPC playlists may contain entries such as:\n\n```text\nfile:///F:/Musik/2025/Doctor%20Stone%20-%20Science%20Future%20OP.flac\n```\n\nThe player maps the music-root portion to the selected Android folder, fully URI-decodes UTF-8 paths, supports `/` and `\\`, keeps literal `+`, accepts relative paths, preserves playlist order and duplicates, and skips missing files without rejecting the whole playlist.\n\n## Build\n\nRequirements:\n\n- JDK 17\n- Android SDK Platform 36\n- Android Build Tools 36.x\n- Android Gradle Plugin 8.9.1\n- Gradle 8.11.1 (the included wrapper is pinned to this version)\n\nBuild the debug APK with:\n\n```bash\n./gradlew clean assembleDebug\n```\n\nOutput:\n\n```text\napp/build/outputs/apk/debug/app-debug.apk\n```\n\nThe GitHub Actions workflow performs the same debug build and verifies the known test certificate before publishing an artifact.\n\n## Release signing\n\nDo **not** reuse `app/debug.keystore` for a real release. Before v1.0, create a new private release/upload key locally, keep it outside this repository, and add release signing without committing the key or passwords. `.gitignore` already excludes normal release keystore/property names.\n\n## Dependencies and licensing\n\nThe app currently has no third-party runtime libraries declared in Gradle; it uses Android platform and Java APIs. A repository scan also found no embedded third-party copyright headers in the source tree.\n\nProject source code is released under the [MIT License](LICENSE).\n\nThe launcher artwork is a project-owned/generated asset stored in the Android resources. It does not intentionally depict or name a specific third-party anime character or franchise. Before a branded v1.0 release, the final icon/name should still receive one last trademark/visual review.\n\n## Supported Android versions\n\n- Minimum: Android 7.0 / API 24\n- Compile/target: Android 16 / API 36\n''', encoding='utf-8')

LICENSE.write_text('''MIT License\n\nCopyright (c) 2026 Eugen\n\nPermission is hereby granted, free of charge, to any person obtaining a copy\nof this software and associated documentation files (the "Software"), to deal\nin the Software without restriction, including without limitation the rights\nto use, copy, modify, merge, publish, distribute, sublicense, and/or sell\ncopies of the Software, and to permit persons to whom the Software is\nfurnished to do so, subject to the following conditions:\n\nThe above copyright notice and this permission notice shall be included in all\ncopies or substantial portions of the Software.\n\nTHE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR\nIMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,\nFITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE\nAUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER\nLIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,\nOUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE\nSOFTWARE.\n''', encoding='utf-8')

GITIGNORE.write_text('''.gradle/\n.idea/\nlocal.properties\n**/build/\n*.iml\n.DS_Store\n\n# Release signing material must stay private.\n*.jks\n*.keystore\nkeystore.properties\nsigning.properties\n\n# Exception: fixed PUBLIC test-only key used by the historical debug upgrade chain.\n!app/debug.keystore\n''', encoding='utf-8')

# Remove obsolete handoff/build snapshots and old packaged APK references.
for old_file in [
    '00_UPLOAD_TO_GITHUB.md',
    'BUILD_APK.md',
    'BUILD_VERIFIED.md',
    'CHANGELOG_v0.12.md',
    'DO_NOT_BREAK.md',
    'GITHUB_BUILD.md',
    'HANDOFF_SHA256.txt',
    'NEXT_CHAT_PROMPT.md',
    'PROJECT_CONTEXT.md',
    'QA_REPORT.md',
    'QA_REPORT_v0.12.md',
    'README_ANDROID_STUDIO.md',
    'README_GITHUB_HANDOFF.md',
    'V0.12_BUILD_NOTE.md',
]:
    p = Path(old_file)
    if p.exists():
        p.unlink()

for old_dir in ['docs', 'reference']:
    p = Path(old_dir)
    if p.exists():
        shutil.rmtree(p)

# This is a one-shot migration helper; do not leave development patch machinery in main.
try:
    Path(__file__).unlink()
except OSError:
    pass

print('v0.14.2 patch and repo cleanup applied')
