package de.minimal.musicplayer;

import android.content.Context;
import android.net.Uri;
import android.util.AtomicFile;

import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.EOFException;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;

/** Persistent metadata index so unchanged files do not need to be parsed again. */
final class LibraryIndex {
    private static final int MAGIC = 0x4D4D5031; // "MMP1"
    private static final int FORMAT_VERSION = 2;
    private static final int MAX_SONGS = 500_000;
    private static final int MAX_STRING_BYTES = 1024 * 1024;
    private static final String FILE_NAME = "music-library-index.bin";

    private LibraryIndex() { }

    static ArrayList<Song> load(Context context, String expectedTreeUri) {
        ArrayList<Song> songs = new ArrayList<>();
        AtomicFile atomicFile = file(context);
        if (!atomicFile.getBaseFile().isFile()) return songs;

        try (DataInputStream input = new DataInputStream(
                new BufferedInputStream(atomicFile.openRead(), 64 * 1024))) {
            if (input.readInt() != MAGIC) return songs;
            int formatVersion = input.readInt();
            if (formatVersion < 1 || formatVersion > FORMAT_VERSION) return songs;
            String storedTreeUri = readString(input);
            if (!expectedTreeUri.equals(storedTreeUri)) return songs;

            int count = input.readInt();
            if (count < 0 || count > MAX_SONGS) throw new IOException("Invalid song count");
            songs.ensureCapacity(count);
            for (int index = 0; index < count; index++) {
                Uri uri = Uri.parse(readString(input));
                String fileName = readString(input);
                String title = readString(input);
                String artist = readString(input);
                String album = readString(input);
                String genre = readString(input);
                // v0.11 used index format 1 and did not persist the Year tag. An
                // empty value marks that entry for one-time background enrichment.
                String year = formatVersion >= 2 ? readString(input) : "";
                int trackNumber = input.readInt();
                long durationMs = input.readLong();
                long lastModifiedMs = input.readLong();
                long sizeBytes = input.readLong();
                songs.add(new Song(uri, fileName, title, artist, album, genre, year,
                        trackNumber, durationMs, lastModifiedMs, sizeBytes));
            }
            return songs;
        } catch (IOException | RuntimeException ignored) {
            // A corrupt or obsolete index must never prevent the app from scanning.
            atomicFile.delete();
            songs.clear();
            return songs;
        }
    }

    static void save(Context context, String treeUri, List<Song> songs) {
        AtomicFile atomicFile = file(context);
        FileOutputStream rawOutput = null;
        try {
            rawOutput = atomicFile.startWrite();
            DataOutputStream output = new DataOutputStream(
                    new BufferedOutputStream(rawOutput, 64 * 1024));
            output.writeInt(MAGIC);
            output.writeInt(FORMAT_VERSION);
            writeString(output, treeUri);
            output.writeInt(songs.size());
            for (Song song : songs) {
                writeString(output, song.uri.toString());
                writeString(output, song.fileName);
                writeString(output, song.title);
                writeString(output, song.artist);
                writeString(output, song.album);
                writeString(output, song.genre);
                writeString(output, song.year);
                output.writeInt(song.trackNumber);
                output.writeLong(song.durationMs);
                output.writeLong(song.lastModifiedMs);
                output.writeLong(song.sizeBytes);
            }
            output.flush();
            atomicFile.finishWrite(rawOutput);
        } catch (IOException | RuntimeException ignored) {
            if (rawOutput != null) atomicFile.failWrite(rawOutput);
        }
    }

    private static AtomicFile file(Context context) {
        return new AtomicFile(new File(context.getFilesDir(), FILE_NAME));
    }

    private static void writeString(DataOutputStream output, String value) throws IOException {
        byte[] bytes = (value == null ? "" : value).getBytes(StandardCharsets.UTF_8);
        output.writeInt(bytes.length);
        output.write(bytes);
    }

    private static String readString(DataInputStream input) throws IOException {
        int length;
        try {
            length = input.readInt();
        } catch (EOFException ex) {
            throw new IOException("Truncated index", ex);
        }
        if (length < 0 || length > MAX_STRING_BYTES) throw new IOException("Invalid string length");
        byte[] bytes = new byte[length];
        input.readFully(bytes);
        return new String(bytes, StandardCharsets.UTF_8);
    }
}
