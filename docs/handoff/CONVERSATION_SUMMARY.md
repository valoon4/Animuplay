# Entwicklungsgeschichte in Kurzform

## Ausgangspunkt

Gewünscht war ein extrem simples Android-Musikplayer-MVP mit frei wählbarem Musikordner, MP3/FLAC-Unterstützung und Sortierung nach Songs, Alben und Genres.

Der wichtigste Spezialfall war von Anfang an die korrekte Behandlung ungewöhnlicher Genres wie `2012_3.Summer`, weil andere Musikplayer solche Tags häufig falsch interpretieren.

## Wichtige Iterationen

- Grundplayer mit Ordnerwahl, Songs/Alben/Genres und Wiedergabe.
- Scanfortschritt `X/Y` für große Bibliotheken.
- Genre-Rohdatenfix für numerisch beginnende Genres.
- Persistenter Bibliothekscache und inkrementeller Hintergrundscan.
- Suche sowie A–Z-Schnellsprung.
- Suche später bewusst von fuzzy auf harte Teilstrings umgestellt und gruppiert: Album → Song → Interpret.
- Audio-Fokus und Android MediaSession/Benachrichtigung.
- Repeat-One als simples `1`.
- Anime/Weeb-App-Icon.
- Playcount nach >50 % tatsächlich gehörter Laufzeit und Top 50.
- `.m3u`/`.m3u8`-Import mit automatischem Mapping alter PC-Pfade auf Android.
- Genre und Tracknummer in der großen Wiedergabeansicht.
- funktionierendes X in der Mediennotification zum vollständigen Stoppen.

## Produktphilosophie

Die App soll kein universeller Poweramp-Klon werden. Sie soll für die reale große Bibliothek des Nutzers zuverlässig sein, vorhandene Metadaten respektieren und nur Funktionen bekommen, die einen konkreten Nutzen haben.
