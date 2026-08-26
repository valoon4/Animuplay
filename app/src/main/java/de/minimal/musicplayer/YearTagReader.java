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
import java.util.Arrays;
import java.util.Locale;

/** Reads real year/date metadata directly from MP3 ID3v2 and FLAC Vorbis comments. */
final class YearTagReader {
    private static final int MAX_ID3_TAG_BYTES = 32 * 1024 * 1024;
    private static final int MAX_FLAC_BLOCK_BYTES = 32 * 1024 * 1024;
    private static final int MAX_FLAC_BLOCKS = 256;

    private YearTagReader() { }

    static String readYear(ContentResolver resolver, Uri uri, String fileName) {
        if (resolver == null || uri == null) return null;
        String lower = fileName == null ? "" : fileName.toLowerCase(Locale.ROOT);
        try (InputStream raw = resolver.openInputStream(uri)) {
            if (raw == null) return null;
            BufferedInputStream input = new BufferedInputStream(raw, 64 * 1024);
            if (lower.endsWith(".flac")) return readFlacYear(input);
            if (lower.endsWith(".mp3")) return readId3v2Year(input);

            input.mark(16);
            byte[] magic = new byte[4];
            int read = readUpTo(input, magic, 0, magic.length);
            input.reset();
            if (read >= 3 && magic[0] == 'I' && magic[1] == 'D' && magic[2] == '3') {
                return readId3v2Year(input);
            }
            if (read == 4 && magic[0] == 'f' && magic[1] == 'L'
                    && magic[2] == 'a' && magic[3] == 'C') {
                return readFlacYear(input);
            }
        } catch (IOException | RuntimeException ignored) {
            // MediaMetadataRetriever remains the fallback.
        }
        return null;
    }

    static String parseId3v2Year(byte[] completeTag) {
        if (completeTag == null || completeTag.length < 10) return null;
        try {
            return readId3v2Year(new ByteArrayInputStream(completeTag));
        } catch (IOException impossible) {
            return null;
        }
    }

    static String parseFlacYear(byte[] completeFlac) {
        if (completeFlac == null) return null;
        try {
            return readFlacYear(new ByteArrayInputStream(completeFlac));
        } catch (IOException impossible) {
            return null;
        }
    }

    private static String readId3v2Year(InputStream input) throws IOException {
        byte[] header = new byte[10];
        if (!readFully(input, header, 0, header.length)) return null;
        if (header[0] != 'I' || header[1] != 'D' || header[2] != '3') return null;

        int version = header[3] & 0xFF;
        if (version < 2 || version > 4) return null;
        int tagFlags = header[5] & 0xFF;
        int tagSize = synchsafeInt(header, 6);
        if (tagSize <= 0 || tagSize > MAX_ID3_TAG_BYTES) return null;

        byte[] body = new byte[tagSize];
        if (!readFully(input, body, 0, body.length)) return null;
        int position = skipExtendedHeader(version, tagFlags, body);

        while (version == 2 ? position + 6 <= body.length : position + 10 <= body.length) {
            int idLength = version == 2 ? 3 : 4;
            if (allZero(body, position, idLength) || !validFrameId(body, position, idLength)) break;
            String id = ascii(body, position, idLength);
            int size;
            int dataStart;
            int formatFlags = 0;
            if (version == 2) {
                size = ((body[position + 3] & 0xFF) << 16)
                        | ((body[position + 4] & 0xFF) << 8)
                        | (body[position + 5] & 0xFF);
                dataStart = position + 6;
            } else {
                size = version == 4 ? synchsafeInt(body, position + 4) : intBigEndian(body, position + 4);
                dataStart = position + 10;
                formatFlags = body[position + 9] & 0xFF;
            }
            if (size < 0 || dataStart + size > body.length) break;

            boolean yearFrame = (version == 2 && "TYE".equals(id))
                    || (version >= 3 && ("TYER".equals(id) || "TDRC".equals(id)));
            if (yearFrame) {
                byte[] payload = Arrays.copyOfRange(body, dataStart, dataStart + size);
                if (version == 2) {
                    if ((tagFlags & 0x80) != 0) payload = removeUnsynchronisation(payload);
                } else {
                    payload = prepareFramePayload(version, tagFlags, formatFlags, payload);
                }
                String year = normalizeYear(payload == null ? null : decodeTextFrame(payload));
                if (year != null) return year;
            }
            position = dataStart + size;
        }
        return null;
    }

