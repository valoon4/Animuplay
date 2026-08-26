# APK bauen

## Android Studio

1. Diesen Ordner in Android Studio öffnen.
2. Die vorgeschlagenen SDK-Komponenten installieren.
3. **Build → Build APK(s)** anklicken.
4. Ergebnis: `app/build/outputs/apk/debug/app-debug.apk`

## Debug-Signatur

`app/debug.keystore` ist absichtlich Teil dieses MVP-Testprojekts. Die Debug-Konfiguration in `app/build.gradle` verwendet diesen festen Key, damit spätere Test-APKs updatefähig bleiben.

- Alias: `androiddebugkey`
- Store-/Key-Passwort: `android`
- Nur für lokale Debug-Tests
- Niemals für eine Release-, Store- oder produktive Version verwenden

## GitHub Actions

Das Projekt enthält `.github/workflows/build-apk.yml`. Ein Workflow-Build verwendet durch die Projektkonfiguration denselben Test-Debug-Key.
