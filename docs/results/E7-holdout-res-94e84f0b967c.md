# E7 HOLDOUT (single run): resolver res-94e84f0b967c, git b4cbea3, 2026-09-29

Synthetic text perturbations written before this run and not used for tuning. NOT evidence of real-STT robustness;
the decisive E7 evaluation is on real E4 transcripts.

## Person names (N=37: 28 targets, 3 ambiguous, 6 unknown)

- Top-1 correct: 28/28 = 100.0% (95% CI 87.9%-100.0%)
- Top-3 recall: 28/28 = 100.0% (95% CI 87.9%-100.0%)
- Decisions on targets: auto 1, confirm 26, clarify 0, no_match 1
- Needed a confirmation or clarification turn: 26/28 = 92.9% (95% CI 77.4%-98.0%)
- Correct after one clarification (simulated truthful caller): 27/28 = 96.4% (95% CI 82.3%-99.4%)
- Ambiguous inputs sent to clarification: 3/3 = 100.0% (95% CI 43.8%-100.0%)
- Unknown entities rejected (not matched to a record): 4/6 = 66.7% (95% CI 30.0%-90.3%)
- SILENT WRONG resolutions: 0 observed in N=37 (95% upper bound 7.8%)

Failures (recorded, NOT fixed against this set):
  - `అంజలి చౌదరి` expected c06 got no_match/c06
  - `Venkatesh Rao` expected None got confirm/c02
  - `Ravi Teja` expected None got confirm/c09

## Services (N=16: 12 targets, 0 ambiguous, 4 unknown)

- Top-1 correct: 11/12 = 91.7% (95% CI 64.6%-98.5%)
- Top-3 recall: 11/12 = 91.7% (95% CI 64.6%-98.5%)
- Decisions on targets: auto 0, confirm 8, clarify 0, no_match 4
- Needed a confirmation or clarification turn: 8/12 = 66.7% (95% CI 39.1%-86.2%)
- Correct after one clarification (simulated truthful caller): 8/12 = 66.7% (95% CI 39.1%-86.2%)
- Ambiguous inputs sent to clarification: not observed (N=0)
- Unknown entities rejected (not matched to a record): 4/4 = 100.0% (95% CI 51.0%-100.0%)
- SILENT WRONG resolutions: 0 observed in N=16 (95% upper bound 17.1%)

Failures (recorded, NOT fixed against this set):
  - `periodic maintenance` expected general_service got no_match/general_service
  - `ఏసీ పనిచేయట్లేదు` expected ac_repair got no_match/None
  - `battery down` expected battery_replacement got no_match/battery_replacement
  - `వీల్ బ్యాలెన్సింగ్` expected wheel_alignment got no_match/wheel_alignment

## Vehicle registrations (N=10: 7 targets, 1 ambiguous, 2 unknown)

- Top-1 correct: 7/7 = 100.0% (95% CI 64.6%-100.0%)
- Top-3 recall: 7/7 = 100.0% (95% CI 64.6%-100.0%)
- Decisions on targets: auto 0, confirm 7, clarify 0, no_match 0
- Needed a confirmation or clarification turn: 7/7 = 100.0% (95% CI 64.6%-100.0%)
- Correct after one clarification (simulated truthful caller): 7/7 = 100.0% (95% CI 64.6%-100.0%)
- Ambiguous inputs sent to clarification: 1/1 = 100.0% (95% CI 20.7%-100.0%)
- Unknown entities rejected (not matched to a record): 2/2 = 100.0% (95% CI 34.2%-100.0%)
- SILENT WRONG resolutions: 0 observed in N=10 (95% upper bound 25.9%)

Failures (recorded, NOT fixed against this set):
  - `TS 09 EA 4512` expected None got confirm/TS09EA4512
  - `AP 16 DD 9091` expected None got confirm/AP16DD9091

