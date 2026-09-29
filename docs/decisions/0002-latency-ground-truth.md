# Decision 0002: Latency ground truth for STT benchmarks

Status: ACCEPTED 2026-09-30. Supersedes the Phase 2 runner metric `final_ms - WAV_duration`.

## Problem
The recorder ends an utterance after ~1.5 s of trailing silence, and that silence is part of the WAV. The old runner
added more silence and computed latency as `provider_final_time - WAV_duration`. Because the WAV end is up to ~1.5 s after
the real end of speech, that formula understates latency (it can even go negative). A test with a fake provider
reproduces the error: on the same audio the old formula reported a value more than 1 s below the correct one.

## Decision
1. **Recorder stores speech timing as sample indices** for every utterance: `speech_start_sample`, `speech_end_sample`,
   `file_end_sample`, `sample_rate`, `end_reason`, `silence_after_speech_ms`, plus the mark/beep timing.
   Computed with the shared energy VAD (`audio/vad.py`, version `energy-v1`), whose parameters are stored with the data.
2. **Raw audio is immutable.** The whole inbound stream is kept as `session_raw.wav`; each utterance file is an exact byte
   slice of it; files are made read-only; sha256 is recorded at write time and re-checked by `build_manifest` and `run_stt`.
3. **Replay methodology B is the default for provider comparisons:** derived segment = raw audio up to
   `speech_end_sample` + a standardized trailing silence (default 1,500 ms), content-addressed under `benchmark/derived/`
   with the derivation version. Every provider therefore receives an identical endpoint condition.
   Methodology A (replay the exact carrier recording) remains available with `--replay exact` for realism checks.
4. **Reference point:** the monotonic-clock instant the chunk ending exactly at `speech_end_sample` is handed to the
   socket. Chunks are cut so a boundary falls on the speech end; audio is sent on an absolute real-time schedule.
   All provider timestamps use the same clock (`benchmark/replay.py::Timeline`).
5. **Metric:** endpoint latency = first final transcript received at or after the reference point, minus the reference point.
   A final that only arrives before the speech end is flagged `final_before_speech_end` (premature endpointing, a quality
   signal), and no final at all is flagged `no_final`. Flagged rows are counted and reported, never averaged into percentiles.
   A negative latency without a flag raises an error (measurement bug).
6. Also recorded: `first_partial_ms` (from first audio sent) and the provider's own end-of-speech event
   (Sarvam `vad.speech_end`, Deepgram `speech_final`) relative to the speech end.

## Limitations
- Network transit from the test machine to the provider is included and identical across providers only if runs happen
  from the same machine and region; record the machine and region in the run notes.
- Energy VAD can place the end slightly late on breathy or noisy endings (+/- one 20 ms frame in synthetic tests);
  the offline re-computation is checked against the recorder's value in the quality gate.
- This measures STT endpointing only. The caller-perceived end-of-speech to first agent audio (E1A/E10) needs call
  recordings with separated channels.

## Tests
`tests/test_latency_ground_truth.py` (speech end before file end; derived segment keeps raw immutable; chunk boundary
on speech end; single clock; latency relative to speech end through fake Sarvam and Deepgram servers; negative/premature
finals flagged and excluded) and `tests/test_recorder_protocol.py`.
