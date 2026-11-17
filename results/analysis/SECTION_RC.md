# Section RC: risk-coverage curves from existing predictions (exploratory, descriptive)
Rules: `docs/plan/analysis_plan_changes.md`, 'Section RC' (logged before this script ran) and its Amendment 1 (sets D and E added after the first run, same method; the traffic-light scores of D and E were recomputed by the frozen tool from the saved digitised signals, and the recomputed light equals the saved light on all 320 images, `sectionRC_light_recompute_check.csv`). Nothing was fitted or retrained. Bad = wrong heart rate (more than 5 bpm, cleaned measure) or no output; for the own-phone set, no usable HR or wrong. Intervals: bootstrap over recordings (A, B) or pages (C), 2,000 resamples, ranking recomputed inside each resample. No guarantee of any kind.

Figure: `results/analysis/sectionRC_risk_coverage.png` (also `docs/reports/figures/fig4_rc_risk_coverage.png`).

## A. Competition real captures (1,260 images, 140 recordings): 103 bad of 1260 (8.2%)

| Score | Coverage | Images answered | Bad among answered % (95% interval) | Random % | Oracle % |
|---|---|---|---|---|---|
| Traffic light | 70% | 882 | 0.23 (0.00 to 0.79) | 8.17 | 0.00 |
| Traffic light | 80% | 1008 | 0.89 (0.20 to 2.18) | 8.17 | 0.00 |
| Traffic light | 90% | 1134 | 1.76 (0.53 to 3.35) | 8.17 | 0.00 |
| Traffic light | 100% | 1260 | 8.17 (6.19 to 10.48) | 8.17 | 8.17 |

| Score | AURC % (95% interval) | Random % | Oracle % |
|---|---|---|---|
| Traffic light | 0.91 (0.39 to 1.63) | 8.17 | 0.40 |

Traffic-light operating points:

| Answered | Coverage | Images | Bad among answered | Selective risk % | Random % |
|---|---|---|---|---|---|
| GREEN only | 72.8% | 917 | 2 | 0.22 | 8.17 |
| GREEN + AMBER | 89.0% | 1121 | 16 | 1.43 | 8.17 |

## B. Arm C+ subset (900 images, 100 recordings): 73 bad of 900 (8.1%)

| Score | Coverage | Images answered | Bad among answered % (95% interval) | Random % | Oracle % |
|---|---|---|---|---|---|
| Traffic light | 70% | 630 | 0.32 (0.00 to 1.11) | 8.11 | 0.00 |
| Traffic light | 80% | 720 | 0.97 (0.14 to 2.78) | 8.11 | 0.00 |
| Traffic light | 90% | 810 | 1.98 (0.49 to 4.07) | 8.11 | 0.00 |
| Traffic light | 100% | 900 | 8.11 (6.00 to 10.67) | 8.11 | 8.11 |
| Photo detector | 70% | 630 | 4.60 (2.70 to 6.98) | 8.11 | 0.00 |
| Photo detector | 80% | 720 | 4.17 (2.50 to 6.39) | 8.11 | 0.00 |
| Photo detector | 90% | 810 | 5.43 (3.33 to 7.90) | 8.11 | 0.00 |
| Photo detector | 100% | 900 | 8.11 (6.00 to 10.67) | 8.11 | 8.11 |

| Score | AURC % (95% interval) | Random % | Oracle % |
|---|---|---|---|
| Traffic light | 1.05 (0.38 to 2.03) | 8.11 | 0.39 |
| Photo detector | 4.30 (2.41 to 6.76) | 8.11 | 0.39 |

Traffic-light operating points:

| Answered | Coverage | Images | Bad among answered | Selective risk % | Random % |
|---|---|---|---|---|---|
| GREEN only | 73.3% | 660 | 2 | 0.30 | 8.11 |
| GREEN + AMBER | 88.9% | 800 | 12 | 1.50 | 8.11 |

## C. Own phone set 1 (60 photos, 30 pages): 20 bad of 60 (33.3%)

| Score | Coverage | Images answered | Bad among answered % (95% interval) | Random % | Oracle % |
|---|---|---|---|---|---|
| Traffic light | 70% | 42 | 11.90 (2.38 to 26.19) | 33.33 | 4.76 |
| Traffic light | 80% | 48 | 18.75 (6.25 to 33.33) | 33.33 | 16.67 |
| Traffic light | 90% | 54 | 25.93 (12.96 to 40.74) | 33.33 | 25.93 |
| Traffic light | 100% | 60 | 33.33 (21.67 to 46.67) | 33.33 | 33.33 |
| Photo detector | 70% | 42 | 40.48 (23.81 to 54.76) | 33.33 | 4.76 |
| Photo detector | 80% | 48 | 37.50 (22.86 to 52.08) | 33.33 | 16.67 |
| Photo detector | 90% | 54 | 33.33 (20.37 to 48.15) | 33.33 | 25.93 |
| Photo detector | 100% | 60 | 33.33 (21.67 to 46.67) | 33.33 | 33.33 |

| Score | AURC % (95% interval) | Random % | Oracle % |
|---|---|---|---|
| Traffic light | 11.39 (4.71 to 21.10) | 33.33 | 6.98 |
| Photo detector | 29.49 (14.06 to 47.89) | 33.33 | 6.98 |

Traffic-light operating points:

