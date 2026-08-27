from pathlib import Path
p=Path('app/src/main/java/de/minimal/musicplayer/MainActivity.java')
s=p.read_text()
def r(a,b,n):
    global s
    if a not in s: raise SystemExit('missing '+n)
    s=s.replace(a,b,1)
r('    private LinearLayout groupFilterRow;\n    private LinearLayout miniPlayer;', '    private LinearLayout groupFilterRow;\n    private LinearLayout seasonModeRow;\n    private LinearLayout miniPlayer;', 'season row field')
r('    private Button groupEdFilterButton;\n    private EditText searchInput;', '    private Button groupEdFilterButton;\n    private Button seasonAnimeButton;\n    private Button seasonRlButton;\n    private EditText searchInput;', 'season buttons')
r('    private String groupTitle = "";\n    private Uri currentTreeUri;', '    private String groupTitle = "";\n    private String seasonCategory = "ANIME";\n    private Uri currentTreeUri;', 'category')
r('        initializeGroupFilterRow();\n        repeatOne =', '        initializeGroupFilterRow();\n        initializeSeasonModeRow();\n        libraryList.setChoiceMode(ListView.CHOICE_MODE_NONE);\n        repeatOne =', 'init')
anchor='''    private Button makeGroupFilterButton(String label) {
        Button button = new Button(this);
        button.setText(label);
        button.setTextSize(14f);
        button.setTextColor(getColor(R.color.text_secondary));
        button.setTypeface(android.graphics.Typeface.DEFAULT, android.graphics.Typeface.BOLD);
        button.setBackgroundResource(R.drawable.rounded_surface);
        button.setPadding(0, 0, 0, 0);
        return button;
    }
'''
extra=anchor+'''
    private void initializeSeasonModeRow() {
        seasonModeRow = new LinearLayout(this);
        seasonModeRow.setOrientation(LinearLayout.HORIZONTAL);
        seasonModeRow.setGravity(Gravity.CENTER_VERTICAL);
        seasonModeRow.setVisibility(View.GONE);
        seasonAnimeButton = makeGroupFilterButton("ANIME");
        seasonRlButton = makeGroupFilterButton("RL");
        seasonModeRow.addView(seasonAnimeButton, new LinearLayout.LayoutParams(0, dp(44), 1f));
        LinearLayout.LayoutParams rp = new LinearLayout.LayoutParams(0, dp(44), 1f);
        rp.setMarginStart(dp(6));
        seasonModeRow.addView(seasonRlButton, rp);
        LinearLayout.LayoutParams row = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(44));
        row.setMargins(dp(12), dp(4), dp(12), dp(2));
        rootLayout.addView(seasonModeRow, Math.max(0, rootLayout.indexOfChild(searchRow) + 1), row);
        seasonAnimeButton.setOnClickListener(v -> setSeasonCategory("ANIME"));
        seasonRlButton.setOnClickListener(v -> setSeasonCategory("RL"));
        updateSeasonModeButtons();
    }

    private void setSeasonCategory(String category) {
        if (libraryMode != MODE_GENRES || groupOpen || playerOpen) return;
        seasonCategory = "RL".equals(category) ? "RL" : "ANIME";
        if (!TextUtils.isEmpty(searchInput.getText())) {
            searchInput.setText("");
            hideSearchKeyboard();
        }
        searchQuery = "";
        visibleSongs.clear();
        visibleGroups.clear();
        visibleGroups.addAll(buildSeasonGroupsForCategory());
        updateSeasonModeButtons();
        adapter.notifyDataSetChanged();
        updateAlphabetVisibility();
        scrollLibraryToTop();
    }

    private void updateSeasonModeButtons() {
        styleGroupFilterButton(seasonAnimeButton, "ANIME".equals(seasonCategory));
        styleGroupFilterButton(seasonRlButton, "RL".equals(seasonCategory));
    }
'''
r(anchor,extra,'season methods')
r('        if (groupFilterRow != null) groupFilterRow.setVisibility(View.GONE);\n        if (searchInput != null)', '        if (groupFilterRow != null) groupFilterRow.setVisibility(View.GONE);\n        if (seasonModeRow != null) seasonModeRow.setVisibility(View.GONE);\n        if (searchInput != null)', 'hide row reset')
r('''        } else if (mode == MODE_GENRES) {
            visibleGroups.addAll(buildGroups(false));
            randomPlayButton.setVisibility(View.GONE);
''','''        } else if (mode == MODE_GENRES) {
            visibleGroups.addAll(buildSeasonGroupsForCategory());
            seasonModeRow.setVisibility(View.VISIBLE);
            updateSeasonModeButtons();
            randomPlayButton.setVisibility(View.GONE);
''','season build')
r('        searchQuery = query;\n        if (groupOpen && groupSearchEnabled', '        searchQuery = query;\n        if (!query.isEmpty() && seasonModeRow != null) seasonModeRow.setVisibility(View.GONE);\n        if (groupOpen && groupSearchEnabled', 'search hide')
r('''    private void hideSearchKeyboard() {
        searchInput.clearFocus();
        InputMethodManager inputMethodManager =
                (InputMethodManager) getSystemService(Context.INPUT_METHOD_SERVICE);
        if (inputMethodManager != null) {
            inputMethodManager.hideSoftInputFromWindow(searchInput.getWindowToken(), 0);
        }
    }
''','''    private void hideSearchKeyboard() {
        if (searchInput != null) searchInput.clearFocus();
        View decor = getWindow().getDecorView();
        decor.setFocusableInTouchMode(true);
        decor.requestFocus();
        InputMethodManager imm = (InputMethodManager) getSystemService(Context.INPUT_METHOD_SERVICE);
        if (imm != null) {
            imm.hideSoftInputFromWindow(decor.getWindowToken(), InputMethodManager.HIDE_NOT_ALWAYS);
            mainHandler.postDelayed(() -> imm.hideSoftInputFromWindow(decor.getWindowToken(), 0), 120L);
        }
    }
''','keyboard')
needle='    private static int compareSeasonNames(String left, String right) {\n'
add='''    private List<GroupRow> buildSeasonGroupsForCategory() {
        ArrayList<GroupRow> out = new ArrayList<>();
        for (GroupRow group : buildGroups(false)) {
            boolean rl = group.name != null && group.name.regionMatches(true, 0, "RL_", 0, 3);
            if (("RL".equals(seasonCategory) && rl) || (!"RL".equals(seasonCategory) && !rl)) out.add(group);
        }
        return out;
    }

'''
r(needle,add+needle,'group filter')
r('        tabBar.setVisibility(View.GONE);\n        alphabetIndex.setVisibility(View.GONE);', '        tabBar.setVisibility(View.GONE);\n        if (seasonModeRow != null) seasonModeRow.setVisibility(View.GONE);\n        alphabetIndex.setVisibility(View.GONE);', 'group hide row')
p.write_text(s)
