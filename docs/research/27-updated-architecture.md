# 27 - Updated Architecture

## Architecture 1: Fastest to real customer (managed voice)
```
Caller -> business number (conditional forward on busy/no-answer) -> AI number (Rent from Sarvam / Vobiz)
      -> Sarvam Voice Agents (Saaras v4, turn-taking, LLM, Bulbul v3, call_transfer)
      -> HTTP tools (signed, per-tenant secret) -> Our backend (FastAPI + Postgres, Mumbai)
      -> WhatsApp confirmation (Meta Cloud API) + owner daily summary
Human transfer: Sarvam call_transfer on Vobiz + our WhatsApp context message to staff first
```
- Build only: backend, tools API, entity resolver, WhatsApp, owner summary, cost ledger ingestion from Sarvam analytics API, eval harness.
- Time to pilot: about 2-3 weeks. Marginal cost about Rs3.5-4.3/min (to be verified).

## Architecture 2: Best expected quality and flexibility (own orchestration, managed speech)
```
Caller -> Exotel ExoPhone (Voicebot applet, 8 kHz) or Vobiz stream
      -> Pipecat 1.12 on Mumbai VM
           Silero VAD + Saaras v4 realtime (manual endpointing, per-call keyterms, codemix mode)
           Telugu turn policy (rules + state-dependent silence)
           pipecat.flows state machine; LLM chosen by benchmark (small model default, larger on escalation)
           Bulbul v3 streaming TTS (+ cached short acknowledgements if measured useful)
      -> same backend, tools, WhatsApp, ledger
Observability: OpenTelemetry spans per stage -> Langfuse / Grafana; Sentry for errors
```
- Time to pilot: about 4-6 weeks. Marginal cost about Rs1.2-2.9/min.

## Architecture 3: Long-term lowest cost at scale
Architecture 2 plus: negotiated SIP trunk telephony; self-hosted STT (Saaras v3 on SageMaker, or a fine-tuned open model) and possibly TTS where measured quality holds; cheapest adequate LLM with prompt caching; Telugu turn model. Only above about 1M minutes/month and only for the component that dominates COGS.

## Migration triggers
| From | To | Trigger |
|---|---|---|
| 1 | 2 | Any of: (a) A/B shows B materially better on P0/P1, entity accuracy or false cutoffs; (b) volume above about 100k min/month (file 25 break-even); (c) a required feature blocked on A (warm transfer on our telephony, dynamic turn policy, per-stage traces, tenant auth metadata in tool calls); (d) Sarvam pricing or terms change adversely |
| 2 | 3 | Above about 1M min/month and one component above 40% of COGS with a measured self-host alternative within quality tolerance |

## Conversation control: fully generative vs state machine (to be measured)
| Design | Description | Hypothesis |
|---|---|---|
| Fully generative | One prompt, tools, LLM decides everything | Most natural; highest risk of skipped confirmations |
| LLM + state machine | States gate tools and required fields; LLM handles language inside each state | Best balance for booking |
| Deterministic workflow + LLM language layer | Code decides next step; LLM only parses and phrases | Most reliable, least flexible; good for status and price lookups |

Booking state machine (B, or A via backend-enforced checks):
`INTENT_BOOKING -> IDENTIFY_SERVICE -> IDENTIFY_VEHICLE_OR_PROVIDER -> IDENTIFY_DATE -> GET_AVAILABILITY -> SELECT_SLOT -> CONFIRM_DETAILS -> CREATE_BOOKING -> VERIFY_BOOKING -> CONFIRM_TO_CALLER`

On System A the same guarantees are enforced in the backend: `create_booking` rejects requests missing a `confirmation_token` that is only issued by `confirm_details`, so the LLM cannot skip confirmation.

## Transactional tool contract (both systems)
Every write tool: validate schema -> authorize (tenant derived from called number or per-agent secret, never from LLM output) -> idempotency key (call_id + intent + slot) -> execute -> read back from DB -> return `{status: "confirmed", booking_id, slot}` or `{status: "failed", reason}`.
Agent policy: never say "booked" unless the tool returned `confirmed`. On timeout or failure: "ఆ slot confirm చేయడంలో problem వస్తోంది అండి. మీకు callback arrange చేయమంటారా?" and create a callback request.

## Entity resolution layer (ours, both systems)
1. Normalise: Unicode NFC, Telugu digits to ASCII, number words (Telugu and English) to digits, time words ("సాయంత్రం 5") to 24 h.
2. Candidates: tenant tables via `pg_trgm` similarity on transliterated (Latin) and native forms; Indic phonetic key (collapse aspirates, retroflex vs dental, vowel length, doubled consonants; e.g. Reddy / Ready / Redi share a key).
3. Decide: one strong candidate -> confirm ("Srinivas Reddy గారేనా?"); two or more -> disambiguate on the differing attribute ("Reddy గారా, Rao గారా?"); none -> ask to repeat or spell, then transfer / callback.
4. Always read back: phone numbers (in groups), dates with weekday, times, prices, vehicle registrations. Validate formats deterministically (10-digit mobile starting 6-9; registration regex for TS, AP and BH series).
5. Feed tenant names as per-call keyterms (Saaras v4, up to 50) on B; "Important words" on A.

## Data model (initial)
organizations, locations, phone_numbers, agents, agent_versions, services, staff, business_hours, slots, customers, vehicles, bookings, callbacks, calls, call_events, transcripts, tool_calls, call_cost_ledger, whatsapp_messages, consents, eval_runs, eval_results. Every table carries `org_id`; Postgres row-level security keyed on `org_id` from the server session.

## What NOT to build yet
Outbound calling, RAG / vector DB, owner web dashboard beyond a call list, billing, multi-language beyond Telugu + English, voice cloning, self-hosted models, Kubernetes, CRM marketplace, white-label, custom SIP or WebRTC infrastructure, our own telephony gateway.
