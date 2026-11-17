# Section AA: learned QRS duration and QT/QTc, test once (EXPLORATORY; rules logged before any code ran)

Rules: `docs/plan/analysis_plan_changes.md`, 'Section AA'. The pass thresholds are the assistant's proposal, not approved by the guide. Reference = 12SL. Digitised sets use the digitised-input offset fitted on the development pages. T2b (G pages) and T3 (phone photos) were used before for other methods; the new model was never tuned on them.

## T1 fold 10 originals (benchmark)

| Parameter | n | With value | Typical error (ms) | Within tolerance | Bias ms (95% interval) | Slope on 12SL (95% interval) | Tails (n, mean error ms) | AF pages (n, bias) | All rules met |
|---|---|---|---|---|---|---|---|---|---|
| QRS | 2114 | 100% | 3.8 | 99% | +0.2 (-0.1 to +0.5) | 0.93 (0.90 to 0.96) | hi120: 183, -0.7 | 147, +0.5 | **YES** |
| QT | 2114 | 100% | 6.7 | 98% | -0.4 (-1.0 to +0.2) | 0.88 (0.84 to 0.91) | hi450: 168, -10.9; lo350: 227, +6.9 | 147, +2.3 | **YES** |
| QTc (Fridericia) | 2114 | 100% | 7.1 | 98% | -0.1 (-0.8 to +0.6) | 0.73 (0.69 to 0.77) |  | 147, +3.0 | **no** |

## T2 primary: sealed K pages

| Parameter | n | With value | Typical error (ms) | Within tolerance | Bias ms (95% interval) | Slope on 12SL (95% interval) | Tails (n, mean error ms) | AF pages (n, bias) | All rules met |
|---|---|---|---|---|---|---|---|---|---|
| QRS | 100 | 100% | 6.4 | 92% | -2.1 (-4.1 to +0.2) | 0.92 (0.83 to 1.00) | hi120: 33, -3.6 | 10, -4.2 | **YES** |
| QT | 100 | 100% | 13.1 | 87% | -2.8 (-8.2 to +3.2) | 0.83 (0.69 to 0.98) | hi450: 23, -13.5; lo350: 15, +6.0 | 10, +2.5 | **no** |
| QTc (Fridericia) | 100 | 98% | 14.6 | 90% | -2.0 (-8.2 to +4.7) | 0.70 (0.56 to 0.86) |  | 10, +4.6 | **no** |

## T2b: sealed G pages

| Parameter | n | With value | Typical error (ms) | Within tolerance | Bias ms (95% interval) | Slope on 12SL (95% interval) | Tails (n, mean error ms) | AF pages (n, bias) | All rules met |
|---|---|---|---|---|---|---|---|---|---|
| QRS | 100 | 100% | 4.2 | 96% | -1.3 (-2.7 to +0.4) | 0.87 (0.77 to 0.93) | hi120: 11, -7.2 | 9, +4.2 | **YES** |
| QT | 100 | 100% | 9.5 | 92% | -1.1 (-5.3 to +4.1) | 0.87 (0.77 to 0.98) | hi450: 9, -22.1; lo350: 11, +4.2 | 9, +6.5 | **YES** |
| QTc (Fridericia) | 100 | 100% | 9.7 | 94% | -0.2 (-5.5 to +5.5) | 0.77 (0.58 to 1.00) |  | 9, +8.3 | **no** |

## T3: straightened phone photos

| Parameter | n | With value | Typical error (ms) | Within tolerance | Bias ms (95% interval) | Slope on 12SL (95% interval) | Tails (n, mean error ms) | AF pages (n, bias) | All rules met |
|---|---|---|---|---|---|---|---|---|---|
| QRS | 140 | 100% | 4.7 | 91% | +3.3 (+0.2 to +5.9) | 0.65 (0.56 to 0.81) | hi120: 14, -14.1 | 12, +5.8 | **no** |
| QT | 140 | 100% | 13.1 | 75% | +11.2 (+1.5 to +20.8) | 0.50 (0.27 to 0.81) | hi450: 12, -44.6; lo350: 14, +43.3 | 12, +27.6 | **no** |
| QTc (Fridericia) | 140 | 100% | 12.9 | 78% | +13.9 (+3.3 to +24.6) | 0.23 (0.05 to 0.52) |  | 12, +31.8 | **no** |

## Verdict

| Parameter | Passed on K | Passed on G | G contradicts | Passed on phone photos | Shown in the app | AF guard needed |
|---|---|---|---|---|---|---|
| QRS | True | True | False | False | **False** | False |
| QT | False | True | False | False | **False** | False |
| QTc (Fridericia) | False | False | False | False | **False** | False |

Rules (same numbers as the earlier attempts): QT typical error at most 20 ms, at least 90% within 40 ms, |bias| at most 10 ms, slope at least 0.8, tails (QT at least 450 or at most 350 ms) |mean error| at most 25 ms; QRS typical error at most 10 ms, at least 90% within 20 ms, |bias| at most 5 ms, slope at least 0.8, true QRS at least 120 ms |mean error| at most 20 ms; QTc (Fridericia, with the heart rate of the same photo) typical error at most 25 ms, at least 90% within 50 ms, |bias| at most 10 ms, slope at least 0.8. At least 90% with a value.
