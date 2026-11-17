# QTc false reassurance: Bazett vs Fridericia (rerun 2026-11-04)

Script: scripts/analysis/qtc_fridericia_rerun.py. Input: results/v2_intervals/results_v2.csv. Nothing saved was changed.
Same rules as analyze_v2_intervals.py: 49 reliable records, a "real" event needs the record to be correct on its own
clean image and the digitised QTc under-read by more than the tolerance. Thresholds QTc >= 450 ms (male), >= 460 ms (female).
Check: Bazett recomputed from QT and HR matches the stored QTc column (max diff 0.22 ms) and the stored abnormal flags (100%).

Counts use the 30 damaged versions per record (clean image excluded); the paper's 589 tests include the 19 clean rows (19 x 31).

| Formula | Tolerance | Truly prolonged records | Usable at-risk records | At-risk tests | Real events | Records with events | Rate (Wilson 95%) |
|---|---|---|---|---|---|---|---|
| Bazett | none | 21 | 19 | 570 | 7 | 4 | 1.2% (0.6 to 2.5) |
| Bazett | 10 ms | 21 | 19 | 570 | 6 | 4 | 1.05% (0.5 to 2.3) |
| Bazett | 20 ms | 21 | 19 | 570 | 6 | 4 | 1.05% (0.5 to 2.3) |
| Fridericia | none | 16 | 15 | 450 | 3 | 3 | 0.67% (0.2 to 1.9) |
| Fridericia | 10 ms | 16 | 15 | 450 | 2 | 2 | 0.44% (0.1 to 1.6) |
| Fridericia | 20 ms | 16 | 15 | 450 | 2 | 2 | 0.44% (0.1 to 1.6) |

Findings
- The 6-event Bazett result reproduces exactly (10 ms tolerance).
- With Fridericia, 6 of the 21 "prolonged" records become normal (1 goes the other way), leaving 16, and real events
  fall from 6 to 2 (from 4 records to 2). The intervals overlap, so this is not a significant difference, but the
  direction matches the literature: Bazett over-calls prolonged QTc at higher heart rates.
- The 10 ms and 20 ms tolerances give the same counts, so the result is not sensitive to the tolerance in that range.
- Where the events sit: Bazett: resolution 2, rotate 2, blur 1, brightness 1 (record 14236_lr alone has 3).
  Fridericia: jpeg 1, resolution 1. Two or six events cannot rank damage types.
- Clean-image QTc error is about the same with either formula: median 20.1 ms (Bazett) vs 18.8 ms (Fridericia),
  95th percentile 52.2 vs 50.3 ms.

What this means
- QTc false reassurance is rare in this sample under either formula, and the Bazett figure is probably an over-count.
- Do not quote the damage-type breakdown of QTc events as a finding; there are too few.
- If the paper keeps Bazett as the main formula, add Fridericia as a sensitivity result (2 events vs 6).
- A QTc cut-off of 450/460 ms is itself a convention; the Vandenberk study found the Bazett healthy upper limit
  (472 ms men, 482 ms women) is above it.
