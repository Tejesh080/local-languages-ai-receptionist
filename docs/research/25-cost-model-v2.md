# 25 - Cost Model V2

Every number below is either VERIFIED (price list), secondary, or HYPOTHESIS (usage assumption). Usage assumptions must be replaced by instrumented values from real calls.

## Layers (kept separate)
1. **Variable voice cost** (per call-minute): telephony, STT, TTS, LLM, platform fee, WhatsApp per call.
2. **Platform infrastructure** (monthly): servers, Postgres, storage, Redis if any, logging, monitoring.
3. **Fixed business cost** (monthly): support, engineering, operations, sales. Never divided into minutes to produce a "voice cost".

Reported separately:
- **MARGINAL API COST / MIN** = layer 1 only.
- **TECHNICAL COGS / MIN** = layer 1 + (layer 2 / monthly minutes).
- **FULLY LOADED COGS / CUSTOMER / MONTH** = customer minutes x technical COGS/min + number rental + WhatsApp + support hours x hourly cost.

## Price inputs
| Input | Value | Status |
|---|---|---|
| FX | Rs92 per USD | ESTIMATED |
| Sarvam STT | Rs30/hour = Rs0.50 per audio-minute, billed per second | VERIFIED |
| Bulbul v3 | Rs30 per 10K chars = Rs0.003/char | VERIFIED |
| Sarvam 105B | Rs29.28 in / Rs10.98 cached / Rs73.2 out per 1M tokens | VERIFIED |
| Gemini 3.1 Flash-Lite | $0.25 / $1.50 per 1M (conflict: $0.125 / $0.75) | Secondary |
| Exotel inbound | Rs0.40 local, Rs0.75 inter-circle per minute; 30 or 60 s pulses | Secondary, dated |
| Vobiz inbound | from $0.0055/min (about Rs0.51); local number from $1/month | Secondary listing |
| Bolna platform fee | $0.02/min (about Rs1.84), providers extra or bring-your-own | VERIFIED |
| Sarvam Voice Agents | about Rs3.5/min; unclear if telephony included | VENDOR CLAIM via press |
| WhatsApp utility message (India) | about Rs0.115 + 18% GST; BSP markup extra | Secondary, conflicting |

## Usage parameters (HYPOTHESIS until instrumented)
| Parameter | Low / Mid / High |
|---|---|
| Average call length | 1.5 / 2.5 / 4 min |
| Agent talk ratio r_agent | 0.25 / 0.35 / 0.45 |
| Telugu TTS characters per second of speech (cps) | 10 / 12 / 15 |
| Fraction of call audio sent to STT (s_frac) | 0.6 (VAD-gated) / 1.0 / 1.0 |
| LLM turns per call-minute | 3 / 4 / 5 |
| Input tokens per turn (cached / uncached) | 2,400 / 600 |
| Output tokens per turn | 60 |

## Formulas (per call-minute)
```
STT      = 0.50 x s_frac
TTS      = 0.003 x 60 x r_agent x cps
LLM      = turns x (uncached_in x p_in + cached_in x p_cached + out x p_out)
TEL      = telephony_rate_per_min (+ pulse rounding effect)
PLATFORM = platform_fee_per_min (0 for custom)
WA_min   = (messages_per_call x price_per_message) / call_minutes
MARGINAL = STT + TTS + LLM + TEL + PLATFORM + WA_min
INFRA_min = monthly_infra / monthly_minutes
TECH_COGS = MARGINAL + INFRA_min
```

## Results
### System B (custom, Sarvam APIs)
| Component | Low | Mid | High |
|---|---|---|---|
| STT | 0.30 | 0.50 | 0.50 |
| TTS (60 x r x cps x 0.003) | 0.45 | 0.76 | 1.22 |
| LLM (Gemini FL mid about 0.11; Sarvam 105B about 0.19) | 0.05 | 0.15 | 0.35 |
| Telephony | 0.40 | 0.55 | 0.80 |
| **Marginal API cost / min** | **Rs1.20** | **Rs1.96** | **Rs2.87** |

