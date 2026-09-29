# E3 collection -> quality gate -> E4 STT bake-off -> E7 on real transcripts

## E3
1. Consent first (collection/consent/consent_en_te.md); record `consent_ref` per speaker in speakers.csv.
2. Exotel ExoPhone -> App Bazaar: Call Start -> Voicebot applet `wss://<host>/` -> Hangup. Run
   `APP_ENV=development PHONE_HASH_SALT=... python collection/recorder/exotel_recorder.py` behind ngrok.
   The recorder waits for Exotel's mark acknowledgement after each beep (timeout fallback is recorded per prompt), keeps
   `session_raw.wav` (immutable master), writes each utterance as an exact read-only slice, and stores speech timing.
3. `python -m benchmark.build_manifest collection/recordings speakers.csv` -> benchmark/manifests/e3_raw.jsonl (nothing filtered).
4. `python -m benchmark.quality benchmark/manifests/e3_raw.jsonl [--exclusions exclusions.csv]`
   -> dataset-quality-report.md. Blocking items need an explicit exclusion WITH reason and excluded_by; only then is
   e3_analysis.jsonl written (with derived segments, methodology B, decision 0002).

## E4
1. `python -m benchmark.preflight` -> every provider must be READY (key, reachability, config accepted, fixture transcribes).
2. `python -m benchmark.smoke --config sarvam_v4` (and each config you will run) -> inspect events, errors, billing.
3. `python benchmark/run_stt.py benchmark/manifests/e3_analysis.jsonl --limit 20` -> smoke on real data, then full.
   Circuit breaker aborts a config whose first 5 attempts fail. sha256 of every audio file is verified before sending.
4. `python benchmark/score_stt.py benchmark/runs/<run_id> benchmark/manifests/e3_analysis.jsonl`.
   Latency = speech end -> first final after it; premature finals flagged and excluded from percentiles.

## E7
- Development set (used for tuning): scripts/e7_synthetic.py. Holdout (single use per resolver version):
  scripts/e7_holdout.py, result docs/results/E7-holdout-res-94e84f0b967c.md.
- Decisive: `python scripts/e7_on_stt.py benchmark/runs/<run_id> benchmark/manifests/e3_analysis.jsonl`.
