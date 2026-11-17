# Section U: PR and QRS with my own method, tested once on the new 100 (EXPLORATORY, added after the freeze)

Rules fixed before any code ran (`docs/plan/analysis_plan_changes.md`, 2026-11-14 later entries). The acceptance rules are the assistant's proposal and are **not approved by the guide**. Frozen on the first 50: QRS = qrs_C_5 (offset -7.6 ms), PR = pr_B_tan (offset +5.8 ms). Primary set: clean pages of the new 100 recordings, 21205 excluded (99 recordings). Difference = measured minus 12SL.

## QRS duration (rule: median abs diff <= 10 ms, 90% within 20 ms, |bias| <= 5 ms; at least 90% with a value)

| Measurement | With a value | rho with 12SL | Median abs diff (95% CI) | 90th pct | Bias (95% CI) | Within tolerance | Rule |
|---|---|---|---|---|---|---|---|
| (a) frozen method on the original signal, photo windows | 99 of 99 (100% of those with a reference) | 0.37 | 8.4 (6.4 to 9.4) | 27.2 | +1.0 (-2.3 to +4.1) | 85% | **does not meet** |
| (b) digitised clean page | 99 of 99 (100% of those with a reference) | 0.13 | 13.2 (9.5 to 15.8) | 28.1 | +1.6 (-2.2 to +5.6) | 72% | **does not meet** |
| (c) digitised minus (a): what the photo adds | 99 | | 8.6 | 25.1 | +0.6 | | |

**QRS duration validated on the held-out test: NO** ((a) meets: False, (b) meets: False). Still needs the new-photo confirmation.

## PR interval (rule: median abs diff <= 20 ms, 90% within 40 ms, |bias| <= 10 ms; at least 90% with a value)

| Measurement | With a value | rho with 12SL | Median abs diff (95% CI) | 90th pct | Bias (95% CI) | Within tolerance | Rule |
|---|---|---|---|---|---|---|---|
| (a) frozen method on the original signal, photo windows | 97 of 99 (98% of those with a reference) | 0.85 | 8.2 (6.5 to 10.2) | 24.8 | +0.1 (-2.9 to +3.2) | 99% | **meets** |
| (b) digitised clean page | 98 of 99 (99% of those with a reference) | 0.79 | 7.3 (5.5 to 9.4) | 24.0 | +3.1 (-0.0 to +6.6) | 97% | **meets** |
| (c) digitised minus (a): what the photo adds | 97 | | 6.9 | 16.8 | +2.9 | | |

**PR interval validated on the held-out test: YES** ((a) meets: True, (b) meets: True). Still needs the new-photo confirmation.

## Secondary (descriptive): digitised, all versions, by damage; GREEN images only (median abs diff / bias in ms; value share)

| Group | Images | QRS | PR |
|---|---|---|---|
| all versions | 1287 | 17 / +20; 98% | 8 / +3; 88% |
| GREEN images only | 903 | 14 / +8; 100% | 7 / +2; 96% |
| clean | 99 | 13 / +2; 100% | 7 / +3; 99% |
| blur 3 | 99 | 35 / +33; 100% | 9 / +3; 91% |
| blur 5 | 99 | 67 / +80; 97% | 13 / +8; 47% |
| rotate 3 | 99 | 14 / +2; 98% | 9 / +2; 99% |
| rotate 5 | 99 | 18 / +18; 82% | 8 / +2; 73% |
| jpeg 3 | 99 | 12 / +1; 100% | 8 / +4; 100% |
| jpeg 5 | 99 | 11 / +1; 99% | 7 / +4; 95% |
| resolution 3 | 99 | 15 / +11; 100% | 7 / +2; 95% |
| resolution 5 | 99 | 91 / +101; 100% | 17 / +10; 43% |
| brightness 3 | 99 | 14 / +3; 100% | 9 / +2; 100% |
| brightness 5 | 99 | 12 / +2; 99% | 7 / +4; 98% |
| gridcontrast 3 | 99 | 12 / +1; 100% | 7 / +3; 100% |
| gridcontrast 5 | 99 | 12 / +1; 100% | 8 / +3; 99% |

## Development tables (first 50 recordings; for the record)

**QRS**

| Candidate | Value share | Bias before offset | Offset | Median abs after offset | rho |
|---|---|---|---|---|---|
| qrs_A_5 | 100% | -27.0 | -26.0 | 12.0 | 0.28 |
| qrs_A_10 | 100% | -36.5 | -34.0 | 10.0 | 0.24 |
| qrs_B_5 | 100% | -33.4 | -31.5 | 9.0 | 0.24 |
| qrs_B_10 | 100% | -43.2 | -40.0 | 8.5 | 0.22 |
| qrs_C_5 | 100% | -8.4 | -7.6 | 6.8 | 0.58 |
| qrs_C_10 | 100% | -25.5 | -24.2 | 9.7 | 0.33 |

**PR**

| Candidate | Value share | Bias before offset | Offset | Median abs after offset | rho |
|---|---|---|---|---|---|
| pr_A_tan | 94% | +3.9 | +4.2 | 9.9 | 0.76 |
| pr_A_thr | 48% | +40.0 | +39.0 | 27.0 | 0.35 |
| pr_B_tan | 96% | +6.5 | +5.8 | 7.5 | 0.78 |
| pr_B_thr | 83% | +14.8 | +17.5 | 12.0 | 0.44 |
| pr_C_tan | 96% | +28.3 | +24.9 | 15.4 | 0.56 |
| pr_C_thr | 83% | +52.4 | +49.5 | 18.8 | 0.25 |

## Limits

- The pixel size (about 5 ms at 200 dpi) bounds the QRS duration error from below; blurred or small photos cannot meet a 10 ms rule.
- 12SL is an algorithm, not an expert measurement. Developed on 50 recordings with 6 candidates per parameter and one offset: mild overfitting is possible.
- One digitiser, simulated pages. Nothing from this section is shown to patients unless the held-out test AND the new-photo confirmation both say YES.