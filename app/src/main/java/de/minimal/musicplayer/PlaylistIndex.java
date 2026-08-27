package de.minimal.musicplayer;

import android.content.Context;
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

/** Persistent imported-playlist snapshot so normal app launches need no folder walk. */
final class PlaylistIndex {
    private static final int MAGIC = 0x4D4D5050; // MMPP
    private static final int VERSION = 1;
    private static final int MAX_PLAYLISTS = 50_000;
    private static final int MAX_URIS = 1_000_000;
    private static final int MAX_STRING_BYTES = 1024 * 1024;
    private static final String FILE_NAME = "playlist-index.bin";

    private PlaylistIndex() { }

    static final class Entry {
        final String name;
        final String sourceRelativePath;
        final ArrayList<String> songUris;
        final int totalEntries;
        final int missingEntries;

        Entry(String name, String sourceRelativePath, ArrayList<String> songUris,
              int totalEntries, int missingEntries) {
            this.name = name;
            this.sourceRelativePath = sourceRelativePath;
            this.songUris = songUris;
            this.totalEntries = totalEntries;
            this.missingEntries = missingEntries;
        }
    }

    static final class Snapshot {
        final boolean valid;
        final ArrayList<Entry> entries;

        Snapshot(boolean valid, ArrayList<Entry> entries) {
            this.valid = valid;
            this.entries = entries;
        }
    }

    static Snapshot load(Context context, String expectedTreeUri) {
        ArrayList<Entry> entries = new ArrayList<>();
        AtomicFile file = file(context);
        if (!file.getBaseFile().isFile()) return new Snapshot(false, entries);
        try (DataInputStream input = new DataInputStream(
                new BufferedInputStream(file.openRead(), 32 * 1024))) {
            if (input.readInt() != MAGIC || input.readInt() != VERSION) {
                return new Snapshot(false, entries);
            }
            if (!expectedTreeUri.equals(readString(input))) return new Snapshot(false, entries);
            int count = input.readInt();
            if (count < 0 || count > MAX_PLAYLISTS) throw new IOException("Invalid playlist count");
            for (int i = 0; i < count; i++) {
                String name = readString(input);
                String path = readString(input);
                int total = input.readInt();
                int missing = input.readInt();
                int uriCount = input.readInt();
                if (uriCount < 0 || uriCount > MAX_URIS) throw new IOException("Invalid URI count");
                ArrayList<String> uris = new ArrayList<>(uriCount);
                for (int u = 0; u < uriCount; u++) uris.add(readString(input));
                entries.add(new Entry(name, path, uris, total, missing));
            }
            return new Snapshot(true, entries);
        } catch (IOException | RuntimeException ignored) {
            file.delete();
            return new Snapshot(false, new ArrayList<>());
        }
    }

    static void save(Context context, String treeUri, List<Entry> entries) {
        AtomicFile file = file(context);
        FileOutputStream raw = null;
        try {
            raw = file.startWrite();
            DataOutputStream output = new DataOutputStream(new BufferedOutputStream(raw, 32 * 1024));
            output.writeInt(MAGIC);
            output.writeInt(VERSION);
            writeString(output, treeUri);
            output.writeInt(entries.size());
            for (Entry entry : entries) {
                writeString(output, entry.name);
                writeString(output, entry.sourceRelativePath);
                output.writeInt(entry.totalEntries);
                output.writeInt(entry.missingEntries);
                output.writeInt(entry.songUris.size());
                for (String uri : entry.songUris) writeString(output, uri);
            }
            output.flush();
            file.finishWrite(raw);
        } catch (IOException | RuntimeException ignored) {
            if (raw != null) file.failWrite(raw);
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
            throw new IOException("Truncated playlist index", ex);
        }
        if (length < 0 || length > MAX_STRING_BYTES) throw new IOException("Invalid string length");
        byte[] bytes = new byte[length];
        input.readFully(bytes);
        return new String(bytes, StandardCharsets.UTF_8);
    }
}
