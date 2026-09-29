# E7 part 1 (RUN 2, after -avu rule, re-run at commit): entity resolver on SYNTHETIC perturbations (2026-09-29, git 716c369)

Status: MEASURED on hand-written text perturbations, NOT on STT output. It tests the resolver logic and policy only.
Real-transcript E7 runs after E4 (scripts/e7_on_stt.py).

## Person names (N=41: 33 targets, 3 ambiguous-by-design, 5 distractors)

- Top-1 candidate correct: 33/33 = 100.0% (95% CI 89.6%-100.0%)
- Top-3 recall: 33/33 = 100.0% (95% CI 89.6%-100.0%)
- Decisions on targets: auto 17, confirm 16, clarify 0, no_match 0
- Correct after one clarification (simulated truthful caller): 33/33 = 100.0% (95% CI 89.6%-100.0%)
- Ambiguous inputs sent to clarification (not silently picked): 3/3 = 100.0% (95% CI 43.8%-100.0%)
- Unknown entities NOT matched to an existing record: 5/5 = 100.0% (95% CI 56.6%-100.0%)
- SILENT WRONG resolutions: 0 observed in N=41 (95% upper bound 7.0%)

## Services (N=21: 18 targets, 0 ambiguous-by-design, 3 distractors)

- Top-1 candidate correct: 18/18 = 100.0% (95% CI 82.4%-100.0%)
- Top-3 recall: 18/18 = 100.0% (95% CI 82.4%-100.0%)
- Decisions on targets: auto 17, confirm 1, clarify 0, no_match 0
- Correct after one clarification (simulated truthful caller): 18/18 = 100.0% (95% CI 82.4%-100.0%)

- Unknown entities NOT matched to an existing record: 3/3 = 100.0% (95% CI 43.8%-100.0%)
- SILENT WRONG resolutions: 0 observed in N=21 (95% upper bound 13.3%)

## Vehicle registrations (N=10: 6 targets, 2 ambiguous-by-design, 2 distractors)

- Top-1 candidate correct: 6/6 = 100.0% (95% CI 61.0%-100.0%)
- Top-3 recall: 6/6 = 100.0% (95% CI 61.0%-100.0%)
- Decisions on targets: auto 0, confirm 6, clarify 0, no_match 0
- Correct after one clarification (simulated truthful caller): 6/6 = 100.0% (95% CI 61.0%-100.0%)
- Ambiguous inputs sent to clarification (not silently picked): 2/2 = 100.0% (95% CI 34.2%-100.0%)
- Unknown entities NOT matched to an existing record: 2/2 = 100.0% (95% CI 34.2%-100.0%)
- SILENT WRONG resolutions: 0 observed in N=10 (95% upper bound 25.9%)

