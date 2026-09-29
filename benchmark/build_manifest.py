"""RAW manifest: one row per recorded utterance, joined with prompt, assignment and speaker metadata.
Nothing is filtered here. Integrity: each file's sha256 is re-computed and compared with the recorder's value.
Usage: python -m benchmark.build_manifest <recordings_dir> <speakers.csv> [out]"""
from __future__ import annotations
import csv, hashlib, json, sys
from pathlib import Path
from benchmark.segments import sha256_file

ROOT = Path(__file__).resolve().parents[1]


def build(recordings_dir: str, speakers_csv: str, out: str = str(ROOT / "benchmark/manifests/e3_raw.jsonl"),
          prompts_path: Path = ROOT / "benchmark/manifests/e3_prompts.jsonl",
          assignments_path: Path = ROOT / "benchmark/manifests/e3_assignments.json") -> tuple[int, str]:
    prompts = {json.loads(l)["id"]: json.loads(l) for l in open(prompts_path, encoding="utf-8")}
    assign = json.load(open(assignments_path, encoding="utf-8"))
    speakers = {r["speaker_code"]: r for r in csv.DictReader(open(speakers_csv, encoding="utf-8"))}
    rows = []
    for sess in sorted(p for p in Path(recordings_dir).iterdir() if (p / "session.jsonl").exists()):
        events = [json.loads(l) for l in open(sess / "session.jsonl", encoding="utf-8")]
        head = next((e for e in events if e["event"] == "session"), {})
        code = head.get("speaker_code", "")
        spk_key = f"SPK{int(code) - 1000:02d}" if code.isdigit() else "unknown"
        plan = {p["n"]: p for p in assign["speakers"].get(spk_key, [])}
        meta = speakers.get(code, {})
        for e in (e for e in events if e["event"] == "utterance"):
            p = plan.get(e["n"], {}); pr = prompts.get(p.get("prompt_id"), {})
            path = sess / e["file"]
            actual = sha256_file(path) if path.exists() else None
            rows.append({
                "id": f"{sess.name}/{e['file']}", "audio_path": str(path), "raw_sha256": actual,
                "recorder_sha256": e.get("sha256"), "session": sess.name, "n": e["n"],
                "prompt_id": p.get("prompt_id"), "text_ref": pr.get("text"), "partition": pr.get("partition"),
                "style": pr.get("style"), "entities": pr.get("entities"), "condition": p.get("condition"),
                "speaker": spk_key, "speaker_code": code, "consent_ref": meta.get("consent_ref"),
                "region": meta.get("region") or "unknown", "gender": meta.get("gender") or "unknown",
                "age_band": meta.get("age_band") or "unknown", "carrier": meta.get("carrier") or "unknown",
                "sample_rate": e.get("sample_rate"), "speech_start_sample": e.get("speech_start_sample"),
                "speech_end_sample": e.get("speech_end_sample"), "file_end_sample": e.get("file_end_sample"),
                "silence_after_speech_ms": e.get("silence_after_speech_ms"), "end_reason": e.get("end_reason"),
                "mark_method": e.get("mark_method"), "speech_in_preroll": e.get("speech_in_preroll"),
                "clipped_peak": e.get("clipped"), "channel": "pstn", "codec": "exotel_pcm16",
                "recorder_params": head.get("params"), "vad": head.get("vad")})
    body = "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n"
    Path(out).write_text(body, encoding="utf-8")
    return len(rows), hashlib.sha256(body.encode()).hexdigest()[:12]


if __name__ == "__main__":
    n, v = build(*sys.argv[1:])
    print(f"{n} raw utterances; raw_manifest_version={v}")
