"""Generate the E3 read-prompt pool (receptionist-style lines) with KNOWN / CONFUSABLE / UNSEEN partitions,
and assign 50 prompts per speaker with a condition schedule. Deterministic given --seed."""
from __future__ import annotations
import argparse, hashlib, json, random
from pathlib import Path
import yaml

TE_DIGITS = ["సున్నా", "ఒకటి", "రెండు", "మూడు", "నాలుగు", "ఐదు", "ఆరు", "ఏడు", "ఎనిమిది", "తొమ్మిది"]
KNOWN = yaml.safe_load(open(Path(__file__).resolve().parents[1] / "benchmark/configs/tenant_known_entities.yaml"))

CONFUSABLE_NAMES = ["Srinivasa Reddy", "Venkat Reddy", "Venkat Rao", "Ravi Naidu", "Srinivas Row", "Lakshmi Naidoo"]
CONFUSABLE_LOCALITIES = ["Kukatpally", "KPHB", "Ameerpet", "Begumpet", "Moosapet", "Musheerabad"]
CONFUSABLE_REGS = ["TS09EA4521", "TS09EA4527", "TS09AE4521", "TG09EA4521"]
UNSEEN_NAMES = ["Durga Prasad", "Chandrasekhar", "Sowmya", "Yashwanth Goud", "Bhargavi Chowdary", "Nagendra Babu",
                "Padmavathi", "Hemanth Kumar", "Swathi Varma", "Rambabu"]
UNSEEN_LOCALITIES = {"Hyderabad": ["Dilsukhnagar", "Miyapur", "Gachibowli", "LB Nagar", "Secunderabad", "Uppal"],
                     "Vijayawada": ["Benz Circle", "Patamata", "Governorpet", "Moghalrajpuram"],
                     "Tirupati": ["Alipiri", "Tiruchanur", "Renigunta"],
                     "Warangal": ["Hanamkonda", "Kazipet", "Hunter Road"]}
DATES = [("రేపు", "tomorrow"), ("ఎల్లుండి", "day_after"), ("Saturday", "weekday:5"), ("శనివారం", "weekday:5"),
         ("సోమవారం", "weekday:0"), ("Monday", "weekday:0"), ("గురువారం", "weekday:3")]
TIMES = [("సాయంత్రం ఐదున్నరకి", "17:30"), ("ఉదయం పది గంటలకి", "10:00"), ("five thirty కి", "17:30"),
         ("2:30 కి", "14:30"), ("మధ్యాహ్నం మూడు గంటలకి", "15:00"), ("eleven o'clock కి", "11:00")]
PRICES = [499, 699, 1200, 1899, 3499, 4500, 2750]


def rand_phone(r: random.Random) -> str:
    return r.choice("6789") + "".join(r.choice("0123456789") for _ in range(9))


def rand_reg(r: random.Random) -> str:
    st = r.choice(["TS", "TG", "AP"])
    return f"{st}{r.randint(1, 40):02d}{''.join(r.choice('ABCDEFGHJKLMNPRSTUVWXYZ') for _ in range(r.choice([1, 2])))}{r.randint(1, 9999):04d}"


def spaced_reg(reg: str) -> str:
    import re
    m = re.match(r"([A-Z]{2})(\d{2})([A-Z]+)(\d+)", reg)
    return " ".join(m.groups()) if m else reg