### System A (Sarvam Voice Agents)
Rs3.5 (vendor claim) + telephony Rs0.40-0.80 if not included = **Rs3.5-4.3 / min** (UNKNOWN until checked in dashboard).

### Bolna (bring your own Sarvam + telephony)
Rs1.84 platform + System B components = **Rs3.0-4.7 / min**.

**Largest controllable cost:** TTS characters (short replies halve it). LLM is under 10%. Telephony is the largest external unknown.

## Variable cost at scale (marginal only, mid case)
| Minutes / month | System A at Rs4.0 | System B at Rs1.96 | Difference |
|---|---|---|---|
| 100 | Rs400 | Rs196 | Rs204 |
| 1,000 | Rs4,000 | Rs1,960 | Rs2,040 |
| 10,000 | Rs40,000 | Rs19,600 | Rs20,400 |
| 100,000 | Rs4.0 lakh | Rs1.96 lakh | Rs2.04 lakh |
| 1,000,000 | Rs40 lakh | Rs19.6 lakh | Rs20.4 lakh |
| 10,000,000 | Rs4 crore | Rs1.96 crore | Rs2.04 crore |

Infrastructure for System B (ESTIMATED): pilot Rs3,000-8,000/month; at 100k min/month about Rs10,000-20,000. Fixed business costs listed separately in file 29.

**A to B break-even** (ESTIMATED): if operating B costs about Rs1.5-2.5 lakh/month more in engineering and ops time, break-even is Rs2 lakh / Rs2.04 per min, about **100,000 minutes/month**. Below that, per-minute savings do not justify B. Quality differences can justify B earlier.

## Cost per business outcome (the metric that matters)
```
cost_per_booking         = (sum call cost + WhatsApp + transfer leg cost) / confirmed_bookings
cost_per_resolved_call   = total cost / calls resolved without human
cost_per_transferred_call = total cost of calls ending in transfer / transferred calls
revenue_recovered_per_100_calls = bookings_from_otherwise_missed_calls x show_rate x average_ticket
```
Worked example (HYPOTHESIS): 100 service-centre calls, 2.0 min average, 45% booking intent, 80% completed by AI = 36 bookings. At System A Rs4/min: Rs800 + WhatsApp 36 x Rs0.14 = about Rs805, so **about Rs22 per booking**. JD Power's 2021 India CSI study reported an average spend of Rs4,390 on the most recent car service (VERIFIED, dated). If a booking has even a 60% show rate, Rs22 is about 0.8% of expected ticket value.

**Conclusion:** at pilot scale, the choice between Rs2/min and Rs4/min is irrelevant economically. A single wrong booking or a frustrated caller costs more than a month of minute-price difference. Optimise quality first.

## Gross margin on hypothetical plans (ESTIMATED)
| Plan | Price / month | Included AI minutes | COGS on A (Rs4.3) + number + WA | GM on A | COGS on B (Rs1.96 + infra alloc) | GM on B |
|---|---|---|---|---|---|---|
| Starter (after-hours + missed calls) | Rs2,999 | 300 | about Rs1,490 | about 50% | about Rs900 | about 70% |
| Standard | Rs4,999 | 500 | about Rs2,350 | about 53% | about Rs1,480 | about 70% |
| Pro (booking + WhatsApp + transfer) | Rs7,999 | 1,000 | about Rs4,500 | about 44% | about Rs2,660 | about 67% |
| Multi-location | Rs14,999 | 2,500 | about Rs11,000 | about 27% | about Rs5,900 | about 61% |
Support cost (for example 1-2 hours per customer per month) must be subtracted from these.

## Per-call instrumentation (replaces every HYPOTHESIS above)
caller speech s, agent speech s, silence s, STT billed s (from `session.end.audio_duration_s`), TTS chars sent, LLM input tokens, cached tokens, output tokens, telephony billed minutes (from CDR), tool calls, WhatsApp messages, DB queries. Store in a `call_cost_ledger` table keyed by call_id, aggregated by customer, agent, day, month, vertical and provider.
