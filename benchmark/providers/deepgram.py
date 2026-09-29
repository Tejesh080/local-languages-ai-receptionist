"""Deepgram live STT, nova-3 language=te. Protocol re-verified 2026-09-30 (developers.deepgram.com listen-streaming):
wss://api.deepgram.com/v1/listen ; header `Authorization: Token <key>` ; binary audio frames ; client
{"type":"Finalize"} / {"type":"CloseStream"} ; server Results{is_final,speech_final,channel.alternatives},
Metadata{request_id,model_info,duration}, UtteranceEnd. keyterm is repeatable (nova-3 monolingual supported)."""
from __future__ import annotations
import asyncio, json, os, urllib.parse
import websockets
from .base import STTResult
from benchmark.replay import ReplayPlan, Timeline, send_paced, endpoint_latency

URL = os.environ.get("DEEPGRAM_URL", "wss://api.deepgram.com/v1/listen")


def build_url(cfg: dict, keyterms: list[str], rate: int) -> str:
    params = [("model", cfg["model"]), ("language", cfg.get("language", "te")), ("encoding", "linear16"),
              ("sample_rate", str(rate)), ("channels", "1"), ("interim_results", "true"), ("punctuate", "true"),
              ("endpointing", str(cfg.get("endpointing_ms", 500)))]
    return URL + "?" + urllib.parse.urlencode(params + [("keyterm", k) for k in keyterms[:50]])


async def transcribe(plan: ReplayPlan, cfg: dict, keyterms: list[str], tl: Timeline | None = None) -> STTResult:
    tl = tl or Timeline()
    res, finals_t, texts, speech_final = STTResult(), [], [], []
    async with websockets.connect(build_url(cfg, keyterms, plan.rate), max_size=2**22,
                                  additional_headers={"Authorization": f"Token {os.environ['DEEPGRAM_API_KEY']}"}) as ws:
        async def send():
            await send_paced(plan, ws.send, tl)
            await ws.send(json.dumps({"type": "CloseStream"}))

        async def recv():
            async for msg in ws:
                ev = json.loads(msg); t = tl.clock(); kind = ev.get("type", "?")
                res.events[kind] = res.events.get(kind, 0) + 1
                if kind == "Results":
                    alt = (ev.get("channel", {}).get("alternatives") or [{}])[0].get("transcript", "")
                    if ev.get("is_final"):
                        if alt:
                            finals_t.append(t); texts.append(alt)
                        if ev.get("speech_final"):
                            speech_final.append(t)
                    elif alt:
                        res.partials += 1
                        if res.first_partial_ms is None and tl.t0 is not None:
                            res.first_partial_ms = tl.rel_ms(t)
                elif kind == "Metadata":
                    res.session = {"request_id": ev.get("request_id"), "model_info": ev.get("model_info")}
                    res.billed_seconds = ev.get("duration")
                elif kind == "Error" or "err_code" in ev:
                    res.errors.append(f"{ev.get('err_code')}:{ev.get('err_msg') or ev.get('description')}")
        try:
            await asyncio.wait_for(asyncio.gather(send(), recv()),
                                   timeout=sum(len(c) for c in plan.chunks) / (2 * plan.rate) + cfg.get("timeout_margin_s", 30))
        except asyncio.TimeoutError:
            res.errors.append("client_timeout")
        except websockets.ConnectionClosed as e:
            if not isinstance(e, websockets.ConnectionClosedOK):
                res.errors.append(f"closed:{e.code}")
    res.transcript = " ".join(texts).strip()
    if tl.t0 is not None:
        res.final_ms = [round(tl.rel_ms(t), 1) for t in finals_t]
        res.speech_end_sent_ms = round(tl.rel_ms(tl.t_speech_end_sent), 1) if tl.t_speech_end_sent else None
    res.final_after_speech_end_ms, res.latency_flag = endpoint_latency(tl, finals_t)
    after = [t for t in speech_final if tl.t_speech_end_sent and t >= tl.t_speech_end_sent]
    res.provider_endpoint_ms = round((after[0] - tl.t_speech_end_sent) * 1000, 1) if after else None
    return res
