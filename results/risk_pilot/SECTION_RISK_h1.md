# Section RISK: ECG-estimated all-cause mortality risk, horizon 1 year, test once (PILOT; rules logged before any model was trained)

Rules: `docs/plan/analysis_plan_changes.md` ('ECG-estimated mortality RISK PILOT'). Data: CODE-15% (open, CC-BY 4.0), patients with an outcome, 10 s recordings, ECG only (no age or sex). Categories and pass rules are the assistant's proposal, not approved by the guide. All-cause mortality, not cardiac events; one Brazilian primary-care source; largely driven by age. The transfer check is NOT outcome validation.

## Test split (untouched until this run)

| Model | n | Events | AUROC (95% interval) | AUPRC | Brier | ECE | Calibration slope |
|---|---|---|---|---|---|---|---|
| ECG model (calibrated) | 6188 | 82 | 0.713 (0.653 to 0.770) | 0.058 | 0.0129 | 0.0057 | 0.62 |
| Age alone (logistic) | 6188 | 82 | 0.799 (0.752 to 0.840) | 0.047 | 0.0128 | 0.0023 |  |
| Age + sex (logistic) | 6188 | 82 | 0.797 (0.749 to 0.839) | 0.045 | 0.0128 | 0.0024 |  |
| ECG model, age < 50 | 3063 | 10 | 0.611 (0.429 to 0.792) | | | |  |
| ECG model, age 50 to 69 | 1754 | 17 | 0.606 (0.439 to 0.765) | | | |  |
| ECG model, age 70 and over | 1371 | 55 | 0.644 (0.565 to 0.717) | | | |  |

## Categories on the test split (proposal: Low < 1%, Moderate 1% to < 3%, High 3% or more)

| Category | Patients | Events | Observed rate | Mean predicted |
|---|---|---|---|---|
| Low (< 1%) | 2857 | 18 | 0.63% | 0.58% |
| Moderate (1% to < 3%) | 2404 | 26 | 1.08% | 1.71% |
| High (3% or more) | 927 | 38 | 4.10% | 5.69% |

Deciles of predicted risk:

| Decile | Mean predicted | Observed | n |
|---|---|---|---|
| 1 | 0.25% | 0.65% | 619 |
| 2 | 0.45% | 0.32% | 619 |
| 3 | 0.62% | 0.32% | 619 |
| 4 | 0.79% | 0.81% | 618 |
| 5 | 0.98% | 1.13% | 619 |
| 6 | 1.23% | 0.48% | 619 |
| 7 | 1.56% | 1.29% | 618 |
| 8 | 2.10% | 1.45% | 619 |
| 9 | 3.05% | 2.58% | 619 |
| 10 | 6.83% | 4.20% | 619 |

## Transfer check: the same ECG, original signal against its digitised version (no outcomes exist for these ECGs)

| Group | n | Spearman | Mean absolute difference | Mean risk original | Mean risk digitised | Same category |
|---|---|---|---|---|---|---|
| drawn pages (dev: new100, F, G) | 300 | 0.92 | 0.34 points | 2.23% | 2.36% | 88% |
| drawn pages (dev: K) | 100 | 0.98 | 0.36 points | 2.96% | 3.05% | 86% |
| real phone photos (dev) | 140 | 0.65 | 0.74 points | 2.36% | 2.17% | 80% |
| simulated photos (dev) | 118 | 0.53 | 0.96 points | 2.29% | 2.08% | 58% |
| drawn pages (fresh L) | 100 | 0.88 | 0.41 points | 2.69% | 2.69% | 88% |
| drawn pages (fresh M) | 59 | 0.88 | 0.54 points | 2.53% | 2.52% | 85% |
| simulated photos (fresh L) | 100 | 0.67 | 1.07 points | 2.69% | 2.62% | 75% |
| REAL printed-paper STRAIGHT photos (H2, friend's phone) | 22 | 0.43 | 0.70 points | 2.00% | 2.07% | 59% |

## Verdict (pass rules applied)

| Rule | Result |
|---|---|
| AUROC at least 0.75, lower end above 0.70 | False |
| Calibration slope 0.8 to 1.25 and ECE at most 0.02 | False |
| Observed rates increase across Low, Moderate, High and High is at least 3 times Low | True |
| Transfer check on digitised drawn pages (Spearman at least 0.85, at least 80% same category) | True |
| Transfer check on photos incl. REAL printed-paper photos | False (real photos available: True) |
| **Shown in the app** | **False** |
