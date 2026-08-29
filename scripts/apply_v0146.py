from pathlib import Path

MAIN = Path("app/src/main/java/de/minimal/musicplayer/MainActivity.java")
MATCHER = Path("app/src/main/java/de/minimal/musicplayer/SearchMatcher.java")
GRADLE = Path("app/build.gradle")

main = MAIN.read_text(encoding="utf-8")
matcher = MATCHER.read_text(encoding="utf-8")
gradle = GRADLE.read_text(encoding="utf-8")

# SearchMatcher: add a leading-quote exact, case-sensitive search mode.
old_matcher = '''    static String normalizeQuery(String value) {
        return normalize(value).trim().replaceAll("\\\\s+", " ");
    }

    static boolean contains(String value, String normalizedQuery) {
        return !normalizedQuery.isEmpty() && normalize(value).contains(normalizedQuery);
    }
'''
new_matcher = '''    static String normalizeQuery(String value) {
        return normalize(value).trim().replaceAll("\\\\s+", " ");
    }

    static boolean isDirectQuote(String value) {
        return value != null && value.startsWith("\\\"");
    }

    static String queryText(String value) {
        if (!isDirectQuote(value)) return normalizeQuery(value);
        String exact = value.substring(1).trim();
        // A closing quote is optional. If supplied, ignore it for convenience.
        if (exact.endsWith("\\\"") && exact.length() > 1) {
            exact = exact.substring(0, exact.length() - 1).trim();
        }
        return exact;
    }

    static boolean isEmptyQuery(String value) {
        return queryText(value).isEmpty();
    }

    static boolean matches(String value, String query, boolean directQuote) {
        if (query.isEmpty()) return false;
        return directQuote ? safe(value).contains(query) : normalize(value).contains(query);
    }

    static boolean contains(String value, String normalizedQuery) {
        return !normalizedQuery.isEmpty() && normalize(value).contains(normalizedQuery);
    }
'''
if old_matcher not in matcher:
    raise SystemExit("SearchMatcher insertion point not found")
matcher = matcher.replace(old_matcher, new_matcher, 1)

# Keep the raw query until applySearch so a leading quote can preserve case.
old_pending = '''        // SearchMatcher trims/collapses whitespace. Use the normalized value here too,
        // otherwise a raw whitespace-only EditText recursively bounces between
        // selectTab() and applySearch() until the stack overflows.
        String pendingSearch = searchInput == null ? ""
                : SearchMatcher.normalizeQuery(searchInput.getText().toString());
        if (!pendingSearch.isEmpty()) {
            applySearch(pendingSearch);
            return;
        }
'''
new_pending = '''        // Preserve the raw query here so a leading quote can enable case-sensitive
        // direct-quote search. SearchMatcher still treats whitespace-only input as empty.
        String pendingSearch = searchInput == null ? "" : searchInput.getText().toString();
        if (!SearchMatcher.isEmptyQuery(pendingSearch)) {
            applySearch(pendingSearch);
            return;
        }
'''
if old_pending not in main:
    raise SystemExit("selectTab pending-search block not found")
main = main.replace(old_pending, new_pending, 1)

old_apply_head = '''    private void applySearch(String rawQuery) {
        String query = SearchMatcher.normalizeQuery(rawQuery);
        searchQuery = query;
        if (!query.isEmpty() && seasonModeRow != null) seasonModeRow.setVisibility(View.GONE);
        if (groupOpen && groupSearchEnabled && !playerOpen) {
            applyGroupSearchAndFilter(query);
            return;
        }
'''
new_apply_head = '''    private void applySearch(String rawQuery) {
        boolean directQuote = SearchMatcher.isDirectQuote(rawQuery);
        String query = SearchMatcher.queryText(rawQuery);
        searchQuery = query;
        if (!query.isEmpty() && seasonModeRow != null) seasonModeRow.setVisibility(View.GONE);
        if (groupOpen && groupSearchEnabled && !playerOpen) {
            applyGroupSearchAndFilter(rawQuery);
            return;
        }
'''
if old_apply_head not in main:
    raise SystemExit("applySearch header not found")
main = main.replace(old_apply_head, new_apply_head, 1)

for field in ("album", "title", "artist"):
    old = f"SearchMatcher.contains(song.{field}, query)"
    new = f"SearchMatcher.matches(song.{field}, query, directQuote)"
    if old not in main:
        raise SystemExit(f"main search matcher for {field} not found")
    main = main.replace(old, new, 1)

old_toggle = '''        String query = groupSearchEnabled ? SearchMatcher.normalizeQuery(searchInput.getText().toString()) : "";
        applyGroupSearchAndFilter(query);
'''
new_toggle = '''        String query = groupSearchEnabled ? searchInput.getText().toString() : "";
        applyGroupSearchAndFilter(query);
'''
if old_toggle not in main:
    raise SystemExit("group filter query block not found")
main = main.replace(old_toggle, new_toggle, 1)

old_group = '''    private void applyGroupSearchAndFilter(String query) {
        if (!groupSearchEnabled && !groupTypeFiltersEnabled) return;
        visibleGroups.clear();
        visibleSongs.clear();
        for (Song song : groupBaseSongs) {
            if (!TextUtils.isEmpty(groupTypeFilter)
                    && !albumMatchesType(song, groupTypeFilter)) continue;
            if (!query.isEmpty()
                    && !SearchMatcher.contains(song.title, query)
                    && !SearchMatcher.contains(song.artist, query)
                    && !SearchMatcher.contains(song.album, query)) continue;
            visibleSongs.add(song);
        }
'''
new_group = '''    private void applyGroupSearchAndFilter(String rawQuery) {
        boolean directQuote = SearchMatcher.isDirectQuote(rawQuery);
        String query = SearchMatcher.queryText(rawQuery);
        if (!groupSearchEnabled && !groupTypeFiltersEnabled) return;
        visibleGroups.clear();
        visibleSongs.clear();
        for (Song song : groupBaseSongs) {
            if (!TextUtils.isEmpty(groupTypeFilter)
                    && !albumMatchesType(song, groupTypeFilter)) continue;
            if (!query.isEmpty()
                    && !SearchMatcher.matches(song.title, query, directQuote)
                    && !SearchMatcher.matches(song.artist, query, directQuote)
                    && !SearchMatcher.matches(song.album, query, directQuote)) continue;
            visibleSongs.add(song);
        }
'''
if old_group not in main:
    raise SystemExit("group search block not found")
main = main.replace(old_group, new_group, 1)

old_back = '''        String rawSearch = searchInput == null ? "" : searchInput.getText().toString();
        if (!SearchMatcher.normalizeQuery(rawSearch).isEmpty()) {
'''
new_back = '''        String rawSearch = searchInput == null ? "" : searchInput.getText().toString();
        if (!SearchMatcher.isEmptyQuery(rawSearch)) {
'''
if old_back not in main:
    raise SystemExit("back search-empty check not found")
main = main.replace(old_back, new_back, 1)

# Installable update over v0.14.5.
gradle = gradle.replace("versionCode 23", "versionCode 24")
gradle = gradle.replace("versionName '0.14.5-debug'", "versionName '0.14.6-debug'")
if "versionCode 24" not in gradle or "versionName '0.14.6-debug'" not in gradle:
    raise SystemExit("Version bump failed")

MAIN.write_text(main, encoding="utf-8")
MATCHER.write_text(matcher, encoding="utf-8")
GRADLE.write_text(gradle, encoding="utf-8")

print('Applied v0.14.6 direct-quote search: leading " => case-sensitive exact substring')
