"""Entity-level scoring of an STT hypothesis against reference entities. RAW and NORMALIZED kept separate."""
from __future__ import annotations
import datetime as dt
import re
from entities.normalize import base, extract_phones, normalize_vehicle_reg, extract_prices, name_tokens, phonetic_key
from entities.dates import parse_date, parse_time

REF_TODAY = dt.date(2026, 10, 1)  # fixed anchor so relative dates score deterministically


def _date_value(label: str) -> dt.date:
    if label == "tomorrow":
        return REF_TODAY + dt.timedelta(days=1)
    if label == "day_after":
        return REF_TODAY + dt.timedelta(days=2)
    wd = int(label.split(":")[1])
    return REF_TODAY + dt.timedelta(days=(wd - REF_TODAY.weekday()) % 7 or 7)


def match(entity: dict, hyp: str) -> tuple[bool, bool, str]:
    """Return (raw_exact, normalized, error_kind). error_kind in {'ok','missing','wrong_value','invalid_format'}."""
    t, v = entity["type"], entity["value"]
    hb = base(hyp)
    if t == "phone":
        raw = v in re.sub(r"\s", "", hb)
        found = extract_phones(hyp)
        norm = v in found
        return raw, norm, "ok" if norm else ("wrong_value" if found else "missing")
    if t == "vehicle_reg":
        raw = v.lower() in re.sub(r"[\s-]", "", hb)
        got = normalize_vehicle_reg(hyp)
        return raw, got == v, "ok" if got == v else ("wrong_value" if got else "invalid_format")
    if t == "price":
        raw = str(v) in re.sub(r"[,\s]", "", hb)
        got = extract_prices(hyp) or [int(x) for x in re.findall(r"\d{3,6}", re.sub(r",", "", hb))]
        return raw, v in got, "ok" if v in got else ("wrong_value" if got else "missing")
    if t == "date":
        got = parse_date(hyp, REF_TODAY)
        ok = got.date == _date_value(v)
        return ok, ok, "ok" if ok else ("wrong_value" if got.date else "missing")
    if t == "time":
        got = parse_time(hyp)
        ok = bool(got.time) and got.time.strftime("%H:%M") == v
        return ok, ok, "ok" if ok else ("wrong_value" if got.time else "missing")
    # names, localities, services, business: surface match (raw) vs phonetic token coverage (normalized)
    raw = base(str(v)) in hb
    ref_keys = [phonetic_key(x) for x in name_tokens(str(v))]
    hyp_keys = {phonetic_key(x) for x in name_tokens(hyp)}
    norm = bool(ref_keys) and all(k in hyp_keys for k in ref_keys)
    partial = any(k in hyp_keys for k in ref_keys)
    return raw, norm, "ok" if norm else ("wrong_value" if partial else "missing")
