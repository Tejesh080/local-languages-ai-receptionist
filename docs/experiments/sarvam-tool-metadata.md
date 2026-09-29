# Sarvam tool-call metadata

Status: NO REAL CAPTURES YET. This file is overwritten by `python scripts/tool_metadata_report.py` after the smoke calls.
(The report pipeline was exercised locally with a simulated request on 2026-09-30; that local output is intentionally NOT kept.)

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
