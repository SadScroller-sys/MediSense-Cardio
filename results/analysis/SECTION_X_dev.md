# Section X development (1,100 development recordings, original signals, page-layout windows)

Offset-only calibration (QT: + b x RR + c; QRS: + c) refitted on the training folds. CV = 5-fold by recording. Eligible = a value for at least 90% AND a cross-validated slope on 12SL of at least 0.8. Selection: smallest CV median absolute difference, ties by the share within tolerance. The attempt-2 baselines are shown for comparison and are not eligible choices.

## QT interval

| Candidate | With a value | n | CV median abs diff (ms) | CV within tolerance | CV bias | CV slope on 12SL | |
|---|---|---|---|---|---|---|---|
| qt_thr05 | 6% | 70 | 94.8 | 17% | -2.7 | 0.25 |  |
| qt_thr10 | 34% | 373 | 61.2 | 25% | -0.2 | 0.46 |  |
| qt_thr20 | 73% | 804 | 16.3 | 85% | -0.1 | 0.63 |  |
| qt_tan | 98% | 1079 | 6.6 | 91% | +0.0 | 0.61 |  |
| qt_B_tan | 99% | 1093 | 8.5 | 90% | +0.0 | 0.58 | baseline (attempt 2) |

**No candidate is eligible (slope >= 0.8 and 90% with a value). Nothing is frozen for this parameter; the attempt stops here for it.**

## QRS duration

| Candidate | With a value | n | CV median abs diff (ms) | CV within tolerance | CV bias | CV slope on 12SL | |
|---|---|---|---|---|---|---|---|
| qrs_abs_3 | 99% | 1094 | 10.0 | 85% | +0.0 | 0.96 |  |
| qrs_abs_5 | 99% | 1094 | 6.1 | 89% | +0.0 | 0.81 |  |
| qrs_abs_10 | 99% | 1094 | 6.7 | 87% | +0.0 | 0.60 |  |
| qrs_euc_3 | 99% | 1094 | 10.8 | 84% | +0.0 | 0.92 |  |
| qrs_euc_5 | 99% | 1094 | 6.3 | 89% | -0.0 | 0.80 |  |
| qrs_euc_10 | 99% | 1094 | 6.3 | 88% | +0.0 | 0.62 |  |
| qrs_C1_3 | 99% | 1094 | 6.8 | 85% | -0.0 | 0.69 | baseline (attempt 2) |

**Frozen candidate: qrs_abs_5**; original-signal offsets {'c': -0.1663619744058501}

## Photo offsets (fitted once on 199 digitised clean pages: the 99 earlier held-out pages and F001-F100)

- QRS: qrs_abs_5, photo offsets {'c': -10.282828282828282}; in-sample median abs diff 4.7 ms, slope 0.99 (for the record only: this fit is NOT a test)
