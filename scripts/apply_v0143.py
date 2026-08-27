from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

main_path = ROOT / "app/src/main/java/de/minimal/musicplayer/MainActivity.java"
text = main_path.read_text(encoding="utf-8")
old = '''        if (!TextUtils.isEmpty(searchInput.getText())) {\n            applySearch(searchInput.getText().toString());\n            return;\n        }\n        searchQuery = "";\n'''
new = '''        // SearchMatcher trims/collapses whitespace. Use the normalized value here too,\n        // otherwise a raw whitespace-only EditText recursively bounces between\n        // selectTab() and applySearch() until the stack overflows.\n        String pendingSearch = searchInput == null ? ""\n                : SearchMatcher.normalizeQuery(searchInput.getText().toString());\n        if (!pendingSearch.isEmpty()) {\n            applySearch(pendingSearch);\n            return;\n        }\n        searchQuery = "";\n'''
if old not in text:
    raise SystemExit("selectTab search block not found")
text = text.replace(old, new, 1)
main_path.write_text(text, encoding="utf-8")

build_path = ROOT / "app/build.gradle"
build = build_path.read_text(encoding="utf-8")
build = build.replace("versionCode 20", "versionCode 21", 1)
build = build.replace("versionName '0.14.2-debug'", "versionName '0.14.3-debug'", 1)
if "versionCode 21" not in build or "0.14.3-debug" not in build:
    raise SystemExit("version patch failed")
build_path.write_text(build, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
readme = readme.replace("`0.14.2-debug` (`versionCode 20`)", "`0.14.3-debug` (`versionCode 21`)", 1)
readme_path.write_text(readme, encoding="utf-8")

# The bootstrap workflow only needs this script for the current run.
Path(__file__).unlink()
