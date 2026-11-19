# Risk pilot 3: internal validation (cross-validated, same cohort)

Rules written before the run: docs/plan/analysis_plan_changes.md (2026-11-18 night, late). INTERNAL validation only: the same 19,048 patients, each predicted by models that never saw them. It is not external validation.

## 1. Calibration by decile of predicted risk

| Decile | n | Predicted | Observed (95% interval) | Within 5 points |
|---|---|---|---|---|
| 1 | 1905 | 1.3% | 1.6% (1.1 to 2.2) | yes |
| 2 | 1905 | 2.7% | 2.4% (1.8 to 3.2) | yes |
| 3 | 1905 | 4.1% | 2.7% (2.1 to 3.6) | yes |
| 4 | 1905 | 6.0% | 4.4% (3.5 to 5.4) | yes |
| 5 | 1905 | 8.5% | 7.0% (5.9 to 8.2) | yes |
| 6 | 1905 | 11.9% | 12.2% (10.8 to 13.7) | yes |
| 7 | 1905 | 16.7% | 17.4% (15.8 to 19.2) | yes |
| 8 | 1905 | 23.6% | 24.4% (22.5 to 26.3) | yes |
| 9 | 1904 | 34.4% | 32.8% (30.7 to 34.9) | yes |
| 10 | 1904 | 57.1% | 50.9% (48.6 to 53.1) | yes |

Slope 0.94, intercept -0.17, ECE 0.0147. Deciles within 5 points: 10 of 10 (target 8: met).
With the age estimated from the ECG: AUROC 0.795, slope 0.88, ECE 0.0163.

## 2. Against simple baselines

| Model | AUROC (95% interval) | Brier |
|---|---|---|
| ECG + age | 0.811 (0.803 to 0.820) | 0.1080 |
| Age + sex | 0.804 (0.796 to 0.812) | 0.1093 |
| Age alone | 0.798 (0.790 to 0.806) | 0.1102 |

ECG + age minus age + sex: +0.008 (95% interval +0.000 to +0.015).

## 3. Subgroups

| Group | n | Events | AUROC ECG + age (95% interval) | AUROC age + sex | Note |
|---|---|---|---|---|---|
| Women | 10991 | 1336 | 0.812 (0.801 to 0.825) | 0.810 | ECG + age higher |
| Men | 8057 | 1629 | 0.803 (0.792 to 0.814) | 0.781 | ECG + age higher |
| Age under 50 | 8014 | 275 | 0.713 (0.676 to 0.744) | 0.642 | ECG + age higher |
| Age 50 to 69 | 5581 | 719 | 0.739 (0.721 to 0.758) | 0.650 | ECG + age higher |
| Age 70 and over | 5453 | 1971 | 0.664 (0.649 to 0.679) | 0.620 | ECG + age higher |

Target (ECG + age higher than age + sex in every subgroup with at least 100 events): met.

## 4. Decision curve (net benefit)

| Threshold | ECG + age | Age + sex | Treat all |
|---|---|---|---|
| 5 in 100 | 0.1200 | 0.1191 | 0.1112 |
| 10 in 100 | 0.0974 | 0.0967 | 0.0618 |
| 15 in 100 | 0.0770 | 0.0764 | 0.0067 |

Limits: same cohort (one Brazilian telehealth network), clean ECGs, all-cause death, only people with a complete five-year follow-up, no photographs. External validation on a fresh cohort is future work.

![internal validation](fig_internal_validation.png)