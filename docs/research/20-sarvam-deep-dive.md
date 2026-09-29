# 20 - Sarvam Deep Dive

Sarvam now sells three layers that matter to us:
1. **Model APIs** (Saaras STT, Bulbul TTS, LLMs), priced per use.
2. **Voice Agents** (formerly Samvaad), an end-to-end managed voice agent platform on telephony.
3. **Developer tooling**: MCP servers, docs MCP, Context7, Pipecat / LiveKit / Exotel / Vobiz guides.

## 1. Speech-to-text (Saaras)
| Property | Detail | Status |
|---|---|---|
| Models | `saaras:v4` (docs call it default and recommended), `saaras:v3`, `saaras:v3-realtime` (default on the Realtime endpoint). Saarika deprecated | VERIFIED; docs inconsistent about the default |
| Languages | 22 Indian + English; Telugu `te-IN`; `auto` detection | VERIFIED |
| Output modes | transcribe (numbers normalized), verbatim (fillers and spoken numbers kept), codemix (English words stay Latin), translit, translate | VERIFIED |
| Realtime mode caveat | `mode` applies to the final transcript only; partials are always plain transcription | VERIFIED |
| Audio | `linear16`, `linear32`, `mulaw`, `alaw`; mono; `sample_rate` 8000 or 16000 only | VERIFIED |
| Turn detection | `endpointing=vad` (server VAD: `threshold` 0.3, `silence_duration_ms` 500, `min_speech_duration_ms` 250 defaults) or `manual` (client sends speech_start / speech_end / flush) | VERIFIED |
| Live reconfiguration | `config.update`: silence and threshold apply immediately; language, prompt, mode, endpointing at next utterance | VERIFIED |
| Keyterms | v4 only; max 50 terms x 64 chars; set as a connection query parameter (not listed as live-updatable); bias, no guarantee | VERIFIED |
| Prompt | Free-text terminology hint on final transcript | VERIFIED |
| Latency | Streaming TTFT under 150 ms | VENDOR CLAIM |
| Accuracy | V4: lowest average WER on Sarvam's chosen sets; Kathbath Noisy LLM-WER under half of Deepgram Nova-3 and GPT-4o Transcribe; 16.03% WER on IndicContextEval L5 | VENDOR CLAIM (no independent reproduction yet) |
| Billing | Rs30/hour, per second; `session.end.audio_duration_s` is the billed audio | VERIFIED |
| Concurrency | Streaming WebSocket: Starter 20 concurrent, Pro 100, Business 100 | VERIFIED |
| Self-hosting | Saaras v3 on AWS SageMaker documented; v4 not yet | VERIFIED |

**What this means for us**
- Manual endpointing and live `silence_duration_ms` changes let a custom pipeline implement Telugu-specific, state-aware turn-taking on top of Sarvam STT. This was not known in Phase 1 and is the single most useful technical finding for System B.
- Per-call keyterms (doctor names, service names, localities, up to 50) are possible because each call opens its own connection.
- 20 concurrent STT streams on Starter caps a pilot at about 20 simultaneous calls unless upgraded. Enough for 5 pilots.

**V3 vs V4: test both.** V4 adds keyterms and global English. Do not assume V4 is better on 8 kHz Telugu entities. Benchmark configs: v3-realtime; v4; v4 + keyterms; v4 codemix; v4 + keyterms + codemix.

## 2. Text-to-speech (Bulbul v3)
| Property | Detail | Status |
|---|---|---|
| Languages | 11 incl. Telugu `te-IN`; code-mixed input | VERIFIED |
| Voices | 37 named speakers (Shubh default; e.g. Priya, Kavya, Kavitha, Roopa, Anand, Mani, Gokul, Vijay) | VERIFIED; which suit Telugu is UNKNOWN |
| Output | 8, 16, 22.05, 24 kHz (higher on REST only); PCM, mulaw, alaw and others | VERIFIED |
| Streaming | HTTP stream and WebSocket; 2,500 chars per request | VERIFIED |
| Controls | Pace 0.5-2.0, pronunciation dictionary, text preprocessing, sentence splitting, buffer size | VERIFIED |
| Price | Rs30 per 10K characters (Rs3 per 1,000) | VERIFIED |
| Concurrency | bulbul:v3 WebSocket on Starter: 30 concurrent; REST 30 req/min | VERIFIED |
| Quality | Sarvam reports 8 kHz listener preference over ElevenLabs Flash v2.5, v3 alpha and Cartesia Sonic-3 | VENDOR CLAIM |
| TTFA | Not published | UNKNOWN |
| Commercial use | Separate "Commercial Licensing" page for shipping generated audio | VERIFIED exists; terms not reviewed |

