package de.minimal.musicplayer;

import android.content.ContentResolver;
import android.net.Uri;

import java.io.BufferedInputStream;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.PushbackInputStream;
import java.nio.charset.Charset;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Locale;

/**
 * Reads the raw genre field instead of relying only on MediaMetadataRetriever.
 * Android's metadata layer may treat a TCON value that starts with digits as a
 * legacy numeric genre code. This reader deliberately decodes the actual text
 * stored in MP3 ID3v2 and FLAC Vorbis-comment metadata without interpreting it.
 */
final class GenreTagReader {
    private static final int MAX_ID3_TAG_BYTES = 32 * 1024 * 1024;
    private static final int MAX_FLAC_BLOCK_BYTES = 32 * 1024 * 1024;
    private static final int MAX_FLAC_BLOCKS = 256;

    private GenreTagReader() { }

    static String readGenre(ContentResolver resolver, Uri uri, String fileName) {
        if (resolver == null || uri == null) return null;
        String lower = fileName == null ? "" : fileName.toLowerCase(Locale.ROOT);
        try (InputStream raw = resolver.openInputStream(uri)) {
            if (raw == null) return null;
            BufferedInputStream input = new BufferedInputStream(raw, 64 * 1024);
            if (lower.endsWith(".flac")) return readFlacGenre(input);
            if (lower.endsWith(".mp3")) return readId3v2Genre(input);

            input.mark(16);
            byte[] magic = new byte[4];
            int read = readUpTo(input, magic, 0, magic.length);
            input.reset();
            if (read >= 3 && magic[0] == 'I' && magic[1] == 'D' && magic[2] == '3') {
                return readId3v2Genre(input);
            }
            if (read == 4 && magic[0] == 'f' && magic[1] == 'L'
                    && magic[2] == 'a' && magic[3] == 'C') {
                return readFlacGenre(input);
            }
        } catch (IOException | RuntimeException ignored) {
            // MediaMetadataRetriever remains the fallback.
        }
        return null;
    }

    static String readId3v2Genre(InputStream input) throws IOException {
        byte[] header = new byte[10];
        if (!readFully(input, header, 0, header.length)) return null;
        if (header[0] != 'I' || header[1] != 'D' || header[2] != '3') return null;

        int majorVersion = header[3] & 0xFF;
        if (majorVersion < 2 || majorVersion > 4) return null;
        int flags = header[5] & 0xFF;
        int tagSize = synchsafeInt(header, 6);
        if (tagSize <= 0 || tagSize > MAX_ID3_TAG_BYTES) return null;

        byte[] body = new byte[tagSize];
        if (!readFully(input, body, 0, body.length)) return null;
        return parseId3Body(majorVersion, flags, body);
    }

    static String parseId3v2Genre(byte[] completeTag) {
        if (completeTag == null || completeTag.length < 10) return null;
        try {
            return readId3v2Genre(new ByteArrayInputStream(completeTag));
        } catch (IOException impossible) {
            return null;
        }
    }

    private static String parseId3Body(int version, int tagFlags, byte[] body) {
        int offset = skipExtendedHeader(version, tagFlags, body);
        String parsed = parseFrames(version, tagFlags, body, offset);
        if (parsed != null) return parsed;
        return scanForGenreFrame(version, tagFlags, body);
    }

    private static int skipExtendedHeader(int version, int flags, byte[] body) {
        if ((flags & 0x40) == 0) return 0;
        if (body.length < 4) return body.length;
        if (version == 3) {
            long size = unsignedIntBigEndian(body, 0);
            long offset = 4L + size;
            return offset <= body.length ? (int) offset : body.length;
        }
        if (version == 4) {
            int size = synchsafeInt(body, 0);
            return size >= 4 && size <= body.length ? size : body.length;
        }
        return 0;
    }

