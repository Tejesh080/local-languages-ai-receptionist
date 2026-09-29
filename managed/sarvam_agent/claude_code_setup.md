# Building the System A agent from Claude Code (Sarvam Voice Agents MCP)

1. `claude mcp add --transport http sarvam-voice-agents https://mcp.sarvam.ai/voice-agents --scope project`
2. In Claude Code run `/mcp`, choose `sarvam-voice-agents`, **Authenticate** (browser SSO; token lasts 24 h).
3. Read-only check: "Use sarvam-voice-agents to list my voice agents and show which tools my plan exposes."
   Record in `docs/experiments/sarvam-account-capabilities.md`: plan name, available write tools
   (create_http_tool vs upload_agent_code), whether place_test_call exists, concurrency and per-minute price
   (also check dashboard Settings > Plans & pricing and Settings > Usage).
4. Ask Claude Code to read `sarvam://playbooks/index` and `sarvam://schemas/agent-config`, then create the agent from
   `managed/sarvam_agent/instructions.md`, `settings.md`, `important_words.txt` and the six tools in `tools.md`
   (bearer auth secret entered by you in the masked input, not pasted into chat).
5. Commit the agent version. Record the committed version number in every E1A call log row.
6. Telephony: Rent from Sarvam (Individual KYC) or connect Exotel / Vobiz. Create an inbound deployment with the
   post-call webhook URL from `tools.md`.
7. Security reminders from Sarvam's MCP docs: approve every mutation manually; `commit`, `place_test_call`,
   `verify_phone_number` and `delete_*` are irreversible or cost money.
