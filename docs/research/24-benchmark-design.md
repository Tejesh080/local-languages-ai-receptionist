# 24 - Benchmark Harness and Dataset Design

The first engineering artifact is a **Telugu voice benchmark harness**, not the SaaS. It is reused for every decision (provider choice, A vs B, turn-taking, regression gating). Challenge considered: "just use Sarvam Tests instead". Rejected as the only tool because Sarvam Tests are simulated text conversations graded by an AI judge. They cannot measure real 8 kHz audio, turn cutoffs or the custom stack. Use Sarvam Tests as a complement for System A.

## Harness layout
```
telugu-voice-bench/
  datasets/            # manifests (JSONL) + audio; see schema below
  collect/
    ivr_recorder/      # phone line: plays a prompt, records caller reading it (real PSTN audio)
    labeler/           # tiny web app: correct transcript, tag entities, mark turn ends
  runners/
    stt_runner.py      # streams 8 kHz audio at real-time pace to each provider; logs partial/final timestamps
    tts_runner.py      # synthesises test sentences; logs TTFA; stores audio for rating
    turn_replay.py     # replays recorded dialogues through endpointing strategies 1-7 (file 23)
    e2e_caller.py      # dials the agent number over PSTN, plays scenario audio, records both sides
  scoring/
    normalize.py       # Unicode NFC, Telugu digits to ASCII, number words to digits, codemix equivalences
    wer.py             # WER / CER (jiwer)
    entities.py        # per-class entity exact match after normalization
    latency.py         # P50/P95/P99
    judge.py           # scenario pass/fail from backend DB state + transcript checks
  results/             # Postgres or SQLite; one row per (run, item, provider, config)
  report/              # static HTML comparison report
```

### Manifest schema (one JSON line per utterance)
`id, audio_path, channel (pstn|studio), carrier, handset (phone|speaker), noise_tag, speaker_id, region (telangana|coastal_andhra|rayalaseema), gender, age_band, speed, text_ref, text_ref_codemix, entities [{type, value, char_span}], scenario_id, consent_id`

## Capturing real phone audio (cheap)
1. Rent one number (Sarvam rent or Vobiz or Exotel).
2. Point it at a small Pipecat bot or provider IVR flow: greet, read out prompt N, beep, record 15 s, next prompt.
3. Testers call from their own phones (Jio, Airtel, Vi, BSNL), indoors, outdoors, on speaker, in a car.
4. The recording is genuine carrier-path 8 kHz audio. Studio WAVs are never used for the primary metrics.
5. Supplement with GSM / AMR codec simulation only for augmentation, never as a replacement.

## Datasets
| Set | Initial size | Content | Primary metrics |
|---|---|---|---|
| A. STT | 1,000 utterances (start with 300 in week 1) | Entity-heavy: names, doctor names, localities, villages, 10-digit mobiles read fast and slow, dates, relative dates, times ("five thirty", "సాయంత్రం"), rupee amounts, vehicle registrations (TS / AP formats), service names, English terms inside Telugu | WER, CER, entity exact-match per class, streaming latency |
| B. Turn | 3,000+ labeled turns | Real role-play calls with fillers, pauses, corrections, holds, spelled entities | False cutoff rate, late endpoint, false barge-in |
| C. TTS | 200 sentences | Receptionist lines with doctor, appointment, WhatsApp, five thirty, online payment, scan, report, service, booking, Google Maps; numbers, prices, dates, names | Native MOS (naturalness, "sounds like a receptionist", pronunciation), TTFA, round-trip ASR CER |
| D. E2E scenarios | 100, growing to 500+ | Booking, reschedule, cancel, status, price, location, callback, transfer, after-hours | Task completion, wrong bookings, entity accuracy, latency, repetition |
| E. Adversarial | 100 | Changes mind 5 times, interrupts every sentence, prompt injection, asks for another customer's data, TV noise, rapid numbers, "Wednesday... కాదు Thursday", ambiguous "evening", rare village names, three language switches | P0/P1 incidents (must be 0) |
| F. Production failures | grows forever | Every meaningful failure, consented and redacted | Regression gate |

## Severity classes (business-weighted scoring)
| Class | Meaning | Examples | Gate |
|---|---|---|---|
| P0 | Dangerous, privacy or financial | Disclosed another customer's booking; stated a price not from the database | Any P0 blocks release |
| P1 | Wrong business action | Booked Tuesday when caller said Thursday; said "booked" before persistence | Any P1 blocks release |
| P2 | Conversation failure | Caller repeated 3+ times; transfer failed; hung up frustrated | Must not regress |
| P3 | Minor transcription error with no action impact | "Ready" vs "Reddy" resolved by clarification | Tracked |
| P4 | Cosmetic / naturalness | Slightly formal phrasing | Tracked via MOS |

## Native tester plan
- Initial panel: 10 Telangana, 10 Coastal Andhra, 5 Rayalaseema; mix of heavy Telugu and heavy Tenglish speakers, ages 18-65, male and female, fast and slow.
- Recruitment: family and alumni networks, Telugu associations (including in Australia for remote sessions), college students in Hyderabad / Vijayawada / Tirupati, paid via UPI.
- Pay: Rs500-1,000 per 30-45 minute session (ESTIMATED market rate).
- Instructions: do not speak clearly for the benefit of the machine; behave like a real caller.

## A/B experiment (System A vs System B)
- Same business data (a mock two-wheeler / car service centre with 3 advisors, 12 services, a price list, slots, 20 existing customer records).
- Same HTTP tools against the same backend. Tools log every call with request id.
- 100 scripted scenarios run by `e2e_caller.py` over PSTN, plus 20 human testers each making 5 free-form calls to both systems, blind (numbers A and B, randomised order).
- Measured per call: P50 / P95 / P99 end-of-turn to first-audio (from recordings), entity accuracy, tool-call correctness (DB state vs expected), task completion, false cutoffs, missed interruptions, caller repetition, Tenglish handling (rated), native score, cost per call, cost per successful booking.
- Decision rule in file 31.

## Success criteria (starting hypotheses, revise with data)
| Metric | Target |
|---|---|
| Task completion (in-scope intents) | 85% or more |
| Tool-call correctness | 99% or more |
| Wrong confirmed bookings | 0 |
| Hallucinated transactional facts | 0 |
| Entity accuracy after clarification | 97% or more |
| False turn cutoffs | 3 or fewer per 100 turns |
| Native naturalness | 4 / 5 or more, both regional panels |
| P50 end-of-turn to first-audio | about 1.0-1.5 s |
| P95 | under 3 s |
| Caller repetition rate | under 10-15% |

## Existing tools to reuse
jiwer (WER), Pipecat built-in metrics (TTFB per service), Silero VAD, Sarvam Tests (System A), Postgres `pg_trgm` / `fuzzystrmatch` for entity candidate search. Commercial voice-agent testing services exist (for example Cekura); pricing and Telugu support UNKNOWN, evaluate later.
