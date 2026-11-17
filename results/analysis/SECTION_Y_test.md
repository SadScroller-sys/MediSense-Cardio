# Section Y: P-wave and T-wave amplitude (lead II), tested ONCE on 100 new sealed pages (EXPLORATORY)

Rules fixed before any code ran (`docs/plan/analysis_plan_changes.md`, 2026-11-14 afternoon). Proposal of the assistant, NOT approved by the guide. Difference = measured minus 12SL (mV). Rule: share with a value >= 90%; slope on 12SL >= 0.8; P: median abs <= 0.03, 90% within 0.06, |bias| <= 0.015, tails (ref P <= 0.05 and >= 0.20) within +-0.03; T: median abs <= 0.05, 90% within 0.10, |bias| <= 0.03, tails (ref T <= -0.10 and >= 0.50) within +-0.05, sign agreement >= 90% where |ref| >= 0.10. Disclosure: these pages were used before for QRS/QT only.

## P-wave amplitude, lead II (frozen: PA)

| Measurement | With a value | Median abs diff mV (95% CI) | 90th pct | Bias mV (95% CI) | Within tolerance | Slope on 12SL | Tails / sign | Rule |
|---|---|---|---|---|---|---|---|---|
| (a) original signal in the photo windows | 98 of 100 (98%) | 0.013 (0.009 to 0.016) | 0.043 | +0.001 (-0.006 to +0.007) | 94% | 1.04 | ref P <= 0.05: n=23, mean error -0.005; ref P >= 0.20: n=2, mean error +0.005 (too few) | **meets** |
| (b) digitised clean page | 98 of 100 (98%) | 0.012 (0.009 to 0.017) | 0.038 | -0.001 (-0.007 to +0.005) | 97% | 0.99 | ref P <= 0.05: n=23, mean error -0.001; ref P >= 0.20: n=2, mean error +0.003 (too few) | **meets** |

**P-wave amplitude, lead II validated on the new sealed pages: YES** ((a) meets: True, (b) meets: True)

- (b) atrial fibrillation / flutter pages: n = 9, median abs diff 0.033 mV, bias -0.002 mV
- (b) other pages: n = 91, median abs diff 0.011 mV, bias -0.000 mV

## T-wave amplitude, lead II

No candidate was frozen in development: not tested.

## Limits

- Drawn pages digitised on this computer (not photos); the phone photos follow separately. 12SL is an algorithm. One digitiser, not fully deterministic. The pages were used before for the QRS/QT test (disclosed in the plan).
- Nothing is shown to patients unless the page test AND the photo confirmation both say YES.