    private static String parseFrames(int version, int tagFlags, byte[] body, int start) {
        int position = Math.max(0, start);
        if (version == 2) {
            while (position + 6 <= body.length) {
                if (allZero(body, position, 3)) break;
                if (!validFrameId(body, position, 3)) break;
                String id = ascii(body, position, 3);
                int size = ((body[position + 3] & 0xFF) << 16)
                        | ((body[position + 4] & 0xFF) << 8)
                        | (body[position + 5] & 0xFF);
                int dataStart = position + 6;
                if (size < 0 || dataStart + size > body.length) break;
                if ("TCO".equals(id)) {
                    byte[] payload = Arrays.copyOfRange(body, dataStart, dataStart + size);
                    if ((tagFlags & 0x80) != 0) payload = removeUnsynchronisation(payload);
                    return decodeTextFrame(payload);
                }
                position = dataStart + size;
            }
            return null;
        }

        while (position + 10 <= body.length) {
            if (allZero(body, position, 4)) break;
            if (!validFrameId(body, position, 4)) break;
            String id = ascii(body, position, 4);
            int size = version == 4
                    ? synchsafeInt(body, position + 4)
                    : signedIntBigEndian(body, position + 4);
            int dataStart = position + 10;
            if (size < 0 || dataStart + size > body.length) break;
            if ("TCON".equals(id)) {
                byte[] payload = Arrays.copyOfRange(body, dataStart, dataStart + size);
                int formatFlags = body[position + 9] & 0xFF;
                payload = prepareFramePayload(version, tagFlags, formatFlags, payload);
                return payload == null ? null : decodeTextFrame(payload);
            }
            position = dataStart + size;
        }
        return null;
    }

    private static String scanForGenreFrame(int version, int tagFlags, byte[] body) {
        byte[] target = version == 2
                ? new byte[] {'T', 'C', 'O'}
                : new byte[] {'T', 'C', 'O', 'N'};
        int headerSize = version == 2 ? 6 : 10;
        for (int position = 0; position + headerSize <= body.length; position++) {
            if (!matches(body, position, target)) continue;
            if (version == 2) {
                int size = ((body[position + 3] & 0xFF) << 16)
                        | ((body[position + 4] & 0xFF) << 8)
                        | (body[position + 5] & 0xFF);
                int dataStart = position + 6;
                if (size <= 0 || dataStart + size > body.length) continue;
                byte[] payload = Arrays.copyOfRange(body, dataStart, dataStart + size);
                if ((tagFlags & 0x80) != 0) payload = removeUnsynchronisation(payload);
                String decoded = decodeTextFrame(payload);
                if (decoded != null) return decoded;
            } else {
                int size = version == 4
                        ? synchsafeInt(body, position + 4)
                        : signedIntBigEndian(body, position + 4);
                int dataStart = position + 10;
                if (size <= 0 || dataStart + size > body.length) continue;
                byte[] payload = Arrays.copyOfRange(body, dataStart, dataStart + size);
                int formatFlags = body[position + 9] & 0xFF;
                payload = prepareFramePayload(version, tagFlags, formatFlags, payload);
                String decoded = payload == null ? null : decodeTextFrame(payload);
                if (decoded != null) return decoded;
            }
        }
        return null;
    }

    private static byte[] prepareFramePayload(int version, int tagFlags,
                                              int formatFlags, byte[] payload) {
        int offset = 0;
        boolean unsynchronised = (tagFlags & 0x80) != 0;
        if (version == 3) {
            boolean compressed = (formatFlags & 0x80) != 0;
            boolean encrypted = (formatFlags & 0x40) != 0;
            boolean grouped = (formatFlags & 0x20) != 0;
            if (compressed || encrypted) return null;
            if (grouped) offset += 1;
        } else if (version == 4) {
            boolean grouped = (formatFlags & 0x40) != 0;
            boolean compressed = (formatFlags & 0x08) != 0;
            boolean encrypted = (formatFlags & 0x04) != 0;
            boolean frameUnsynchronised = (formatFlags & 0x02) != 0;
            boolean hasDataLength = (formatFlags & 0x01) != 0;
            if (compressed || encrypted) return null;
            if (grouped) offset += 1;
            if (hasDataLength) offset += 4;
            unsynchronised = unsynchronised || frameUnsynchronised;
        }
        if (offset > payload.length) return null;
        byte[] result = offset == 0 ? payload : Arrays.copyOfRange(payload, offset, payload.length);
        return unsynchronised ? removeUnsynchronisation(result) : result;
    }

