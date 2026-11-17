# Section CI: Bland-Altman pictures and cluster-bootstrap intervals (exploratory, descriptive)
Rules: `docs/plan/analysis_plan_changes.md`, 'Section CI' (logged before this script ran). Intervals: bootstrap over recordings (simulated, competition) or printed pages (phone photos), 2,000 resamples, percentile 95%. Nothing refitted; no pass/fail rule is re-applied.

Figure: `results/analysis/sectionCI_bland_altman.png` (also `docs/reports/figures/fig4_ci_bland_altman.png`). Numbers: `sectionCI_intervals.csv`.

## Heart rate (bpm), simulated, all 150 minus 2 unreliable

| Condition | Clusters | Statistic | Value (95% interval) |
|---|---|---|---|
| clean page | 148 | bias | -0.03 (-0.29 to 0.24) |
| clean page | 148 | lower limit | -3.16 (-4.64 to -1.36) |
| clean page | 148 | upper limit | 3.10 (1.32 to 4.44) |
| clean page | 148 | median abs error | 0.10 (0.10 to 0.10) |
| clean page | 148 | n images | 148.00 (148.00 to 148.00) |
| resolution level 5 | 148 | bias | 0.54 (-1.43 to 2.53) |
| resolution level 5 | 148 | lower limit | -24.86 (-30.20 to -19.21) |
| resolution level 5 | 148 | upper limit | 25.93 (21.47 to 29.71) |
| resolution level 5 | 148 | median abs error | 3.80 (1.90 to 6.00) |
| resolution level 5 | 148 | n images | 148.00 (148.00 to 148.00) |
| blur level 5 | 146 | bias | -1.26 (-2.59 to -0.07) |
| blur level 5 | 146 | lower limit | -17.51 (-24.60 to -10.17) |
| blur level 5 | 146 | upper limit | 14.99 (8.63 to 20.15) |
| blur level 5 | 146 | median abs error | 1.55 (1.20 to 1.90) |
| blur level 5 | 146 | n images | 146.00 (146.00 to 146.00) |

## Heart rate (bpm), CLEANED measure, new 100 only

| Condition | Clusters | Statistic | Value (95% interval) |
|---|---|---|---|
| clean page | 99 | bias | -0.33 (-0.90 to 0.07) |
| clean page | 99 | lower limit | -5.45 (-9.32 to -1.18) |
| clean page | 99 | upper limit | 4.79 (1.05 to 7.65) |
| clean page | 99 | median abs error | 0.08 (0.06 to 0.09) |
| clean page | 99 | n images | 99.00 (99.00 to 99.00) |
| resolution level 5 | 98 | bias | -0.62 (-3.51 to 2.25) |
| resolution level 5 | 98 | lower limit | -29.57 (-38.19 to -20.09) |
| resolution level 5 | 98 | upper limit | 28.33 (21.63 to 33.98) |
| resolution level 5 | 98 | median abs error | 5.15 (2.02 to 6.66) |
| resolution level 5 | 98 | n images | 98.00 (98.00 to 98.00) |
| blur level 5 | 97 | bias | -1.43 (-3.24 to 0.10) |
| blur level 5 | 97 | lower limit | -17.90 (-26.18 to -9.68) |
| blur level 5 | 97 | upper limit | 15.05 (7.98 to 20.95) |
| blur level 5 | 97 | median abs error | 1.52 (1.18 to 1.87) |
| blur level 5 | 97 | n images | 97.00 (97.00 to 97.00) |

## PR interval vs 12SL

| Condition | Clusters | Statistic | Value (95% interval) |
|---|---|---|---|
| digitised clean pages, held-out new 100 | 92 | bias (ms) | 3.09 (-0.24 to 6.74) |
| digitised clean pages, held-out new 100 | 92 | lower limit (ms) | -30.07 (-37.62 to -21.84) |
| digitised clean pages, held-out new 100 | 92 | upper limit (ms) | 36.25 (24.72 to 48.25) |
| digitised clean pages, held-out new 100 | 92 | median abs error (ms) | 7.33 (5.52 to 9.45) |
| digitised clean pages, held-out new 100 | 92 | within 40 ms (%) | 96.74 (92.39 to 100.00) |
| digitised clean pages, held-out new 100 | 92 | n | 92.00 (92.00 to 92.00) |
| digitised clean pages, held-out new 100 | 92 | 2.5th percentile of the differences (ms) | -27.68 (-32.29 to -14.45) |
| digitised clean pages, held-out new 100 | 92 | 97.5th percentile of the differences (ms) | 49.08 (21.90 to 75.96) |
| straightened phone photos (100 photos) | 43 | bias (ms) | 5.15 (-0.76 to 11.12) |
| straightened phone photos (100 photos) | 43 | lower limit (ms) | -38.63 (-52.45 to -24.02) |
| straightened phone photos (100 photos) | 43 | upper limit (ms) | 48.94 (31.84 to 67.34) |
| straightened phone photos (100 photos) | 43 | median abs error (ms) | 12.03 (7.50 to 16.14) |
| straightened phone photos (100 photos) | 43 | within 40 ms (%) | 95.24 (89.16 to 100.00) |
| straightened phone photos (100 photos) | 43 | n | 84.00 (81.00 to 86.00) |
| straightened phone photos (100 photos) | 43 | 2.5th percentile of the differences (ms) | -34.53 (-48.58 to -18.93) |
| straightened phone photos (100 photos) | 43 | 97.5th percentile of the differences (ms) | 50.34 (25.94 to 113.65) |

