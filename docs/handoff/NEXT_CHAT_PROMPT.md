# Prompt für einen neuen Chat

Kopiere den folgenden Text in einen neuen Chat, nachdem du dieses Handoff-Paket hochgeladen hast:

---

Ich möchte meinen Android-Musikplayer weiterentwickeln. Im hochgeladenen Handoff-Paket befindet sich der aktuelle Stand **v0.11** inklusive Debug-APK, vollständigem Source, festem Debug-Key, Screenshots und Projektdokumentation.

Bitte lies **zuerst**:

1. `00_START_HERE.md`
2. `Docs/PROJECT_CONTEXT.md`
3. `Docs/DO_NOT_BREAK.md`
4. `Docs/ARCHITECTURE.md`
5. bei Bedarf die bestehenden README-/QA-Dateien im Source-Projekt.

Arbeite auf `Source/Expanded/MinimalMusicPlayer/` bzw. dem exakten v0.11-Source weiter.

Wichtig: Bestehende Funktionen nicht unnötig verändern. Insbesondere die numerisch beginnenden Genre-Tags, Albumgruppierung, harte Suchlogik, M3U/M3U8-Pfadauflösung, Playcount-Logik und das Notification-X müssen erhalten bleiben.

Für die nächste Debug-APK unbedingt den vorhandenen `app/debug.keystore` verwenden und `versionCode` erhöhen, damit sie direkt über meine installierte v0.11 aktualisiert werden kann.

Meine nächste gewünschte Änderung ist:

[HIER ÄNDERUNG EINTRAGEN]

Nach der Änderung bitte wieder eine installierbare Debug-APK bauen und den Source mitliefern.

---
