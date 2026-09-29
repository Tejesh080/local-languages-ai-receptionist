"""Provider preflight: key present -> endpoint reachable -> config accepted -> tiny fixture transcribes.
Usage: python -m benchmark.preflight [--providers sarvam deepgram]. Writes benchmark/runs/preflight/<ts>.json."""
from __future__ import annotations
import argparse, asyncio, datetime as dt, json, os, socket
from pathlib import Path
from benchmark.stt_common import ROOT, FIXTURE, KEY_ENV, HOSTS, config, transcribe_file

PREFLIGHT_CONFIG = {"sarvam": "sarvam_v4", "deepgram": "deepgram_nova3_te"}
OUT = ROOT / "benchmark/runs/preflight"


def reachable(host: str, port: int = 443, timeout: float = 5.0) -> str | None:
    try:
        socket.create_connection((host, port), timeout).close()
        return None
    except OSError as e:
        return f"cannot reach {host}:{port} ({type(e).__name__})"


async def check(provider: str, host_check=reachable) -> dict:
    cfg_name = PREFLIGHT_CONFIG[provider]
    if not os.environ.get(KEY_ENV[provider]):
        return {"provider": provider, "status": "FAILED", "reason": f"{KEY_ENV[provider]} not set"}
    err = host_check(HOSTS[provider])
    if err:
        return {"provider": provider, "status": "FAILED", "reason": err}
    try:
        r = await asyncio.wait_for(transcribe_file(config(cfg_name), str(FIXTURE)), 60)
    except Exception as e:  # noqa: BLE001
        return {"provider": provider, "status": "FAILED", "reason": f"{type(e).__name__}: {e}"[:300]}
    if r.errors:
        return {"provider": provider, "status": "FAILED", "reason": "provider errors: " + "; ".join(r.errors)[:300]}
    if not r.transcript:
        return {"provider": provider, "status": "FAILED", "reason": "connected but empty transcript on the fixture"}
    return {"provider": provider, "status": "READY", "config": cfg_name, "transcript": r.transcript, "session": r.session,
            "billed_seconds": r.billed_seconds, "final_after_speech_end_ms": r.final_after_speech_end_ms}


def latest_ready(providers: set[str], max_age_h: float = 24) -> tuple[bool, str]:
    files = sorted(OUT.glob("*.json"))
    if not files:
        return False, "no preflight has been run"
    rep = json.loads(files[-1].read_text())
    age = dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(rep["at"])
    if age.total_seconds() > max_age_h * 3600:
        return False, f"latest preflight is {age} old"
    status = {r["provider"]: r["status"] for r in rep["results"]}
    missing = [p for p in providers if status.get(p) != "READY"]
    return (not missing), ("ok" if not missing else f"not READY: {missing}")


def main() -> int:
    a = argparse.ArgumentParser(); a.add_argument("--providers", nargs="*", default=["sarvam", "deepgram"])
    x = a.parse_args()
    results = [asyncio.run(check(p)) for p in x.providers]
    OUT.mkdir(parents=True, exist_ok=True)
    at = dt.datetime.now(dt.timezone.utc)
    (OUT / f"{at:%Y%m%dT%H%M%S}.json").write_text(json.dumps({"at": at.isoformat(), "results": results}, ensure_ascii=False, indent=1))
    for r in results:
        print(f"{r['provider']:9s} {r['status']}" + (f"  ({r['reason']})" if r["status"] != "READY" else f"  transcript: {r['transcript'][:60]}"))
    return 0 if all(r["status"] == "READY" for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
