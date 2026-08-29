from pathlib import Path

MAIN = Path("app/src/main/java/de/minimal/musicplayer/MainActivity.java")
GRADLE = Path("app/build.gradle")
README = Path("README.md")

main = MAIN.read_text(encoding="utf-8")
old_back = '''        // Only a real top-level screen is allowed to close the activity.\n        finish();'''
new_back = '''        // Top-level Back behaves like Home: keep the activity/process alive so\n        // current playback, queue, MediaSession and notification continue.\n        // Only the explicit playback X/stop action calls stopPlaybackAndDismiss().\n        moveTaskToBack(true);'''
if old_back not in main:
    raise SystemExit("Top-level finish() target not found")
main = main.replace(old_back, new_back, 1)
MAIN.write_text(main, encoding="utf-8")

gradle = GRADLE.read_text(encoding="utf-8")
old_version = "        versionCode 27\n        versionName '0.14.9-debug'"
new_version = "        versionCode 28\n        versionName '0.15.0-debug'"
if old_version not in gradle:
    raise SystemExit("v0.14.9 Gradle version target not found")
gradle = gradle.replace(old_version, new_version, 1)
GRADLE.write_text(gradle, encoding="utf-8")

readme = README.read_text(encoding="utf-8")
old_readme_version = "`0.14.9-debug` (`versionCode 27`)"
new_readme_version = "`0.15.0-debug` (`versionCode 28`)"
if old_readme_version not in readme:
    raise SystemExit("README version target not found")
readme = readme.replace(old_readme_version, new_readme_version, 1)
old_back_bullet = "- Hierarchical Android Back handling returns from player/group/playlist/detail screens before allowing the activity to close."
new_back_bullet = "- Hierarchical Android Back handling returns from player/group/playlist/detail screens first; top-level Back moves Animuplay to the background so playback, queue and media notification keep running."
if old_back_bullet not in readme:
    raise SystemExit("README Back bullet target not found")
readme = readme.replace(old_back_bullet, new_back_bullet, 1)
README.write_text(readme, encoding="utf-8")
