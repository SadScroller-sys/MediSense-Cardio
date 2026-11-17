# Held-out photo-quality detector test (Colab run, 2026-11-04)

Notebook: colab/MediSense_Cardio_Detector_Heldout.ipynb. 49 reliable recordings, 1,519 tests.
Whole recordings held out (5-fold x10); 95% interval = cluster bootstrap over recordings.
Numbers below were read off the Colab screen (the saved CSV on Drive has the same table).

| Target (bad = wrong or unreadable) | Bad readings | AUC 5 signals | 95% interval | Best single signal | AUC oracle severity |
|---|---|---|---|---|---|
| HR >5 bpm (PRIMARY) | 99 of 1519 | 0.607 | 0.49 to 0.82 | contrast_score 0.635 | 0.655 |
| HR >10 bpm | 36 of 1519 | 0.825 | 0.72 to 0.94 | blur_score 0.752 | 0.787 |
| QTc >60 ms | 235 of 1519 | 0.767 | 0.66 to 0.90 | blur_score 0.746 | 0.773 |
| QRS >100 ms | 181 of 1519 | 0.736 | 0.61 to 0.92 | blur_score 0.714 | 0.729 |
| HR >5, 2 hard recordings removed | 61 of 1457 | 0.735 | 0.64 to 0.88 | contrast_score 0.699 | 0.761 |

Random split (leaky) AUC 0.661 vs held-out 0.607 (primary target).

Unseen damage type (primary target, train on the other five):
blur 0.619 (21 bad), brightness 0.316 (9), gridcontrast 0.512 (11), jpeg 0.374 (9), resolution 0.749 (32), rotate 0.366 (15).

Gate on primary target: flag top 10% -> catch 37% of bad, wrongly flag 8%;
20% -> 46% / 18%; 30% -> 58% / 28%.

Not yet reported: whether the saved CSV/PNG on Drive were downloaded locally; the executed notebook was not downloaded.
