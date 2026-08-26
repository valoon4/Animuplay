# PROJECT CONTEXT — Minimal Music Player

## Projektziel

Minimalistischer lokaler Android-Musikplayer für eine sehr große persönliche Musikbibliothek (ca. 10.000 Titel). Die App soll absichtlich schlank bleiben und dort korrekt sein, wo andere Player bei Metadaten, Albumgruppierung, Genres und Playlists Probleme machen.

Aktueller Stand: **v0.12.0-debug**, `versionCode 12`.

Package: `de.minimal.musicplayer`

Android: Minimum API 24 / Android 7.0, compile/target API 35.

Keine Internetberechtigung.

## Grundprinzip

Bestehende Funktionen möglichst **nicht verändern**, wenn eine neue Anforderung das nicht zwingend erfordert. Der Nutzer bevorzugt ein stabiles MVP statt Feature-Bloat.

## Bibliothek und Scan

- Auswahl eines Musik-Hauptordners über Android Storage Access Framework.
- Rekursive Erkennung von `.mp3` und `.flac`.
- Beim allerersten Scan sichtbarer Fortschritt `X / Y`.
- Danach persistenter Bibliotheksindex.
- Bei späteren App-Starts wird der Cache sofort angezeigt.
- Änderungen werden im Hintergrund geprüft; dieser Änderungscheck soll bei vorhandenem Cache nicht störend als Vollscan-UI erscheinen.
- Eine kurze Toast-Zusammenfassung nach Änderungen ist erwünscht.

## Metadaten — besonders kritisch

Metadaten: Titel, Interpret, Album, Tracknummer, Dauer, Genre/Season, Jahr und eingebettetes Cover.

**Höchste Priorität des Projekts:** Genre-Tags müssen als echte Rohstrings erhalten bleiben. Numerisch beginnende oder ungewöhnlich formatierte Genres dürfen NICHT als ID3-Genrecodes interpretiert, zerlegt oder verworfen werden.

Beispiele, die korrekt und exakt angezeigt werden müssen:

- `2012_3.Summer`
- `RL_1977_4.Fall`
- `2026_2.Spring`

Dafür existiert `GenreTagReader.java`, der MP3-ID3v2-`TCON` und FLAC-Vorbis-`GENRE` explizit behandelt.

## Ansichten

Tabs:

1. Songs
2. Alben
3. Seasons
4. Jahr
5. Sonstiges

### Songs

- Standardmäßig A–Z.
- A–Z-Schnellsprung am rechten Rand für große Listen.

### Alben

- Albumgruppierung ist aktuell auf der echten Bibliothek sehr gut und soll nicht unnötig geändert werden.
- Titel innerhalb eines Albums werden nach Tracknummer sortiert.
- Ziel: Ein Album bleibt ein gemeinsamer Entry statt zufällig in mehrere Gruppen zu zerfallen.

### Seasons

- Der frühere Genre-Tab heißt in der UI `Seasons`; technisch bleibt es dieselbe Gruppierung nach Genre-Rohstring.
- Die oben beschriebenen numerisch beginnenden Strings müssen unverändert funktionieren.
- Zufallswiedergabe innerhalb eines geöffneten Season/Genre-Eintrags ist möglich.

### Jahr

- Gruppiert ausschließlich nach dem echten Year-Metadatum des Songs (`MediaMetadataRetriever.METADATA_KEY_YEAR`).
- Fehlendes Year landet unter `Unbekannt`.
- Der A–Z-Schnellsprung wird in dieser numerischen Ansicht nicht eingeblendet.
- Beim Update von v0.11 wird das fehlende Year-Feld im vorhandenen Cache einmalig im Hintergrund nachgeladen.

### Sonstiges

Enthält aktuell u. a.:

- Top 50 meistgespielte Songs
- Playlists

## Suche

Die Suche ist bewusst **nicht fuzzy**.

Es gilt harte normalisierte Teilstring-Suche. Beispiel: `Liar Game` findet echte Teiltreffer, aber keine ungefähr ähnlichen Schreibweisen.

Ergebnisreihenfolge:

1. passende **Alben als Gruppen**
2. passende **Songtitel**
3. passende **Interpreten als Gruppen**

Genres werden ausdrücklich **nicht durchsucht**.

## Player

Funktionen:

- Play/Pause
- Previous
- Next
- Repeat One
- Audio-Fokus
- Android MediaSession
- Medienbenachrichtigung / Sperrbildschirmsteuerung
- eingebettete Albumcover

