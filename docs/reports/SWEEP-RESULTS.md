# Sweep results — first analysis (2026-09-20)

Source data: `results_clean.csv` (1,550 tests = 50 PTB-XL records × 31 versions). Analysis notebooks:
`colab/MediSense_Cardio_Analysis_Part1.ipynb`, `…Part1b.ipynb`, `…Part2.ipynb`. All outputs are on Drive at
`MyDrive/MediSense-Cardio-Study/`.

## What was run

- **Sample:** 50 records (25 normal / 25 abnormal by PTB-XL label; classes NORM 24, HYP 9, STTC 7, CD 5, MI 4),
  a fixed seed-42 subset of a 500-record pool. Scope was cut from 500 → 150 → 50 records to fit the free GPU
  quota and the 2026-09-28 deadline. The cut was made before seeing any result.
- **Versions per record:** 1 clean + 6 damage types × 5 levels = 31.
  Damage types: blur (Gaussian kernel 3/7/11/15/21), rotation (2/5/8/12/16°), JPEG quality (50/30/15/8/3),
  resolution (×0.75/0.5/0.35/0.25/0.15 then back up), brightness (linear shadow 15–75 %), grid contrast
  (fade toward mean 15–75 %). Rendered with ecg-image-kit, read back with Open-ECG-Digitizer (T4 GPU).
- **Measured so far:** lead II heart rate vs ground truth (neurokit2 R-peak rate). Not yet measured: PR, QRS,
  QT, diagnosis-level correctness, no-reference quality score.

## Data cleaning

| Step | Count |
|---|---|
| Rows in raw `results.csv` | 1,688 |
| Stray rows from earlier scope changes (removed) | 138 |
| Duplicate tests | 0 |
| Tests kept | **1,550 / 1,550** (all present) |

## Records that fail most of the time (4 of them even on the clean picture)

163 of 1,550 tests (10.5 %) gave no readable heart rate; 154 of those had no digitized signal at all.

| Record | Class | Unreadable / 31 |
|---|---|---|
| 00102 | CD (abnormal) | 31 (its ground-truth heart rate is also unmeasurable) |
| 08150 | NORM | 30 |
| 13316 | NORM | 29 |
| 00053 | NORM | 25 |
| 18151 | NORM | 21 |
| 19059 | NORM | 18 |

37 records never fail, 7 fail once or twice. Failures are tied to particular pictures, not to the damage. These 6
are **reported separately**; all damage curves below use the **44 reliable records** (≤ 20 % failures).

## Heart-rate error vs damage (44 reliable records; mean / median bpm; clean = 0.52 / 0.13)

| Damage | Level 1 | 2 | 3 | 4 | 5 | Reading |
|---|---|---|---|---|---|---|
| Blur | 0.41 / 0.12 | 0.78 / 0.12 | 0.70 / 0.15 | 2.29 / 0.63 | 2.90 / 1.64 | rises with level |
| Resolution | 0.37 / 0.12 | 0.37 / 0.11 | 0.75 / 0.15 | 0.87 / 0.20 | **7.72 / 2.36** | jumps at level 5 (41 % of readings > 5 bpm off) |
| Rotation | 0.53 | 0.33 | 0.55 | 0.80 | 0.96 | small error, but **silent drops** at level 5 |
| JPEG | 0.84 | 0.20 | 0.40 | 0.69 | 0.36 | no effect |
| Grid contrast | 0.70 | 0.50 | 0.53 | 0.53 | 0.50 | no effect |
| Brightness/shadow | 0.77 | 1.18 | 0.76 | 0.38 | 0.39 | noisy, no trend |

## Patient-facing outcome (heart-rate version of the T3 measure)

Rule: told slow (<60), normal (60–100) or fast (>100 bpm) from the digitized rate vs the ground-truth category.
Outcomes: correct · false alarm · **false reassurance** (told normal, truth abnormal) · wrong-abnormal · silent drop.

