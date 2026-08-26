# MVP-Prüfbericht — Version 0.11

## Automatisch geprüft

- Java-Quellcode gegen Android API 35 kompiliert: **bestanden**
- Android-Ressourcen einschließlich `playerTrackNumber` und eigenem X-Icon mit AAPT2 kompiliert: **bestanden**
- DEX-Erzeugung mit D8: **bestanden**
- Paket `de.minimal.musicplayer`, `versionCode 11`, `versionName 0.11.0-debug`: **bestanden**
- Mindestversion Android 7.0 / API 24: **bestanden**
- Keine `INTERNET`-Berechtigung: **bestanden**
- APK-Archivintegrität (`unzip -t`): **bestanden**
- ZIP-Alignment: **bestanden**
- APK Signature Scheme v2 und v3: **bestanden**
- Signaturzertifikat identisch zu v0.10 (`63df019b…404227`): **bestanden**

## Tracknummer

- Neue Zeile zwischen Album und Genre zeigt bei vorhandener Tracknummer `Nummer: X`.
- Bei fehlender oder ungültiger Tracknummer wird die Zeile ausgeblendet.
- `METADATA_KEY_TRACK_NUMBER` wird zusätzlich in der Android-MediaSession gesetzt.
- Bestehende Tracksortierung in der Albumansicht wurde nicht verändert.

## Medienabschluss

- Notification-Aktionen werden über einen expliziten, nicht exportierten `PlaybackActionReceiver` verarbeitet.
- Die Stop-/X-Aktion liegt als dritte Aktion in der kompakten Medienbenachrichtigung.
- `PlaybackState` enthält zusätzlich eine Custom-Action **Beenden** mit eigenem X-Icon.
- Das Delete-Intent beim erlaubten Wegwischen sendet dasselbe Stop-Signal.
- Stop leert Player und Queue, gibt Audio-Fokus frei, setzt die MediaSession auf gestoppt/inaktiv und entfernt die Benachrichtigung.

## Bestehende Funktionen

Genre-Rohdatenauswertung, Suche, Albumgruppierung, A–Z-Navigation, Top 50, Wiedergabezähler, M3U/M3U8-Import, Cache, Hintergrundscan und Repeat-One wurden nicht absichtlich verändert.

## Einschränkungen

Ein Laufzeittest auf einem echten Android-Gerät oder Emulator war in dieser Build-Umgebung nicht möglich. Insbesondere Samsung und andere Hersteller können das Wegwischen einer **aktiven** System-Medienkarte unabhängig von `setOngoing(false)` blockieren. In diesem Fall soll die nun kompakt sichtbare X-Aktion die Wiedergabe zuverlässig beenden. Die tatsächliche Darstellung der System-Medienoberfläche muss auf dem Zielgerät geprüft werden.
