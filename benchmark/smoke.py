"""One request, one config, one short WAV. Prints everything needed to trust (or distrust) an adapter.
Usage: python -m benchmark.smoke --config sarvam_v4 [--wav path.wav]"""
from __future__ import annotations
import argparse, asyncio, json
from benchmark.stt_common import FIXTURE, config, transcribe_file


def main() -> int:
    a = argparse.ArgumentParser(); a.add_argument("--config", required=True); a.add_argument("--wav", default=str(FIXTURE))
    x = a.parse_args()
    cfg = config(x.config)
    try:
        r = asyncio.run(transcribe_file(cfg, x.wav))
    except Exception as e:  # noqa: BLE001  printed, not swallowed
        print(json.dumps({"config": x.config, "connection": "FAILED", "error": f"{type(e).__name__}: {e}"}, ensure_ascii=False, indent=1))
        return 1
    print(json.dumps({"config": x.config, "wav": x.wav, "connection": "OK" if r.session else "NO_SESSION_METADATA",
                      "session": r.session, "transcript": r.transcript, "events": r.events, "errors": r.errors,
                      "first_partial_ms": r.first_partial_ms, "finals_ms": r.final_ms, "speech_end_sent_ms": r.speech_end_sent_ms,
                      "final_after_speech_end_ms": r.final_after_speech_end_ms, "latency_flag": r.latency_flag,
                      "provider_endpoint_ms": r.provider_endpoint_ms, "billed_seconds": r.billed_seconds}, ensure_ascii=False, indent=1))
    return 0 if not r.errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
