package de.minimal.musicplayer;

import android.content.ContentResolver;
import android.content.Context;
import android.database.Cursor;
import android.net.Uri;
import android.provider.DocumentsContract;
import android.util.AtomicFile;

import org.json.JSONException;
import org.json.JSONObject;

import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.BufferedReader;
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.text.Normalizer;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;

/** Persistent play counters with an internal mirror and a portable profile in the music folder. */
final class PlayHistory {
    private static final int MAGIC = 0x4D4D5048; // "MMPH"
    private static final int FORMAT_VERSION = 1;
    private static final int PROFILE_VERSION = 1;
    private static final int MAX_ENTRIES = 500_000;
    private static final int MAX_KEY_BYTES = 1024 * 1024;
    private static final int MAX_PROFILE_BYTES = 32 * 1024 * 1024;
    private static final String FILE_NAME = "play-history.bin";
    private static final String PROFILE_DIRECTORY = "MinimalMusicPlayer";
    private static final String PROFILE_FILE = "profile.json";

    private PlayHistory() { }

    static HashMap<String, Integer> load(Context context) {
        HashMap<String, Integer> counts = new HashMap<>();
        AtomicFile atomicFile = file(context);
        if (!atomicFile.getBaseFile().isFile()) return counts;
        try (DataInputStream input = new DataInputStream(
                new BufferedInputStream(atomicFile.openRead(), 32 * 1024))) {
            if (input.readInt() != MAGIC || input.readInt() != FORMAT_VERSION) return counts;
            int size = input.readInt();
            if (size < 0 || size > MAX_ENTRIES) throw new IOException("Invalid play-count size");
            for (int index = 0; index < size; index++) {
                String key = readString(input);
                int count = input.readInt();
                if (!key.isEmpty() && count > 0) counts.put(key, count);
            }
        } catch (IOException | RuntimeException ignored) {
            atomicFile.delete();
            counts.clear();
        }
        return counts;
    }

    static void save(Context context, Map<String, Integer> counts) {
        AtomicFile atomicFile = file(context);
        FileOutputStream raw = null;
        try {
            raw = atomicFile.startWrite();
            DataOutputStream output = new DataOutputStream(
                    new BufferedOutputStream(raw, 32 * 1024));
            output.writeInt(MAGIC);
            output.writeInt(FORMAT_VERSION);
            int valid = validEntryCount(counts);
            output.writeInt(valid);
            for (Map.Entry<String, Integer> entry : counts.entrySet()) {
                if (!isValid(entry)) continue;
                writeString(output, entry.getKey());
                output.writeInt(entry.getValue());
            }
            output.flush();
            atomicFile.finishWrite(raw);
        } catch (IOException | RuntimeException ignored) {
            if (raw != null) atomicFile.failWrite(raw);
        }
    }

    static HashMap<String, Integer> loadFromMusicFolder(ContentResolver resolver, Uri treeUri) {
        HashMap<String, Integer> counts = new HashMap<>();
        if (resolver == null || treeUri == null) return counts;
        try {
            Uri root = rootDocumentUri(treeUri);
            Uri profileDirectory = findChild(resolver, treeUri, root, PROFILE_DIRECTORY,
                    DocumentsContract.Document.MIME_TYPE_DIR);
            if (profileDirectory == null) return counts;
            Uri profile = findChild(resolver, treeUri, profileDirectory, PROFILE_FILE, null);
            if (profile == null) return counts;

            StringBuilder json = new StringBuilder();
            try (InputStream raw = resolver.openInputStream(profile)) {
                if (raw == null) return counts;
                try (BufferedReader reader = new BufferedReader(
                        new InputStreamReader(raw, StandardCharsets.UTF_8), 32 * 1024)) {
                    char[] buffer = new char[8192];
                    int total = 0;
                    int read;
                    while ((read = reader.read(buffer)) >= 0) {
                        total += read;
                        if (total > MAX_PROFILE_BYTES) throw new IOException("Profile too large");
                        json.append(buffer, 0, read);
                    }
                }
            }
            JSONObject rootJson = new JSONObject(json.toString());
            if (rootJson.optInt("version", -1) != PROFILE_VERSION) return counts;
            JSONObject entries = rootJson.optJSONObject("playCounts");
            if (entries == null || entries.length() > MAX_ENTRIES) return counts;
            Iterator<String> keys = entries.keys();
            while (keys.hasNext()) {
                String key = keys.next();
                int count = entries.optInt(key, 0);
                if (!key.isEmpty() && count > 0) counts.put(key, count);
            }
        } catch (IOException | RuntimeException | JSONException ignored) {
            counts.clear();
        }
        return counts;
    }

