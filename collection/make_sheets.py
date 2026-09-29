"""Write one printable prompt sheet per speaker (share as PDF/WhatsApp image). Speaker code = 1000 + speaker number."""
from __future__ import annotations
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
COND_TE = {"quiet_room": "నిశ్శబ్ద గది (quiet room)", "handset_outdoors": "బయట, phone చెవి దగ్గర (outdoors)",
           "speakerphone": "Speaker on", "fan_on": "Fan on", "tv_background": "TV on in background",
           "traffic": "Road side / traffic", "car": "Car లో (not driving!)"}


def main():
    prompts = {json.loads(l)["id"]: json.loads(l) for l in open(ROOT / "benchmark/manifests/e3_prompts.jsonl", encoding="utf-8")}
    a = json.load(open(ROOT / "benchmark/manifests/e3_assignments.json", encoding="utf-8"))
    out = ROOT / "collection/sheets"; out.mkdir(exist_ok=True)
    for spk, plan in a["speakers"].items():
        code = 1000 + int(spk[3:])
        L = [f"# Speaker sheet {spk} | Code: {code}", "",
             "Call the recording number. After the double tone type your code then #. Press 1 to agree (consent).",
             "After each beep, read the next line the way you would say it on a normal call. Press # when done (or just pause).",
             "Do not try to speak extra clearly. Pauses, 'ఆ...', 'అంటే...' are fine. Change setting when the heading changes.", ""]
        cur = None
        for p in plan:
            if p["condition"] != cur:
                cur = p["condition"]; L += ["", f"## Setting: {COND_TE[cur]}", ""]
            pr = prompts[p["prompt_id"]]
            L.append(f"{p['n']}. {pr['text']}" + (f"   _({pr['instruction']})_" if pr["instruction"] else ""))
        (out / f"{spk}.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("sheets written:", len(a["speakers"]))


if __name__ == "__main__":
    main()
