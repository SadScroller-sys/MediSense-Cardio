# Section FIND2-B: CODE-15% labels, test once (EXPLORATORY; rules logged before training)

Rules: `docs/plan/analysis_plan_changes.md` ('MORE DISEASE FINDINGS' and Amendment 1). Public data only. Findings are ECG PATTERNS, not diagnoses and not risk. Pass rules and thresholds are the assistant's proposal, not approved by the guide. Intervals: bootstrap over clusters (1000 resamples); the photos of one page are not independent.

## T1 CODE-15% test split (benchmark)

| Finding | n | Positives | AUROC (95% interval) | Calibration error | Sensitivity | Specificity |
|---|---|---|---|---|---|---|
| 1dAVb (first-degree AV block) | 26346 | 415 | 0.978 (0.974 to 0.982) | 0.004 | 0.97 | 0.88 |
| RBBB (right bundle branch block) | 26346 | 635 | 0.989 (0.986 to 0.991) | 0.003 | 0.94 | 0.97 |
| LBBB (left bundle branch block) | 26346 | 511 | 0.995 (0.994 to 0.996) | 0.002 | 0.98 | 0.97 |
| SB (slow heart rate (sinus bradycardia)) | 26346 | 423 | 0.990 (0.987 to 0.993) | 0.002 | 0.97 | 0.96 |
| ST (fast heart rate (sinus tachycardia)) | 26346 | 515 | 0.992 (0.991 to 0.994) | 0.003 | 0.98 | 0.97 |
| AF (atrial fibrillation) | 26346 | 542 | 0.980 (0.973 to 0.986) | 0.003 | 0.93 | 0.96 |

## T2 drawn pages, digitised

| Finding | n | Positives | AUROC (95% interval) | Calibration error | Sensitivity | Specificity |
|---|---|---|---|---|---|---|
| 1dAVb (first-degree AV block) | 300 | 12 | 0.926 (0.875 to 0.968) | 0.024 | 1.00 | 0.76 |
| RBBB (right bundle branch block) | 300 | 30 | 0.709 (0.592 to 0.822) | 0.081 | 0.50 | 0.95 |
| LBBB (left bundle branch block) | 300 | 2 | 0.856 (0.707 to 0.983) | 0.008 | 0.50 | 0.96 |
| SB (slow heart rate (sinus bradycardia)) | 300 | 16 | 0.976 (0.947 to 0.996) | 0.031 | 0.81 | 0.95 |
| ST (fast heart rate (sinus tachycardia)) | 300 | 12 | 0.931 (0.798 to 0.998) | 0.016 | 0.83 | 0.98 |
| AF (atrial fibrillation) | 300 | 23 | 0.919 (0.814 to 0.994) | 0.022 | 0.91 | 0.87 |

## T3 straightened phone photos

| Finding | n | Positives | AUROC (95% interval) | Calibration error | Sensitivity | Specificity |
|---|---|---|---|---|---|---|
| 1dAVb (first-degree AV block) | 140 | 4 | 1.000 (1.000 to 1.000) | 0.033 | 1.00 | 0.61 |
| RBBB (right bundle branch block) | 140 | 8 | 0.602 (0.308 to 0.891) | 0.062 | 0.00 | 0.93 |
| LBBB (left bundle branch block) | 140 | 4 | 0.987 (0.951 to 1.000) | 0.017 | 1.00 | 0.94 |
| SB (slow heart rate (sinus bradycardia)) | 140 | 6 | 0.689 (0.264 to 0.993) | 0.035 | 0.50 | 0.95 |
| ST (fast heart rate (sinus tachycardia)) | 140 | 4 | 1.000 (1.000 to 1.000) | 0.024 | 1.00 | 1.00 |
| AF (atrial fibrillation) | 140 | 12 | 0.987 (0.966 to 1.000) | 0.020 | 1.00 | 0.81 |

## What may be shown (pass rules applied)

| Finding | Testable on drawn pages (positives) | Supported for drawn pages | Testable on photos (positives) | Supported for phone photos |
|---|---|---|---|---|
| 1dAVb (first-degree AV block) | False (12) | False | False (4) | False |
| RBBB (right bundle branch block) | True (30) | False | False (8) | False |
| LBBB (left bundle branch block) | False (2) | False | False (4) | False |
| SB (slow heart rate (sinus bradycardia)) | False (16) | False | False (6) | False |
| ST (fast heart rate (sinus tachycardia)) | False (12) | False | False (4) | False |
| AF (atrial fibrillation) | True (23) | True | False (12) | False |
