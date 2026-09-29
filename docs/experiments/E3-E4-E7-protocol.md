# E3 collection -> E4 STT bake-off -> E7 resolver on real transcripts

## E3 (real PSTN audio)
1. Consent first: send collection/consent/consent_en_te.md; record the reply reference in speakers.csv
   (template: collection/speakers_template.csv). No addresses, no real names in the dataset.
2. Telephony: an Exotel ExoPhone with the Voicebot applet pointing at `wss://<host>/` running
   `collection/recorder/exotel_recorder.py` (8 kHz PCM16, protocol verified against Exotel docs and a local simulated client).
   If only a Sarvam-rented number is available, the recorder cannot run (Sarvam numbers route to Sarvam agents);
   use Exotel, or ask Sarvam about raw streaming on rented numbers (UNKNOWN).
3. Sheets: collection/sheets/SPKxx.md (20 speakers x 50 lines from 120 prompts, 8 conditions per speaker,
   prompt set version in benchmark/manifests/e3_assignments.json). Aim: Jio, Airtel, Vi and one more carrier.
4. `python benchmark/build_manifest.py collection/recordings speakers.csv` -> benchmark/manifests/e3_dataset.jsonl with dataset_version.

## E4 (STT bake-off)
- Configs: benchmark/configs/e4_stt.yaml (Sarvam v3-realtime, v4, v4+keyterms, v4 codemix, v4 codemix+keyterms,
  Deepgram nova-3 te, nova-3 te + keyterms). Telugu support confirmed in current docs for both providers.
- Keyterms: ONLY benchmark/configs/tenant_known_entities.yaml (known business terms). Never test answers.
- `SARVAM_API_KEY=... DEEPGRAM_API_KEY=... python benchmark/run_stt.py benchmark/manifests/e3_dataset.jsonl --limit 20`
  (smoke), then full. Audio is replayed at real-time pace in 100 ms chunks with 1.5 s trailing silence.
- `python benchmark/score_stt.py benchmark/runs/<run_id> benchmark/manifests/e3_dataset.jsonl` -> report.md with:
  critical entities by class, slices (partition known/confusable/unseen, style, region, quiet/noisy/speakerphone),
  keyterm effect per partition, WER/CER raw and digit-normalized, latency, error matrix.
- Cost of a full run (ESTIMATED): 1,000 utterances x ~5 s = ~1.4 h audio per config; 5 Sarvam configs x Rs30/h = ~Rs210,
  plus Deepgram (price not rechecked).

## E7
- Part 1 done: docs/results/E7-resolver-synthetic-run1.md and -run2.md (synthetic, not STT).
- Part 2: `python scripts/e7_on_stt.py benchmark/runs/<run_id> benchmark/manifests/e3_dataset.jsonl`.
