# Phase 2A: lab hardening before real calls

Date 2026-09-30. Scope: measurement and security fixes only. No System B, no SaaS, no provider calls, no paid usage.
Tests: 21 before -> **57 passing** (36 added), including a real PostgreSQL 16.2 concurrency test.

## 1. What changed and bugs fixed
| # | Area | Problem found | Fix | Evidence |
|---|---|---|---|---|
| 1 | STT latency | `final - WAV_duration` counted the recorder's ~1.5 s trailing silence; understated latency by >1 s in a reproduction | Speech timing stored per utterance; replay chunk boundary at speech end; single monotonic clock; premature finals flagged, never averaged (decision 0002) | test_latency_ground_truth (8) |
| 2 | Raw data | Utterance WAVs were the only copy | `session_raw.wav` master; utterances are exact read-only slices with sha256; derived segments content-addressed; sha re-checked before every run | recorder + quality tests |
| 3 | Privacy | RequestCapture and ToolCallLog stored full request/response bodies (phone, name, vehicle, free text); webhook stored raw payload and transcript | Default redaction: phones salted-hashed, registrations masked+hashed, names/free text length only, unknown fields keep only the key; PII debug mode explicit, off by default, forbidden in production | test_default_capture_and_logs_contain_no_pii |
| 4 | Secrets | `PHONE_HASH_SALT=change-me` accepted; no environment mode | APP_ENV test/development/production; unset = production (fail closed); weak/placeholder salts, SQLite, PII capture and transcript storage rejected in production; errors never echo secrets | test_config (9) |
| 5 | Credentials | A webhook secret could authenticate tool calls and vice versa (found during this pass) | Credentials carry a purpose (`tools` / `webhook`) | test_credential_purposes_are_not_interchangeable |
| 6 | Webhook auth | Secret in URL path (lands in proxy/ngrok/access logs) | Body token via `webhook_config.metadata` (only mechanism Sarvam offers: PLATFORM LIMITATION), idempotent upsert, cross-tenant overwrite rejected, `--no-access-log` (decision 0003) | test_webhook_auth_and_privacy |
| 7 | Caller identity | Caller-ID match returned full name and full registration | Identification only: masked vehicles on caller-ID match, nothing for other numbers, `authenticated: false` constant, `identity_assurance` field; HIGH actions not implemented (decision 0004) | test_lookup_is_identification_not_authentication |
| 8 | Booking concurrency | Concurrent retries of the SAME request could get "unavailable" when their own twin took the last seat (inferred from the code path) | Re-check the idempotency key after a failed claim; commit only inside the successful-claim branch | PostgreSQL test below |
| 9 | Postgres | Seed insert order violated foreign keys on PostgreSQL; SQLite never enforces FKs by default, so tests hid it | Parent-first flushes; SQLite now enforces FKs in tests | test_seed_runs_on_postgres |
| 10 | Recorder sync | Recording started when a local sleep expired, ignoring Exotel's mark | Waits for the mark acknowledgement (documented: "sent when audio you previously sent has finished playing"); timeout fallback recorded as `mark_method` | recorder tests (5) |
| 11 | Recorder VAD | VAD frames not aligned to the mark: normal speech flagged as "talked over the beep" | Pre-roll is a whole number of frames; one-frame tolerance otherwise | test_normal_mark_and_immediate_speech |
| 12 | Sarvam adapter | Schema types `audio_duration_s` as a string; session request_id/config not kept | Tolerant float parsing; session.begin stored for provenance; `vad.speech_end` timing recorded; header `API-Subscription-Key` per current reference | fake-server tests |
| 13 | Paid-run safety | A broken adapter could write 1,000 error rows | `python -m benchmark.preflight` (key, reachability, config accepted, fixture transcribes) required by default; `benchmark.smoke`; circuit breaker after 5 consecutive initial failures (failures still recorded) | test_preflight (5) |
| 14 | Data quality | No validation or exclusion discipline | `benchmark.quality`: format, duration, silence, clipping, speaker metadata, consent ref, prompt, entity annotations, partition, condition, sha; exclusions require reason + excluded_by; analysis manifest blocked while blocking items are undecided | test_quality (3) |
| 15 | E7 evidence | Same cases used to find a bug and to re-evaluate | Development set vs single-use holdout (guard refuses re-runs per resolver version) | below |

