# 30 - Phase 1.5 Evidence Ledger

| Claim | Status | Source | Source date | Last verified | Notes |
|---|---|---|---|---|---|
| Saaras V4 released, 22 Indian languages + English, 5 output modes | VERIFIED | marktechpost.com; docs.sarvam.ai models/saaras | 26 Sep 2026 | 30 Sep 2026 | |
| Saaras V4 best WER / under half of Nova-3 and GPT-4o Transcribe on Kathbath Noisy | VENDOR CLAIM | Sarvam via MarkTechPost | Sep 2026 | 30 Sep 2026 | No independent reproduction |
| Saaras streaming TTFT under 150 ms | VENDOR CLAIM | Sarvam | Sep 2026 | 30 Sep 2026 | Measure in E4 |
| Keyterms: v4 only, 50 terms x 64 chars, REST / Batch / both WebSockets | VERIFIED | Sarvam changelog 9 and 22 Sep; keyterms page | Sep 2026 | 30 Sep 2026 | Saaras model page still says REST / Batch only (stale) |
| Realtime API: 8 / 16 kHz, mulaw / alaw, VAD in ms, manual endpointing, config.update | VERIFIED | Sarvam realtime-streaming docs | 2026 | 29 Sep 2026 | |
| Default model: docs say v4 default (model page) and v3-realtime default (realtime page) | VERIFIED CONFLICT | Sarvam docs | 2026 | 30 Sep 2026 | Always set model explicitly |
| STT Rs30 / hr; Bulbul v3 Rs30 / 10K chars | VERIFIED | docs.sarvam.ai pricing; sarvam.ai/api-pricing | 2026 | 29 Sep 2026 | |
| sarvam-105b raised about 7x on 5 Aug 2026 | VERIFIED | Sarvam changelog | Aug 2026 | 30 Sep 2026 | Price-risk evidence |
| Free credits Rs100 | VERIFIED | Sarvam ratelimits / pricing docs | 2026 | 29 Sep 2026 | Third-party pages still say Rs1,000 |
| STT streaming concurrency Starter 20; Bulbul v3 WS Starter 30 | VERIFIED | Sarvam ratelimits | 2026 | 29 Sep 2026 | |
| Voice Agents: no BYO models; routed LLMs; temperature only | VERIFIED | Sarvam Voice Agents models / settings | 2026 | 29 Sep 2026 | |
| Voice Agents: call_transfer self-serve on Vobiz only; Exotel via Sarvam; human handover enterprise | VERIFIED | Sarvam call-transfer, run-time | 2026 | 29 Sep 2026 | |
| Voice Agents: Tests, MCP server, Boards, retention, versioning | VERIFIED | Sarvam changelog and docs | Sep 2026 | 30 Sep 2026 | |
| Voice Agents price about Rs3.5 / min | VENDOR CLAIM | Inc42 | Aug 2026 | 30 Sep 2026 | Check dashboard |
| Rent from Sarvam supports Individual and Corporate KYC | VERIFIED | Sarvam rent-from-sarvam docs | 2026 | 29 Sep 2026 | Exact documents UNKNOWN |
| Pipecat v1.12.0 (26 Sep 2026), BSD-2 | VERIFIED | GitHub | Sep 2026 | 30 Sep 2026 | |
| Pipecat Flows merged into core from 1.5.0 | VERIFIED | pipecat-flows README | 2026 | 30 Sep 2026 | |
| LiveKit agents 1.8.3; turn detector no Telugu | VERIFIED | GitHub; LiveKit docs | Sep 2026 | 30 Sep 2026 | |
| Smart Turn v3.2 no Telugu; open training data | VERIFIED | smart-turn README | 2026 | 30 Sep 2026 | |
| Deepgram Flux Multilingual 10 languages, no Telugu | VERIFIED | Deepgram changelog | Apr 2026 | 30 Sep 2026 | |
| ElevenLabs Flash v2.5 languages exclude Telugu | VERIFIED | ElevenLabs models page | 2026 | 30 Sep 2026 | v3 Telugu UNKNOWN |
| Exotel supports 8 / 16 / 24 kHz on Voicebot URL; about 60 min session cap | VERIFIED | Sarvam Exotel guide | 2026 | 29 Sep 2026 | |
| Exotel inbound Rs0.40-0.75 / min | Secondary, dated | dialnexa.com (historical tariff) | 2026 article | 30 Sep 2026 | Get a quote |
| Vobiz inbound from $0.0055 / min; number from $1 / month | Secondary | Capterra / GetApp listing | 2026 | 30 Sep 2026 | |
| Bolna platform fee $0.02 / min, BYO providers | VERIFIED | Bolna docs | 2026 | 30 Sep 2026 | Phase 1's 6 cents figure was the bundle view |
| Average car service spend Rs4,390 (India CSI 2021) | VERIFIED (dated) | J.D. Power press release | 2021 | 30 Sep 2026 | Old; use only as order of magnitude |
| System B marginal Rs1.2-2.9 / min | ESTIMATED | File 25 | | | Telephony and usage assumptions |
| A to B break-even about 100k min / month | ESTIMATED | File 25 | | | |
| Dialogue-state-dependent silence reduces false cutoffs | HYPOTHESIS | File 23 | | | E6 |
| Telugu verb-final continuation rules | HYPOTHESIS | File 23 | | | E6 |
| Automotive service is the best first vertical | HYPOTHESIS | File 31 | | | E2 |

## UNKNOWN list (ranked by impact)
1. Real Telugu conversational quality of Sarvam Voice Agents on 8 kHz calls (E1).
2. Whether Voice Agents HTTP tools carry caller / called number and a verifiable signature (E1).
3. Voice Agents actual per-minute price and whether telephony is included (E1).
4. Entity accuracy of Saaras v3 vs v4 (with keyterms) on Telugu phone audio (E4).
5. False cutoff rate of available endpointing on Telugu (E6).
6. Willingness to pay per vertical (E2).
7. Conditional call forwarding support and charges per Indian operator (E5).
8. Bulbul v3 TTFA and Telugu voice naturalness (E8).
9. Exotel current tariff and Voicebot enablement terms (quote).
10. Telugu tool-calling accuracy of small LLMs (E9).
