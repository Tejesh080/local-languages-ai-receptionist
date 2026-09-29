"""Recorder vs a simulated Exotel Voicebot client that streams audio in real time and acknowledges marks."""
import asyncio, base64, importlib, json, os, sys, wave
from pathlib import Path
import pytest
import websockets
from tests.fakes import tone, silence

os.environ["APP_ENV"] = "test"
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "collection/recorder"))
rec = importlib.import_module("exotel_recorder")
rec.P.update(prompts=2, end_silence_ms=300, max_utterance_s=5.0, pre_roll_ms=250, mark_grace_s=1.2, dtmf_timeout_s=5.0)
CHUNK = 1600  # 100 ms at 8 kHz


class FakeExotel:
    def __init__(self, ws, mark_mode="normal", mark_delay=0.8, talk_over_beep=False, stop_during=None):
        self.ws, self.mode, self.delay = ws, mark_mode, mark_delay
        self.talk_over, self.stop_during = talk_over_beep, stop_during
        self.say = asyncio.Queue(); self.play_bytes = 0; self.stopped = False

    async def pump_audio(self):
        buf = b""
        while not self.stopped:
            while len(buf) < CHUNK and not self.say.empty():
                buf += self.say.get_nowait()
            chunk, buf = (buf[:CHUNK], buf[CHUNK:]) if buf else (silence(100), b"")
            chunk = chunk.ljust(CHUNK, b"\x00")
            try:
                await self.ws.send(json.dumps({"event": "media", "media": {"payload": base64.b64encode(chunk).decode()}}))
            except websockets.ConnectionClosed:
                return
            await asyncio.sleep(0.1)

    async def speak(self, ms=600):
        await self.say.put(tone(ms))

    async def dtmf(self, digits):
        for d in digits:
            try:
                await self.ws.send(json.dumps({"event": "dtmf", "dtmf": {"digit": d, "duration": "100"}}))
            except websockets.ConnectionClosed:
                return

    async def on_mark(self, name):
        dur = self.play_bytes / 16000; self.play_bytes = 0
        prompt = name.startswith("p")
        if prompt and self.talk_over:
            await asyncio.sleep(max(0.0, dur - 0.2)); await self.speak(); dur = 0.2
        if self.mode == "missing":
            await asyncio.sleep(dur + rec.P["mark_grace_s"] + 0.1)
        else:
            await asyncio.sleep(dur + (self.delay if self.mode == "delayed" else 0.0))
            try:
                await self.ws.send(json.dumps({"event": "mark", "mark": {"name": name}}))
            except websockets.ConnectionClosed:
                return
        if name.startswith("intro"):
            await self.dtmf("1001#")
        elif name.startswith("consent"):
            await self.dtmf("1#")
        elif prompt and not self.talk_over:
            await self.speak()                                   # caller starts IMMEDIATELY after the beep
            if self.stop_during and name.startswith(self.stop_during):
                await asyncio.sleep(0.3)
                await self.ws.send(json.dumps({"event": "stop", "stop": {"reason": "callended"}}))
                self.stopped = True

    async def run(self):
        await self.ws.send(json.dumps({"event": "connected"}))
        await self.ws.send(json.dumps({"event": "start", "stream_sid": "MZ1", "start": {"stream_sid": "MZ1", "call_sid": "CA1",
                               "from": "+919000000101", "to": "+918000000000", "media_format": {"sample_rate": "8000"}}}))
        pump = asyncio.create_task(self.pump_audio())
        try:
            async for msg in self.ws:
                ev = json.loads(msg)
                if ev["event"] == "media":
                    self.play_bytes += len(base64.b64decode(ev["media"]["payload"]))
                elif ev["event"] == "mark":
                    asyncio.create_task(self.on_mark(ev["mark"]["name"]))
        except websockets.ConnectionClosed:
            pass
        self.stopped = True; await pump


def _session(tmp_path, port, **kw):
    async def go():
        async with websockets.serve(lambda ws: rec.handler(ws, str(tmp_path)), "127.0.0.1", port):
            async with websockets.connect(f"ws://127.0.0.1:{port}") as ws:
                await FakeExotel(ws, **kw).run()
        await asyncio.sleep(0.2)
    asyncio.run(asyncio.wait_for(go(), 40))
    d = next(tmp_path.iterdir())
    lines = [json.loads(l) for l in open(d / "session.jsonl")]
    return d, lines, [l for l in lines if l["event"] == "utterance"]


def _checks(d, utts):
    master = (d / "session_raw.wav").read_bytes()
    for u in utts:
        assert u["speech_end_sample"] < u["file_end_sample"]               # trailing silence exists and is measured
        assert u["silence_after_speech_ms"] >= rec.P["end_silence_ms"] - 40
        with wave.open(str(d / u["file"])) as w:
            pcm = w.readframes(w.getnframes())
        with wave.open(str(d / "session_raw.wav")) as w:
            full = w.readframes(w.getnframes())
        assert pcm == full[u["window_start_sample"] * 2:u["window_end_sample"] * 2]   # exact slice of the master
        assert not os.access(d / u["file"], os.W_OK) or os.geteuid() == 0              # read-only (root bypasses)


def test_normal_mark_and_immediate_speech(tmp_path):
    d, lines, utts = _session(tmp_path, 5101)
    assert lines[0]["speaker_code"] == "1001" and lines[0]["consent_dtmf"] == "1" and "from" not in lines[0]
    assert [u["mark_method"] for u in utts] == ["ack", "ack"]
    pre = (8000 * rec.P["pre_roll_ms"] // 1000) // 160 * 160
    for u in utts:   # speech began right after the mark and was not lost
        assert u["speech_start_sample"] is not None and pre - 400 <= u["speech_start_sample"] <= pre + 1600
        assert not u["speech_in_preroll"]
    _checks(d, utts)
    assert lines[-1]["event"] == "session_end" and lines[-1]["outcome"] == "completed"


def test_delayed_mark_waits_for_ack(tmp_path):
    d, _, utts = _session(tmp_path, 5102, mark_mode="delayed", mark_delay=0.8)
    assert [u["mark_method"] for u in utts] == ["ack", "ack"]
    assert all(u["mark_wait_ms"] >= 250 + 800 - 150 for u in utts)          # did not start on local sleep expiry
    _checks(d, utts)


def test_missing_mark_falls_back_to_timeout(tmp_path):
    d, _, utts = _session(tmp_path, 5103, mark_mode="missing")
    assert [u["mark_method"] for u in utts] == ["timeout", "timeout"] and len(utts) == 2
    assert all(u["speech_end_sample"] is not None for u in utts)
    _checks(d, utts)


def test_caller_talking_over_beep_is_flagged(tmp_path):
    d, _, utts = _session(tmp_path, 5104, mark_mode="delayed", mark_delay=0.0, talk_over_beep=True)
    assert any(u["speech_in_preroll"] for u in utts)


def test_stop_mid_session(tmp_path):
    d, lines, utts = _session(tmp_path, 5105, stop_during="p1")
    end = lines[-1]
    assert end["event"] == "session_end" and end["outcome"] == "call_ended" and end["stop_reason"] == "callended"
    assert len(utts) == 1 and utts[0]["end_reason"] == "call_ended"
    assert (d / "session_raw.wav").exists()
