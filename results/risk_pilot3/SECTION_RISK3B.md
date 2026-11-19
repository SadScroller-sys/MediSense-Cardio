# Risk pilot 3b: risk with the age estimated from the ECG (5-fold, out-of-fold)

Rules written before the run: docs/plan/analysis_plan_changes.md (2026-11-18 evening). Same limits as pilot 3: not a blind test, clean ECGs, one cohort, no photos.

Patients 19048, events 2965.

| Quantity | Value |
|---|---|
| Age error of the ECG-estimated age (mean absolute) | 9.27 years (bias -1.56, correlation 0.809) |
| AUROC of the risk with the ESTIMATED age (95% interval) | 0.795 (0.786 to 0.804) |
| AUROC of the risk with the TRUE age (pilot 3) | 0.811 |
| AUROC of the estimated age alone | 0.757 |
| Calibration slope after Platt scaling (descriptive) | 0.88 |
| Observed 5-year rate, lower / middle / higher group | 2.5% (n=5791) / 9.7% (n=6252) / 31.6% (n=7005) |

## Verdict (rules for using it in the app)

| Rule | Result |
|---|---|
| Mean absolute age error at most 10 years | True |
| AUROC with the estimated age at least 0.75 and lower end above 0.72 | True |
| **Use the estimated age in the app when no age is typed** | **True** |