# Bekannte Einschränkungen / offene Punkte

## System-Medienkarte wegwischen

Auf dem getesteten Samsung-/Android-System lässt sich eine aktive Medienkarte möglicherweise nicht zuverlässig wegwischen. Das Betriebssystem/OEM kann dies blockieren.

**Aktueller akzeptierter Workaround:** Das sichtbare X in der kompakten Mediennotification funktioniert und beendet Wiedergabe, Audio-Fokus, MediaSession und Notification.

## Kein echter Release-Build

Das Projekt verwendet bewusst einen festen Test-Debug-Key. Für eine spätere Veröffentlichung muss ein eigener sicher verwahrter Release-Key eingeführt werden. Den aktuellen Debug-Key nicht für einen Store-Build verwenden.

## Laufzeittests

Die Build-Umgebung hat Kompilierung, DEX, Ressourcen, Signatur, Alignment und Archivintegrität geprüft. Vollständige Laufzeit-QA erfolgt auf dem realen Android-Gerät.

## Bewusst nicht implementiert

- Playlist-Erstellung/-Bearbeitung
- allgemeine Queue/Warteschlange
- Equalizer
- Cloud/Streaming
- Internetfunktionen

Diese Punkte sind nicht automatisch Bugs; sie wurden als MVP-Scope bewusst weggelassen bzw. teilweise explizit abgelehnt.
