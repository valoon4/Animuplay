package de.minimal.musicplayer;

import android.Manifest;
import android.app.Activity;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.ContentResolver;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.database.Cursor;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Color;
import android.graphics.drawable.ColorDrawable;
import android.media.AudioAttributes;
import android.media.AudioFocusRequest;
import android.media.AudioManager;
import android.media.MediaMetadata;
import android.media.MediaMetadataRetriever;
import android.media.MediaPlayer;
import android.media.session.MediaSession;
import android.media.session.PlaybackState;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.os.SystemClock;
import android.provider.DocumentsContract;
import android.text.Editable;
import android.text.TextUtils;
import android.text.TextWatcher;
import android.view.Gravity;
import android.view.inputmethod.InputMethodManager;
import android.view.View;
import android.view.ViewGroup;
import android.widget.BaseAdapter;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ListView;
import android.widget.ProgressBar;
import android.widget.SeekBar;
import android.widget.TextView;
import android.widget.Toast;

import java.io.FileNotFoundException;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.lang.ref.WeakReference;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

public final class MainActivity extends Activity implements MediaPlayer.OnCompletionListener {
    private static final int REQUEST_TREE = 20;
    private static final int REQUEST_NOTIFICATIONS = 21;
    private static final String PREFS = "music_player";
    private static final String PREF_TREE_URI = "tree_uri";
    private static final String PREF_REPEAT_ONE = "repeat_one";
    private static final String MEDIA_CHANNEL_ID = "music_playback";
    private static final int MEDIA_NOTIFICATION_ID = 61;
    private static final String ACTION_PREVIOUS = "de.minimal.musicplayer.PREVIOUS";
    private static final String ACTION_PLAY_PAUSE = "de.minimal.musicplayer.PLAY_PAUSE";
    private static final String ACTION_NEXT = "de.minimal.musicplayer.NEXT";
    private static final String ACTION_STOP = "de.minimal.musicplayer.STOP";
    private static WeakReference<MainActivity> activeInstance = new WeakReference<>(null);

    private static final int MODE_SONGS = 0;
    private static final int MODE_ALBUMS = 1;
    private static final int MODE_GENRES = 2;
    private static final int MODE_YEARS = 3;
    private static final int MODE_OTHER = 4;

    private final ArrayList<Song> allSongs = new ArrayList<>();
    private final ArrayList<Song> visibleSongs = new ArrayList<>();
    private final ArrayList<Song> playQueue = new ArrayList<>();
    private final ArrayList<GroupRow> visibleGroups = new ArrayList<>();
    private final ArrayList<SearchResultRow> searchRows = new ArrayList<>();
    private final ArrayList<Song> searchPlayableSongs = new ArrayList<>();
    private final ArrayList<ImportedPlaylist> importedPlaylists = new ArrayList<>();
    private final HashMap<String, Integer> playCounts = new HashMap<>();

    private final ExecutorService scanExecutor = Executors.newSingleThreadExecutor();
    private final ExecutorService historyExecutor = Executors.newSingleThreadExecutor();
    private final Handler mainHandler = new Handler(Looper.getMainLooper());
    private final Handler progressHandler = new Handler(Looper.getMainLooper());

    private LinearLayout rootLayout;
    private LinearLayout topBar;
    private ListView libraryList;
    private LinearLayout emptyState;
    private LinearLayout scanningState;
    private ProgressBar progress;
    private TextView scanProgressText;
    private LinearLayout tabBar;
    private LinearLayout searchRow;
    private LinearLayout miniPlayer;
    private LinearLayout playerPanel;
    private LinearLayout otherPanel;
    private TextView titleText;
    private Button backButton;
    private Button tabSongs;
    private Button tabAlbums;
    private Button tabGenres;
    private Button tabYears;
    private Button tabOther;
    private Button randomPlayButton;
    private Button topPlayedButton;
    private Button playlistsButton;
    private Button clearSearchButton;
    private EditText searchInput;
    private AlphabetIndexView alphabetIndex;
    private TextView miniTitle;
    private TextView miniArtist;
    private Button miniPlay;
    private Button miniRepeat;
    private Button playerPlay;
    private Button playerRepeat;
    private TextView playerTitle;
    private TextView playerArtist;
    private TextView playerAlbum;
    private TextView playerTrackNumber;
    private TextView playerGenre;
    private ImageView artwork;
    private SeekBar seekBar;
    private TextView currentTime;
    private TextView totalTime;

    private final LibraryAdapter adapter = new LibraryAdapter();
    private MediaPlayer mediaPlayer;
    private AudioManager audioManager;
    private AudioFocusRequest audioFocusRequest;
    private MediaSession mediaSession;
    private NotificationManager notificationManager;
    private Song currentSong;
    private int currentQueueIndex = -1;
    private int libraryMode = MODE_SONGS;
    private boolean groupOpen;
    private boolean groupUsesTrackNumbers;
    private boolean playerOpen;
    private boolean preparing;
    private boolean userSeeking;
    private boolean audioFocusHeld;
    private boolean resumeOnFocusGain;
    private boolean notificationPermissionRequested;
    private boolean repeatOne;
    private boolean showPlayCounts;
    private boolean playlistBrowserOpen;
    private boolean playlistDetailOpen;
    private boolean playlistScanCompleted;
    private boolean playCountedThisCycle;
    private long listenedThisCycleMs;
    private long lastProgressRealtimeMs;
    private int lastPlaybackPositionMs;
    private String searchQuery = "";
    private Uri currentTreeUri;
    private long lastPlaybackStateSyncRealtimeMs;
    private volatile int scanGeneration;

    private final AudioManager.OnAudioFocusChangeListener audioFocusListener = focusChange -> {
        mainHandler.post(() -> {
            if (mediaPlayer == null || preparing) return;
            try {
                if (focusChange == AudioManager.AUDIOFOCUS_GAIN) {
                    mediaPlayer.setVolume(1f, 1f);
                    if (resumeOnFocusGain && !mediaPlayer.isPlaying()) mediaPlayer.start();
                    resumeOnFocusGain = false;
                } else if (focusChange == AudioManager.AUDIOFOCUS_LOSS_TRANSIENT_CAN_DUCK) {
                    mediaPlayer.setVolume(0.2f, 0.2f);
                } else if (focusChange == AudioManager.AUDIOFOCUS_LOSS_TRANSIENT) {
                    if (mediaPlayer.isPlaying()) {
                        resumeOnFocusGain = true;
                        mediaPlayer.pause();
                    }
                } else if (focusChange == AudioManager.AUDIOFOCUS_LOSS) {
                    resumeOnFocusGain = false;
                    audioFocusHeld = false;
                    if (mediaPlayer.isPlaying()) mediaPlayer.pause();
                }
                updatePlayButtons();
            } catch (IllegalStateException ignored) { }
        });
    };

    private final Runnable delayedSearch = () -> applySearch(searchInput == null ? "" : searchInput.getText().toString());

    private final Runnable progressUpdater = new Runnable() {
        @Override
        public void run() {
            if (mediaPlayer != null && !preparing) {
                try {
                    int position = mediaPlayer.getCurrentPosition();
                    int duration = mediaPlayer.getDuration();
                    boolean playing = mediaPlayer.isPlaying();
                    updatePlayCountProgress(position, duration, playing);
                    seekBar.setMax(Math.max(duration, 1));
                    if (!userSeeking) seekBar.setProgress(position);
                    currentTime.setText(formatDuration(position));
                    totalTime.setText(formatDuration(duration));
                    long now = SystemClock.elapsedRealtime();
                    if (playing && now - lastPlaybackStateSyncRealtimeMs >= 1000L) {
                        lastPlaybackStateSyncRealtimeMs = now;
                        updateSystemPlaybackState(true);
                    }
                } catch (IllegalStateException ignored) {
                    // Player is changing state.
                }
            }
            progressHandler.postDelayed(this, 500L);
        }
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        activeInstance = new WeakReference<>(this);
        setContentView(R.layout.activity_main);
        bindViews();
        repeatOne = getSharedPreferences(PREFS, MODE_PRIVATE).getBoolean(PREF_REPEAT_ONE, false);
        playCounts.putAll(PlayHistory.load(this));
        configureMarquee(titleText);
        configureMarquee(miniTitle);
        configureMarquee(miniArtist);
        configureMarquee(playerTitle);
        configureMarquee(playerArtist);
        configureMarquee(playerAlbum);
        configureMarquee(playerGenre);
        applySystemInsets();
        initializePlaybackSystem();
        bindActions();
        libraryList.setAdapter(adapter);
        selectTab(MODE_SONGS);
        progressHandler.post(progressUpdater);
        handlePlaybackIntent(getIntent());

        String savedTree = getSharedPreferences(PREFS, MODE_PRIVATE).getString(PREF_TREE_URI, null);
        if (!TextUtils.isEmpty(savedTree)) {
            scanLibrary(Uri.parse(savedTree), false);
        } else {
            showNoFolderState();
        }
    }

    private void bindViews() {
        rootLayout = findViewById(R.id.rootLayout);
        topBar = findViewById(R.id.topBar);
        libraryList = findViewById(R.id.libraryList);
        emptyState = findViewById(R.id.emptyState);
        scanningState = findViewById(R.id.scanningState);
        progress = findViewById(R.id.progress);
        scanProgressText = findViewById(R.id.scanProgressText);
        tabBar = findViewById(R.id.tabBar);
        searchRow = findViewById(R.id.searchRow);
        miniPlayer = findViewById(R.id.miniPlayer);
        playerPanel = findViewById(R.id.playerPanel);
        otherPanel = findViewById(R.id.otherPanel);
        titleText = findViewById(R.id.titleText);
        backButton = findViewById(R.id.backButton);
        tabSongs = findViewById(R.id.tabSongs);
        tabAlbums = findViewById(R.id.tabAlbums);
        tabGenres = findViewById(R.id.tabGenres);
        tabYears = findViewById(R.id.tabYears);
        tabOther = findViewById(R.id.tabOther);
        randomPlayButton = findViewById(R.id.randomPlayButton);
        topPlayedButton = findViewById(R.id.topPlayedButton);
        playlistsButton = findViewById(R.id.playlistsButton);
        clearSearchButton = findViewById(R.id.clearSearchButton);
        searchInput = findViewById(R.id.searchInput);
        alphabetIndex = findViewById(R.id.alphabetIndex);
        miniTitle = findViewById(R.id.miniTitle);
        miniArtist = findViewById(R.id.miniArtist);
        miniPlay = findViewById(R.id.miniPlay);
        miniRepeat = findViewById(R.id.miniRepeat);
        playerPlay = findViewById(R.id.playerPlay);
        playerRepeat = findViewById(R.id.playerRepeat);
        playerTitle = findViewById(R.id.playerTitle);
        playerArtist = findViewById(R.id.playerArtist);
        playerAlbum = findViewById(R.id.playerAlbum);
        playerTrackNumber = findViewById(R.id.playerTrackNumber);
        playerGenre = findViewById(R.id.playerGenre);
        artwork = findViewById(R.id.artwork);
        seekBar = findViewById(R.id.seekBar);
        currentTime = findViewById(R.id.currentTime);
        totalTime = findViewById(R.id.totalTime);
    }

    private void applySystemInsets() {
        rootLayout.setOnApplyWindowInsetsListener((view, insets) -> {
            int left = insets == null ? 0 : insets.getSystemWindowInsetLeft();
            int top = insets == null ? 0 : insets.getSystemWindowInsetTop();
            int right = insets == null ? 0 : insets.getSystemWindowInsetRight();
            int bottom = insets == null ? 0 : insets.getSystemWindowInsetBottom();

            // Keep the entire application content inside the usable screen area.
            // This avoids status-bar overlap at the top and navigation-button overlap
            // at the bottom, including Android 15's enforced edge-to-edge mode.
            view.setPadding(left, top, right, bottom);
            return insets;
        });
        refreshInsets();
    }

