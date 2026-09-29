"""Local fake provider servers implementing the documented wire protocols (for adapter + timing tests only)."""
from __future__ import annotations
import array, asyncio, base64, json, math, struct


def tone(ms: int, rate: int = 8000, amp: int = 8000, hz: int = 300) -> bytes:
    return b"".join(struct.pack("<h", int(amp * math.sin(2 * math.pi * hz * i / rate))) for i in range(rate * ms // 1000))


def silence(ms: int, rate: int = 8000) -> bytes:
    return b"\x00\x00" * (rate * ms // 1000)


def _speechy(pcm: bytes) -> bool:
    a = array.array("h", pcm)
    return any(abs(x) > 500 for x in a)


def sarvam_handler(final_delay_ms: int = 150, premature: bool = False, seen: dict | None = None):
    async def handler(ws):
        hdrs = {k.lower(): v for k, v in ws.request.headers.items()}
        if seen is not None:
            seen.update(path=ws.request.path, headers=hdrs)
        if "api-subscription-key" not in hdrs:
            await ws.send(json.dumps({"event": "error", "code": "unauthorized", "is_fatal": True, "message": "no key", "status_code": 401}))
            return
        await ws.send(json.dumps({"event": "session.begin", "request_id": "fake-req-1", "config": {"turn_detection": "vad"}}))
        total, spoke, ended = 0, False, False
        async for msg in ws:
            ev = json.loads(msg)
            if ev["event"] == "audio_input":
                pcm = base64.b64decode(ev["audio"]); total += len(pcm)
                if _speechy(pcm):
                    if not spoke:
                        await ws.send(json.dumps({"event": "transcript.partial", "utterance_idx": 0, "text": "రేపు"}))
                        if premature:
                            await ws.send(json.dumps({"event": "transcript.final", "utterance_idx": 0, "text": "రేపు"}))
                    spoke = True
                elif spoke and not ended and not premature:
                    ended = True
                    await ws.send(json.dumps({"event": "vad.speech_end", "utterance_idx": 0}))
                    await asyncio.sleep(final_delay_ms / 1000)
                    await ws.send(json.dumps({"event": "transcript.final", "utterance_idx": 0, "text": "రేపు service slot ఉందా"}))
            elif ev["event"] == "end":
                await ws.send(json.dumps({"event": "session.end", "request_id": "fake-req-1",
                                          "audio_duration_s": str(round(total / 16000, 3))}))
                return
    return handler


def deepgram_handler(final_delay_ms: int = 150, seen: dict | None = None):
    async def handler(ws):
        hdrs = {k.lower(): v for k, v in ws.request.headers.items()}
        if seen is not None:
            seen.update(path=ws.request.path, headers=hdrs)
        total, spoke, ended = 0, False, False
        async for msg in ws:
            if isinstance(msg, bytes):
                total += len(msg)
                if _speechy(msg):
                    if not spoke:
                        await ws.send(json.dumps({"type": "Results", "is_final": False, "channel": {"alternatives": [{"transcript": "రేపు"}]}}))
                    spoke = True
                elif spoke and not ended:
                    ended = True
                    await asyncio.sleep(final_delay_ms / 1000)
                    await ws.send(json.dumps({"type": "Results", "is_final": True, "speech_final": True,
                                              "channel": {"alternatives": [{"transcript": "రేపు service"}]}}))
            elif json.loads(msg).get("type") == "CloseStream":
                await ws.send(json.dumps({"type": "Metadata", "request_id": "dg-1", "model_info": {"name": "nova-3"},
                                          "duration": round(total / 16000, 3)}))
                return
    return handler
