"""E4 runner: replay every manifest utterance at real-time pace to each STT config. Results are append-only JSONL.
Every attempt is kept (including errors). A retry is a new row with attempt=2, never a replacement."""
from __future__ import annotations
import argparse, asyncio, datetime as dt, hashlib, json, platform, subprocess, sys, wave
from pathlib import Path
import yaml
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from benchmark.providers import sarvam_rt, deepgram

PROVIDERS = {"sarvam": sarvam_rt.transcribe, "deepgram": deepgram.transcribe}


def known_keyterms() -> list[str]:
    k = yaml.safe_load(open(ROOT / "benchmark/configs/tenant_known_entities.yaml"))
    return [k["business"], k["locality"], *k["advisors"], *k["services"], *k["extra_terms"]]


async def main(manifest: str, configs: list[str] | None, limit: int | None, attempt: int) -> None:
    spec = yaml.safe_load(open(ROOT / "benchmark/configs/e4_stt.yaml"))
    items = [json.loads(l) for l in open(manifest, encoding="utf-8")][:limit]
    run_id = dt.datetime.now().strftime("%Y%m%dT%H%M%S")
    out_dir = ROOT / "benchmark/runs" / run_id; out_dir.mkdir(parents=True)
    kt = known_keyterms()
    prov = {"run_id": run_id, "date": dt.datetime.now(dt.timezone.utc).isoformat(),
            "git_commit": subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=ROOT).stdout.strip(),
            "dataset": manifest, "dataset_version": hashlib.sha256(Path(manifest).read_bytes()).hexdigest()[:12],
            "n_items": len(items), "keyterms": kt, "keyterms_sha": hashlib.sha256("|".join(kt).encode()).hexdigest()[:12],
            "common": spec["common"], "configs": [c for c in spec["configs"] if not configs or c["name"] in configs],
            "python": platform.python_version(), "regions": {}}
    for it in items:
        prov["regions"][it["region"]] = prov["regions"].get(it["region"], 0) + 1
    (out_dir / "run.json").write_text(json.dumps(prov, ensure_ascii=False, indent=1))
    with open(out_dir / "results.jsonl", "a", encoding="utf-8") as f:
        for cfg in prov["configs"]:
            c = {**spec["common"], **cfg}
            for it in items:
                with wave.open(it["audio_path"]) as w:
                    assert w.getframerate() == c["sample_rate"], "resampling is not allowed silently"
                    pcm = w.readframes(w.getnframes())
                try:
                    r = await PROVIDERS[c["provider"]](pcm, c, kt if c.get("keyterms") else [], c["sample_rate"])
                    row = r.__dict__
                except Exception as e:  # noqa: BLE001  recorded, never dropped
                    row = {"transcript": "", "errors": [f"{type(e).__name__}: {e}"]}
                f.write(json.dumps({"run_id": run_id, "config": c["name"], "item_id": it["id"], "attempt": attempt, **row},
                                   ensure_ascii=False) + "\n"); f.flush()
                print(c["name"], it["id"], (row.get("transcript") or "")[:60], row.get("errors"))
    print("results in", out_dir)


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("manifest"); a.add_argument("--configs", nargs="*"); a.add_argument("--limit", type=int)
    a.add_argument("--attempt", type=int, default=1)
    x = a.parse_args(); asyncio.run(main(x.manifest, x.configs, x.limit, x.attempt))
