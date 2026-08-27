from pathlib import Path
p=Path('app/src/main/java/de/minimal/musicplayer/MainActivity.java')
s=p.read_text()
def r(a,b,n):
    global s
    if a not in s: raise SystemExit('missing '+n)
    s=s.replace(a,b,1)
r('    private LinearLayout otherPanel;\n    private TextView titleText;', '    private LinearLayout otherPanel;\n    private LinearLayout infoSettingsPanel;\n    private TextView titleText;', 'panel field')
r('    private Button playlistsButton;\n    private Button clearSearchButton;', '    private Button playlistsButton;\n    private Button infoSettingsButton;\n    private Button clearSearchButton;', 'button field')
r('    private boolean rlYearDetailOpen;\n    private boolean playCountedThisCycle;', '    private boolean rlYearDetailOpen;\n    private boolean infoSettingsOpen;\n    private boolean playCountedThisCycle;', 'state')
r('        otherPanel = findViewById(R.id.otherPanel);\n        titleText =', '        otherPanel = findViewById(R.id.otherPanel);\n        infoSettingsPanel = findViewById(R.id.infoSettingsPanel);\n        titleText =', 'bind panel')
r('        playlistsButton = findViewById(R.id.playlistsButton);\n        clearSearchButton =', '        playlistsButton = findViewById(R.id.playlistsButton);\n        infoSettingsButton = findViewById(R.id.infoSettingsButton);\n        clearSearchButton =', 'bind button')
r('        topPlayedButton.setOnClickListener(v -> openTopPlayed());\n        playlistsButton.setOnClickListener', '        topPlayedButton.setOnClickListener(v -> openTopPlayed());\n        infoSettingsButton.setOnClickListener(v -> openInfoSettings());\n        playlistsButton.setOnClickListener', 'click')
r('        rlYearDetailOpen = false;\n        rlSongsForBrowser.clear();', '        rlYearDetailOpen = false;\n        infoSettingsOpen = false;\n        rlSongsForBrowser.clear();', 'reset state')
r('        otherPanel.setVisibility(View.GONE);\n        tabBar.setVisibility(View.VISIBLE);', '        otherPanel.setVisibility(View.GONE);\n        if (infoSettingsPanel != null) infoSettingsPanel.setVisibility(View.GONE);\n        tabBar.setVisibility(View.VISIBLE);', 'hide panel')
anchor='    private void openTopPlayed() {\n'
method='''    private void openInfoSettings() {
        infoSettingsOpen = true;
        groupOpen = false;
        playerOpen = false;
        playlistBrowserOpen = false;
        playlistDetailOpen = false;
        libraryList.setVisibility(View.GONE);
        emptyState.setVisibility(View.GONE);
        otherPanel.setVisibility(View.GONE);
        infoSettingsPanel.setVisibility(View.VISIBLE);
        tabBar.setVisibility(View.GONE);
        searchRow.setVisibility(View.GONE);
        if (seasonModeRow != null) seasonModeRow.setVisibility(View.GONE);
        if (groupFilterRow != null) groupFilterRow.setVisibility(View.GONE);
        alphabetIndex.setVisibility(View.GONE);
        randomPlayButton.setVisibility(View.GONE);
        backButton.setVisibility(View.VISIBLE);
        titleText.setText("Infos & Einstellungen");
        refreshInsets();
    }

'''
r(anchor,method+anchor,'method')
r('''    private void handleBack() {
        if (playerOpen) {
''','''    private void handleBack() {
        if (infoSettingsOpen) {
            infoSettingsOpen = false;
            selectTab(MODE_OTHER);
        } else if (playerOpen) {
''','back')
r('''    public void onBackPressed() {
        if (playerOpen || groupOpen) handleBack();
        else super.onBackPressed();
    }
''','''    public void onBackPressed() {
        if (infoSettingsOpen || playerOpen || groupOpen) handleBack();
        else super.onBackPressed();
    }
''','system back')
p.write_text(s)
