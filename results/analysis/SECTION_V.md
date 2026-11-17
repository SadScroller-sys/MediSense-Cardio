# Section V: QRS and QT, second attempt, tested ONCE on 100 fresh pages (EXPLORATORY)

Rules fixed before any code ran (`docs/plan/analysis_plan_changes.md`, 2026-11-14 night). The fresh pages were drawn and digitised before any result was looked at. The acceptance rules are unchanged and are the assistant's proposal, **not approved by the guide**. Frozen: QT = qt_B_tan, QRS = qrs_C1_3; (a) uses the calibration from the 1,000 development recordings, (b) the photo calibration fitted on the digitised pages of the earlier 99 held-out recordings. Difference = measured minus 12SL (ms).

## QT interval (rule: median abs diff <= 20 ms, 90% within 40 ms, |bias| <= 10 ms; at least 90% with a value)

| Measurement | With a value | rho with 12SL | Median abs diff (95% CI) | 90th pct | Bias (95% CI) | Within tolerance | Rule |
|---|---|---|---|---|---|---|---|
| (a) original signal in the photo windows | 100 of 100 (100%) | 0.78 | 7.0 (5.5 to 11.1) | 27.6 | +0.7 (-7.5 to +8.4) | 94% | **meets** |
| (b) digitised clean page | 99 of 100 (99%) | 0.76 | 8.8 (6.5 to 9.9) | 26.2 | -3.4 (-11.8 to +4.7) | 93% | **meets** |
| (c) digitised minus (a): what the photo adds | 99 | | 3.7 | 12.8 | -4.3 | | |

**QT interval validated on the fresh pages: YES** ((a) meets: True, (b) meets: True).

- (b) atrial fibrillation / flutter pages: n = 7, median abs diff 21.9 ms, bias -45.7 ms
- (b) other pages: n = 92, median abs diff 8.0 ms, bias -0.2 ms

## QRS duration (rule: median abs diff <= 10 ms, 90% within 20 ms, |bias| <= 5 ms; at least 90% with a value)

| Measurement | With a value | rho with 12SL | Median abs diff (95% CI) | 90th pct | Bias (95% CI) | Within tolerance | Rule |
|---|---|---|---|---|---|---|---|
| (a) original signal in the photo windows | 100 of 100 (100%) | 0.50 | 6.9 (5.2 to 9.3) | 25.2 | -3.1 (-6.7 to +0.1) | 86% | **does not meet** |
| (b) digitised clean page | 99 of 100 (99%) | 0.19 | 9.2 (5.8 to 12.4) | 37.5 | -4.8 (-9.9 to +0.2) | 74% | **does not meet** |
| (c) digitised minus (a): what the photo adds | 99 | | 7.3 | 28.3 | -1.7 | | |

**QRS duration validated on the fresh pages: NO** ((a) meets: False, (b) meets: False).

- (b) atrial fibrillation / flutter pages: n = 7, median abs diff 5.2 ms, bias -0.1 ms
- (b) other pages: n = 92, median abs diff 9.3 ms, bias -5.2 ms

## Limits

- Drawn pages digitised on this computer (not photos); the phone-photo confirmation follows separately. 12SL is an algorithm. One digitiser.
- The calibration was fitted on drawn pages; the fresh pages were never used to choose a method or a coefficient.
- Nothing is shown to patients unless the fresh test AND the phone-photo confirmation both say YES.
