# Heart health module on the six demo photos (descriptive; 6 photos, one fixed seed)

| Photo | PTB-XL label of the source recording | Light | Overall indicator | Supported findings found | Supported findings not found | Not available |
|---|---|---|---|---|---|---|
| sample1_straight_clean.jpg | normal ECG | GREEN | No supported abnormal pattern found | - | MI; STTC; CD | NORM; HYP; AF |
| sample2_angled_left.jpg | left ventricular hypertrophy, non-specific ischemic signs, non-specific intraventricular conduction delay | GREEN | Possible ECG pattern found: medical evaluation advised | STTC; CD | MI | NORM; HYP; AF |
| sample3_angled_from_below.jpg | complete left bundle branch block (conduction) | GREEN | Possible ECG pattern found: medical evaluation advised | CD | MI; STTC | NORM; HYP; AF |
| sample4_dim_uneven_light.jpg | incomplete right bundle branch block (conduction) and non-specific ST changes | GREEN | Possible ECG pattern found: medical evaluation advised | MI; STTC; CD | - | NORM; HYP; AF |
| sample5_far_and_small.jpg | left ventricular hypertrophy; possible old inferior heart attack (likelihood 15 of 100) | GREEN | Possible ECG pattern found: medical evaluation advised | MI; STTC; CD | - | NORM; HYP; AF |
| sample6_blurry_and_angled.jpg | normal ECG (likelihood 80 of 100) | RED | Photo not clear enough | - | - | NORM; MI; STTC; CD; HYP; AF |

Reading: only 6 photos, so this shows the path works and what the output looks like, not accuracy (accuracy is in SECTION_HEALTH.md).
