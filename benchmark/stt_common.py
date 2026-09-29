"""Shared helpers: provider registry, config lookup, one-utterance transcription with ground-truth speech end."""
from __future__ import annotations
from pathlib import Path
import yaml
from benchmark.segments import read_pcm
from benchmark.replay import make_plan
from audio.vad import speech_bounds

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "benchmark/fixtures/preflight_te_espeak_8k.wav"
KEY_ENV = {"sarvam": "SARVAM_API_KEY", "deepgram": "DEEPGRAM_API_KEY"}
HOSTS = {"sarvam": "api.sarvam.ai", "deepgram": "api.deepgram.com"}


def load_spec() -> dict:
    return yaml.safe_load(open(ROOT / "benchmark/configs/e4_stt.yaml"))


def config(name: str) -> dict:
    spec = load_spec()
    for c in spec["configs"]:
        if c["name"] == name:
            return {**spec["common"], **c}
    raise KeyError(name)


def known_keyterms() -> list[str]:
    k = yaml.safe_load(open(ROOT / "benchmark/configs/tenant_known_entities.yaml"))
    return [k["business"], k["locality"], *k["advisors"], *k["services"], *k["extra_terms"]]


def provider_fn(name: str):
    if name == "sarvam":
        from benchmark.providers import sarvam_rt
        return sarvam_rt.transcribe
    if name == "deepgram":
        from benchmark.providers import deepgram
        return deepgram.transcribe
    raise KeyError(name)


async def transcribe_file(cfg: dict, wav: str, speech_end_sample: int | None = None, keyterms: list[str] | None = None):
    pcm, rate = read_pcm(wav)
    if rate != cfg["sample_rate"]:
        raise ValueError(f"{wav}: {rate} Hz but config expects {cfg['sample_rate']} Hz; resampling is never silent")
    if speech_end_sample is None:
        speech_end_sample = speech_bounds(pcm, rate).end_sample
        if speech_end_sample is None:
            raise ValueError(f"{wav}: no speech detected")
    plan = make_plan(pcm, rate, cfg["chunk_ms"], speech_end_sample)
    kt = (keyterms if keyterms is not None else known_keyterms()) if cfg.get("keyterms") else []
    return await provider_fn(cfg["provider"])(plan, cfg, kt)
