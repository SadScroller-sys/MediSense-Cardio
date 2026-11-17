# Section FIND2-A: PTB-XL fine labels, test once (EXPLORATORY; rules logged before training)

Rules: `docs/plan/analysis_plan_changes.md` ('MORE DISEASE FINDINGS' and Amendment 1). Public data only. Findings are ECG PATTERNS, not diagnoses and not risk. Pass rules and thresholds are the assistant's proposal, not approved by the guide. Intervals: bootstrap over clusters (2000 resamples); the photos of one page are not independent.

## T1 fold 10 (benchmark)

| Finding | n | Positives | AUROC (95% interval) | Calibration error | Sensitivity | Specificity |
|---|---|---|---|---|---|---|
| ASMI (anteroseptal infarction) | 2133 | 183 | 0.972 (0.963 to 0.979) | 0.013 | 0.94 | 0.91 |
| NDT (non-diagnostic T abnormality) | 2133 | 176 | 0.910 (0.890 to 0.929) | 0.006 | 0.86 | 0.80 |
| LVH (left ventricular hypertrophy) | 2133 | 172 | 0.942 (0.927 to 0.955) | 0.015 | 0.78 | 0.90 |
| IMI (inferior infarction) | 2133 | 168 | 0.924 (0.907 to 0.939) | 0.014 | 0.82 | 0.86 |
| LAFB (left anterior fascicular block) | 2133 | 154 | 0.982 (0.974 to 0.988) | 0.011 | 0.98 | 0.91 |
| ISC_ (non-specific ischaemia) | 2133 | 125 | 0.961 (0.948 to 0.973) | 0.010 | 0.91 | 0.86 |
| IRBBB (incomplete right bundle branch block) | 2133 | 109 | 0.967 (0.956 to 0.977) | 0.008 | 0.93 | 0.91 |
| PVC (premature ventricular beats) | 2133 | 94 | 0.968 (0.946 to 0.984) | 0.014 | 0.96 | 0.92 |
| 1AVB (first-degree AV block) | 2133 | 76 | 0.945 (0.927 to 0.961) | 0.008 | 0.91 | 0.84 |
| IVCD (non-specific conduction delay) | 2133 | 78 | 0.739 (0.677 to 0.797) | 0.008 | 0.76 | 0.64 |
| ISCAL (anterolateral ischaemia) | 2133 | 64 | 0.918 (0.885 to 0.945) | 0.006 | 0.88 | 0.81 |
| NST_ (non-specific ST change) | 2133 | 48 | 0.833 (0.785 to 0.875) | 0.002 | 0.60 | 0.83 |
| CRBBB (complete right bundle branch block) | 2133 | 51 | 0.998 (0.996 to 0.999) | 0.005 | 1.00 | 0.98 |
| CLBBB (complete left bundle branch block) | 2133 | 54 | 0.998 (0.995 to 0.999) | 0.006 | 1.00 | 0.95 |
| ILMI (inferolateral infarction) | 2133 | 35 | 0.940 (0.889 to 0.979) | 0.005 | 0.83 | 0.94 |
| LAO/LAE (left atrial enlargement) | 2133 | 41 | 0.804 (0.739 to 0.863) | 0.002 | 0.63 | 0.79 |

## T2 drawn pages, digitised

| Finding | n | Positives | AUROC (95% interval) | Calibration error | Sensitivity | Specificity |
|---|---|---|---|---|---|---|
| ASMI (anteroseptal infarction) | 300 | 34 | 0.930 (0.870 to 0.975) | 0.033 | 0.94 | 0.84 |
| NDT (non-diagnostic T abnormality) | 300 | 25 | 0.850 (0.753 to 0.928) | 0.028 | 0.80 | 0.82 |
| LVH (left ventricular hypertrophy) | 300 | 21 | 0.922 (0.875 to 0.961) | 0.046 | 0.81 | 0.85 |
| IMI (inferior infarction) | 300 | 15 | 0.916 (0.858 to 0.960) | 0.038 | 0.87 | 0.85 |
| LAFB (left anterior fascicular block) | 300 | 25 | 0.929 (0.832 to 0.990) | 0.022 | 0.92 | 0.91 |
| ISC_ (non-specific ischaemia) | 300 | 11 | 0.952 (0.887 to 0.989) | 0.040 | 0.91 | 0.85 |
| IRBBB (incomplete right bundle branch block) | 300 | 22 | 0.946 (0.890 to 0.982) | 0.030 | 0.91 | 0.90 |
| PVC (premature ventricular beats) | 300 | 15 | 0.971 (0.945 to 0.991) | 0.020 | 1.00 | 0.88 |
| 1AVB (first-degree AV block) | 300 | 12 | 0.932 (0.869 to 0.979) | 0.011 | 0.92 | 0.83 |
| IVCD (non-specific conduction delay) | 300 | 11 | 0.757 (0.604 to 0.893) | 0.017 | 0.91 | 0.46 |
| ISCAL (anterolateral ischaemia) | 300 | 7 | 0.945 (0.887 to 0.984) | 0.003 | 0.86 | 0.84 |
| NST_ (non-specific ST change) | 300 | 8 | 0.783 (0.570 to 0.957) | 0.009 | 0.62 | 0.87 |
| CRBBB (complete right bundle branch block) | 300 | 8 | 0.975 (0.926 to 1.000) | 0.013 | 0.88 | 0.98 |
| CLBBB (complete left bundle branch block) | 300 | 2 | 0.721 (0.462 to 0.963) | 0.007 | 0.50 | 0.91 |
| ILMI (inferolateral infarction) | 300 | 4 | 0.805 (0.538 to 1.000) | 0.008 | 0.50 | 0.95 |
| LAO/LAE (left atrial enlargement) | 300 | 10 | 0.734 (0.573 to 0.875) | 0.021 | 0.60 | 0.77 |