    private static String readFlacYear(InputStream rawInput) throws IOException {
        PushbackInputStream input = new PushbackInputStream(rawInput, 16);
        byte[] magic = new byte[4];
        if (!readFully(input, magic, 0, magic.length)) return null;

        if (magic[0] == 'I' && magic[1] == 'D' && magic[2] == '3') {
            byte[] rest = new byte[6];
            if (!readFully(input, rest, 0, rest.length)) return null;
            byte[] id3Header = new byte[10];
            System.arraycopy(magic, 0, id3Header, 0, 4);
            System.arraycopy(rest, 0, id3Header, 4, 6);
            int size = synchsafeInt(id3Header, 6);
            if (size < 0 || size > MAX_ID3_TAG_BYTES || !skipFully(input, size)) return null;
            if ((id3Header[5] & 0x10) != 0 && !skipFully(input, 10)) return null;
            if (!readFully(input, magic, 0, magic.length)) return null;
        }

        if (magic[0] != 'f' || magic[1] != 'L' || magic[2] != 'a' || magic[3] != 'C') return null;

        for (int blockIndex = 0; blockIndex < MAX_FLAC_BLOCKS; blockIndex++) {
            int first = input.read();
            if (first < 0) return null;
            boolean last = (first & 0x80) != 0;
            int blockType = first & 0x7F;
            byte[] len = new byte[3];
            if (!readFully(input, len, 0, len.length)) return null;
            int length = ((len[0] & 0xFF) << 16) | ((len[1] & 0xFF) << 8) | (len[2] & 0xFF);
            if (length < 0 || length > MAX_FLAC_BLOCK_BYTES) return null;

            if (blockType == 4) {
                byte[] block = new byte[length];
                if (!readFully(input, block, 0, length)) return null;
                String year = parseVorbisCommentYear(block);
                if (year != null) return year;
            } else if (!skipFully(input, length)) {
                return null;
            }
            if (last) break;
        }
        return null;
    }

    private static String parseVorbisCommentYear(byte[] block) {
        int position = 0;
        long vendorLength = uintLittleEndian(block, position);
        if (vendorLength < 0) return null;
        position += 4;
        if (vendorLength > block.length - position) return null;
        position += (int) vendorLength;

        long count = uintLittleEndian(block, position);
        if (count < 0 || count > 1_000_000L) return null;
        position += 4;

        String date = null;
        String originalYear = null;
        String originalDate = null;
        for (long index = 0; index < count; index++) {
            long itemLength = uintLittleEndian(block, position);
            if (itemLength < 0) break;
            position += 4;
            if (itemLength > block.length - position) break;
            String item = new String(block, position, (int) itemLength, StandardCharsets.UTF_8);
            position += (int) itemLength;
            int equals = item.indexOf('=');
            if (equals <= 0) continue;
            String key = item.substring(0, equals).trim();
            String value = item.substring(equals + 1);
            if ("YEAR".equalsIgnoreCase(key)) {
                String year = normalizeYear(value);
                if (year != null) return year;
            } else if ("DATE".equalsIgnoreCase(key)) {
                date = value;
            } else if ("ORIGINALYEAR".equalsIgnoreCase(key)) {
                originalYear = value;
            } else if ("ORIGINALDATE".equalsIgnoreCase(key)) {
                originalDate = value;
            }
        }
        String result = normalizeYear(date);
        if (result != null) return result;
        result = normalizeYear(originalYear);
        return result != null ? result : normalizeYear(originalDate);
    }

    private static String normalizeYear(String value) {
        if (value == null) return null;
        String cleaned = value.replace("\uFEFF", "").replace('\u0000', ' ').trim();
        for (int i = 0; i + 4 <= cleaned.length(); i++) {
            char a = cleaned.charAt(i);
            char b = cleaned.charAt(i + 1);
            char c = cleaned.charAt(i + 2);
            char d = cleaned.charAt(i + 3);
            if (!Character.isDigit(a) || !Character.isDigit(b)
                    || !Character.isDigit(c) || !Character.isDigit(d)) continue;
            int year = (a - '0') * 1000 + (b - '0') * 100 + (c - '0') * 10 + (d - '0');
            if (year >= 1000 && year <= 2999) return cleaned.substring(i, i + 4);
        }
        return null;
    }

    private static String decodeTextFrame(byte[] payload) {
        if (payload == null || payload.length <= 1) return null;
        int encoding = payload[0] & 0xFF;
        Charset charset;
        switch (encoding) {
            case 0: charset = StandardCharsets.ISO_8859_1; break;
            case 1: charset = StandardCharsets.UTF_16; break;
            case 2: charset = StandardCharsets.UTF_16BE; break;
            case 3: charset = StandardCharsets.UTF_8; break;
            default: return null;
        }
        return new String(payload, 1, payload.length - 1, charset);
    }

