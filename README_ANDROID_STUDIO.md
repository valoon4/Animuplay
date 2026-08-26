# Minimal Music Player v0.12 — kompletter Android-Studio-Projektstand

Dies ist der v0.12-App-Stand auf Basis von v0.11, inklusive Gradle-Wrapper für direkte Builds.

## Build

Voraussetzungen:
- JDK 17
- Android SDK Platform 35 / Build Tools 35.x
- Internetzugang beim ersten Wrapper-Lauf (Gradle 8.11.1 wird geladen)

Linux/macOS:
```bash
./gradlew assembleDebug
```

Windows:
```bat
gradlew.bat assembleDebug
```

Erwartete APK:
`app/build/outputs/apk/debug/app-debug.apk`

## Wichtige Versionen
- Android Gradle Plugin: 8.9.1
- Gradle Wrapper: 8.11.1
- compileSdk / targetSdk: 35
- minSdk: 24
- Java: 17
- package: `de.minimal.musicplayer`
- app version: `0.12.0-debug` / versionCode 12

## Signatur
`app/debug.keystore` ist derselbe feste Testschlüssel wie in v0.10/v0.11 und muss beibehalten werden, damit v0.12 direkt über v0.11 installierbar bleibt.

Keystore:
- alias: `androiddebugkey`
- store password: `android`
- key password: `android`
- Zertifikat SHA-256: `63df019bdb5fbd06dee0cc7910cc81ed908dcd2d9ae9cfd8cc6e1d1c34404227`

## Kontext für Weiterentwicklung
Vor Änderungen bitte lesen:
- `docs/handoff/PROJECT_CONTEXT.md`
- `docs/handoff/DO_NOT_BREAK.md`
- `docs/handoff/ARCHITECTURE.md`
- `docs/handoff/NEXT_CHAT_PROMPT.md`

In v0.12 umgesetzt:
- bestehender Tab **Genres** heißt nun **Seasons**; die kritische Genre-Gruppierung bleibt technisch unverändert.
- direkt rechts daneben neuer Tab **Jahr**, gruppiert nach `MediaMetadataRetriever.METADATA_KEY_YEAR`; fehlende Werte erscheinen unter **Unbekannt**.
- beim Antippen eines direkten Songtreffers in der Suche wird die Bildschirmtastatur geschlossen und der Titel gestartet.

Beim ersten Start nach dem Update werden vorhandene v0.11-Cacheeinträge einmalig **im Hintergrund** um das Year-Metadatum ergänzt. Der vorhandene Cache wird trotzdem sofort angezeigt.

## Wrapper-Hinweis
Der Bootstrap-JAR ist ein kleiner kompatibler `GradleWrapperMain`, der die in `gradle-wrapper.properties` angegebene offizielle Gradle-8.11.1-Distribution lädt, deren offiziellen SHA-256-Wert prüft und anschließend Gradle startet. Die Projekt-/Gradle-Struktur entspricht dem üblichen Wrapper-Aufruf (`gradlew` / `gradlew.bat`).
