"""Caller end-of-speech -> first audible agent audio, from a 2-channel recording (ch0 caller, ch1 agent).
Also flags overlaps where the agent starts while the caller is still speaking (candidate false cutoffs for human review).
Mono recordings cannot separate speakers: report latency as UNKNOWN rather than guessing."""
from __future__ import annotations
import array, math, sys, wave


def segments(samples: array.array, rate: int, frame_ms=20, margin_db=12, min_speech_ms=120, hang_ms=300):
    n = rate * frame_ms // 1000
    dbs = []
    for i in range(0, len(samples) - n + 1, n):
        fr = samples[i:i + n]
        rms = math.sqrt(sum(x * x for x in fr) / n) or 1
        dbs.append(20 * math.log10(rms / 32768))
    floor = sorted(dbs)[len(dbs) // 10] if dbs else -90
    segs, start, quiet = [], None, 0
    for k, db in enumerate(dbs):
        if db > floor + margin_db:
            start = k if start is None else start; quiet = 0
        elif start is not None:
            quiet += frame_ms
            if quiet >= hang_ms:
                end = k - quiet // frame_ms + 1
                if (end - start) * frame_ms >= min_speech_ms:
                    segs.append((start * frame_ms / 1000, end * frame_ms / 1000))
                start, quiet = None, 0
    if start is not None:
        segs.append((start * frame_ms / 1000, len(dbs) * frame_ms / 1000))
    return segs


def main(path: str) -> None:
    with wave.open(path) as w:
        if w.getnchannels() != 2:
            print("mono recording: speaker separation impossible, latency UNKNOWN"); return
        rate = w.getframerate(); data = array.array("h", w.readframes(w.getnframes()))
    caller, agent = segments(data[0::2], rate), segments(data[1::2], rate)
    gaps, overlaps = [], 0
    for cs, ce in caller:
        nxt = [a for a in agent if a[0] >= ce - 0.05]
        during = [a for a in agent if cs < a[0] < ce - 0.2]
        overlaps += bool(during)
        if nxt:
            gaps.append(round(nxt[0][0] - ce, 2))
    gaps.sort()
    q = lambda p: gaps[min(len(gaps) - 1, int(p * len(gaps)))] if gaps else None
    print({"caller_turns": len(caller), "gaps_s_p50": q(.5), "p95": q(.95), "max": gaps[-1] if gaps else None,
           "agent_started_during_caller_speech": overlaps})


if __name__ == "__main__":
    main(sys.argv[1])
