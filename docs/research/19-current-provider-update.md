# 19 - Current Provider Update (rechecked 29-30 Sep 2026)

Only items actually rechecked this round are marked VERIFIED. Items not rechecked keep their Phase 1 value and are marked STALE.

## Sarvam (most changes)
| Change | Date | Status | Source |
|---|---|---|---|
| Saaras V4 released: 22 Indian languages + English incl. global English accents, 5 output modes (transcribe, verbatim, codemix, translit, translate), sub-150 ms streaming TTFT | Sep 2026 | VERIFIED (features) / VENDOR CLAIM (accuracy, latency) | marktechpost.com 26 Sep 2026; docs.sarvam.ai |
| saaras:v4 available on the Realtime streaming API | 3 Sep 2026 | VERIFIED | docs.sarvam.ai/changelog |
| Keyterm prompting (max 50 terms, 64 chars each) for saaras:v4 on REST/Batch (9 Sep) and on both streaming WebSockets (22 Sep). v4 only | Sep 2026 | VERIFIED | changelog, keyterms page |
| New Realtime endpoint `/speech-to-text-realtime/ws`: true partials, VAD tuned in ms, `endpointing=manual` with client speech_start / speech_end / flush, mid-call `config.update`, mulaw/alaw/linear16 at 8 or 16 kHz, `language_code=auto` | 2026 | VERIFIED | realtime-streaming docs |
| Voice Agents (formerly Conversations / Samvaad) opened publicly (Jul), renamed Aug | Jul-Aug 2026 | VERIFIED | changelog |
| Voice Agents: Tests (simulated user + AI judge, up to 20 runs per case) | 17 Sep 2026 | VERIFIED | changelog |
| Voice Agents MCP server (remote, OAuth) | 16 Sep 2026 | VERIFIED | changelog, MCP docs |
| Boards API (SQL analytics, scheduled delivery) | 16 Sep 2026 | VERIFIED | changelog |
| Self-serve data retention controls | 15 Sep 2026 | VERIFIED | changelog |
| Per-language voice selection | 9 Sep 2026 | VERIFIED | changelog |
| sarvam-105b price raised from Rs4 / 2.5 / 16 to Rs29.28 / 10.98 / 73.2 per 1M tokens (about 7x) | 5 Aug 2026 | VERIFIED | changelog |
| Free signup credits now Rs100 (several 2026 third-party pages still say Rs1,000) | 2026 | VERIFIED (docs) | ratelimits and pricing docs |
| Voice Agents price: Sarvam pitches about Rs3.5/min vs industry Rs8-12 | Aug 2026 | VENDOR CLAIM via press | Inc42 "Sarvam's AI Arsenal" |

## Frameworks and turn detection
| Item | Current state | Status |
|---|---|---|
| Pipecat | v1.12.0 released 26 Sep 2026; 15,980 stars; BSD-2-Clause; ~118 open issues | VERIFIED (GitHub) |
| Pipecat Flows | Merged into core `pipecat.flows` as of pipecat-ai 1.5.0; standalone repo archived at v1.4.0 | VERIFIED (repo README) |
| LiveKit Agents | livekit-agents 1.8.3 released 26 Sep 2026; 14,420 stars; Apache-2.0; ~224 open issues | VERIFIED |
| LiveKit turn detector | Still 14 languages incl. Hindi, not Telugu; "performance on unsupported languages is undefined"; Python dynamic endpointing exists | VERIFIED |
| Smart Turn | v3.2, 23 languages incl. Hindi, Marathi, Bengali, not Telugu; BSD-2; training data published | VERIFIED |
| Silero VAD | v6.2.3; MIT; active (push 29 Sep 2026) | VERIFIED |
| Deepgram Flux Multilingual | GA Apr 2026, 10 languages incl. Hindi, not Telugu | VERIFIED |

## Other speech providers
| Item | State | Status |
|---|---|---|
| Deepgram Nova-3 | Telugu (te) monolingual; Telugu not in `multi` code-switching list | VERIFIED (Phase 1), not rechecked in depth |
| ElevenLabs Flash v2.5 (real-time TTS) | Languages list does not include Telugu (includes Hindi, Tamil) | VERIFIED |
| ElevenLabs Eleven v3 / v3 Conversational | 74 languages; Telugu presence not confirmed in the truncated list read | UNKNOWN |
| ElevenLabs Scribe v2 Realtime | 90+ languages; Telugu not individually confirmed | UNKNOWN |
| Google, Azure, AWS, OpenAI Telugu STT/TTS | Not rechecked | STALE / UNKNOWN |

## Telephony and platforms
| Item | State | Status |
|---|---|---|
| Exotel Voicebot applet | 8 kHz default; 16 and 24 kHz via `?sample-rate=`; session cap about 60 min; server must accept WebSocket within about 10 s | VERIFIED (Sarvam's Exotel guide) |
| Exotel usage prices | Historical: local incoming Rs0.40/min, inter-circle incoming Rs0.75/min | VERIFIED as secondary, dated |
| Vobiz | Inbound from $0.0055/min, local numbers from $1/month, transfer over SIP and streaming | VERIFIED as listing (Capterra / GetApp), not official page |
| Bolna | Platform fee flat $0.02/min; provider costs pass through or zero if you connect your own accounts; bundles $0.05-0.10/min | VERIFIED (Bolna docs and pricing page) |
| Retell, Vapi, Dvaarik | Not rechecked | STALE |

## LLMs (cost is minor; see 25)
| Model | Price per 1M tokens (input / output) | Status |
|---|---|---|
| Gemini 3.1 Flash-Lite | $0.25 / $1.50 (one aggregator shows $0.125 / $0.75) | Secondary, CONFLICT |
| Gemini 3.5 Flash-Lite | $0.30 / $2.50 | Secondary |
| Sarvam 105B (and 105B Chat / Conversations) | Rs29.28 / Rs73.2 (cached Rs10.98) | VERIFIED |
| DeepSeek V4 Flash on Sarvam | Rs19.8 / Rs59.4 (cached Rs0.63), beta | VERIFIED |
| OpenAI, Anthropic, Groq, Cerebras, Fireworks, Together | Not rechecked | UNKNOWN |
