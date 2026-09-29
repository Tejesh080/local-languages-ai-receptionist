import asyncio, json, os
import pytest
import websockets
from tests.fakes import sarvam_handler
from benchmark import preflight


def test_missing_key_fails_with_reason(monkeypatch):
    monkeypatch.delenv("SARVAM_API_KEY", raising=False)
    r = asyncio.run(preflight.check("sarvam"))
    assert r["status"] == "FAILED" and "SARVAM_API_KEY" in r["reason"]


def test_unreachable_fails_with_reason(monkeypatch):
    monkeypatch.setenv("DEEPGRAM_API_KEY", "x")
    r = asyncio.run(preflight.check("deepgram", host_check=lambda h: f"cannot reach {h}:443 (OSError)"))
    assert r["status"] == "FAILED" and "cannot reach" in r["reason"]


def _with_fake(handler, port):
    os.environ["SARVAM_API_KEY"] = "k"
    os.environ["SARVAM_RT_URL"] = f"ws://127.0.0.1:{port}/speech-to-text-realtime/ws"
    import importlib, benchmark.providers.sarvam_rt as m
    importlib.reload(m)

    async def go():
        async with websockets.serve(handler, "127.0.0.1", port):
            return await preflight.check("sarvam", host_check=lambda h: None)
    return asyncio.run(go())


def test_ready_on_working_adapter():
    r = _with_fake(sarvam_handler(final_delay_ms=50), 8771)
    assert r["status"] == "READY" and r["transcript"] and r["billed_seconds"] > 0


def test_provider_error_fails():
    async def rejecting(ws):
        await ws.send(json.dumps({"event": "error", "code": "invalid_model", "is_fatal": True,
                                  "message": "model not enabled", "status_code": 400}))
    r = _with_fake(rejecting, 8772)
    assert r["status"] == "FAILED" and "invalid_model" in r["reason"]


def test_circuit_breaker_stops_a_broken_config(tmp_path, monkeypatch):
    import wave, hashlib
    from tests.fakes import tone, silence
    from benchmark import run_stt
    items = []
    for i in range(8):
        p = tmp_path / f"u{i}.wav"
        with wave.open(str(p), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(8000); w.writeframes(tone(300) + silence(300))
        sha = hashlib.sha256(p.read_bytes()).hexdigest()
        items.append({"id": f"u{i}", "derived_path": str(p), "derived_sha256": sha, "audio_path": str(p),
                      "raw_sha256": sha, "speech_end_sample": 2400, "region": "telangana"})
    man = tmp_path / "m.jsonl"; man.write_text("\n".join(json.dumps(i) for i in items) + "\n")
    monkeypatch.setattr(run_stt, "ROOT", tmp_path)
    (tmp_path / "benchmark/providers").mkdir(parents=True)
    for f in ("sarvam_rt.py", "deepgram.py"):
        (tmp_path / "benchmark/providers" / f).write_text("x")

    async def always_fail(plan, cfg, kt):
        raise ConnectionRefusedError("bad key")
    monkeypatch.setattr(run_stt, "provider_fn", lambda name: always_fail)
    asyncio.run(run_stt.main(str(man), ["sarvam_v4"], None, 1, "standardized", True))
    run_dir = next((tmp_path / "benchmark/runs").iterdir())
    rows = [json.loads(l) for l in open(run_dir / "results.jsonl")]
    assert len([r for r in rows if r.get("item_id")]) == 5 and rows[-1]["event"] == "config_aborted"
    assert all(r["errors"] for r in rows[:5])                     # failures kept, not dropped
