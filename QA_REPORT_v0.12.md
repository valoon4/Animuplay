# QA-Bericht — v0.12

## Statisch geprüft

- `versionCode 12`, `versionName 0.12.0-debug`.
- bestehender Debug-Keystore unverändert; Zertifikat SHA-256 `63df019bdb5fbd06dee0cc7910cc81ed908dcd2d9ae9cfd8cc6e1d1c34404227`.
- Tab-Reihenfolge im Layout: Songs → Alben → Seasons → Jahr → Sonstiges.
- `Song` und `LibraryIndex` persistieren das neue `year`-Feld.
- LibraryIndex v2 liest weiterhin v1-Caches aus v0.11.
- alte Cacheeinträge mit noch unbekanntem Year werden beim Hintergrundscan gezielt neu eingelesen.
- Year wird ausschließlich über `MediaMetadataRetriever.METADATA_KEY_YEAR` gelesen.
- fehlendes Year wird als `Unbekannt` gruppiert.
- A–Z-Index ist in der Year-Ansicht deaktiviert.
- direkter Songklick in Suchergebnissen ruft vor Wiedergabe `hideSearchKeyboard()` auf.
- keine Änderung an `GenreTagReader`, `SearchMatcher`, `M3uPlaylistReader`, `PlayHistory` oder `PlaybackActionReceiver`.

## Buildstatus dieser Laufzeit

Der vollständige Android-Build konnte in dieser Laufzeit nicht ausgeführt werden, weil weder Android SDK/Build Tools lokal installiert sind noch externe Gradle-/SDK-Downloads aus der Containerumgebung möglich sind. Der mitgelieferte Gradle-Wrapper und das komplette Android-Studio-Projekt sind vorhanden; in einer normalen Android-Buildumgebung lautet der Build `./gradlew assembleDebug`.
