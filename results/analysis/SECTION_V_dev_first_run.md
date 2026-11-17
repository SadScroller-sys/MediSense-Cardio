# Section V development (1,000 unused original recordings, page-layout windows)

Reference = 12SL. Value share = share of recordings with a value. CV = 5-fold cross-validation by recording, calibration refitted on the training folds. Selection rule from the 2026-11-14 (night) plan entry.

## QT interval

| Candidate | Recordings with a value | n | CV median abs diff (ms) | CV within tolerance | CV bias (ms) | rho (raw) |
|---|---|---|---|---|---|---|
| qt_B_tan | 99% | 993 | 14.1 | 89% | -0.0 | 0.72 |
| qt_B_area | 99% | 993 | 15.9 | 88% | +0.0 | 0.61 |
| qt_D_tan | 99% | 993 | 14.0 | 89% | -0.0 | 0.69 |
| qt_D_area | 99% | 993 | 15.9 | 88% | +0.0 | 0.62 |
| qt_E_tan | 99% | 993 | 14.4 | 89% | +0.0 | 0.69 |
| qt_E_area | 99% | 993 | 15.4 | 88% | +0.0 | 0.59 |

**Frozen candidate: qt_D_tan**; original-signal calibration {'a': 0.19163819767836812, 'b': 0.10244249731557581, 'c': 240.29992985978785}

## QRS duration

| Candidate | Recordings with a value | n | CV median abs diff (ms) | CV within tolerance | CV bias (ms) | rho (raw) |
|---|---|---|---|---|---|---|
| qrs_C1_3 | 99% | 994 | 7.4 | 87% | +0.0 | 0.62 |
| qrs_C1_5 | 99% | 994 | 8.6 | 86% | +0.0 | 0.51 |
| qrs_C1_10 | 99% | 994 | 8.7 | 84% | +0.0 | 0.38 |
| qrs_C2_3 | 99% | 994 | 7.5 | 87% | +0.0 | 0.62 |
| qrs_C2_5 | 99% | 994 | 8.2 | 86% | +0.0 | 0.54 |
| qrs_C2_10 | 99% | 994 | 8.2 | 84% | +0.0 | 0.44 |
| qrs_B_3 | 99% | 994 | 9.5 | 85% | +0.0 | 0.35 |
| qrs_B_5 | 99% | 994 | 9.4 | 85% | +0.0 | 0.35 |
| qrs_B_10 | 99% | 994 | 9.6 | 84% | -0.0 | 0.30 |

**Frozen candidate: qrs_C1_3**; original-signal calibration {'a': 0.41292891252143926, 'c': 54.132903109837144}

## Photo calibration (fitted once on the digitised clean pages of 99 earlier held-out recordings)

- QT: candidate qt_D_tan, photo calibration {'a': 0.4726870039289073, 'b': 0.0776625928461348, 'c': 157.218600128637}; in-sample median abs diff 10.6 ms (for the record only: this fit is NOT a test)
- QRS: candidate qrs_C1_3, photo calibration {'a': 0.18088689670234137, 'c': 76.311248077256}; in-sample median abs diff 7.4 ms (for the record only: this fit is NOT a test)
