# 31 - Phase 1.5 Decision

## 1. What changed (ten most important discoveries)
1. **Sarvam Voice Agents is public** (Jul-Aug 2026): telephony, tools, transfer, versioning, simulated tests, SQL analytics, retention controls and an MCP server. Much of what Phase 1 planned to build already exists as a managed product.
2. **Saaras V4 shipped** (Sep 2026) with keyterm prompting (v4 only, 50 terms), a codemix mode that keeps English words in Latin script, and realtime streaming.
3. **Sarvam's realtime STT supports manual endpointing and live VAD retuning.** A custom stack can implement Telugu-aware, state-dependent turn-taking without training a model.
4. **Managed Voice Agents allows no model choice** and has coarse turn controls. Warm human handover is enterprise; self-serve transfer works only on Vobiz / Rent from Sarvam.
5. **Sarvam raised sarvam-105b prices about 7x** on 5 Aug 2026. Vendor price risk is real, not theoretical.
6. **Still no Telugu semantic turn detector** anywhere checked: LiveKit (14 languages), Smart Turn v3.2 (23), Deepgram Flux Multilingual (10).
7. **Bolna is a $0.02/min platform fee** on top of providers you connect, not a flat 6 cents.
8. **Telephony is an onboarding task:** Rent from Sarvam offers Individual KYC; Udyam + GST as a sole proprietor likely satisfies Exotel, Plivo and Vobiz.
9. **At pilot scale, per-minute price is economically irrelevant.** About Rs22 per booking vs an average car service ticket in the thousands. Quality and wrong-booking risk dominate.
10. **Pipecat is at v1.12 with Flows in core;** a state-machine dialogue layer is available off the shelf for System B.

## 2. What Phase 1 got wrong
- **Missed the Sarvam Voice Agents platform entirely.** The biggest error. It led to recommending a custom Pipecat stack before checking whether managed covered the need (premature architecture decision).
- **Outdated STT picture:** treated Saaras V3 as current and implied keyterms were available on it; keyterms are V4-only.
- **Price errors:** Bolna "6 cents/min" (that is a bundle view; platform fee is $0.02 + providers); Sarvam agents "Rs1/min" (a 2024 launch price; 2026 pitch is about Rs3.5); did not report the sarvam-105b 7x price increase.
- **Overstated the turn-detection gap:** said no Telugu turn detection exists, ignoring Sarvam's server VAD, manual endpointing and live retuning. The real gap is semantic Telugu turn detection only.
- **False precision:** per-stage latency numbers were mostly invented; vertical scoring totals looked objective but were not; the cost table divided fixed costs into 100 minutes (Rs152.5/min), which is meaningless as a voice cost.
- **Wrong blocker:** foreign-founder RED rating.
- **Weak evidence presented firmly:** "Dvaarik appears US-hosted" rested on third-party site profiles; downgraded to UNKNOWN.
- **Unfinished:** GitHub due diligence was skipped (done now in 19).

## 3. Current best architecture (to validate, not yet chosen)
Default candidate for the first pilot is **Architecture 1**: Sarvam Voice Agents (Saaras v4, Bulbul v3, managed turn-taking and transfer) on a Rent-from-Sarvam / Vobiz number, calling **our** backend (FastAPI + Postgres with RLS, Mumbai) through signed HTTP tools, with our entity resolver, WhatsApp via Meta Cloud API, owner daily WhatsApp summary, cost ledger and eval harness.

## 4. Why
It is the shortest path to real callers, it is Telugu-native per vendor, India-hosted, versioned and testable, and everything we build (backend, resolver, datasets, harness, WhatsApp, onboarding) is portable to Architecture 2. The part we would give up (orchestration) is exactly the part Phase 1.5 found we should not own unless measurements demand it.

## 5. Second-best architecture and when it wins
**Architecture 2:** Exotel / Vobiz -> Pipecat 1.12 -> Saaras v4 realtime with our Telugu turn policy and per-call keyterms -> benchmarked LLM in a `pipecat.flows` state machine -> Bulbul v3. It wins if E10 shows materially fewer P0/P1 errors, entity errors or false cutoffs; if A lacks tool-call metadata for tenant auth; if we need warm transfer on Exotel; or above about 100k min/month.

## 6. What we should buy
Telephony, STT, TTS, LLM, managed orchestration (initially), Postgres hosting, WhatsApp API, error monitoring.

## 7. What we should build
Vertical backend and tool API, deterministic booking rules, entity resolution layer, Telugu turn policy (for B), benchmark harness, datasets A-F, warm-transfer context message, owner daily summary, per-call cost ledger, onboarding form.

## 8. What we should not build yet
Outbound, RAG, dashboard beyond a call list, billing, other languages, voice cloning, self-hosted models, Kubernetes, custom telephony, CRM marketplace, white-label, a trained turn model.

## 9. Expected marginal cost per minute
- System A: about **Rs3.5-4.3** = platform (about Rs3.5, vendor claim) + telephony (Rs0-0.8 if not included).
- System B: about **Rs1.2-2.9** = STT (0.50 x s_frac) + TTS (0.003 x 60 x r_agent x cps) + LLM (turns x token cost) + telephony.
See file 25 for inputs and formulas.

