package de.minimal.musicplayer;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

/** Receives media-notification actions without opening or focusing the Activity UI. */
public final class PlaybackActionReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context context, Intent intent) {
        if (intent != null) MainActivity.handleExternalPlaybackAction(intent.getAction());
    }
}
