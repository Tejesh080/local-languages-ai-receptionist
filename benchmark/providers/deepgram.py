"""Deepgram live STT, nova-3 with language=te (Telugu listed in Deepgram models page, checked 2026-09-30)."""
from __future__ import annotations
import asyncio, json, os, time, urllib.parse
import websockets
from .base import STTResult

URL = "wss://api.deepgram.com/v1/listen"


async def transcribe(pcm: bytes, cfg: dict, keyterms: list[str], rate: int = 8000) -> STTResult:
    params = [("model", cfg["model"]), ("language", cfg.get("language", "te")), ("encoding", "linear16"),
              ("sample_rate", str(rate)), ("channels", "1"), ("interim_results", "true"), ("punctuate", "true"),
              ("endpointing", str(cfg.get("endpointing_ms", 500)))]
    params += [("keyterm", k) for k in keyterms[:50]]
    url = URL + "?" + urllib.parse.urlencode(params)
    res = STTResult()
    chunk = rate * 2 * cfg.get("chunk_ms", 100) // 1000
    speech_len_s = len(pcm) / (2 * rate)
    padded = pcm + b"\x00" * (rate * 2 * cfg.get("trailing_silence_ms", 1500) // 1000)
    finals: list[str] = []
    async with websockets.connect(url, additional_headers={"Authorization": f"Token {os.environ['DEEPGRAM_API_KEY']}"},
                                  max_size=2**22) as ws:
        t0 = time.perf_counter()

        async def send():
            for i in range(0, len(padded), chunk):
                await ws.send(padded[i:i + chunk])
                await asyncio.sleep(cfg.get("chunk_ms", 100) / 1000)
            await ws.send(json.dumps({"type": "CloseStream"}))

        async def recv():
            async for msg in ws:
                ev = json.loads(msg); res.raw_events += 1
                now_ms = (time.perf_counter() - t0) * 1000
                if ev.get("type") == "Results":
                    alt = ev["channel"]["alternatives"][0].get("transcript", "")
                    if not alt:
                        continue
                    if ev.get("is_final"):
                        finals.append(alt); res.final_ms = now_ms
                        res.final_after_speech_end_ms = now_ms - speech_len_s * 1000
                    else:
                        res.partials += 1; res.first_partial_ms = res.first_partial_ms or now_ms
                elif ev.get("type") == "Metadata":
                    res.billed_seconds = ev.get("duration")
        try:
            await asyncio.wait_for(asyncio.gather(send(), recv()), timeout=speech_len_s + 30)
        except (asyncio.TimeoutError, websockets.ConnectionClosed) as e:
            if not isinstance(e, websockets.ConnectionClosedOK):
                res.errors.append(type(e).__name__)
    res.transcript = " ".join(finals).strip()
    return res
