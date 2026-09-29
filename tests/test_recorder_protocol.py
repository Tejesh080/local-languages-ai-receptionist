import asyncio, base64, json, math, os, struct, importlib, shutil, sys
from pathlib import Path
import websockets


def test_recorder_session(tmp_path):
    os.environ["RECORDINGS_DIR"] = str(tmp_path); os.environ["PROMPTS_PER_SESSION"] = "2"
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "collection/recorder"))
    rec = importlib.import_module("exotel_recorder"); importlib.reload(rec)
    rec.END_SIL_MS = 300

    async def run():
        async with websockets.serve(rec.handler, "127.0.0.1", 5099):
            async with websockets.connect("ws://127.0.0.1:5099") as ws:
                await ws.send(json.dumps({"event": "connected"}))
                await ws.send(json.dumps({"event": "start", "stream_sid": "MZ1", "start": {"stream_sid": "MZ1", "call_sid": "CA1",
                                          "from": "+919000000101", "to": "+918000000000", "media_format": {"sample_rate": "8000"}}}))
                async def dt(d):
                    await ws.send(json.dumps({"event": "dtmf", "dtmf": {"digit": d}}))
                await asyncio.sleep(0.6)
                for d in "1001#": await dt(d)
                await asyncio.sleep(0.4); await dt("1"); await dt("#")
                speech = b"".join(struct.pack("<h", int(8000 * math.sin(2 * math.pi * 300 * i / 8000))) for i in range(3200))
                sil = b"\x00\x00" * 3200
                for _ in range(2):
                    await asyncio.sleep(0.4)
                    for chunk in (sil[:1600], speech, sil, sil):
                        await ws.send(json.dumps({"event": "media", "media": {"payload": base64.b64encode(chunk).decode()}}))
                        await asyncio.sleep(0.05)
                    await asyncio.sleep(0.5)
                await asyncio.sleep(1.0)
                try:
                    await ws.send(json.dumps({"event": "stop", "stop": {"reason": "callended"}}))
                except websockets.ConnectionClosed:
                    pass  # recorder hangs up itself after the last prompt
    asyncio.run(asyncio.wait_for(run(), 20))
    sess = next(tmp_path.iterdir())
    lines = [json.loads(l) for l in open(sess / "session.jsonl")]
    assert lines[0]["speaker_code"] == "1001" and lines[0]["consent_dtmf"] == "1"
    assert "from" not in lines[0] and len(lines[0]["from_hash"]) == 16
    assert sum(1 for l in lines if l["event"] == "utterance") == 2