    private static String decodeTextFrame(byte[] payload) {
        if (payload == null || payload.length <= 1) return null;
        int encoding = payload[0] & 0xFF;
        Charset charset;
        switch (encoding) {
            case 0:
                charset = StandardCharsets.ISO_8859_1;
                break;
            case 1:
                charset = StandardCharsets.UTF_16;
                break;
            case 2:
                charset = StandardCharsets.UTF_16BE;
                break;
            case 3:
                charset = StandardCharsets.UTF_8;
                break;
            default:
                return null;
        }
        String value = new String(payload, 1, payload.length - 1, charset);
        return cleanTextValue(value);
    }

    static String readFlacGenre(InputStream rawInput) throws IOException {
        PushbackInputStream input = new PushbackInputStream(rawInput, 16);
        byte[] magic = new byte[4];
        if (!readFully(input, magic, 0, magic.length)) return null;

        if (magic[0] == 'I' && magic[1] == 'D' && magic[2] == '3') {
            byte[] remainingHeader = new byte[6];
            if (!readFully(input, remainingHeader, 0, remainingHeader.length)) return null;
            byte[] id3Header = new byte[10];
            System.arraycopy(magic, 0, id3Header, 0, 4);
            System.arraycopy(remainingHeader, 0, id3Header, 4, 6);
            int size = synchsafeInt(id3Header, 6);
            if (size < 0 || size > MAX_ID3_TAG_BYTES || !skipFully(input, size)) return null;
            if (!readFully(input, magic, 0, magic.length)) return null;
        }

        if (magic[0] != 'f' || magic[1] != 'L' || magic[2] != 'a' || magic[3] != 'C') {
            return null;
        }

        for (int blockIndex = 0; blockIndex < MAX_FLAC_BLOCKS; blockIndex++) {
            int first = input.read();
            if (first < 0) return null;
            boolean last = (first & 0x80) != 0;
            int blockType = first & 0x7F;
            byte[] lengthBytes = new byte[3];
            if (!readFully(input, lengthBytes, 0, lengthBytes.length)) return null;
            int length = ((lengthBytes[0] & 0xFF) << 16)
                    | ((lengthBytes[1] & 0xFF) << 8)
                    | (lengthBytes[2] & 0xFF);
            if (length < 0 || length > MAX_FLAC_BLOCK_BYTES) return null;

            if (blockType == 4) {
                byte[] commentBlock = new byte[length];
                if (!readFully(input, commentBlock, 0, length)) return null;
                String genre = parseVorbisCommentGenre(commentBlock);
                if (genre != null) return genre;
            } else if (!skipFully(input, length)) {
                return null;
            }
            if (last) break;
        }
        return null;
    }

    static String parseFlacGenre(byte[] completeFlac) {
        if (completeFlac == null) return null;
        try {
            return readFlacGenre(new ByteArrayInputStream(completeFlac));
        } catch (IOException impossible) {
            return null;
        }
    }

    private static String parseVorbisCommentGenre(byte[] block) {
        int position = 0;
        long vendorLength = unsignedIntLittleEndian(block, position);
        if (vendorLength < 0) return null;
        position += 4;
        if (vendorLength > block.length - position) return null;
        position += (int) vendorLength;

        long count = unsignedIntLittleEndian(block, position);
        if (count < 0 || count > 1_000_000L) return null;
        position += 4;
        List<String> genres = new ArrayList<>();
        for (long index = 0; index < count; index++) {
            long itemLength = unsignedIntLittleEndian(block, position);
            if (itemLength < 0) break;
            position += 4;
            if (itemLength > block.length - position) break;
            String item = new String(block, position, (int) itemLength, StandardCharsets.UTF_8);
            position += (int) itemLength;
            int equals = item.indexOf('=');
            if (equals <= 0) continue;
            String key = item.substring(0, equals);
            if (!"GENRE".equalsIgnoreCase(key)) continue;
            String value = cleanTextValue(item.substring(equals + 1));
            if (value != null) genres.add(value);
        }
        if (genres.isEmpty()) return null;
        StringBuilder combined = new StringBuilder();
        for (String genre : genres) {
            if (combined.length() > 0) combined.append(" / ");
            combined.append(genre);
        }
        return combined.toString();
    }

