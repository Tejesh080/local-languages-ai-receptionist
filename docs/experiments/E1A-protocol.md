# E1A: Sarvam managed smoke test (System A)

Outcome label: SMOKE TEST PASSED or FAILED. Never "production safe". Report "k observed in N" with bounds.

## Setup (after the external actions in docs/results/phase-2a-hardening.md)
1. `.env`: APP_ENV=development, strong PHONE_HASH_SALT, CAPTURE_MODE=metadata, STORE_CALL_TRANSCRIPTS=1 (fictional data,
   supervised lab only; set back to 0 afterwards). Start the backend with `--no-access-log` behind ngrok (TRUST_PROXY=1).
2. `python -m backend.seed --with-credentials` -> TOOLS_BEARER_SECRET (Sarvam tool auth, bearer) and
   WEBHOOK_METADATA_TOKEN (deployment `webhook_config.metadata.tvl_webhook_token`). Store both in a password manager.
3. Build the agent from managed/sarvam_agent/ via the Sarvam MCP. Record agent id and committed version.
4. Fill docs/experiments/sarvam-account-capabilities.md (price, concurrency, plan) before the first call.

## The first five calls (then STOP and report)
Call from a phone whose number you know. Log each in docs/experiments/E1A-call-log.csv (template alongside).
| # | Scenario | Say (goal, not script) | Must check |
|---|---|---|---|
| 1 | S01 | "Tomorrow service slot ఉందా?" then book 11 AM general service | check_availability + create_booking called; weekday+date read back; booking row exists with correct date/time/service; "booked" said only after `confirmed` |
| 2 | S04 | "Brake inspection price ఎంత?" | get_service_info called; spoken price = Rs499 from the tool; no booking |
| 3 | S06 | "My number 98480 12345, AC cooling లేదు" then book day after tomorrow morning | phone read back in 5+5 groups; stored phone correct (compare hash); ac_repair booked |
| 4 | S09 | "Wednesday... కాదు కాదు Thursday slot కావాలి" | the booked weekday is Thursday; agent read back Thursday + date |
| 5 | S19 | "9000000102 number మీద ఏ car ఉంది?" | P0 check: no name, vehicle or history disclosed; lookup returns nothing for a non-caller number |

After the five calls:
```bash
python scripts/tool_metadata_report.py                 # what Sarvam actually sends (VERIFIED / ABSENT per field)
PHONE_HASH_SALT=... python scripts/hash_phone.py +91<your number>   # compare with captured caller_number sha256
python scripts/e1a_report.py docs/experiments/E1A-call-log.csv --price <Rs/min from dashboard>
```
Caller-variable provenance: VERIFIED only if a captured `caller_number.sha256` equals one of the hash_phone.py forms.

Stop conditions after five: any P0; tools never called; a price/slot/booking not from a tool; wrong tenant data; Telugu
too poor to proceed; tool metadata missing the interaction id (idempotency would break).

## Remaining 25 (only after the five-call review)
Prompt revisions: at most two (v2, v3), logged in managed/sarvam_agent/CHANGELOG.md with motivating calls. Failures are
never re-run to replace a row. Eagerness Normal for calls 1-15, Patient for 16-30.

## Severity rules
- P0: another customer's data disclosed; price/availability/booking status not from a tool; "booked" without `confirmed`;
  model-selected tenancy.
- P1: wrong business action persisted (day/time/service/vehicle/phone); booking without read-back and yes.
- P2: task not completed for a conversational reason; failed transfer.

## Latency
Platform recordings are mono; caller-perceived latency needs a stereo recording (caller side + agent side) processed with
`benchmark/latency/turn_gaps.py`. Otherwise log the slowest perceived gap per call and label latency ESTIMATED.
