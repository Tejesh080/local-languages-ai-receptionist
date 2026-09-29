# Agent settings for E1A (record the actual values used in the E1A results file)

| Setting | Value for E1A | Why |
|---|---|---|
| Starting language | Telugu | Target market |
| Languages allowed | Telugu, English | Tenglish callers |
| Switch language during call | On | Callers switch mid-call |
| Auto-detected language switch | On, default delay | Measure, do not tune yet |
| Output numbers in Indic | Off | Digits read in English are common in Tenglish ("five thirty"); test both only if callers complain |
| Voice | Try 2 Bulbul v3 voices on 3 calls each (one female, one male), keep the better one for the rest | Voice choice is E8; this is a quick sanity pick |
| Let callers interrupt | On | Barge-in is a benchmark dimension |
| Sound sensitivity | Medium | Default; change only if false barge-ins are observed |
| Eagerness to respond | Normal for calls 1-15, Patient for calls 16-30 | Cheap A/B on cutoffs vs latency; record which calls used which |
| Detect when the caller stops talking (advanced) | On | Documented as improving turn-taking |
| Important words | `important_words.txt` (known business entities only) | Realistic hotwords; never test answers |
| Protect sensitive info | On | Mask phones in logs |
| Max call length | 10 min | Smoke scope |
| Temperature | 0.3 (default) | Do not tune |
| Call transfer (In Call Actions) | Configure only if the number is Vobiz / Rent from Sarvam and an Indian test destination is available | Transfer finding for E1A |
