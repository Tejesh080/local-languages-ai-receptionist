# Environment audit (2026-09-30, Claude in claude.ai chat)

| Capability | Available here? | Notes |
|---|---|---|
| Terminal / Python sandbox | Yes | Ephemeral Linux sandbox; resets between sessions. Code is delivered as a zip for you to push. |
| Outbound network from sandbox | Yes | Used to read Sarvam, Exotel and Deepgram docs directly |
| Web search | Yes | |
| Firecrawl | Yes (connector) | Not needed this round |
| GitHub | No connector; no push credentials | You push the repo. Unauthenticated GitHub API is rate-limited from the sandbox |
| Context7 | No | Sarvam publishes a docs MCP (https://docs.sarvam.ai/_mcp/server) usable from Claude Code |
| Sarvam Voice Agents MCP | No (needs your SSO login) | Use from Claude Code: see managed/sarvam_agent/claude_code_setup.md |
| Sarvam / Deepgram API keys | No | Blocks E4 runs and the managed agent |
| Phone line, KYC, telephony account | No | Blocks E1A calls and E3 recording |
| Playwright | Not installed | Not needed until a UI exists |
| Database | SQLite locally; Postgres via DATABASE_URL | Tests run on SQLite |
| Cloud deployment | No | Use ngrok from your machine, or any host that runs the Dockerfile |
| Hugging Face | Not needed yet | |
| n8n, Airtable, HubSpot, Gmail, Drive connectors | Yes | Not used; tool capture is built into the backend instead |

**Blocking items only you can do:** Sarvam account + credits + MCP login; a phone number (Rent from Sarvam, Individual KYC)
for E1A; an Exotel account with the Voicebot applet for E3; Deepgram key (optional comparator); approve paid usage.