    private void refreshInsets() {
        rootLayout.requestApplyInsets();
    }

    private void bindActions() {
        View.OnClickListener chooseFolder = v -> chooseFolder();
        findViewById(R.id.folderButton).setOnClickListener(chooseFolder);
        findViewById(R.id.emptyFolderButton).setOnClickListener(chooseFolder);
        tabSongs.setOnClickListener(v -> selectTab(MODE_SONGS));
        tabAlbums.setOnClickListener(v -> selectTab(MODE_ALBUMS));
        tabGenres.setOnClickListener(v -> selectTab(MODE_GENRES));
        tabYears.setOnClickListener(v -> selectTab(MODE_YEARS));
        tabOther.setOnClickListener(v -> selectTab(MODE_OTHER));
        randomPlayButton.setOnClickListener(v -> playCurrentListRandomly());
        backButton.setOnClickListener(v -> handleBack());
        clearSearchButton.setOnClickListener(v -> searchInput.setText(""));
        alphabetIndex.setOnLetterSelectedListener(this::jumpToLetter);
        topPlayedButton.setOnClickListener(v -> openTopPlayed());
        playlistsButton.setOnClickListener(v -> {
            if (!playlistScanCompleted) {
                Toast.makeText(this, "Playlists werden noch im Hintergrund geprüft.", Toast.LENGTH_SHORT).show();
            } else if (importedPlaylists.isEmpty()) {
                Toast.makeText(this, "Keine .m3u- oder .m3u8-Playlists im Musikordner gefunden.",
                        Toast.LENGTH_SHORT).show();
            } else {
                openPlaylistBrowser();
            }
        });
        searchInput.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence s, int start, int count, int after) { }
            @Override public void onTextChanged(CharSequence s, int start, int before, int count) {
                clearSearchButton.setVisibility(s.length() == 0 ? View.GONE : View.VISIBLE);
                mainHandler.removeCallbacks(delayedSearch);
                mainHandler.postDelayed(delayedSearch, 120L);
            }
            @Override public void afterTextChanged(Editable s) { }
        });

        libraryList.setOnItemClickListener((parent, view, position, id) -> {
            if (!TextUtils.isEmpty(searchQuery) && !groupOpen) {
                if (position < 0 || position >= searchRows.size()) return;
                SearchResultRow result = searchRows.get(position);
                if (result.type == SearchResultRow.TYPE_SONG && result.song != null) {
                    int queueIndex = searchPlayableSongs.indexOf(result.song);
                    hideSearchKeyboard();
                    playSongFromList(searchPlayableSongs, Math.max(queueIndex, 0));
                } else if (result.group != null) {
                    openSearchGroup(result);
                }
                return;
            }
            if (visibleGroups.isEmpty()) {
                if (position >= 0 && position < visibleSongs.size()) {
                    playSongFromList(visibleSongs, position);
                }
            } else if (position >= 0 && position < visibleGroups.size()) {
                openGroup(visibleGroups.get(position));
            }
        });

        findViewById(R.id.miniInfo).setOnClickListener(v -> openPlayer());
        miniPlayer.setOnClickListener(v -> openPlayer());
        miniPlay.setOnClickListener(v -> togglePlayback());
        miniRepeat.setOnClickListener(v -> toggleRepeatOne());
        playerPlay.setOnClickListener(v -> togglePlayback());
        playerRepeat.setOnClickListener(v -> toggleRepeatOne());
        findViewById(R.id.miniPrev).setOnClickListener(v -> previousSong());
        findViewById(R.id.miniNext).setOnClickListener(v -> nextSong());
        findViewById(R.id.playerPrev).setOnClickListener(v -> previousSong());
        findViewById(R.id.playerNext).setOnClickListener(v -> nextSong());

        seekBar.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
            @Override public void onProgressChanged(SeekBar seekBar, int progress, boolean fromUser) {
                if (fromUser) currentTime.setText(formatDuration(progress));
            }
            @Override public void onStartTrackingTouch(SeekBar seekBar) { userSeeking = true; }
            @Override public void onStopTrackingTouch(SeekBar seekBar) {
                userSeeking = false;
                if (mediaPlayer != null && !preparing) {
                    try { mediaPlayer.seekTo(seekBar.getProgress()); }
                    catch (IllegalStateException ignored) { }
                }
            }
        });
    }

    private void initializePlaybackSystem() {
        audioManager = (AudioManager) getSystemService(AUDIO_SERVICE);
        AudioAttributes attributes = new AudioAttributes.Builder()
                .setContentType(AudioAttributes.CONTENT_TYPE_MUSIC)
                .setUsage(AudioAttributes.USAGE_MEDIA)
                .build();
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            audioFocusRequest = new AudioFocusRequest.Builder(AudioManager.AUDIOFOCUS_GAIN)
                    .setAudioAttributes(attributes)
                    .setOnAudioFocusChangeListener(audioFocusListener, mainHandler)
                    .setAcceptsDelayedFocusGain(false)
                    .build();
        }
        notificationManager = (NotificationManager) getSystemService(NOTIFICATION_SERVICE);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel channel = new NotificationChannel(MEDIA_CHANNEL_ID,
                    "Musikwiedergabe", NotificationManager.IMPORTANCE_LOW);
            channel.setDescription("Steuerung der laufenden Musikwiedergabe");
            channel.setLockscreenVisibility(Notification.VISIBILITY_PUBLIC);
            notificationManager.createNotificationChannel(channel);
        }

        mediaSession = new MediaSession(this, "MinimalMusicPlayer");
        mediaSession.setFlags(MediaSession.FLAG_HANDLES_MEDIA_BUTTONS
                | MediaSession.FLAG_HANDLES_TRANSPORT_CONTROLS);
        mediaSession.setCallback(new MediaSession.Callback() {
            @Override public void onPlay() { mainHandler.post(() -> {
                if (mediaPlayer != null && !preparing && requestAudioFocus()) {
                    try { mediaPlayer.start(); } catch (IllegalStateException ignored) { }
                    updatePlayButtons();
                }
            }); }
            @Override public void onPause() { mainHandler.post(() -> {
                if (mediaPlayer != null && !preparing) {
                    try { mediaPlayer.pause(); } catch (IllegalStateException ignored) { }
                    updatePlayButtons();
                }
            }); }
            @Override public void onSkipToPrevious() { mainHandler.post(MainActivity.this::previousSong); }
            @Override public void onSkipToNext() { mainHandler.post(MainActivity.this::nextSong); }
            @Override public void onSeekTo(long position) { mainHandler.post(() -> {
                if (mediaPlayer != null && !preparing) {
                    try {
                        mediaPlayer.seekTo((int) Math.max(0L, Math.min(Integer.MAX_VALUE, position)));
                        updateSystemPlaybackState(mediaPlayer.isPlaying());
                    } catch (IllegalStateException ignored) { }
                }
            }); }
            @Override public void onStop() { mainHandler.post(MainActivity.this::stopPlaybackAndDismiss); }
            @Override public void onCustomAction(String action, Bundle extras) {
                if (ACTION_STOP.equals(action)) mainHandler.post(MainActivity.this::stopPlaybackAndDismiss);
            }
        });
        mediaSession.setActive(true);
        updateSystemPlaybackState(false);
        updateRepeatButtons();
    }

    private boolean requestAudioFocus() {
        if (audioManager == null) return true;
        if (audioFocusHeld) return true;
        int result;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            result = audioManager.requestAudioFocus(audioFocusRequest);
        } else {
            result = audioManager.requestAudioFocus(audioFocusListener,
                    AudioManager.STREAM_MUSIC, AudioManager.AUDIOFOCUS_GAIN);
        }
        audioFocusHeld = result == AudioManager.AUDIOFOCUS_REQUEST_GRANTED;
        return audioFocusHeld;
    }

    private void abandonAudioFocus() {
        if (!audioFocusHeld || audioManager == null) return;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            audioManager.abandonAudioFocusRequest(audioFocusRequest);
        } else {
            audioManager.abandonAudioFocus(audioFocusListener);
        }
        audioFocusHeld = false;
        resumeOnFocusGain = false;
    }

    private void updateSystemPlaybackState(boolean playing) {
        if (mediaSession == null) return;
        long position = 0L;
        if (mediaPlayer != null && !preparing) {
            try { position = mediaPlayer.getCurrentPosition(); }
            catch (IllegalStateException ignored) { }
        }
        int state = preparing ? PlaybackState.STATE_BUFFERING
                : playing ? PlaybackState.STATE_PLAYING : PlaybackState.STATE_PAUSED;
        long actions = PlaybackState.ACTION_PLAY | PlaybackState.ACTION_PAUSE
                | PlaybackState.ACTION_PLAY_PAUSE | PlaybackState.ACTION_SKIP_TO_PREVIOUS
                | PlaybackState.ACTION_SKIP_TO_NEXT | PlaybackState.ACTION_SEEK_TO
                | PlaybackState.ACTION_STOP;
        mediaSession.setPlaybackState(new PlaybackState.Builder()
                .setActions(actions)
                .addCustomAction(new PlaybackState.CustomAction.Builder(
                        ACTION_STOP, "Beenden", R.drawable.ic_close).build())
                .setState(state, position, playing ? 1f : 0f, SystemClock.elapsedRealtime())
                .build());
    }

    private void updateSystemMetadata(Bitmap cover) {
        if (mediaSession == null || currentSong == null) return;
        MediaMetadata.Builder builder = new MediaMetadata.Builder()
                .putString(MediaMetadata.METADATA_KEY_TITLE, currentSong.title)
                .putString(MediaMetadata.METADATA_KEY_ARTIST, currentSong.artist)
                .putString(MediaMetadata.METADATA_KEY_ALBUM, currentSong.album)
                .putLong(MediaMetadata.METADATA_KEY_TRACK_NUMBER, Math.max(0, currentSong.trackNumber))
                .putLong(MediaMetadata.METADATA_KEY_DURATION, currentSong.durationMs);
        if (cover != null) builder.putBitmap(MediaMetadata.METADATA_KEY_ALBUM_ART, cover);
        mediaSession.setMetadata(builder.build());
    }

    private void updateMediaNotification(boolean playing) {
        if (notificationManager == null || mediaSession == null || currentSong == null) return;
        if (Build.VERSION.SDK_INT >= 33
                && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
            if (!notificationPermissionRequested) {
                notificationPermissionRequested = true;
                requestPermissions(new String[] {Manifest.permission.POST_NOTIFICATIONS}, REQUEST_NOTIFICATIONS);
            }
            return;
        }
        PendingIntent previous = playbackPendingIntent(ACTION_PREVIOUS, 1);
        PendingIntent playPause = playbackPendingIntent(ACTION_PLAY_PAUSE, 2);
        PendingIntent next = playbackPendingIntent(ACTION_NEXT, 3);
        PendingIntent stop = playbackPendingIntent(ACTION_STOP, 5);
        Intent contentIntent = new Intent(this, MainActivity.class)
                .addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP | Intent.FLAG_ACTIVITY_CLEAR_TOP);
        PendingIntent content = PendingIntent.getActivity(this, 4, contentIntent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);

        Notification.Builder builder = Build.VERSION.SDK_INT >= Build.VERSION_CODES.O
                ? new Notification.Builder(this, MEDIA_CHANNEL_ID)
                : new Notification.Builder(this);
        builder.setSmallIcon(android.R.drawable.ic_media_play)
                .setContentTitle(currentSong.title)
                .setContentText(currentSong.artist + " · " + currentSong.album)
                .setContentIntent(content)
                .setVisibility(Notification.VISIBILITY_PUBLIC)
                .setCategory(Notification.CATEGORY_TRANSPORT)
                .setOnlyAlertOnce(true)
                .setShowWhen(false)
                .setOngoing(false)
                .setDeleteIntent(stop)
                .addAction(new Notification.Action(android.R.drawable.ic_media_previous,
                        "Zurück", previous))
                .addAction(new Notification.Action(playing ? android.R.drawable.ic_media_pause
                        : android.R.drawable.ic_media_play, playing ? "Pause" : "Abspielen", playPause))
                .addAction(new Notification.Action(R.drawable.ic_close,
                        "Wiedergabe beenden", stop))
                .addAction(new Notification.Action(android.R.drawable.ic_media_next,
                        "Weiter", next))
                .setStyle(new Notification.MediaStyle()
                        .setMediaSession(mediaSession.getSessionToken())
                        // X is intentionally one of the three compact actions so Samsung/Android
                        // media surfaces do not hide it behind the expanded notification.
                        .setShowActionsInCompactView(0, 1, 2));
        notificationManager.notify(MEDIA_NOTIFICATION_ID, builder.build());
    }

    private PendingIntent playbackPendingIntent(String action, int requestCode) {
        Intent intent = new Intent(this, PlaybackActionReceiver.class).setAction(action);
        return PendingIntent.getBroadcast(this, requestCode, intent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
    }

    static void handleExternalPlaybackAction(String action) {
        MainActivity activity = activeInstance.get();
        if (activity == null || action == null) return;
        activity.mainHandler.post(() -> {
            if (ACTION_PREVIOUS.equals(action)) activity.previousSong();
            else if (ACTION_PLAY_PAUSE.equals(action)) activity.togglePlayback();
            else if (ACTION_NEXT.equals(action)) activity.nextSong();
            else if (ACTION_STOP.equals(action)) activity.stopPlaybackAndDismiss();
        });
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == REQUEST_NOTIFICATIONS && currentSong != null
                && grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
            boolean playing = false;
            if (mediaPlayer != null && !preparing) {
                try { playing = mediaPlayer.isPlaying(); }
                catch (IllegalStateException ignored) { }
            }
            updateMediaNotification(playing);
        }
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
        handlePlaybackIntent(intent);
    }

    private void handlePlaybackIntent(Intent intent) {
        if (intent == null || intent.getAction() == null) return;
        String action = intent.getAction();
        if (ACTION_PREVIOUS.equals(action)) previousSong();
        else if (ACTION_PLAY_PAUSE.equals(action)) togglePlayback();
        else if (ACTION_NEXT.equals(action)) nextSong();
        else if (ACTION_STOP.equals(action)) stopPlaybackAndDismiss();
        intent.setAction(null);
    }

    private void chooseFolder() {
        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT_TREE);
        intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION
                | Intent.FLAG_GRANT_WRITE_URI_PERMISSION
                | Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION
                | Intent.FLAG_GRANT_PREFIX_URI_PERMISSION);
        startActivityForResult(intent, REQUEST_TREE);
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode != REQUEST_TREE || resultCode != RESULT_OK || data == null || data.getData() == null) {
            return;
        }
        Uri treeUri = data.getData();
        int flags = data.getFlags() & (Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION);
        try {
            getContentResolver().takePersistableUriPermission(treeUri, flags | Intent.FLAG_GRANT_READ_URI_PERMISSION);
        } catch (SecurityException ignored) {
            // Some document providers grant access without supporting persistable flags.
        }
        getSharedPreferences(PREFS, MODE_PRIVATE).edit().putString(PREF_TREE_URI, treeUri.toString()).apply();
        currentTreeUri = treeUri;
        scanLibrary(treeUri, true);
    }

    private void scanLibrary(Uri treeUri, boolean userInitiated) {
        final int generation = ++scanGeneration;
        final String treeKey = treeUri.toString();
        currentTreeUri = treeUri;
        playlistScanCompleted = false;
        importedPlaylists.clear();
        if (libraryMode == MODE_OTHER) updateOtherPanel();
        if (userInitiated) showScanningState();

        scanExecutor.execute(() -> {
            ArrayList<Song> cachedSongs = LibraryIndex.load(this, treeKey);
            HashMap<String, Integer> folderPlayCounts = PlayHistory.loadFromMusicFolder(
                    getContentResolver(), treeUri);
            sortSongsByTitle(cachedSongs);
            final boolean hasCache = !cachedSongs.isEmpty();

            final boolean showProgress = userInitiated || !hasCache;
            if (hasCache && !userInitiated) {
                mainHandler.post(() -> {
                    if (generation != scanGeneration) return;
                    allSongs.clear();
                    allSongs.addAll(cachedSongs);
                    mergePlayHistory(treeUri, folderPlayCounts, cachedSongs);
                    if (!playerOpen && !groupOpen) selectTab(libraryMode);
                });
            } else if (!hasCache && !userInitiated) {
                mainHandler.post(() -> {
                    if (generation == scanGeneration) showScanningState();
                });
            }

            ArrayList<PendingAudio> files = new ArrayList<>();
            ArrayList<PendingPlaylist> playlistFiles = new ArrayList<>();
            ArrayList<Song> found = new ArrayList<>();
            ArrayList<ImportedPlaylist> foundPlaylists = new ArrayList<>();
            String error = null;
            boolean completed = false;
            int addedCount = 0;
            int changedCount = 0;
            int removedCount = 0;
            int failedCount = 0;
            int playlistReadErrorCount = 0;

            try {
                String rootId = DocumentsContract.getTreeDocumentId(treeUri);
                scanDocumentTree(treeUri, rootId, "", files, playlistFiles,
                        generation, showProgress);
                if (generation != scanGeneration || Thread.currentThread().isInterrupted()) return;

                HashMap<String, Song> cachedByUri = new HashMap<>();
                for (Song cached : cachedSongs) cachedByUri.put(cached.uri.toString(), cached);

                ArrayList<MetadataTask> metadataTasks = new ArrayList<>();
                for (PendingAudio audio : files) {
                    Song cached = cachedByUri.remove(audio.uri.toString());
                    if (cached != null && isUnchanged(audio, cached)
                            && !TextUtils.isEmpty(cached.year)) {
                        found.add(cached);
                    } else {
                        metadataTasks.add(new MetadataTask(audio, cached));
                        if (cached == null) {
                            addedCount++;
                        } else if (!isUnchanged(audio, cached)) {
                            changedCount++;
                        }
                    }
                }
                removedCount = cachedByUri.size();

                final int metadataTotal = metadataTasks.size();
                for (int index = 0; index < metadataTotal; index++) {
                    if (generation != scanGeneration || Thread.currentThread().isInterrupted()) return;
                    MetadataTask task = metadataTasks.get(index);
                    postMetadataProgress(generation, index, metadataTotal,
                            task.audio.fileName, showProgress);
                    Song song = readMetadata(task.audio);
                    if (song != null) {
                        found.add(song);
                    } else if (task.previous != null) {
                        // Keep a previously working entry after a temporary provider/read error.
                        // Its old fingerprint ensures that the next scan retries the file.
                        found.add(task.previous);
                        failedCount++;
                    } else {
                        failedCount++;
                    }
                }

                sortSongsByTitle(found);
                LibraryIndex.save(this, treeKey, found);

                PlaylistImportBatch playlistBatch = importPlaylists(playlistFiles, files, found);
                foundPlaylists.addAll(playlistBatch.playlists);
                playlistReadErrorCount = playlistBatch.readErrors;
                completed = true;
            } catch (Exception ex) {
                error = ex.getMessage() == null ? ex.getClass().getSimpleName() : ex.getMessage();
            }

            final String scanError = error;
            final boolean scanCompleted = completed;
            final int added = addedCount;
            final int changed = changedCount;
            final int removed = removedCount;
            final int failed = failedCount;
            final int playlistErrors = playlistReadErrorCount;
            mainHandler.post(() -> {
                if (generation != scanGeneration) return;

                scanningState.setVisibility(View.GONE);
                playlistScanCompleted = true;
                if (scanCompleted) {
                    allSongs.clear();
                    allSongs.addAll(found);
                    mergePlayHistory(treeUri, folderPlayCounts, found);
                    importedPlaylists.clear();
                    importedPlaylists.addAll(foundPlaylists);
                }

                if (scanError != null) {
                    Toast.makeText(this,
                            "Ordner konnte nicht vollständig geprüft werden: " + scanError,
                            Toast.LENGTH_LONG).show();
                }

                if (allSongs.isEmpty()) {
                    showEmptyLibraryState();
                } else if (playlistBrowserOpen) {
                    openPlaylistBrowser();
                } else if (!playerOpen && !groupOpen) {
                    selectTab(libraryMode);
                } else if (libraryMode == MODE_OTHER) {
                    updateOtherPanel();
                }

                if (hasCache && scanCompleted && (added + changed + removed > 0)) {
                    String summary = "Bibliothek aktualisiert: " + added + " neu, "
                            + changed + " geändert, " + removed + " entfernt";
                    if (failed > 0) summary += ", " + failed + " nicht lesbar";
                    Toast.makeText(this, summary, Toast.LENGTH_LONG).show();
                }
                if (playlistErrors > 0) {
                    Toast.makeText(this, playlistErrors + " Playlist-Datei(en) nicht lesbar.",
                            Toast.LENGTH_LONG).show();
                }
            });
        });
    }

    private void scanDocumentTree(Uri treeUri, String parentDocumentId,
                                  String relativeDirectory,
                                  ArrayList<PendingAudio> audioOutput,
                                  ArrayList<PendingPlaylist> playlistOutput,
                                  int generation, boolean showProgress) {
        if (generation != scanGeneration || Thread.currentThread().isInterrupted()) return;
        Uri childrenUri = DocumentsContract.buildChildDocumentsUriUsingTree(treeUri, parentDocumentId);
        String[] projection = {
                DocumentsContract.Document.COLUMN_DOCUMENT_ID,
                DocumentsContract.Document.COLUMN_DISPLAY_NAME,
                DocumentsContract.Document.COLUMN_MIME_TYPE,
                DocumentsContract.Document.COLUMN_LAST_MODIFIED,
                DocumentsContract.Document.COLUMN_SIZE
        };

        try (Cursor cursor = getContentResolver().query(childrenUri, projection, null, null, null)) {
            if (cursor == null) return;
            int idIndex = cursor.getColumnIndexOrThrow(DocumentsContract.Document.COLUMN_DOCUMENT_ID);
            int nameIndex = cursor.getColumnIndex(DocumentsContract.Document.COLUMN_DISPLAY_NAME);
            int mimeIndex = cursor.getColumnIndex(DocumentsContract.Document.COLUMN_MIME_TYPE);
            int modifiedIndex = cursor.getColumnIndex(DocumentsContract.Document.COLUMN_LAST_MODIFIED);
            int sizeIndex = cursor.getColumnIndex(DocumentsContract.Document.COLUMN_SIZE);

            while (cursor.moveToNext()) {
                if (generation != scanGeneration || Thread.currentThread().isInterrupted()) return;
                String documentId = cursor.getString(idIndex);
                String name = nameIndex >= 0 ? cursor.getString(nameIndex) : null;
                String safeName = name == null ? "Unbekannte Datei" : name;
                String mime = mimeIndex >= 0 ? cursor.getString(mimeIndex) : null;
                long lastModified = readCursorLong(cursor, modifiedIndex, 0L);
                long size = readCursorLong(cursor, sizeIndex, -1L);
                String relativePath = joinRelativePath(relativeDirectory, safeName);

                if (DocumentsContract.Document.MIME_TYPE_DIR.equals(mime)) {
                    scanDocumentTree(treeUri, documentId, relativePath, audioOutput,
                            playlistOutput, generation, showProgress);
                } else if (isSupportedAudio(safeName, mime)) {
                    Uri fileUri = DocumentsContract.buildDocumentUriUsingTree(treeUri, documentId);
                    audioOutput.add(new PendingAudio(fileUri, safeName, relativePath,
                            lastModified, size));
                    if (audioOutput.size() == 1 || audioOutput.size() % 100 == 0) {
                        final int discovered = audioOutput.size();
                        if (showProgress) {
                            mainHandler.post(() -> {
                                if (generation == scanGeneration
                                        && scanningState.getVisibility() == View.VISIBLE) {
                                    scanProgressText.setText(discovered + " Musikdateien gefunden …");
                                }
                            });
                        }
                    }
                } else if (isSupportedPlaylist(safeName, mime)) {
                    Uri fileUri = DocumentsContract.buildDocumentUriUsingTree(treeUri, documentId);
                    playlistOutput.add(new PendingPlaylist(fileUri, safeName, relativePath));
                }
            }
        } catch (SecurityException | IllegalArgumentException ignored) {
            // Ignore folders that a provider refuses to expose.
        }
    }

    private void postMetadataProgress(int generation, int processed, int total,
                                      String fileName, boolean showProgress) {
        if (!showProgress) return;
        mainHandler.post(() -> {
            if (generation != scanGeneration || scanningState.getVisibility() != View.VISIBLE) return;
            progress.setIndeterminate(false);
            progress.setMax(Math.max(total, 1));
            progress.setProgress(processed + 1);
            scanProgressText.setText("Lese " + (processed + 1) + " / " + total + "\n" + fileName);
        });
    }

    private static long readCursorLong(Cursor cursor, int columnIndex, long fallback) {
        if (columnIndex < 0 || cursor.isNull(columnIndex)) return fallback;
        try { return cursor.getLong(columnIndex); }
        catch (RuntimeException ignored) { return fallback; }
    }

    private static boolean isUnchanged(PendingAudio audio, Song cached) {
        if (!audio.fileName.equals(cached.fileName)) return false;

        boolean comparedFingerprint = false;
        if (audio.lastModifiedMs > 0L || cached.lastModifiedMs > 0L) {
            comparedFingerprint = true;
            if (audio.lastModifiedMs != cached.lastModifiedMs) return false;
        }
        if (audio.sizeBytes >= 0L || cached.sizeBytes >= 0L) {
            comparedFingerprint = true;
            if (audio.sizeBytes != cached.sizeBytes) return false;
        }

        // Some document providers expose neither timestamp nor size. In that case
        // the stable document URI and filename are the best available identity.
        return comparedFingerprint || audio.uri.equals(cached.uri);
    }

    private static boolean isSupportedAudio(String name, String mime) {
        String lower = name == null ? "" : name.toLowerCase(Locale.ROOT);
        if (lower.endsWith(".mp3") || lower.endsWith(".flac")) return true;
        return "audio/mpeg".equalsIgnoreCase(mime) || "audio/flac".equalsIgnoreCase(mime)
                || "audio/x-flac".equalsIgnoreCase(mime);
    }

    private static boolean isSupportedPlaylist(String name, String mime) {
        String lower = name == null ? "" : name.toLowerCase(Locale.ROOT);
        if (lower.endsWith(".m3u") || lower.endsWith(".m3u8")) return true;
        return "audio/x-mpegurl".equalsIgnoreCase(mime)
                || "application/x-mpegurl".equalsIgnoreCase(mime)
                || "application/vnd.apple.mpegurl".equalsIgnoreCase(mime);
    }

    private static String joinRelativePath(String directory, String name) {
        if (TextUtils.isEmpty(directory)) return M3uPlaylistReader.normalizeRelativePath(name);
        return M3uPlaylistReader.normalizeRelativePath(directory + "/" + name);
    }

    private PlaylistImportBatch importPlaylists(List<PendingPlaylist> playlistFiles,
                                                List<PendingAudio> audioFiles,
                                                List<Song> songs) {
        HashMap<String, String> uriByRelativePath = new HashMap<>();
        HashMap<String, String> uniqueUriByFileName = new HashMap<>();
        for (PendingAudio audio : audioFiles) {
            String uri = audio.uri.toString();
            uriByRelativePath.put(M3uPlaylistReader.key(audio.relativePath), uri);

            String fileKey = M3uPlaylistReader.key(audio.fileName);
            if (uniqueUriByFileName.containsKey(fileKey)) {
                uniqueUriByFileName.put(fileKey, null);
            } else {
                uniqueUriByFileName.put(fileKey, uri);
            }
        }

        HashMap<String, Song> songByUri = new HashMap<>();
        for (Song song : songs) songByUri.put(song.uri.toString(), song);

        ArrayList<ImportedPlaylist> result = new ArrayList<>();
        int readErrors = 0;
        for (PendingPlaylist playlistFile : playlistFiles) {
            try {
                ArrayList<String> entries = M3uPlaylistReader.readEntries(
                        getContentResolver(), playlistFile.uri, playlistFile.fileName);
                ArrayList<Song> matchedSongs = new ArrayList<>();
                int missing = 0;
                for (String entry : entries) {
                    String songUri = M3uPlaylistReader.matchSongUri(
                            entry, uriByRelativePath, uniqueUriByFileName);
                    if (songUri == null) {
                        int parentSlash = playlistFile.relativePath.lastIndexOf('/');
                        if (parentSlash > 0) {
                            String playlistParent = playlistFile.relativePath.substring(0, parentSlash);
                            String relativeToPlaylist = M3uPlaylistReader.normalizeRelativePath(
                                    playlistParent + "/" + entry);
                            songUri = M3uPlaylistReader.matchSongUri(
                                    relativeToPlaylist, uriByRelativePath, uniqueUriByFileName);
                        }
                    }
                    Song song = songUri == null ? null : songByUri.get(songUri);
                    if (song == null) missing++; else matchedSongs.add(song);
                }
                result.add(new ImportedPlaylist(stripExtension(playlistFile.fileName),
                        playlistFile.relativePath, matchedSongs, entries.size(), missing));
            } catch (IOException | RuntimeException ignored) {
                readErrors++;
            }
        }

        result.sort((left, right) -> {
            int byName = left.name.compareToIgnoreCase(right.name);
            if (byName != 0) return byName;
            return left.sourceRelativePath.compareToIgnoreCase(right.sourceRelativePath);
        });

        HashMap<String, Integer> nameCounts = new HashMap<>();
        for (ImportedPlaylist playlist : result) {
            String key = playlist.name.toLowerCase(Locale.ROOT);
            nameCounts.put(key, nameCounts.getOrDefault(key, 0) + 1);
        }
        for (ImportedPlaylist playlist : result) {
            if (nameCounts.getOrDefault(playlist.name.toLowerCase(Locale.ROOT), 0) > 1) {
                int slash = playlist.sourceRelativePath.lastIndexOf('/');
                String parent = slash <= 0 ? "Musikordner"
                        : playlist.sourceRelativePath.substring(0, slash);
                playlist.name = playlist.name + " · " + parent;
            }
        }
        return new PlaylistImportBatch(result, readErrors);
    }

    private Song readMetadata(PendingAudio audio) {
        MediaMetadataRetriever retriever = new MediaMetadataRetriever();
        try {
            retriever.setDataSource(this, audio.uri);
            String fallbackTitle = stripExtension(audio.fileName);
            String title = valueOr(retriever.extractMetadata(MediaMetadataRetriever.METADATA_KEY_TITLE), fallbackTitle);
            String artist = valueOr(retriever.extractMetadata(MediaMetadataRetriever.METADATA_KEY_ARTIST), "Unbekannter Interpret");
            String album = valueOr(retriever.extractMetadata(MediaMetadataRetriever.METADATA_KEY_ALBUM), "Unbekanntes Album");

            // Read the raw tag first. Android's MediaMetadataRetriever can interpret
            // leading digits in ID3 TCON as a legacy genre number and then omit or
            // rewrite custom values. The raw reader preserves e.g. "2012_3.Summer".
            String rawGenre = GenreTagReader.readGenre(getContentResolver(), audio.uri, audio.fileName);
            String androidGenre = retriever.extractMetadata(MediaMetadataRetriever.METADATA_KEY_GENRE);
            String genre = valueOr(rawGenre, valueOr(androidGenre, "Unbekannt"));
            String rawYear = YearTagReader.readYear(getContentResolver(), audio.uri, audio.fileName);
    String androidYear = retriever.extractMetadata(MediaMetadataRetriever.METADATA_KEY_YEAR);
    String year = valueOr(rawYear, valueOr(androidYear, "Unbekannt"));
            int track = parseTrackNumber(retriever.extractMetadata(MediaMetadataRetriever.METADATA_KEY_CD_TRACK_NUMBER));
            long duration = parseLong(retriever.extractMetadata(MediaMetadataRetriever.METADATA_KEY_DURATION));
            return new Song(audio.uri, audio.fileName, title, artist, album, genre, year,
                    track, duration, audio.lastModifiedMs, audio.sizeBytes);
        } catch (RuntimeException ex) {
            return null;
        } finally {
            try { retriever.release(); } catch (IOException ignored) { }
        }
    }

    private void selectTab(int mode) {
        libraryMode = mode;
        groupOpen = false;
        groupUsesTrackNumbers = false;
        showPlayCounts = false;
        playlistBrowserOpen = false;
        playlistDetailOpen = false;
        playerOpen = false;
        playerPanel.setVisibility(View.GONE);
        scanningState.setVisibility(View.GONE);
        otherPanel.setVisibility(View.GONE);
        tabBar.setVisibility(View.VISIBLE);
        backButton.setVisibility(View.GONE);
        titleText.setText("Musikplayer");
        updateTabStyles();

        visibleSongs.clear();
        visibleGroups.clear();
        searchRows.clear();
        searchPlayableSongs.clear();
        if (mode == MODE_OTHER) {
            libraryList.setVisibility(View.GONE);
            emptyState.setVisibility(View.GONE);
            randomPlayButton.setVisibility(View.GONE);
            searchRow.setVisibility(View.GONE);
            alphabetIndex.setVisibility(View.GONE);
            otherPanel.setVisibility(View.VISIBLE);
            updateOtherPanel();
            adapter.notifyDataSetChanged();
            refreshInsets();
            return;
        }

        libraryList.setVisibility(View.VISIBLE);
        searchRow.setVisibility(allSongs.isEmpty() ? View.GONE : View.VISIBLE);
        if (allSongs.isEmpty()) {
            randomPlayButton.setVisibility(View.GONE);
            alphabetIndex.setVisibility(View.GONE);
            adapter.notifyDataSetChanged();
            return;
        }
        emptyState.setVisibility(View.GONE);
        if (!TextUtils.isEmpty(searchInput.getText())) {
            applySearch(searchInput.getText().toString());
            return;
        }
        searchQuery = "";
        if (mode == MODE_SONGS) {
            visibleSongs.addAll(allSongs);
            sortSongsByTitle(visibleSongs);
            randomPlayButton.setVisibility(View.VISIBLE);
        } else if (mode == MODE_ALBUMS) {
            visibleGroups.addAll(buildGroups(true));
            randomPlayButton.setVisibility(View.GONE);
        } else if (mode == MODE_GENRES) {
            visibleGroups.addAll(buildGroups(false));
            randomPlayButton.setVisibility(View.GONE);
        } else if (mode == MODE_YEARS) {
            visibleGroups.addAll(buildYearGroups());
            randomPlayButton.setVisibility(View.GONE);
        }
        adapter.notifyDataSetChanged();
        updateAlphabetVisibility();
        refreshInsets();
    }

    private void applySearch(String rawQuery) {
        String query = SearchMatcher.normalizeQuery(rawQuery);
        searchQuery = query;
        if (libraryMode == MODE_OTHER || groupOpen || playerOpen) return;
        if (query.isEmpty()) {
            selectTab(libraryMode);
            return;
        }

        visibleGroups.clear();
        visibleSongs.clear();
        searchRows.clear();
        searchPlayableSongs.clear();

        LinkedHashMap<String, ArrayList<Song>> albumMatches = new LinkedHashMap<>();
        LinkedHashMap<String, ArrayList<Song>> artistMatches = new LinkedHashMap<>();
        ArrayList<Song> songMatches = new ArrayList<>();

        for (Song song : allSongs) {
            if (SearchMatcher.contains(song.album, query)) {
                albumMatches.computeIfAbsent(song.album, key -> new ArrayList<>()).add(song);
            }
            if (SearchMatcher.contains(song.title, query)) {
                songMatches.add(song);
            }
            if (SearchMatcher.contains(song.artist, query)) {
                artistMatches.computeIfAbsent(song.artist, key -> new ArrayList<>()).add(song);
            }
        }

        ArrayList<Map.Entry<String, ArrayList<Song>>> albums = new ArrayList<>(albumMatches.entrySet());
        albums.sort((left, right) -> left.getKey().compareToIgnoreCase(right.getKey()));
        if (!albums.isEmpty()) {
            searchRows.add(SearchResultRow.header("ALBEN · " + albums.size()));
            for (Map.Entry<String, ArrayList<Song>> entry : albums) {
                sortAlbumTracks(entry.getValue());
                searchRows.add(SearchResultRow.album(entry.getKey(), entry.getValue()));
            }
        }

        sortSongsByTitle(songMatches);
        if (!songMatches.isEmpty()) {
            searchRows.add(SearchResultRow.header("SONGS · " + songMatches.size()));
            for (Song song : songMatches) searchRows.add(SearchResultRow.song(song));
        }

        ArrayList<Map.Entry<String, ArrayList<Song>>> artists = new ArrayList<>(artistMatches.entrySet());
        artists.sort((left, right) -> left.getKey().compareToIgnoreCase(right.getKey()));
        if (!artists.isEmpty()) {
            searchRows.add(SearchResultRow.header("INTERPRETEN · " + artists.size()));
            for (Map.Entry<String, ArrayList<Song>> entry : artists) {
                sortSongsByTitle(entry.getValue());
                searchRows.add(SearchResultRow.artist(entry.getKey(), entry.getValue()));
            }
        }

        LinkedHashMap<String, Song> playableByUri = new LinkedHashMap<>();
        for (Map.Entry<String, ArrayList<Song>> entry : albums) {
            for (Song song : entry.getValue()) playableByUri.put(song.uri.toString(), song);
        }
        for (Song song : songMatches) playableByUri.put(song.uri.toString(), song);
        for (Map.Entry<String, ArrayList<Song>> entry : artists) {
            for (Song song : entry.getValue()) playableByUri.put(song.uri.toString(), song);
        }
        searchPlayableSongs.addAll(playableByUri.values());

        int resultCount = albums.size() + songMatches.size() + artists.size();
        libraryList.setVisibility(View.VISIBLE);
        emptyState.setVisibility(View.GONE);
        otherPanel.setVisibility(View.GONE);
        randomPlayButton.setVisibility(searchPlayableSongs.isEmpty() ? View.GONE : View.VISIBLE);
        alphabetIndex.setVisibility(View.GONE);
        titleText.setText("Suche · " + resultCount + (resultCount == 1 ? " Treffer" : " Treffer"));
        adapter.notifyDataSetChanged();
    }

    private void hideSearchKeyboard() {
        searchInput.clearFocus();
        InputMethodManager inputMethodManager =
                (InputMethodManager) getSystemService(Context.INPUT_METHOD_SERVICE);
        if (inputMethodManager != null) {
            inputMethodManager.hideSoftInputFromWindow(searchInput.getWindowToken(), 0);
        }
    }

    private static String normalizeSearch(String value) {
        return SearchMatcher.normalize(value);
    }

    private void jumpToLetter(String letter) {
        if (!TextUtils.isEmpty(searchQuery) || groupOpen || playerOpen
                || libraryMode == MODE_OTHER || libraryMode == MODE_YEARS) return;
        int count = visibleGroups.isEmpty() ? visibleSongs.size() : visibleGroups.size();
        for (int index = 0; index < count; index++) {
            String name = visibleGroups.isEmpty() ? visibleSongs.get(index).title : visibleGroups.get(index).name;
            if (letter.equals(sectionFor(name))) {
                libraryList.setSelection(index);
                return;
            }
        }
    }

    private static String sectionFor(String value) {
        String normalized = normalizeSearch(value).trim();
        if (normalized.isEmpty()) return "#";
        char first = normalized.charAt(0);
        return first >= 'a' && first <= 'z' ? String.valueOf(Character.toUpperCase(first)) : "#";
    }

    private void updateAlphabetVisibility() {
        int count = visibleGroups.isEmpty() ? visibleSongs.size() : visibleGroups.size();
        boolean show = count >= 30 && TextUtils.isEmpty(searchQuery) && !groupOpen && !playerOpen
                && libraryMode != MODE_OTHER && libraryMode != MODE_YEARS
                && libraryList.getVisibility() == View.VISIBLE;
        alphabetIndex.setVisibility(show ? View.VISIBLE : View.GONE);
    }

    private void updateTabStyles() {
        styleTab(tabSongs, libraryMode == MODE_SONGS);
        styleTab(tabAlbums, libraryMode == MODE_ALBUMS);
        styleTab(tabGenres, libraryMode == MODE_GENRES);
        styleTab(tabYears, libraryMode == MODE_YEARS);
        styleTab(tabOther, libraryMode == MODE_OTHER);
    }

    private void styleTab(Button button, boolean selected) {
        button.setBackgroundResource(selected ? R.drawable.tab_selected : R.drawable.tab_normal);
        button.setTextColor(getColor(selected ? R.color.accent : R.color.text_secondary));
    }

    private List<GroupRow> buildGroups(boolean albums) {
        LinkedHashMap<String, ArrayList<Song>> groups = new LinkedHashMap<>();
        ArrayList<Song> source = new ArrayList<>(allSongs);
        source.sort((left, right) -> {
            String a = albums ? left.album : left.genre;
            String b = albums ? right.album : right.genre;
            int result = a.compareToIgnoreCase(b);
            if (result != 0) return result;
            if (albums) {
                result = Integer.compare(normalizedTrack(left.trackNumber), normalizedTrack(right.trackNumber));
                if (result != 0) return result;
            }
            return left.title.compareToIgnoreCase(right.title);
        });
        for (Song song : source) {
            String key = albums ? song.album : song.genre;
            ArrayList<Song> group = groups.get(key);
            if (group == null) {
                group = new ArrayList<>();
                groups.put(key, group);
            }
            group.add(song);
        }

        ArrayList<GroupRow> result = new ArrayList<>();
        for (Map.Entry<String, ArrayList<Song>> entry : groups.entrySet()) {
            ArrayList<Song> songs = entry.getValue();
            if (albums) sortAlbumTracks(songs); else sortSongsByTitle(songs);
            result.add(new GroupRow(entry.getKey(), songs, albums));
        }
        result.sort((a, b) -> a.name.compareToIgnoreCase(b.name));
        return result;
    }

    private List<GroupRow> buildYearGroups() {
        LinkedHashMap<String, ArrayList<Song>> groups = new LinkedHashMap<>();
        for (Song song : allSongs) {
            String year = valueOr(song.year, "Unbekannt");
            groups.computeIfAbsent(year, key -> new ArrayList<>()).add(song);
        }

        ArrayList<GroupRow> result = new ArrayList<>();
        for (Map.Entry<String, ArrayList<Song>> entry : groups.entrySet()) {
            ArrayList<Song> songs = entry.getValue();
            sortSongsByTitle(songs);
            result.add(new GroupRow(entry.getKey(), songs, false));
        }
        result.sort((left, right) -> {
            boolean leftUnknown = "Unbekannt".equalsIgnoreCase(left.name);
            boolean rightUnknown = "Unbekannt".equalsIgnoreCase(right.name);
            if (leftUnknown != rightUnknown) return leftUnknown ? 1 : -1;
            return left.name.compareToIgnoreCase(right.name);
        });
        return result;
    }

    private void openGroup(GroupRow group) {
        if (group.playlistGroup && group.songs.isEmpty()) {
            Toast.makeText(this, "In dieser Playlist wurde kein Titel im Musikordner gefunden.",
                    Toast.LENGTH_LONG).show();
            return;
        }
        groupOpen = true;
        playlistDetailOpen = group.playlistGroup;
        playlistBrowserOpen = false;
        showPlayCounts = false;
        groupUsesTrackNumbers = group.albumGroup;
        visibleGroups.clear();
        visibleSongs.clear();
        visibleSongs.addAll(group.songs);
        tabBar.setVisibility(View.GONE);
        searchRow.setVisibility(View.GONE);
        alphabetIndex.setVisibility(View.GONE);
        otherPanel.setVisibility(View.GONE);
        randomPlayButton.setVisibility(visibleSongs.isEmpty() ? View.GONE : View.VISIBLE);
        backButton.setVisibility(View.VISIBLE);
        titleText.setText(group.name);
        adapter.notifyDataSetChanged();
        refreshInsets();
    }

    private void openSearchGroup(SearchResultRow result) {
        if (result.group == null) return;
        groupOpen = true;
        playlistBrowserOpen = false;
        playlistDetailOpen = false;
        showPlayCounts = false;
        groupUsesTrackNumbers = result.type == SearchResultRow.TYPE_ALBUM;
        visibleGroups.clear();
        visibleSongs.clear();
        visibleSongs.addAll(result.group.songs);
        tabBar.setVisibility(View.GONE);
        searchRow.setVisibility(View.GONE);
        alphabetIndex.setVisibility(View.GONE);
        otherPanel.setVisibility(View.GONE);
        randomPlayButton.setVisibility(visibleSongs.isEmpty() ? View.GONE : View.VISIBLE);
        backButton.setVisibility(View.VISIBLE);
        titleText.setText(result.label);
        adapter.notifyDataSetChanged();
        refreshInsets();
    }

    private void updateOtherPanel() {
        int playedSongs = 0;
        for (Song song : allSongs) {
            if (getPlayCount(song) > 0) playedSongs++;
        }
        topPlayedButton.setText(playedSongs == 0
                ? "TOP 50 MEISTGESPIELT"
                : "TOP 50 MEISTGESPIELT · " + Math.min(50, playedSongs) + " TITEL");
        topPlayedButton.setEnabled(playedSongs > 0);
        topPlayedButton.setAlpha(playedSongs > 0 ? 1f : 0.55f);

        if (!playlistScanCompleted) {
            playlistsButton.setText("PLAYLISTS WERDEN GELADEN …");
            playlistsButton.setEnabled(false);
            playlistsButton.setAlpha(0.55f);
        } else {
            int count = importedPlaylists.size();
            playlistsButton.setText(count == 0
                    ? "PLAYLISTS (.M3U / .M3U8)"
                    : "PLAYLISTS · " + count);
            playlistsButton.setEnabled(true);
            playlistsButton.setAlpha(count > 0 ? 1f : 0.7f);
        }
    }

    private void openTopPlayed() {
        ArrayList<Song> songs = new ArrayList<>();
        for (Song song : allSongs) {
            if (getPlayCount(song) > 0) songs.add(song);
        }
        songs.sort((left, right) -> {
            int byCount = Integer.compare(getPlayCount(right), getPlayCount(left));
            if (byCount != 0) return byCount;
            return left.title.compareToIgnoreCase(right.title);
        });
        if (songs.size() > 50) songs.subList(50, songs.size()).clear();
        if (songs.isEmpty()) {
            Toast.makeText(this, "Noch keine vollständig genug gehörten Titel.", Toast.LENGTH_SHORT).show();
            return;
        }
        openSpecialSongList("Top 50 meistgespielt", songs, true);
    }

    private void openPlaylistBrowser() {
        if (importedPlaylists.isEmpty()) {
            selectTab(MODE_OTHER);
            Toast.makeText(this, "Keine Playlists gefunden.", Toast.LENGTH_SHORT).show();
            return;
        }
        groupOpen = true;
        playlistBrowserOpen = true;
        playlistDetailOpen = false;
        showPlayCounts = false;
        playerOpen = false;
        groupUsesTrackNumbers = false;
        visibleSongs.clear();
        visibleGroups.clear();
        for (ImportedPlaylist playlist : importedPlaylists) {
            visibleGroups.add(GroupRow.playlist(playlist));
        }
        playerPanel.setVisibility(View.GONE);
        otherPanel.setVisibility(View.GONE);
        emptyState.setVisibility(View.GONE);
        libraryList.setVisibility(View.VISIBLE);
        tabBar.setVisibility(View.GONE);
        searchRow.setVisibility(View.GONE);
        alphabetIndex.setVisibility(View.GONE);
        randomPlayButton.setVisibility(View.GONE);
        backButton.setVisibility(View.VISIBLE);
        titleText.setText("Playlists");
        adapter.notifyDataSetChanged();
        refreshInsets();
    }

    private void openSpecialSongList(String title, List<Song> songs, boolean displayPlayCounts) {
        groupOpen = true;
        playlistBrowserOpen = false;
        playlistDetailOpen = false;
        playerOpen = false;
        groupUsesTrackNumbers = false;
        showPlayCounts = displayPlayCounts;
        visibleGroups.clear();
        visibleSongs.clear();
        visibleSongs.addAll(songs);
        playerPanel.setVisibility(View.GONE);
        otherPanel.setVisibility(View.GONE);
        emptyState.setVisibility(View.GONE);
        libraryList.setVisibility(View.VISIBLE);
        tabBar.setVisibility(View.GONE);
        searchRow.setVisibility(View.GONE);
        alphabetIndex.setVisibility(View.GONE);
        randomPlayButton.setVisibility(visibleSongs.isEmpty() ? View.GONE : View.VISIBLE);
        backButton.setVisibility(View.VISIBLE);
        titleText.setText(title);
        adapter.notifyDataSetChanged();
        refreshInsets();
    }

    private void openPlayer() {
        if (currentSong == null) return;
        playerOpen = true;
        groupOpen = false;
        playlistBrowserOpen = false;
        playlistDetailOpen = false;
        libraryList.setVisibility(View.GONE);
        emptyState.setVisibility(View.GONE);
        tabBar.setVisibility(View.GONE);
        searchRow.setVisibility(View.GONE);
        alphabetIndex.setVisibility(View.GONE);
        otherPanel.setVisibility(View.GONE);
        randomPlayButton.setVisibility(View.GONE);
        playerPanel.setVisibility(View.VISIBLE);
        backButton.setVisibility(View.VISIBLE);
        titleText.setText("Aktuelle Wiedergabe");
        updatePlayerMetadata();
        refreshInsets();
    }

    private void handleBack() {
        if (playerOpen) {
            playerOpen = false;
            playerPanel.setVisibility(View.GONE);
            libraryList.setVisibility(View.VISIBLE);
            selectTab(libraryMode);
        } else if (playlistDetailOpen) {
            openPlaylistBrowser();
        } else if (playlistBrowserOpen) {
            selectTab(MODE_OTHER);
            refreshInsets();
        } else if (groupOpen) {
            selectTab(libraryMode);
            refreshInsets();
        }
    }

    @Override
    public void onBackPressed() {
        if (playerOpen || groupOpen) handleBack();
        else super.onBackPressed();
    }

    private void playCurrentListRandomly() {
        List<Song> source = !TextUtils.isEmpty(searchQuery) && !groupOpen
                ? searchPlayableSongs : visibleSongs;
        if (source.isEmpty()) return;
        playQueue.clear();
        playQueue.addAll(source);
        Collections.shuffle(playQueue);
        currentQueueIndex = 0;
        playSong(playQueue.get(0));
        Toast.makeText(this, "Zufallswiedergabe: " + playQueue.size() + " Titel", Toast.LENGTH_SHORT).show();
    }

    private void playSongFromList(List<Song> source, int index) {
        if (index < 0 || index >= source.size()) return;
        playQueue.clear();
        playQueue.addAll(source);
        currentQueueIndex = index;
        playSong(playQueue.get(index));
    }

    private void playSong(Song song) {
        releasePlayer(false);
        if (mediaSession != null) mediaSession.setActive(true);
        currentSong = song;
        resetPlayCountCycle();
        preparing = true;
        mediaPlayer = new MediaPlayer();
        mediaPlayer.setAudioAttributes(new AudioAttributes.Builder()
                .setContentType(AudioAttributes.CONTENT_TYPE_MUSIC)
                .setUsage(AudioAttributes.USAGE_MEDIA)
                .build());
        mediaPlayer.setLooping(repeatOne);
        mediaPlayer.setOnCompletionListener(this);
        mediaPlayer.setOnPreparedListener(player -> {
            preparing = false;
            if (requestAudioFocus()) {
                player.start();
            } else {
                Toast.makeText(this, "Audio-Fokus konnte nicht übernommen werden.", Toast.LENGTH_SHORT).show();
            }
            updatePlayButtons();
            seekBar.setMax(Math.max(player.getDuration(), 1));
            totalTime.setText(formatDuration(player.getDuration()));
        });
        mediaPlayer.setOnErrorListener((player, what, extra) -> {
            preparing = false;
            Toast.makeText(this, "Datei konnte nicht abgespielt werden.", Toast.LENGTH_SHORT).show();
            updatePlayButtons();
            return true;
        });
        try {
            mediaPlayer.setDataSource(this, song.uri);
            mediaPlayer.prepareAsync();
            miniPlayer.setVisibility(View.VISIBLE);
            refreshInsets();
            updatePlayerMetadata();
            updatePlayButtons();
        } catch (IOException | SecurityException ex) {
            preparing = false;
            Toast.makeText(this, "Kein Zugriff auf diese Audiodatei.", Toast.LENGTH_SHORT).show();
        }
    }

    private void togglePlayback() {
        if (mediaPlayer == null || preparing) return;
        try {
            if (mediaPlayer.isPlaying()) {
                mediaPlayer.pause();
            } else if (requestAudioFocus()) {
                mediaPlayer.setVolume(1f, 1f);
                mediaPlayer.start();
            }
            updatePlayButtons();
        } catch (IllegalStateException ignored) { }
    }

    private void toggleRepeatOne() {
        repeatOne = !repeatOne;
        getSharedPreferences(PREFS, MODE_PRIVATE).edit().putBoolean(PREF_REPEAT_ONE, repeatOne).apply();
        if (mediaPlayer != null) {
            try { mediaPlayer.setLooping(repeatOne); }
            catch (IllegalStateException ignored) { }
        }
        updateRepeatButtons();
        Toast.makeText(this, repeatOne ? "Titel-Wiederholung an" : "Titel-Wiederholung aus",
                Toast.LENGTH_SHORT).show();
    }

    private void updateRepeatButtons() {
        if (miniRepeat == null || playerRepeat == null) return;
        int color = getColor(repeatOne ? R.color.accent : R.color.text_secondary);
        miniRepeat.setTextColor(color);
        playerRepeat.setTextColor(color);
        miniRepeat.setContentDescription(repeatOne ? "Titel-Wiederholung ausschalten" : "Titel-Wiederholung einschalten");
        playerRepeat.setContentDescription(repeatOne ? "Titel-Wiederholung ausschalten" : "Titel-Wiederholung einschalten");
    }

    private void previousSong() {
        if (mediaPlayer != null && !preparing) {
            try {
                if (mediaPlayer.getCurrentPosition() > 5000) {
                    mediaPlayer.seekTo(0);
                    resetPlayCountCycle();
                    return;
                }
            } catch (IllegalStateException ignored) { }
        }
        if (playQueue.isEmpty()) return;
        currentQueueIndex = (currentQueueIndex - 1 + playQueue.size()) % playQueue.size();
        playSong(playQueue.get(currentQueueIndex));
    }

    private void nextSong() {
        if (playQueue.isEmpty()) return;
        currentQueueIndex = (currentQueueIndex + 1) % playQueue.size();
        playSong(playQueue.get(currentQueueIndex));
    }

    @Override
    public void onCompletion(MediaPlayer mp) {
        if (repeatOne && currentSong != null) {
            resetPlayCountCycle();
            try {
                mp.seekTo(0);
                mp.start();
                updatePlayButtons();
            } catch (IllegalStateException ignored) { }
        } else {
            nextSong();
        }
    }

    private void updatePlayButtons() {
        boolean playing = false;
        if (mediaPlayer != null && !preparing) {
            try { playing = mediaPlayer.isPlaying(); }
            catch (IllegalStateException ignored) { }
        }
        String icon = playing ? "Ⅱ" : "▶";
        miniPlay.setText(icon);
        playerPlay.setText(icon);
        updateSystemPlaybackState(playing);
        updateMediaNotification(playing);
    }

    private void updatePlayerMetadata() {
        if (currentSong == null) return;
        miniTitle.setText(currentSong.title);
        miniArtist.setText(currentSong.artist);
        playerTitle.setText(currentSong.title);
        playerArtist.setText(currentSong.artist);
        playerAlbum.setText(currentSong.album);
        if (currentSong.trackNumber > 0) {
            playerTrackNumber.setText("Nummer: " + currentSong.trackNumber);
            playerTrackNumber.setVisibility(View.VISIBLE);
        } else {
            playerTrackNumber.setText("");
            playerTrackNumber.setVisibility(View.GONE);
        }
        String genre = currentSong.genre == null ? "" : currentSong.genre.trim();
        if (genre.isEmpty() || "Unbekannt".equalsIgnoreCase(genre)) {
            playerGenre.setText("");
            playerGenre.setVisibility(View.GONE);
        } else {
            playerGenre.setText(genre);
            playerGenre.setVisibility(View.VISIBLE);
        }
        totalTime.setText(formatDuration(currentSong.durationMs));
        updateSystemMetadata(null);
        loadArtwork(currentSong);
    }

    private void configureMarquee(TextView view) {
        if (view == null) return;
        view.setSingleLine(true);
        view.setHorizontallyScrolling(true);
        view.setEllipsize(TextUtils.TruncateAt.MARQUEE);
        view.setMarqueeRepeatLimit(-1);
        view.setSelected(true);
    }

    private void resetPlayCountCycle() {
        playCountedThisCycle = false;
        listenedThisCycleMs = 0L;
        lastProgressRealtimeMs = 0L;
        lastPlaybackPositionMs = 0;
    }

    private void updatePlayCountProgress(int position, int duration, boolean playing) {
        long now = SystemClock.elapsedRealtime();
        if (duration <= 0 || currentSong == null) {
            lastProgressRealtimeMs = now;
            lastPlaybackPositionMs = position;
            return;
        }

        // MediaPlayer loops without a completion callback on many devices. Detect the
        // jump from the end back to the beginning so every real repeat is a new listen.
        if (repeatOne && lastPlaybackPositionMs > duration * 85 / 100
                && position < duration * 15 / 100) {
            playCountedThisCycle = false;
            listenedThisCycleMs = 0L;
            lastProgressRealtimeMs = now;
        }

        if (playing && lastProgressRealtimeMs > 0L) {
            long elapsed = now - lastProgressRealtimeMs;
            // Do not award minutes after the process/UI was suspended for a long time.
            if (elapsed > 0L && elapsed <= 5000L) listenedThisCycleMs += elapsed;
        }
        lastProgressRealtimeMs = now;
        lastPlaybackPositionMs = position;

        if (!playCountedThisCycle && listenedThisCycleMs * 2L > duration) {
            playCountedThisCycle = true;
            String key = PlayHistory.keyForSong(currentTreeUri, currentSong);
            int previousCount = getPlayCount(currentSong);
            int next = previousCount == Integer.MAX_VALUE ? Integer.MAX_VALUE : previousCount + 1;
            playCounts.put(key, next);
            savePlayHistoryAsync();
            if (showPlayCounts) adapter.notifyDataSetChanged();
        }
    }

    private int getPlayCount(Song song) {
        String stableKey = PlayHistory.keyForSong(currentTreeUri, song);
        Integer stable = playCounts.get(stableKey);
        Integer legacy = playCounts.get(song.uri.toString());
        return Math.max(stable == null ? 0 : stable, legacy == null ? 0 : legacy);
    }

    private void mergePlayHistory(Uri treeUri, Map<String, Integer> folderCounts, List<Song> songs) {
        for (Map.Entry<String, Integer> entry : folderCounts.entrySet()) {
            if (entry.getValue() == null || entry.getValue() <= 0) continue;
            int current = playCounts.getOrDefault(entry.getKey(), 0);
            if (entry.getValue() > current) playCounts.put(entry.getKey(), entry.getValue());
        }
        boolean migrated = false;
        for (Song song : songs) {
            String stableKey = PlayHistory.keyForSong(treeUri, song);
            String legacyKey = song.uri.toString();
            int stable = playCounts.getOrDefault(stableKey, 0);
            int legacy = playCounts.getOrDefault(legacyKey, 0);
            int merged = Math.max(stable, legacy);
            if (merged > 0) playCounts.put(stableKey, merged);
            if (!stableKey.equals(legacyKey) && playCounts.remove(legacyKey) != null) migrated = true;
        }
        if (migrated || (!playCounts.isEmpty() && folderCounts.isEmpty())) savePlayHistoryAsync();
    }

    private void savePlayHistoryAsync() {
        HashMap<String, Integer> snapshot = new HashMap<>(playCounts);
        Uri tree = currentTreeUri;
        historyExecutor.execute(() -> {
            PlayHistory.save(getApplicationContext(), snapshot);
            if (tree != null) {
                PlayHistory.saveToMusicFolder(getContentResolver(), tree, snapshot);
            }
        });
    }

    private void loadArtwork(Song song) {
        artwork.setImageDrawable(new ColorDrawable(getColor(R.color.surface)));
        artwork.setPadding(dp(48), dp(48), dp(48), dp(48));
        scanExecutor.execute(() -> {
            MediaMetadataRetriever retriever = new MediaMetadataRetriever();
            Bitmap bitmap = null;
            try {
                retriever.setDataSource(this, song.uri);
                byte[] bytes = retriever.getEmbeddedPicture();
                if (bytes != null && bytes.length > 0) {
                    BitmapFactory.Options bounds = new BitmapFactory.Options();
                    bounds.inJustDecodeBounds = true;
                    BitmapFactory.decodeByteArray(bytes, 0, bytes.length, bounds);
                    bounds.inSampleSize = calculateSample(bounds.outWidth, bounds.outHeight, 512);
                    bounds.inJustDecodeBounds = false;
                    bitmap = BitmapFactory.decodeByteArray(bytes, 0, bytes.length, bounds);
                }
            } catch (RuntimeException ignored) {
            } finally {
                try { retriever.release(); } catch (IOException ignored) { }
            }
            Bitmap finalBitmap = bitmap;
            mainHandler.post(() -> {
                if (currentSong != song) return;
                if (finalBitmap != null) {
                    artwork.setPadding(0, 0, 0, 0);
                    artwork.setImageBitmap(finalBitmap);
                    updateSystemMetadata(finalBitmap);
                } else {
                    artwork.setPadding(dp(48), dp(48), dp(48), dp(48));
                    artwork.setImageDrawable(new MusicNoteDrawable(getColor(R.color.accent)));
                }
            });
        });
    }

    private void releasePlayer() {
        releasePlayer(true);
    }

    private void releasePlayer(boolean abandonFocus) {
        if (mediaPlayer != null) {
            try { mediaPlayer.reset(); } catch (IllegalStateException ignored) { }
            mediaPlayer.release();
            mediaPlayer = null;
        }
        preparing = false;
        lastProgressRealtimeMs = 0L;
        lastPlaybackStateSyncRealtimeMs = 0L;
        if (abandonFocus) abandonAudioFocus();
    }

    private void stopPlaybackAndDismiss() {
        releasePlayer();
        playQueue.clear();
        currentQueueIndex = -1;
        currentSong = null;
        preparing = false;
        playerOpen = false;
        miniPlayer.setVisibility(View.GONE);
        playerPanel.setVisibility(View.GONE);
        seekBar.setProgress(0);
        currentTime.setText("0:00");
        totalTime.setText("0:00");
        if (playerTrackNumber != null) {
            playerTrackNumber.setText("");
            playerTrackNumber.setVisibility(View.GONE);
        }
        if (playerGenre != null) {
            playerGenre.setText("");
            playerGenre.setVisibility(View.GONE);
        }
        if (mediaSession != null) {
            long actions = PlaybackState.ACTION_PLAY | PlaybackState.ACTION_PLAY_PAUSE;
            mediaSession.setPlaybackState(new PlaybackState.Builder()
                    .setActions(actions)
                    .setState(PlaybackState.STATE_STOPPED, 0L, 0f, SystemClock.elapsedRealtime())
                    .build());
            mediaSession.setMetadata(null);
            mediaSession.setActive(false);
        }
        if (notificationManager != null) notificationManager.cancel(MEDIA_NOTIFICATION_ID);
        if (!allSongs.isEmpty()) selectTab(libraryMode);
        refreshInsets();
    }

    private void showNoFolderState() {
        scanningState.setVisibility(View.GONE);
        randomPlayButton.setVisibility(View.GONE);
        searchRow.setVisibility(View.GONE);
        alphabetIndex.setVisibility(View.GONE);
        otherPanel.setVisibility(View.GONE);
        emptyState.setVisibility(View.VISIBLE);
        libraryList.setVisibility(View.GONE);
        ((TextView) findViewById(R.id.emptyTitle)).setText("Kein Musikordner ausgewählt");
        ((TextView) findViewById(R.id.emptyMessage)).setText("Wähle einen Ordner mit MP3- oder FLAC-Dateien.");
        refreshInsets();
    }

    private void showScanningState() {
        playerPanel.setVisibility(View.GONE);
        searchRow.setVisibility(View.GONE);
        alphabetIndex.setVisibility(View.GONE);
        otherPanel.setVisibility(View.GONE);
        libraryList.setVisibility(View.GONE);
        emptyState.setVisibility(View.GONE);
        randomPlayButton.setVisibility(View.GONE);
        scanningState.setVisibility(View.VISIBLE);
        progress.setIndeterminate(true);
        progress.setProgress(0);
        scanProgressText.setText("Musikdateien werden gesucht …");
        titleText.setText("Musik wird eingelesen …");
        refreshInsets();
    }

    private void showEmptyLibraryState() {
        scanningState.setVisibility(View.GONE);
        randomPlayButton.setVisibility(View.GONE);
        searchRow.setVisibility(View.GONE);
        alphabetIndex.setVisibility(View.GONE);
        otherPanel.setVisibility(View.GONE);
        emptyState.setVisibility(View.VISIBLE);
        libraryList.setVisibility(View.GONE);
        ((TextView) findViewById(R.id.emptyTitle)).setText("Keine Musik gefunden");
        ((TextView) findViewById(R.id.emptyMessage)).setText("Im gewählten Ordner wurden keine MP3- oder FLAC-Dateien gefunden.");
        titleText.setText("Musikplayer");
        refreshInsets();
    }

    @Override
    protected void onDestroy() {
        MainActivity active = activeInstance.get();
        if (active == this) activeInstance.clear();
        progressHandler.removeCallbacks(progressUpdater);
        releasePlayer();
        mainHandler.removeCallbacks(delayedSearch);
        if (notificationManager != null) notificationManager.cancel(MEDIA_NOTIFICATION_ID);
        if (mediaSession != null) {
            mediaSession.setActive(false);
            mediaSession.release();
        }
        scanExecutor.shutdownNow();
        historyExecutor.shutdown();
        try {
            if (!historyExecutor.awaitTermination(600L, TimeUnit.MILLISECONDS)) {
                historyExecutor.shutdownNow();
            }
        } catch (InterruptedException ex) {
            historyExecutor.shutdownNow();
            Thread.currentThread().interrupt();
        }
        HashMap<String, Integer> finalCounts = new HashMap<>(playCounts);
        PlayHistory.save(this, finalCounts);
        if (currentTreeUri != null) {
            PlayHistory.saveToMusicFolder(getContentResolver(), currentTreeUri, finalCounts);
        }
        super.onDestroy();
    }

    private static void sortSongsByTitle(List<Song> songs) {
        songs.sort((a, b) -> {
            int result = a.title.compareToIgnoreCase(b.title);
            if (result != 0) return result;
            return a.artist.compareToIgnoreCase(b.artist);
        });
    }

    private static void sortAlbumTracks(List<Song> songs) {
        songs.sort((a, b) -> {
            int result = Integer.compare(normalizedTrack(a.trackNumber), normalizedTrack(b.trackNumber));
            if (result != 0) return result;
            return a.title.compareToIgnoreCase(b.title);
        });
    }

    private static int normalizedTrack(int track) {
        return track <= 0 ? Integer.MAX_VALUE : track;
    }

    private static int parseTrackNumber(String raw) {
        if (TextUtils.isEmpty(raw)) return 0;
        String first = raw.split("/", 2)[0].trim();
        StringBuilder digits = new StringBuilder();
        for (int i = 0; i < first.length(); i++) {
            char c = first.charAt(i);
            if (Character.isDigit(c)) digits.append(c);
            else if (digits.length() > 0) break;
        }
        if (digits.length() == 0) return 0;
        try { return Integer.parseInt(digits.toString()); }
        catch (NumberFormatException ignored) { return 0; }
    }

    private static long parseLong(String value) {
        if (TextUtils.isEmpty(value)) return 0L;
        try { return Long.parseLong(value); }
        catch (NumberFormatException ignored) { return 0L; }
    }

    private static String stripExtension(String value) {
        if (value == null) return "Unbekannter Titel";
        int dot = value.lastIndexOf('.');
        return dot > 0 ? value.substring(0, dot) : value;
    }

    private static String valueOr(String value, String fallback) {
        return TextUtils.isEmpty(value) ? fallback : value.trim();
    }

    private static String formatDuration(long ms) {
        long seconds = Math.max(0L, ms / 1000L);
        return String.format(Locale.getDefault(), "%d:%02d", seconds / 60L, seconds % 60L);
    }

    private static int calculateSample(int width, int height, int max) {
        int sample = 1;
        while (width / sample > max * 2 || height / sample > max * 2) sample *= 2;
        return sample;
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }

    private final class LibraryAdapter extends BaseAdapter {
        private static final int VIEW_NORMAL = 0;
        private static final int VIEW_HEADER = 1;

        @Override public int getCount() {
            if (!TextUtils.isEmpty(searchQuery) && !groupOpen) return searchRows.size();
            return visibleGroups.isEmpty() ? visibleSongs.size() : visibleGroups.size();
        }
        @Override public Object getItem(int position) {
            if (!TextUtils.isEmpty(searchQuery) && !groupOpen) return searchRows.get(position);
            return visibleGroups.isEmpty() ? visibleSongs.get(position) : visibleGroups.get(position);
        }
        @Override public long getItemId(int position) { return position; }
        @Override public int getViewTypeCount() { return 2; }
        @Override public int getItemViewType(int position) {
            if (!TextUtils.isEmpty(searchQuery) && !groupOpen
                    && searchRows.get(position).type == SearchResultRow.TYPE_HEADER) return VIEW_HEADER;
            return VIEW_NORMAL;
        }
        @Override public boolean areAllItemsEnabled() { return false; }
        @Override public boolean isEnabled(int position) { return getItemViewType(position) != VIEW_HEADER; }

        @Override
        public View getView(int position, View convertView, ViewGroup parent) {
            if (getItemViewType(position) == VIEW_HEADER) {
                TextView header;
                if (convertView instanceof TextView) {
                    header = (TextView) convertView;
                } else {
                    header = new TextView(MainActivity.this);
                    header.setGravity(Gravity.CENTER_VERTICAL);
                    header.setPadding(dp(18), dp(12), dp(12), dp(7));
                    header.setTextColor(getColor(R.color.accent));
                    header.setTextSize(12f);
                    header.setTypeface(android.graphics.Typeface.DEFAULT, android.graphics.Typeface.BOLD);
                    header.setBackgroundColor(getColor(R.color.bg));
                }
                header.setText(searchRows.get(position).label);
                return header;
            }

            RowHolder holder;
            if (convertView == null || !(convertView.getTag() instanceof RowHolder)) {
                LinearLayout row = new LinearLayout(MainActivity.this);
                row.setOrientation(LinearLayout.HORIZONTAL);
                row.setGravity(Gravity.CENTER_VERTICAL);
                row.setPadding(dp(16), dp(10), dp(12), dp(10));
                row.setMinimumHeight(dp(68));

                TextView icon = new TextView(MainActivity.this);
                icon.setGravity(Gravity.CENTER);
                icon.setTextColor(getColor(R.color.accent));
                icon.setTextSize(25f);
                row.addView(icon, new LinearLayout.LayoutParams(dp(44), dp(44)));

                LinearLayout texts = new LinearLayout(MainActivity.this);
                texts.setOrientation(LinearLayout.VERTICAL);
                texts.setGravity(Gravity.CENTER_VERTICAL);
                LinearLayout.LayoutParams textParams = new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f);
                textParams.setMarginStart(dp(10));
                row.addView(texts, textParams);

                TextView primary = new TextView(MainActivity.this);
                primary.setTextColor(getColor(R.color.text_primary));
                primary.setTextSize(16f);
                primary.setSingleLine(true);
                primary.setEllipsize(TextUtils.TruncateAt.END);
                texts.addView(primary, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

                TextView secondary = new TextView(MainActivity.this);
                secondary.setTextColor(getColor(R.color.text_secondary));
                secondary.setTextSize(13f);
                secondary.setMaxLines(2);
                secondary.setEllipsize(TextUtils.TruncateAt.END);
                texts.addView(secondary, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

                TextView trailing = new TextView(MainActivity.this);
                trailing.setGravity(Gravity.END | Gravity.CENTER_VERTICAL);
                trailing.setTextColor(getColor(R.color.text_secondary));
                trailing.setTextSize(12f);
                row.addView(trailing, new LinearLayout.LayoutParams(dp(58), ViewGroup.LayoutParams.MATCH_PARENT));

                holder = new RowHolder(icon, primary, secondary, trailing);
                row.setTag(holder);
                convertView = row;
            } else {
                holder = (RowHolder) convertView.getTag();
            }

            if (!TextUtils.isEmpty(searchQuery) && !groupOpen) {
                SearchResultRow result = searchRows.get(position);
                if (result.type == SearchResultRow.TYPE_SONG) {
                    Song song = result.song;
                    holder.icon.setText("♫");
                    holder.primary.setText(song.title);
                    holder.secondary.setText(song.artist + "  •  " + song.album);
                    holder.trailing.setText(formatDuration(song.durationMs));
                } else {
                    GroupRow group = result.group;
                    holder.icon.setText(result.type == SearchResultRow.TYPE_ALBUM ? "▣" : "♬");
                    holder.primary.setText(result.label);
                    if (group == null || group.songs.isEmpty()) {
                        holder.secondary.setText("");
                        holder.trailing.setText("");
                    } else if (result.type == SearchResultRow.TYPE_ARTIST) {
                        Song first = group.songs.get(0);
                        holder.secondary.setText(first.album + "  •  " + first.title);
                        holder.trailing.setText(group.songs.size() + " Titel");
                    } else {
                        holder.secondary.setText(group.subtitle());
                        holder.trailing.setText(group.songs.size() + " Titel");
                    }
                }
                return convertView;
            }

            if (visibleGroups.isEmpty()) {
                Song song = visibleSongs.get(position);
                holder.icon.setText("♫");
                String prefix = groupOpen && groupUsesTrackNumbers && song.trackNumber > 0
                        ? String.format(Locale.getDefault(), "%02d · ", song.trackNumber) : "";
                holder.primary.setText(prefix + song.title);
                holder.secondary.setText(song.artist + "  •  " + song.album);
                holder.trailing.setText(showPlayCounts
                        ? getPlayCount(song) + "×"
                        : formatDuration(song.durationMs));
            } else {
                GroupRow group = visibleGroups.get(position);
                holder.icon.setText(group.playlistGroup ? "≡" : (group.albumGroup ? "▣" : "▤"));
                holder.primary.setText(group.name);
                holder.secondary.setText(group.subtitle());
                holder.trailing.setText(group.playlistGroup
                        ? group.songs.size() + "/" + group.playlistTotalEntries
                        : group.songs.size() + " Titel");
            }
            return convertView;
        }
    }

    private static final class PendingAudio {
        final Uri uri;
        final String fileName;
        final String relativePath;
        final long lastModifiedMs;
        final long sizeBytes;

        PendingAudio(Uri uri, String fileName, String relativePath,
                     long lastModifiedMs, long sizeBytes) {
            this.uri = uri;
            this.fileName = fileName;
            this.relativePath = relativePath;
            this.lastModifiedMs = lastModifiedMs;
            this.sizeBytes = sizeBytes;
        }
    }

    private static final class PendingPlaylist {
        final Uri uri;
        final String fileName;
        final String relativePath;

        PendingPlaylist(Uri uri, String fileName, String relativePath) {
            this.uri = uri;
            this.fileName = fileName;
            this.relativePath = relativePath;
        }
    }

    private static final class ImportedPlaylist {
        String name;
        final String sourceRelativePath;
        final ArrayList<Song> songs;
        final int totalEntries;
        final int missingEntries;

        ImportedPlaylist(String name, String sourceRelativePath, ArrayList<Song> songs,
                         int totalEntries, int missingEntries) {
            this.name = name;
            this.sourceRelativePath = sourceRelativePath;
            this.songs = songs;
            this.totalEntries = totalEntries;
            this.missingEntries = missingEntries;
        }
    }

    private static final class PlaylistImportBatch {
        final ArrayList<ImportedPlaylist> playlists;
        final int readErrors;

        PlaylistImportBatch(ArrayList<ImportedPlaylist> playlists, int readErrors) {
            this.playlists = playlists;
            this.readErrors = readErrors;
        }
    }

    private static final class MetadataTask {
        final PendingAudio audio;
        final Song previous;

        MetadataTask(PendingAudio audio, Song previous) {
            this.audio = audio;
            this.previous = previous;
        }
    }

    private static final class RowHolder {
        final TextView icon;
        final TextView primary;
        final TextView secondary;
        final TextView trailing;
        RowHolder(TextView icon, TextView primary, TextView secondary, TextView trailing) {
            this.icon = icon;
            this.primary = primary;
            this.secondary = secondary;
            this.trailing = trailing;
        }
    }

    private static final class SearchResultRow {
        static final int TYPE_HEADER = 0;
        static final int TYPE_ALBUM = 1;
        static final int TYPE_SONG = 2;
        static final int TYPE_ARTIST = 3;

        final int type;
        final String label;
        final Song song;
        final GroupRow group;

        private SearchResultRow(int type, String label, Song song, GroupRow group) {
            this.type = type;
            this.label = label;
            this.song = song;
            this.group = group;
        }

        static SearchResultRow header(String label) {
            return new SearchResultRow(TYPE_HEADER, label, null, null);
        }

        static SearchResultRow album(String name, ArrayList<Song> songs) {
            return new SearchResultRow(TYPE_ALBUM, name, null, new GroupRow(name, songs, true));
        }

        static SearchResultRow song(Song song) {
            return new SearchResultRow(TYPE_SONG, song.title, song, null);
        }

        static SearchResultRow artist(String name, ArrayList<Song> songs) {
            return new SearchResultRow(TYPE_ARTIST, name, null, new GroupRow(name, songs, false));
        }
    }

    private static final class GroupRow {
        final String name;
        final ArrayList<Song> songs;
        final boolean albumGroup;
        final boolean playlistGroup;
        final int playlistTotalEntries;
        final int playlistMissingEntries;

        GroupRow(String name, ArrayList<Song> songs, boolean albumGroup) {
            this(name, songs, albumGroup, false, songs.size(), 0);
        }

        private GroupRow(String name, ArrayList<Song> songs, boolean albumGroup,
                         boolean playlistGroup, int playlistTotalEntries,
                         int playlistMissingEntries) {
            this.name = name;
            this.songs = songs;
            this.albumGroup = albumGroup;
            this.playlistGroup = playlistGroup;
            this.playlistTotalEntries = playlistTotalEntries;
            this.playlistMissingEntries = playlistMissingEntries;
        }

        static GroupRow playlist(ImportedPlaylist playlist) {
            return new GroupRow(playlist.name, playlist.songs, false, true,
                    playlist.totalEntries, playlist.missingEntries);
        }

        String subtitle() {
            if (playlistGroup) {
                if (playlistTotalEntries == 0) return "Leere Playlist";
                String status = songs.size() + " von " + playlistTotalEntries + " Titeln gefunden";
                if (songs.isEmpty()) return status;
                Song first = songs.get(0);
                return status + "  •  " + first.artist + " – " + first.title;
            }
            if (songs.isEmpty()) return "";
            if (!albumGroup) {
                Song first = songs.get(0);
                return first.artist + "  •  " + first.title;
            }
            Song first = songs.get(0);
            String preview = first.trackNumber > 0
                    ? String.format(Locale.getDefault(), "%02d · %s", first.trackNumber, first.title)
                    : first.title;
            return first.artist + "  •  " + preview;
        }
    }

    /** Tiny vector-like drawable generated in code so the MVP needs no image assets. */
    private static final class MusicNoteDrawable extends android.graphics.drawable.Drawable {
        private final android.graphics.Paint paint = new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);
        MusicNoteDrawable(int color) {
            paint.setColor(color);
            paint.setStrokeWidth(12f);
            paint.setStrokeCap(android.graphics.Paint.Cap.ROUND);
            paint.setStyle(android.graphics.Paint.Style.STROKE);
        }
        @Override public void draw(android.graphics.Canvas canvas) {
            android.graphics.Rect bounds = getBounds();
            float cx = bounds.exactCenterX();
            float cy = bounds.exactCenterY();
            float scale = Math.min(bounds.width(), bounds.height()) / 200f;
            paint.setStrokeWidth(12f * scale);
            canvas.drawLine(cx + 25f * scale, cy - 60f * scale, cx + 25f * scale, cy + 35f * scale, paint);
            canvas.drawLine(cx + 25f * scale, cy - 60f * scale, cx + 75f * scale, cy - 45f * scale, paint);
            canvas.drawCircle(cx, cy + 45f * scale, 24f * scale, paint);
            canvas.drawCircle(cx + 50f * scale, cy + 60f * scale, 24f * scale, paint);
        }
        @Override public void setAlpha(int alpha) { paint.setAlpha(alpha); }
        @Override public void setColorFilter(android.graphics.ColorFilter colorFilter) { paint.setColorFilter(colorFilter); }
        @Override public int getOpacity() { return android.graphics.PixelFormat.TRANSLUCENT; }
    }
}
