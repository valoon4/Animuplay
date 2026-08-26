# Änderungen v0.12

1. **Genres → Seasons**
   - Derselbe bestehende Tab und dieselbe Genre-Rohstring-Gruppierung.
   - Keine zusätzliche Überschrift oder Unteransicht.

2. **Neuer Tab Jahr**
   - Direkt rechts neben `Seasons`.
   - Gruppiert nach `MediaMetadataRetriever.METADATA_KEY_YEAR`.
   - Fehlende Angaben: `Unbekannt`.
   - v0.11-Cacheformat wird weiter gelesen; fehlende Year-Felder werden einmalig unsichtbar im Hintergrund nachgeladen und danach im neuen Cacheformat gespeichert.

3. **Suche / Tastatur**
   - Bei einem direkten Songtreffer wird vor dem Starten die Bildschirmtastatur geschlossen.
   - Suchlogik selbst bleibt unverändert.

4. **Unverändert**
   - numerisch beginnende Genre/Season-Tags
   - Albumgruppierung und Tracknummern
   - harte Suche Album → Song → Interpret
   - M3U/M3U8
   - Playcount/Top 50
   - Player, Repeat One, MediaSession und Notification-X
