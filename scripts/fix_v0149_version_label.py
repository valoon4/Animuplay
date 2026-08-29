from pathlib import Path

path = Path("app/src/main/java/de/minimal/musicplayer/MainActivity.java")
text = path.read_text(encoding="utf-8")
old = '        versionText.setText("Version " + BuildConfig.VERSION_NAME);'
new = '''        String installedVersion = "";\n        try {\n            installedVersion = getPackageManager().getPackageInfo(getPackageName(), 0).versionName;\n        } catch (Exception ignored) { }\n        versionText.setText(TextUtils.isEmpty(installedVersion) ? "Version" : "Version " + installedVersion);'''
if old not in text:
    raise SystemExit("BuildConfig version label target not found")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
