# Section S: PR, QRS and QT on the digitised signals, against 12SL (EXPLORATORY, added after the freeze)

Rules and the acceptance rule were written before the run (`docs/plan/analysis_plan_changes.md`, 2026-11-13). The acceptance rule was proposed by the assistant and is **not approved by the guide**. Reference = PTB-XL+ 12SL global value. Difference = measured minus 12SL (ms). Frozen methods (lead II only, amended before any result): QT cwt, PR dwt, QRS dwt; beats with a gap or outside the page dropped; median over beats, at least 3 beats. Tolerance rule (median absolute difference / share within / |bias|): QT and PR 20 ms / 90% within 40 ms / 10 ms; QRS 10 ms / 90% within 20 ms / 5 ms.

Primary set: clean pages of the new 100 recordings, 21205 excluded (unreliable): 99 recordings.

## QT (rule: median |diff| <= 20 ms, 90% within 40 ms, |bias| <= 10 ms)

| Measurement | Recordings with a value | rho with 12SL | Median abs diff (95% CI) | 90th pct abs diff | Bias (95% CI) | Within tolerance | Rule |
|---|---|---|---|---|---|---|---|
| (a) same method on the original lead II (500 Hz) | 69 of 99 | 0.55 | 36.0 (29.0 to 46.0) | 157.2 | +45.6 (+23.6 to +71.3) | 55% | **does not meet** |
| (b) digitised clean page | 70 of 99 | 0.40 | 26.0 (16.2 to 44.0) | 144.2 | -0.0 (-19.8 to +20.0) | 54% | **does not meet** |
| (c) digitised minus (a): what the photo adds | 67 | | 12.0 | 138.6 | -47.8 | | |

Share of recordings with a digitised value: 71%. **Validated under the pre-set rule: NO** ((a) meets: False, (b) meets: False, value share at least 90%: False).

## PR (rule: median |diff| <= 20 ms, 90% within 40 ms, |bias| <= 10 ms)

| Measurement | Recordings with a value | rho with 12SL | Median abs diff (95% CI) | 90th pct abs diff | Bias (95% CI) | Within tolerance | Rule |
|---|---|---|---|---|---|---|---|
| (a) same method on the original lead II (500 Hz) | 99 of 99 | 0.21 | 78.0 (65.0 to 82.0) | 111.6 | -66.3 (-75.6 to -57.5) | 25% | **does not meet** |
| (b) digitised clean page | 99 of 99 | 0.20 | 78.5 (72.0 to 88.0) | 117.4 | -69.4 (-78.7 to -61.0) | 24% | **does not meet** |
| (c) digitised minus (a): what the photo adds | 99 | | 4.0 | 33.5 | -1.7 | | |

Share of recordings with a digitised value: 100%. **Validated under the pre-set rule: NO** ((a) meets: False, (b) meets: False, value share at least 90%: True).

## QRS (rule: median |diff| <= 10 ms, 90% within 20 ms, |bias| <= 5 ms)

| Measurement | Recordings with a value | rho with 12SL | Median abs diff (95% CI) | 90th pct abs diff | Bias (95% CI) | Within tolerance | Rule |
|---|---|---|---|---|---|---|---|
| (a) same method on the original lead II (500 Hz) | 98 of 99 | 0.19 | 84.5 (72.0 to 94.0) | 158.6 | +91.4 (+80.7 to +103.8) | 9% | **does not meet** |
| (b) digitised clean page | 98 of 99 | 0.18 | 98.0 (89.0 to 107.5) | 164.8 | +103.4 (+93.4 to +115.1) | 1% | **does not meet** |
| (c) digitised minus (a): what the photo adds | 98 | | 8.0 | 48.6 | +12.1 | | |

Share of recordings with a digitised value: 99%. **Validated under the pre-set rule: NO** ((a) meets: False, (b) meets: False, value share at least 90%: True).

## Summary

| Parameter | (a) original lead II | (b) digitised clean page | Validated |
|---|---|---|---|
| QT | does not meet | does not meet | NO |
| PR | does not meet | does not meet | NO |
| QRS | does not meet | does not meet | NO |

## Secondary (descriptive): digitised, all versions, by damage type and level; and GREEN images only

GREEN here = safeguard score below the AMBER threshold (0.2585) and at least 3 beats; the out-of-range guard is not applied (as written in the rules). Bias and median absolute difference in ms.

| Group | Images | QT median abs / bias | PR median abs / bias | QRS median abs / bias | QT value share |
|---|---|---|---|---|---|
| all versions | 1287 | 32 / +8 | 80 / -71 | 105 / +119 | 60% |
| GREEN images only | 903 | 23 / +14 | 80 / -72 | 101 / +115 | 60% |
| clean | 99 | 26 / -0 | 78 / -69 | 98 / +103 | 71% |
| blur 3 | 99 | 46 / +34 | 85 / -82 | 122 / +146 | 39% |
| blur 5 | 99 | 75 / +78 | 79 / -73 | 182 / +206 | 30% |
| rotate 3 | 99 | 28 / +2 | 78 / -71 | 99 / +107 | 69% |
| rotate 5 | 99 | 23 / +4 | 80 / -71 | 96 / +99 | 51% |
| jpeg 3 | 99 | 28 / -3 | 78 / -67 | 97 / +105 | 69% |
| jpeg 5 | 99 | 30 / +4 | 80 / -70 | 98 / +104 | 69% |
| resolution 3 | 99 | 36 / +18 | 81 / -74 | 103 / +107 | 63% |
| resolution 5 | 99 | 66 / +37 | 82 / -75 | 146 / +161 | 38% |
| brightness 3 | 99 | 26 / -3 | 80 / -62 | 98 / +99 | 69% |
| brightness 5 | 99 | 24 / +2 | 78 / -69 | 97 / +104 | 69% |
| gridcontrast 3 | 99 | 25 / -3 | 78 / -70 | 98 / +103 | 71% |
| gridcontrast 5 | 99 | 26 / -5 | 78 / -69 | 98 / +104 | 70% |

## Limits

- 12SL is an algorithm, not an expert annotation; 12SL and Glasgow differ by 4 to 6.5 ms for QT, so tolerances below that are not meaningful.
- One digitiser, simulated pages, 99 recordings in the primary set; lead II only (the other leads cover only 2.5 s of a page, too short for the wavelet detector), which is weaker than the median-of-12-leads method on the original signal (QT rho 0.56 instead of 0.66).
- The acceptance thresholds are the assistant's proposal. A different threshold could change a verdict; the table above gives the raw errors so a reader can apply their own.
- QTc is not evaluated. Nothing from this section is shown to patients unless the Validated column says YES.