## Frontal QRS axis vs 12SL

| Condition | Clusters | Statistic | Value (95% interval) |
|---|---|---|---|
| 100 fresh pages, digitised | 99 | mean error (deg) | 0.57 (-0.87 to 2.18) |
| 100 fresh pages, digitised | 99 | lower limit (deg) | -14.41 (-17.99 to -10.69) |
| 100 fresh pages, digitised | 99 | upper limit (deg) | 15.56 (10.67 to 20.58) |
| 100 fresh pages, digitised | 99 | median abs error (deg) | 3.76 (2.41 to 5.33) |
| 100 fresh pages, digitised | 99 | within 30 deg (%) | 98.99 (96.97 to 100.00) |
| 100 fresh pages, digitised | 99 | n | 99.00 (99.00 to 99.00) |
| 100 fresh pages, digitised | 99 | 2.5th percentile of the differences (deg) | -10.00 (-17.28 to -8.55) |
| 100 fresh pages, digitised | 99 | 97.5th percentile of the differences (deg) | 15.70 (9.39 to 32.64) |
| straightened phone photos (100 photos) | 50 | mean error (deg) | 0.10 (-5.24 to 6.43) |
| straightened phone photos (100 photos) | 50 | lower limit (deg) | -41.87 (-60.97 to -15.71) |
| straightened phone photos (100 photos) | 50 | upper limit (deg) | 42.07 (13.66 to 69.37) |
| straightened phone photos (100 photos) | 50 | median abs error (deg) | 4.41 (3.37 to 5.71) |
| straightened phone photos (100 photos) | 50 | within 30 deg (%) | 95.00 (89.00 to 100.00) |
| straightened phone photos (100 photos) | 50 | n | 100.00 (100.00 to 100.00) |
| straightened phone photos (100 photos) | 50 | 2.5th percentile of the differences (deg) | -22.44 (-69.23 to -12.61) |
| straightened phone photos (100 photos) | 50 | 97.5th percentile of the differences (deg) | 28.76 (8.68 to 119.09) |

## Bad readings, original vs straightened

| Condition | Clusters | Statistic | Value (95% interval) |
|---|---|---|---|
| 40 confirmation photos (Section Q2) | 20 | original bad (%) | 35.00 (20.00 to 50.00) |
| 40 confirmation photos (Section Q2) | 20 | straightened bad (%) | 5.00 (0.00 to 15.00) |
| 40 confirmation photos (Section Q2) | 20 | drop (percentage points) | 30.00 (17.50 to 45.00) |
| 120 simulated photos (Section Z) | 60 | original bad (%) | 53.33 (47.50 to 60.00) |
| 120 simulated photos (Section Z) | 60 | straightened bad (%) | 17.50 (10.83 to 24.17) |
| 120 simulated photos (Section Z) | 60 | drop (percentage points) | 35.83 (26.67 to 45.00) |

## Traffic light, competition captures with an output

| Condition | Clusters | Statistic | Value (95% interval) |
|---|---|---|---|
| wrong heart rate by light | 140 | GREEN wrong (%) | 0.22 (0.00 to 0.56) |
| wrong heart rate by light | 140 | AMBER wrong (%) | 6.86 (1.29 to 14.49) |
| wrong heart rate by light | 140 | RED wrong (%) | 36.59 (20.29 to 56.82) |
| wrong heart rate by light | 140 | GREEN share of readings (%) | 76.23 (69.93 to 82.23) |

## Pre-set rule check with cluster intervals (share within tolerance; rule: at least 90%)

| Measure | Condition | Share within tolerance | Lower end of the 95% interval | Lower end at or above 90%? |
|---|---|---|---|---|
| PR interval vs 12SL | digitised clean pages, held-out new 100 | 96.7% | 92.4% | yes |
| PR interval vs 12SL | straightened phone photos (100 photos) | 95.2% | 89.2% | NO (point estimate met the rule, the interval reaches below it) |
| Frontal QRS axis vs 12SL | 100 fresh pages, digitised | 99.0% | 97.0% | yes |
| Frontal QRS axis vs 12SL | straightened phone photos (100 photos) | 95.0% | 89.0% | NO (point estimate met the rule, the interval reaches below it) |

Reading notes: the Bland-Altman limits are bias +- 1.96 standard deviations of the differences; their intervals come from resampling whole recordings. The two photos of a page are kept together when pages are resampled. The axis difference is wrapped to -180..180 degrees; the axis limits are therefore not a Gaussian statement when there are gross failures (P13: 117 to 121 degrees). Heart rate uses the original (not cleaned) measure, as in Section A, except panel d (cleaned measure, as in Section Q2). PR and axis compare against 12SL, an algorithm.
