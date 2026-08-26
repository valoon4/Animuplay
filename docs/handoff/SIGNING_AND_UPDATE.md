# Debug-Signatur und Updatefähigkeit

Update-Basis: v0.11; aktueller Source-Stand: v0.12.

Package: `de.minimal.musicplayer`

Signer certificate SHA-256 laut geprüftem v0.11-Build:

`63df019bdb5fbd06dee0cc7910cc81ed908dcd2d9ae9cfd8cc6e1d1c34404227`

APK SHA-256 v0.11:

`175ed8b3be9b70fc88dbafa08c28aa422139684c339d29ebb90073b316c7bc5c`

Der feste Test-Key liegt unter:

`Source/Expanded/MinimalMusicPlayer/app/debug.keystore`

und ebenfalls im unveränderten Original-Source-ZIP.

Konfiguration:

- Alias: `androiddebugkey`
- Store-Passwort: `android`
- Key-Passwort: `android`

## Für die nächste APK

- denselben `applicationId` verwenden
- denselben Debug-Key verwenden
- v0.12 verwendet `versionCode 12` und `versionName 0.12.0-debug`
- für folgende Builds `versionCode > 12` verwenden

Den Debug-Key **nicht neu erzeugen**, sonst verlangt Android eine Deinstallation und App-Daten/Playcounts können verloren gehen.

Der Key ist nur ein Testschlüssel und nicht für eine öffentliche Release-Version geeignet.
