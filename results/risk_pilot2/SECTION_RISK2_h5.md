# Section RISK 2: ECG + age, all-cause mortality within 5 years, SEALED test once (PILOT 2; rules logged before the download and before any model was trained)

Rules: `docs/plan/analysis_plan_changes.md` ('RISK PILOT 2'). Data: CODE-15% (open, CC-BY 4.0), parts 0 to 17, patients with an outcome, 10 s recordings; people with a complete 5-year follow-up only (so the observed rate is higher than a population risk). Sealed test = patients of parts 6 to 17 never used before. Categories and pass rules are the assistant's proposal, not approved by the guide. All-cause mortality, not cardiac events; largely driven by age. The transfer check is NOT outcome validation.

## Sealed test split

| Model | n | Events | AUROC (95% interval) | AUPRC | Brier | ECE | Calibration slope |
|---|---|---|---|---|---|---|---|
| ECG + age (calibrated) | 2323 | 365 | 0.833 (0.810 to 0.854) | 0.484 | 0.1031 | 0.0179 | 1.18 |
| Age alone (logistic) | 2323 | 365 | 0.819 (0.798 to 0.840) | 0.426 | 0.1079 | 0.0260 |  |
| Age + sex (logistic) | 2323 | 365 | 0.828 (0.807 to 0.849) | 0.434 | 0.1060 | 0.0203 |  |
| ECG + age, age < 50 | 966 | 21 | 0.642 (0.502 to 0.784) | | | |  |
| Age alone, age < 50 | 966 | 21 | 0.553 (0.437 to 0.674) | | | |  |
| ECG + age, age 50 to 69 | 700 | 92 | 0.703 (0.648 to 0.759) | | | |  |
| Age alone, age 50 to 69 | 700 | 92 | 0.607 (0.547 to 0.666) | | | |  |
| ECG + age, age 70 and over | 657 | 252 | 0.698 (0.656 to 0.738) | | | |  |
| Age alone, age 70 and over | 657 | 252 | 0.610 (0.565 to 0.653) | | | |  |

**Added value of the ECG over age alone (paired bootstrap, AUROC difference): +0.013 (95% -0.005 to +0.032).**

## Categories on the sealed test (proposal: Low < 5%, Moderate 5% to < 15%, High 15% or more)

| Category | Patients | Events | Observed rate | Mean predicted |
|---|---|---|---|---|
| Low (< 5%) | 728 | 12 | 1.65% | 2.58% |
| Moderate (5% to < 15%) | 731 | 53 | 7.25% | 9.14% |
| High (15% or more) | 864 | 300 | 34.72% | 32.65% |

Deciles of predicted risk:

| Decile | Mean predicted | Observed | n |
|---|---|---|---|
| 1 | 1.17% | 1.72% | 233 |
| 2 | 2.40% | 2.59% | 232 |
| 3 | 3.86% | 0.86% | 232 |
| 4 | 5.70% | 3.45% | 232 |
| 5 | 8.21% | 7.73% | 233 |
| 6 | 11.50% | 7.76% | 232 |
| 7 | 16.26% | 18.97% | 232 |
| 8 | 22.92% | 26.29% | 232 |
| 9 | 32.71% | 33.19% | 232 |
| 10 | 53.47% | 54.51% | 233 |

## Transfer check: the same ECG (and the same age), original signal against its digitised version (no outcomes exist for these ECGs)

FULL = what the app would show (true age entered). ECG-ONLY = age fixed at 60 for both versions, so only the ECG changes.

| Group | n | Spearman FULL | Same category FULL | Mean abs. difference FULL | Spearman ECG-ONLY | Same category ECG-ONLY |
|---|---|---|---|---|---|---|
| drawn pages (dev: new100, F, G) | 300 | 0.95 | 95% | 2.63 points | 0.93 | 95% |
| drawn pages (dev: K) | 100 | 0.98 | 98% | 2.29 points | 0.97 | 96% |
| real phone photos (dev, not gated) | 140 | 0.91 | 89% | 4.88 points | 0.80 | 96% |
| simulated photos (dev) | 118 | 0.59 | 77% | 11.14 points | 0.50 | 75% |
| drawn pages (fresh L) | 100 | 0.84 | 93% | 4.84 points | 0.80 | 94% |
| drawn pages (fresh M) | 100 | 0.96 | 95% | 2.93 points | 0.95 | 93% |
| simulated photos (fresh L) | 100 | 0.75 | 83% | 8.80 points | 0.69 | 80% |
| simulated photos (fresh M) | 100 | 0.43 | 77% | 13.24 points | 0.35 | 73% |
| REAL printed-paper STRAIGHT photos (H2, friend's phone) | 22 | 0.95 | 100% | 6.27 points | 0.89 | 86% |

## Verdict (pass rules applied)

| Rule | Result |
|---|---|
| AUROC at least 0.80, lower end above 0.75 | True |
| ECG adds value: lower end of the paired difference over age alone above 0 | False |
| Calibration slope 0.8 to 1.25 and ECE at most 0.02 | True |
| Observed rates increase across Low, Moderate, High and High at least 3 times Low | True |
| Transfer FULL on drawn pages (Spearman at least 0.85, at least 80% same category) | False |
| Transfer FULL on simulated photos | False |
| Transfer FULL on REAL straight printed-paper photos | True |
| **Shown in the app** | **False** |