    private static String cleanTextValue(String value) {
        if (value == null) return null;
        value = value.replace("\uFEFF", "");
        String[] parts = value.replace('\u0000', '\n').split("\n+");
        StringBuilder cleaned = new StringBuilder();
        for (String part : parts) {
            String trimmed = part.trim();
            if (trimmed.isEmpty()) continue;
            if (cleaned.length() > 0) cleaned.append(" / ");
            cleaned.append(trimmed);
        }
        return cleaned.length() == 0 ? null : cleaned.toString();
    }

    private static byte[] removeUnsynchronisation(byte[] input) {
        ByteArrayOutputStream output = new ByteArrayOutputStream(input.length);
        for (int index = 0; index < input.length; index++) {
            int value = input[index] & 0xFF;
            output.write(value);
            if (value == 0xFF && index + 1 < input.length && input[index + 1] == 0) {
                index++;
            }
        }
        return output.toByteArray();
    }

    private static boolean validFrameId(byte[] data, int offset, int length) {
        for (int index = 0; index < length; index++) {
            int value = data[offset + index] & 0xFF;
            if (!((value >= 'A' && value <= 'Z') || (value >= '0' && value <= '9'))) {
                return false;
            }
        }
        return true;
    }

    private static boolean allZero(byte[] data, int offset, int length) {
        for (int index = 0; index < length; index++) {
            if (data[offset + index] != 0) return false;
        }
        return true;
    }

    private static boolean matches(byte[] data, int offset, byte[] target) {
        if (offset < 0 || offset + target.length > data.length) return false;
        for (int index = 0; index < target.length; index++) {
            if (data[offset + index] != target[index]) return false;
        }
        return true;
    }

    private static String ascii(byte[] data, int offset, int length) {
        return new String(data, offset, length, StandardCharsets.ISO_8859_1);
    }

    private static int synchsafeInt(byte[] data, int offset) {
        if (offset < 0 || offset + 4 > data.length) return -1;
        int a = data[offset] & 0xFF;
        int b = data[offset + 1] & 0xFF;
        int c = data[offset + 2] & 0xFF;
        int d = data[offset + 3] & 0xFF;
        if ((a | b | c | d) > 0x7F) return -1;
        return (a << 21) | (b << 14) | (c << 7) | d;
    }

    private static int signedIntBigEndian(byte[] data, int offset) {
        if (offset < 0 || offset + 4 > data.length) return -1;
        long value = unsignedIntBigEndian(data, offset);
        return value > Integer.MAX_VALUE ? -1 : (int) value;
    }

    private static long unsignedIntBigEndian(byte[] data, int offset) {
        if (offset < 0 || offset + 4 > data.length) return -1L;
        return ((long) (data[offset] & 0xFF) << 24)
                | ((long) (data[offset + 1] & 0xFF) << 16)
                | ((long) (data[offset + 2] & 0xFF) << 8)
                | (long) (data[offset + 3] & 0xFF);
    }

    private static long unsignedIntLittleEndian(byte[] data, int offset) {
        if (offset < 0 || offset + 4 > data.length) return -1L;
        return (long) (data[offset] & 0xFF)
                | ((long) (data[offset + 1] & 0xFF) << 8)
                | ((long) (data[offset + 2] & 0xFF) << 16)
                | ((long) (data[offset + 3] & 0xFF) << 24);
    }

    private static boolean readFully(InputStream input, byte[] buffer, int offset, int length)
            throws IOException {
        int total = 0;
        while (total < length) {
            int read = input.read(buffer, offset + total, length - total);
            if (read < 0) return false;
            if (read == 0) continue;
            total += read;
        }
        return true;
    }

    private static int readUpTo(InputStream input, byte[] buffer, int offset, int length)
            throws IOException {
        int total = 0;
        while (total < length) {
            int read = input.read(buffer, offset + total, length - total);
            if (read < 0) break;
            if (read == 0) continue;
            total += read;
        }
        return total;
    }

    private static boolean skipFully(InputStream input, long length) throws IOException {
        long remaining = length;
        byte[] scratch = new byte[8192];
        while (remaining > 0) {
            long skipped = input.skip(remaining);
            if (skipped > 0) {
                remaining -= skipped;
                continue;
            }
            int read = input.read(scratch, 0, (int) Math.min(scratch.length, remaining));
            if (read < 0) return false;
            remaining -= read;
        }
        return true;
    }
}
