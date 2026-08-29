from pathlib import Path

MAIN = Path("app/src/main/java/de/minimal/musicplayer/MainActivity.java")
GRADLE = Path("app/build.gradle")

main = MAIN.read_text(encoding="utf-8")
gradle = GRADLE.read_text(encoding="utf-8")

needle = '''        searchRow.setVisibility(View.GONE);\n        if (groupFilterRow != null) groupFilterRow.setVisibility(View.GONE);\n        alphabetIndex.setVisibility(View.GONE);'''
replacement = '''        searchRow.setVisibility(View.GONE);\n        if (seasonModeRow != null) seasonModeRow.setVisibility(View.GONE);\n        if (groupFilterRow != null) groupFilterRow.setVisibility(View.GONE);\n        alphabetIndex.setVisibility(View.GONE);'''

# Apply only inside openPlayer(): the ANIME/RL selector belongs to Seasons,
# and must be hidden before the full player becomes visible.
player_start = main.index("    private void openPlayer() {")
player_end = main.index("    private void registerSystemBackHandler()", player_start)
player_block = main[player_start:player_end]
if needle not in player_block:
    raise SystemExit("Could not find player UI hide sequence")
player_block = player_block.replace(needle, replacement, 1)
main = main[:player_start] + player_block + main[player_end:]

gradle = gradle.replace("versionCode 24", "versionCode 25")
gradle = gradle.replace("versionName '0.14.6-debug'", "versionName '0.14.7-debug'")
if "versionCode 25" not in gradle or "versionName '0.14.7-debug'" not in gradle:
    raise SystemExit("Version bump failed")

MAIN.write_text(main, encoding="utf-8")
GRADLE.write_text(gradle, encoding="utf-8")
