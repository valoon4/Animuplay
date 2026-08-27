from pathlib import Path

main = Path('app/src/main/java/de/minimal/musicplayer/MainActivity.java')
build = Path('app/build.gradle')

text = main.read_text(encoding='utf-8')

# Track separately whether OP/ED buttons are allowed. Search remains available in
# Season and Year detail lists, but OP/ED belongs only to numeric Anime Seasons.
text = text.replace(
    '    private boolean groupSearchEnabled;\n    private boolean rlYearBrowserOpen;',
    '    private boolean groupSearchEnabled;\n    private boolean groupTypeFiltersEnabled;\n    private boolean rlYearBrowserOpen;',
    1,
)

old_sort = '''    private static int compareSeasonNames(String left, String right) {
        int leftYear = leadingYear(left);
        int rightYear = leadingYear(right);
        boolean leftNumeric = leftYear >= 0;
        boolean rightNumeric = rightYear >= 0;

        // Numeric seasons first, newest year first. Non-numeric labels stay normal A-Z.
        if (leftNumeric != rightNumeric) return leftNumeric ? -1 : 1;
        if (leftNumeric) {
            int byYear = Integer.compare(rightYear, leftYear);
            if (byYear != 0) return byYear;
            return right.compareToIgnoreCase(left);
        }
        return left.compareToIgnoreCase(right);
    }

    private static int leadingYear(String value) {'''
new_sort = '''    private static int compareSeasonNames(String left, String right) {
        int leftYear = leadingYear(left);
        int rightYear = leadingYear(right);
        boolean leftNumeric = leftYear >= 0;
        boolean rightNumeric = rightYear >= 0;

        // 1) Numeric Anime seasons: newest year first.
        if (leftNumeric != rightNumeric) return leftNumeric ? -1 : 1;
        if (leftNumeric) {
            int byYear = Integer.compare(rightYear, leftYear);
            if (byYear != 0) return byYear;
            return right.compareToIgnoreCase(left);
        }

        // 2) RL_YYYY seasons: also newest first, but after numeric Anime seasons.
        int leftRlYear = rlSeasonYear(left);
        int rightRlYear = rlSeasonYear(right);
        boolean leftRl = leftRlYear >= 0;
        boolean rightRl = rightRlYear >= 0;
        if (leftRl != rightRl) return leftRl ? -1 : 1;
        if (leftRl) {
            int byYear = Integer.compare(rightRlYear, leftRlYear);
            if (byYear != 0) return byYear;
            return left.compareToIgnoreCase(right);
        }

        // 3) Everything else stays normal A-Z (Special, Unbekannt, etc.).
        return left.compareToIgnoreCase(right);
    }

    private static int rlSeasonYear(String value) {
        if (value == null || !value.regionMatches(true, 0, "RL_", 0, 3)) return -1;
        for (int start = 3; start + 4 <= value.length(); start++) {
            boolean digits = true;
            for (int i = 0; i < 4; i++) {
                if (!Character.isDigit(value.charAt(start + i))) {
                    digits = false;
                    break;
                }
            }
            if (!digits) continue;
            try {
                return Integer.parseInt(value.substring(start, start + 4));
            } catch (NumberFormatException ignored) {
                return -1;
            }
        }
        return -1;
    }

    private static int leadingYear(String value) {'''
if old_sort in text:
    text = text.replace(old_sort, new_sort, 1)
elif 'private static int rlSeasonYear(String value)' not in text:
    raise SystemExit('Expected season comparator not found')

old_open = '''        groupSearchEnabled = !group.playlistGroup && !group.albumGroup
                && (libraryMode == MODE_GENRES || libraryMode == MODE_YEARS);
        groupTypeFilter = "";
        groupTitle = group.name;'''
new_open = '''        groupSearchEnabled = !group.playlistGroup && !group.albumGroup
                && (libraryMode == MODE_GENRES || libraryMode == MODE_YEARS);
        groupTypeFiltersEnabled = groupSearchEnabled
                && libraryMode == MODE_GENRES && leadingYear(group.name) >= 0;
        groupTypeFilter = "";
        groupTitle = group.name;'''
if old_open in text:
    text = text.replace(old_open, new_open, 1)
elif 'groupTypeFiltersEnabled = groupSearchEnabled' not in text:
    raise SystemExit('Expected group-open filter block not found')

old_visibility = '''            searchInput.setHint("In dieser Gruppe suchen");
            searchRow.setVisibility(View.VISIBLE);
            groupFilterRow.setVisibility(View.VISIBLE);
            updateGroupFilterButtons();'''
new_visibility = '''            searchInput.setHint("In dieser Gruppe suchen");
            searchRow.setVisibility(View.VISIBLE);
            groupFilterRow.setVisibility(groupTypeFiltersEnabled ? View.VISIBLE : View.GONE);
            if (groupTypeFiltersEnabled) updateGroupFilterButtons();'''
if old_visibility in text:
    text = text.replace(old_visibility, new_visibility, 1)
elif 'groupFilterRow.setVisibility(groupTypeFiltersEnabled ? View.VISIBLE : View.GONE);' not in text:
    raise SystemExit('Expected group filter visibility block not found')

text = text.replace(
    '    private void toggleGroupTypeFilter(String type) {\n        if (!groupSearchEnabled) return;',
    '    private void toggleGroupTypeFilter(String type) {\n        if (!groupSearchEnabled || !groupTypeFiltersEnabled) return;',
    1,
)

# Reset the new state everywhere the group search UI is reset.
text = text.replace(
    '        groupSearchEnabled = false;\n        groupTypeFilter = "";\n        groupTitle = "";',
    '        groupSearchEnabled = false;\n        groupTypeFiltersEnabled = false;\n        groupTypeFilter = "";\n        groupTitle = "";',
)
text = text.replace(
    '        groupOpen = true;\n        groupSearchEnabled = false;\n        if (groupFilterRow != null)',
    '        groupOpen = true;\n        groupSearchEnabled = false;\n        groupTypeFiltersEnabled = false;\n        if (groupFilterRow != null)',
    1,
)

main.write_text(text, encoding='utf-8')

b = build.read_text(encoding='utf-8')
b = b.replace('versionCode 15', 'versionCode 16')
b = b.replace("versionName '0.13.1-debug'", "versionName '0.13.2-debug'")
build.write_text(b, encoding='utf-8')
