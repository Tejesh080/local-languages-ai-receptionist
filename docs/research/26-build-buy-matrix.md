# 26 - Build vs Buy Matrix

## Decisions per subsystem
| Subsystem | Decision | Why |
|---|---|---|
| Telephony | BUY (Sarvam rent / Vobiz / Exotel) | Licensing and KYC; zero product differentiation |
| STT | BUY (Sarvam Saaras; Deepgram as comparator) | Best Indic coverage per vendor claims; we only need to measure and configure |
| TTS | BUY (Bulbul v3) | Telugu voice quality is a vendor capability; we choose and tune |
| Turn detection | BUY first (Sarvam VAD / Silero), BUILD LATER (Telugu rules, then fine-tune) | Genuine gap; rules are cheap, a model only if rules fail |
| LLM | BUY | LLM is under 10% of cost; choose on tool accuracy |
| Orchestration | BUY (Sarvam Voice Agents) or BUY-OPEN-SOURCE (Pipecat); decide by A/B | Must earn its existence |
| Business backend (tenants, services, slots, bookings, callbacks) | BUILD | Core product; must be deterministic and ours |
| Entity resolution against tenant data | BUILD | Moat candidate; no vendor does this for our data |
| WhatsApp | BUY (Meta Cloud API direct; BSP only if needed) | Commodity |
| Database | BUY (managed Postgres, Mumbai region) | Commodity |
| Observability | BUY-OPEN-SOURCE (OpenTelemetry + Langfuse or Grafana) + Sentry free tier | Cheap, standard |
| Evaluation harness | BUILD | Core asset; no vendor measures our Telugu phone audio |
| Datasets (STT, turn, TTS, scenarios, failures) | BUILD | Strongest moat candidate |
| Owner dashboard | BUILD LATER (daily WhatsApp summary first) | Owners live on WhatsApp |
| Analytics | BUILD minimal (from our own ledger); Sarvam Boards if on A | |
| RAG | DO NOT BUILD | Structured tables are enough for SMB receptionists |
| Billing | BUILD LATER (Razorpay) | Not needed for pilots |

## Technical decision matrix (qualitative; no invented scores)
| Component | Option | Quality | Latency | Cost | Reliability | Control | Eng. effort | Lock-in | India support | Telugu fit | Status | Evidence | Phase |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Orchestration | Sarvam Voice Agents | U | VC sub-second | about Rs3.5/min VC | VC | Low | Very low | High | Strong | VC | Candidate A | Sarvam docs | Now (A) |
| Orchestration | Pipecat 1.12 | depends on parts | measure | infra only | self-run | High | Medium | Low | Exotel serializer, Sarvam guide | via parts | Candidate B | GitHub, Sarvam guide | Now (B slice) |
| Orchestration | LiveKit Agents 1.8 | depends | measure | infra | self-run | High | Medium-high | Low | SIP | no Telugu turn model | Escape route | GitHub, docs | Later |
| Orchestration | Bolna | U | VC under 300 ms | $0.02/min + providers | U | Medium | Low | Medium | Strong | via Sarvam | Fallback A | Bolna docs | If A fails |
| STT | Saaras v4 realtime | VC best | VC under 150 ms TTFT | Rs0.50/min | U | Keyterms, manual endpointing | Low | Medium | Strong | VC | Benchmark | Sarvam docs | Now |
| STT | Saaras v3-realtime | VC | VC | Rs0.50/min | U | No keyterms | Low | Medium | Strong | VC | Benchmark | Sarvam docs | Now |
| STT | Deepgram Nova-3 te | U | U | U | U | Keyterms (paid add-on) | Low | Medium | Global | te monolingual only | Comparator | Deepgram docs | Now |
| TTS | Bulbul v3 | VC | U (measure TTFA) | Rs3/1K chars | U | Pronunciation dict, pace | Low | Medium | Strong | VC | Primary | Sarvam docs | Now |
| TTS | ElevenLabs v3 Conversational | U | U | U | U | High | Low | Medium | Global | Telugu UNKNOWN | Comparator if Telugu | ElevenLabs docs | Optional |
| TTS | Indic Parler-TTS / IndicF5 | below commercial per paper | GPU | GPU cost | self-run | Full | High | None | n/a | Yes | Later | HF, arXiv | Not now |
| Turn | Rules + dynamic silence | U | adds 0 | 0 | ours | Full | Low | None | n/a | Designed for Telugu | Build | File 23 | Now (B) |
| Turn | Smart Turn fine-tune | U | 10-100 ms | training cost | ours | Full | Medium | None | n/a | needs data | Later | smart-turn README | Only if needed |
| LLM | Sarvam 105B Conversations | U | U | Rs0.19/min est. | U | Medium | Low | Medium | India-hosted | Tuned for Indic | Benchmark | Sarvam docs | Now |
| LLM | Gemini Flash-Lite class | U | U | Rs0.11/min est. | U | Medium | Low | Medium | Global | U | Benchmark | Google pricing (secondary) | Now |
| Telephony | Rent from Sarvam / Vobiz | U | VC under 80 ms | about Rs0.5/min | U | Medium | Low | Low | Yes | n/a | Primary for A | docs | Now |
| Telephony | Exotel | U | 100 ms frames | Rs0.40-0.75/min (dated) | Mature | Medium | Low | Low | Yes | n/a | Primary for B | docs | Now |
| DB | Postgres (Supabase Mumbai or managed) | High | Low | Low | High | High | Low | Low | Yes | n/a | Build | standard | Now |
