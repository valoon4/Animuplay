# Architektur / Code-Navigation

Das MVP ist absichtlich klein und verwendet überwiegend Android-Bordmittel.

## Wichtige Dateien

### `app/src/main/java/de/minimal/musicplayer/MainActivity.java`

Zentrale Activity und aktuell der größte Teil der App-Logik/UI-Verkabelung. Enthält Bibliotheksdarstellung, Navigation, Playersteuerung, MediaSession/Notification-Anbindung und viele UI-Abläufe.

Bei Refactorings vorsichtig sein: Ein großer Umbau erhöht unnötig das Risiko, funktionierende Spezialfälle zu beschädigen.

### `Song.java`

Datenmodell für einen Musiktitel. Seit v0.12 enthält es zusätzlich das echte `year`-Metadatum.

### `GenreTagReader.java`

**Besonders kritisch.** Liest Genre-Rohdaten aus MP3-ID3v2 und FLAC-Vorbis, damit ungewöhnliche Genre-Tags nicht von Androids Standard-Metadateninterpretation beschädigt werden.

### `LibraryIndex.java`

Persistenter Bibliotheksindex/Cache für schnelle Folgestarts und inkrementelle Aktualisierung. Cacheformat v2 speichert zusätzlich `year` und kann v1 aus v0.11 rückwärtskompatibel laden.

### `M3uPlaylistReader.java`

Parser und Pfadauflösung für `.m3u`/`.m3u8`, einschließlich PC-Pfad-Mapping und URI-Decoding.

### `PlayHistory.java`

Wiedergabezähler / Top-50-Statistik und portables Profil im Musikordner.

### `SearchMatcher.java`

Harte normalisierte Teilstring-Suche. Keine Fuzzy-Suche hinzufügen, sofern nicht ausdrücklich gewünscht.

### `AlphabetIndexView.java`

A–Z-Schnellsprung am rechten Listenrand.

### `PlaybackActionReceiver.java`

Verarbeitet Aktionen aus Mediennotification/Delete-Intent, insbesondere das funktionierende X/Stop-Verhalten ohne Activity in den Vordergrund zu holen.

## Ressourcen

- `app/src/main/res/layout/activity_main.xml` — Hauptlayout.
- `app/src/main/res/mipmap-*/ic_launcher.png` — Launcher-Icon.
- `docs/app-icon-v0.8.png` — Icon-Referenz im Source-Projekt.
- `docs/PLAYLIST_IMPORT.md` — kurze technische Importbeschreibung.

## Build

Gradle-Projekt, Java 17, compile/target SDK 35, min SDK 24.

Der feste Test-Debug-Key liegt unter:

`app/debug.keystore`

Alias: `androiddebugkey`

Store-/Key-Passwort: `android`

Dieser Key ist absichtlich öffentlich im Testprojekt und **niemals** für einen Release-/Store-Build gedacht.
