"""Real-time replay with speech-end ground truth (decision 0002).

Reference point = the monotonic-clock instant the chunk ENDING at speech_end_sample was handed to the socket.
Chunks are cut so a boundary falls exactly on speech_end_sample; audio is sent on an absolute real-time schedule."""
from __future__ import annotations
import asyncio
import time
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class ReplayPlan:
    chunks: list[bytes]
    offsets_s: list[float]           # scheduled send time of each chunk relative to the first send
    speech_end_chunk: int            # index of the chunk whose last sample is speech_end_sample - 1
    rate: int
    speech_end_sample: int


def make_plan(pcm: bytes, rate: int, chunk_ms: int, speech_end_sample: int) -> ReplayPlan:
    n = len(pcm) // 2
    if not 0 < speech_end_sample <= n:
        raise ValueError("speech_end_sample must be inside the audio")
    step = rate * chunk_ms // 1000
    bounds = list(range(0, speech_end_sample, step)) + [speech_end_sample]
    bounds += list(range(speech_end_sample + step, n, step)) + ([n] if bounds[-1] != n else [])
    bounds = sorted(set(bounds))
    chunks = [pcm[a * 2:b * 2] for a, b in zip(bounds, bounds[1:])]
    offsets = [a / rate for a in bounds[:-1]]
    idx = bounds.index(speech_end_sample) - 1
    return ReplayPlan(chunks, offsets, idx, rate, speech_end_sample)


@dataclass
class Timeline:
    clock: Callable[[], float] = time.perf_counter
    t0: float | None = None
    t_speech_end_sent: float | None = None
    events: list[tuple[str, float]] = field(default_factory=list)

    def rel_ms(self, t: float) -> float:
        return (t - self.t0) * 1000

    def mark(self, name: str) -> float:
        t = self.clock()
        self.events.append((name, t))
        return t


async def send_paced(plan: ReplayPlan, send: Callable, tl: Timeline, sleep=asyncio.sleep) -> None:
    for i, (chunk, off) in enumerate(zip(plan.chunks, plan.offsets_s)):
        if tl.t0 is None:
            tl.t0 = tl.clock()
        else:
            delay = tl.t0 + off - tl.clock()
            if delay > 0:
                await sleep(delay)
        await send(chunk)
        if i == plan.speech_end_chunk:
            tl.t_speech_end_sent = tl.clock()


def endpoint_latency(tl: Timeline, finals: list[float]) -> tuple[float | None, str | None]:
    """Latency from speech end to the first final transcript that arrives after it.
    Returns (ms, flag). A flag means the value must NOT enter percentiles."""
    if tl.t_speech_end_sent is None:
        return None, "speech_end_never_sent"
    after = [t for t in finals if t >= tl.t_speech_end_sent]
    if not after:
        return (None, "final_before_speech_end") if finals else (None, "no_final")
    return (after[0] - tl.t_speech_end_sent) * 1000, None


def latency_summary(rows: list[dict]) -> dict:
    """P50/P95/P99 over valid rows only; invalid rows are counted, never dropped silently."""
    valid, flags = [], {}
    for r in rows:
        v, f = r.get("final_after_speech_end_ms"), r.get("latency_flag")
        if f:
            flags[f] = flags.get(f, 0) + 1
            continue
        if v is None:
            flags["missing"] = flags.get("missing", 0) + 1
            continue
        if v < 0:
            raise AssertionError("negative endpoint latency without a flag: measurement bug")
        valid.append(v)
    valid.sort()
    q = lambda p: round(valid[min(len(valid) - 1, int(p * len(valid)))], 1) if valid else None
    return {"n_valid": len(valid), "n_flagged": sum(flags.values()), "flags": flags, "p50": q(.5), "p95": q(.95), "p99": q(.99)}
