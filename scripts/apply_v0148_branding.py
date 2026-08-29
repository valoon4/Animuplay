from pathlib import Path

MAIN = Path("app/src/main/java/de/minimal/musicplayer/MainActivity.java")
MANIFEST = Path("app/src/main/AndroidManifest.xml")
LAYOUT = Path("app/src/main/res/layout/activity_main.xml")
GRADLE = Path("app/build.gradle")
README = Path("README.md")

main = MAIN.read_text(encoding="utf-8")
manifest = MANIFEST.read_text(encoding="utf-8")
layout = LAYOUT.read_text(encoding="utf-8")
gradle = GRADLE.read_text(encoding="utf-8")
readme = README.read_text(encoding="utf-8")

# Visible working-name branding. Keep Java package/applicationId untouched until final v1.0 branding.
main_count = main.count('"Musikplayer"')
if main_count < 1:
    raise SystemExit("Expected at least one visible Musikplayer title in MainActivity")
main = main.replace('"Musikplayer"', '"Animuplay"')

if 'android:label="Musikplayer"' not in manifest:
    raise SystemExit("Manifest Musikplayer label not found")
manifest = manifest.replace('android:label="Musikplayer"', 'android:label="Animuplay"')

if 'android:text="Musikplayer"' not in layout:
    raise SystemExit("Layout Musikplayer title not found")
layout = layout.replace('android:text="Musikplayer"', 'android:text="Animuplay"')

old_info = '''            <TextView
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:layout_marginTop="28dp"
                android:gravity="center"
                android:text="Developed by Eugen"
                android:textColor="@color/text_primary"
                android:textSize="18sp"
                android:textStyle="bold" />'''
new_info = '''            <TextView
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:layout_marginTop="28dp"
                android:gravity="center"
                android:text="Animuplay"
                android:textColor="@color/accent"
                android:textSize="22sp"
                android:textStyle="bold" />

            <TextView
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:layout_marginTop="12dp"
                android:gravity="center"
                android:text="Developed by Eugen · @valoon4"
                android:textColor="@color/text_primary"
                android:textSize="16sp"
                android:textStyle="bold" />

            <TextView
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:layout_marginTop="6dp"
                android:gravity="center"
                android:text="AI-assisted coding"
                android:textColor="@color/text_secondary"
                android:textSize="14sp" />

            <TextView
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:layout_marginTop="28dp"
                android:gravity="center"
                android:text="SUPPORT / KONTAKT"
                android:textColor="@color/text_secondary"
                android:textSize="12sp"
                android:textStyle="bold" />

            <TextView
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:layout_marginTop="6dp"
                android:gravity="center"
                android:text="valoon@protonmail.com"
                android:textColor="@color/accent"
                android:textIsSelectable="true"
                android:textSize="15sp" />

            <TextView
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:layout_marginTop="24dp"
                android:gravity="center"
                android:text="BUGREPORTS &amp; FEATURE REQUESTS"
                android:textColor="@color/text_secondary"
                android:textSize="12sp"
                android:textStyle="bold" />

            <TextView
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:layout_marginTop="6dp"
                android:gravity="center"
                android:text="GitHub Issues · valoon4/Animuplay"
                android:textColor="@color/accent"
                android:textIsSelectable="true"
                android:textSize="15sp" />'''
if old_info not in layout:
    raise SystemExit("Existing developer info block not found")
layout = layout.replace(old_info, new_info, 1)

# Pre-release version bump.
gradle = gradle.replace("versionCode 25", "versionCode 26")
gradle = gradle.replace("versionName '0.14.7-debug'", "versionName '0.14.8-debug'")
if "versionCode 26" not in gradle or "versionName '0.14.8-debug'" not in gradle:
    raise SystemExit("Version bump failed")

