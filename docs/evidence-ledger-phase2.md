# Evidence ledger, Phase 2 updates

| Claim | Status | Evidence | Date |
|---|---|---|---|
| Sarvam API tools support bearer / api_key / basic auth with workspace-stored secrets | VERIFIED (docs) | docs.sarvam.ai conversations/build/tools/https-tool | 2026-09-30 |
| Tools can receive caller number, transcript, interaction id, call length via call-context variables | VERIFIED (docs) | same | 2026-09-30 |
| Tools receive called number / agent id / deployment id / signature | UNKNOWN (not documented) | awaiting captures | |
| Post-call webhook includes app_id, deployment_id, agent_phone_number, duration, transcript | VERIFIED (docs) | deployments webhook payload page | 2026-09-30 |
| Sarvam egress IP 4.213.167.70 | VERIFIED (docs) | https-tool page | 2026-09-30 |
| Exotel Voicebot WS: connected/start/media/dtmf/mark/stop; send media/mark/clear; PCM16 8k default; chunks 3,200-100,000 bytes, multiple of 320; 60 min max | VERIFIED (docs) | developer.exotel.com AgentStream WebSocket protocol | 2026-09-30 |
| Recorder implements that protocol (DTMF code, consent, segmentation, hashed caller) | MEASURED (simulated client only) | tests/test_recorder_protocol.py | 2026-09-30 |
| Deepgram nova-3 supports Telugu (te); keyterm works on nova-3 monolingual | VERIFIED (docs) | developers.deepgram.com models overview, keyterm | 2026-09-30 |
| Backend never accepts model-supplied tenancy; idempotent booking; no double booking; privacy masking | MEASURED (unit tests, local) | tests/test_backend.py | 2026-09-30 |
| Resolver on DEVELOPMENT set: 0 silent wrong after one fix | MEASURED on data used for tuning (not independent) | E7-resolver-synthetic-run1/run2 | 2026-09-30 |
| Resolver on HOLDOUT set: 0 silent wrong observed in N=63; unknown names rejected 4/6; services no_match 4/12 | MEASURED (synthetic, single run, author-written) | E7-holdout-res-94e84f0b967c.md | 2026-09-30 |
| Booking concurrency: 20 concurrent -> 1 booking; 20 same-request retries -> 1 booking, same ref | MEASURED on PostgreSQL 16.2 (embedded, local) | tests/integration/test_pg_concurrency.py | 2026-09-30 |
| Old STT latency formula understated latency by >1 s | MEASURED (fake provider reproduction) | tests/test_latency_ground_truth.py | 2026-09-30 |
| Sarvam webhook supports only url + metadata (no signature/headers) | VERIFIED (docs); PLATFORM LIMITATION | decision 0003 | 2026-09-30 |
| Sarvam realtime: header API-Subscription-Key; session.begin/vad.*/transcript.*/session.end/error; audio_duration_s billed | VERIFIED (docs) | AsyncAPI reference | 2026-09-30 |
| Deepgram live: Authorization Token; Finalize/CloseStream; Metadata request_id/model_info | VERIFIED (docs) | listen-streaming reference | 2026-09-30 |
| Exotel inbound mark = playback finished | VERIFIED (docs); name echo INFERRED | AgentStream protocol | 2026-09-30 |
| Default capture/logs persist no plaintext PII | MEASURED (unit test with PII needles) | tests/test_backend.py | 2026-09-30 |
| Resolver handles Telugu "రావు" vs "Rao" | MEASURED after fix (run 1 missed it) | run1 vs run2 | 2026-09-30 |
| Any STT accuracy, latency, managed-agent quality, real cost | UNKNOWN | needs E1A, E3, E4 | |
