# HTTP tools for Sarvam Voice Agents

Base URL: `https://<your-public-host>` (ngrok for the smoke test, a stable host for E1B).
Auth: **bearer token** using `TOOLS_BEARER_SECRET` from `python -m backend.seed --with-credentials`, entered through Sarvam's
masked secret input. The backend derives the tenant from this secret; the body never carries tenancy.

In every tool body, insert the call-context variables with the `@` picker:
- `interaction_id` <- **Interaction ID**
- `caller_number` <- **User Identifier**
Every other field is filled by the LLM from the conversation. Set **Max wait** to 5 s and **If it fails** to:
"క్షమించండి అండి, system slow గా ఉంది. మీకు callback arrange చేయమంటారా?"

Paste these cURL commands into the tool builder (it fills method, URL, headers, body), then replace the two
placeholder values with the `@` variables.

```bash
# get_business_hours: "Opening hours / is the shop open / which days"
curl -X POST https://HOST/tools/get_business_hours -H 'Authorization: Bearer SECRET' -H 'Content-Type: application/json' \
  -d '{"interaction_id":"@InteractionID","caller_number":"@UserIdentifier"}'

# get_service_info: "Services offered, price of a service"
curl -X POST https://HOST/tools/get_service_info -H 'Authorization: Bearer SECRET' -H 'Content-Type: application/json' \
  -d '{"interaction_id":"@InteractionID","caller_number":"@UserIdentifier","service":"<caller words, empty for all>"}'

# lookup_customer: "Find the caller's record by their number (empty phone = calling number)"
curl -X POST https://HOST/tools/lookup_customer -H 'Authorization: Bearer SECRET' -H 'Content-Type: application/json' \
  -d '{"interaction_id":"@InteractionID","caller_number":"@UserIdentifier","phone":"<number the caller said, or empty>"}'

# check_availability: "Free slots for a day/time; pass the caller's own words"
curl -X POST https://HOST/tools/check_availability -H 'Authorization: Bearer SECRET' -H 'Content-Type: application/json' \
  -d '{"interaction_id":"@InteractionID","caller_number":"@UserIdentifier","date_expression":"<e.g. రేపు>","time_expression":"<optional>","service":"<optional>","advisor":"<optional>"}'

# create_booking: "Book ONLY after reading back all details and getting a clear yes"
curl -X POST https://HOST/tools/create_booking -H 'Authorization: Bearer SECRET' -H 'Content-Type: application/json' \
  -d '{"interaction_id":"@InteractionID","caller_number":"@UserIdentifier","slot_id":"<from check_availability>","service":"<service>","customer_phone":"<10 digits>","customer_name":"<optional>","vehicle_reg":"<as said>","caller_confirmed":true}'

# request_callback: "When the caller wants a human, or a tool failed"
curl -X POST https://HOST/tools/request_callback -H 'Authorization: Bearer SECRET' -H 'Content-Type: application/json' \
  -d '{"interaction_id":"@InteractionID","caller_number":"@UserIdentifier","phone":"<optional>","reason":"<short reason>","preferred_time":"<optional>"}'
```

Note: `get_service_info` is a sixth tool beyond the five originally specified. It is required because smoke scenarios ask
for prices and prices must come from the backend.

Deployment post-call webhook (decision 0003): set on the inbound deployment (API/MCP `webhook_config`):
`{"url": "https://HOST/webhooks/sarvam/call-complete", "metadata": {"tvl_webhook_token": "<WEBHOOK_METADATA_TOKEN>"}}`.
Never put the token in the URL.

`lookup_customer` semantics (decision 0004): it returns `caller_id_match`, `identity_assurance` and masked vehicles only.
It never returns names. `authenticated` is always false.