# Refresh public project description for the branded pre-release.
readme = '''# Animuplay

Animuplay is a focused offline Android music player for large, personally managed MP3/FLAC libraries. The project grew out of a practical need: browse thousands of anime songs by custom season tags, keep real-life music separate, import existing PC playlists, and avoid accounts, cloud libraries, ads, tracking, and broad storage permissions.

**Animuplay is the current working app name for all pre-v1.0 builds.** The final public name and package ID will be locked before v1.0. The current package/application ID intentionally remains `de.minimal.musicplayer` so existing development installs continue to update normally.

**Developed by Eugen · GitHub @valoon4**  
**AI-assisted coding**

Support / contact: `valoon@protonmail.com`  
Bug reports and feature requests: GitHub Issues in `valoon4/Animuplay`

## Current development version

`0.14.8-debug` (`versionCode 26`)

This is the final feature-frozen pre-release/debug line before the later v1.0 branding and release-signing pass. The fixed debug signing key in the repository is intentionally public so existing test installs can update in place. It is **not** a release key and must never be used for a public production release.

## What it does

- Selects exactly one music root through Android's Storage Access Framework; no broad storage permission.
- Recursively indexes MP3 and FLAC files and caches metadata for fast later starts.
- Manual **Bibliothek aktualisieren** action for the rare cases where files or tags changed.
- Songs A-Z, album view, Seasons view, Year view and Top 50 most played.
- Season browser split into **ANIME** and **RL**:
  - Anime = tags beginning with a year (for example `2026_2.Spring`) plus the explicit `OST` tag.
  - RL = all remaining tags, including `RL_YYYY`, `Special`, `Unbekannt`, etc.
- Raw MP3/FLAC genre readers preserve custom tags beginning with digits instead of treating them as legacy numeric ID3 genres.
- Year reader supports common MP3 ID3 and FLAC Vorbis year/date fields.
- Normal substring search over album, song title and artist, plus a leading-quote direct mode: for example `"K ED` performs a case-sensitive exact substring search without requiring a closing quote.
- OP/ED filtering for numeric anime Seasons and numeric playlist names.
- Recursive `.m3u` / `.m3u8` import with Windows paths, relative paths, URI decoding, Unicode, duplicates and missing-entry counts.
- Imported playlists and music metadata are cached so a normal launch does not walk the full music tree.
- Playback queue is internal only; no separate queue-management UI.
- Repeat-one, previous/next, random playback, Audio Focus, MediaSession, lock-screen progress and media controls.
- Embedded album artwork where available.
- Long-press the artwork in **Aktuelle Wiedergabe** to share the actual MP3/FLAC file through Android's system share sheet.
- Play counts increase only after more than 50% was actually listened to; seeking past the threshold does not count.
- Portable play history remains at the legacy-compatible `MinimalMusicPlayer/profile.json` path inside the selected music root, with internal fallback.
- Hierarchical Android Back handling returns from player/group/playlist/detail screens before allowing the activity to close.

## Offline and privacy

The app has **no internet permission** and sends no library, playback or analytics data anywhere. It only accesses the folder explicitly selected by the user.

The Android media notification is used only for local playback controls. The app does not request `POST_NOTIFICATIONS`; MediaSession playback notifications use Android's media-notification path.

Sharing a song happens only after the user long-presses the current cover. Android grants the chosen receiving app temporary read access to that one audio document.

## Library cache

After the first complete scan, song metadata and imported playlist mappings are stored in the app's private storage. Normal launches restore those caches directly.

When music files or metadata change, use:

**Sonstiges → Infos & Einstellungen → Bibliothek aktualisieren**

If no valid cache exists (for example on first use), the app scans automatically.

## Playlist compatibility

PC playlists may contain entries such as:

```text
file:///F:/Musik/2025/Doctor%20Stone%20-%20Science%20Future%20OP.flac
```

The player maps the music-root portion to the selected Android folder, fully URI-decodes UTF-8 paths, supports `/` and `\\`, keeps literal `+`, accepts relative paths, preserves playlist order and duplicates, and skips missing files without rejecting the whole playlist.

## Build

Requirements:

- JDK 17
- Android SDK Platform 36
- Android Build Tools 36.x
- Android Gradle Plugin 8.9.1
- Gradle 8.11.1 (the included wrapper is pinned to this version)

Build the debug APK with:

```bash
./gradlew clean assembleDebug
```

Output:

```text
app/build/outputs/apk/debug/app-debug.apk
```

The GitHub Actions workflow performs the same debug build and verifies the known test certificate before publishing an artifact.

## Release signing

Do **not** reuse `app/debug.keystore` for a real release. Before v1.0, choose the final app name/package ID, create a new private release/upload key locally, keep it outside this repository, and add release signing without committing the key or passwords. `.gitignore` already excludes normal release keystore/property names.

## Dependencies and licensing

The app currently has no third-party runtime libraries declared in Gradle; it uses Android platform and Java APIs. A repository scan also found no embedded third-party copyright headers in the source tree.

Project source code is released under the [MIT License](LICENSE).

The launcher artwork is a project-owned/generated asset stored in the Android resources. It does not intentionally depict or name a specific third-party anime character or franchise. Before a branded v1.0 release, the final icon/name should still receive one last trademark/visual review.

## Supported Android versions

- Minimum: Android 7.0 / API 24
- Compile/target: Android 16 / API 36
'''

MAIN.write_text(main, encoding="utf-8")
MANIFEST.write_text(manifest, encoding="utf-8")
LAYOUT.write_text(layout, encoding="utf-8")
GRADLE.write_text(gradle, encoding="utf-8")
README.write_text(readme, encoding="utf-8")