def build(seed: int) -> list[dict]:
    r = random.Random(seed)
    P: list[dict] = []

    def add(text, style, partition, entities, instruction=""):
        P.append({"text": text, "style": style, "partition": partition, "entities": entities, "instruction": instruction})

    for adv in KNOWN["advisors"]:
        add(f"{adv} గారితో మాట్లాడాలి, రేపు ఉంటారా?", "tenglish", "known", [{"type": "person", "value": adv}, {"type": "date", "value": "tomorrow"}])
        add(f"Last time {adv} garu service చేశారు, ఆయనకే ఇవ్వండి", "tenglish", "known", [{"type": "person", "value": adv}])
    for svc in KNOWN["services"]:
        d, dv = r.choice(DATES); t, tv = r.choice(TIMES)
        add(f"{d} {t} {svc} కి slot ఉందా?", "tenglish", "known", [{"type": "service", "value": svc}, {"type": "date", "value": dv}, {"type": "time", "value": tv}])
        add(f"Can I book a {svc.lower()} for {r.choice(['tomorrow', 'Saturday', 'Monday'])} morning?", "english_heavy", "known", [{"type": "service", "value": svc}])
    add("Kukatpally లో మీ Kaveri Auto Care shop ఎక్కడ ఉంది?", "tenglish", "known", [{"type": "locality", "value": "Kukatpally"}, {"type": "business", "value": "Kaveri Auto Care"}])
    for name in CONFUSABLE_NAMES:
        add(f"నా పేరు {name}, నా car ready అయిందా?", "tenglish", "confusable", [{"type": "person", "value": name}])
    for loc in CONFUSABLE_LOCALITIES:
        add(f"మేము {loc} నుంచి, pickup ఇస్తారా?", "tenglish", "confusable", [{"type": "locality", "value": loc}])
    for reg in CONFUSABLE_REGS:
        add(f"Vehicle number {spaced_reg(reg)}, service ఎప్పుడు అవుతుంది?", "tenglish", "confusable", [{"type": "vehicle_reg", "value": reg}])
        add(f"{spaced_reg(reg)} బండి ready అయిందా?", "tenglish", "confusable", [{"type": "vehicle_reg", "value": reg}], "say it fast")
    for _ in range(12):
        name = r.choice(UNSEEN_NAMES); city = r.choice(list(UNSEEN_LOCALITIES)); loc = r.choice(UNSEEN_LOCALITIES[city])
        add(f"నా పేరు {name}, {loc} దగ్గర ఉంటాను", "tenglish", "unseen", [{"type": "person", "value": name}, {"type": "locality", "value": loc}])
    for _ in range(14):
        ph = rand_phone(r)
        add(f"నా number {ph[:5]} {ph[5:]}", "tenglish", "unseen", [{"type": "phone", "value": ph}])
    for _ in range(8):
        ph = rand_phone(r)
        add("నా నంబర్ " + " ".join(TE_DIGITS[int(c)] for c in ph), "telugu", "unseen", [{"type": "phone", "value": ph}], "read the digits naturally")
    for _ in range(8):
        ph = rand_phone(r)
        add(f"{ph}", "tenglish", "unseen", [{"type": "phone", "value": ph}], "say it as fast as you normally would")
    for _ in range(14):
        reg = rand_reg(r)
        add(f"నా vehicle {spaced_reg(reg)}, oil change కావాలి", "tenglish", "unseen", [{"type": "vehicle_reg", "value": reg}, {"type": "service", "value": "Oil change"}])
    for _ in range(10):
        d, dv = r.choice(DATES); t, tv = r.choice(TIMES)
        add(f"{d} {t} రావచ్చా?", "telugu", "unseen", [{"type": "date", "value": dv}, {"type": "time", "value": tv}])
    for _ in range(8):
        p = r.choice(PRICES); svc = r.choice(KNOWN["services"])
        add(f"{svc} కి ₹{p:,} అన్నారు, correct ఏనా?", "tenglish", "unseen", [{"type": "price", "value": p}, {"type": "service", "value": svc}])
    corr = [("Wednesday... కాదు కాదు Thursday వస్తాను", [{"type": "date", "value": "weekday:3"}]),
            ("రేపు... అంటే... ఎల్లుండి వస్తాను అండి", [{"type": "date", "value": "day_after"}]),
            ("ఉదయం పది... సారీ పదకొండు గంటలకి", [{"type": "time", "value": "11:00"}]),
            ("అంటే... ఆ... wheel alignment అనుకుంటా", [{"type": "service", "value": "Wheel alignment"}]),
            ("ఒక్క నిమిషం అండి... ఆ... AC repair కావాలి", [{"type": "service", "value": "AC repair"}])]
    for text, ents in corr:
        add(text, "telugu", "unseen", ents, "include the pauses")
    add("Engine oil change and brake check ఒకే రోజు చేస్తారా?", "tenglish", "known", [{"type": "service", "value": "Oil change"}, {"type": "service", "value": "Brake inspection"}])
    add("మా ఇంట్లో TV sound ఎక్కువగా ఉంది, మీకు వినిపిస్తుందా? రేపు service కావాలి", "tenglish", "unseen", [{"type": "date", "value": "tomorrow"}])
    for i, p in enumerate(P):
        p["id"] = f"P{i+1:03d}"
    return P


CONDITIONS = ["quiet_room", "quiet_room", "handset_outdoors", "speakerphone", "fan_on", "tv_background", "traffic", "car"]


def assign(prompts: list[dict], n_speakers: int, per: int, seed: int) -> dict:
    r = random.Random(seed + 1)
    ids = [p["id"] for p in prompts]
    out = {}
    for s in range(1, n_speakers + 1):
        pick = r.sample(ids, per)
        # 50 prompts in blocks of ~6-7 under different conditions so every speaker covers noise + speakerphone
        blocks = [CONDITIONS[i * len(CONDITIONS) // per] for i in range(per)]
        out[f"SPK{s:02d}"] = [{"n": i + 1, "prompt_id": pid, "condition": blocks[i]} for i, pid in enumerate(pick)]
    return out


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("--seed", type=int, default=20261001)
    a.add_argument("--speakers", type=int, default=20)
    a.add_argument("--per", type=int, default=50)
    x = a.parse_args()
    prompts = build(x.seed)
    root = Path(__file__).resolve().parents[1] / "benchmark/manifests"
    body = "\n".join(json.dumps(p, ensure_ascii=False) for p in prompts) + "\n"
    version = hashlib.sha256(body.encode()).hexdigest()[:12]
    (root / "e3_prompts.jsonl").write_text(body, encoding="utf-8")
    (root / "e3_assignments.json").write_text(json.dumps({"prompt_set_version": version, "seed": x.seed,
        "speakers": assign(prompts, x.speakers, x.per, x.seed)}, ensure_ascii=False, indent=1), encoding="utf-8")
    from collections import Counter
    print(f"prompts={len(prompts)} version={version}", Counter(p["partition"] for p in prompts),
          Counter(e["type"] for p in prompts for e in p["entities"]))
