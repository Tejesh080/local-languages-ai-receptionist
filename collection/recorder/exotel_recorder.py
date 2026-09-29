"""E3 phone recorder over Exotel's Voicebot WebSocket.

VERIFIED from developer.exotel.com AgentStream WebSocket protocol (2026-09-30):
  inbound events connected/start/media/dtmf/mark/stop; outbound media/mark/clear; PCM16 mono, 8 kHz default;
  outbound chunks 3,200-100,000 bytes and multiples of 320; inbound `mark` is "sent when audio you previously sent
  has finished playing"; max session 60 min.
INFERRED (not stated in docs): the mark echoes the same `name` we sent; media arrives in order and continuously
  (~100 ms) during our playback. Both are logged per prompt (mark_method) so violations are visible in the data.

Data model (decision 0002): the entire inbound stream is kept as session_raw.wav (immutable master). Each utterance
file is an exact byte slice of it; nothing is trimmed or modified. Speech timing is stored as sample indices.
"""
from __future__ import annotations
import array, asyncio, base64, datetime as dt, hashlib, json, math, os, stat, struct, sys, wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from audio.vad import speech_bounds, VadParams  # noqa: E402

AUDIO_DIR = Path(__file__).parent / "audio"
RATE = 8000
P = {  # tunables (tests override); stored into every session file
    "prompts": int(os.environ.get("PROMPTS_PER_SESSION", "50")),
    "end_silence_ms": 1500, "max_utterance_s": 15.0, "pre_roll_ms": 250, "mark_grace_s": 2.0, "dtmf_timeout_s": 20.0,
}
VAD = VadParams()
_PLACEHOLDER_SALTS = {"", "change-me", "changeme", "secret", "salt", "test"}


def _salt() -> str:
    s = os.environ.get("PHONE_HASH_SALT", "")
    if os.environ.get("APP_ENV", "production") != "test" and (s.lower() in _PLACEHOLDER_SALTS or len(s) < 16):
        raise SystemExit("PHONE_HASH_SALT missing or weak; refusing to record (set APP_ENV=test only for tests)")
    return s


