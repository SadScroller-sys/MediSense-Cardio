# Heart health module, the DATASET-ONLY model 1 (PTB-XL only): tested again ONCE on NEW fresh data (EXPLORATORY; user decisions of 2026-11-15 logged before)

Model 1 unchanged (trained on PTB-XL only; Platt and thresholds from fold 9). L, M and the printed-paper photos were never used for anything but this single test. Real photos: PRIMARY = straight full-resolution photos of set H2 (friend's phone), SECONDARY = all full-resolution photos. Pass rules are the assistant's proposal, not approved by the guide. Findings are ECG patterns, not risk.

## L pages

| Class | n | Positives | Clusters | AUROC (95% interval) | Calibration error | Brier | Sensitivity | Specificity |
|---|---|---|---|---|---|---|---|---|
| NORM | 100 | 33 | 100 | 0.956 (0.903 to 0.995) | 0.072 | 0.071 | 0.82 | 0.97 |
| MI | 100 | 35 | 100 | 0.938 (0.889 to 0.975) | 0.097 | 0.096 | 0.97 | 0.75 |
| STTC | 100 | 23 | 100 | 0.942 (0.875 to 0.989) | 0.073 | 0.074 | 0.87 | 0.86 |
| CD | 100 | 41 | 100 | 0.926 (0.868 to 0.972) | 0.095 | 0.097 | 0.88 | 0.81 |
| HYP | 100 | 10 | 100 | 0.703 (0.571 to 0.827) | 0.189 | 0.202 | 0.90 | 0.58 |
| AF | 100 | 13 | 100 | 0.934 (0.835 to 1.000) | 0.049 | 0.039 | 0.85 | 0.95 |

## M pages

| Class | n | Positives | Clusters | AUROC (95% interval) | Calibration error | Brier | Sensitivity | Specificity |
|---|---|---|---|---|---|---|---|---|
| NORM | 100 | 30 | 100 | 0.868 (0.767 to 0.954) | 0.093 | 0.114 | 0.73 | 0.91 |
| MI | 100 | 27 | 100 | 0.943 (0.893 to 0.979) | 0.109 | 0.092 | 0.96 | 0.74 |
| STTC | 100 | 35 | 100 | 0.903 (0.839 to 0.955) | 0.069 | 0.122 | 0.83 | 0.78 |
| CD | 100 | 31 | 100 | 0.919 (0.838 to 0.979) | 0.067 | 0.098 | 0.90 | 0.84 |
| HYP | 100 | 37 | 100 | 0.792 (0.696 to 0.879) | 0.201 | 0.224 | 0.84 | 0.71 |
| AF | 100 | 27 | 100 | 0.936 (0.863 to 0.988) | 0.122 | 0.101 | 0.70 | 0.97 |

## L simulated photos

| Class | n | Positives | Clusters | AUROC (95% interval) | Calibration error | Brier | Sensitivity | Specificity |
|---|---|---|---|---|---|---|---|---|
| NORM | 100 | 33 | 100 | 0.711 (0.572 to 0.837) | 0.199 | 0.187 | 0.45 | 0.99 |
| MI | 100 | 35 | 100 | 0.840 (0.745 to 0.923) | 0.092 | 0.155 | 0.86 | 0.69 |
| STTC | 100 | 23 | 100 | 0.848 (0.744 to 0.928) | 0.127 | 0.150 | 0.87 | 0.73 |
| CD | 100 | 41 | 100 | 0.790 (0.678 to 0.892) | 0.163 | 0.174 | 0.80 | 0.56 |
| HYP | 100 | 10 | 100 | 0.630 (0.502 to 0.751) | 0.347 | 0.349 | 0.90 | 0.42 |
| AF | 100 | 13 | 100 | 0.838 (0.652 to 0.985) | 0.052 | 0.054 | 0.69 | 0.94 |

## M simulated photos

| Class | n | Positives | Clusters | AUROC (95% interval) | Calibration error | Brier | Sensitivity | Specificity |
|---|---|---|---|---|---|---|---|---|
| NORM | 100 | 30 | 100 | 0.818 (0.700 to 0.924) | 0.145 | 0.133 | 0.57 | 0.99 |
| MI | 100 | 27 | 100 | 0.789 (0.671 to 0.895) | 0.144 | 0.159 | 0.70 | 0.71 |
| STTC | 100 | 35 | 100 | 0.835 (0.749 to 0.913) | 0.127 | 0.172 | 0.89 | 0.66 |
| CD | 100 | 31 | 100 | 0.771 (0.671 to 0.864) | 0.136 | 0.193 | 0.77 | 0.65 |
| HYP | 100 | 37 | 100 | 0.775 (0.675 to 0.859) | 0.234 | 0.247 | 0.97 | 0.51 |
| AF | 100 | 27 | 100 | 0.772 (0.645 to 0.888) | 0.178 | 0.170 | 0.52 | 0.96 |

## H2 real STRAIGHT photos (printed paper, friend's phone)

| Class | n | Positives | Clusters | AUROC (95% interval) | Calibration error | Brier | Sensitivity | Specificity |
|---|---|---|---|---|---|---|---|---|
| NORM | 22 | 7 | 18 | 0.914 (0.785 to 1.000) | 0.216 | 0.180 | 0.43 | 1.00 |
| MI | 22 | 5 | 18 | 0.765 (0.439 to 1.000) | 0.360 | 0.262 | 0.80 | 0.41 |
| STTC | 22 | 6 | 18 | 0.802 (0.500 to 1.000) | 0.265 | 0.195 | 0.67 | 0.88 |
| CD | 22 | 5 | 18 | 0.424 (0.167 to 0.500) | 0.221 | 0.216 | 0.40 | 0.53 |
| HYP | 22 | 5 | 18 | 0.776 (0.556 to 0.941) | 0.303 | 0.250 | 1.00 | 0.71 |
| AF | 22 | 0 | 18 | nan (nan to nan) | 0.024 | 0.004 | nan | 0.95 |

## H2 ALL full-resolution photos (secondary)

| Class | n | Positives | Clusters | AUROC (95% interval) | Calibration error | Brier | Sensitivity | Specificity |
|---|---|---|---|---|---|---|---|---|
| NORM | 52 | 17 | 19 | 0.713 (0.576 to 0.854) | 0.249 | 0.223 | 0.29 | 1.00 |
| MI | 52 | 13 | 19 | 0.673 (0.553 to 0.775) | 0.274 | 0.265 | 0.54 | 0.54 |
| STTC | 52 | 12 | 19 | 0.723 (0.563 to 0.870) | 0.211 | 0.233 | 0.67 | 0.68 |
| CD | 52 | 12 | 19 | 0.485 (0.358 to 0.608) | 0.275 | 0.271 | 0.58 | 0.47 |
| HYP | 52 | 10 | 19 | 0.707 (0.578 to 0.826) | 0.444 | 0.415 | 1.00 | 0.43 |
| AF | 52 | 0 | 19 | nan (nan to nan) | 0.026 | 0.007 | nan | 0.96 |

## POOLED fresh pages (L + M)

| Class | n | Positives | Clusters | AUROC (95% interval) | Calibration error | Brier | Sensitivity | Specificity |
|---|---|---|---|---|---|---|---|---|
| NORM | 200 | 63 | 200 | 0.916 (0.860 to 0.959) | 0.067 | 0.092 | 0.78 | 0.94 |
| MI | 200 | 62 | 200 | 0.940 (0.907 to 0.969) | 0.072 | 0.094 | 0.97 | 0.75 |
| STTC | 200 | 58 | 200 | 0.924 (0.881 to 0.959) | 0.033 | 0.098 | 0.84 | 0.82 |
| CD | 200 | 72 | 200 | 0.922 (0.876 to 0.959) | 0.056 | 0.097 | 0.89 | 0.83 |
| HYP | 200 | 47 | 200 | 0.749 (0.677 to 0.818) | 0.165 | 0.213 | 0.85 | 0.63 |
| AF | 200 | 40 | 200 | 0.932 (0.873 to 0.974) | 0.082 | 0.070 | 0.75 | 0.96 |

## POOLED fresh photos (L + M + H2)

| Class | n | Positives | Clusters | AUROC (95% interval) | Calibration error | Brier | Sensitivity | Specificity |
|---|---|---|---|---|---|---|---|---|
| NORM | 222 | 70 | 218 | 0.774 (0.688 to 0.854) | 0.168 | 0.162 | 0.50 | 0.99 |
| MI | 222 | 67 | 218 | 0.809 (0.742 to 0.867) | 0.120 | 0.167 | 0.79 | 0.67 |
| STTC | 222 | 64 | 218 | 0.839 (0.782 to 0.888) | 0.103 | 0.164 | 0.86 | 0.72 |
| CD | 222 | 77 | 218 | 0.758 (0.684 to 0.828) | 0.128 | 0.187 | 0.77 | 0.60 |
| HYP | 222 | 52 | 218 | 0.738 (0.668 to 0.799) | 0.257 | 0.293 | 0.96 | 0.48 |
| AF | 222 | 40 | 218 | 0.781 (0.674 to 0.868) | 0.095 | 0.101 | 0.57 | 0.95 |

## What the app may show (pass rules applied)

| Class | Testable on pages | Supported for drawn pages | Testable on photos | Real H photos OK | Supported for phone photos | Percentage allowed |
|---|---|---|---|---|---|---|
| NORM | True | True | True | True | **True** | False |
| MI | True | True | True | True | **True** | False |
| STTC | True | True | True | True | **True** | False |
| CD | True | True | True | False | **False** | False |
| HYP | True | False | True | True | **False** | False |
| AF | True | True | True | False | **False** | False |
