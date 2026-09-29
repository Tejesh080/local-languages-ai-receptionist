# Decision 0001: Tenant binding for Sarvam Voice Agents HTTP tools

Date: 2026-09-30. Status: ACCEPTED for the lab; revisit after the metadata capture (docs/experiments/sarvam-tool-metadata.md).

**Context (VERIFIED from Sarvam docs, 2026-09-30):** API tools support auth types none / bearer / api_key / basic, with the
secret stored in Sarvam's workspace secrets. Call-context variables available to tools: User Identifier (caller phone on
inbound), Call Transcript, Interaction ID, Call Length. No documented called-number, agent-id or deployment-id variable
for tools, and no documented request signature. The post-call deployment webhook does include app_id, deployment_id and
agent_phone_number. Sarvam documents a single egress IP to allowlist: 4.213.167.70.

**Decision:**
1. One bearer secret per agent (per tenant). The backend stores only SHA-256 and maps secret -> tenant. The tenant is never
   read from the request body; bodies containing tenant_id / org_id / business_id are rejected and logged.
2. Optional source-IP allowlist (`ALLOWED_SOURCE_IPS=4.213.167.70`) as defense in depth, enabled once captures confirm the IP.
3. Caller identity (User Identifier) is used only to scope what the caller may see (own record full, other numbers masked).
   It is not authentication.
4. Interaction ID is used for idempotency keys and to join tool calls, bookings and the post-call webhook.

**Update 2026-09-30 (Phase 2A):** credentials carry a purpose (`tools` or `webhook`); a tool secret cannot authenticate
webhooks and vice versa. Webhook authentication moved from a URL path secret to a body token (decision 0003).

**Consequences:** A leaked secret exposes one tenant only; rotate by adding a new credential and deactivating the old.
If captures show Sarvam sends a verifiable signature or agent metadata, add it as a second factor rather than replacing (1).
