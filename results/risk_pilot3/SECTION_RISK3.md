# Risk pilot 3: five-fold cross-validation on all usable patients (5-year death, ECG + age)

Rules written before the run: docs/plan/analysis_plan_changes.md (2026-11-18 day). Out-of-fold predictions of one run; NOT a blind test (the pilot-2 sealed-test patients are included).

Patients 19048, events 2965. Held-out AUROC per fold: 0.817, 0.809, 0.801, 0.815, 0.816.

| Quantity | Value |
|---|---|
| AUROC, ECG + age (95% interval) | 0.811 (0.803 to 0.820) |
| AUROC, age alone | 0.798 |
| Difference (ECG + age minus age alone), 95% interval | +0.013 (+0.006 to +0.021) |
| Calibration slope / ECE | 0.76 / 0.0147 |
| Observed 5-year rate, Low / Moderate / High | 2.2% (n=5787) / 8.3% (n=6031) / 32.3% (n=7230) |

## Verdict (stage 1)

| Rule | Result |
|---|---|
| AUROC at least 0.80, lower end above 0.75 | True |
| ECG adds value: lower end of the paired difference above 0 | True |
| Calibration slope 0.8 to 1.25 and ECE at most 0.02 | False |
| Observed rates increase across the categories and High at least 3 times Low | True |
| **Stage 1 passed** | **False** |

Stage 2 (transfer of the five fold models to drawn pages and simulated photos) has NOT been run. No percentage is shown in the app until it passes. Limits: not a blind test; clean 12-lead ECGs from one Brazilian telehealth cohort; no photos.