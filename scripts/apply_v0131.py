from pathlib import Path

main = Path('app/src/main/java/de/minimal/musicplayer/MainActivity.java')
build = Path('app/build.gradle')

text = main.read_text(encoding='utf-8')
old = '''        if (albums) {
            result.sort((a, b) -> a.name.compareToIgnoreCase(b.name));
        } else {
            result.sort((a, b) -> compareNewestFirst(a.name, b.name));
        }
        return result;
    }

    private List<GroupRow> buildYearGroups() {'''
new = '''        if (albums) {
            result.sort((a, b) -> a.name.compareToIgnoreCase(b.name));
        } else {
            result.sort((a, b) -> compareSeasonNames(a.name, b.name));
        }
        return result;
    }

    private static int compareSeasonNames(String left, String right) {
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

    private static int leadingYear(String value) {
        if (value == null || value.length() < 4) return -1;
        for (int i = 0; i < 4; i++) {
            if (!Character.isDigit(value.charAt(i))) return -1;
        }
        try {
            return Integer.parseInt(value.substring(0, 4));
        } catch (NumberFormatException ignored) {
            return -1;
        }
    }

    private List<GroupRow> buildYearGroups() {'''
if old not in text:
    if 'compareSeasonNames(a.name, b.name)' not in text:
        raise SystemExit('Expected season sort block not found')
else:
    text = text.replace(old, new, 1)
    main.write_text(text, encoding='utf-8')

b = build.read_text(encoding='utf-8')
b = b.replace("versionCode 14", "versionCode 15")
b = b.replace("versionName '0.13.0-debug'", "versionName '0.13.1-debug'")
build.write_text(b, encoding='utf-8')
