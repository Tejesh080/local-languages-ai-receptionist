# 23 - Telugu Turn-Taking

Goal: minimise false cutoffs (agent speaks while the caller is still going) and keep end-of-turn to first-audio latency low. A 400 ms reply that interrupts is worse than a 900 ms reply that waited correctly.

## Strategies to benchmark (in order; build #8 only if 1-7 fail)
| # | Strategy | Available in | Notes |
|---|---|---|---|
| 1 | Sarvam server VAD defaults (threshold 0.3, silence 500 ms, min speech 250 ms) | A (implicitly) and B | Baseline |
| 2 | Sarvam VAD with Telugu-tuned silence (sweep 500 / 700 / 900 / 1200 ms) | B; A only via "Eagerness" slider | |
| 3 | Silero VAD v6 local + fixed silence | B | Removes dependence on server VAD |
| 4 | Silero + transcript rules (Telugu rule set below) | B | Uses Sarvam partials, manual endpointing |
| 5 | Smart Turn v3.2 (Telugu unsupported) | B | Try anyway; audio-only model may partially transfer from Hindi / Marathi / Bengali |
| 6 | LiveKit multilingual turn detector (Telugu unsupported) | B (via LiveKit) | Text-based on Qwen2.5-0.5B; likely weak on Telugu script |
| 7 | Hybrid: VAD + rules + dialogue-state-dependent silence via `config.update` | B | Cheapest likely winner |
| 8 | Telugu fine-tune of Smart Turn (open data and code, BSD-2) | B | Only if 1-7 fail meaningfully |

## Dialogue-state-dependent silence (HYPOTHESIS, strategy 7)
| Agent just asked | Expected answer | Silence before ending turn |
|---|---|---|
| Yes / no confirmation ("Thursday 5 గంటలకి OK నా?") | short | 400-500 ms |
| Open question ("ఏం కావాలి అండి?") | a sentence | 600-800 ms |
| Phone number, vehicle number, address, name spelling | long entity with pauses | 1,000-1,500 ms, and do not end while digit count is incomplete |
| Caller said "ఒక్క నిమిషం" / "one second" / "wait" | hold | Suspend endpointing up to 20-30 s; one soft backchannel ("సరే అండి") at most |

## Telugu continuation rules (HYPOTHESIS, grounded in Telugu being verb-final SOV)
Do NOT end the turn when the latest partial ends with:
- Discourse fillers: అంటే, మరి, ఆ..., ఏంటంటే, అదీ, ఇంకా, అలాగే, basically, like, so, and, but
- Conjunctive participle or non-finite verb forms (for example చేసి, వెళ్ళి, వచ్చి) and conditional -తే forms (అయితే, వస్తే, ఉంటే)
- Quotative అని at the end
- Correction markers without the replacement yet: కాదు, కాదు కాదు, sorry, అంటే
- An entity prefix: "Doctor పేరు...", "Number 9848..." (fewer than 10 digits), a registration prefix like "TS 09" without the full pattern
- Postpositions / case markers with no verb after (లో, కి, దగ్గర, తో)

Likely complete when the partial ends with:
- A finite verb or modal: కావాలి, ఉందా, ఉంటారా, చెప్పండి, చేయండి, అయిందా, వద్దు
- Question particles: -ఆ (ఉందా), ఏంటి, ఎప్పుడు, ఎక్కడ, ఎంత
- Utterance-final honorific after a finite verb: "...కావాలి అండి"
- A complete entity (10-digit mobile, full registration pattern, full date + time)

Politeness markers (అండి, గారు, సార్, మేడమ్, అన్నా) are not reliable end signals alone; they also appear mid-utterance.

## Metrics
- False cutoff rate: agent audio starts while the caller's labeled turn is still in progress, per 100 turns. Target 3 or fewer.
- Missed or late endpoint: turn end detected more than 1.5 s after true end.
- End-of-turn to first-audio: P50 / P95 / P99 measured at caller side.
- False barge-in: agent stops for noise, TV or a backchannel ("ఆ", "హా", "ok").

## Data needed (Dataset B, file 24)
Several thousand labeled turns from real phone role-plays, with human-marked turn ends, pauses, fillers and corrections. Collect via the recording line; label with a simple web tool.
