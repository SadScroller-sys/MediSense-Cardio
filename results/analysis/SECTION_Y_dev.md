# Section Y development (1,100 development recordings, original signals, page-layout windows)

Offset-only calibration refitted on the training folds. CV = 5-fold by recording. Eligible = a value for at least 90% AND a cross-validated slope on 12SL of at least 0.8. Selection: smallest CV median absolute difference (mV).

## P-wave amplitude, lead II

| Candidate | With a value | n | CV median abs diff (mV) | CV within tolerance | CV bias | CV slope on 12SL | sign agreement (|ref| >= 0.10) |
|---|---|---|---|---|---|---|---|
| PA | 97% | 1064 | 0.012 | 93% | +0.000 | 0.97 | 98% |
| PB | 97% | 1064 | 0.012 | 93% | +0.000 | 0.93 | 97% |
| PC | 97% | 1070 | 0.017 | 92% | -0.000 | 0.74 | 98% |

**Frozen candidate: PA**; original-signal offset -0.0235 mV

## T-wave amplitude, lead II

| Candidate | With a value | n | CV median abs diff (mV) | CV within tolerance | CV bias | CV slope on 12SL | sign agreement (|ref| >= 0.10) |
|---|---|---|---|---|---|---|---|
| TA | 97% | 1064 | 0.015 | 91% | -0.000 | 0.68 | 97% |
| TB | 97% | 1064 | 0.017 | 91% | +0.000 | 0.66 | 97% |
| TC | 99% | 1084 | 0.034 | 77% | +0.000 | 0.72 | 94% |

**No candidate is eligible (slope >= 0.8 and 90% with a value). Nothing is frozen for this measurand; it stops here.**

## Photo offsets (fitted once on 199 digitised clean pages: the 99 earlier held-out pages and F001-F100)

- P: PA, photo offset -0.0177 mV; in-sample median abs diff 0.015 mV, slope 1.13 (for the record only: NOT a test)