    static boolean saveToMusicFolder(ContentResolver resolver, Uri treeUri,
                                     Map<String, Integer> counts) {
        if (resolver == null || treeUri == null) return false;
        try {
            Uri root = rootDocumentUri(treeUri);
            Uri profileDirectory = findChild(resolver, treeUri, root, PROFILE_DIRECTORY,
                    DocumentsContract.Document.MIME_TYPE_DIR);
            if (profileDirectory == null) {
                profileDirectory = DocumentsContract.createDocument(resolver, root,
                        DocumentsContract.Document.MIME_TYPE_DIR, PROFILE_DIRECTORY);
            }
            if (profileDirectory == null) return false;

            Uri profile = findChild(resolver, treeUri, profileDirectory, PROFILE_FILE, null);
            if (profile == null) {
                profile = DocumentsContract.createDocument(resolver, profileDirectory,
                        "application/json", PROFILE_FILE);
            }
            if (profile == null) return false;

            JSONObject entries = new JSONObject();
            for (Map.Entry<String, Integer> entry : counts.entrySet()) {
                if (!isValid(entry)) continue;
                entries.put(entry.getKey(), entry.getValue());
            }
            JSONObject rootJson = new JSONObject();
            rootJson.put("version", PROFILE_VERSION);
            rootJson.put("playCounts", entries);
            byte[] bytes = rootJson.toString(2).getBytes(StandardCharsets.UTF_8);
            if (bytes.length > MAX_PROFILE_BYTES) return false;
            try (OutputStream output = resolver.openOutputStream(profile, "wt")) {
                if (output == null) return false;
                output.write(bytes);
                output.flush();
            }
            return true;
        } catch (IOException | RuntimeException | JSONException ignored) {
            return false;
        }
    }

    static String keyForSong(Uri treeUri, Song song) {
        if (song == null || song.uri == null) return "";
        if (treeUri != null) {
            try {
                String rootId = DocumentsContract.getTreeDocumentId(treeUri);
                String documentId = DocumentsContract.getDocumentId(song.uri);
                if (documentId.equals(rootId)) return "path:" + normalizePath(song.fileName);
                String prefix = rootId.endsWith("/") ? rootId : rootId + "/";
                if (documentId.startsWith(prefix)) {
                    return "path:" + normalizePath(documentId.substring(prefix.length()));
                }
            } catch (IllegalArgumentException | SecurityException ignored) {
                // Fall back to the document URI below.
            }
        }
        return "uri:" + song.uri;
    }

    private static Uri rootDocumentUri(Uri treeUri) {
        return DocumentsContract.buildDocumentUriUsingTree(treeUri,
                DocumentsContract.getTreeDocumentId(treeUri));
    }

    private static Uri findChild(ContentResolver resolver, Uri treeUri, Uri parent,
                                 String displayName, String requiredMimeType) {
        String parentDocumentId = DocumentsContract.getDocumentId(parent);
        Uri children = DocumentsContract.buildChildDocumentsUriUsingTree(treeUri, parentDocumentId);
        String[] projection = {
                DocumentsContract.Document.COLUMN_DOCUMENT_ID,
                DocumentsContract.Document.COLUMN_DISPLAY_NAME,
                DocumentsContract.Document.COLUMN_MIME_TYPE
        };
        try (Cursor cursor = resolver.query(children, projection, null, null, null)) {
            if (cursor == null) return null;
            int idColumn = cursor.getColumnIndexOrThrow(DocumentsContract.Document.COLUMN_DOCUMENT_ID);
            int nameColumn = cursor.getColumnIndexOrThrow(DocumentsContract.Document.COLUMN_DISPLAY_NAME);
            int mimeColumn = cursor.getColumnIndexOrThrow(DocumentsContract.Document.COLUMN_MIME_TYPE);
            while (cursor.moveToNext()) {
                String name = cursor.getString(nameColumn);
                String mime = cursor.getString(mimeColumn);
                if (!displayName.equals(name)) continue;
                if (requiredMimeType != null && !requiredMimeType.equals(mime)) continue;
                return DocumentsContract.buildDocumentUriUsingTree(treeUri, cursor.getString(idColumn));
            }
        } catch (RuntimeException ignored) {
            return null;
        }
        return null;
    }

    private static String normalizePath(String value) {
        String path = value == null ? "" : value.replace('\\', '/');
        while (path.startsWith("/")) path = path.substring(1);
        while (path.contains("//")) path = path.replace("//", "/");
        return Normalizer.normalize(path, Normalizer.Form.NFC);
    }

    private static int validEntryCount(Map<String, Integer> counts) {
        int valid = 0;
        for (Map.Entry<String, Integer> entry : counts.entrySet()) {
            if (isValid(entry)) valid++;
        }
        return valid;
    }

    private static boolean isValid(Map.Entry<String, Integer> entry) {
        return entry.getKey() != null && !entry.getKey().isEmpty()
                && entry.getValue() != null && entry.getValue() > 0;
    }

    private static AtomicFile file(Context context) {
        return new AtomicFile(new File(context.getFilesDir(), FILE_NAME));
    }

    private static void writeString(DataOutputStream output, String value) throws IOException {
        byte[] bytes = value.getBytes(StandardCharsets.UTF_8);
        output.writeInt(bytes.length);
        output.write(bytes);
    }

    private static String readString(DataInputStream input) throws IOException {
        int length = input.readInt();
        if (length < 0 || length > MAX_KEY_BYTES) throw new IOException("Invalid key length");
        byte[] bytes = new byte[length];
        input.readFully(bytes);
        return new String(bytes, StandardCharsets.UTF_8);
    }
}
