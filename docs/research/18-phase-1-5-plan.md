# 18 - Phase 1.5 Plan: Architecture Validation and Assumption Destruction

Date: 30 Sep 2026. Status labels: VERIFIED, MEASURED, ESTIMATED, HYPOTHESIS, UNKNOWN, VENDOR CLAIM.
Nothing in this phase is MEASURED. No API keys, phone numbers or Telugu audio were used.

## Founder clarification applied
The founder is Indian and can set up an Indian entity, KYC, bank account and director arrangement.
"Foreign founder" is removed as a blocker. Telephony onboarding is now a compliance checklist (file 22).

## Tool audit (what was actually used this round)
| Tool | Used | Notes |
|---|---|---|
| Web search / fetch | Yes | Primary source of evidence |
| Sandbox (bash + open network) | Yes | Pulled Sarvam docs as markdown (docs.sarvam.ai/<page>.md), scraped GitHub pages |
| GitHub REST API | Partly | Unauthenticated limit (60/hr, shared IP) was hit; fell back to GitHub HTML |
| Firecrawl | No | Not needed this round |
| Context7 | No | Not connected |
| Sarvam MCP | No | Requires your Sarvam login (OAuth) |
| Playwright, Supabase, Sentry, Hugging Face | No | Not needed until code exists |

### What to install (materially improves the next phase)
1. Sarvam Voice Agents MCP in Claude Code (VERIFIED command from Sarvam docs):
   `claude mcp add --transport http sarvam-voice-agents https://mcp.sarvam.ai/voice-agents`
   It can create agents, connect telephony, run evals, pull transcripts and analytics. Sign-in token lasts 24 h.
2. Sarvam docs MCP: `https://docs.sarvam.ai/_mcp/server` (listed in every Sarvam docs page header). Sarvam also publishes a Context7 page.
3. A GitHub personal access token in the dev environment (removes the 60 req/hr limit for due diligence scripts).
4. API keys for the benchmark: Sarvam (required), Deepgram, ElevenLabs, OpenAI, Google (optional comparators).

## Questions Phase 1.5 had to answer, and where
| Question | Answer location | Status |
|---|---|---|
| What changed since Phase 1? | 19 | Done |
| Can Sarvam already do most of what we planned? | 20, 21 | Largely yes, with specific gaps |
| Managed vs custom? | 21, 27 | Needs measurement (decision D) |
| Exact telephony onboarding per entity type | 22 | Done, some UNKNOWN |
| Telugu turn-taking approach | 23 | Design done, needs data |
| Benchmark harness design | 24 | Done |
| Cost model separating variable / infra / fixed | 25 | Done, telephony still partly UNKNOWN |
| Build / buy per subsystem | 26 | Done |
| Next experiments | 28 | Done |
| Budget to first pilot | 29 | Done (ESTIMATED) |
| Final decision | 31 | Decision D with a default |

## Decision rule for this phase
Custom infrastructure must beat the managed baseline on a measured, business-weighted metric
(wrong bookings, entity errors, false cutoffs, task completion, native naturalness) by more than it costs
to build and operate. Price per minute is a secondary criterion until volume exceeds ~100k minutes/month (file 25).
