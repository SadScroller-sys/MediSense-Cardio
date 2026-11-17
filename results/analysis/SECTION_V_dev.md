# Section V development (1,000 unused original recordings, page-layout windows)

Reference = 12SL. Value share = share of recordings with a value. CV = 5-fold cross-validation by recording, calibration refitted on the training folds. Selection rule from the 2026-11-14 (night) plan entry.

## QT interval

| Candidate | Recordings with a value | n | CV median abs diff (ms) | CV within tolerance | CV bias (ms) | rho (raw) |
|---|---|---|---|---|---|---|
| qt_B_tan | 99% | 993 | 8.8 | 90% | -0.1 | 0.72 |
| qt_B_area | 99% | 993 | 28.9 | 67% | -0.0 | 0.61 |
| qt_D_tan | 99% | 993 | 9.8 | 87% | -0.1 | 0.69 |
| qt_D_area | 99% | 993 | 28.3 | 68% | -0.0 | 0.62 |
| qt_E_tan | 99% | 993 | 9.7 | 87% | -0.0 | 0.69 |
| qt_E_area | 99% | 993 | 29.6 | 63% | -0.0 | 0.59 |

**Frozen candidate: qt_B_tan**; original-signal calibration {'b': -0.012879583705991996, 'c': 50.22505920888459}

## QRS duration

| Candidate | Recordings with a value | n | CV median abs diff (ms) | CV within tolerance | CV bias (ms) | rho (raw) |
|---|---|---|---|---|---|---|
| qrs_C1_3 | 99% | 994 | 7.0 | 85% | +0.0 | 0.62 |
| qrs_C1_5 | 99% | 994 | 8.0 | 82% | +0.0 | 0.51 |
| qrs_C1_10 | 99% | 994 | 10.6 | 80% | -0.0 | 0.38 |
| qrs_C2_3 | 99% | 994 | 8.1 | 83% | +0.0 | 0.62 |
| qrs_C2_5 | 99% | 994 | 7.8 | 82% | +0.0 | 0.54 |
| qrs_C2_10 | 99% | 994 | 9.1 | 81% | +0.0 | 0.44 |
| qrs_B_3 | 99% | 994 | 10.5 | 80% | -0.0 | 0.35 |
| qrs_B_5 | 99% | 994 | 9.8 | 82% | -0.0 | 0.35 |
| qrs_B_10 | 99% | 994 | 9.7 | 82% | -0.0 | 0.30 |

**Frozen candidate: qrs_C1_3**; original-signal calibration {'c': -8.588732394366199}

## Photo calibration (fitted once on the digitised clean pages of 99 earlier held-out recordings)

- QT: candidate qt_B_tan, photo calibration {'b': -0.004748054087555346, 'c': 33.93072647700216}; in-sample median abs diff 8.3 ms (for the record only: this fit is NOT a test)
- QRS: candidate qrs_C1_3, photo calibration {'c': -11.198989898989899}; in-sample median abs diff 10.6 ms (for the record only: this fit is NOT a test)
