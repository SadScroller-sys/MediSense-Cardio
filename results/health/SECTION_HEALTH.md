# Section HEALTH: ECG-pattern model, test once (EXPLORATORY; rules logged before training)

Rules: `docs/plan/analysis_plan_changes.md`, 'Heart health module'. Model trained once on PTB-XL folds 1-8 minus our digitised recordings, epoch and calibration from fold 9. Findings are ECG PATTERNS, not cardiac risk (no outcome data exists). The pass rules are the assistant's proposal, not approved by the guide.

## T1 fold 10 (benchmark)

| Class | n | Positives | Clusters | AUROC (95% interval) | Calibration error | Brier | Sensitivity | Specificity |
|---|---|---|---|---|---|---|---|---|
| NORM | 2133 | 942 | 2133 | 0.932 (0.922 to 0.942) | 0.017 | 0.101 | 0.91 | 0.82 |
| MI | 2133 | 525 | 2133 | 0.898 (0.883 to 0.912) | 0.020 | 0.105 | 0.79 | 0.84 |
| STTC | 2133 | 502 | 2133 | 0.917 (0.904 to 0.930) | 0.021 | 0.092 | 0.80 | 0.88 |
| CD | 2133 | 478 | 2133 | 0.908 (0.890 to 0.923) | 0.018 | 0.087 | 0.80 | 0.88 |
| HYP | 2133 | 255 | 2133 | 0.882 (0.860 to 0.903) | 0.008 | 0.071 | 0.80 | 0.79 |
| AF | 2133 | 150 | 2133 | 0.972 (0.956 to 0.984) | 0.010 | 0.025 | 0.90 | 0.96 |

## T2 drawn pages, digitised

| Class | n | Positives | Clusters | AUROC (95% interval) | Calibration error | Brier | Sensitivity | Specificity |
|---|---|---|---|---|---|---|---|---|
| NORM | 300 | 150 | 300 | 0.882 (0.841 to 0.921) | 0.139 | 0.158 | 0.71 | 0.91 |
| MI | 300 | 70 | 300 | 0.908 (0.868 to 0.944) | 0.080 | 0.104 | 0.87 | 0.76 |
| STTC | 300 | 68 | 300 | 0.886 (0.846 to 0.922) | 0.084 | 0.125 | 0.66 | 0.87 |
| CD | 300 | 74 | 300 | 0.895 (0.839 to 0.943) | 0.041 | 0.094 | 0.85 | 0.85 |
| HYP | 300 | 33 | 300 | 0.775 (0.689 to 0.850) | 0.125 | 0.147 | 0.79 | 0.67 |
| AF | 300 | 23 | 300 | 0.869 (0.758 to 0.952) | 0.043 | 0.044 | 0.61 | 0.95 |

## T3 straightened phone photos

| Class | n | Positives | Clusters | AUROC (95% interval) | Calibration error | Brier | Sensitivity | Specificity |
|---|---|---|---|---|---|---|---|---|
| NORM | 140 | 58 | 70 | 0.754 (0.650 to 0.854) | 0.273 | 0.254 | 0.36 | 0.93 |
| MI | 140 | 28 | 70 | 0.857 (0.724 to 0.975) | 0.094 | 0.096 | 0.79 | 0.80 |
| STTC | 140 | 50 | 70 | 0.865 (0.772 to 0.942) | 0.129 | 0.157 | 0.72 | 0.84 |
| CD | 140 | 28 | 70 | 0.875 (0.766 to 0.957) | 0.076 | 0.105 | 0.86 | 0.76 |
| HYP | 140 | 24 | 70 | 0.636 (0.481 to 0.778) | 0.321 | 0.319 | 0.83 | 0.37 |
| AF | 140 | 12 | 70 | 0.866 (0.749 to 0.973) | 0.051 | 0.046 | 0.50 | 0.96 |

## What the app may show (pass rules applied)

| Class | Testable on drawn pages | Supported for drawn pages | Testable on photos | Supported for phone photos | Percentage allowed (photos) |
|---|---|---|---|---|---|
| NORM | True | True | True | True | True |
| MI | True | True | True | True | True |
| STTC | True | True | True | True | True |
| CD | True | True | True | True | True |
| HYP | True | False | True | False | False |
| AF | True | True | False | False | False |

Rules: supported for drawn pages = at least 20 positives, AUROC at least 0.80 on T2 and its lower interval end above 0.70; supported for phone photos = that, plus at least 20 positive photos and AUROC at least 0.75 on T3 (point estimate); a percentage only for a supported finding whose calibration error on T1 is at most 0.10. Decision thresholds = Youden J on fold 9. Intervals: bootstrap over recordings (pages for photos), 2,000 resamples. The two photos of a page are not independent.
