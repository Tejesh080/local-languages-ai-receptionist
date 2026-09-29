"""E4 runner. Replays each analysis-manifest item at real-time pace with speech-end ground truth (decision 0002).
- Requires a READY preflight (<24 h) for every provider used, unless --skip-preflight-check.
- Verifies audio sha256 against the manifest before sending (raw/derived immutability).
- Circuit breaker: if the first 5 attempts of a config all error, that config is aborted with one explicit row.
- Every attempt is kept. A retry is a new row with attempt=N, never a replacement."""
from __future__ import annotations
import argparse, asyncio, datetime as dt, hashlib, json, platform, subprocess, sys
from pathlib import Path
import websockets
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from benchmark.stt_common import load_spec, known_keyterms, provider_fn
from benchmark.replay import make_plan
from benchmark.segments import read_pcm, sha256_file
from benchmark.preflight import latest_ready
from audio.vad import VadParams
from entities import normalization_version

BREAKER_N = 5


def _sha(p: Path) -> str:
    return sha256_file(p)[:12]


async def main(manifest: str, configs: list[str] | None, limit: int | None, attempt: int, replay: str, skip_preflight: bool) -> None:
    spec = load_spec()
    chosen = [c for c in spec["configs"] if not configs or c["name"] in configs]
    if not skip_preflight:
        ok, why = latest_ready({c["provider"] for c in chosen})
        if not ok:
            raise SystemExit(f"Preflight not satisfied ({why}). Run: python -m benchmark.preflight")
    items = [json.loads(l) for l in open(manifest, encoding="utf-8")][:limit]
    run_id = dt.datetime.now().strftime("%Y%m%dT%H%M%S")
    out_dir = ROOT / "benchmark/runs" / run_id; out_dir.mkdir(parents=True)
    kt = known_keyterms()
    prov = {"run_id": run_id, "date": dt.datetime.now(dt.timezone.utc).isoformat(),
            "git_commit": subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=ROOT).stdout.strip(),
            "git_dirty": bool(subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, cwd=ROOT).stdout.strip()),
            "dataset": manifest, "dataset_version": hashlib.sha256(Path(manifest).read_bytes()).hexdigest()[:12],
            "n_items": len(items), "replay": replay, "keyterms": kt,
            "keyterms_sha": hashlib.sha256("|".join(kt).encode()).hexdigest()[:12], "common": spec["common"], "configs": chosen,
            "normalization_version": normalization_version(), "vad": VadParams().as_dict(),
            "adapters": {p: _sha(ROOT / f"benchmark/providers/{f}") for p, f in (("sarvam", "sarvam_rt.py"), ("deepgram", "deepgram.py"))},
            "python": platform.python_version(), "websockets": websockets.__version__, "regions": {}}
    for it in items:
        prov["regions"][it.get("region", "unknown")] = prov["regions"].get(it.get("region", "unknown"), 0) + 1
    (out_dir / "run.json").write_text(json.dumps(prov, ensure_ascii=False, indent=1))
    with open(out_dir / "results.jsonl", "a", encoding="utf-8") as f:
        for cfg in chosen:
            c = {**spec["common"], **cfg}
            fn = provider_fn(c["provider"])
            errors_in_a_row = 0
            for i, it in enumerate(items):
                path = Path(it["derived_path"] if replay == "standardized" else it["audio_path"])
                want = it["derived_sha256"] if replay == "standardized" else it["raw_sha256"]
                if sha256_file(path) != want:
                    raise SystemExit(f"{path}: sha256 mismatch with manifest. Audio was modified; aborting run.")
                pcm, rate = read_pcm(path)
                if rate != c["sample_rate"]:
                    raise SystemExit(f"{path}: {rate} Hz, config expects {c['sample_rate']} Hz")
                plan = make_plan(pcm, rate, c["chunk_ms"], it["speech_end_sample"])
                try:
                    r = (await fn(plan, c, kt if c.get("keyterms") else [])).__dict__
                except Exception as e:  # noqa: BLE001  recorded, never dropped
                    r = {"transcript": "", "errors": [f"{type(e).__name__}: {e}"[:300]]}
                f.write(json.dumps({"run_id": run_id, "config": c["name"], "item_id": it["id"], "attempt": attempt, **r},
                                   ensure_ascii=False) + "\n"); f.flush()
                errors_in_a_row = errors_in_a_row + 1 if r.get("errors") else 0
                print(c["name"], it["id"], (r.get("transcript") or "")[:50], r.get("errors") or "", r.get("final_after_speech_end_ms"))
                if i + 1 == errors_in_a_row == BREAKER_N:
                    f.write(json.dumps({"run_id": run_id, "config": c["name"], "item_id": None, "event": "config_aborted",
                                        "reason": f"first {BREAKER_N} attempts all failed; fix the adapter/setup (see smoke/preflight)"}) + "\n")
                    print(f"ABORTED {c['name']}: first {BREAKER_N} attempts failed")
                    break
    print("results in", out_dir)


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("manifest", help="analysis manifest from benchmark/quality.py")
    a.add_argument("--configs", nargs="*"); a.add_argument("--limit", type=int); a.add_argument("--attempt", type=int, default=1)
    a.add_argument("--replay", choices=["standardized", "exact"], default="standardized")
    a.add_argument("--skip-preflight-check", action="store_true")
    x = a.parse_args(); asyncio.run(main(x.manifest, x.configs, x.limit, x.attempt, x.replay, x.skip_preflight_check))
