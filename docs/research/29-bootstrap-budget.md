# 29 - Bootstrap Budget to First Pilot (INR, excludes your salary)

All figures ESTIMATED unless marked. Verify prices at purchase time.

## Scenario 1: ULTRA LEAN (benchmarks + 1-2 friendly pilots, about 6-8 weeks)
| Item | Type | Amount |
|---|---|---|
| Udyam registration | one-time | Rs0 (government portal) |
| Domain | one-time / yearly | Rs800-1,500 |
| Sarvam credits (benchmarks, Voice Agents test calls) | usage | Rs5,000-10,000 |
| Phone number (Rent from Sarvam or Vobiz; Vobiz local from about $1/month) | monthly | Rs100-500 |
| Telephony minutes (about 2,000 test minutes at Rs0.5) | usage | Rs1,000 |
| Native testers (25 x Rs600 average) | one-time | Rs15,000 |
| Comparator APIs (Deepgram / ElevenLabs / OpenAI; free credits where offered) | usage | Rs0-3,000 |
| LLM | usage | Rs500-2,000 |
| Mumbai VM for System B slice | monthly | Rs1,000-2,500 |
| Postgres (free tier), Sentry / Langfuse / Grafana free tiers | monthly | Rs0 |
| WhatsApp test messages (Meta Cloud API) | usage | Rs200-500 |
| **Total to first pilot** | | **about Rs25,000-40,000** |

## Scenario 2: SERIOUS MVP (5 paid or free pilots, about 3 months)
| Item | Type | Amount |
|---|---|---|
| Sole proprietorship + Udyam + GST via CA | one-time | Rs2,000-5,000 |
| Legal consult (telecom + DPDP, 1-2 hours) | one-time | Rs15,000-40,000 |
| Exotel starter bundle (secondary: Rs9,999-19,999) or Vobiz pay-as-you-go | one-time / yearly | Rs0-20,000 |
| Numbers (5-6) | monthly | Rs500-2,000 |
| Native testers (50 x Rs800) + labeling (1,000 utterances + turn labels) | one-time | Rs50,000-60,000 |
| Sarvam usage (5 pilots x 1,000 min x Rs2-4) | monthly | Rs10,000-20,000 |
| Cloud (VM + managed Postgres + storage) | monthly | Rs3,000-8,000 |
| WhatsApp (utility messages, optional BSP) | monthly | Rs500-2,000 |
| Monitoring beyond free tiers | monthly | Rs0-3,000 |
| Part-time field partner in Hyderabad / Vijayawada | monthly | Rs15,000-30,000 |
| **Total for 3 months** | | **about Rs1.5-3.2 lakh** |

## Scenario 3: COMFORTABLE PILOT (10 pilots, 3-4 months)
Serious MVP plus: private limited company (Rs10,000-25,000 incl. professional fees, needs an Indian-resident director), fuller legal review (Rs50,000), 100 testers (Rs80,000-1,00,000), full-time field partner (Rs30,000-45,000 / month), usage for 10 pilots (Rs30,000-60,000 / month), one founder trip to Hyderabad / Vijayawada (Rs80,000-1,50,000, optional). **Total about Rs5-8 lakh.**

## Accounts and keys checklist
| Account | When | Why |
|---|---|---|
| Sarvam (dashboard + API key + Voice Agents workspace) | Now | STT, TTS, LLM, managed baseline, number rental |
| Sarvam Voice Agents MCP in Claude Code | Now | Build and test System A from your editor |
| Telephony: Rent from Sarvam (Individual KYC) | Now | Fastest test line |
| Vobiz or Exotel account | Now (B slice), Later (pilots) | Streaming for System B; transfer |
| Deepgram API key | Now | STT comparator |
| ElevenLabs API key | Now (optional) | STT / TTS comparator if Telugu supported |
| OpenAI / Google AI Studio keys | Now (optional) | STT and LLM comparators |
| Bolna account | Now | Competitor baseline, managed fallback |
| GitHub (repo + personal access token) | Now | Code, due diligence scripts |
| Supabase or other managed Postgres (Mumbai region, verify availability) | Now | Backend DB |
| Cloud VM in Mumbai (AWS ap-south-1, DigitalOcean BLR, E2E or similar) | Now (B) | Pipecat host |
| ngrok | Now | Local WebSocket exposure during development |
| Domain | Now | Recording line and webhooks |
| Meta developer account + WhatsApp Business (Cloud API) | Later (before pilots) | Confirmations, owner summaries |
| Udyam + GST + current account | Later (before paid pilots) | Telephony and WhatsApp business verification |
| Sentry, Langfuse or Grafana Cloud | Later (first real calls) | Errors, traces |
| Razorpay | Optional (paid plans) | Billing |
| Google Calendar API | Optional | If a pilot insists on calendar sync |
| Hugging Face | Optional | Datasets and open models |
