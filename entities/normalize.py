"""Deterministic normalization. Keep RAW and NORMALIZED separate in scoring; never hide real errors."""
from __future__ import annotations
import re
import unicodedata
from .telugu import TELUGU_DIGITS, DEVANAGARI_DIGITS, DIGIT_WORDS, REPEAT_WORDS, LETTER_NAMES_TE, romanize

_ZW = dict.fromkeys(map(ord, "\u200b\u200c\u200d\ufeff"), None)
_PUNCT = re.compile(r"[\"'`.,!?;:()\[\]{}|/\\-]+")


def base(text: str) -> str:
    """Unicode NFC, strip zero-width chars, map native digits, lowercase Latin, collapse spaces."""
    t = unicodedata.normalize("NFC", text or "").translate(_ZW)
    t = "".join(TELUGU_DIGITS.get(c, DEVANAGARI_DIGITS.get(c, c)) for c in t)
    t = t.lower()
    return re.sub(r"\s+", " ", t).strip()


def for_wer(text: str) -> str:
    """WER normalization: base + punctuation removal. Does NOT convert number words (kept for RAW-vs-NORM)."""
    return re.sub(r"\s+", " ", _PUNCT.sub(" ", base(text))).strip()


def spoken_digits_to_digits(text: str) -> str:
    """'nine eight double four' -> '9844'. Only converts runs of digit words; leaves other words intact."""
    t = re.sub(r"(?<=\d),(?=\d)", "", base(text))     # 1,899 -> 1899 (Indian and Western grouping)
    toks = t.replace(",", " ").split()
    out: list[str] = []
    repeat = 1
    for tok in toks:
        if tok in REPEAT_WORDS:
            repeat = REPEAT_WORDS[tok]
            continue
        if tok in DIGIT_WORDS:
            out.append(DIGIT_WORDS[tok] * repeat)
        elif tok.isdigit():
            out.append(tok * repeat if repeat > 1 and len(tok) == 1 else tok)
        else:
            out.append(" " + tok + " ")
        repeat = 1
    return re.sub(r"\s+", " ", "".join(out)).strip()


# ---------- phone numbers ----------
_PHONE = re.compile(r"(?:\+?91|0)?([6-9]\d{9})")


def extract_phones(text: str) -> list[str]:
    digits_text = spoken_digits_to_digits(text)
    compact = re.sub(r"(?<=\d)[\s-]+(?=\d)", "", digits_text)
    return [m.group(1) for m in _PHONE.finditer(compact)]


def normalize_phone(value: str) -> str | None:
    found = extract_phones(value)
    return found[0] if found else None


# ---------- vehicle registrations (Telangana TS/TG, Andhra AP, Bharat series BH) ----------
_REG_STATE = re.compile(r"^(TS|TG|AP)(\d{2})([A-Z]{1,3})(\d{1,4})$")
_REG_BH = re.compile(r"^(\d{2})BH(\d{4})([A-Z]{1,2})$")


def _tokens_to_reg_chars(text: str) -> str:
    out = []
    t = base(text)
    for tok in t.split():
        if tok in LETTER_NAMES_TE:
            out.append(LETTER_NAMES_TE[tok])
        elif tok in DIGIT_WORDS:
            out.append(DIGIT_WORDS[tok])
        elif tok in REPEAT_WORDS:
            out.append(f"<R{REPEAT_WORDS[tok]}>")
        else:
            out.append(re.sub(r"[^a-z0-9]", "", tok).upper())
    s = "".join(out)
    # expand double/triple markers applying to the following char
    return re.sub(r"<R(\d)>(.)", lambda m: m.group(2) * int(m.group(1)), s)


def normalize_vehicle_reg(value: str) -> str | None:
    """Return canonical 'TS09EA4521' or None if the text does not form a valid registration."""
    s = _tokens_to_reg_chars(value)
    for m in re.finditer(r"(?:TS|TG|AP)\d{2}[A-Z]{1,3}\d{4}|\d{2}BH\d{4}[A-Z]{1,2}", s):
        return m.group(0)
    return None


def partial_vehicle_reg(value: str) -> str:
    """Best-effort compact form even when invalid (used for candidate search, never for booking)."""
    return _tokens_to_reg_chars(value)


def format_vehicle_reg_readback(reg: str) -> str:
    m = _REG_STATE.match(reg)
    if m:
        return " ".join(list(m.group(1))) + " " + " ".join(m.group(2)) + " " + " ".join(m.group(3)) + " " + " ".join(m.group(4))
    return " ".join(reg)


def format_phone_readback(phone: str) -> str:
    return f"{phone[:5]} {phone[5:]}"  # grouped 5+5, standard Indian mobile readback


# ---------- prices ----------
_PRICE = re.compile(r"(?:₹|rs\.?|inr)\s*([\d,]+)|([\d,]+)\s*(?:rupees|rupaayalu|రూపాయలు|రూపాయిలు|/-)")


def extract_prices(text: str) -> list[int]:
    t = spoken_digits_to_digits(text)
    out = []
    for m in _PRICE.finditer(t):
        n = (m.group(1) or m.group(2)).replace(",", "")
        if n.isdigit():
            out.append(int(n))
    return out


# ---------- names / free text for matching ----------
def to_latin(text: str) -> str:
    t = base(text)
    return romanize(t) if any("\u0C00" <= c <= "\u0C7F" for c in t) else t


_HONORIFICS = {"garu", "gaaru", "sir", "madam", "anna", "akka", "dr", "doctor", "mr", "mrs", "ms", "andi", "gari"}


def name_tokens(text: str) -> list[str]:
    latin = re.sub(r"[^a-z ]", " ", to_latin(text))
    return [t for t in latin.split() if t and t not in _HONORIFICS]


def phonetic_key(token: str) -> str:
    """Indic-aware phonetic key for Latin tokens. Collapses aspiration, vowel length, doubling."""
    t = re.sub(r"[^a-z]", "", token.lower())
    for a, b in (("x", "ks"), ("ph", "f"), ("sh", "s"), ("ch", "c"), ("th", "t"), ("dh", "d"), ("bh", "b"),
                 ("kh", "k"), ("gh", "g"), ("jh", "j"), ("ck", "k"), ("q", "k"), ("z", "j"), ("w", "v"),
                 ("ee", "i"), ("ii", "i"), ("oo", "u"), ("uu", "u"), ("aa", "a"), ("ea", "e"), ("ey", "i"), ("ie", "i")):
        t = t.replace(a, b)
    t = re.sub(r"(.)\1+", r"\1", t)          # doubled letters
    t = re.sub(r"y$", "i", t)                # Reddy/Reddi
    t = re.sub(r"avu$", "ao", t)             # Telugu -avu ending vs English -ao spelling: రావు "raavu" / Rao
    if len(t) > 4:
        t = re.sub(r"(?<=[^aeiou])a$", "", t)  # Srinivasa/Srinivas
    return t
