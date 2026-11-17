# Section X: QRS duration and QT, THIRD attempt, tested ONCE on 100 new sealed pages (EXPLORATORY)

Rules fixed before any code ran (`docs/plan/analysis_plan_changes.md`, 2026-11-14 night, third). **Stricter rule** (the assistant's proposal, not approved by the guide), for both (a) and (b): the error rule of attempt 2, at least 90% with a value, **slope of the measured value on 12SL >= 0.8** and **tail checks** (mean error within +-20 ms for a reference QT >= 450, QT <= 350 and QRS >= 120; at least 5 pages needed). Difference = measured minus 12SL (ms).

## QT interval

No candidate was frozen in development (none passed the slope filter): not tested.

## QRS duration (frozen: qrs_abs_5; rule: median abs diff <= 10 ms, 90% within 20 ms, |bias| <= 5 ms)

| Measurement | With a value | Median abs diff (95% CI) | 90th pct | Bias (95% CI) | Within tolerance | Slope on 12SL | Tails | Rule |
|---|---|---|---|---|---|---|---|---|
| (a) original signal in the photo windows | 100 of 100 (100%) | 6.2 (4.2 to 9.0) | 17.9 | +3.2 (-1.9 to +9.8) | 93% | 0.79 | ref QRS >= 120: n=11, mean error -2.3 | **does not meet** |
| (b) digitised clean page | 100 of 100 (100%) | 5.5 (4.3 to 7.3) | 14.4 | +3.0 (-1.9 to +9.4) | 93% | 0.87 | ref QRS >= 120: n=11, mean error +3.1 | **meets** |

**QRS duration validated on the new sealed pages: NO** ((a) meets: False, (b) meets: True).

- (b) atrial fibrillation / flutter pages: n = 9, median abs diff 5.3 ms, bias -0.5 ms
- (b) other pages: n = 91, median abs diff 5.7 ms, bias +3.4 ms

## Limits

- Drawn pages digitised on this computer (not photos); the new phone photos follow separately. 12SL is an algorithm. One digitiser; the digitiser is not fully deterministic.
- Nothing is shown to patients unless the new-page test AND the new-phone-photo confirmation both say YES; QT and QRS duration would also get the atrial-fibrillation guard (hidden when rr_cv > 0.12).
