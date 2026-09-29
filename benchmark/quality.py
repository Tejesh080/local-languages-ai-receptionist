"""E3 data-quality gate -> dataset-quality-report.md + analysis manifest (+ derived segments, methodology B).
Rules: flag, never silently drop. An item leaves the analysis only via an exclusions.csv row WITH a reason.
Blocking flags must each be resolved by an explicit exclusion before the analysis manifest is written.
Usage: python -m benchmark.quality <raw_manifest> [--exclusions exclusions.csv] [--trailing-ms 1500]"""
from __future__ import annotations
import argparse, array, csv, datetime as dt, hashlib, json, re, wave
from pathlib import Path
from audio.vad import speech_bounds, VadParams
from benchmark.segments import derive, DERIVATION_VERSION
from entities import normalization_version
from entities.normalize import normalize_phone, normalize_vehicle_reg

ROOT = Path(__file__).resolve().parents[1]
PARTITIONS = {"known", "confusable", "unseen"}
CONDITIONS = {"quiet_room", "handset_outdoors", "speakerphone", "fan_on", "tv_background", "traffic", "car"}
ENTITY_TYPES = {"phone", "vehicle_reg", "date", "time", "price", "person", "locality", "service", "business"}


def entity_problem(e: dict) -> str | None:
    t, v = e.get("type"), e.get("value")
    if t not in ENTITY_TYPES:
        return f"unknown entity type {t}"
    if t == "phone" and normalize_phone(str(v)) != v:
        return f"invalid phone {v}"
    if t == "vehicle_reg" and normalize_vehicle_reg(str(v)) != v:
        return f"invalid registration {v}"
    if t == "date" and not re.fullmatch(r"tomorrow|day_after|weekday:[0-6]", str(v)):
        return f"invalid date label {v}"
    if t == "time" and not re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", str(v)):
        return f"invalid time {v}"
    if t == "price" and not (isinstance(v, int) and v > 0):
        return f"invalid price {v}"
    return None


def check(item: dict) -> list[tuple[str, str]]:
    """Return [(severity, code)] with severity in blocking | warn | info."""
    f: list[tuple[str, str]] = []
    p = Path(item["audio_path"])
    if not p.exists():
        return [("blocking", "file_missing")]
    if item.get("raw_sha256") != item.get("recorder_sha256"):
        f.append(("blocking", "sha_mismatch_raw_modified"))
    with wave.open(str(p)) as w:
        rate, ch, sw, nfr = w.getframerate(), w.getnchannels(), w.getsampwidth(), w.getnframes()
        pcm = w.readframes(nfr)
    if rate != 8000: f.append(("blocking", f"sample_rate_{rate}"))
    if ch != 1: f.append(("blocking", f"channels_{ch}"))
    if sw != 2: f.append(("blocking", f"sample_width_{sw}"))
    dur = nfr / rate if rate else 0
    if nfr == 0: f.append(("blocking", "empty"))
    elif dur < 0.5: f.append(("blocking", f"too_short_{dur:.2f}s"))
    elif dur > 16: f.append(("warn", f"long_{dur:.1f}s"))
    if sw == 2 and ch == 1 and nfr:
        a = array.array("h", pcm)
        clip = sum(1 for x in a if abs(x) >= 32000) / len(a)
        if clip > 0.01: f.append(("warn", f"clipped_{clip:.1%}"))
        b = speech_bounds(pcm, rate, VadParams())
        if b.end_sample is None: f.append(("blocking", "no_speech_detected"))
        elif b.speech_ratio < 0.15: f.append(("warn", f"mostly_silence_{b.speech_ratio:.0%}"))
        if item.get("speech_end_sample") is None: f.append(("blocking", "recorder_speech_end_missing"))
        elif b.end_sample is not None and abs(b.end_sample - item["speech_end_sample"]) > rate * VadParams().frame_ms // 1000:
            f.append(("warn", "offline_vad_disagrees_with_recorder"))
    if not item.get("prompt_id") or not item.get("text_ref"): f.append(("blocking", "prompt_missing"))
    if item.get("partition") not in PARTITIONS: f.append(("blocking", f"partition_{item.get('partition')}"))
    if item.get("condition") not in CONDITIONS: f.append(("blocking", f"condition_{item.get('condition')}"))
    for e in item.get("entities") or []:
        prob = entity_problem(e)
        if prob: f.append(("blocking", "entity_" + prob.replace(" ", "_")))
    if any(item.get(k) in (None, "", "unknown") for k in ("region", "gender", "age_band", "carrier")):
        f.append(("warn", "speaker_metadata_missing"))
    if not item.get("consent_ref"): f.append(("blocking", "consent_ref_missing"))
    if item.get("end_reason") in ("max_len", "call_ended"): f.append(("warn", f"end_reason_{item['end_reason']}"))
    if item.get("speech_in_preroll"): f.append(("warn", "speech_started_before_beep_finished"))
    if item.get("mark_method") == "timeout": f.append(("info", "mark_timeout_fallback"))
    return f