- **Clean baseline:** 44/44 correct.
- Only **9 reliable records** have an abnormal heart rate in the truth (6 slow, 3 fast + record 08150 fast but
  unreliable), so only they can produce false reassurance.
- **9 false-reassurance events in total; 6 are real** (digitized rate off by > 10 bpm), **all at level 5**:
  - resolution 5: 4 of 9 abnormal-rate records told "normal" (readings off by 14–33 bpm)
  - blur 5: 2 of 9 (off by ~15 bpm)
- **3 are threshold artefacts** (e.g. 10811: 59.7 read as 60.0; 16637 at JPEG 4: 57.5 read as 60.8) and should
  not be counted as clinically meaningful.
- **Rotation level 5:** 4 of 44 pictures unreadable (9 %) — a *silent drop*, not a wrong answer.
- **False alarms:** 4 in total. JPEG, grid contrast, brightness: essentially none.

Pooled by severity with Wilson 95 % intervals: `t3_hr_pooled.csv`. Intervals are wide (n = 9 at risk).

## Paper figures (made 2026-09-20)

Notebook `colab/MediSense_Cardio_Analysis_Part3_figures.ipynb` writes PNG (300 dpi) + PDF to
`MyDrive/MediSense-Cardio-Study/figures/` (IEEE column sizes, single hue, numbers printed in the heatmap cells):

| File | Shows |
|---|---|
| `fig1_hr_error_by_damage` | Median and 90th-percentile heart-rate error vs damage level, one panel per damage type (44 reliable records) |
| `fig2_false_reassurance_and_silent_drops` | Left: records wrongly told "normal" (reading off > 10 bpm) out of the 9 with a truly slow/fast rate. Right: unreadable pictures out of 44 |
| `fig3_unreadable_records` | The 12 records that fail most often (6 fail in most versions) |

Figure 2 values (real): wrongly told "normal" = blur level 5: 2/9, low resolution level 5: 4/9, all other cells 0/9;
3 borderline flips excluded. Silent drops: rotation level 3/4/5 = 1/1/4 of 44, plus one each for blur 5, JPEG 1,
lighting 2.

## Limitations that must appear in the paper

1. Heart rate only. Diagnosis-level false reassurance (e.g. a missed MI) is **not** measured; the digitized
   signals were not stored, so PR/QRS/QT need a re-run.
2. Only 9 reliable records with an abnormal rate → wide uncertainty; describe as a pattern, not a rate.
3. 6 of 50 records (12 %) are unreadable in most versions, and 4 of them (00102, 08150, 13316, 19059) even on the
   clean picture; excluded from damage curves, reported separately.
4. Damage is simulated (OpenCV post-processing on rendered pages), not real phone photos.
5. 50 records, one digitizer, one rendering tool, one lead (II).
6. The sample cut (500 → 50) was made for time/quota reasons; stated, not hidden.

## Reproducing / where everything is

- Raw + cleaned results, per-record failures and summaries: `MyDrive/MediSense-Cardio-Study/` (owner
  salava.niharsaiadithya@gmail.com; shared as Editor with niharsaiaditya@gmail.com). Key files: `results.csv`,
  `results_clean.csv`, `per_record_failures.csv`, `summary_by_axis_level.csv`,
  `summary_reliable_records.csv`, `t3_hr_outcomes.csv`, `t3_hr_by_axis_level.csv`, `t3_hr_pooled.csv`.
- To resume or extend the sweep: upload `colab/MediSense_Cardio_FullSweep_v1.ipynb`, set the runtime to **T4 GPU**,
  Run all, and check the log prints `Using device: cuda`. It resumes from `results.csv` automatically.
- The notebooks are generated by scripts in `scripts/notebook_builders/` (`build_fullsweep_notebook.py`,
  `build_analysis_*.py`, `build_harness_notebook.py`); edit those and rebuild, don't edit notebooks by hand.
- Lessons: never hand-edit Colab cells; check `Using device:`; verify saves by read-back (built in); never let
  two runs write the same `results.csv`.
