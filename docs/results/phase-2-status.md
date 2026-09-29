# Phase 2 status (updated after Phase 2A hardening, 2026-09-30)

See docs/results/phase-2a-hardening.md. 57 tests passing.

| Item | Status | Evidence |
|---|---|---|
| Environment audit | Done | docs/experiments/environment-audit.md |
| Repository | Done (lab only, no SaaS) | this repo, 57 automated tests passing |
| Sarvam MCP / account capability check | BLOCKED: needs your login | managed/sarvam_agent/claude_code_setup.md |
| Voice Agents price / concurrency | BLOCKED: needs your account | docs/experiments/sarvam-account-capabilities.md |
| Mock automotive backend + 6 tools | Built and tested locally | backend/, tests/test_backend.py |
| Tenant binding | Designed from verified docs, tested locally | docs/decisions/0001-tenant-binding.md |
| Tool-call metadata capture | Instrumented; awaiting real Sarvam calls | backend request_captures + scripts/tool_metadata_report.py |
| First 5 smoke calls | BLOCKED: needs phone number + deployed agent | docs/experiments/E1A-protocol.md |
| E1B kit | Ready | benchmark/scenarios/e1b_goals.yaml, docs/experiments/E1B-rating-form.md |
| E3 recorder | Built; protocol tested against a simulated Exotel client | collection/recorder, tests/test_recorder_protocol.py |
| E3 prompts + sheets + consent | Ready (120 prompts, 20 sheets, known/confusable/unseen) | benchmark/manifests, collection/ |
| E4 runner + scoring | Built; scoring unit-tested; no provider calls made | benchmark/run_stt.py, benchmark/score_stt.py |
| E7 resolver | Built; measured on synthetic perturbations (2 runs kept) | docs/results/E7-resolver-synthetic-run1.md, -run2.md |
| Discovery | Plan + tracker ready | discovery/ |

Checkpoint (docs/results/phase-2-checkpoint.md) is NOT written: it requires E1, E3, E4 data.
