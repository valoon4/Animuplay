package de.minimal.musicplayer;

import android.net.Uri;

final class Song {
    final Uri uri;
    final String fileName;
    final String title;
    final String artist;
    final String album;
    final String genre;
    final String year;
    final int trackNumber;
    final long durationMs;
    final long lastModifiedMs;
    final long sizeBytes;
    final String searchKey;

    Song(Uri uri, String fileName, String title, String artist, String album,
         String genre, String year, int trackNumber, long durationMs,
         long lastModifiedMs, long sizeBytes) {
        this.uri = uri;
        this.fileName = fileName;
        this.title = title;
        this.artist = artist;
        this.album = album;
        this.genre = genre;
        this.year = year;
        this.trackNumber = trackNumber;
        this.durationMs = durationMs;
        this.lastModifiedMs = lastModifiedMs;
        this.sizeBytes = sizeBytes;
        this.searchKey = SearchMatcher.buildKey(title, artist, album);
    }
}
