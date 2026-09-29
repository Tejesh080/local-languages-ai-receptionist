"""Telugu script helpers: digits, romanization, spelled letters, number words."""
from __future__ import annotations
import unicodedata

TELUGU_DIGITS = {chr(0x0C66 + i): str(i) for i in range(10)}
DEVANAGARI_DIGITS = {chr(0x0966 + i): str(i) for i in range(10)}

_CONS = {
    "క": "k", "ఖ": "kh", "గ": "g", "ఘ": "gh", "ఙ": "ng", "చ": "ch", "ఛ": "chh", "జ": "j", "ఝ": "jh",
    "ఞ": "ny", "ట": "t", "ఠ": "th", "డ": "d", "ఢ": "dh", "ణ": "n", "త": "t", "థ": "th", "ద": "d",
    "ధ": "dh", "న": "n", "ప": "p", "ఫ": "ph", "బ": "b", "భ": "bh", "మ": "m", "య": "y", "ర": "r",
    "ఱ": "r", "ల": "l", "ళ": "l", "వ": "v", "శ": "sh", "ష": "sh", "స": "s", "హ": "h",
}
_VOWELS = {"అ": "a", "ఆ": "aa", "ఇ": "i", "ఈ": "ii", "ఉ": "u", "ఊ": "uu", "ఋ": "ru", "ఎ": "e",
           "ఏ": "ee", "ఐ": "ai", "ఒ": "o", "ఓ": "oo", "ఔ": "au"}
_MATRAS = {"ా": "aa", "ి": "i", "ీ": "ii", "ు": "u", "ూ": "uu", "ృ": "ru", "ె": "e", "ే": "ee",
           "ై": "ai", "ొ": "o", "ో": "oo", "ౌ": "au"}
_VIRAMA = "్"
_OTHER = {"ం": "m", "ః": "h", "ఁ": ""}


def romanize(text: str) -> str:
    """Deterministic, lossy Telugu -> Latin romanization for matching (not for display)."""
    text = unicodedata.normalize("NFC", text)
    out: list[str] = []
    chars = list(text)
    for i, ch in enumerate(chars):
        nxt = chars[i + 1] if i + 1 < len(chars) else ""
        if ch in _CONS:
            out.append(_CONS[ch])
            if nxt not in _MATRAS and nxt != _VIRAMA:
                out.append("a")
        elif ch in _VOWELS:
            out.append(_VOWELS[ch])
        elif ch in _MATRAS:
            out.append(_MATRAS[ch])
        elif ch == _VIRAMA:
            continue
        elif ch in _OTHER:
            out.append(_OTHER[ch])
        elif ch in TELUGU_DIGITS:
            out.append(TELUGU_DIGITS[ch])
        else:
            out.append(ch)
    return "".join(out)


def has_telugu(text: str) -> bool:
    return any("\u0C00" <= c <= "\u0C7F" for c in text)


# Letter names as spoken/transcribed in Telugu script (for vehicle registrations).
LETTER_NAMES_TE = {
    "ఏ": "A", "ఎ": "A", "బీ": "B", "బి": "B", "సీ": "C", "సి": "C", "డీ": "D", "డి": "D", "ఈ": "E", "ఇ": "E",
    "ఎఫ్": "F", "జీ": "G", "జి": "G", "హెచ్": "H", "ఎచ్": "H", "ఐ": "I", "జే": "J", "జె": "J", "కే": "K", "కె": "K",
    "ఎల్": "L", "ఎం": "M", "ఎమ్": "M", "ఎన్": "N", "ఓ": "O", "పీ": "P", "పి": "P", "క్యూ": "Q", "ఆర్": "R",
    "ఎస్": "S", "టీ": "T", "టి": "T", "యూ": "U", "యు": "U", "వీ": "V", "వి": "V", "డబ్ల్యూ": "W", "డబ్ల్యు": "W",
    "ఎక్స్": "X", "వై": "Y", "జెడ్": "Z", "జడ్": "Z",
}

DIGIT_WORDS = {
    # English
    "zero": "0", "oh": "0", "one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
    "six": "6", "seven": "7", "eight": "8", "nine": "9",
    # Telugu native
    "సున్నా": "0", "సున్న": "0", "ఒకటి": "1", "రెండు": "2", "మూడు": "3", "నాలుగు": "4", "ఐదు": "5",
    "అయిదు": "5", "ఆరు": "6", "ఏడు": "7", "ఎనిమిది": "8", "తొమ్మిది": "9",
    # English words in Telugu script (common in Tenglish transcripts)
    "జీరో": "0", "వన్": "1", "టు": "2", "టూ": "2", "త్రీ": "3", "ఫోర్": "4", "ఫైవ్": "5", "సిక్స్": "6",
    "సెవెన్": "7", "ఎయిట్": "8", "ఎయిట్స్": "8", "నైన్": "9",
}
REPEAT_WORDS = {"double": 2, "triple": 3, "డబుల్": 2, "ట్రిపుల్": 3}
