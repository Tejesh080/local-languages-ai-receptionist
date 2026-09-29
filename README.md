# telugu-voice-lab

Measurement infrastructure for a Telugu-first voice receptionist. Not the SaaS. Its job is to turn UNKNOWN into MEASURED:
which voice architecture gives the best Telugu business phone experience (System A: Sarvam Voice Agents managed;
System B: custom Pipecat pipeline, built only if triggered).

## What is here
| Path | Purpose | Status |
|---|---|---|
| `backend/` | Mock automotive service centre (fictional "Kaveri Auto Care", Kukatpally) + 6 HTTP tools, tenant binding, request capture, post-call webhook | Tested locally |
| `entities/` | Deterministic normalization (Telugu digits, spoken numbers, vehicle regs incl. TS/TG/AP/BH, dates, times, prices) and resolver | Tested |
| `managed/sarvam_agent/` | Agent instructions, tool cURLs, settings, important words, Claude Code + Sarvam MCP setup | Ready to apply |
| `benchmark/scenarios/` | E1A 30 smoke scenarios, E1B goals | Ready |
| `collection/` | E3 Exotel recorder, prompt generator, speaker sheets, consent | Recorder tested with simulated Exotel client |
| `benchmark/` | E4 STT runner (Sarvam realtime, Deepgram nova-3 te), scoring by entity/slice, stats, latency tool | Scoring tested; no provider runs yet |
| `scripts/` | E1A report, tool-metadata report, E7 resolver evaluations | E7 synthetic runs recorded |
| `docs/` | Protocols, decisions, results, evidence ledger | |

## Quick start
```bash
pip install -r requirements.txt
python -m pytest -q                      # 21 tests
python -m backend.seed --with-credentials  # prints TOOLS_BEARER_SECRET and WEBHOOK_PATH_SECRET once
TRUST_PROXY=1 uvicorn backend.app:app --port 8000
ngrok http 8000                          # public HTTPS URL for Sarvam tools
```
Then follow `docs/experiments/E1A-protocol.md`.

## Rules this repo enforces
- Transactional facts (hours, prices, slots, bookings) come only from the backend; the agent is told never to state them otherwise.
- Tenant = f(bearer secret). Bodies carrying tenant_id/org_id are rejected.
- `create_booking` requires `caller_confirmed=true`, validates phone and registration, is idempotent per interaction,
  claims the slot atomically, and returns `confirmed` only after reading the row back.
- Benchmarks keep failures and provider errors; retries are new rows. Results carry git commit, dataset version,
  config, keyterm hash, sample rate and codec. Keyterms contain only entities the business would know.
- Results report k/N with confidence bounds; "0 observed in N" is never written as "zero rate".
