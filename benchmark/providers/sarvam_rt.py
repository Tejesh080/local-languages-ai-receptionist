"""Sarvam realtime STT. Protocol re-verified 2026-09-30 against docs.sarvam.ai realtime-streaming guide and the
AsyncAPI reference (api-reference/speech-to-text/transcribe/realtime/ws):
- URL wss://api.sarvam.ai/speech-to-text-realtime/ws ; auth header `API-Subscription-Key`
- client: {"event":"audio_input","audio":<b64>}, {"event":"end"} (also speech_start/speech_end/flush in manual mode)
- server: session.begin{request_id,config}, vad.speech_start/end, transcript.partial/final{text,language?},
          session.end{audio_duration_s (billed; string-typed float)}, error{code,is_fatal,message,status_code?}
- keyterms: saaras:v4 only, JSON list <=50 x 64 chars, connection query parameter."""
from __future__ import annotations
import asyncio, base64, json, os, urllib.parse
import websockets
from .base import STTResult
from benchmark.replay import ReplayPlan, Timeline, send_paced, endpoint_latency

URL = os.environ.get("SARVAM_RT_URL", "wss://api.sarvam.ai/speech-to-text-realtime/ws")


def build_url(cfg: dict, keyterms: list[str], rate: int) -> str:
    params = {"language_code": cfg.get("language_code", "te-IN"), "model": cfg["model"], "mode": cfg.get("mode", "transcribe"),
              "stream_type": cfg.get("stream_type", "fast"), "encoding": "linear16", "sample_rate": str(rate),
              "endpointing": "vad", "silence_duration_ms": str(cfg.get("silence_duration_ms", 500))}
    if keyterms:
        if not cfg["model"].startswith("saaras:v4"):
            raise ValueError("keyterms are supported only on saaras:v4")
        if len(keyterms) > 50 or any(len(k) > 64 for k in keyterms):
            raise ValueError("keyterms: max 50 terms of 64 chars")
        params["keyterms"] = json.dumps(keyterms, ensure_ascii=False)
    return URL + "?" + urllib.parse.urlencode(params)


def _f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


async def transcribe(plan: ReplayPlan, cfg: dict, keyterms: list[str], tl: Timeline | None = None) -> STTResult:
    tl = tl or Timeline()
    res, finals_t, texts, vad_end = STTResult(), [], [], []
    async with websockets.connect(build_url(cfg, keyterms, plan.rate), max_size=2**22,
                                  additional_headers={"API-Subscription-Key": os.environ["SARVAM_API_KEY"]}) as ws:
        async def send():
            await send_paced(plan, lambda c: ws.send(json.dumps({"event": "audio_input", "audio": base64.b64encode(c).decode()})), tl)
            await ws.send(json.dumps({"event": "end"}))

        async def recv():
            async for msg in ws:
                ev = json.loads(msg); t = tl.clock(); kind = ev.get("event", "?")
                res.events[kind] = res.events.get(kind, 0) + 1
                if kind == "session.begin":
                    res.session = {"request_id": ev.get("request_id"), "config": ev.get("config")}
                elif kind == "transcript.partial":
                    res.partials += 1
                    if res.first_partial_ms is None and tl.t0 is not None:
                        res.first_partial_ms = tl.rel_ms(t)
                elif kind == "transcript.final":
                    finals_t.append(t); texts.append(ev.get("text", ""))
                    res.detected_language = ev.get("language", res.detected_language)
                elif kind == "vad.speech_end":
                    vad_end.append(t)
                elif kind == "session.end":
                    res.billed_seconds = _f(ev.get("audio_duration_s")); return
                elif kind == "error":
                    res.errors.append(f"{ev.get('code')}:{ev.get('status_code')}:{ev.get('message')}")
                    if ev.get("is_fatal"):
                        return
        try:
            await asyncio.wait_for(asyncio.gather(send(), recv()),
                                   timeout=sum(len(c) for c in plan.chunks) / (2 * plan.rate) + cfg.get("timeout_margin_s", 30))
        except asyncio.TimeoutError:
            res.errors.append("client_timeout")
        except websockets.ConnectionClosed as e:
            if not isinstance(e, websockets.ConnectionClosedOK):
                res.errors.append(f"closed:{e.code}")
    res.transcript = " ".join(x for x in texts if x).strip()
    if tl.t0 is not None:
        res.final_ms = [round(tl.rel_ms(t), 1) for t in finals_t]
        res.speech_end_sent_ms = round(tl.rel_ms(tl.t_speech_end_sent), 1) if tl.t_speech_end_sent else None
    res.final_after_speech_end_ms, res.latency_flag = endpoint_latency(tl, finals_t)
    after = [t for t in vad_end if tl.t_speech_end_sent and t >= tl.t_speech_end_sent]
    res.provider_endpoint_ms = round((after[0] - tl.t_speech_end_sent) * 1000, 1) if after else None
    return res