def tone(freq: float, ms: int, vol: float = 0.3) -> bytes:
    return b"".join(struct.pack("<h", int(vol * 32767 * math.sin(2 * math.pi * freq * i / RATE))) for i in range(RATE * ms // 1000))


BEEP = tone(1000, 250)
DOUBLE = tone(800, 150) + b"\x00\x00" * 800 + tone(800, 150)


def wav_bytes(name: str) -> bytes | None:
    p = AUDIO_DIR / name
    if not p.exists():
        return None
    with wave.open(str(p)) as w:
        assert w.getframerate() == RATE and w.getnchannels() == 1 and w.getsampwidth() == 2, f"{name} must be 8k mono 16-bit"
        return w.readframes(w.getnframes())


def _peak(b: bytes) -> int:
    return max((abs(x) for x in array.array("h", b)), default=0)


class Session:
    def __init__(self, ws, salt: str):
        self.ws, self.salt, self.sid = ws, salt, None
        self.pcm = bytearray()                       # master: every inbound sample, in order
        self.new_audio = asyncio.Event()
        self.marks: dict[str, tuple[asyncio.Event, list[int]]] = {}
        self.dtmf: asyncio.Queue[tuple[str, int]] = asyncio.Queue()
        self.stopped = asyncio.Event()
        self.stop_reason: str | None = None
        self.meta: dict = {}
        self.seq = 0

    @property
    def n(self) -> int:
        return len(self.pcm) // 2

    async def reader(self):
        try:
            async for msg in self.ws:
                ev = json.loads(msg)
                kind = ev.get("event")
                if kind == "start":
                    st = ev["start"]; self.sid = st["stream_sid"]
                    self.meta = {"call_sid": st.get("call_sid"), "to": st.get("to"),
                                 "from_hash": hashlib.sha256((self.salt + "|" + (st.get("from") or "")).encode()).hexdigest()[:16],
                                 "media_format": st.get("media_format")}
                elif kind == "media":
                    self.pcm += base64.b64decode(ev["media"]["payload"]); self.new_audio.set()
                elif kind == "mark":
                    name = (ev.get("mark") or {}).get("name", "")
                    if name in self.marks:
                        e, at = self.marks[name]; at.append(self.n); e.set()
                elif kind == "dtmf":
                    await self.dtmf.put(((ev.get("dtmf") or {}).get("digit", ""), self.n))
                elif kind == "stop":
                    self.stop_reason = (ev.get("stop") or {}).get("reason", "stop"); break
        finally:
            self.stopped.set(); self.new_audio.set()

    async def play(self, pcm: bytes, label: str) -> dict:
        """Send audio then a mark; wait for Exotel's mark (= playback finished). Timeout fallback is recorded."""
        self.seq += 1
        name = f"{label}-{self.seq}"
        ev = asyncio.Event(); at: list[int] = []
        self.marks[name] = (ev, at)
        pcm = pcm + b"\x00" * ((-len(pcm)) % 3200)
        sent_at = self.n
        for i in range(0, len(pcm), 3200):
            await self.ws.send(json.dumps({"event": "media", "stream_sid": self.sid,
                                           "media": {"payload": base64.b64encode(pcm[i:i + 3200]).decode()}}))
        await self.ws.send(json.dumps({"event": "mark", "stream_sid": self.sid, "mark": {"name": name}}))
        dur = len(pcm) / (2 * RATE)
        waiter = asyncio.create_task(ev.wait()); stopper = asyncio.create_task(self.stopped.wait())
        done, _ = await asyncio.wait({waiter, stopper}, timeout=dur + P["mark_grace_s"], return_when=asyncio.FIRST_COMPLETED)
        for t in (waiter, stopper):
            t.cancel()
        if ev.is_set():
            method, sample = "ack", at[0]
        elif self.stopped.is_set():
            method, sample = "stopped", self.n
        else:
            method, sample = "timeout", self.n
        return {"mark_name": name, "mark_method": method, "sent_sample": sent_at, "mark_sample": sample,
                "mark_wait_ms": round((sample - sent_at) / RATE * 1000)}

    async def read_digits(self, terminator="#") -> str:
        s = ""
        while True:
            try:
                d, _ = await asyncio.wait_for(self.dtmf.get(), P["dtmf_timeout_s"])
            except asyncio.TimeoutError:
                return s
            if d == terminator:
                return s
            s += d

    async def record_utterance(self, mark_sample: int, prev_end: int) -> dict:
        frame = RATE * VAD.frame_ms // 1000
        pre_roll = (RATE * P["pre_roll_ms"] // 1000) // frame * frame      # whole VAD frames: frames align with the mark
        start = max(prev_end, mark_sample - pre_roll)
        end_sil = RATE * P["end_silence_ms"] // 1000
        max_n = int(RATE * P["max_utterance_s"])
        while True:
            if self.stopped.is_set():
                reason = "call_ended"; break
            while not self.dtmf.empty():
                d, at = self.dtmf.get_nowait()
                if d == "#" and at >= mark_sample:
                    reason = "dtmf"; break
            else:
                window = bytes(self.pcm[start * 2:self.n * 2])
                b = speech_bounds(window, RATE, VAD)
                if b.end_sample is not None and (self.n - start - b.end_sample) >= end_sil:
                    reason = "silence"; break
                if self.n - mark_sample >= max_n:
                    reason = "max_len"; break
                self.new_audio.clear()
                try:
                    await asyncio.wait_for(self.new_audio.wait(), 1.0)
                except asyncio.TimeoutError:
                    pass
                continue
            break
        end = self.n
        window = bytes(self.pcm[start * 2:end * 2])
        b = speech_bounds(window, RATE, VAD)
        pre = mark_sample - start
        return {"window_start_sample": start, "window_end_sample": end, "end_reason": reason,
                "speech_start_sample": b.start_sample, "speech_end_sample": b.end_sample, "file_end_sample": end - start,
                "speech_ratio": round(b.speech_ratio, 3),
                "silence_after_speech_ms": round((end - start - b.end_sample) / RATE * 1000) if b.end_sample is not None else None,
                # tolerance of one frame covers alignment when prev_end (not the pre-roll) set the window start
                "speech_in_preroll": b.start_sample is not None and b.start_sample < pre - frame,
                "clipped": _peak(window) >= 32000}


def _write(path: Path, pcm: bytes) -> str:
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE); w.writeframes(pcm)
    os.chmod(path, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)          # raw data is read-only after writing
    return hashlib.sha256(path.read_bytes()).hexdigest()


async def handler(ws, out_root: str | None = None):
    s = Session(ws, _salt())
    rtask = asyncio.create_task(s.reader())
    while s.sid is None and not s.stopped.is_set():
        await asyncio.sleep(0.02)
    started = dt.datetime.now(dt.timezone.utc)
    sess_dir = Path(out_root or os.environ.get("RECORDINGS_DIR", "collection/recordings")) / f"{started:%Y%m%dT%H%M%S}_{s.meta.get('call_sid')}"
    sess_dir.mkdir(parents=True, exist_ok=True)
    log = open(sess_dir / "session.jsonl", "a", encoding="utf-8")
    outcome, done_n, prev_end = "completed", 0, 0
    try:
        await s.play(wav_bytes("intro.wav") or DOUBLE, "intro")
        code = await s.read_digits()
        await s.play(wav_bytes("consent.wav") or BEEP, "consent")
        consent = await s.read_digits()
        log.write(json.dumps({"event": "session", **s.meta, "speaker_code": code, "consent_dtmf": consent,
                              "started_utc": started.isoformat(), "sample_rate": RATE, "params": P, "vad": VAD.as_dict()}) + "\n"); log.flush()
        if consent != "1":
            outcome = "no_consent"; await s.play(DOUBLE, "no-consent"); return
        for n in range(1, P["prompts"] + 1):
            if s.stopped.is_set():
                outcome = "call_ended"; break
            mk = await s.play(BEEP, f"p{n}")
            u = await s.record_utterance(mk["mark_sample"], prev_end)
            prev_end = u["window_end_sample"]
            f = sess_dir / f"SPK{code}_{n:02d}.wav"
            sha = _write(f, bytes(s.pcm[u["window_start_sample"] * 2:u["window_end_sample"] * 2]))
            log.write(json.dumps({"event": "utterance", "n": n, "file": f.name, "sha256": sha, "sample_rate": RATE, **mk, **u}) + "\n"); log.flush()
            done_n = n
            if u["end_reason"] == "call_ended":
                outcome = "call_ended"; break
        if outcome == "completed":
            await s.play(DOUBLE, "done")
    finally:
        sha = _write(sess_dir / "session_raw.wav", bytes(s.pcm))
        log.write(json.dumps({"event": "session_end", "outcome": outcome, "prompts_completed": done_n,
                              "stop_reason": s.stop_reason, "session_raw_sha256": sha, "session_samples": s.n}) + "\n")
        log.close(); rtask.cancel()


async def main():
    _salt()
    port = int(os.environ.get("PORT", "5001"))
    import websockets
    async with websockets.serve(handler, "0.0.0.0", port, max_size=2**22):
        print(f"recorder on :{port}; expose with ngrok and put wss://<host>/ in the Exotel Voicebot applet")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
