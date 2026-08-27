# Minimal Music Player / Animuplay

A focused offline Android music player for large, personally managed MP3/FLAC libraries.
The project grew out of a practical need: browse thousands of anime songs by custom season tags, keep real-life music separate, import existing PC playlists, and avoid accounts, cloud libraries, ads, tracking, and broad storage permissions.

> The final public app name and package ID will be chosen for the v1.0 release. The current Android app label is still **Musikplayer** and the package is `de.minimal.musicplayer`.

**Developed by Eugen.**

## Current development version

`0.14.3-debug` (`versionCode 21`)

This is still a development build. The fixed debug signing key in the repository is intentionally public so existing test installs can update in place. It is **not** a release key and must never be used for a public production release.

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
- Strict substring search over album, song title and artist.
- OP/ED filtering for numeric anime Seasons and numeric playlist names.
- Recursive `.m3u` / `.m3u8` import with Windows paths, relative paths, URI decoding, Unicode, duplicates and missing-entry counts.
- Imported playlists and music metadata are cached so a normal launch does not walk the full music tree.
- Playback queue is internal only; no separate queue-management UI.
- Repeat-one, previous/next, random playback, Audio Focus, MediaSession, lock-screen progress and media controls.
- Embedded album artwork where available.
- Long-press the artwork in **Aktuelle Wiedergabe** to share the actual MP3/FLAC file through Android's system share sheet.
- Play counts increase only after more than 50% was actually listened to; seeking past the threshold does not count.
- Portable play history at `MinimalMusicPlayer/profile.json` inside the selected music root, with internal fallback.

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

The player maps the music-root portion to the selected Android folder, fully URI-decodes UTF-8 paths, supports `/` and `\`, keeps literal `+`, accepts relative paths, preserves playlist order and duplicates, and skips missing files without rejecting the whole playlist.

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

Do **not** reuse `app/debug.keystore` for a real release. Before v1.0, create a new private release/upload key locally, keep it outside this repository, and add release signing without committing the key or passwords. `.gitignore` already excludes normal release keystore/property names.

## Dependencies and licensing

The app currently has no third-party runtime libraries declared in Gradle; it uses Android platform and Java APIs. A repository scan also found no embedded third-party copyright headers in the source tree.

Project source code is released under the [MIT License](LICENSE).

The launcher artwork is a project-owned/generated asset stored in the Android resources. It does not intentionally depict or name a specific third-party anime character or franchise. Before a branded v1.0 release, the final icon/name should still receive one last trademark/visual review.

## Supported Android versions

- Minimum: Android 7.0 / API 24
- Compile/target: Android 16 / API 36
