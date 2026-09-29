# 28 - Next 10 Experiments (priority order)

Each experiment resolves one uncertainty. Costs are ESTIMATED in INR and exclude your time.

### E1. Managed baseline plus competitor calls
- **Question:** How good is Telugu on Sarvam Voice Agents (and Bolna, Dvaarik) today, on a real phone?
- **Method:** Build a two-wheeler / car service-centre receptionist on Sarvam Voice Agents via the MCP server with 4 HTTP tools pointed at a mock backend. Rent one number. Place 30 scripted calls yourself plus 5 native testers x 3 calls. Same 30 scripts against Bolna and Dvaarik demos where possible. Also answer the System A open questions in file 21 (tool-call metadata, concurrency, per-minute price shown in dashboard, transfer).
- **Cost:** Rs5,000-10,000. **Time:** 1 week.
- **Success:** Scorecard with P0/P1 counts, entity errors and native ratings for each platform.
- **Decision enabled:** Whether the bar is already high (lean to A) or clearly failing (lean to B or stop).

### E2. Customer discovery (runs in parallel from week 1)
- **Question:** Which vertical has painful missed calls and will pay?
- **Method:** 20 interviews: 10 automotive service (5 two-wheeler, 5 car multi-brand / authorised), 5 diagnostic centres, 5 clinics, in Hyderabad, Vijayawada, Tirupati or Warangal. Script below.
- **Cost:** Rs0-10,000 (field partner or calls). **Time:** 2-3 weeks.
- **Success:** At least 8 businesses report 10+ missed or after-hours calls per week and a willingness to pay of Rs3,000+.
- **Decision enabled:** Vertical choice and pricing.

### E3. Real phone audio collection line and Dataset A v0
- **Question:** Can we collect entity-heavy 8 kHz Telugu audio cheaply?
- **Method:** IVR recorder number; 20 speakers x 50 prompts = 1,000 utterances; label in the labeler tool.
- **Cost:** Rs15,000-25,000 (tester payments). **Time:** 2 weeks.
- **Success:** 1,000 labeled utterances across 3 regions and 3+ carriers.
- **Decision enabled:** Unlocks E4, E6, E7.

### E4. STT bake-off on real phone audio
- **Question:** Which STT config gives the best entity accuracy on 8 kHz Telugu?
- **Method:** Saaras v3-realtime, v4, v4 + keyterms, v4 codemix, Deepgram Nova-3 te, plus ElevenLabs Scribe v2 / GPT-4o Transcribe if Telugu is supported. Stream at real-time pace.
- **Cost:** Rs3,000-8,000. **Time:** 1 week.
- **Success:** Ranked table of entity error by class, WER / CER, P50 / P95 final-transcript latency.
- **Decision enabled:** STT choice and keyterm strategy.

### E5. Custom vertical slice with full tracing
- **Question:** Can System B hit P50 about 1.0-1.5 s with per-stage traces?
- **Method:** Exotel or Vobiz -> Pipecat -> Saaras v4 -> LLM -> Bulbul v3 with the same tools. OpenTelemetry spans for every stage, cost ledger. Also test conditional call forwarding from a Jio and an Airtel SIM.
- **Cost:** Rs3,000-6,000. **Time:** 1-2 weeks.
- **Success:** Working calls, timeline per call, forwarding result documented.
- **Decision enabled:** Feasibility and latency profile of B.

### E6. Turn-taking replay benchmark
- **Question:** Which endpointing strategy minimises false cutoffs without adding delay?
- **Method:** Strategies 1-7 (file 23) on Dataset B role-play recordings.
- **Cost:** Rs5,000 (extra role-play sessions). **Time:** 1-2 weeks.
- **Success:** 3 or fewer false cutoffs per 100 turns at P50 added delay under 300 ms versus the fastest strategy.
- **Decision enabled:** Whether a Telugu turn model is needed at all.

### E7. Entity resolution layer
- **Question:** Does the phonetic resolver plus confirmation reach 97% entity accuracy after clarification?
- **Method:** 300 entity utterances against a mock tenant DB (names, localities, vehicle numbers), with and without keyterms and resolver.
- **Cost:** under Rs2,000. **Time:** 1 week.
- **Success:** 97%+ after at most one clarification; 0 silent wrong resolutions.
- **Decision enabled:** Confidence thresholds and confirmation policy.

### E8. TTS listening test
- **Question:** Which voice sounds like a natural Telugu receptionist, and do cached acknowledgements help?
- **Method:** 200 sentences, 3-4 Bulbul v3 voices (plus any other provider that supports Telugu), pace variants; 20 raters, blind; measure TTFA; compare cached "సరే అండి / ఒక్క second" vs live synthesis.
- **Cost:** Rs10,000-15,000. **Time:** 1 week.
- **Success:** One voice at 4 / 5 or more in both panels.
- **Decision enabled:** Voice choice; whether to cache phrases.

### E9. Dialogue control design test
- **Question:** Fully generative vs LLM + state machine vs deterministic + LLM: which gives 0 wrong bookings with natural flow?
- **Method:** 100 booking scenarios at text level first (fast), then top design by voice. 2-3 candidate LLMs.
- **Cost:** Rs2,000-5,000. **Time:** 1 week.
- **Success:** 0 P1 errors and task completion 85%+.
- **Decision enabled:** Conversation architecture and LLM choice.

### E10. Head-to-head A vs B decision benchmark
- **Question:** Does custom orchestration earn its existence?
- **Method:** File 24 A/B protocol: 100 scripted PSTN scenarios + 20 blind testers x 5 calls on each system, including WhatsApp confirmation and transfer.
- **Cost:** Rs20,000-35,000. **Time:** 2 weeks.
- **Success / decision:** Rule in file 31.

## Customer discovery script (listen first, do not pitch)
1. Tell me about your shop. How many people handle phone calls?
2. Roughly how many calls a day? Busiest hours? Any after-hours calls?
3. What happens when nobody picks up? Do people call back, or go elsewhere? Any example recently?
4. What do callers most often ask? (Get the top 5 in their words.)
5. What language do callers use? How much English mixing?
6. How are bookings recorded today (register, WhatsApp, software, OEM system)? Can I see it?
7. What does a typical service / visit bring in? How many new customers a month come by phone?
8. Do you use WhatsApp Business with customers? For what?
9. Who would a caller need to be transferred to, and when?
10. What would make you trust a machine answering? What mistake would make you switch it off?
11. What do you pay the person who answers the phone?
12. If something answered every missed call and booked slots correctly, what would that be worth monthly? (Then test Rs2,999 / 4,999 / 7,999 / 9,999 reactions.)
13. Can I call you back in two weeks to show you a demo? Would you forward missed calls for a free 30-day pilot?
