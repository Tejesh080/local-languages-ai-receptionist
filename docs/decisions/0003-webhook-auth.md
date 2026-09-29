# Decision 0003: Sarvam post-call webhook authentication

Status: ACCEPTED 2026-09-30. Classification: **PLATFORM LIMITATION** (verified from current docs).

## What Sarvam offers (VERIFIED, docs.sarvam.ai conversations/api/deployments/create and webhook-payload, 2026-09-30)
- `webhook_config` has exactly two fields: `url` (required) and `metadata` (optional map).
- The webhook payload echoes `metadata` ("Custom metadata from the webhook configuration").
- No documented signature/HMAC, no custom request headers, no authorization header, no mTLS.
- Deliveries can be listed and retried via the API (so the endpoint must be idempotent).
- Sarvam documents one egress IP for tool calls (4.213.167.70); whether webhooks use the same IP is UNKNOWN.

## Decision
1. **Shared token in the body, not the URL.** Configure `webhook_config.metadata = {"tvl_webhook_token": "<secret>"}`
   and the fixed URL `https://HOST/webhooks/sarvam/call-complete`. URL paths are routinely written to proxy, ngrok and
   access logs; request bodies generally are not. The previous path-secret design is removed.
2. Token = 256-bit random (`tvl_...`), stored only as SHA-256, **purpose `webhook`**. Tool credentials cannot authenticate
   webhooks and vice versa (tested).
3. Idempotent upsert keyed by `interaction_id`; a webhook for an interaction already owned by another tenant is rejected (409).
4. Stored data is redacted: phone numbers as salted hashes, variables and transcripts not stored unless
   `STORE_CALL_TRANSCRIPTS=1` (forbidden in production until a retention policy exists).
5. Uvicorn runs with `--no-access-log` in the Dockerfile; our own logs never include tokens or bodies.

## Residual risk
Anyone who learns the token can forge call-complete events for that tenant (integrity, not confidentiality, since the
endpoint returns nothing). There is no replay protection beyond idempotency. Mitigations: token rotation, optional IP
allowlist once the webhook source IP is observed, and cross-checking `interaction_id` against our tool-call log.

## Rotation
`python -c "from backend.seed import add_credential; print(add_credential('<tenant>', 'sarvam-webhook-v2', 'webhook'))"`,
update the deployment's `webhook_config.metadata`, confirm a delivery succeeds, then set the old credential `active=false`.
