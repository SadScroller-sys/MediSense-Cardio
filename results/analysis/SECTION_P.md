# Section P: traffic-light safeguard, evaluated once on real captures and own-phone photos

*Tool and rules frozen before this evaluation (docs/plan/analysis_plan_changes.md, 2026-11-10; one rule added before the evaluation). Trained only on the simulated new 100. Wilson 95% intervals treat images as independent, which is optimistic because the same recording appears up to 9 times (competition) or 2 times (own photos). Descriptive: fewer than 100 wrong readings on real captures.*

## Competition real captures C0-C8, images with an output (wrong heart rate > 5 bpm, cleaned)

| light | readings | wrong | wrong_rate | share_of_all_wrong | share_of_all_right |
|---|---|---|---|---|---|
| GREEN | 917 | 2 | 0.2% (0.1-0.8) | 4% | 79% |
| AMBER | 204 | 14 | 6.9% (4.1-11.2) | 30% | 16% |
| RED | 82 | 30 | 36.6% (27.0-47.4) | 65% | 4% |

## Competition real captures C1-C8 only, images with an output

| light | readings | wrong | wrong_rate | share_of_all_wrong | share_of_all_right |
|---|---|---|---|---|---|
| GREEN | 801 | 2 | 0.2% (0.1-0.9) | 5% | 78% |
| AMBER | 190 | 13 | 6.8% (4.0-11.4) | 32% | 17% |
| RED | 73 | 25 | 34.2% (24.4-45.7) | 62% | 5% |

## Competition real captures C0-C8, 'bad' = no output OR wrong (no-output images are RED by rule)

| light | readings | wrong | wrong_rate | share_of_all_wrong | share_of_all_right |
|---|---|---|---|---|---|
| GREEN | 917 | 2 | 0.2% (0.1-0.8) | 2% | 79% |
| AMBER | 204 | 14 | 6.9% (4.1-11.2) | 14% | 16% |
| RED | 139 | 87 | 62.6% (54.3-70.2) | 84% | 4% |

## Own phone, 60 photos: the 54 with an output (wrong > 5 bpm)

| light | readings | wrong | wrong_rate | share_of_all_wrong | share_of_all_right |
|---|---|---|---|---|---|
| GREEN | 22 | 0 | 0.0% (0.0-14.9) | 0% | 55% |
| AMBER | 15 | 1 | 6.7% (1.2-29.8) | 7% | 35% |
| RED | 17 | 13 | 76.5% (52.7-90.4) | 93% | 10% |

## Own phone, all 60 photos, 'bad' = no usable heart rate OR wrong

| light | readings | wrong | wrong_rate | share_of_all_wrong | share_of_all_right |
|---|---|---|---|---|---|
| GREEN | 22 | 0 | 0.0% (0.0-14.9) | 0% | 55% |
| AMBER | 15 | 1 | 6.7% (1.2-29.8) | 5% | 35% |
| RED | 23 | 19 | 82.6% (62.9-93.0) | 95% | 10% |

## Own phone, straight photos (30)

| light | readings | wrong | wrong_rate | share_of_all_wrong | share_of_all_right |
|---|---|---|---|---|---|
| GREEN | 15 | 0 | 0.0% (-0.0-20.4) | 0% | 60% |
| AMBER | 9 | 1 | 11.1% (2.0-43.5) | 20% | 32% |
| RED | 6 | 4 | 66.7% (30.0-90.3) | 80% | 8% |

## Own phone, angled photos (30)

| light | readings | wrong | wrong_rate | share_of_all_wrong | share_of_all_right |
|---|---|---|---|---|---|
| GREEN | 7 | 0 | 0.0% (0.0-35.4) | 0% | 47% |
| AMBER | 6 | 0 | 0.0% (0.0-39.0) | 0% | 40% |
| RED | 17 | 15 | 88.2% (65.7-96.7) | 100% | 13% |