## T3 straightened phone photos

| Finding | n | Positives | AUROC (95% interval) | Calibration error | Sensitivity | Specificity |
|---|---|---|---|---|---|---|
| ASMI (anteroseptal infarction) | 140 | 4 | 0.954 (0.897 to 0.996) | 0.102 | 1.00 | 0.77 |
| NDT (non-diagnostic T abnormality) | 140 | 12 | 0.708 (0.583 to 0.831) | 0.089 | 0.33 | 0.73 |
| LVH (left ventricular hypertrophy) | 140 | 16 | 0.836 (0.736 to 0.921) | 0.140 | 0.94 | 0.67 |
| IMI (inferior infarction) | 140 | 12 | 0.937 (0.830 to 0.996) | 0.021 | 0.83 | 0.93 |
| LAFB (left anterior fascicular block) | 140 | 10 | 0.921 (0.808 to 0.986) | 0.044 | 0.90 | 0.89 |
| ISC_ (non-specific ischaemia) | 140 | 12 | 0.840 (0.684 to 0.956) | 0.088 | 0.83 | 0.69 |
| IRBBB (incomplete right bundle branch block) | 140 | 8 | 0.772 (0.251 to 1.000) | 0.041 | 0.75 | 0.96 |
| PVC (premature ventricular beats) | 140 | 6 | 0.919 (0.859 to 0.970) | 0.084 | 1.00 | 0.85 |
| 1AVB (first-degree AV block) | 140 | 4 | 0.741 (0.457 to 1.000) | 0.025 | 0.75 | 0.83 |
| IVCD (non-specific conduction delay) | 140 | 6 | 0.724 (0.351 to 1.000) | 0.026 | 0.83 | 0.50 |
| ISCAL (anterolateral ischaemia) | 140 | 10 | 0.820 (0.593 to 0.993) | 0.051 | 0.80 | 0.80 |
| NST_ (non-specific ST change) | 140 | 8 | 0.663 (0.378 to 0.968) | 0.038 | 0.38 | 0.83 |
| CRBBB (complete right bundle branch block) | 140 | 0 | nan (nan to nan) | 0.023 | nan | 0.94 |
| CLBBB (complete left bundle branch block) | 140 | 4 | 0.550 (0.062 to 1.000) | 0.014 | 0.50 | 0.93 |
| ILMI (inferolateral infarction) | 140 | 2 | 0.750 (0.692 to 0.805) | 0.015 | 0.50 | 0.94 |
| LAO/LAE (left atrial enlargement) | 140 | 2 | 0.953 (0.913 to 0.986) | 0.037 | 1.00 | 0.65 |

## What may be shown (pass rules applied)

| Finding | Testable on drawn pages (positives) | Supported for drawn pages | Testable on photos (positives) | Supported for phone photos |
|---|---|---|---|---|
| ASMI (anteroseptal infarction) | True (34) | True | False (4) | False |
| NDT (non-diagnostic T abnormality) | True (25) | True | False (12) | False |
| LVH (left ventricular hypertrophy) | True (21) | True | False (16) | False |
| IMI (inferior infarction) | False (15) | False | False (12) | False |
| LAFB (left anterior fascicular block) | True (25) | True | False (10) | False |
| ISC_ (non-specific ischaemia) | False (11) | False | False (12) | False |
| IRBBB (incomplete right bundle branch block) | True (22) | True | False (8) | False |
| PVC (premature ventricular beats) | False (15) | False | False (6) | False |
| 1AVB (first-degree AV block) | False (12) | False | False (4) | False |
| IVCD (non-specific conduction delay) | False (11) | False | False (6) | False |
| ISCAL (anterolateral ischaemia) | False (7) | False | False (10) | False |
| NST_ (non-specific ST change) | False (8) | False | False (8) | False |
| CRBBB (complete right bundle branch block) | False (8) | False | False (0) | False |
| CLBBB (complete left bundle branch block) | False (2) | False | False (4) | False |
| ILMI (inferolateral infarction) | False (4) | False | False (2) | False |
| LAO/LAE (left atrial enlargement) | False (10) | False | False (2) | False |
