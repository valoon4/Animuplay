# M3U/M3U8-Import

1. Lege `.m3u`- oder `.m3u8`-Dateien an eine beliebige Stelle innerhalb des in der App ausgewählten Musikordners.
2. Starte die App oder wähle den Musikordner erneut, damit der Hintergrundscan läuft.
3. Öffne **Sonstiges → Playlists**.
4. Die Anzeige `X von Y Titeln gefunden` zeigt, ob alle Pfade zugeordnet werden konnten.

Absolute PC-Pfade müssen vor dem Kopieren nicht manuell geändert werden. Die App verwendet den Teil des Pfades, der innerhalb der Musikbibliothek liegt. Aus `F:/Musik/2025/Titel.flac` wird beispielsweise `2025/Titel.flac`, sofern der ausgewählte Android-Ordner dem früheren PC-Ordner `F:/Musik` entspricht.

Bei mehreren Dateien mit exakt gleichem Namen ist ein relativer Unterordnerpfad wichtig. Ein reiner Dateiname wird aus Sicherheitsgründen nur zugeordnet, wenn er in der Bibliothek eindeutig ist.
