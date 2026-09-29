# Sarvam tool-call metadata

Status: NO REAL CAPTURES YET. This file is overwritten by `python scripts/tool_metadata_report.py` after the smoke calls.
Captures store field names, header names, source IP and presence/salted hashes; never plaintext personal values (Phase 2A).

What the docs say (VERIFIED as documentation, 2026-09-30), to be confirmed or contradicted by captures:
| Field | Documented? | Experimental status |
|---|---|---|
| Our bearer secret (Authorization) | Yes (auth type bearer, stored as workspace secret) | UNKNOWN |
| Caller number | Yes, "User Identifier" call-context variable (inbound) | UNKNOWN |
| Interaction / call ID | Yes, "Interaction ID" call-context variable | UNKNOWN |
| Call transcript so far | Yes, "Call Transcript" (we do NOT request it, to limit PII) | not requested |
| Call length | Yes, "Call Length" | not requested |
| Called number (our DID) | Not documented for tools (present in post-call webhook as agent_phone_number) | UNKNOWN |
| Agent ID / version | Not documented for tools (webhook has app_id, app_version) | UNKNOWN |
| Deployment ID | Not documented for tools (webhook has deployment_id) | UNKNOWN |
| Tool call ID | Not documented | UNKNOWN |
| Request signature / HMAC | Not documented | UNKNOWN |
| Source IP | Documented egress IP 4.213.167.70 | UNKNOWN |
| Caller-number provenance (User Identifier == real calling number) | Implied by docs | UNKNOWN (verify with scripts/hash_phone.py) |
| Post-call webhook: signature / auth header | Not supported: only url + metadata (decision 0003) | PLATFORM LIMITATION (docs) |
| Post-call webhook source IP | Not documented | UNKNOWN |