## 10. Expected latency
- System A: sub-second per vendor (VENDOR CLAIM), measured from the platform, not the caller's ear.
- System B (ESTIMATED): P50 about 1.0-1.5 s, P95 about 2-3 s from end of caller speech to first audio heard, assuming 500-800 ms endpoint silence, 100 ms telephony frames, Saaras partials streaming, small-LLM first token under about 500 ms, Bulbul TTFA UNKNOWN, all hosted in Mumbai. Longer when the caller is giving a number (by design).

## 11. Biggest remaining uncertainties (ranked)
1. Telugu conversational quality on real phone calls (any system).
2. Entity accuracy on 8 kHz Telugu (names, numbers, vehicle registrations).
3. Willingness to pay and the best vertical.
4. False cutoff rate with available endpointing.
5. System A tool-call metadata, pricing and concurrency.
6. Conditional call forwarding behaviour across Indian operators.
7. Sarvam platform and price stability.

## 12. First benchmark (exact implementation)
**Real-phone Telugu entity STT benchmark v0**
1. Rent one number (Rent from Sarvam). Point it at a 60-line Pipecat recorder bot: greet, play prompt audio N, beep, record 12 s, repeat for 50 prompts.
2. Prompts: 50 entity-heavy receptionist lines per speaker (names incl. Reddy / Rao / Naidu / Chowdary, localities like Kukatpally, Benz Circle, Tirupati bus stand, 10-digit mobiles, "TS 09 EA 4521" style registrations, dates, "సాయంత్రం five thirty", rupee amounts, service names).
3. 20 speakers (8 Telangana, 8 Coastal Andhra, 4 Rayalaseema), own phones, at least 3 carriers, 25% on speakerphone or outdoors. Paid by UPI.
4. Label with the labeler (reference transcript in codemix form + entity spans).
5. `stt_runner.py` streams each 8 kHz file at real-time pace to: saaras:v3-realtime, saaras:v4, saaras:v4 + 50 keyterms (from the mock tenant), saaras:v4 codemix, Deepgram Nova-3 te (+ others if Telugu is confirmed). Log partial and final timestamps.
6. `normalize.py` then `entities.py` and `wer.py`. Report entity exact-match by class, WER, CER, P50 / P95 final latency, cost per hour.
7. Store everything in `results/` keyed by run id; publish a static HTML report.

## 13. Next 10 experiments
E1 managed baseline + competitor calls; E2 customer discovery (parallel); E3 phone audio collection line; E4 STT bake-off; E5 custom slice + call forwarding test; E6 turn-taking replay; E7 entity resolver; E8 TTS listening test; E9 dialogue control design test; E10 A vs B head-to-head. Details in file 28.

## 14. Accounts / API keys
Now: Sarvam (+ Voice Agents MCP), Rent-from-Sarvam number, Vobiz or Exotel, Deepgram, Bolna, GitHub + token, Postgres host, Mumbai VM, ngrok, domain. Optional now: ElevenLabs, OpenAI, Google. Later: Meta developer + WhatsApp Business, Udyam + GST + current account, Sentry / Langfuse. Details in file 29.

## 15. Ultra-lean budget
About **Rs25,000-40,000** to first pilot (file 29).

## 16. Serious MVP budget
About **Rs1.5-3.2 lakh** for three months with 5 pilots (file 29).

## 17. 30-day action plan
- **Days 1-3:** Sarvam account and credits; install Voice Agents MCP; rent a number (Individual KYC); register Udyam; start booking 20 discovery interviews (auto service first).
- **Days 3-7 (E1):** Build the service-centre agent on Voice Agents with 4 HTTP tools to a mock backend; 30 scripted calls; call Bolna and Dvaarik demos; answer the System A open questions.
- **Days 5-14 (E3):** Deploy the recorder line; recruit 20 speakers; collect and label 1,000 utterances.
- **Days 8-21 (E2):** Run interviews; score vertical pain and willingness to pay.
- **Days 12-18 (E4):** STT bake-off report.
- **Days 15-25 (E5):** Pipecat slice on Exotel / Vobiz with tracing and cost ledger; test conditional forwarding on Jio and Airtel.
- **Days 20-28 (E7, E9):** Entity resolver and dialogue control tests at text level.
- **Day 30:** Founder review: vertical choice, STT config, whether A already meets the bar, go / no-go for E6, E8, E10.

## 18. Go / no-go conditions
- **GO to pilot on A** if E1 + E4 + E7 show: 0 P0/P1 in 30 scripted calls, entity accuracy after clarification 95% or more, native rating 4 / 5 or more, and E2 finds 8+ businesses with real missed-call pain and Rs3,000+ willingness to pay.
- **GO to B** if A fails on turn-taking, entities or tenant-auth metadata and B's slice fixes it in E10 by a clear margin.
- **PIVOT vertical** if automotive interviews show low missed-call pain or no willingness to pay; test diagnostics next.
- **STOP or rethink** if no configuration reaches 95% entity accuracy after clarification on real phone audio, or if fewer than 3 of 20 businesses would pilot even for free.

## Most important decision
**D. Evidence is insufficient; run a direct A/B benchmark before choosing.**
With a stated default: build everything portable now (backend, resolver, harness, datasets) and use System A for the first pilots unless E1 / E10 show it fails. Custom orchestration (B) must earn its place with measured quality gains, not because it is more interesting to build.
