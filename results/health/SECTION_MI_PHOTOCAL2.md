# Heart-attack pattern percentage from photos: SECOND attempt, fresh random set S (tested once)

Rules written before the set was selected: docs/plan/analysis_plan_changes.md (2026-11-18 night, late, 'SET S'). Second attempt after a failure (first attempt: ECE 0.061 against 0.05).

Fit: 666 simulated photos (sets N, P, Q, R; 195 positives), weighted to the PTB-XL prevalence 25.1%. Test: 300 photos of set S (66 positives, 22.0%).
Calibration (frozen): p = sigmoid(0.337 * logit(score) -0.944).

| Quantity (set S) | Value | Rule |
|---|---|---|
| Calibration slope | 1.15 | 0.8 to 1.25: pass |
| Expected calibration error (5 bins) | 0.040 | at most 0.05: pass |
| Brier, calibrated / uncalibrated / prevalence only | 0.145 / 0.184 / 0.172 | calibrated below both: pass |
| AUROC of the score | 0.773 | descriptive |
| Sensitivity / specificity at the app threshold 0.279 | 76% / 66% | descriptive |

**Show a percentage in the app: True**

Limits: simulated phone photos of dataset recordings, one drawing program, one digitiser; second attempt (a lucky pass is more likely); not validated on real phone photos.

![reliability](fig_MI_photocal2.png)