# E1A: Sarvam managed smoke test (System A)

**Goal:** make one real managed Telugu receptionist work end to end and record what breaks. Outcome label: SMOKE TEST PASSED
or FAILED, never "production safe".

## Steps
1. Deploy the backend with a public HTTPS URL (README: ngrok for the first 5 calls; a stable host before E1B).
2. `python -m backend.seed --with-credentials` -> store TOOLS_BEARER_SECRET and WEBHOOK_PATH_SECRET.
3. Build the agent (managed/sarvam_agent/claude_code_setup.md). Record agent id and committed version.
4. Fill docs/experiments/sarvam-account-capabilities.md from the dashboard (price, concurrency, plan).
5. **First 5 calls (checkpoint):** S01, S04, S06, S09, S19 from benchmark/scenarios/e1a_smoke.yaml. Log each row in
   docs/experiments/E1A-call-log.csv (copy the template). Then run:
   `python scripts/tool_metadata_report.py` and `python scripts/e1a_report.py docs/experiments/E1A-call-log.csv --price <Rs/min>`.
   Stop and review if any call shows: tools never called, a spoken price/slot/booking not from a tool (P0/P1), wrong tenant
   data, or Telugu so poor the scenario cannot proceed.
6. Remaining 25 scenarios. Prompt revisions: at most two (v2, v3), each logged in managed/sarvam_agent/CHANGELOG.md
   with the failing calls that motivated it. Calls are never re-run to replace a failure; a re-run is a new row.
7. Eagerness: Normal for calls 1-15, Patient for 16-30 (cheap cutoff-vs-latency comparison).

## Severity rules for the log
- P0: another customer's data revealed; price, availability or booking status not returned by a tool; "booked" said
  without a `confirmed` tool response; model-selected tenancy.
- P1: wrong business action (wrong day/time/service/vehicle/phone persisted), booking created without read-back and yes.
- P2: task not completed for a conversational reason (repeated 3+ times, stuck, hung up), failed transfer.
- Entity errors: list as `type:heard->expected` separated by `;`.

## Latency
Mono platform recordings cannot separate speakers. If you record the call on the caller side in stereo (or via a second
line), run `python benchmark/latency/turn_gaps.py call.wav`. Otherwise record the slowest perceived gap per call in seconds
and label latency ESTIMATED.
