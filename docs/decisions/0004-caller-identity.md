# Decision 0004: Caller identification vs caller authentication

Status: ACCEPTED 2026-09-30 (policy). Implementation in the lab: LOW and MEDIUM tiers only; no HIGH actions exist.

## Principle
The platform-reported caller number (Sarvam "User Identifier") is **identification**: a hint about who might be calling.
It is **not authentication**. Caller ID can be spoofed, phones are shared within families and staff, and the provenance of
Sarvam's value is not yet experimentally verified (E1A checks it with salted hashes, see scripts/hash_phone.py).
The API makes this explicit: `lookup_customer` returns `identity_assurance` ("none" | "unverified_caller_id") and a
constant `authenticated: false`. No field in any response can be read as "this caller is verified".

## Sensitivity tiers
| Tier | Examples | Identity needed | Lab status |
|---|---|---|---|
| LOW | business hours, services, prices, availability, creating a new booking, requesting a callback | none | implemented |
| MEDIUM | recognising a returning caller; offering masked vehicle candidates ("vehicle ending 4521?") | caller-ID match (unverified) may assist | implemented, masked only |
| HIGH | revealing names, service history, invoices or booking details; changing or cancelling a booking; changing contact details | stronger verification (below) | NOT implemented; agent offers a callback |

## Rules
1. Never read a customer's name, history or booking details from our records to a caller. The caller states their own
   name; the resolver may only *confirm* what the caller said. (E7 holdout showed the name resolver can propose an
   existing customer for an unknown name such as "Venkatesh Rao" -> "Venkat Rao"; proposing it aloud would disclose a
   customer's name, so customer-name candidates are never spoken. Staff/advisor names are public and may be offered.)
2. A number stated by the caller that differs from the caller ID reveals nothing about that number's records.
3. New bookings are LOW risk: a booking under someone else's number is mitigated by the WhatsApp confirmation to that
   number and a human-handled cancel path.

## Minimum safe verification for automotive HIGH actions (when we build them)
Two independent factors, at least one not visible from outside the car:
1. caller-ID match to the number on the booking, **and**
2. the booking reference sent by WhatsApp/SMS at booking time (not guessable, not printed on the vehicle).
The vehicle registration alone is not a secret (it is on the number plate) and never counts as a factor.
If either factor fails: no disclosure; offer a callback to the number on file. OTP is deferred until a HIGH action is
actually needed and until we measure how often factor 2 is unavailable.
