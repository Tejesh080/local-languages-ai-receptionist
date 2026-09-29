"""E3 phone recorder over Exotel's Voicebot WebSocket (protocol per developer.exotel.com AgentStream docs).

Call flow: caller dials the ExoPhone -> App Bazaar flow: Call Start -> Voicebot applet (wss://HOST/ws) -> Hangup.
Session: optional intro.wav -> caller types 4-digit speaker code + '#' -> presses 1 to confirm consent ->
for n in 1..50: beep -> caller reads line n from their sheet -> utterance ends on '#', 1.5 s silence, or 15 s cap.
Audio is carrier-path 8 kHz 16-bit PCM exactly as Exotel delivers it. The caller's number is stored only as a salted hash.
"""
from __future__ import annotations
import array, asyncio, base64, datetime as dt, hashlib, json, math, os, struct, wave
from pathlib import Path
import websockets

OUT = Path(os.environ.get("RECORDINGS_DIR", "collection/recordings"))
AUDIO_DIR = Path(__file__).parent / "audio"          # optional intro.wav / consent.wav (8 kHz mono 16-bit)
SALT = os.environ.get("PHONE_HASH_SALT", "change-me")
RATE, FRAME = 8000, 320                                # 20 ms frames at 8 kHz, 16-bit
MAX_UTT_S, END_SIL_MS, PROMPTS = 15.0, 1500, int(os.environ.get("PROMPTS_PER_SESSION", "50"))


def tone(freq: float, ms: int, vol: float = 0.3) -> bytes:
    n = RATE * ms // 1000
    return b"".join(struct.pack("<h", int(vol * 32767 * math.sin(2 * math.pi * freq * i / RATE))) for i in range(n))


def _rms(b: bytes) -> int:
    a = array.array("h", b)
    return int(math.sqrt(sum(x * x for x in a) / len(a))) if a else 0


def _peak(b: bytes) -> int:
    a = array.array("h", b)
    return max((abs(x) for x in a), default=0)


BEEP = tone(1000, 250)
DOUBLE = tone(800, 150) + b"\x00\x00" * 800 + tone(800, 150)


def wav_bytes(name: str) -> bytes | None:
    p = AUDIO_DIR / name
    if not p.exists():
        return None
    with wave.open(str(p)) as w:
        assert w.getframerate() == RATE and w.getnchannels() == 1 and w.getsampwidth() == 2, f"{name} must be 8k mono 16-bit"
        return w.readframes(w.getnframes())


class Session:
    def __init__(self, ws):
        self.ws, self.sid, self.buf = ws, None, bytearray()
        self.dtmf: asyncio.Queue[str] = asyncio.Queue()
        self.audio: asyncio.Queue[bytes] = asyncio.Queue()
        self.meta: dict = {}

    async def play(self, pcm: bytes, label: str) -> None:
        pad = (-len(pcm)) % 3200 or 0                       # chunks must be multiples of 320, >= 3200 bytes
        pcm = pcm + b"\x00" * pad
        for i in range(0, len(pcm), 3200):
            await self.ws.send(json.dumps({"event": "media", "stream_sid": self.sid,
                                           "media": {"payload": base64.b64encode(pcm[i:i + 3200]).decode()}}))
        await self.ws.send(json.dumps({"event": "mark", "stream_sid": self.sid, "mark": {"name": label}}))
        await asyncio.sleep(len(pcm) / (RATE * 2))           # rough wait for playback

    async def read_digits(self, terminator="#", timeout=20.0) -> str:
        s = ""
        try:
            while True:
                d = await asyncio.wait_for(self.dtmf.get(), timeout)
                if d == terminator:
                    return s
                s += d
        except asyncio.TimeoutError:
            return s

    async def record_utterance(self) -> tuple[bytes, str]:
        while not self.audio.empty():
            self.audio.get_nowait()
        pcm, floor, spoke, silent_ms, t, reason = bytearray(), None, False, 0, 0.0, "max_len"
        while t < MAX_UTT_S:
            try:
                chunk = await asyncio.wait_for(self.audio.get(), 0.5)
            except asyncio.TimeoutError:
                chunk = b""
            if not self.dtmf.empty() and (await self.dtmf.get()) == "#":
                reason = "dtmf"; break
            pcm += chunk; t += len(chunk) / (RATE * 2)
            for i in range(0, len(chunk) - FRAME + 1, FRAME):
                rms = _rms(chunk[i:i + FRAME]) or 1
                db = 20 * math.log10(rms / 32768)
                floor = db if floor is None else (min(floor, db) if not spoke else floor)
                if db > (floor or -60) + 12:
                    spoke, silent_ms = True, 0
                elif spoke:
                    silent_ms += 20
            if spoke and silent_ms >= END_SIL_MS:
                reason = "silence"; break
        return bytes(pcm), reason


async def handler(ws):
    s = Session(ws)

    async def reader():
        async for msg in ws:
            ev = json.loads(msg)
            if ev["event"] == "start":
                st = ev["start"]; s.sid = st["stream_sid"]
                s.meta = {"call_sid": st.get("call_sid"), "to": st.get("to"),
                          "from_hash": hashlib.sha256((SALT + st.get("from", "")).encode()).hexdigest()[:16],
                          "media_format": st.get("media_format")}
            elif ev["event"] == "media":
                await s.audio.put(base64.b64decode(ev["media"]["payload"]))
            elif ev["event"] == "dtmf":
                await s.dtmf.put(ev["dtmf"]["digit"])
            elif ev["event"] == "stop":
                break
    rtask = asyncio.create_task(reader())
    while s.sid is None:
        await asyncio.sleep(0.05)
    if s.meta.get("media_format", {}).get("sample_rate") not in (None, "8000", 8000):
        print("WARNING: non-8k stream", s.meta["media_format"])
    started = dt.datetime.now(dt.timezone.utc)
    sess_dir = OUT / f"{started:%Y%m%dT%H%M%S}_{s.meta['call_sid']}"
    sess_dir.mkdir(parents=True, exist_ok=True)
    log = open(sess_dir / "session.jsonl", "a", encoding="utf-8")
    try:
        await s.play(wav_bytes("intro.wav") or DOUBLE, "intro")
        code = await s.read_digits()
        await s.play(wav_bytes("consent.wav") or BEEP, "consent")
        consent = await s.read_digits(timeout=15)
        log.write(json.dumps({"event": "session", **s.meta, "speaker_code": code, "consent_dtmf": consent,
                              "started_utc": started.isoformat()}) + "\n"); log.flush()
        if consent != "1":
            await s.play(DOUBLE, "no-consent"); return
        for n in range(1, PROMPTS + 1):
            await s.play(BEEP, f"p{n}")
            pcm, reason = await s.record_utterance()
            path = sess_dir / f"SPK{code}_{n:02d}.wav"
            with wave.open(str(path), "wb") as w:
                w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE); w.writeframes(pcm)
            peak = _peak(pcm)
            log.write(json.dumps({"event": "utterance", "n": n, "file": path.name, "seconds": round(len(pcm) / (2 * RATE), 2),
                                  "end_reason": reason, "clipped": peak >= 32000}) + "\n"); log.flush()
        await s.play(DOUBLE, "done")
    finally:
        log.close(); rtask.cancel()


async def main():
    port = int(os.environ.get("PORT", "5001"))
    async with websockets.serve(handler, "0.0.0.0", port, max_size=2**22):
        print(f"recorder listening on :{port} (expose with: ngrok http {port}; use wss://<ngrok>/ in the Voicebot applet)")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
