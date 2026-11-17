# Repeat variation of the demo pipeline (descriptive)
Same 10 demo photos, 3 runs each, nothing changed between runs (GPU, `demo/pipeline.py`, frozen PR and axis methods). Raw rows: `repeat_variation_runs.csv`. Rule: descriptive, no pass/fail (written in `scripts/analysis/repeat_variation_demo.py` before the run).

| Photo | Runs | Heart-rate range (bpm) | Light(s) | PR range (ms) | PR value in some runs only | Axis range (deg) | Traffic-light score range |
|---|---|---|---|---|---|---|---|
| example1_angled_photo_fixed_by_straightening.jpg | 3 | 0.0 | GREEN | 0.0 (3 values) | no | 0.0 | 0.0 |
| example2_straight_photo_green.jpg | 3 | 0.0 | GREEN | 0.0 (3 values) | no | 0.0 | 0.0 |
| example3_angled_photo_amber.jpg | 3 | 0.0 | AMBER | 0.0 (3 values) | no | 0.0 | 0.0 |
| example4_hard_page_red.jpg | 3 | 0.02 | RED | nan (0 values) | no | 0.1 | 0.0006 |
| sample1_straight_clean.jpg | 3 | 0.0 | GREEN | 0.0 (3 values) | no | 0.0 | 0.0 |
| sample2_angled_left.jpg | 3 | 0.0 | GREEN | 0.2 (3 values) | no | 0.1 | 0.0017 |
| sample3_angled_from_below.jpg | 3 | 0.0 | GREEN | nan (0 values) | no | 0.0 | 0.0 |
| sample4_dim_uneven_light.jpg | 3 | 0.01 | GREEN | 22.3 (3 values) | no | 0.1 | 0.0011 |
| sample5_far_and_small.jpg | 3 | 0.01 | GREEN | 5.0 (3 values) | no | 11.3 | 0.0037 |
| sample6_blurry_and_angled.jpg | 3 | 0.08 | RED | nan (0 values) | no | 0.0 | 0.0015 |

**Overall**

- Heart rate: largest range 0.08 bpm, median range 0.00 bpm (the 5 bpm 'wrong' limit is 62 times the largest range).
- Traffic light changed between runs of the same photo on 0 of 10 photos.
- PR (photos with at least 2 values): largest range 22.3 ms, median 0.0 ms. A PR value appeared in some runs but not in others for 0 photos.
- Axis: largest range 11.3 degrees, median 0.0 degrees.

Limits: 10 photos from the demo folders (simulated and real phone photos), a handful of runs each, one computer and one GPU. This measures the pipeline's own repeat variation, not photo-to-photo variation. Whether the variation comes from the digitiser's random tie-break or from GPU arithmetic was not separated.
