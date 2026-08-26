package de.minimal.musicplayer;

import java.text.Normalizer;
import java.util.Locale;

/** Hard substring search over title, artist and album only — never genre. */
final class SearchMatcher {
    private SearchMatcher() { }

    static String buildKey(String title, String artist, String album) {
        return normalize(safe(title) + " " + safe(artist) + " " + safe(album));
    }

    static String normalizeQuery(String value) {
        return normalize(value).trim().replaceAll("\\s+", " ");
    }

    static boolean contains(String value, String normalizedQuery) {
        return !normalizedQuery.isEmpty() && normalize(value).contains(normalizedQuery);
    }

    static String normalize(String value) {
        if (value == null) return "";
        String decomposed = Normalizer.normalize(value, Normalizer.Form.NFD);
        StringBuilder output = new StringBuilder(decomposed.length());
        for (int index = 0; index < decomposed.length(); index++) {
            char c = decomposed.charAt(index);
            if (Character.getType(c) != Character.NON_SPACING_MARK) {
                output.append(Character.toLowerCase(c));
            }
        }
        return output.toString().toLowerCase(Locale.ROOT);
    }

    private static String safe(String value) {
        return value == null ? "" : value;
    }
}
