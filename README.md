# Minimal Music Player (Android MVP) — v0.12

Ein bewusst kleiner lokaler Musikplayer für große MP3- und FLAC-Bibliotheken.

## Enthalten

- Ordnerauswahl über Androids Storage Access Framework
- Rekursive Erkennung von `.mp3` und `.flac`
- Sichtbarer Fortschritt beim ersten Metadaten-Scan (`X / Y`)
- Persistenter Bibliotheksindex; spätere Starts zeigen den Cache sofort und prüfen Änderungen im Hintergrund
- Metadaten: Titel, Interpret, Album, Tracknummer, Dauer, Genre/Season und Jahr
- Eigener Rohdatenleser für MP3-ID3v2-`TCON` und FLAC-Vorbis-`GENRE`
- Numerisch beginnende Genre-Tags bleiben exakt erhalten, z. B. `2012_3.Summer`
- Songs A–Z, Album-, Seasons- und Jahresansicht sowie gruppenbezogene Zufallswiedergabe
- Suche nach Album, Songtitel und Interpret; Genres werden nicht durchsucht
- A–Z-Schnellsprung am rechten Listenrand
- Audio-Fokus, MediaSession und Medienbenachrichtigung
- Repeat-One-Schalter als schlichtes `1`
- Album, Tracknummer und Genre in der großen Wiedergabeansicht
- Eingebettete Cover, sofern vorhanden
- Wiedergabezähler nach mehr als 50 % tatsächlich gehörter Zeit
- Top 50 meistgespielte Titel mit Zufallswiedergabe
- Automatischer `.m3u`/`.m3u8`-Import aus dem gewählten Musikordner
- Android 7.0 (API 24) oder neuer

## Playcount-Profil

Die Wiedergabezähler werden weiterhin intern gespiegelt und zusätzlich portabel im ausgewählten Musikordner gespeichert:

```text
MinimalMusicPlayer/profile.json
```

Die Einträge verwenden relative Musikpfade. Dadurch bleiben Statistiken nach einer späteren Neuinstallation erhalten, sofern wieder derselbe Musik-Hauptordner ausgewählt wird. Falls der Dokumentanbieter den Ordner nicht beschreibbar bereitstellt, bleibt der interne App-Speicher als Fallback aktiv.

## Mediensteuerung

Die MediaSession veröffentlicht Position, Geschwindigkeit und einen aktuellen Zeitstempel. Dadurch kann Android den Fortschritt auf Sperrbildschirm und Medienleiste weiterrechnen. Zusätzlich wird der Zustand während der Wiedergabe regelmäßig synchronisiert.

Version 0.11 erzwingt die Stop-/X-Aktion in den drei kompakten Benachrichtigungsaktionen und verarbeitet Benachrichtigungsaktionen über einen eigenen BroadcastReceiver, ohne die Activity in den Vordergrund zu holen. Ein erlaubtes Wegwischen verwendet dasselbe Stop-Signal. Manche Hersteller-Oberflächen blockieren das Wegwischen aktiver Medienkarten grundsätzlich; dort ist das sichtbare X der vorgesehene Abschlussweg.

## Playlist-Import

Die App sucht rekursiv im ausgewählten Musikordner nach `.m3u` und `.m3u8`. Es ist kein separater Importordner nötig.

Unter **Sonstiges → Playlists** werden die gefundenen Dateien angezeigt. Beim Öffnen einer Playlist bleibt die Reihenfolge aus der Datei erhalten. Doppelte Einträge bleiben ebenfalls erhalten. Die vorhandene Zufallswiedergabe kann innerhalb der geöffneten Playlist verwendet werden.

### Pfade vom PC

Desktop-Pfade werden automatisch auf den ausgewählten Android-Musikordner abgebildet. Beispiel:

```text
file:///F:/Musik/2025/Doctor%20Stone%20-%20Science%20Future%20OP.flac
```

wird vollständig URI-dekodiert und über den relativen Teil

```text
2025/Doctor Stone - Science Future OP.flac
```

im Android-Musikordner gesucht. Unterstützt werden vollständige UTF-8-Prozentkodierung, echte Pluszeichen, Windows-Backslashes, absolute Windows-Pfade, relative Pfade sowie übliche M3U/M3U8-Zeichenkodierungen.

Nicht gefundene Einträge brechen den Import nicht ab. Pro Playlist wird beispielsweise `117 von 120 Titeln gefunden` angezeigt. Die App liest Playlists nur ein; Erstellen oder Bearbeiten ist in diesem MVP nicht enthalten.

## Suche

Die Suche arbeitet als harte, normalisierte Teiltextsuche ohne Tippfehlertoleranz. Ergebnisse erscheinen in dieser Reihenfolge:

1. passende Alben als Gruppen
2. passende Songtitel
3. passende Interpreten als Gruppen

Durchsucht werden ausschließlich Album, Songtitel und Interpret.

## Datenschutz

Die App benötigt keine Internetberechtigung. Sie liest nur den ausdrücklich ausgewählten Ordner. Bibliotheksindex und ein Fallback der Wiedergabezähler liegen im internen App-Speicher; das portable Statistikprofil liegt im ausgewählten Musikordner.

## Debug-Signatur

Das Projekt enthält absichtlich einen festen **Test-Debug-Key**, damit weitere Debug-APKs direkt aktualisiert werden können. Dieser Schlüssel ist öffentlich im Quellpaket und darf niemals für eine Release- oder Store-Version verwendet werden.

## Neu in v0.12

- Bestehender Tab `GENRES` wurde ohne zusätzliche Ebene in `SEASONS` umbenannt.
- Neuer Tab `JAHR` direkt rechts daneben; Gruppierung basiert ausschließlich auf dem echten Year-Metadatum (`METADATA_KEY_YEAR`).
- Songs ohne Year-Metadatum landen unter `Unbekannt`.
- v0.11-Bibliothekscache ist rückwärtskompatibel; fehlende Year-Werte werden einmalig im Hintergrund angereichert und danach im Cacheformat v2 gespeichert.
- Beim Antippen eines direkten Songtreffers in der Suche schließt sich die Bildschirmtastatur sofort.
- Bestehende Genre-Rohdatenauswertung, Suche, Albumgruppierung, Playlists, Playcount und Playerfunktionen wurden nicht absichtlich verändert.
