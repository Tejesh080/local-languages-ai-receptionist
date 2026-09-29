"""Energy VAD shared by the recorder (online) and the benchmark (offline), so speech boundaries are computed identically.
Deterministic: same PCM -> same boundaries. Parameters are versioned into every result (VAD_VERSION)."""
from __future__ import annotations
import array
import math
from dataclasses import dataclass, asdict

VAD_VERSION = "energy-v1"


@dataclass(frozen=True)
class VadParams:
    frame_ms: int = 20
    margin_db: float = 12.0          # speech if frame dB > noise floor + margin
    abs_floor_db: float = -55.0      # and above this absolute level
    min_speech_ms: int = 120         # ignore clicks shorter than this
    hang_ms: int = 300               # gap shorter than this does not end a speech region

    def as_dict(self) -> dict:
        return {"vad_version": VAD_VERSION, **asdict(self)}


def frame_db(pcm: bytes, rate: int, frame_ms: int) -> list[float]:
    a = array.array("h", pcm[: len(pcm) - len(pcm) % 2])
    n = rate * frame_ms // 1000
    out = []
    for i in range(0, len(a) - n + 1, n):
        fr = a[i:i + n]
        rms = math.sqrt(sum(x * x for x in fr) / n) or 1.0
        out.append(20 * math.log10(rms / 32768))
    return out


@dataclass(frozen=True)
class SpeechBounds:
    start_sample: int | None
    end_sample: int | None       # exclusive: first sample after the last speech frame
    speech_ratio: float


def speech_bounds(pcm: bytes, rate: int, p: VadParams = VadParams()) -> SpeechBounds:
    dbs = frame_db(pcm, rate, p.frame_ms)
    if not dbs:
        return SpeechBounds(None, None, 0.0)
    floor = sorted(dbs)[len(dbs) // 10]
    thr = max(floor + p.margin_db, p.abs_floor_db)
    speech = [d > thr for d in dbs]
    regions, start, gap = [], None, 0
    hang = p.hang_ms // p.frame_ms
    for i, s in enumerate(speech + [False] * (hang + 1)):
        if s:
            start = i if start is None else start
            gap = 0
        elif start is not None:
            gap += 1
            if gap > hang:
                end = i - gap + 1
                if (end - start) * p.frame_ms >= p.min_speech_ms:
                    regions.append((start, end))
                start, gap = None, 0
    if not regions:
        return SpeechBounds(None, None, 0.0)
    fs = rate * p.frame_ms // 1000
    voiced = sum(e - s for s, e in regions)
    return SpeechBounds(regions[0][0] * fs, regions[-1][1] * fs, voiced / len(dbs))
