package de.minimal.musicplayer;

import android.content.ContentResolver;
import android.net.Uri;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.ByteBuffer;
import java.nio.charset.CharacterCodingException;
import java.nio.charset.Charset;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.net.URI;
import java.net.URISyntaxException;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.Locale;
import java.util.Map;

/** Reads M3U/M3U8 files and maps desktop paths to paths below the selected Android folder. */
final class M3uPlaylistReader {
    private static final int MAX_PLAYLIST_BYTES = 32 * 1024 * 1024;

    private M3uPlaylistReader() { }

    static ArrayList<String> readEntries(ContentResolver resolver, Uri uri, String fileName)
            throws IOException {
        byte[] bytes;
        try (InputStream input = resolver.openInputStream(uri)) {
            if (input == null) throw new IOException("Playlist konnte nicht geöffnet werden");
            ByteArrayOutputStream output = new ByteArrayOutputStream(16 * 1024);
            byte[] buffer = new byte[16 * 1024];
            int total = 0;
            int read;
            while ((read = input.read(buffer)) != -1) {
                total += read;
                if (total > MAX_PLAYLIST_BYTES) throw new IOException("Playlist ist zu groß");
                output.write(buffer, 0, read);
            }
            bytes = output.toByteArray();
        }

        String text = decodeText(bytes, fileName);
        ArrayList<String> entries = new ArrayList<>();
        String[] lines = text.split("\\r?\\n|\\r", -1);
        for (String rawLine : lines) {
            String line = rawLine.trim();
            if (line.isEmpty() || line.startsWith("#")) continue;
            if (line.length() >= 2 && line.startsWith("\"") && line.endsWith("\"")) {
                line = line.substring(1, line.length() - 1);
            }
            String normalized = normalizeReference(line);
            if (!normalized.isEmpty()) entries.add(normalized);
        }
        return entries;
    }

    /**
     * Finds a song URI by trying the complete path and then successively shorter suffixes.
     * Example: F:/Musik/2025/a.flac -> Musik/2025/a.flac -> 2025/a.flac.
     */
    static String matchSongUri(String normalizedReference,
                               Map<String, String> uriByRelativePath,
                               Map<String, String> uniqueUriByFileName) {
        String candidate = normalizePath(normalizedReference);
        while (!candidate.isEmpty()) {
            String match = uriByRelativePath.get(key(candidate));
            if (match != null) return match;
            int slash = candidate.indexOf('/');
            if (slash < 0) break;
            candidate = candidate.substring(slash + 1);
        }

        String fileName = fileName(normalizedReference);
        return fileName.isEmpty() ? null : uniqueUriByFileName.get(key(fileName));
    }

    static String normalizeRelativePath(String path) {
        return normalizePath(path);
    }

    static String fileName(String path) {
        String normalized = normalizePath(path);
        int slash = normalized.lastIndexOf('/');
        return slash < 0 ? normalized : normalized.substring(slash + 1);
    }

    static String key(String value) {
        return normalizePath(value).toLowerCase(Locale.ROOT);
    }

    private static String decodeText(byte[] bytes, String fileName) {
        int offset = 0;
        Charset charset = StandardCharsets.UTF_8;
        if (bytes.length >= 3 && (bytes[0] & 0xff) == 0xef
                && (bytes[1] & 0xff) == 0xbb && (bytes[2] & 0xff) == 0xbf) {
            offset = 3;
        } else if (bytes.length >= 2 && (bytes[0] & 0xff) == 0xff && (bytes[1] & 0xff) == 0xfe) {
            offset = 2;
            charset = StandardCharsets.UTF_16LE;
        } else if (bytes.length >= 2 && (bytes[0] & 0xff) == 0xfe && (bytes[1] & 0xff) == 0xff) {
            offset = 2;
            charset = StandardCharsets.UTF_16BE;
        }

        try {
            return charset.newDecoder()
                    .onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT)
                    .decode(ByteBuffer.wrap(bytes, offset, bytes.length - offset))
                    .toString();
        } catch (CharacterCodingException ignored) {
            // Legacy .m3u files are often Windows-1252. M3U8 remains UTF-8 by convention.
            String lower = fileName == null ? "" : fileName.toLowerCase(Locale.ROOT);
            Charset fallback = lower.endsWith(".m3u8")
                    ? StandardCharsets.UTF_8 : Charset.forName("windows-1252");
            return new String(bytes, offset, bytes.length - offset, fallback);
        }
    }

    static String normalizeReference(String raw) {
        String value = raw == null ? "" : raw.trim();
        if (value.regionMatches(true, 0, "file:", 0, 5)) {
            try {
                URI uri = new URI(value);
                String encodedPath = uri.getRawPath();
                value = encodedPath == null ? value.substring(5) : percentDecode(encodedPath);
                String authority = uri.getRawAuthority();
                if (authority != null && !authority.isEmpty()
                        && !"localhost".equalsIgnoreCase(authority)) {
                    value = percentDecode(authority) + "/" + value;
                }
            } catch (URISyntaxException | IllegalArgumentException ignored) {
                value = percentDecode(value.substring(5));
            }
        } else {
            // Decode all %HH URI escapes as UTF-8, but preserve a literal '+' exactly.
            value = percentDecode(value);
        }
        return normalizePath(value);
    }

    private static String percentDecode(String value) {
        StringBuilder result = new StringBuilder(value.length());
        ByteArrayOutputStream encodedBytes = new ByteArrayOutputStream();
        int index = 0;
        while (index < value.length()) {
            char current = value.charAt(index);
            if (current == '%' && index + 2 < value.length()) {
                encodedBytes.reset();
                int cursor = index;
                while (cursor + 2 < value.length() && value.charAt(cursor) == '%') {
                    int high = Character.digit(value.charAt(cursor + 1), 16);
                    int low = Character.digit(value.charAt(cursor + 2), 16);
                    if (high < 0 || low < 0) break;
                    encodedBytes.write((high << 4) | low);
                    cursor += 3;
                }
                if (encodedBytes.size() > 0) {
                    result.append(new String(encodedBytes.toByteArray(), StandardCharsets.UTF_8));
                    index = cursor;
                    continue;
                }
            }
            result.append(current);
            index++;
        }
        return result.toString();
    }

    private static String normalizePath(String raw) {
        if (raw == null) return "";
        String value = raw.replace('\\', '/').trim();
        while (value.startsWith("//")) value = value.substring(1);
        if (value.length() >= 4 && value.charAt(0) == '/'
                && Character.isLetter(value.charAt(1)) && value.charAt(2) == ':'
                && value.charAt(3) == '/') {
            value = value.substring(1);
        }
        while (value.startsWith("/")) value = value.substring(1);

        String[] parts = value.split("/+", -1);
        Deque<String> clean = new ArrayDeque<>();
        for (String part : parts) {
            if (part.isEmpty() || ".".equals(part)) continue;
            if ("..".equals(part)) {
                if (!clean.isEmpty()) clean.removeLast();
            } else {
                clean.addLast(part);
            }
        }
        StringBuilder result = new StringBuilder();
        for (String part : clean) {
            if (result.length() > 0) result.append('/');
            result.append(part);
        }
        return result.toString();
    }
}
