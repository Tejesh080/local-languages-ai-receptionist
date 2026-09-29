"""Join recorder output (session.jsonl + wav) with speaker assignments and prompts into a versioned manifest.
Speaker metadata (region, gender, age band, carrier, handset) comes from the consent/registration sheet CSV."""
from __future__ import annotations
import csv, hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main(recordings_dir: str, speakers_csv: str, out: str = "benchmark/manifests/e3_dataset.jsonl") -> None:
    prompts = {json.loads(l)["id"]: json.loads(l) for l in open(ROOT / "benchmark/manifests/e3_prompts.jsonl", encoding="utf-8")}
    assign = json.load(open(ROOT / "benchmark/manifests/e3_assignments.json", encoding="utf-8"))
    speakers = {r["speaker_code"]: r for r in csv.DictReader(open(speakers_csv, encoding="utf-8"))}
    rows = []
    for sess in sorted(Path(recordings_dir).iterdir()):
        events = [json.loads(l) for l in open(sess / "session.jsonl", encoding="utf-8")]
        head = next(e for e in events if e["event"] == "session")
        code = head["speaker_code"]; spk_key = f"SPK{int(code) - 1000:02d}"
        plan = {p["n"]: p for p in assign["speakers"].get(spk_key, [])}
        meta = speakers.get(code, {})
        for e in (e for e in events if e["event"] == "utterance"):
            p = plan.get(e["n"]); pr = prompts.get(p["prompt_id"]) if p else None
            if not pr:
                continue
            rows.append({"id": f"{sess.name}/{e['file']}", "audio_path": str(sess / e["file"]), "prompt_id": pr["id"],
                         "text_ref": pr["text"], "partition": pr["partition"], "style": pr["style"], "entities": pr["entities"],
                         "condition": p["condition"], "speaker": spk_key, "region": meta.get("region", "unknown"),
                         "gender": meta.get("gender", "unknown"), "age_band": meta.get("age_band", "unknown"),
                         "carrier": meta.get("carrier", "unknown"), "seconds": e["seconds"], "end_reason": e["end_reason"],
                         "clipped": e["clipped"], "channel": "pstn", "codec": "exotel_pcm16_8k",
                         "session_date": sess.name[:8]})
    body = "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n"
    Path(out).write_text(body, encoding="utf-8")
    print(f"{len(rows)} utterances; dataset_version={hashlib.sha256(body.encode()).hexdigest()[:12]}")


if __name__ == "__main__":
    main(*sys.argv[1:])