def load_exclusions(path: str | None) -> dict[str, dict]:
    if not path or not Path(path).exists():
        return {}
    out = {}
    for r in csv.DictReader(open(path, encoding="utf-8")):
        if not (r.get("reason") or "").strip() or not (r.get("excluded_by") or "").strip():
            raise SystemExit(f"exclusion for {r.get('item_id')} has no reason/excluded_by; every exclusion needs both")
        out[r["item_id"]] = r
    return out


def run(raw_manifest: str, exclusions: str | None, trailing_ms: int, out_dir: str | None = None) -> dict:
    out = Path(out_dir or ROOT / "benchmark/manifests")
    items = [json.loads(l) for l in open(raw_manifest, encoding="utf-8")]
    excl = load_exclusions(exclusions)
    results = {it["id"]: check(it) for it in items}
    unresolved = [i for i, fl in results.items() if any(s == "blocking" for s, _ in fl) and i not in excl]
    counts: dict[str, int] = {}
    for fl in results.values():
        for s, c in fl:
            k = f"{s}:{re.sub(r'_[0-9.%]+s?$', '', c)}"; counts[k] = counts.get(k, 0) + 1
    raw_v = hashlib.sha256(Path(raw_manifest).read_bytes()).hexdigest()[:12]
    L = [f"# Dataset quality report ({dt.date.today()}, raw manifest {raw_v})", "",
         f"Items: {len(items)} | with any flag: {sum(1 for f in results.values() if f)} | explicitly excluded: {len(excl)} | "
         f"blocking and unresolved: {len(unresolved)}", "", "## Flag counts", ""] + \
        [f"- {k}: {v}" for k, v in sorted(counts.items())] + ["", "## Items by flag", ""]
    for i, fl in results.items():
        if fl:
            L.append(f"- `{i}`: " + ", ".join(f"{s}:{c}" for s, c in fl) + (f"  **EXCLUDED** ({excl[i]['reason']})" if i in excl else ""))
    status = {"raw_manifest_version": raw_v, "unresolved_blocking": unresolved}
    if unresolved:
        sugg = out / "suggested_exclusions.csv"
        with open(sugg, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh); w.writerow(["item_id", "reason", "excluded_by", "date"])
            for i in unresolved:
                w.writerow([i, "; ".join(c for s, c in results[i] if s == "blocking"), "", dt.date.today().isoformat()])
        L += ["", f"**Analysis manifest NOT written:** {len(unresolved)} blocking items need an explicit decision. "
              f"Review {sugg.name}, fill `excluded_by`, save as exclusions.csv, re-run."]
    else:
        rows = []
        for it in items:
            if it["id"] in excl:
                continue
            d = derive(it["audio_path"], it["speech_end_sample"], trailing_ms, str(ROOT / "benchmark/derived"))
            rows.append({**it, **d, "quality_flags": [f"{s}:{c}" for s, c in results[it["id"]]],
                         "normalization_version": normalization_version(), "derivation": DERIVATION_VERSION})
        body = "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n"
        (out / "e3_analysis.jsonl").write_text(body, encoding="utf-8")
        status["analysis_version"] = hashlib.sha256(body.encode()).hexdigest()[:12]
        status["n_analysis"] = len(rows)
        L += ["", f"Analysis manifest: {len(rows)} items, version {status['analysis_version']}, "
              f"derivation {DERIVATION_VERSION} trailing {trailing_ms} ms, {normalization_version()}."]
    (out / "dataset-quality-report.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    return status


if __name__ == "__main__":
    a = argparse.ArgumentParser(); a.add_argument("raw_manifest"); a.add_argument("--exclusions")
    a.add_argument("--trailing-ms", type=int, default=1500)
    x = a.parse_args()
    print(json.dumps(run(x.raw_manifest, x.exclusions, x.trailing_ms), indent=1))
