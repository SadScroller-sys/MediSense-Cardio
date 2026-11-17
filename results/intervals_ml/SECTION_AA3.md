# Section AA3: the DATASET-ONLY QRS/QT model (attempt 1, PTB-XL only), tested once on NEW data (EXPLORATORY; rules logged before)

Rules: `docs/plan/analysis_plan_changes.md`, 'Section AA'. The pass thresholds are the assistant's proposal, not approved by the guide. Reference = 12SL. Digitised sets use the digitised-input offset fitted on the development pages. Model: attempt 1 (trained on PTB-XL only, digitiser emulation as augmentation) with its frozen digitised-input offset; nothing about it was changed. Fresh data: L pages, L simulated photos, and the printed-paper photos of set H2 (the user's friend, another phone): PRIMARY = the straight full-resolution photos, SECONDARY = all full-resolution photos. User decisions of 2026-11-15 in analysis_plan_changes.md.

## T2 primary: fresh L pages

| Parameter | n | With value | Typical error (ms) | Within tolerance | Bias ms (95% interval) | Slope on 12SL (95% interval) | Tails (n, mean error ms) | AF pages (n, bias) | All rules met |
|---|---|---|---|---|---|---|---|---|---|
| QRS | 100 | 100% | 4.1 | 91% | +0.8 (-1.8 to +3.4) | 0.89 (0.79 to 0.99) | hi120: 32, -1.1 | 13, +5.7 | **YES** |
| QT | 100 | 100% | 9.9 | 87% | +12.4 (+3.4 to +22.9) | 0.79 (0.65 to 0.91) | hi450: 17, -1.4; lo350: 25, +18.5 | 13, +19.9 | **no** |
| QTc (Fridericia) | 100 | 99% | 10.2 | 90% | +14.3 (+5.2 to +25.1) | 0.87 (0.73 to 1.05) |  | 13, +29.8 | **no** |

## L simulated photos (a simulation)

| Parameter | n | With value | Typical error (ms) | Within tolerance | Bias ms (95% interval) | Slope on 12SL (95% interval) | Tails (n, mean error ms) | AF pages (n, bias) | All rules met |
|---|---|---|---|---|---|---|---|---|---|
| QRS | 100 | 100% | 7.5 | 72% | +11.0 (+5.9 to +16.4) | 0.81 (0.66 to 0.99) | hi120: 32, +5.5 | 13, +3.0 | **no** |
| QT | 100 | 100% | 17.8 | 67% | +31.0 (+20.2 to +41.8) | 0.71 (0.50 to 0.95) | hi450: 17, +17.5; lo350: 25, +51.1 | 13, +32.7 | **no** |
| QTc (Fridericia) | 100 | 98% | 16.7 | 71% | +32.7 (+21.2 to +45.8) | 0.56 (0.22 to 0.89) |  | 13, +49.3 | **no** |

## T3 primary: REAL printed-paper photos H2, STRAIGHT (friend's phone)

| Parameter | n | With value | Typical error (ms) | Within tolerance | Bias ms (95% interval) | Slope on 12SL (95% interval) | Tails (n, mean error ms) | AF pages (n, bias) | All rules met |
|---|---|---|---|---|---|---|---|---|---|
| QRS | 22 | 100% | 8.5 | 100% | +7.6 (+4.3 to +10.8) | 0.65 (0.39 to 0.96) |  | 0, +nan | **no** |
| QT | 22 | 100% | 14.9 | 77% | +9.9 (-4.4 to +23.7) | 0.54 (0.34 to 0.92) | hi450: 3, -20.2; lo350: 4, +38.3 | 0, +nan | **no** |
| QTc (Fridericia) | 22 | 100% | 17.6 | 82% | +12.8 (-2.3 to +27.0) | 0.51 (-0.05 to 1.03) |  | 0, +nan | **no** |

## H2 secondary: ALL full-resolution photos (straight and angled)

| Parameter | n | With value | Typical error (ms) | Within tolerance | Bias ms (95% interval) | Slope on 12SL (95% interval) | Tails (n, mean error ms) | AF pages (n, bias) | All rules met |
|---|---|---|---|---|---|---|---|---|---|
| QRS | 52 | 100% | 14.5 | 69% | +25.3 (+15.9 to +36.5) | 0.05 (-0.75 to 0.98) |  | 0, +nan | **no** |
| QT | 52 | 100% | 27.3 | 54% | +39.7 (+23.4 to +56.4) | 0.30 (0.03 to 0.57) | hi450: 6, -10.6; lo350: 10, +85.4 | 0, +nan | **no** |
| QTc (Fridericia) | 52 | 98% | 27.6 | 57% | +45.7 (+29.3 to +64.9) | 0.23 (-0.54 to 0.79) |  | 0, +nan | **no** |

## Verdict

| Parameter | Passed on L pages | Passed on L simulated | Simulation contradicts | Passed on REAL straight photos | Shown in the app | AF guard needed |
|---|---|---|---|---|---|---|
| QRS | True | False | True | False | **False** | False |
| QT | False | False | False | False | **False** | False |
| QTc (Fridericia) | False | False | False | False | **False** | True |

Rules (same numbers as the earlier attempts): QT typical error at most 20 ms, at least 90% within 40 ms, |bias| at most 10 ms, slope at least 0.8, tails (QT at least 450 or at most 350 ms) |mean error| at most 25 ms; QRS typical error at most 10 ms, at least 90% within 20 ms, |bias| at most 5 ms, slope at least 0.8, true QRS at least 120 ms |mean error| at most 20 ms; QTc (Fridericia, with the heart rate of the same photo) typical error at most 25 ms, at least 90% within 50 ms, |bias| at most 10 ms, slope at least 0.8. At least 90% with a value.