Repeat One wird absichtlich nur als schlichtes `1` dargestellt:

- grau = aus
- lila/hell = aktiv

### Große Wiedergabeansicht

Reihenfolge der Metadaten:

1. Cover
2. Songtitel
3. Interpret
4. Album
5. `Nummer: X`
6. Genre

Bei fehlender Tracknummer wird `Nummer: X` ausgeblendet.

Lange Titel/Interpreten/Alben/Genres sollen einzeilig bleiben und als Marquee horizontal laufen statt hässlich umzubrechen.

### Medienabschluss

v0.11 hat ein sichtbares **X** in der kompakten Medienbenachrichtigung. Dieses X funktioniert auf dem echten Zielgerät und beendet den Player vollständig.

Ein aktives Wegwischen der System-Medienkarte kann je nach Samsung-/Android-Version weiterhin vom OS blockiert sein. Das ist derzeit akzeptiert; das X ist der zuverlässige Abschlussweg.

## Playcount / Statistik

Ein Song erhält `playCount + 1`, wenn **mehr als 50 % der tatsächlichen Laufzeit gehört** wurden.

Wichtig: Nur auf >50 % vorzuspulen darf nicht sofort zählen.

Unter `Sonstiges` gibt es **Top 50 meistgespielt** mit Zufallswiedergabe.

Die Statistik wird intern gespiegelt und zusätzlich portabel im ausgewählten Musikordner gespeichert:

`MinimalMusicPlayer/profile.json`

Die Zuordnung erfolgt über relative Musikpfade. Falls der Ordner nicht beschreibbar ist, bleibt der interne Speicher als Fallback.

## M3U / M3U8 Playlists

Die App scannt den ausgewählten Musik-Hauptordner rekursiv zusätzlich nach `.m3u` und `.m3u8`.

Playlists werden nur **eingelesen**, nicht erstellt oder bearbeitet.

Unter `Sonstiges → Playlists` werden gefundene Playlists angezeigt.

Eigenschaften:

- Reihenfolge aus der Playlist erhalten.
- Doppelte Einträge erhalten.
- Zufallswiedergabe innerhalb der geöffneten Playlist.
- Fehlende Dateien brechen den Import nicht ab.
- Anzeige z. B. `117 von 120 Titeln gefunden`.

### PC-Pfad-Mapping

Beispiel aus echter Playlist:

```text
#EXTM3U
#EXTINF:240,ALI - CASANOVA POSSE
file:///F:/Musik/2025/Doctor%20Stone%20-%20Science%20Future%20OP.flac
```

Auf Android soll der alte PC-Basisordner automatisch auf den vom Nutzer ausgewählten Musik-Hauptordner abgebildet werden.

Aus:

`file:///F:/Musik/2025/Doctor%20Stone%20-%20Science%20Future%20OP.flac`

wird logisch der relative Pfad:

`2025/Doctor Stone - Science Future OP.flac`

Wichtig:

- vollständiges URI-/Percent-Decoding, nicht nur `%20`
- UTF-8-Sonderzeichen unterstützen
- `%23` etc. korrekt dekodieren
- echtes `+` darf **nicht** als Leerzeichen missverstanden werden
- `/` und `\` unterstützen
- relative Pfade unterstützen
- bei mehreren gleichen Dateinamen nur sicher zuordnen

Parser: `M3uPlaylistReader.java`.

## Design

- Dark Theme
- lila/neon Akzente
- bewusst schlicht
- Anime/Weeb-App-Icon ist eingebaut
- kein großer UI-Umbau ohne ausdrücklichen Wunsch

Referenz-Icon und Gerätescreenshots befinden sich im Handoff-Paket.

## Nutzerentscheidungen, die respektiert werden sollen

- Keine Warteschlange/Queue als neues Feature ohne ausdrückliche Nachfrage; wurde bewusst abgelehnt.
- Wiedergabestatus nach App-Neustart vollständig wiederherzustellen war bisher nicht wichtig genug.
- Playlist-Import ist wichtiger als Playlist-Erstellung.
- Keine fuzzy Suche.
- Bestehendes Verhalten möglichst nicht anfassen, wenn nicht nötig.

## Realgerät / QA

Automatische Build-/Paketprüfungen wurden durchgeführt, aber die eigentliche Laufzeit-QA erfolgt auf einem realen Samsung-Android-Gerät des Nutzers.

Gerätescreenshots im Ordner `ReferenceScreenshots/` dokumentieren wichtige Zustände.
