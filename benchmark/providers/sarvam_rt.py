"""Sarvam realtime STT (wss://api.sarvam.ai/speech-to-text-realtime/ws), per docs checked 2026-09-29.
Auth header name `api-subscription-key` follows Sarvam's REST convention: VERIFY on first run (error 1003 = bad key)."""
from __future__ import annotations
import asyncio, base64, json, os, time, urllib.parse
import websockets
from .base import STTResult

URL = "wss://api.sarvam.ai/speech-to-text-realtime/ws"


async def transcribe(pcm: bytes, cfg: dict, keyterms: list[str], rate: int = 8000) -> STTResult:
    params = {"language_code": cfg.get("language_code", "te-IN"), "model": cfg["model"], "mode": cfg.get("mode", "transcribe"),
              "stream_type": cfg.get("stream_type", "fast"), "encoding": "linear16", "sample_rate": str(rate),
              "endpointing": "vad", "silence_duration_ms": str(cfg.get("silence_duration_ms", 500))}
    if keyterms:
        params["keyterms"] = json.dumps(keyterms[:50], ensure_ascii=False)
    url = URL + "?" + urllib.parse.urlencode(params)
    res = STTResult()
    chunk = rate * 2 * cfg.get("chunk_ms", 100) // 1000
    speech_len_s = len(pcm) / (2 * rate)
    padded = pcm + b"\x00" * (rate * 2 * cfg.get("trailing_silence_ms", 1500) // 1000)
    finals: list[str] = []
    async with websockets.connect(url, additional_headers={"api-subscription-key": os.environ["SARVAM_API_KEY"]},
                                  max_size=2**22) as ws:
        t0 = time.perf_counter()

        async def send():
            for i in range(0, len(padded), chunk):
                await ws.send(json.dumps({"event": "audio_input", "audio": base64.b64encode(padded[i:i + chunk]).decode()}))
                await asyncio.sleep(cfg.get("chunk_ms", 100) / 1000)       # real-time pacing
            await ws.send(json.dumps({"event": "end"}))

        async def recv():
            async for msg in ws:
                ev = json.loads(msg); res.raw_events += 1
                now_ms = (time.perf_counter() - t0) * 1000
                kind = ev.get("event")
                if kind == "transcript.partial":
                    res.partials += 1
                    res.first_partial_ms = res.first_partial_ms or now_ms
                elif kind == "transcript.final":
                    finals.append(ev.get("text", ""))
                    res.final_ms = now_ms
                    res.final_after_speech_end_ms = now_ms - speech_len_s * 1000
                    res.detected_language = ev.get("language", res.detected_language)
                elif kind == "session.end":
                    res.billed_seconds = ev.get("audio_duration_s"); return
                elif kind == "error":
                    res.errors.append(f"{ev.get('code')}:{ev.get('message')}")
                    if ev.get("is_fatal"):
                        return
        try:
            await asyncio.wait_for(asyncio.gather(send(), recv()), timeout=speech_len_s + 30)
        except (asyncio.TimeoutError, websockets.ConnectionClosed) as e:
            res.errors.append(type(e).__name__)
    res.transcript = " ".join(f for f in finals if f).strip()
    return res
