# Heart-attack pattern percentage from photos: calibration test (sets Q + R, tested once)

Rules written before the run: docs/plan/analysis_plan_changes.md (2026-11-18 night, late). Simulated phone photos of PTB-XL fold-10 recordings; weights represent the PTB-XL population.

Population prevalence of the MI pattern in PTB-XL: 25.1%. Fit set N + P: 386 pictures (131 positives). Test set Q + R: 280 pictures (64 positives).
Calibration (frozen): p = sigmoid(0.346 * logit(score) + -1.004).

| Quantity (test, weighted) | Value | Rule |
|---|---|---|
| Calibration slope | 0.95 | 0.8 to 1.25: pass |
| Expected calibration error (5 bins) | 0.061 | at most 0.05: FAIL |
| Brier score, calibrated / uncalibrated / prevalence only | 0.165 / 0.188 / 0.188 | calibrated below uncalibrated: pass |
| AUROC of the score on the test set (unweighted) | 0.757 | descriptive |

**Show a percentage in the app: False**

Limits: simulated phone photos of dataset recordings, one drawing program, one digitiser; sets are enriched in some patterns and the weights are a rough correction; 280 test pictures; not validated on real phone photos.

![reliability](fig_MI_photocal.png)