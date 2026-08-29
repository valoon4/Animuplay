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

gradle = GRADLE.read_text(encoding="utf-8")n