    private static int skipExtendedHeader(int version, int flags, byte[] body) {
        if ((flags & 0x40) == 0 || body.length < 4) return 0;
        if (version == 3) {
            long size = uintBigEndian(body, 0);
            long offset = 4L + size;
            return offset <= body.length ? (int) offset : body.length;
        }
        if (version == 4) {
            int size = synchsafeInt(body, 0);
            return size >= 4 && size <= body.length ? size : body.length;
        }
        return 0;
    }

    private static byte[] prepareFramePayload(int version, int tagFlags, int formatFlags, byte[] payload) {
        int offset = 0;
        boolean unsync = (tagFlags & 0x80) != 0;
        if (version == 3) {
            if ((formatFlags & 0x80) != 0 || (formatFlags & 0x40) != 0) return null;
            if ((formatFlags & 0x20) != 0) offset++;
        } else if (version == 4) {
            if ((formatFlags & 0x08) != 0 || (formatFlags & 0x04) != 0) return null;
            if ((formatFlags & 0x40) != 0) offset++;
            if ((formatFlags & 0x01) != 0) offset += 4;
            unsync = unsync || (formatFlags & 0x02) != 0;
        }
        if (offset > payload.length) return null;
        byte[] result = offset == 0 ? payload : Arrays.copyOfRange(payload, offset, payload.length);
        return unsync ? removeUnsynchronisation(result) : result;
    }

    private static byte[] removeUnsynchronisation(byte[] input) {
        ByteArrayOutputStream output = new ByteArrayOutputStream(input.length);
        for (int i = 0; i < input.length; i++) {
            int value = input[i] & 0xFF;
            output.write(value);
            if (value == 0xFF && i + 1 < input.length && input[i + 1] == 0) i++;
        }
        return output.toByteArray();
    }

    private static int synchsafeInt(byte[] data, int offset) {
        if (offset < 0 || offset + 4 > data.length) return -1;
        return ((data[offset] & 0x7F) << 21)
                | ((data[offset + 1] & 0x7F) << 14)
                | ((data[offset + 2] & 0x7F) << 7)
                | (data[offset + 3] & 0x7F);
    }

    private static int intBigEndian(byte[] data, int offset) {
        if (offset < 0 || offset + 4 > data.length) return -1;
        return ((data[offset] & 0xFF) << 24)
                | ((data[offset + 1] & 0xFF) << 16)
                | ((data[offset + 2] & 0xFF) << 8)
                | (data[offset + 3] & 0xFF);
    }

    private static long uintBigEndian(byte[] data, int offset) {
        if (offset < 0 || offset + 4 > data.length) return -1;
        return ((long) (data[offset] & 0xFF) << 24)
                | ((long) (data[offset + 1] & 0xFF) << 16)
                | ((long) (data[offset + 2] & 0xFF) << 8)
                | (long) (data[offset + 3] & 0xFF);
    }

    private static long uintLittleEndian(byte[] data, int offset) {
        if (offset < 0 || offset + 4 > data.length) return -1;
        return (long) (data[offset] & 0xFF)
                | ((long) (data[offset + 1] & 0xFF) << 8)
                | ((long) (data[offset + 2] & 0xFF) << 16)
                | ((long) (data[offset + 3] & 0xFF) << 24);
    }

    private static boolean validFrameId(byte[] data, int offset, int length) {
        if (offset < 0 || offset + length > data.length) return false;
        for (int i = 0; i < length; i++) {
            int value = data[offset + i] & 0xFF;
            if (!((value >= 'A' && value <= 'Z') || (value >= '0' && value <= '9'))) return false;
        }
        return true;
    }

    private static boolean allZero(byte[] data, int offset, int length) {
        if (offset < 0 || offset + length > data.length) return false;
        for (int i = 0; i < length; i++) if (data[offset + i] != 0) return false;
        return true;
    }

    private static String ascii(byte[] data, int offset, int length) {
        return new String(data, offset, length, StandardCharsets.ISO_8859_1);
    }

    private static boolean readFully(InputStream input, byte[] buffer, int offset, int length) throws IOException {
        return readUpTo(input, buffer, offset, length) == length;
    }

    private static int readUpTo(InputStream input, byte[] buffer, int offset, int length) throws IOException {
        int total = 0;
        while (total < length) {
            int read = input.read(buffer, offset + total, length - total);
            if (read < 0) break;
            if (read == 0) continue;
            total += read;
        }
        return total;
    }

    private static boolean skipFully(InputStream input, long amount) throws IOException {
        long remaining = amount;
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
