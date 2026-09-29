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
| Resolver: 0 silent wrong resolutions on synthetic set | MEASURED (synthetic, author-written, N=72 total) | docs/results/E7-resolver-synthetic-run2.md | 2026-09-30 |
| Resolver handles Telugu "రావు" vs "Rao" | MEASURED after fix (run 1 missed it) | run1 vs run2 | 2026-09-30 |
| Any STT accuracy, latency, managed-agent quality, real cost | UNKNOWN | needs E1A, E3, E4 | |