## 2. Measurements from this phase
**PostgreSQL concurrency: MEASURED** (PostgreSQL 16.2 via embedded `pgserver`, 20 threads each with its own
transaction, released by a barrier):
- 20 different callers, one seat: 1 confirmed, 19 unavailable, 1 booking row, `slot.booked`=1, one reference.
- 20 concurrent retries of the same request: 20/20 confirmed with the same reference, 1 row, `slot.booked`=1.
Not yet measured on a managed cloud Postgres or under network latency.

**E7 holdout: MEASURED on synthetic text only** (single run, resolver `res-94e84f0b967c`,
docs/results/E7-holdout-res-94e84f0b967c.md):
- Silent wrong resolutions: 0 observed in 63 (names N=37 upper bound 7.8%; services N=16; registrations N=10).
- Names: top-1 28/28; unknown names rejected only 4/6: "Venkatesh Rao" -> proposed "Venkat Rao", "Ravi Teja" -> proposed
  "Sai Teja" (not silent, but it would speak a customer's name: now forbidden by decision 0004 rule 1);
  Telugu-script "అంజలి చౌదరి" fell below threshold (no_match).
- Services: 4 of 12 valid phrasings fell below threshold ("periodic maintenance", "ఏసీ పనిచేయట్లేదు", "battery down",
  "వీల్ బ్యాలెన్సింగ్"): a repeat-request cost, not a wrong booking. Not tuned against the holdout.
- Registrations: correct top-1 7/7. The two "failures" listed for unknown registrations are a reporting-code
  inconsistency: the resolver correctly offered them as NEW vehicles for character read-back and the metric counted them
  as not matched to a record. Listing code fixed for future holdouts only; resolver unchanged.
Synthetic holdout results are not evidence of real-STT robustness.

## 3. Remaining risks
1. Everything provider-side is still UNKNOWN: Sarvam tool metadata, caller-variable provenance, webhook source IP,
   Voice Agents price and concurrency, real transcripts, real latency.
2. Provider adapters are tested against fake servers built from the current docs; the real services may differ
   (preflight and smoke exist to catch this before paid runs).
3. Exotel echoing the mark `name` and continuous inbound media during playback are INFERRED; per-prompt `mark_method`
   exposes violations.
4. Energy VAD on noisy PSTN audio is untested; the quality gate re-computes it offline and flags disagreement.
5. STT latency here is endpointing latency only; caller-perceived latency needs stereo call recordings.
6. Holdout written by the resolver's author; services threshold likely too strict (4/12 no_match).
7. `STORE_CALL_TRANSCRIPTS=1` is needed for E1A analysis; turn it off after the lab run; no retention policy yet.
8. The preflight fixture is synthetic espeak-ng Telugu (plumbing only, never accuracy).

## 4. Still UNKNOWN (not measured)
Managed Sarvam Telugu quality; tool metadata fields; User Identifier provenance; webhook IP; per-minute price;
concurrency limits; STT entity accuracy on PSTN; endpoint latency on real providers; keyterm effect; Tenglish
performance; caller-perceived latency; real cost per call/booking; native-speaker ratings; Exotel mark behaviour in production.

## 5. Accounts and actions required from you
| Needed for | Action | Who |
|---|---|---|
| E1A (now) | Sarvam account; add credits (about Rs2,000 is ample for 5 calls + preflight) | you |
| E1A | In Claude Code: `claude mcp add --transport http sarvam-voice-agents https://mcp.sarvam.ai/voice-agents`, then `/mcp` > Authenticate | you |
| E1A | Rent one number from Sarvam (Individual KYC) | you |
| E1A | Read Settings > Plans & pricing and Usage: record price/min, concurrency, plan | you |
| E1A | Run backend + ngrok on your machine; generate PHONE_HASH_SALT; seed credentials | you (commands in E1A protocol) |
| E1A | Create a Voice Agents API key (X-API-Key) if you prefer REST over MCP for setting `webhook_config` | you |
| E4 preflight | Sarvam API key (dashboard) | you |
| E4 preflight | Deepgram API key (optional comparator; approve paid usage) | you |
| E3 | Exotel account with KYC and Voicebot applet enabled (ask Exotel to enable streaming if missing) | you |
| E3 | Recruit and consent 20 speakers; pay via UPI | you |

## 6. Exact first five real calls
S01, S04, S06, S09, S19 as specified in docs/experiments/E1A-protocol.md, from a phone whose number you know, then
run tool_metadata_report.py, hash_phone.py and e1a_report.py and stop for review.
