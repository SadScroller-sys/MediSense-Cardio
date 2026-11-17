# Section Q: retrained networks A2 and B2, fresh set Q, tested once

NORMAL pictures flagged by at least one of the three tested patterns: drawn pages 0 of 40; simulated photos 1 of 39.

| Pair | Drawn pages: positives, AUROC (lower 95%), sens / spec | Simulated photos: positives, AUROC (lower 95%), sens / spec | Verdict |
|---|---|---|---|
| A2:LAFB | 42, 0.967 (0.913), 83 / 99 | 42, 0.754 (0.634), 43 / 99 | stays research-only: fails sensitivity 0.60 and specificity 0.90 on simulated photos |
| B2:AF | 47, 0.980 (0.959), 96 / 85 | 47, 0.836 (0.741), 79 / 89 | stays research-only: fails sensitivity 0.60 and specificity 0.90 on simulated photos |
| B2:LBBB | 40, 0.987 (0.971), 100 / 91 | 40, 0.841 (0.739), 72 / 92 | AVAILABLE: validated on dataset pictures (drawn pages and simulated photos) |
| A:LAFB | 42, 0.948 (0.892), 62 / 100 | 42, 0.758 (0.643), 43 / 96 | descriptive only (first network) |
| B:AF | 47, 0.975 (0.952), 96 / 88 | 47, 0.835 (0.733), 79 / 88 | descriptive only (first network) |
| B:LBBB | 40, 0.987 (0.974), 100 / 90 | 40, 0.809 (0.701), 75 / 84 | descriptive only (first network) |
