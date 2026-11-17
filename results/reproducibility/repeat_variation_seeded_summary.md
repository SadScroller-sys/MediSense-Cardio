# Seeded demo: repeat test (descriptive)

Same 10 demo photos, 2 runs each, seeded digitiser (seed 42), GPU. **Success criterion (fixed before the run): identical heart rate, light, PR, axis and score in both runs for every photo. Result: MET** (10 of 10 photos identical).

| Photo | Runs | Identical | HR (bpm) | Light | PR (ms) | Axis (deg) | Earlier unseeded HR mean | Earlier unseeded PR range (ms) | Seeded PR inside that range | Earlier unseeded axis values |
|---|---|---|---|---|---|---|---|---|---|---|
| example1_angled_photo_fixed_by_straightening.jpg | 2 | yes | 62.56 | GREEN | 164.5 | 49.2 | 62.56 | 0.0 | True | 49.2 |
| example2_straight_photo_green.jpg | 2 | yes | 55.03 | GREEN | 173.6 | 71.3 | 55.03 | 0.0 | True | 71.3 |
| example3_angled_photo_amber.jpg | 2 | yes | 106.28 | AMBER | 197.8 | 63.4 | 106.28 | 0.0 | True | 63.4 |
| example4_hard_page_red.jpg | 2 | yes | 65.90 | RED |  | -38.6 | 65.91 |  | None | -38.7, -38.6 |
| sample1_straight_clean.jpg | 2 | yes | 56.90 | GREEN | 171.9 | 19.2 | 56.88 | 0.0 | False | 19.2 |
| sample2_angled_left.jpg | 2 | yes | 74.55 | GREEN | 213.3 | -19.5 | 74.55 | 0.2 | True | -19.6, -19.5 |
| sample3_angled_from_below.jpg | 2 | yes | 77.64 | GREEN |  | 1.7 | 77.64 |  | None | 1.7 |
| sample4_dim_uneven_light.jpg | 2 | yes | 69.40 | GREEN | 173.7 | -38.9 | 69.40 | 22.3 | True | -38.9, -38.8 |
| sample5_far_and_small.jpg | 2 | yes | 62.36 | GREEN | 187.4 | 72.4 | 62.37 | 5.0 | True | 61.1, 72.4 |
| sample6_blurry_and_angled.jpg | 2 | yes | 61.52 | RED |  | 74.4 | 61.46 |  | None | 74.4 |

**Against the study values of the four example photos (Kaggle run, unseeded):**

| Photo | Study HR / light | Seeded demo HR / light | Difference (bpm) |
|---|---|---|---|
| example2_straight_photo_green.jpg | 55.03 / GREEN | 55.03 / GREEN | -0.00 |
| example1_angled_photo_fixed_by_straightening.jpg | 62.56 / GREEN | 62.56 / GREEN | -0.00 |
| example3_angled_photo_amber.jpg | 106.28 / AMBER | 106.28 / AMBER | -0.00 |
| example4_hard_page_red.jpg | 65.9 / RED | 65.90 / RED | -0.00 |

Reading: the seed removes the run-to-run variation; the seeded demo shows one fixed draw of the tie-break, which can differ slightly from the unseeded study values (a 1e-6 perturbation). The study results themselves were produced unseeded and are unchanged. Limits: 10 photos, 2 runs, one computer and one GPU.
