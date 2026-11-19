# Risk pilot 3, stage 2 (descriptive): does the displayed range hold on pictures?

Rules written before the run: docs/plan/analysis_plan_changes.md (2026-11-18 night). Frozen pilot-3 models; same items and ages as pilot 2. NOT an outcome validation.

| Group | Age used for the picture | n | Spearman | Same group | Mean abs. difference | Range covers the clean value |
|---|---|---|---|---|---|---|
| drawn pages (dev: new100, F, G) | true age on both (typed or dataset age) | 300 | 0.97 | 92% | 3.6 points | 96% (plus or minus 10) |
| drawn pages (dev: new100, F, G) | age estimated from the picture (nothing typed) | 300 | 0.93 | 89% | 4.8 points | 93% (plus or minus 12) |
| drawn pages (dev: K) | true age on both (typed or dataset age) | 100 | 0.95 | 93% | 3.6 points | 97% (plus or minus 10) |
| drawn pages (dev: K) | age estimated from the picture (nothing typed) | 100 | 0.91 | 93% | 5.7 points | 94% (plus or minus 12) |
| real phone photos (dev, not gated) | true age on both (typed or dataset age) | 140 | 0.81 | 77% | 10.1 points | 67% (plus or minus 10) |
| real phone photos (dev, not gated) | age estimated from the picture (nothing typed) | 140 | 0.73 | 74% | 9.7 points | 72% (plus or minus 12) |
| simulated photos (dev) | true age on both (typed or dataset age) | 118 | 0.74 | 89% | 10.5 points | 61% (plus or minus 10) |
| simulated photos (dev) | age estimated from the picture (nothing typed) | 118 | 0.68 | 83% | 9.8 points | 70% (plus or minus 12) |
| drawn pages (fresh L) | true age on both (typed or dataset age) | 100 | 0.90 | 97% | 5.0 points | 89% (plus or minus 10) |
| drawn pages (fresh L) | age estimated from the picture (nothing typed) | 100 | 0.84 | 91% | 7.2 points | 88% (plus or minus 12) |
| drawn pages (fresh M) | true age on both (typed or dataset age) | 100 | 0.96 | 92% | 4.2 points | 91% (plus or minus 10) |
| drawn pages (fresh M) | age estimated from the picture (nothing typed) | 100 | 0.93 | 94% | 5.4 points | 94% (plus or minus 12) |
| simulated photos (fresh L) | true age on both (typed or dataset age) | 100 | 0.74 | 88% | 10.7 points | 66% (plus or minus 10) |
| simulated photos (fresh L) | age estimated from the picture (nothing typed) | 100 | 0.65 | 83% | 11.9 points | 67% (plus or minus 12) |
| simulated photos (fresh M) | true age on both (typed or dataset age) | 100 | 0.69 | 85% | 10.9 points | 65% (plus or minus 10) |
| simulated photos (fresh M) | age estimated from the picture (nothing typed) | 100 | 0.57 | 79% | 11.8 points | 69% (plus or minus 12) |
| REAL printed-paper STRAIGHT photos (H2, friend's phone) | true age on both (typed or dataset age) | 22 | 0.90 | 73% | 9.8 points | 68% (plus or minus 10) |
| REAL printed-paper STRAIGHT photos (H2, friend's phone) | age estimated from the picture (nothing typed) | 22 | 0.66 | 73% | 11.1 points | 73% (plus or minus 12) |

## Descriptive target: coverage at least 80% in every gated group

- true age on both (typed or dataset age): NOT met
- age estimated from the picture (nothing typed): NOT met