"""Deterministic relative date and time parsing for Telugu / Tenglish / English. Always read back results."""
from __future__ import annotations
import datetime as dt
import re
from dataclasses import dataclass
from .normalize import base, spoken_digits_to_digits

WEEKDAYS = {
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6,
    "సోమవారం": 0, "మంగళవారం": 1, "బుధవారం": 2, "గురువారం": 3, "శుక్రవారం": 4, "శనివారం": 5, "ఆదివారం": 6,
    "మండే": 0, "ట్యూస్డే": 1, "వెడ్నెస్డే": 2, "థర్స్డే": 3, "ఫ్రైడే": 4, "సాటర్డే": 5, "సండే": 6,
}
TODAY = {"today", "ఈరోజు", "ఈ రోజు", "ఇవాళ", "ఇవ్వాళ", "టుడే"}
TOMORROW = {"tomorrow", "రేపు", "టుమారో"}
DAY_AFTER = {"day after tomorrow", "ఎల్లుండి"}
NEXT = {"next", "వచ్చే", "నెక్స్ట్"}
WEEKDAY_EN = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


@dataclass
class DateResult:
    date: dt.date | None
    status: str          # "ok" | "ambiguous" | "unparsed"
    note: str = ""


def parse_date(text: str, today: dt.date) -> DateResult:
    t = base(text)
    iso = re.search(r"(\d{4})-(\d{2})-(\d{2})", t)
    if iso:
        return DateResult(dt.date(*map(int, iso.groups())), "ok")
    rel = []
    for words, off in ((DAY_AFTER, 2), (TOMORROW, 1), (TODAY, 0)):
        for w in words:
            for m in re.finditer(re.escape(w), t):
                rel.append((m.start(), off))
    if rel:
        rel.sort()
        note = "caller corrected the day; read back" if len({r[1] for r in rel}) > 1 else ""
        return DateResult(today + dt.timedelta(days=rel[-1][1]), "ok", note)
    hits = sorted((m.start(), wd) for name, wd in WEEKDAYS.items() for m in re.finditer(re.escape(name), t))
    if hits:
        wd = hits[-1][1]                      # last mention wins: "Wednesday... కాదు Thursday" -> Thursday
        corrected = len({h[1] for h in hits}) > 1
        delta = (wd - today.weekday()) % 7 or 7
        d = today + dt.timedelta(days=delta)
        if delta == 7 and not any(n in t for n in NEXT):
            return DateResult(d, "ambiguous", f"today is also {WEEKDAY_EN[wd]}: could mean today {today.isoformat()}")
        if any(n in t for n in NEXT) and delta <= 6:
            # "next Saturday" is ambiguous in Indian usage: coming Saturday or the one after.
            return DateResult(d, "ambiguous", f"could also mean {(d + dt.timedelta(days=7)).isoformat()}")
        return DateResult(d, "ok", "caller corrected the day; read back" if corrected else "")
    return DateResult(None, "unparsed")


DAYPART_PM = {"సాయంత్రం", "మధ్యాహ్నం", "రాత్రి", "evening", "afternoon", "night", "pm", "ఈవెనింగ్", "ఆఫ్టర్నూన్"}
DAYPART_AM = {"ఉదయం", "పొద్దున", "పొద్దున్నే", "morning", "am", "మార్నింగ్"}
HALF_HOURS = {"ఒకటిన్నర": 1, "రెండున్నర": 2, "మూడున్నర": 3, "నాలుగున్నర": 4, "ఐదున్నర": 5, "ఆరున్నర": 6,
              "ఏడున్నర": 7, "ఎనిమిదిన్నర": 8, "తొమ్మిదిన్నర": 9, "పదిన్నర": 10, "పదకొండున్నర": 11, "పన్నెండున్నర": 12}
EN_HOURS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
            "ten": 10, "eleven": 11, "twelve": 12}
EN_MIN = {"thirty": 30, "fifteen": 15, "forty five": 45, "forty-five": 45}
TE_HOURS = {"ఒంటి": 1, "రెండు": 2, "మూడు": 3, "నాలుగు": 4, "ఐదు": 5, "ఆరు": 6, "ఏడు": 7, "ఎనిమిది": 8,
            "తొమ్మిది": 9, "పది": 10, "పదకొండు": 11, "పన్నెండు": 12}


@dataclass
class TimeResult:
    time: dt.time | None
    status: str          # "ok" | "inferred_ampm" | "daypart_only" | "unparsed"
    daypart: str | None = None


def parse_time(text: str, open_hour: int = 9, close_hour: int = 19) -> TimeResult:
    t = base(text)
    pm = any(p in t for p in DAYPART_PM)
    am = any(p in t for p in DAYPART_AM)
    cands: list[tuple[int, int, int]] = []   # (position, hour, minute); last mention wins
    for w, h in HALF_HOURS.items():
        cands += [(m.start(), h, 30) for m in re.finditer(w, t)]
    cands += [(m.start(), int(m.group(1)), int(m.group(2))) for m in re.finditer(r"\b(\d{1,2})[:.](\d{2})\b", t)]
    cands += [(m.start(), EN_HOURS[m.group(1)], 30) for m in re.finditer(r"half past (\w+)", t) if m.group(1) in EN_HOURS]
    for w, h in EN_HOURS.items():
        cands += [(m.start(), h, EN_MIN.get(m.group(1) or "", 0))
                  for m in re.finditer(rf"\b{w}\b(?:\s+(thirty|fifteen|forty five|forty-five|o'?clock))?", t)
                  if not t[max(0, m.start() - 10):m.start()].endswith("half past ")]
    for w, h in TE_HOURS.items():
        cands += [(m.start(), h, 0) for m in re.finditer(rf"(?<![^\s]){w}\s*(గంటలకి|గంటలకు|గంటకి|గంటలు)", t)]
    hour = minute = None
    if cands:
        _, hour, minute = max(cands)
    if hour is None:
        m = re.search(r"\b(\d{1,2})\s*(?:గంటలకి|గంటలకు|గంటకి|o'?clock|pm|am)?\b", spoken_digits_to_digits(t))
        if m and 1 <= int(m.group(1)) <= 12 and (pm or am or "గంట" in t or "clock" in t):
            hour, minute = int(m.group(1)), 0
    if hour is None:
        dp = "pm" if pm else "am" if am else None
        return TimeResult(None, "daypart_only" if dp else "unparsed", dp)
    status = "ok"
    if hour <= 12:
        if pm and hour < 12:
            hour += 12
        elif not am and not pm:
            # No daypart: pick the reading inside business hours; flag it so the agent reads it back.
            if not (open_hour <= hour < close_hour) and open_hour <= hour + 12 < close_hour:
                hour += 12
            status = "inferred_ampm"
    return TimeResult(dt.time(hour % 24, minute or 0), status)
