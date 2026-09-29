# 22 - Telephony Final (onboarding checklist, not a blocker)

## Provider requirements by entity type
"Y" = accepted per source, "?" = UNKNOWN, "N" = not accepted per source.

| Provider | Indian individual | Sole proprietorship | LLP | Pvt Ltd | Documents named in sources | Status |
|---|---|---|---|---|---|---|
| Rent from Sarvam (Vobiz underneath) | Y (UI offers "Individual") | ? | ? | Y ("Corporate") | KYC in dashboard; exact docs not published | VERIFIED account types; docs UNKNOWN |
| Vobiz direct | ? | Y likely | Y | Y | India-registered businesses; KYC via PAN, GST or Aadhaar | Phase 1 VERIFIED |
| Exotel | N (business KYC) | Y likely via MSME/Udyam in place of COI | Y | Y | Company PAN, COI (or MSME/RERA/DIPP/FSSAI), address proof (GST, MSME, utility bill, rent agreement), director photo; Customer Acquisition Form for VoIP; KYC 1-3 business days | Phase 1 VERIFIED; proprietorship ESTIMATED |
| Plivo | N | Y via GST or Udyam | Y | Y | GST, COI or Udyam; PAN alone not accepted; India data region only | Phase 1 VERIFIED |
| Ozonetel | ? | ? | ? | Y | GST, company PAN, COI, signatory PAN + Aadhaar, cancelled cheque | Phase 1 VERIFIED |
| Knowlarity | ? | ? | ? | Y | DoT-mandated KYC within 7 days | docs UNKNOWN |
| Meta WhatsApp Business (Cloud API) | ? | Y likely | Y | Y | Business verification with legal name, address, registration document | UNKNOWN specifics |

## Entity paperwork (what each structure needs)
| Structure | Registration | Typical documents | Director rule |
|---|---|---|---|
| Individual | none | PAN, Aadhaar, address proof | n/a |
| Sole proprietorship | Udyam (free, online, Aadhaar-based) + GST (optional below turnover threshold; about 7 working days with Aadhaar authentication) | Proprietor PAN + Aadhaar, photo, premises proof (utility bill; rent agreement + NOC if rented), bank proof | n/a |
| LLP | MCA | LLPIN, LLP PAN, LLP agreement, partners' PAN + Aadhaar | designated partners (residency rules apply) |
| Private limited | MCA SPICe+ | COI, company PAN, MoA / AoA, directors' PAN + Aadhaar, Class 3 DSC | At least one director resident in India 182+ days in the financial year (Companies Act s.149(3)) |
| Bank | current account in entity name | as above | |

## Recommended onboarding path (HYPOTHESIS; confirm with a CA)
1. **Now (benchmark stage):** Rent a number from Sarvam as an Individual, or use a Vobiz / Exotel trial, for test lines only. Also open a free Udyam registration.
2. **Before paid pilots:** Sole proprietorship with Udyam + GST, an Indian business address (utility bill + NOC) and a current account. This likely satisfies Exotel (MSME certificate), Plivo (Udyam / GST) and Vobiz (GST / PAN).
3. **Before raising money or enterprise customers:** Convert to a private limited company with an Indian-resident director.
4. **Open question for your CA:** tax residency and operating an Indian proprietorship while living in Australia. This is an UNRESOLVED question, not a stop condition.

## How a business connects (inbound only)
- **Option 1: Conditional call forwarding** from the business's existing mobile or landline to our DID on busy / no answer / unreachable (standard GSM codes such as **67*, **61*, **62*). The business keeps its number; the AI handles overflow and after-hours. Operator support and forwarding charges on Jio / Airtel / Vi / BSNL: UNKNOWN. Test in Experiment 5.
- **Option 2: New AI number** published on Google Business Profile, JustDial listing and WhatsApp.
- **Option 3: Business-owned Exotel account** (they complete KYC; we connect). Slow; enterprise only.

## Human transfer support
| Stack | Cold transfer | Warm transfer with context | Status |
|---|---|---|---|
| Sarvam Voice Agents on Vobiz / Rent from Sarvam | Self-serve | "Human handover" enterprise | VERIFIED |
| Sarvam Voice Agents on Exotel | Via Sarvam team | U | VERIFIED |
| Custom on Exotel | Voicebot then Transfer applet in the flow | Build: WhatsApp / SMS context to staff before bridging | Phase 1 VERIFIED / design |
| Custom on Vobiz | Transfer over SIP and streaming | Build | VERIFIED listing |

Warm-transfer design for both stacks: before bridging, our backend sends the staff member a WhatsApp or SMS with caller name, intent, collected fields, pending action and a link to the transcript. The caller never repeats themselves.

## Regulatory recap (unchanged from Phase 1, inbound-only focus)
- LEGAL REQUIREMENT: licensed telephony with KYC; TCCCPR rules apply to commercial outbound (140 / 1600 / 1601 series); DPDP obligations from 13 May 2027.
- BEST PRACTICE: announce AI and recording at call start; minimal retention; explicit opt-in before WhatsApp follow-ups beyond the booking confirmation.
- UNRESOLVED: whether forwarding a business number to an AI raises any operator or TRAI issue; DPDP cross-border access by an Australia-resident operator.
