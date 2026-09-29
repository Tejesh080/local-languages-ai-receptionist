# 21 - Managed vs Custom

## The two systems
**System A (managed baseline):** Indian number -> Sarvam Voice Agents (ASR, turn-taking, LLM, TTS, transfer, analytics) -> HTTP tools -> **our backend** -> Postgres -> WhatsApp (Meta Cloud API) -> owner summary.

**System B (custom pipeline):** Exotel or Vobiz WebSocket -> Pipecat 1.12 on a Mumbai VM -> Saaras v4 realtime (manual endpointing + our Telugu turn policy + per-call keyterms) -> LLM of our choice inside a state machine (`pipecat.flows`) -> Bulbul v3 streaming -> caller. Same backend, same tools, same database.

**Key insight:** the business backend is identical in both. Only the voice layer differs. So an A/B comparison costs roughly one extra week of work (the Pipecat slice), not a second product.

## Comparison matrix (qualitative; nothing here is MEASURED)
Legend: V = VERIFIED capability exists, VC = vendor claim, U = UNKNOWN, X = not available / not self-serve.

| Dimension | Sarvam Voice Agents | Bolna | Dvaarik dev platform | Retell | Vapi | Custom Pipecat | Custom LiveKit |
|---|---|---|---|---|---|---|---|
| Telugu STT | V (Saaras v4, fixed) | V via Sarvam or others (choose) | U | U (provider-dependent) | V via provider choice | V (any provider) | V (any provider) |
| Telugu TTS | V (Bulbul v3, fixed) | V (choose) | U | U | V via provider | V (any) | V (any) |
| Tenglish / code switching | VC | depends on providers | VC | U | depends | Saaras codemix mode V | same |
| 8 kHz phone performance | VC | depends | U | U | depends | must measure | must measure |
| Keyterm biasing | "Important words" V; dynamic per call U | provider-dependent | U | U | provider-dependent | V (Saaras v4, 50 terms per call) | V |
| Turn detection control | Coarse sliders V | provider / VAD settings | U | U | several endpointing options | Full control (manual endpointing) | Full control; LiveKit model lacks Telugu |
| Barge-in | V | V | U | V | V | V | V |
| Tool calling | HTTP tools V; code tools enterprise | V | V | V | V | Full control | Full control |
| State machine | Multi-state (being retired) V | U | U | U | workflows exist U | `pipecat.flows` V | own code |
| Human transfer | Self-serve on Vobiz V; Exotel via Sarvam; handover enterprise | V (human-in-loop claimed) | U | V | V | Exotel Voicebot -> Transfer applet V; Vobiz SIP V | SIP V |
| Indian numbers | V (rent or BYO) | V (Plivo / Vobiz, needs CIN + GST) | V | SIP only | SIP / BYO | via Exotel / Vobiz | via SIP |
| Recordings / transcripts | V | V | U | V | V | build (cheap) | build |
| Analytics | V (Boards SQL) | V | V | V | V | build (we need our own anyway) | build |
| Eval system | V (simulated tests) | U | U | V | V | build (harness, file 24) | build |
| Versioning | V | U | U | V | V | git | git |
| Per-stage latency traces | U | U | U | U | partial | V (Pipecat metrics + OpenTelemetry) | V |
| Cost/min (API + platform, excl. our infra) | ~Rs3.5 VC + telephony | $0.02 platform + providers (~Rs3.0-4.7) | Rs2 VC | $0.07-0.31 (stale) | $0.05 + providers (stale) | ~Rs1.2-2.9 ESTIMATED | similar + LiveKit infra |
| Lock-in | High (no BYO models, platform config) | Medium | High | Medium | Medium | Low | Low |
| Data portability | API for transcripts / recordings V | U | U | U | U | Full | Full |
| Data residency India | V | U | Phase 1 suggested US hosting (weak evidence) | U | U | Your choice | Your choice |
| Time to first pilot | Days | Days | Days | Days | Days | 1-3 weeks | 2-4 weeks |
| Developer experience for us | MCP + REST + dashboard | dashboard + API | U | good | good | Python, open code | Python / Node |

## What must be measured before choosing (identical scenarios, same backend)
1. Wrong confirmed bookings and hallucinated transactional facts (must be 0 for both).
2. Entity accuracy after clarification (names, phones, dates, times, vehicle numbers).
3. False cutoffs per 100 turns and missed interruptions.
4. End-of-turn to first-audio latency P50 / P95 / P99 measured at the caller side.
5. Task completion and caller repetition rate.
6. Blind native-speaker naturalness scores (Telangana and Andhra panels separately).
7. Cost per successful booking (file 25).

## Why LiveKit is not the default custom option
Exotel and Vobiz deliver audio over WebSocket; Pipecat has an Exotel serializer and Sarvam publishes an Exotel + Pipecat guide. LiveKit's advantages (WebRTC, SIP, turn detector) are either unused or lack Telugu here. LiveKit remains the escape route if we move to SIP trunking at scale.

## Multi-tenant SaaS on System A: open questions to answer in Experiment 1
- Can each tenant be a cloned agent with its own variables and HTTP tool secrets? (docs suggest yes: clone, variables, secrets)
- Do HTTP tool requests include the call id, caller number and called number, so our backend can derive the tenant server-side? UNKNOWN. If not, tenant must be bound per agent via a per-agent secret header, which is acceptable.
- Is there a per-workspace concurrency limit on Starter? UNKNOWN.
- Can we export per-call cost and duration for our ledger? Analytics API suggests duration; cost UNKNOWN.
