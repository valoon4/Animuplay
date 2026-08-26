# DO NOT BREAK — kritische Invarianten

Diese Punkte sind bei jeder weiteren Änderung zu erhalten, außer der Nutzer verlangt ausdrücklich etwas anderes.

1. **Numerische Genre-Tags exakt erhalten.** `2012_3.Summer`, `RL_1977_4.Fall`, `2026_2.Spring` dürfen niemals zu Standard-Genrecodes umgedeutet oder verworfen werden.
2. **Albumgruppierung nicht unnötig ändern.** Die aktuelle Gruppierung funktioniert auf der realen Bibliothek besser als frühere Fremdplayer.
3. **Suche bleibt hart, nicht fuzzy.** Reihenfolge: Albumgruppen → Songtitel → Interpretengruppen. Genre nicht durchsuchen.
4. **Keine Queue/Warteschlange hinzufügen**, sofern nicht ausdrücklich neu gewünscht.
5. **Cache zuerst anzeigen.** Bei vorhandenem Bibliothekscache Änderungen im Hintergrund prüfen, keinen sichtbaren minutenlangen Vollscan vortäuschen.
6. **Playcount zählt echte Hörzeit.** Erst >50 % tatsächlich gehört = +1; Vorspulen allein reicht nicht.
7. **Playlist-Reihenfolge und Duplikate erhalten.** Fehlende Dateien dürfen den Rest der Playlist nicht zerstören.
8. **M3U8-Pfade robust dekodieren.** Vollständiges Percent-/UTF-8-Decoding, echtes `+` erhalten, Windows-/relative Pfade unterstützen.
9. **Package-ID beibehalten:** `de.minimal.musicplayer`.
10. **Debug-Signatur beibehalten.** `app/debug.keystore` nicht regenerieren/ersetzen. Sonst lässt sich die neue APK nicht über v0.11 installieren.
11. **Version bei jedem Build erhöhen.** Nach v0.12 `versionCode > 12` und passend neuer `versionName`.
12. **Keine Internetberechtigung hinzufügen**, sofern nicht ausdrücklich erforderlich und genehmigt.
13. **Tracknummer in Now Playing behalten:** Album → `Nummer: X` → Genre.
14. **Repeat-One UI bleibt schlichtes `1`.**
15. **Notification-X muss weiter funktionieren.** Es ist auf dem Zielgerät der zuverlässige Weg, die Medienwiedergabe vollständig zu beenden.
