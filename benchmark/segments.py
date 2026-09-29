"""Derived benchmark segments (methodology B, decision 0002): raw carrier audio up to the recorded speech end,
followed by a standardized trailing silence. Raw WAVs are never modified; derived files are content-addressed."""
from __future__ import annotations
import hashlib
import json
import wave
from pathlib import Path

DERIVATION_VERSION = "seg-b-v1"


def sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_pcm(path: str | Path) -> tuple[bytes, int]:
    with wave.open(str(path)) as w:
        if w.getnchannels() != 1 or w.getsampwidth() != 2:
            raise ValueError(f"{path}: expected mono 16-bit PCM")
        return w.readframes(w.getnframes()), w.getframerate()


def derive(raw_path: str, speech_end_sample: int, trailing_ms: int, out_root: str) -> dict:
    pcm, rate = read_pcm(raw_path)
    n = len(pcm) // 2
    if not 0 < speech_end_sample <= n:
        raise ValueError(f"speech_end_sample {speech_end_sample} outside 1..{n}")
    params = {"derivation": DERIVATION_VERSION, "trailing_ms": trailing_ms}
    pid = hashlib.sha256(json.dumps(params, sort_keys=True).encode()).hexdigest()[:10]
    out_dir = Path(out_root) / pid
    out_dir.mkdir(parents=True, exist_ok=True)
    seg = pcm[: speech_end_sample * 2] + b"\x00\x00" * (rate * trailing_ms // 1000)
    raw_sha = sha256_file(raw_path)
    out = out_dir / f"{raw_sha[:16]}.wav"
    if not out.exists():
        with wave.open(str(out), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate); w.writeframes(seg)
    return {"derived_path": str(out), "derived_sha256": sha256_file(out), "raw_sha256": raw_sha, "params_id": pid,
            **params, "speech_end_sample": speech_end_sample, "sample_rate": rate,
            "derived_samples": len(seg) // 2}