## 3. LLMs on Sarvam
Sarvam 105B, 105B Chat, 105B Conversations (tuned for dialogue), Gemma 4 31B, DeepSeek V4 Flash, GLM-5.3 (docs) / GLM 5.2 (marketing page, inconsistent). Prices in 19. The Aug 2026 increase to about 7x is the clearest evidence of vendor price risk.

## 4. Voice Agents platform (System A candidate)
| Capability | What exists | Limits / gaps | Status |
|---|---|---|---|
| Models | Saaras v4 ASR, Bulbul v3 TTS, routed LLMs incl. sarvam-105b-conversations, fine-tuned for tool calling and colloquial code-mixed Indic | **No bring-your-own model at any layer**; no model picker; temperature 0.1-0.9 only | VERIFIED |
| Languages | 11 incl. Telugu; smart language switch; "Output numbers in Indic" | Quality in Telugu UNKNOWN | VERIFIED |
| Turn-taking | Interrupt toggle; Sound sensitivity (Low/Med/High); Eagerness (Patient/Normal/Eager); advanced "Detect when the caller stops talking" | Coarse controls; no state-dependent thresholds visible | VERIFIED |
| ASR hints | "Important words" (hotwords) | Per-tenant dynamic lists UNKNOWN | VERIFIED |
| Tools | HTTP API tool (non-enterprise), validator / verifier (alpha), code tools (enterprise), mocking, on-start / on-end hooks, variables | Whether HTTP tool calls carry caller / called number and a verifiable signature: UNKNOWN (critical for tenant auth) | VERIFIED / UNKNOWN |
| Flow control | Single-state prompt; multi-state agents (being retired for "multi-agent"); workflows (enterprise) | Platform paradigm is changing | VERIFIED |
| Knowledge base | Upload files, retrieval | Not needed for MVP | VERIFIED |
| Call transfer | `call_transfer` core tool to PSTN or SIP; self-serve end to end on Vobiz / Rent from Sarvam; on Exotel only via Sarvam team; run-time page says "human handover" is enterprise | Warm transfer with context: UNKNOWN / enterprise | VERIFIED |
| Telephony | Exotel, Twilio, Smartflo, Pulse, Intalk, Vobiz (bring your own), or Rent from Sarvam (Vobiz underneath, Individual or Corporate KYC, 30-day auto-renew, billed from wallet) | Number prices only visible in catalog | VERIFIED |
| Testing | Tests: simulated user + AI judge, pass/fail per behavior, up to 20 repeats; real test calls | Simulated tests are text-level (audio realism UNKNOWN) | VERIFIED |
| Analytics | Call logs, end reasons, recordings, transcripts, goals, tool analytics, log analyser, Boards (SQL), webhooks, REST API | Per-stage latency traces: UNKNOWN | VERIFIED |
| Versioning | Draft then immutable committed versions; deployments run committed versions | Good fit for our rollback needs | VERIFIED |
| Channels | Telephony, web, API, SDK; WhatsApp voice / text agents enterprise-only | We send WhatsApp from our own backend anyway | VERIFIED |
| Scale | Claims 20,000+ concurrent calls, sub-second latency | VENDOR CLAIM | |
| Data | Self-hosted in India; retention controls; PII masking option | VERIFIED |
| Max call | 60 min | VERIFIED |
| Price | About Rs3.5/min per press; not on public pricing page; check Settings > Plans & pricing | VENDOR CLAIM / UNKNOWN |

## 5. Can Sarvam already do most of what we planned?
Yes for: telephony glue, orchestration loop, VAD / barge-in, versioning, analytics, simulated test runs, Telugu ASR and TTS, number rental.

No (or not self-serve) for: our own Telugu turn-taking logic, dynamic per-state endpointing, per-stage latency and cost ledger, model choice, warm transfer on Exotel, tenant-aware authorization inside tool calls (depends on the UNKNOWN above), real-audio regression benchmark.

Always ours regardless: the vertical backend (tenants, services, slots, bookings, callbacks), WhatsApp confirmations, owner summaries, entity resolution against tenant data, evaluation datasets, onboarding, distribution.

**Strategic caution:** Sarvam sells to enterprises (Axis Bank, CRED, Tata Capital, Urban Company, IndiaMART are listed as customers). If a Telugu SMB receptionist becomes attractive, Sarvam can build it. Using System A means our moat must live entirely in the vertical layer and data.
