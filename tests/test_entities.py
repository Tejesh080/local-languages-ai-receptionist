import datetime as dt
from entities.normalize import (normalize_phone, normalize_vehicle_reg, spoken_digits_to_digits, extract_prices,
                                phonetic_key, to_latin, for_wer, format_phone_readback)
from entities.dates import parse_date, parse_time
from entities.resolver import Candidate, resolve_name, resolve_vehicle, resolve_phone
from entities.telugu import romanize


def test_telugu_digits_and_words():
    assert normalize_phone("నా నంబర్ ౯౮౪౮౦ ౧౨౩౪౫") == "9848012345"
    assert normalize_phone("nine eight four eight zero one two three four five") == "9848012345"
    assert normalize_phone("నైన్ ఎయిట్ ఫోర్ ఎయిట్ జీరో డబుల్ వన్ టూ త్రీ ఫోర్") == "9848011234"
    assert normalize_phone("+91 98480 12345") == "9848012345"
    assert normalize_phone("12345") is None
    assert spoken_digits_to_digits("triple nine") == "999"


def test_vehicle_regs():
    assert normalize_vehicle_reg("TS 09 EA 4521") == "TS09EA4521"
    assert normalize_vehicle_reg("ts-09-ea-4521 vehicle status") == "TS09EA4521"
    assert normalize_vehicle_reg("టి ఎస్ జీరో నైన్ ఈ ఏ ఫోర్ ఫైవ్ టూ వన్") == "TS09EA4521"
    assert normalize_vehicle_reg("TG 08 C 1234") == "TG08C1234"
    assert normalize_vehicle_reg("22 BH 1234 AB") == "22BH1234AB"
    assert normalize_vehicle_reg("TS 09 EA") is None


def test_prices():
    assert extract_prices("Brake inspection ₹499 అండి") == [499]
    assert extract_prices("1,899 రూపాయలు") == [1899]
    assert extract_prices("₹1,899 అన్నారు") == [1899]


def test_romanize_and_phonetics():
    assert romanize("రెడ్డి") == "reddi"
    assert phonetic_key("Reddy") == phonetic_key("reddi") == phonetic_key("Ready")
    assert phonetic_key("Naidu") == phonetic_key("Naidoo")
    assert phonetic_key("Srinivasa") == phonetic_key("Srinivas")
    assert phonetic_key("Rao") != phonetic_key("Reddy")
    assert phonetic_key(to_latin("రావు")) == phonetic_key("Rao")      # E7 run 1 finding
    assert to_latin("శ్రీనివాస్") == "shriinivaas"


def test_dates():
    today = dt.date(2026, 10, 1)  # Thursday
    assert parse_date("రేపు", today).date == dt.date(2026, 10, 2)
    assert parse_date("ఎల్లుండి", today).date == dt.date(2026, 10, 3)
    assert parse_date("Saturday slot ఉందా", today).date == dt.date(2026, 10, 3)
    r = parse_date("next Saturday", today)
    assert r.status == "ambiguous" and r.date == dt.date(2026, 10, 3)
    assert parse_date("శనివారం", today).date == dt.date(2026, 10, 3)
    corr = parse_date("Wednesday... కాదు కాదు Friday", today)
    assert corr.date == dt.date(2026, 10, 2) and "corrected" in corr.note
    assert parse_date("Thursday", today).status == "ambiguous"          # today is Thursday
    assert parse_date("రేపు... అంటే... ఎల్లుండి", today).date == dt.date(2026, 10, 3)


def test_times():
    assert parse_time("సాయంత్రం ఐదున్నర").time == dt.time(17, 30)
    assert parse_time("five thirty").time == dt.time(17, 30)
    assert parse_time("five thirty").status == "inferred_ampm"
    assert parse_time("ఉదయం 10 గంటలకి").time == dt.time(10, 0)
    assert parse_time("5:30 pm").time == dt.time(17, 30)
    assert parse_time("evening").status == "daypart_only"
    assert parse_time("half past five").time == dt.time(17, 30)
    assert parse_time("ఉదయం పది... సారీ పదకొండు గంటలకి").time == dt.time(11, 0)


ADVISORS = [Candidate("a1", "Srinivas Reddy"), Candidate("a2", "Srinivas Rao"), Candidate("a3", "Lakshmi Naidu")]


def test_resolver_never_silently_picks_confusable():
    r = resolve_name("Srinivas Ready", ADVISORS)
    assert r.decision == "confirm" and r.best.id == "a1"
    r = resolve_name("Srinivas garu", ADVISORS)
    assert r.decision == "clarify" and {s.candidate.id for s in r.top} == {"a1", "a2"}
    assert resolve_name("Srinivas Reddy", ADVISORS).decision == "auto"
    assert resolve_name("లక్ష్మి నాయుడు", ADVISORS).best.id == "a3"
    assert resolve_name("Mahesh Babu", ADVISORS).decision == "no_match"


def test_critical_entities_never_auto():
    regs = [Candidate("v1", "TS09EA4521"), Candidate("v2", "TS09EA4527")]
    assert resolve_vehicle("TS 09 EA 4521", regs).decision == "confirm"
    assert resolve_vehicle("TS 09 EA 452", regs).decision == "clarify"
    assert resolve_phone("98480 12345").decision == "confirm"
    assert format_phone_readback("9848012345") == "98480 12345"


def test_wer_normalization_keeps_words():
    assert for_wer("Service, బుక్ చేయాలి!") == "service బుక్ చేయాలి"