| Answered | Coverage | Images | Bad among answered | Selective risk % | Random % |
|---|---|---|---|---|---|
| GREEN only | 36.7% | 22 | 0 | 0.00 | 33.33 |
| GREEN + AMBER | 61.7% | 37 | 1 | 2.70 | 33.33 |

## D0. Confirmation photos as taken (40 photos, 20 pages): 14 bad of 40 (35.0%)

| Score | Coverage | Images answered | Bad among answered % (95% interval) | Random % | Oracle % |
|---|---|---|---|---|---|
| Traffic light | 70% | 28 | 7.14 (0.00 to 28.57) | 35.00 | 7.14 |
| Traffic light | 80% | 32 | 18.75 (3.12 to 37.50) | 35.00 | 18.75 |
| Traffic light | 90% | 36 | 27.78 (11.11 to 44.44) | 35.00 | 27.78 |
| Traffic light | 100% | 40 | 35.00 (20.00 to 50.00) | 35.00 | 35.00 |

| Score | AURC % (95% interval) | Random % | Oracle % |
|---|---|---|---|
| Traffic light | 8.57 (2.71 to 18.51) | 35.00 | 7.83 |

Traffic-light operating points:

| Answered | Coverage | Images | Bad among answered | Selective risk % | Random % |
|---|---|---|---|---|---|
| GREEN only | 50.0% | 20 | 0 | 0.00 | 35.00 |
| GREEN + AMBER | 67.5% | 27 | 1 | 3.70 | 35.00 |

## D2. Confirmation photos straightened (40 photos, 20 pages): 2 bad of 40 (5.0%)

| Score | Coverage | Images answered | Bad among answered % (95% interval) | Random % | Oracle % |
|---|---|---|---|---|---|
| Traffic light | 70% | 28 | 0.00 (0.00 to 0.00) | 5.00 | 0.00 |
| Traffic light | 80% | 32 | 0.00 (0.00 to 0.00) | 5.00 | 0.00 |
| Traffic light | 90% | 36 | 0.00 (0.00 to 5.56) | 5.00 | 0.00 |
| Traffic light | 100% | 40 | 5.00 (0.00 to 15.00) | 5.00 | 5.00 |

| Score | AURC % (95% interval) | Random % | Oracle % |
|---|---|---|---|
| Traffic light | 0.21 (0.00 to 1.47) | 5.00 | 0.21 |

Traffic-light operating points:

| Answered | Coverage | Images | Bad among answered | Selective risk % | Random % |
|---|---|---|---|---|---|
| GREEN only | 80.0% | 32 | 0 | 0.00 | 5.00 |
| GREEN + AMBER | 97.5% | 39 | 1 | 2.56 | 5.00 |

## E0. Simulated photos as made (120 photos, 60 pages): 64 bad of 120 (53.3%)

| Score | Coverage | Images answered | Bad among answered % (95% interval) | Random % | Oracle % |
|---|---|---|---|---|---|
| Traffic light | 70% | 84 | 36.90 (28.57 to 46.43) | 53.33 | 33.33 |
| Traffic light | 80% | 96 | 42.71 (36.43 to 51.04) | 53.33 | 41.67 |
| Traffic light | 90% | 108 | 48.15 (41.67 to 55.56) | 53.33 | 48.15 |
| Traffic light | 100% | 120 | 53.33 (46.67 to 60.00) | 53.33 | 53.33 |

| Score | AURC % (95% interval) | Random % | Oracle % |
|---|---|---|---|
| Traffic light | 23.51 (17.97 to 30.10) | 53.33 | 18.97 |

Traffic-light operating points:

| Answered | Coverage | Images | Bad among answered | Selective risk % | Random % |
|---|---|---|---|---|---|
| GREEN only | 25.0% | 30 | 0 | 0.00 | 53.33 |
| GREEN + AMBER | 39.2% | 47 | 3 | 6.38 | 53.33 |

## E2. Simulated photos straightened (120 photos, 60 pages): 21 bad of 120 (17.5%)

| Score | Coverage | Images answered | Bad among answered % (95% interval) | Random % | Oracle % |
|---|---|---|---|---|---|
| Traffic light | 70% | 84 | 7.14 (0.00 to 13.10) | 17.50 | 0.00 |
| Traffic light | 80% | 96 | 10.42 (4.17 to 17.71) | 17.50 | 0.00 |
| Traffic light | 90% | 108 | 12.04 (6.48 to 19.44) | 17.50 | 8.33 |
| Traffic light | 100% | 120 | 17.50 (10.83 to 24.17) | 17.50 | 17.50 |

| Score | AURC % (95% interval) | Random % | Oracle % |
|---|---|---|---|
| Traffic light | 7.11 (2.29 to 14.18) | 17.50 | 1.85 |

Traffic-light operating points:

| Answered | Coverage | Images | Bad among answered | Selective risk % | Random % |
|---|---|---|---|---|---|
| GREEN only | 59.2% | 71 | 1 | 1.41 | 17.50 |
| GREEN + AMBER | 80.8% | 97 | 11 | 11.34 | 17.50 |

AURC = mean selective risk over coverage 0.05 to 1.00 (smaller is better). Random order gives the overall bad rate at every coverage; the oracle answers all good images first.
Limits: real captures of one source set and one phone; (B) and (C) hold fewer than 100 bad readings, so they are descriptive; the images are not exchangeable calibration data, so no coverage or risk guarantee is claimed; the photo detector was trained on simulated damage with the original-measure labels and is scored here against the cleaned labels, the same as the traffic light.
