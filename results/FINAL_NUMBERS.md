# FINAL NUMBERS (frozen 2026-11-11)

This is the one place the report, the poster and the slides take their numbers from. If a number is not here, it is not quoted. After this date a number changes only if a mistake is found; the change is then written in `docs/plan/PROGRESS-LOG.md` and in this file's "Changes after the freeze" list at the end.

**How each result is labelled**
- **PRE-SPECIFIED** = the rule and the pass/fail wording were written before the result existed (`docs/plan/MASTER_PLAN.md`, `analysis_plan_150.md`, or a rule logged in `analysis_plan_changes.md` before the data). These are the strongest results.
- **EXPLORATORY** = the idea came after we had seen earlier data. The rule may still have been logged before the run, but we do not use the word "proved" or "confirmed" for these.
- **POST HOC** = done after seeing a result, to understand it.
- Source = the section report in `results/analysis/` (SECTION_X.md). Numbers marked "rechecked" were recomputed from the raw files by a second script (`scripts/analysis/final_numbers_recompute.py` -> `results/analysis/FINAL_RECHECK.md`, 36 numbers, all match; see section 7).

**Words used everywhere:** *wrong* = a reading exists and its heart rate (HR) is more than 5 bpm from the true HR. *No usable HR* = fewer than 3 beats in lead II. *Bad* = wrong or no usable HR. Heart rate is the cleaned measure (NeuroKit filter, then beats) unless the table says "original measure". Full formulae: `docs/reports/METHODS_AND_FORMULAE.md`.

---

## 1. What was studied (counts)

| Item | Number | Source |
|---|---|---|
| Recordings in the damage sweeps | 150 (first 50 = development set; new 100 = held-out replication) | Section C |
| Reliable recordings used in tables | 49 + 99 = 148 (15192_lr and 21205_lr excluded: more than 20% of versions without output) | Section C |
| Versions per recording | 31 (first 50); 13 (new 100); 13 shared | Section C |
| Reference-uncertain recordings (100 Hz and 500 Hz reference differ by more than 5 bpm) | 20 of 150 (8 + 12) = 13% | `results/extension/reference_check_150.csv` (rechecked by count) |
| Real captures (competition images) | 140 recordings x 9 capture types = 1,260 images; 1,201 have a reading | Sections H, L |
| Own-phone set 1 | 30 pages, 60 photos | Section O |
| Own-phone set 2 (confirmation) | 20 new pages, 40 photos | Section Q2 |
| Digitiser | Open-ECG-Digitizer, commit 97a15087, unchanged | METHODS section 4 |

---

## 2. PRE-SPECIFIED results (simulated damage, computer-drawn pages)

### 2.1 Claim C1: which damage makes the heart rate wrong (Section C) - SUPPORTED
Verdict rule written before the new 100 existed; it must hold with and without reference-uncertain recordings. It does (`ALL_MET` in all three populations).

New 100, level 5 (worst), wrong HR > 5 bpm (Wilson 95%) - rechecked:

| Damage | Wrong HR | Interval | No output |
|---|---|---|---|
| Clean page | 3/99 = 3.0% | 1.0-8.5% | 0 |
| Resolution (shrink to 15%) | **47/99 = 47.5%** | 37.9-57.2% | 0 |
| Blur (21 x 21) | **17/99 = 17.2%** | 11.0-25.8% | 1/99 |
| Rotation (16 degrees) | 0/99 = 0.0% | 0.0-3.7% | **19/99 = 19.2%** |
| JPEG (quality 3) | 0/99 = 0.0% | 0.0-3.7% | 0 |
| Brightness ramp (0.75) | 1/99 = 1.0% | 0.2-5.5% | 1/99 |
| Faded grid (0.75) | 3/99 = 3.0% | 1.0-8.5% | 0 |

- All 150 together (148 reliable), level 5: resolution 68/148 = 45.9% (38.1-54.0), blur 25/148 = 16.9% (11.7-23.7) - rechecked.
- First 50 (development): resolution 21/49 = 42.9%, blur 8/49 = 16.3% - rechecked.
- Without reference-uncertain recordings (new 100): resolution 43.7%, blur 14.9%, others under 3%.
- Level 3 (medium) damage: all types 1-6%, close to the clean page (3.0%).
- **Plain reading:** in the simulation, only very low resolution and heavy blur make the heart rate wrong. Strong rotation does not make it wrong; it makes the digitiser give no answer for about one page in five.

Paired test against the same recording's clean page (first 150, Wilcoxon, Holm): resolution 5 median error 3.8 bpm vs 0.09 (p_holm 1e-24); blur 5 1.5 vs 0.09 (5e-23). JPEG 5, brightness 5, faded grid: no difference.

### 2.2 Claim C2: failures follow the recording (descriptive)
- Wrong HR on the clean page: 4.1% overall, **0.0% among recordings with no PTB-XL quality flag** in the first 50; bad readings over all versions: recordings with a PTB-XL quality flag 61/434 = 14.1% vs without a flag 38/1,085 = 3.5% (first 50; `results/flagged_recordings_effect.md`).
- New 100, unflagged recordings, clean page: 2/69 = 2.9% wrong. All150 unflagged, clean: 2/104 = 1.9%.

### 2.3 Claim C3: can the photo alone warn? (Section D) - INCONCLUSIVE, and the honest reading is negative
Verdict rule: the new 100 must hold at least 100 wrong readings; they hold 86, so the word is **inconclusive**.
- Trained on the first 50, scored once on the new 100: AUC **0.858** (0.81-0.91). The oracle that is told the damage type and level gets **0.827** (0.77-0.90). So the detector is about as good as knowing how damaged the page is.
- **Inside one damage type and level it is at chance:** resolution level 5 AUC 0.521, blur level 5 AUC 0.476. It cannot tell which damaged pages will fail.
- Unseen damage type (train on the others): resolution 0.78, blur 0.56, brightness 0.37, faded grid 0.48. So it does not generalise to a damage type it was not built around.
- Earlier development-set test (first 50, whole recordings held out): AUC 0.607 (0.49-0.82), oracle 0.655, random split 0.661. The old figure 0.785 came from 6 events on the same data and is **never quoted as held-out**.
- **Real captures (EXPLORATORY, Section H/L):** trained on the simulated damage and applied once, the photo detector scores AUC 0.516 (0.46-0.57) on 857 images, and 0.52-0.55 on the own-phone photos (Section O: criterion AUC >= 0.70 with lower bound above 0.50 - **NOT MET**).
- Gate on the new 100 (descriptive, no guarantee): flagging the top 10 / 20 / 30% of photos catches 60 / 76 / 80% of the wrong readings; wrong rate among kept photos 3.0 / 2.1 / 1.9% vs 6.8% overall. The flagged photos are mostly the resolution-5 and blur-5 pages, i.e. it mostly removes pages that were damaged on purpose.

### 2.4 Repeatability (bridge run, mark 3)
- 12 recordings x 13 versions re-digitised on another day: the bad label changed on **0 of 156** images (rule: more than 5% would make pooled comparisons exploratory - not triggered). Heart rates equal within 1 bpm on 153 of 155 images. Rechecked.
- Warning that stays in the report: the first sweep and the second sweep (same images) differed in output availability (163 vs 30 unreadable images); where both gave an HR, 98.1% were identical. The cause is unknown (different machine or unpinned code). This is why the report calls sweep 2 a repeat, not a replication.

### 2.5 Other pre-specified or fixed-rule items
- Arm B (the image-kit's own artifacts: wrinkles, creases, augmentation), 30 recordings: wrong HR clean 0, wrinkles 1, augment 0, both 0 of 30; no difference from clean (Holm p = 1.0). Rechecked. Limit: the digitiser was trained on this kind of artifact, so "no harm" is the expected result.
- Arm C (real captures, 40 recordings) and C+ (100 more): see 3.2. The rate comparison against the clean kit page, by capture type, found no difference after Holm except "no output" for phone photos of a screen (below).

---

## 3. EXPLORATORY results

### 3.1 The digitiser's output can warn when the photo cannot (Sections D2, L)
Fifteen features computed only from the digitised signal (beat regularity, agreement between leads, completeness, ...). Simulated new 100, 5-fold x 10 grouped cross-validation, **cleaned** labels (1,262 images with a reading, 113 wrong - rechecked):

| Model | AUC overall | Inside resolution level 5 | Inside blur level 5 |
|---|---|---|---|
| Output features | **0.926** (0.89-0.95) | 0.873 (0.79-0.94) | 0.892 (0.79-0.96) |
| Five photo scores | 0.724 (0.63-0.85) | 0.481 (0.36-0.60) | 0.432 (0.28-0.61) |
| Both | 0.927 | 0.875 | 0.887 |

The improvement criterion fixed in advance (inside-damage AUC at least 0.70, lower bound above 0.50) was met with the original labels (Section D2: 0.818 and 0.829) and with the cleaned labels.
- Which checks do the work (original labels): beat regularity alone 0.892; agreement between leads alone 0.838; completeness alone 0.723.
- **Cost:** at the top-20% flag level, right readings are flagged for 13% of normal recordings but **67% (45/67) of readings on atrial fibrillation / flutter recordings** (6 recordings). The check cannot tell a rhythm that is truly irregular from a failed read. This goes in the limits.
- Using five different beat detectors (Section M) did not add value (pooled real-capture AUC +0.005; rule needed +0.02). **Rule not met.**

### 3.2 Real captures (competition images) - the digitiser, the check, the traffic light
Rates of wrong HR (Section H; original measure, pooled 140 recordings): clean kit page 16/140 = 11%; print-scan 12-16%; phone photo of print 22/140 = 16%; stained 14%; damaged 14%; mould scan 14-16%. **No capture type is significantly worse than the clean kit page** (all Holm p above 0.5) for wrong HR.
- **Phone photo of a screen: no output on 53/140 = 38% (30-46%)**, against 1% on the clean page (exact paired test, Holm p < 0.001). This is the only large, clear effect among the real captures. Rechecked.
- **Wrong readings on the clean kit page:** 16/140 = 11% - the error is not (only) damage. Cause (POST HOC diagnosis, Section I): a fragile one-number HR from raw-signal beat finding on hard rhythms; the digitiser draws the right waveform (median correlation 0.98 with the true lead II) in nearly all of these.
- **Measurement fix (POST HOC, 2026-11-08):** applying the same cleaning filter to the true and the digitised signal before beat finding cut wrong readings among real captures from **168 of 1,203** (original measure) to **46 of 1,201** (cleaned). Rechecked. Both are always shown. Because the fix was made after seeing the problem, every later label uses it and the report says so.
- **Output check on real captures (trained only on simulated damage, applied once, cleaned labels):** AUC 0.923 (0.86-0.97) on the pooled 140 (1,201 images, 46 wrong); 0.915 (0.84-0.97) on real captures C1-C8. Fewer than 100 wrong readings -> descriptive. With the original labels the same model scored only 0.64 - the higher number depends on the corrected measure; both are reported.
- Gate on real captures C1-C8: flagging the top 10 / 20 / 30% catches 65 / 90 / 95% of the wrong readings; right readings flagged 8 / 17 / 27%; wrong rate among kept 1.5 / 0.5 / 0.3% (overall 3.8%).

### 3.3 Traffic light (Section P) - frozen before any real data was scored
GREEN = no warning; AMBER = have a person check; RED = do not trust the HR (no usable HR is always RED). Thresholds 0.2585 / 0.7823 came from out-of-fold scores of the simulated training set only.

| Data | Light | Readings | Wrong | Wrong rate (Wilson 95%) |
|---|---|---|---|---|
| Competition real captures, images with an output (1,203) | GREEN | 917 | 2 | 0.2% (0.1-0.8) |
| | AMBER | 204 | 14 | 6.9% (4.1-11.2) |
| | RED | 82 | 30 | 36.6% (27.0-47.4) |
| Own phone set 1, 54 photos with an output | GREEN | 22 | 0 | 0.0% (0-14.9) |
| | AMBER | 15 | 1 | 6.7% (1.2-29.8) |
| | RED | 17 | 13 | 76.5% (52.7-90.4) |

- If a missing output also counts as RED (competition, bad = no output or wrong): RED holds 87 of 139 (62.6%) and 84% of all bad readings; GREEN still 2 bad of 917.
- Own phone, all 60 photos (bad = no usable HR or wrong): GREEN 0/22 bad, AMBER 1/15, RED 19/23.
- These intervals treat images as independent; the same recording appears up to 9 times, so they are optimistic. Fewer than 100 wrong readings: descriptive. Not a medical device.

### 3.4 Own-phone set 1 (Section O)
60 photos of a laptop screen, 30 pages, one phone: no usable HR on 6, wrong on 14 (20 of 60 bad). The photo detector did not predict "no output" (AUC 0.552, 0.32-0.80). The output check predicted wrong HR with AUC 0.855 (0.71-0.96) on the 54 photos with an output. Angled + small photos failed most (13 of 15 bad). Rechecked (6 / 14).

### 3.5 Straightening fix (Section Q, first 60 photos) - the idea came from these same photos
Bad readings out of 60: original 20; enlarge 12 (Holm p 0.0215); **straighten 2 (Holm p 0.0001)**; straighten + big 6 (p 0.0087). Newly bad 1, newly good 19 for straighten. Page found 60/60. Lights on the straightened photos: GREEN 48, AMBER 10, RED 2 (original: 22 / 15 / 23). Rechecked. Because the fix was designed on these photos, this is **exploratory**; the next section is what makes it a test.

---

## 4. CONFIRMATION on new photos (Section Q2) - rule written before the photos existed

Design: 20 new pages (seed 45, none used before), 40 photos (each page straight and angled ~30 degrees), same phone and screen, same digitiser, methods frozen. One test: straightened (V2) against the original (V0), exact McNemar, alpha 0.05; "confirmed" only if bad falls AND p < 0.05. Logged 2026-11-11 in `docs/plan/analysis_plan_changes.md` before any new photo.

**Result: CONFIRMED** (rechecked from the digitised signals by a separate script):

| | Original photo | Straightened (V2) |
|---|---|---|
| Bad readings | **14 / 40** | **2 / 40** |
| No usable HR | 4 | 0 |
| Wrong HR | 10 | 2 |
| Straight shots bad | 4 / 20 | 1 / 20 |
| Angled shots bad | 10 / 20 | 1 / 20 |

- Newly bad 0, newly good 12, exact McNemar **p = 0.0005**.
- Enlarging only (V1): 13 / 40 bad (no help). Straighten + enlarge (V3): 3 / 40 bad (no better than V2). Secondary, descriptive.
- Traffic light (not retrained): original photos GREEN 20 (0 bad), AMBER 7 (1 bad), RED 13 (13 bad); straightened GREEN 32 (0 bad), AMBER 7 (1 bad), RED 1 (1 bad). No bad reading was GREEN. Rechecked.
- The two bad straightened readings are one page (Q13): both photos give 66 bpm against a true 58 bpm. The digitiser reads that page wrongly whatever the photo, so straightening cannot fix it; the traffic light flagged it (AMBER on the straight photo, RED on the angled one).
- Both batches together, descriptive only (the first 60 were used to design the fix): original 34/100 bad, straightened 4/100 (Wilson 2-10%).
- **Limits:** one phone, one screen, 20 recordings; the two photos of a page are not independent; photos of a screen, not paper.

---

## 5. Secondary and reference numbers

- **Heart-rate reference is reliable** (agrees with the commercial 12SL and Glasgow algorithms: median absolute difference 0.4-0.7 bpm, rho 0.98-0.99, first 50) except for about 13% of recordings whose reference depends on the sampling rate (20/150). Digitised HR follows the 100 Hz reference on 7 of 8 such recordings in the first 50.
- **Signal quality (aligned SNR, new 100, Section A):** clean pages median 11.8 dB (middle half 9.4-14.5). Resolution 5: 2.2 dB; blur 5: 0.6 dB; rotation 5: 0.0 dB; JPEG 5 and brightness 5: about 10.6 dB. A low SNR goes with a wrong HR (AUC 0.828) but 9 images with acceptable SNR (7.0 dB or more) still had a wrong HR (from 6 recordings). SNR is not a safe stand-alone check. SNR mixes noise with local timing wobble of the traced line.
- **Agreement (Bland-Altman, all 150, digitised minus reference):** clean bias -0.03 bpm, limits -3.2 to +3.1; resolution 5 limits -24.9 to +25.9; blur 5 limits -17.5 to +15.0.
- **False reassurance (heart rate), all 150, 13 shared versions:** resolution level 5: 19 of 148 readings (true HR outside 60-100, digitised inside); blur level 5: 7; clean page: 1; rotation 5: 0. Descriptive, small numbers. (Normal range 60-100 bpm is a convention.)
- **QTc (by this method only, descriptive):** QT, PR and QRS from NeuroKit2 agree only moderately with commercial tools on the clean original (QT rho 0.66-0.67; QTc rho 0.4-0.5); PR and QRS are not used as clinical measures. QTc false-reassurance events: Fridericia 10 of 258 at-risk tests (3.9%, 2-7%), Bazett 16 of 399 (4.0%). Too few events to rank damage types.
- **Second heart-rate detector (Pan-Tompkins):** it is already "wrong" on 13% of clean pages (main detector 3%), so it is a weak second opinion. It keeps resolution 5 and blur 5 as the worst damage types.
- **Calibration of the photo detector (Section G):** trained with class weights, predicted risk is far too high (mean 0.46 vs observed 0.068). Do not read its scores as probabilities.
- **Sample size (Riley/Collins):** the new 100 hold 86 wrong readings and real captures 46 (cleaned): fewer than the recommended 100. This is why C3 is inconclusive and why real-capture numbers are descriptive.
- **CLAIM 2024 checklist (Section G):** 22 met, 12 partly, 6 not applicable, 3 to do, 1 not met (test-set size not derived from a calculation).

---

## 6. What we may claim and what we may not

### May claim (with the stated wording)
1. "In the simulation, with six damage types, only very low resolution (15% size) and heavy blur (21 x 21) made the digitiser's heart rate wrong at a high rate (47% and 17% of pages); JPEG, brightness, faded grid and rotation did not." (C1, supported on a held-out set, with and without reference-uncertain recordings.)
2. "Strong page rotation does not give wrong numbers; it makes the digitiser give no answer on about 1 page in 5 (19%)." (simulation)
3. "On photos of an ECG shown on a screen, taken with one phone, the digitiser often gave a wrong or missing heart rate (20/60 and 14/40 photos)." (own phone, two independent batches, descriptive)
4. "Straightening the photo before digitising (finding the page and flattening it) cut bad readings from 14 to 2 of 40 on new photos (exact paired test p = 0.0005), in a test whose rule was fixed before the photos existed." (one phone, one screen, 20 recordings)
5. "A traffic light computed only from the digitised signal flagged most bad readings: in the 40 new photos no bad reading got a GREEN light (0 of 20 GREEN on the original photos, 0 of 32 on the straightened ones); on the competition real captures GREEN readings were wrong 0.2% (2/917)." (descriptive, exploratory)
6. "A photo-quality score alone could not tell which damaged pages would fail (AUC 0.52 and 0.48 inside the worst damage levels) and did not transfer to real photos (AUC about 0.52)." (negative result, reported as measured)
7. "Wrong readings on real captures were not mainly caused by damage: the clean kit page was already wrong in 11%; a corrected, cleaned heart-rate measure reduced wrong readings from 168 to 46 of about 1,200." (post hoc, both shown)
8. "The digitiser repeats its answers: 0 of 156 bad labels changed on a rerun." (but output availability differed between the first two sweeps)

### May NOT claim
- That the traffic light or the straightening works for other phones, other screens, printed paper, other layouts, or other digitisers (one phone, one screen, one digitiser).
- That the traffic light is safe to use on patients, helps patients, or is a medical device. No claim that a flag changes what a person does (the one clinician study we found shows abstention can even raise missed problems).
- Any statistical guarantee for the traffic light or the gate (no coverage or risk guarantee).
- That the photo-quality detector "works" or "is usable". It recognises how damaged a page is, not which damaged pages fail.
- That the output check detects the cause of an error. It cannot tell a failed read from a truly irregular rhythm (67% of right readings on atrial fibrillation/flutter recordings were flagged).
- "Confirmed" for anything except the Section Q2 test; everything in section 3 is exploratory.
- The numbers listed in section 8 (invalid).
- Clinical accuracy of PR, QRS or QTc. Claims about intervals are "by this method" only.
- That real captures are as easy as the simulated pages. Real captures hold fewer than 100 wrong readings, so all real-capture numbers are descriptive.

### Grades in the claims register (proposed, `CLAIMS_REGISTER.md` itself is fingerprinted and not edited)
Claim 1 (resolution and blur): marks 1 (repeated on the held-out 100), 2 (with and without reference-uncertain recordings; the second detector agrees on the ranking but is a weak check) and 3 (bridge run 0/156) are done -> proposed **B**; grade A needs mark 4 (a second person reruns three numbers). Claim 6 (photo detector discriminates) stays **D** and is reported as measured.

---

## 7. How these numbers were checked

- `scripts/analysis/final_numbers_recompute.py` recomputes 36 headline numbers from the raw files: simulated rates (new 100, first 50, all 150), bridge run, Arm B, cleaned and original counts for simulated and real captures, the whole confirmation set (including the signal-to-heart-rate step, the exact test and the traffic-light counts), own-phone set 1 and the first fix experiment. **All 36 match** the section reports; result file `results/analysis/FINAL_RECHECK.md`.
- The first run found 3 mismatches (blur 5: 16 instead of 17; one real-capture count 167 instead of 168). Cause: the saved heart-rate columns are rounded to 0.1 bpm, so two readings with true differences 5.02 and 5.04 bpm looked like exactly 5.0 bpm. The reports used the unrounded difference, which follows the rule ("more than 5 bpm"); the check script was changed to use it, and then all numbers matched. No reported number changed.
- **This is a second script by the same author, not a second person.** The claims register asks for a team member or the guide to rerun three numbers. That step is still open; suggested three: new-100 resolution level 5 (47/99), confirmation set bad 14 -> 2, competition GREEN wrong 2/917. Command: `python -I scripts/analysis/final_numbers_recompute.py`.
- Limits of the check: it uses the same digitised signals and the same heart-rate definition; it does not re-run the digitiser.

---

## 8. Numbers that are never quoted

| Number | Why |
|---|---|
| `snr_db` column in `results_v2.csv` (about -3 dB) | Compared a 100 Hz truth with a 1,000 Hz output sample by sample; invalid. Use the aligned SNR (Section A) |
| AUC 0.785 for the photo detector, first-50 data (6 events) | Not held-out; replaced by 0.607 (development) and 0.858 (new 100) |
| NeuroKit2 PR and QRS against references | Correlation with the commercial values 0.06-0.35 |
| QTc "prolonged" counts from NeuroKit2 Bazett (21/50 vs 11 for 12SL) | Method over-calls; use Fridericia and "by this method" |
| Original-measure real-capture AUC 0.64 as "the" result | Superseded by the corrected measure; quote both with their labels |
| Pooled 100-photo rates as evidence of the fix | Descriptive only; the first 60 were used to design the fix |
| Wilson intervals in sections 3.3 as exact | They treat images as independent (optimistic) |

---

## 9. Still open (not part of the freeze)
- A second person's recheck of three numbers (claims register mark 4).
- Project title and team details; whether the guide expects a website; funding line (CLAIM item 44).
- The two Downloads papers (Zhou 2021, Huerta Herraiz 2020) are not yet read for related work.
- Git commit and zip backup (waiting for the user's yes).

## 10. Added after the freeze (2026-11-13): gaps found in a review against standard digitisation practice
All EXPLORATORY: the rules were logged in `docs/plan/analysis_plan_changes.md` (2026-11-13, with one amendment made before any gap-3 result) before the runs. No number in sections 1 to 9 was changed. Recounted from the saved CSV files by a separate command (all main numbers match).

### 10.1 Dataset inventory (`results/DATASET_INVENTORY.csv`, `.md`; no new result)
340 recordings, one row each: simulated first 50 (1,550 images), simulated new 100 (1,300), real captures Arm C 40 (360) and C+ 100 (900), own phone P01-P30 (60 photos) and Q01-Q20 (40). Every image has a true digital signal (exact pair for drawn pages; Challenge truth, lead II only, for real captures). 12SL values exist for all 150 + 50 PTB-XL recordings, not for the Challenge recordings. The first 50 have no saved digitised signals. No expert beat annotations are used.

### 10.2 Waveform errors of the digitised lead II (Section R; `results/analysis/SECTION_R.md`)
Aligned within +-0.5 s, means removed, gain not fitted; median (middle half). Simulated new 100, **clean page** (99 of 100 readable): MAE **0.0107 mV** (0.0086 to 0.0151), RMSE **0.0282 mV** (0.021 to 0.041), Pearson r **0.974** (0.958 to 0.989), gain error -0.02% (-1.3 to +1.5), R-peak timing error **2.5 ms** (p90 5 ms), lag 3 ms, **R-peak amplitude error -0.080 mV** (the digitised R peaks are lower than the true ones).
- Damage level 5: blur r 0.54, MAE 0.062 mV, R timing error 31 ms; low resolution r 0.65, MAE 0.048 mV, timing 17.5 ms; rotation 16 degrees: only 78 of 100 readable; JPEG, brightness and faded grid are close to clean (r 0.96 to 0.98).
- Real captures, C+ (100 recordings): kit original r 0.99; print-scan colour / black and white r 0.76 / 0.79, timing about 9 ms, a systematic lag of +21 to +24 ms; mould scans r 0.71 to 0.73; **phone photo of print r 0.47**, timing 27 ms, gain error +7.7%; phone photo of a screen: only 62 of 100 readable, and for those r 0.93 (a selection effect: the unreadable ones are not in it).
- Own phone, original (not straightened) photos: set 1 straight r 0.89, angled r 0.54 with a **median gain error of -48%** (angled photos shrink the amplitude); set 2 straight r 0.93, angled r 0.91 (17 to 18 readable of 20). Unreadable (fewer than half of lead II read): 31 of 1,300 simulated, 58 of 1,260 real captures, 13 of 100 phone photos.
- Limits: the simulated truth is a 100 Hz signal interpolated to 1 kHz, so timing differences below about 5 to 10 ms are not meaningful; real captures are compared on lead II only; descriptive, no pass/fail rule.

### 10.3 PR, QRS and QT on the digitised lead II against 12SL (Section S; `results/analysis/SECTION_S.md`)
Clean pages of the new 100 (99 recordings, 21205 excluded). Methods frozen from development on the first 50 original signals (QT cwt, PR dwt, QRS dwt; lead II only; the 2.5 s segments of the other leads are too short for the detector, an amendment logged before any result). The acceptance rule was written before the run and is the assistant's proposal, **not approved by the guide**.

| Parameter | Original lead II (a): median abs diff / bias / within tolerance | Digitised (b): median abs diff / bias / within tolerance | Recordings with a value (b) | Rule met |
|---|---|---|---|---|
| QT | 36 ms / +46 ms / 55% (within 40 ms), n = 69 | 26 ms / 0 ms / 54%, n = 70 | 71% | **NO** |
| PR | 78 ms / -66 ms / 25%, n = 93 | 78 ms / -69 ms / 24%, n = 93 | 100% | **NO** |
| QRS | 84 ms / +91 ms / 9% (within 20 ms), n = 98 | 98 ms / +103 ms / 1%, n = 98 | 99% | **NO** |

- **No interval is validated.** The method fails on the ORIGINAL signal already (column a), so the photo cannot be blamed. What the photo adds on top (digitised minus original, same method): median 12 ms (QT), 4 ms (PR), 8 ms (QRS).
- Spearman rho with 12SL: QT 0.55 (original) and 0.40 (digitised); PR 0.21 and 0.20; QRS 0.19 and 0.18.
- Damage makes QT worse and rarer: median absolute difference 46 ms (blur 3), 75 ms (blur 5), 36 ms (resolution 3), 66 ms (resolution 5); share of recordings with a QT value falls from 71% (clean) to 30% (blur 5) and 38% (resolution 5). GREEN images only: QT median abs 23 ms, bias +14 ms, value share 60%: still above the rule.
- **Consequence:** the demo keeps PR, QRS and QT as "Not measured by this tool". To get them right a better delineation method is needed first (tested on the original signal, then on photos, with a rule fixed in advance).

### 10.4 What this adds to the claims (section 6)
- May claim (simulation, lead II): "On clean drawn pages the digitised lead II matched the true signal with a median correlation of 0.97, a median error of 0.011 mV and an R-peak timing error of 2.5 ms; R-peak heights were read about 0.08 mV too low. Blur and low resolution at the worst level reduced the correlation to 0.54 and 0.65."
- May claim (descriptive): "On real captures the waveform match fell from r 0.99 (kit original) to about 0.47 for phone photos of printed pages."
- May claim: "PR, QRS and QT intervals measured with NeuroKit2 wavelet methods could not be validated against 12SL even on the original signal, so no interval is shown."
- May NOT claim: that any interval from a photo is accurate; that the phone-photo-of-screen waveform results describe all such photos (only 62 to 70% were readable); that the acceptance thresholds are standards.

### 10.5 A better QT method (Section T, 2026-11-14; `results/analysis/SECTION_T.md`, `SECTION_T_dev.md`, `SECTION_T_confirm.md`)
My own median-beat method (QRS onset by slope, T end by the tangent method, median over leads), instead of NeuroKit2. **Developed on the first 50 recordings only** (original signals cut to the page layout), six candidates, the choice and one constant offset (-40.5 ms: the method reads about 40 ms short of 12SL's global QT) frozen in `results/analysis/sectionT_frozen.json`. Rules were written before any code ran; the held-out test was run **once**; recounted from the CSV files.

| Test | Typical error | Bias | Within 40 ms | Photos / recordings with a value | Rule (<= 20 ms, 90% within 40 ms, |bias| <= 10 ms, 90% with a value) |
|---|---|---|---|---|---|
| Held-out new 100, **original signal** in the photo windows (99 recordings) | 7.8 ms | +6.6 ms | 92% | 100% | **meets** |
| Held-out new 100, **digitised clean page** (primary) | 13.5 ms | **+10.5 ms** (95% interval +5.1 to +16.1) | 92% | 100% | **does not meet** (bias 0.5 ms over the limit; everything else met) |
| New photos (own phone, 100 photos of 50 recordings), **straightened** (primary) | 19.5 ms | -6.0 ms | **84%** (16 of 100 photos more than 40 ms off) | 100% | **does not meet** (only the 90% criterion missed) |
| New photos, original (not straightened) | 24.0 ms | -2.2 ms | 73% | 90% | does not meet |

- Compared with NeuroKit2 (section 10.3): the typical error on the original signal fell from 36 ms to 7.8 ms, on the digitised page from 26 ms to 13.5 ms, and QT values are now given for 100% of recordings (was 69 to 71%).
- Spearman rho with 12SL: 0.83 (original, held-out), 0.81 (digitised, held-out), 0.64 (new straightened photos).
- By damage (held-out, digitised): JPEG, brightness, faded grid and rotation 12 to 14 ms; blur level 5 49 ms (33% within 40 ms) and low resolution level 5 41 ms (47% within 40 ms). GREEN images only: 14 ms, bias +12 ms, 90% within 40 ms.
- New-photo sets differ: set Q (20 recordings) 16.9 ms, bias +6.0 ms, 92% within 40 ms, meets; set P (30 recordings) 25.4 ms, bias -13.9 ms, 78% within 40 ms, does not meet.
- **Verdict: QT is close but NOT validated** under the pre-set rule, which is the assistant's proposal and not approved by the guide. The method, constants, offset and thresholds were NOT changed after seeing the held-out result (changing them and re-running on the same 100 would make them no longer held-out); the confirmation on new photos was written down before it ran. The demo keeps QT as "Not measured by this tool".
- Limits: 12SL is an algorithm; development on 50 recordings with 6 candidates and one offset allows mild overfitting; one phone, one screen, drawn pages; the two photos of a page are not independent; QTc not evaluated.
- May claim: "A median-beat tangent QT method cut the typical QT error against 12SL from 36 ms to 8 ms on the original signal (held-out recordings, offset learned on 50 other recordings), and to 13.5 ms on digitised drawn pages; on new phone photos it was 19.5 ms, with 84% within 40 ms. It did not meet our pre-set rule, so no QT is shown." May NOT claim: that QT can be read reliably from a photo, or that it passed.

### 10.6 PR interval and QRS duration with my own method (Section U, 2026-11-14; `results/analysis/SECTION_U.md`, `SECTION_U_dev.md`, `SECTION_U_confirm.md`)
Same discipline as QT: rules written before any code ran (including a stated pixel limit: about 5 ms per pixel at 200 dpi, so a QRS rule of 10 ms is close to the limit), development on the first 50 original signals, choice and one offset per parameter frozen (`results/analysis/sectionU_frozen.json`), held-out test run **once** on the new 100, confirmation run **once** on 100 new own-phone photos. Recounted from the CSV files.
- Frozen: **QRS** = global measure (earliest QRS onset to latest QRS offset over leads, 5% slope threshold), offset -7.6 ms; **PR** = median over leads with the tangent P onset, offset +5.8 ms.

| | Typical error | Bias | Within tolerance (PR 40 ms, QRS 20 ms) | With a value | Rule (PR: 20 ms / 90% / 10 ms; QRS: 10 ms / 90% / 5 ms; 90% with a value) |
|---|---|---|---|---|---|
| **PR**, held-out 100, original signal | 8.2 ms | +0.1 ms | 99% | 98% | meets |
| **PR**, held-out 100, digitised clean page | **7.3 ms** | +3.1 ms | 97% | 99% | **meets** |
| **PR**, new phone photos, **straightened** | **12.0 ms** | +5.2 ms | 95% | 95% (91 of 100 photos) | **meets** |
| PR, new phone photos, original (not straightened) | 8.7 ms | +6.0 ms | 97% | **67%** | does not meet (too many photos give no PR) |
| **QRS**, held-out 100, original signal | 8.4 ms | +1.0 ms | 85% | 100% | does not meet |
| **QRS**, held-out 100, digitised clean page | 13.2 ms | +1.6 ms | 72% | 100% | does not meet |
| QRS, new phone photos, straightened | 18.2 ms | +15.8 ms | 59% | 100% | does not meet |

- **PR is validated under the pre-set rule** (held-out original, held-out digitised and new straightened photos all meet it), compared with NeuroKit2 where the PR error was 78 ms (section 10.3). Spearman rho with 12SL: 0.85 (original), 0.79 (digitised), 0.76 (new straightened photos). It holds for straight and angled shots and for both phone sets, **only after straightening**.
- **QRS is NOT validated.** On the original signal the typical error is fine (8.4 ms) but 15% of recordings are more than 20 ms off; on photos it is 13 ms (clean pages) and 18 ms (phone photos), with rho only 0.13 to 0.43. The pixel limit and the thin line make a 10 ms rule out of reach for photos.
- Damage (held-out, digitised): PR keeps a small error (7 to 9 ms for JPEG, brightness, grid; 13 to 17 ms for blur 5 and resolution 5) but **gives a value for only 43% to 47%** of recordings at level 5 of resolution and blur. QRS error is 67 ms (blur 5) and 91 ms (resolution 5). GREEN images only: PR 7 ms, 96% with a value; QRS 14 ms.
- Limits: the thresholds are the assistant's proposal, **not approved by the guide**; 12SL is an algorithm; developed on 50 recordings with 6 candidates per parameter and one offset each; simulated drawn pages, one phone, one screen; the two photos of a page are not independent; no verdict such as "normal" or "prolonged" is made.
- **Found while adding PR to the demo (2026-11-14), and corrected after a closer look: the PR statistics exclude atrial fibrillation.** The recordings with no 12SL PR value (6 of 99 held-out; 12 of 100 phone photos) are atrial fibrillation or flutter recordings (all 6 held-out ones carry an AFIB or AFLT label; across PTB-XL 95% of 1,570 such recordings have no 12SL PR, because there are no P waves). They were left out of every PR statistic, and **our method still produced a PR for all 6 held-out pages (170 to 244 ms) and for 7 of the 12 photos: those numbers are meaningless.** So the PR result holds only for rhythms in which 12SL finds a P wave. Safeguards in the demo (precautions, not a validated filter, calibrated on these 14 cases): PR is hidden when the traffic light reports irregular beat spacing (catches 4 of the 6 pages) AND when the beat-spacing variation rr_cv is above 0.12 or unknown (catches all 6 pages and all 8 phone photos of such recordings); this hides PR on about 15% of normal-rhythm photos (14 of 93 pages, 15 of 92 photos).
- May claim: "With a median-beat tangent method, the PR interval read from straightened photos was typically within 7 to 12 ms of 12SL (95 to 97% within 40 ms) on held-out drawn pages and on new phone photos, meeting our pre-set rule; the QRS duration could not be validated." May NOT claim: PR from photos that are not straightened, blurred or very small; any QRS value; that the rule is a standard; clinical accuracy.

### 10.7 QRS and QT, second attempt on FRESH data (Section V, 2026-11-14 night; `results/analysis/SECTION_V.md`, `SECTION_V_dev.md`, `SECTION_V_confirm.md`)
Rules written first (three entries in `docs/plan/analysis_plan_changes.md`). Fresh test set: **100 PTB-XL recordings never used before** (seed 46; 7 with atrial fibrillation or flutter), drawn locally with the same tool and settings and digitised with the same Open-ECG-Digitizer, sealed until one test. Development: 1,000 further unused recordings (original signals in the page layout). **Amendment made before any fresh page was seen:** my first calibration allowed rescaling and gave QT a slope of 0.19 (a number that is mostly the population mean, i.e. false reassurance for long QT); calibration may now only add an offset (first run kept in `SECTION_V_dev_first_run.md`). Frozen: QT = median over leads with the tangent T end (+ small RR term and offset); QRS = global onset to offset with a 3% slope threshold (+ offset); photo offsets fitted once on the digitised pages of the earlier 99 held-out recordings. Development (cross-validated, originals): QT 8.8 ms typical error, 90% within 40 ms; QRS 7.0 ms, only 85% within 20 ms. Recounted from the CSV files.

| | Typical error | Bias | Within tolerance (QT 40 ms, QRS 20 ms) | With a value | Rule (QT 20 ms / 90% / 10 ms; QRS 10 ms / 90% / 5 ms; 90% with a value) |
|---|---|---|---|---|---|
| **QT**, 100 fresh pages, original signal | 7.0 ms | +0.7 ms | 94% | 100% | meets |
| **QT**, 100 fresh pages, digitised | 8.8 ms | -3.4 ms | 93% | 99% | **meets** |
| **QT**, 100 phone photos, straightened | 14.9 ms | **-16.5 ms** | 86% | 100% | **does not meet** |
| QRS, 100 fresh pages, original signal | 6.9 ms | -3.1 ms | 86% | 100% | does not meet |
| QRS, 100 fresh pages, digitised | 9.2 ms | -4.8 ms | 74% | 99% | does not meet |
| QRS, 100 phone photos, straightened | 12.9 ms | +12.0 ms | 69% | 100% | does not meet |

- **Safety checks committed to in the amendment** (the test script did not print them; computed afterwards from the saved per-page file, before any decision): the slope of the measured QT on the 12SL QT is **0.68 (original) and 0.69 (digitised), below the limit of 0.7 fixed in advance**, so QT fails its safety purpose even where the error rule is met: a true QT of 350 ms or less is overestimated by 23 to 27 ms on average (one page read 522 to 529 ms against 344 ms), and for a true QT of 450 ms or more the mean error is -6 ms. On the 7 atrial fibrillation / flutter pages QT is poor: median error 21.9 ms, bias -45.7 ms, one page read 180 ms. For QRS the slope is **0.21 to 0.39** and **recordings with a true QRS of 120 ms or more (n = 7) are read about 42 to 47 ms too short**, so a wide QRS would be shown as normal.
- **Verdict: QT is NOT validated** (it meets the rule on fresh drawn pages, but not on real phone photos, and its slope is below 0.7); **QRS is NOT validated** and must never be shown. Both stay "Not measured by this tool" in the demo. The earlier first-attempt numbers (10.5, 10.6) stay as written.
- Limits: the thresholds are the assistant's proposal, not approved by the guide; 12SL is an algorithm; the same 100 phone photos confirmed an earlier version of these methods (this version was not developed on them); one phone, one screen.

### 10.8 Frontal QRS axis (Section W, 2026-11-14 night; `results/analysis/SECTION_W.md`, `SECTION_W_dev.md`, `SECTION_W_confirm.md`)
Same discipline: rules written first; method frozen on the 1,000 development recordings with nothing fitted (net QRS deflection of all six limb leads, dominant-deflection definition, least-squares axis vector); one test on the 100 fresh pages; one confirmation on the 100 phone photos. Reference = 12SL R_AxisFrontal_Global (Glasgow agrees with it within 30 degrees on 99% of 21,789 recordings). Rule (assistant's proposal, not approved by the guide): median circular error <= 10 degrees, at least 90% within 30 degrees, |mean error| <= 10 degrees, at least 90% category agreement (left < -30, normal, right > +90), at least 90% with a value. Recounted from the CSV files.

| | Typical error | Within 30 degrees | Mean error | Category agreement | With a value | Rule |
|---|---|---|---|---|---|---|
| Development, 1,000 original recordings | 3.6 deg | 97% | +1.5 deg | 98% | 99% | (selection only) |
| **100 fresh pages**, original signal | 4.5 deg | 99% | +0.3 deg | 99% | 100% | meets |
| **100 fresh pages**, digitised | **3.8 deg** | 99% | +0.5 deg | 98% | 99% | **meets** |
| **100 phone photos, straightened** | **4.4 deg** | **95%** | -1.0 deg | 92% | 100% | **meets** |
| 100 phone photos, original (not straightened) | 4.9 deg | 87% | +1.7 deg | 85% | 82% | does not meet |

- **Axis is validated under the pre-set rule** (fresh pages and phone photos), **for straightened photos only**. The photo adds about 1 degree to the original-signal error. Atrial fibrillation / flutter pages (n = 7): median 6.8 degrees, largest 18.4.
- **A real failure to state:** on the phone photos, 2 photos of one recording (P13: 12SL axis 148 degrees, measured -95 and -91 degrees) are wrong by 117 and 121 degrees; the next largest errors are 70 degrees or less (95% within 30). All 8 fresh-page recordings with a left axis (< -30 degrees) were put in the left category; the fresh test had **no right-axis recording**, and on the photos a right axis was matched in 0 of 4 photos (the P13 failure above and Q19, 94 read as 77 degrees, a boundary case): **right-axis detection is therefore not shown to work**.
- Limits: assistant's thresholds; 12SL is an algorithm; paced rhythms and very low voltage give unreliable axes in every program; one phone, one screen; the two photos of a page are not independent. The demo shows degrees only, never a word such as "left axis deviation".
- May claim: "The frontal QRS axis read from straightened photos was typically within about 4 degrees of 12SL (95% within 30 degrees on 100 phone photos, 99% on 100 fresh drawn pages), meeting our pre-set rule." May NOT claim: axis from photos that are not straightened; detection of right axis deviation; QT or QRS values; that the thresholds are a standard.

### 10.9 QRS duration, third attempt (Section X, 2026-11-14; `results/analysis/sectionX_test_run.log`, `sectionX_confirm_run.log`, `sectionX_test_per_page.csv`, `sectionX_confirm_per_photo.csv`)
Rules written first (stricter: slope of measured on 12SL >= 0.8, tail checks, at least 90% with a value). Method frozen in development on 1,100 original recordings (`sectionX_frozen.json`): QRS = global activity of all leads, 5% slope (qrs_abs_5). **QT: no candidate passed the slope filter in development, so QT was not tested** (stopped by the rule). Test run **once** on 100 new sealed pages G001-G100 (9 with atrial fibrillation / flutter); confirmation run **once** on 40 new phone photos of G001-G020 (straightened).

| | Typical error | Bias | Within 20 ms | With a value | Slope on 12SL | Rule |
|---|---|---|---|---|---|---|
| (a) 100 pages, original signal | 6.2 ms | +3.2 ms | 93% | 100% | **0.79** | **does not meet** (slope 0.01 under 0.8) |
| (b) 100 pages, digitised | 5.5 ms | +3.0 ms | 93% | 100% | 0.87 | meets |
| 40 phone photos, straightened | 6.2 ms | **+15.4 ms** (CI +4.9 to +31.1) | 95% | 100% | **0.74** | **does not meet** (bias and slope) |

- Rule for the page test needs both (a) and (b); (a) missed on slope by 0.01, so **QRS duration is NOT validated**. The photo confirmation also fails (bias 15 ms over a 5 ms limit; slope 0.74). Neither result is re-run or re-tuned. Wide QRS (>= 120 ms): n = 11 pages, mean error -2.3 ms (a) and +3.1 ms (b); n = 6 photos, +7.9 ms.
- Atrial fibrillation / flutter pages (b), n = 9: median 5.3 ms, bias -0.5 ms.
- **Consequence:** QRS duration stays "Not measured by this tool". QT and QRS duration are closed as not validated after three attempts each (QT stopped in attempt 3 by the rule). May claim: "A combined-lead QRS method reached a typical error of about 5 to 6 ms on drawn pages and photos, but did not meet our pre-set rule on photos (bias +15 ms), so no QRS duration is shown." May NOT claim: that QRS duration can be read from a photo.

### 10.10 P-wave and T-wave amplitude in lead II (Section Y, 2026-11-14; `results/analysis/SECTION_Y_dev.md`, `SECTION_Y_test.md`, `SECTION_Y_confirm.md`, run logs `sectionY_*_run.log`, per-page CSVs)
Rules written first (`docs/plan/analysis_plan_changes.md`, 2026-11-14 afternoon). **ST segment, P duration and T duration were not attempted**: the two commercial algorithms (12SL and Glasgow) themselves agree poorly on them (rho 0.57 for P duration, 0.49 for T duration; ST amplitude spread 0.047 mV, under 4 pixels), so no reference exists to validate against. Reference = 12SL P_Amp_II and T_Amp_II (mV). Amplitude from one median beat of lead II, baseline = PR segment. Development on 1,100 original recordings (5-fold, offset only, slope >= 0.8, value for >= 90%).
- **T-wave amplitude: stopped in development.** Best candidate slope on 12SL 0.68 (TA), 0.66 (TB), 0.72 (TC), all under 0.8 (median error 0.015 mV, but the measure is compressed: false reassurance for large T waves). Not tested.
- **P-wave amplitude:** frozen PA (largest deviation from the PR baseline in the window 250 to 30 ms before QRS onset), offsets -0.0235 mV (original) and -0.0177 mV (digitised, fitted on 199 earlier digitised pages). Development: median error 0.012 mV, 93% within 0.06 mV, slope 0.97. Test run **once** on 100 sealed pages G001-G100 (9 atrial fibrillation / flutter); confirmation run **once** on 40 phone photos of G001-G020 (straightened). Disclosure: the same pages and photos were used before for QRS/QT only.

| | Typical error | Bias | Within 0.06 mV | With a value | Slope on 12SL | Rule (<= 0.03 mV, 90%, |bias| <= 0.015, slope >= 0.8, 90% with a value) |
|---|---|---|---|---|---|---|
| (a) 100 pages, original signal | 0.013 mV | +0.001 | 94% | 98% | 1.04 | meets |
| (b) 100 pages, digitised | 0.012 mV | -0.001 | 97% | 98% | 0.99 | meets |
| 40 phone photos, straightened | 0.014 mV | -0.014 | 94% | 90% | **0.77** | **does not meet** (slope) |

- Page test: both parts meet (tails: reference P <= 0.05 mV, n = 23, mean error -0.001 mV; reference P >= 0.20 mV, n = 2, too few). Atrial fibrillation / flutter pages (b), n = 9: median error 0.033 mV (the P-wave measure is poor when no P wave exists; this is NOT a detector of atrial fibrillation).
- **Photo confirmation fails on the slope (0.77, limit 0.8):** the measured P amplitude is slightly compressed on photos (bias -0.014 mV, at the limit of 0.015). Straight shots slope 0.80, angled 0.75; 36 of 40 photos gave a value. Neither the rule nor the method was changed after seeing this.
- **Verdict: P-wave amplitude is NOT validated** (page test yes, photo confirmation no). T-wave amplitude is not validated (stopped in development). ST segment, P duration, T duration are not attempted. All stay "Not measured by this tool" in the demo.
- Limits: assistant's thresholds, not approved by the guide; 12SL is an algorithm; a P wave is about 0.1 mV, 8 pixels; one phone, one screen; the two photos of a page are not independent; only 2 pages with a tall P (reference >= 0.20 mV) so the tail is untested. May claim: "On drawn pages the P-wave amplitude in lead II was read typically within 0.012 mV of 12SL (slope 0.99), but on 40 straightened phone photos the slope was 0.77, under our pre-set 0.8, so no P-wave value is shown." May NOT claim: that P or T wave amplitude can be read from a photo, or any P-wave based detection of atrial fibrillation.

### 10.11 Straightening and the traffic light on 120 SIMULATED phone photos (Section Z, 2026-11-14 evening; `results/analysis/SECTION_Z.md`, `sectionZ_all.csv`, `sectionZ_run.log`)
Rules logged before any photo existed (`docs/plan/analysis_plan_changes.md`, 2026-11-14 evening, with one amendment before digitising: the generator keeps the whole page in the frame). **This is a SIMULATION** (a script, not a camera): pages G021-G080, 2 photos per page (straight, angled), tilt, a dark screen edge, vignette, camera noise, and on random photos blur, a shadow or a smaller page (`make_sim_photos.py`, seed 49). Same digitiser, commit and settings; V0 = the photo as it is, V2 = the page finder. Primary test run **once**.

| | Original (V0) | Straightened (V2) |
|---|---|---|
| Bad readings | **64 / 120** | **21 / 120** |
| No usable heart rate | 27 | 2 |
| Wrong heart rate | 37 | 19 |
| Straight shots bad | 13 / 60 | 5 / 60 |
| Angled shots bad | 51 / 60 | 16 / 60 |

- Newly bad 5, newly good 48, exact McNemar **p = 7.1e-10**: **confirmed in simulation** under the pre-set rule. Page finder found the page on 120 of 120.
- By extra (original to straightened): blur 19 to 10 of 35; smaller page 20 to 4 of 33; shadow 9 to 4 of 25; none 16 to 3 of 27. Blur is the damage that straightening helps least.
- Traffic light (frozen, not retrained), straightened photos: GREEN 71 readings, **1 bad (1%)**; AMBER 26 readings, 10 bad (38%); RED 23 readings, 10 bad (43%). On the original photos: GREEN 30 readings, 0 bad; AMBER 17, 3 bad (18%); RED 73, 61 bad (84%).
- **The pre-stated safety criterion (bad GREEN readings on V2) is 1, not 0:** the one GREEN reading with a wrong heart rate is reported as a finding. The real-photo tests had 0 bad GREEN on 40 photos; the simulation is harder (more blur, smaller pages) and larger. This weakens "no bad reading got a GREEN light" for a larger set: it is not a guarantee.
- Limits: a simulation of 120 photos from 60 recordings; the two photos of a page are not independent; no claim about real phones or printed paper; the digitiser is trained on a similar generator.
- May claim: "In a simulation of 120 phone photos, straightening cut bad readings from 64 to 21 (exact paired test p below 1e-8)." May NOT claim: this holds on real phones, or that GREEN means correct (1 of 71 GREEN straightened readings was wrong).

### 10.12 Risk-coverage from saved predictions (Section RC, 2026-11-14; `results/analysis/SECTION_RC.md`, `sectionRC_*.csv`, figure `sectionRC_risk_coverage.png`)
Rules logged before the run (`docs/plan/analysis_plan_changes.md`, "Section RC"), plus **Amendment 1** (sets D and E added after the first run had been seen: same method, nothing tuned, sets A to C unchanged). Nothing refitted: saved scores only; for D and E the traffic-light score was recomputed by the frozen tool from the saved digitised signals, and **the recomputed light equals the saved light on all 320 images** (`sectionRC_light_recompute_check.csv`). EXPLORATORY, descriptive, no guarantee. Coverage = share of images answered when the riskiest are not answered; selective risk = bad readings among the answered. Intervals: bootstrap over recordings (A, B) or pages (C, D, E), ranking recomputed inside each resample.

| Set | Bad overall | Score | Answered 70% | Answered 80% | Answered 90% | AURC (smaller is better) | Random order | Perfect order |
|---|---|---|---|---|---|---|---|---|
| A. Competition captures, 1,260 images, 140 recordings | 103 (8.2%) | Traffic light | 0.23% (0.00-0.79) | 0.89% (0.20-2.18) | 1.76% (0.53-3.35) | 0.91% (0.39-1.63) | 8.17% | 0.40% |
| B. Arm C+ subset, 900 images | 73 (8.1%) | Traffic light | 0.32% (0.00-1.11) | 0.97% (0.14-2.78) | 1.98% (0.49-4.07) | 1.05% (0.38-2.03) | 8.11% | 0.39% |
| B | | Photo detector | 4.60% (2.70-6.98) | 4.17% (2.50-6.39) | 5.43% (3.33-7.90) | 4.30% (2.41-6.76) | 8.11% | |
| C. Own phone set 1, 60 photos, 30 pages | 20 (33.3%) | Traffic light | 11.90% (2.38-26.19) | 18.75% (6.25-33.33) | 25.93% (12.96-40.74) | 11.39% (4.71-21.10) | 33.33% | 6.98% |
| C | | Photo detector | 40.48% (23.81-54.76) | 37.50% (22.86-52.08) | 33.33% (20.37-48.15) | 29.49% (14.06-47.89) | 33.33% | |
| D0. 40 new phone photos, as taken (20 pages) | 14 (35.0%) | Traffic light | 7.14% (0.00-28.57) | 18.75% (3.12-37.50) | 27.78% (11.11-44.44) | 8.57% (2.71-18.51) | 35.00% | 7.83% |
| D2. the same photos, straightened | 2 (5.0%) | Traffic light | 0.00% (0.00-0.00) | 0.00% (0.00-0.00) | 0.00% (0.00-5.56) | 0.21% (0.00-1.47) | 5.00% | 0.21% |
| E0. 120 simulated phone photos, as made (60 pages) | 64 (53.3%) | Traffic light | 36.90% (28.57-46.43) | 42.71% (36.43-51.04) | 48.15% (41.67-55.56) | 23.51% (17.97-30.10) | 53.33% | 18.97% |
| E2. the same photos, straightened | 21 (17.5%) | Traffic light | 7.14% (0.00-13.10) | 10.42% (4.17-17.71) | 12.04% (6.48-19.44) | 7.11% (2.29-14.18) | 17.50% | 1.85% |

- Operating points of the traffic light (share of images answered, bad among them): competition GREEN only 72.8% (2 of 917), GREEN + AMBER 89.0% (16 of 1,121); own phone set 1: 36.7% (0 of 22) and 61.7% (1 of 37); D as taken: 50.0% (0 of 20) and 67.5% (1 of 27); **D straightened: 80.0% (0 of 32) and 97.5% (1 of 39)**; E as made: 25.0% (0 of 30) and 39.2% (3 of 47); **E straightened: 59.2% (1 of 71) and 80.8% (11 of 97 = 11.3%)**.
- **Plain reading:** (1) On the real competition captures, not answering the 20% highest-risk images leaves about 1% bad among the answered (random order: 8%); the photo detector leaves about 4%. (2) On the 40 new real phone photos the traffic light is almost as good as a perfect ordering once the photos are straightened (AURC 0.21% against 0.21%); straightening moves the whole curve down in both D and E. (3) **The "about 1%" does not carry over to harder photos.** On the 120 simulated photos (more blur, smaller pages) straightened, answering the 80% lowest-risk images still leaves 10.4% bad (random 17.5%, perfect order 0%), and answering GREEN + AMBER leaves 11.3%; only GREEN is clean there (1 of 71). The simulation is harder than the 40 real photos, which are few. (4) On own phone set 1 the light helps less (18.8% bad among the 80% answered, wide interval).
- The photo detector's curve is scored against the cleaned labels, the same as the traffic light, although it was trained on the original-measure labels; it has no saved score for D and E. B to E hold fewer than 100 bad readings: descriptive. No coverage or risk guarantee (the images are not exchangeable calibration data). The expectation written before the first run (below 2% bad at 80% coverage on A) held (0.89%); it was only about A.

### 10.13 Intervals that count a recording once, and Bland-Altman pictures (Section CI, 2026-11-14; `results/analysis/SECTION_CI.md`, `sectionCI_intervals.csv`, figure `sectionCI_bland_altman.png`)
Rules logged before the run; Amendment 1 (added after the first run, nothing re-judged): the cleaned heart-rate measure and empirical (percentile) limits were added, and each interval got its own fixed random stream so the numbers do not depend on the order of the calls (two reruns give identical files). Cluster bootstrap (2,000 resamples) over recordings or printed pages; nothing refitted; no pass/fail rule re-applied. Check: the clean-page heart-rate Bland-Altman reproduces the frozen numbers exactly (bias -0.03, limits -3.2 to +3.1); the first version used the absolute difference by mistake and failed this check, and was corrected before anything was recorded.

| Measure | Condition (clusters) | Bias (95% interval) | Limits of agreement, bias +- 1.96 sd (interval of each limit) | Typical error | Within tolerance |
|---|---|---|---|---|---|
| Heart rate (bpm), original measure | clean page (148 recordings) | -0.03 (-0.30 to 0.24) | -3.16 (-4.64 to -1.36) to +3.10 (1.32 to 4.44) | median abs 0.10 | |
| Heart rate | resolution level 5 (148) | +0.54 (-1.43 to 2.53) | -24.86 (-30.20 to -19.21) to +25.93 (21.47 to 29.71) | median abs 3.80 (1.90 to 6.00) | |
| Heart rate | blur level 5 (146) | -1.26 (-2.59 to -0.07) | -17.51 (-24.60 to -10.17) to +15.00 (8.63 to 20.15) | median abs 1.55 (1.20 to 1.90) | |
| Heart rate, CLEANED measure, new 100 | clean page (99) | -0.33 (-0.90 to 0.06) | -5.45 (-9.32 to -1.18) to +4.79 (1.05 to 7.65) | median abs 0.08 | |
| Heart rate, cleaned | resolution level 5 (98) | -0.62 (-3.51 to 2.25) | -29.57 (-38.19 to -20.08) to +28.33 (21.63 to 33.98) | median abs 5.15 (2.02 to 6.66) | |
| Heart rate, cleaned | blur level 5 (97) | -1.42 (-3.24 to 0.10) | -17.90 (-26.18 to -9.68) to +15.05 (7.98 to 20.95) | median abs 1.52 (1.18 to 1.87) | |
| PR (ms) vs 12SL | digitised clean pages, held-out new 100 (92 recordings) | +3.1 (-0.2 to 6.7) | -30.1 (-37.6 to -21.8) to +36.2 (24.7 to 48.3); empirical 2.5th to 97.5th percentile -27.7 to +49.1 | median abs 7.3 (5.5 to 9.4) | within 40 ms: 96.7% (92.4 to 100) |
| PR | straightened phone photos (84 photos, 43 pages) | +5.2 (-0.8 to 11.1) | -38.6 (-52.5 to -24.0) to +48.9 (31.8 to 67.3); empirical -34.5 to +50.3 | median abs 12.0 (7.5 to 16.1) | within 40 ms: 95.2% (89.2 to 100) |
| Axis (deg) vs 12SL | 100 fresh pages, digitised (99 recordings) | +0.6 (-0.9 to 2.2) | -14.4 (-18.0 to -10.7) to +15.6 (10.7 to 20.6); empirical -10.0 to +15.7 | median abs 3.8 (2.4 to 5.3) | within 30 deg: 99.0% (97.0 to 100) |
| Axis | straightened phone photos (100 photos, 50 pages) | +0.1 (-5.2 to 6.4) | -41.9 (-61.0 to -15.7) to +42.1 (13.7 to 69.4); **empirical -22.4 to +28.8** | median abs 4.4 (3.4 to 5.7) | within 30 deg: 95.0% (89.0 to 100) |

| Rate | Original | Straightened | Drop in percentage points |
|---|---|---|---|
| Bad readings, 40 confirmation photos (20 pages) | 35.0% (20.0 to 50.0) | 5.0% (0.0 to 15.0) | 30.0 (17.5 to 45.0) |
| Bad readings, 120 simulated photos (60 pages) | 53.3% (47.5 to 60.0) | 17.5% (10.8 to 24.2) | 35.8 (26.7 to 45.0) |

Wrong heart rate by light, competition captures with an output (140 recordings): GREEN 0.22% (0.00 to 0.56); AMBER 6.86% (1.29 to 14.49); RED 36.59% (20.29 to 56.82).

- **Plain reading:** counting a recording or page once widens the intervals but leaves the story unchanged: the straightening drop is clearly above zero in both sets, and GREEN stays below 0.6% wrong on the competition captures. **Two honest changes of tone.** (1) PR and axis on straightened photos met the pre-set rule (at least 90% within tolerance) by their point estimates (95.2% and 95.0%), but the lower ends of the cluster intervals are 89.2% and 89.0%, just under 90%: "met" means the point estimate met it; the interval reaches below the limit (table in `SECTION_CI.md`). (2) The photo axis limits of agreement (-42 to +42 degrees) are inflated by one gross failure (P13) and assume a bell-shaped spread; the empirical 95% range of the differences is -22 to +29 degrees, which is the fairer statement. The pre-set rule used the median and the share within 30 degrees, not these limits. The blur level 5 heart-rate bias is slightly negative (interval -2.59 to -0.07): blurred pages read a little low on average.
- Limits: 12SL is an algorithm; the cleaned measure exists for the new 100 only (Section K); the axis difference is wrapped to -180..180 degrees; panel d of the figure uses the cleaned measure as in Section Q2.

### 10.14 Failure gallery (Section FG, 2026-11-14; `results/analysis/SECTION_FG.md`, `sectionFG_cards.csv`, figure `sectionFG_failure_gallery.png`)
Ten real failures chosen by rules logged before any card was drawn (every GREEN-but-wrong reading, the largest error after straightening, the page that stays wrong, the axis failure, an atrial fibrillation page with a PR value, a photo with no heart rate; cards 9 and 10 were added in Amendment 1 after the first gallery: the most shrunken own-phone trace, and a false alarm on a right reading). They show what a failure looks like, not how often it happens. What the cards show (trace match r of the digitised against the true trace):
- **Cards 1 and 3 (GREEN but wrong): the trace itself is wrong (r 0.06 and 0.20) and the light was still GREEN.** This is the concrete picture behind "GREEN is not a guarantee".
- Cards 2 and 5 (GREEN wrong; stays wrong after straightening): the traced waveform follows the true one (r 0.89 and 0.97) but the heart rate computed from it is wrong, so the failure is in the heart-rate step (as in the clean-page diagnosis, Section I), not in the tracing. The same page (Q13) gave 66 bpm on both photos against 58.
- Card 4 (largest error after straightening, a blurred simulated photo): trace r 0.24, light RED (correctly flagged).
- Card 6 (axis failure, P13): the digitised aVF trace is upside down against the true aVF (r -0.89), consistent with the axis read as -91 degrees against 148.
- Card 7 (atrial fibrillation page G004): the trace is fine (r 0.95); our method still gives a PR of 209 ms where 12SL gives none (no P waves); the demo hides it (light AMBER, beat-spacing variation 0.23 above the 0.12 limit).
- Card 8: a simulated photo with no usable heart rate on the photo as it is; after straightening 94.1 bpm against 97.7, light RED; the trace is still poor (r 0.16), so the close heart rate is partly luck.
- **Card 9 (amplitude shrunk, own phone P10, angled photo, not straightened): gain error -91%, trace r 0.12, light RED, heart rate wrong.** The angled-photo amplitude shrink seen in Section R (median gain error -48% for angled photos), as a picture.
- **Card 10 (false alarm, atrial fibrillation page G071): the trace is good (r 0.97) and the heart rate is right (100.4 against 99.8 bpm), but the light is AMBER; 7 of the 9 atrial fibrillation / flutter pages in the sealed G set with a right heart rate are not GREEN.** This is the cost already recorded in section 3.1, now as a picture.
- Limits: the two competition cards have no picture (the image files are not on this computer); 8 cards cannot show frequency.

### 10.15 Reproducibility package (2026-11-14; `reproducibility/REPRODUCE.md`)
New folder `reproducibility/`: guide, a minimal pinned package list (`requirements_analysis_minimal.txt`), a one-command check (`run_all_checks.py`, writes `CHECK_REPORT.md`), exact versions (`ENVIRONMENT.md`; Python 3.13.15, RTX 3050, package lists of both environments), tool commits and the two local patches, weight checksums, a one-page second-person check (`SECOND_PERSON_CHECK.md`, with a small script for the third number). **Tested in a clean environment on 2026-11-14:** a new empty virtual environment with only the minimal list installed passes all 4 checks of `run_all_checks.py`, and the interval and risk-coverage scripts run there write tables that are byte-identical (SHA-256) to the ones made in the main Python. Run on 2026-11-14: the 36-number recheck gives ALL MATCH (`results/reproducibility/recompute_run_2026-11-14.log`); the traffic-light tests and the 19 wording tests pass; the GREEN count check gives 2/917. **Not exact, said in the guide:** the digitiser has a random tie-break (repeat variation below); output availability differed between the first two sweeps; Colab package versions were not saved; the recheck is by the same author; nothing is committed to git yet.
- **Seeded demo (2026-11-15; rule and success criterion logged first; `results/reproducibility/repeat_variation_seeded_summary.md`):** the cause of the repeat variation is an unseeded `torch.randn(...) * 1e-6` tie-break in the digitiser (`signal_extractor.py`, `_get_pixel_vals`). The demo wrapper now seeds torch (seed 42, fixed in advance; digitiser code unchanged; `DEMO_DIGITISER_SEED=none` restores the unseeded behaviour). Test: the same 10 demo photos, 2 seeded runs each: **heart rate, light, PR, axis and score identical in both runs on 10 of 10 photos (criterion MET)**, including the two photos that jumped before (sample 4 PR, sample 5 axis). The four example photos give the same heart rate and light as the study values (55.03, 62.56, 106.28, 65.90 bpm). One honest note: the earlier unseeded repeat test (3 runs) under-counted the variation: sample 1 gave PR 163.7 ms in all 3 of those runs, yet an earlier ad-hoc run and the seeded run give 171.9 ms, so several outcomes exist and 3 runs can miss one. The study's results were produced unseeded and are unchanged; the seeded demo shows one fixed draw. Limits: 10 photos, 2 runs, one computer and GPU.
- A wording note: the damage called "faded grid" (`I' = (1-s) I + s mean(I)`) lowers the contrast of the whole page, trace included, not only the grid. The methods file already says "low contrast"; the report and slides should say "reduced contrast", not "faded grid".
- Repeat variation of the demo pipeline (10 photos x 3 runs of the same photo, GPU, nothing changed; `results/reproducibility/repeat_variation_summary.md`; descriptive): **heart rate and traffic light were stable** (largest heart-rate range 0.08 bpm; the light did not change on any of the 10 photos). **PR and axis can jump on a rerun of the same photo:** PR range up to 22.3 ms (sample 4: two runs 173.7 ms, one run 151.4 ms) and 5.0 ms (sample 5); on the other 5 photos with a PR it was 0.2 ms or less. Axis range up to 11.3 degrees (sample 5: 72.4, 61.1, 72.4 degrees); on the other 9 photos 0.1 degrees or less. So a PR or axis number shown for one photo is not exactly repeatable; the validation results (typical errors 12 ms and 4.4 degrees) came from one run per photo and include this noise, but no run-to-run range was measured on the validation sets. Cause not separated (the digitiser's random tie-break or GPU arithmetic). Limits: 10 demo photos, 3 runs, one computer.

### 10.17 Printed-paper photos, set H2 (friend's phone, WhatsApp; Section H2, 2026-11-16; `results/analysis/SECTION_H2_full.md`, `sectionH2_full_all.csv`)
EXPLORATORY. Rules logged before any photo was digitised (`analysis_plan_changes.md`: Section H amendment, provenance correction, user decisions, batch 2). **A different photographer and an unknown phone, NOT the project owner's phone; never pooled with it.** Photos matched to pages by image content (validated on 16 of 16 header IDs). Primary = the **22 straight full-resolution photos** (18 pages); secondary = all 52 full-resolution photos (19 pages, straight and angled); the recompressed copies are a separate part, run later. V0 = photo as taken; V2a = frozen finder as taken; V2b = orientation step (turn a portrait photo 90 degrees counter-clockwise) + frozen finder. bad = no usable heart rate or wrong by more than 5 bpm (cleaned measure).

| Set | Page found by the frozen finder AS TAKEN | Bad as taken (V0) | Bad after V2b | Newly bad / newly good | Exact paired p | Verdict |
|---|---|---|---|---|---|---|
| **Primary: 22 straight photos** | **1 of 22** | 3 | 2 | 0 / 1 | 1.0 | **not confirmed** |
| Secondary: 52 full-resolution photos | 11 of 52 | 15 | 10 | 3 / 8 | 0.227 | not confirmed |

- **Straightening is NOT confirmed on printed paper.** The straight photos were already mostly fine (3 of 22 bad as taken), so there was little to fix; the angled photos were the problem (as taken: 12 of 30 angled photos bad against 3 of 22 straight; after V2b 8 of 30 and 2 of 22) but the improvement is not significant. The frozen finder alone (V2a) finds the page on only 1 of 22 and 11 of 52 photos as taken, because these photos were taken with the phone upright; **it needs the orientation step**, a limit of the pipeline.
- **GREEN is not safe on printed paper:** after V2b, GREEN readings were wrong 2 of 19 (11%) on the primary set and 3 of 37 (8%) on all 52. The earlier statement "no bad reading got a GREEN light" (screen photos, one phone) does NOT carry over to this set.
- PR and axis on V2b (descriptive, GREEN and steady for PR): PR typical error 12.6 ms (94% within 40 ms) primary, 13.1 ms on all; axis 6.3 deg (91% within 30 deg) primary, 6.5 deg (85%) on all. PR stays consistent with the earlier 12 ms; the axis is somewhat worse.
- Limits: a different, unknown phone; WhatsApp-sent originals (full-resolution only here); uneven page coverage (H14 to H20 have 3 to 4 photos, H03 none); the photos of a page are not independent; patterned cloth background; angled photos partly cut by the frame.
- May claim: "On 22 straight full-resolution photos of printed pages taken by one other person with an unknown phone, 3 were bad as taken and 2 after straightening (not a significant change); the frozen page finder needs the phone to be held landscape or an orientation step." May NOT claim: that straightening is confirmed on printed paper; that GREEN means correct.

### 10.18 QRS and QT/QTc of the DATASET-ONLY first model on NEW data (Section AA3, 2026-11-16; `results/intervals_ml/SECTION_AA3.md`, `aa3_status.json`)
EXPLORATORY. By the user's decision (models taught only from public datasets) the model tested is attempt 1 (PTB-XL only, digitiser emulation as augmentation, frozen digitised-input offset), unchanged. Fresh data: 100 new pages L (digitised drawn pages), 100 simulated photos of L, the printed-paper photos of H2 (PRIMARY = 22 straight, SECONDARY = 52). Reference = 12SL; thresholds are the assistant's proposal, not approved by the guide.

| Test | Parameter | Typical error | Within tolerance | Bias | Slope on 12SL | All rules met |
|---|---|---|---|---|---|---|
| **L pages (100)** | **QRS** | 4.1 ms | 91% | +0.8 | 0.89 | **YES** |
| | QT | 9.9 ms | 87% | **+12.4** | 0.79 | no (bias, 90% within, short-QT tail +18.5) |
| | QTc | 10.2 ms | 90% | **+14.3** | 0.87 | no (bias) |
| L simulated photos (100) | QRS | 7.5 ms | 72% | **+11.0** | 0.81 | no |
| | QT | 17.8 ms | 67% | **+31.0** | 0.71 | no |
| **Real straight photos H2 (22)** | QRS | 8.5 ms | 100% | **+7.6** | **0.65** | **no** (bias over 5, slope) |
| | QT | 14.9 ms | 77% | +9.9 | **0.54** | **no** (within, slope, short QT +38.3) |
| | QTc | 17.6 ms | 82% | +12.8 | 0.51 | no |
| All 52 full-resolution photos | QRS / QT / QTc | 14.5 / 27.3 / 27.6 ms | 69 / 54 / 57% | +25 / +40 / +46 | 0.05 / 0.30 / 0.23 | no |

- **Verdict: none of QRS, QT or QTc is shown in the app.** QRS duration passes fresh drawn pages (4.1 ms, slope 0.89) but not simulated or real photos (positive bias +8 to +11 ms, compressed slope 0.65); QT fails even on fresh drawn pages (the digitised-input offset fitted on earlier pages did not transfer: bias +12 ms), and on photos short QT is read about 38 ms too long and long QT too short: false reassurance. The angled photos make everything worse.
- This repeats the first test's finding with new data: the dataset-trained model reads clean pages but not photos. The two fine-tuned models (which studied our photos) were dropped by decision and are not reported.
- May claim: "A network trained only on public ECG datasets read QRS duration within 4.1 ms of 12SL on 100 fresh digitised drawn pages, but not on phone photos of printed pages (bias +7.6 ms, slope 0.65), and QT not even on drawn pages; so neither is shown." May NOT claim: that QRS duration, QT or QTc can be read from a phone photo.

## 11. Heart health assessment module (the guide's request of 2026-11-15; `docs/plan/HEART_HEALTH_MODULE_PLAN.md`, `demo/health/`, `results/health/SECTION_HEALTH.md`)
EXPLORATORY. Rules were logged before training and before any label was counted on our digitised sets (`docs/plan/analysis_plan_changes.md`, "Heart health module"); one training run, one test. The pass thresholds are the assistant's proposal, **not approved by the guide**. The module reports ECG PATTERNS, never cardiac risk (no outcome data exists, so the app shows "risk assessment not available").

### 11.1 The model and the data
Small 1-D convolutional network (about 0.5 million parameters) on the page-layout input (12 leads cut to the page windows plus mask channels, 100 Hz), six labels (normal, infarction pattern MI, ST/T change STTC, conduction disturbance CD, hypertrophy HYP, atrial fibrillation or flutter AF) from PTB-XL. Trained once on folds 1 to 8 (17,104 recordings), epoch (7) and Platt calibration from fold 9 (2,142), fold-9 mean AUROC 0.926. **420 recordings that appear in any of our digitised or photo sets were removed from training** and used as the digitised tests.

### 11.2 Test results (each run once after freezing; AUROC with 95% interval; bootstrap over recordings, pages for photos)
| Class | T1 fold 10, 2,133 recordings (benchmark) | T2 drawn pages, digitised, 300 recordings | T3 straightened phone photos, 140 photos of 70 pages |
|---|---|---|---|
| Normal | 0.932 (0.922-0.942) | 0.882 (0.841-0.921) | 0.754 (0.650-0.854) |
| Infarction pattern (MI) | 0.898 (0.883-0.912) | 0.908 (0.868-0.944) | 0.857 (0.724-0.975) |
| ST/T change (STTC) | 0.917 (0.904-0.930) | 0.886 (0.846-0.922) | 0.865 (0.772-0.942) |
| Conduction disturbance (CD) | 0.908 (0.890-0.923) | 0.895 (0.839-0.943) | 0.875 (0.766-0.957) |
| Hypertrophy (HYP) | 0.882 (0.860-0.903) | **0.775 (0.689-0.850)** | **0.636 (0.481-0.778)** |
| Atrial fibrillation / flutter (AF) | 0.972 (0.956-0.984) | 0.869 (0.758-0.952), 23 positives | 0.866 (0.749-0.973), **12 positive photos: not testable** |

- Calibration error: at most 0.021 on T1 for every class (well calibrated on the benchmark); on T2 0.04 to 0.14; **on phone photos 0.076 to 0.32** (normal 0.27, hypertrophy 0.32).
- Sensitivity / specificity at the decision threshold (Youden J on fold 9), phone photos: MI 0.79 / 0.80, STTC 0.72 / 0.84, CD 0.86 / 0.76, AF 0.50 / 0.96, normal 0.36 / 0.93, HYP 0.83 / 0.37. **So on photos a "not found" misses about 14 to 28 in 100 true patterns and a "found" is wrong for 16 to 24 in 100 photos without the pattern.**
- Positives on photos are few (12 to 58), so the photo intervals are wide and the two photos of a page are not independent. Expectation written before the run: T1 0.88 to 0.94 (held, AF higher), a drop on drawn pages (held for hypertrophy and normal, others about 0 to 0.03), MI and HYP at risk on photos (MI held, HYP failed), AF untestable on photos (held).

### 11.3 What passed the pre-set rules, and what the app shows
- **Supported for drawn pages** (at least 20 positives, AUROC at least 0.80 with lower end above 0.70): normal, MI, STTC, CD, AF. **Hypertrophy fails** (lower end 0.689).
- **Supported for phone photos** (plus at least 20 positive photos and AUROC at least 0.75): normal (0.754, only just), MI, STTC, CD. AF: **not testable on photos**. Hypertrophy: fails.
- **Two decisions made after seeing the test, both only narrowing what is shown** (logged in `analysis_plan_changes.md`; the pass table above is unchanged): (1) **no percentage is shown on photos for any finding** (calibration on phone photos was worse than on the benchmark, and the guide asked for no arbitrary percentages); (2) the "normal-looking" check is not shown (it recognised only 36 in 100 normal ECGs on photos). **The app therefore shows three findings on photos: infarction pattern, ST/T change and conduction disturbance, as "found" or "not found", never as a risk or a percentage.** Hypertrophy, atrial fibrillation and normal show "not available" with the reason.
- The overall indicator is an ECG-PATTERN indicator ("possible ECG pattern found: medical evaluation advised" / "no supported abnormal pattern found" / "findings not available" / "photo not clear enough"), never Low, Moderate or High risk. Findings are shown only for a GREEN or AMBER light on a straightened photo; RED asks for a clearer photo.

### 11.4 What the app shows (parameters with status and confidence)
Heart rate (measured; confidence from the traffic light and our tested errors), RR interval (derived from the same beats), PR interval (measured only for GREEN, straightened photos with steady beat spacing; typical error about 12 ms), frontal QRS axis (GREEN, straightened; about 4 degrees), **QRS duration and QT/QTc: "Not measured", with the reason (failed our validation tests three times)**. Dashboard: risk box (always "not available"), zoomable waveform with a lead selector (seconds, mV), parameter charts with reference ranges, findings chart, and the guide's eight-part results panel. Wording rules and tests: `demo/health/wording.py`, `demo/tests/test_health.py` (13 tests pass; the 19 older wording tests pass after one sentence was made consistent with the new tab).

- **Likelihood graph (added 2026-11-15, user request "how much is the risk"):** graph D now shows, per supported ECG pattern, how likely it is on this ECG, with bands (unlikely, possible, likely). It is a PATTERN likelihood, never cardiac risk. Numbers appear only for a finding whose calibration passed the fresh-photo test of the second model (`results/health/findings_status_v2.json`, not yet run); until then the bars carry no number. The risk box stays "not available" and says what is shown instead.

### 11.5 End-to-end check on the six demo photos (`results/health/demo_samples_check.md`; descriptive, 6 photos)
Normal source: no pattern found. Left bundle branch block source: conduction found. Right bundle branch block plus ST changes source: conduction and ST/T found, plus an infarction pattern that the source label does not carry (a false alarm). Hypertrophy source (with a low-likelihood old infarction): three patterns found, the extra ones not verifiable from the label. Blurry photo: RED, "please send a clearer photo". Hypertrophy-labelled sources get no hypertrophy answer because that check failed. All texts passed the wording checker.

### 11.6 Limits and what may be claimed
- May claim: "A small convolutional network trained on public hospital ECGs found infarction, ST/T and conduction patterns with AUROC 0.86 to 0.88 on straightened phone photos of drawn pages (about 28 to 50 positive photos each), 0.89 to 0.91 on digitised drawn pages and 0.90 to 0.92 on the benchmark; hypertrophy and atrial fibrillation could not be shown to work on photos and are not shown."
- May NOT claim: a diagnosis; cardiac risk or risk categories; that a "not found" result means the ECG is normal (14 to 28 in 100 patterns are missed on photos); probabilities on photos; that it works on printed paper, other phones or other layouts (one phone, one screen, drawn pages); that the pass thresholds are a standard.
- Other limits: labels are PTB-XL's cardiologist and algorithm labels, not our own review; 70 recordings behind the photo results; false-alarm rate 16 to 24 in 100 on photos; the model saw hospital ECGs from one source.
- Not done: a printed-paper test of the module; hypertrophy and atrial fibrillation on photos would need more labelled photos; the guide has not approved the rules.

### 10.16 Learned QRS duration and QT/QTc (Section AA, 2026-11-15; `results/intervals_ml/SECTION_AA.md`, `aa_test_metrics.csv`, `aa_test_per_item.csv`, `aa_status.json`)
EXPLORATORY. Rules logged before any code ran (`docs/plan/analysis_plan_changes.md`, "Section AA"); a neural network trained once on PTB-XL folds 1 to 8 (12SL labels; every recording of any digitised, photo or sealed set removed), digitiser emulation in training (fixed, not fitted), one offset per target fitted on 200 development pages, no slope fitted. Tested ONCE on: sealed K pages (100 new recordings, the primary), sealed G pages (100, used before for other methods), 140 straightened phone photos (used before for other methods; the model was never tuned on them). The thresholds are the assistant's proposal, **not approved by the guide**.

| Test | Parameter | Typical error | Within tolerance | Bias (95% interval) | Slope on 12SL | Tails | All rules met |
|---|---|---|---|---|---|---|---|
| Fold 10 originals (2,114) | QRS | 3.8 ms | 99% | +0.2 | 0.93 | wide QRS -0.7 ms | yes |
| | QT | 6.7 ms | 98% | -0.4 | 0.88 | long QT -10.9, short QT +6.9 | yes |
| | QTc | 7.1 ms | 98% | -0.1 | **0.73** | | no (slope) |
| **K pages, primary (100)** | **QRS** | **6.4 ms** | **92%** | **-2.1 (-4.1 to +0.2)** | **0.92 (0.83-1.00)** | wide QRS (33) -3.6 | **YES** |
| | QT | 13.1 ms | **87% (needs 90%)** | -2.8 (-8.2 to +3.2) | 0.83 (0.69-0.98) | long QT (23) -13.5, short (15) +6.0 | **no** (only the 90% within 40 ms missed, by 3 points) |
| | QTc | 14.6 ms | 90% | -2.0 | **0.70** (0.56-0.86) | | no (slope) |
| G pages (100) | QRS | 4.2 ms | 96% | -1.3 | 0.87 | wide QRS (11) -7.2 | YES |
| | QT | 9.5 ms | 92% | -1.1 | 0.87 | long QT (9) -22.1, short (11) +4.2 | YES |
| | QTc | 9.7 ms | 94% | -0.2 | 0.77 | | no (slope) |
| **Phone photos (140)** | **QRS** | 4.7 ms | 91% | +3.3 (+0.2 to +5.9) | **0.65 (0.56-0.81)** | wide QRS (14) -14.1 | **no** (slope) |
| | **QT** | 13.1 ms | **75%** | **+11.2 (+1.5 to +20.8)** | **0.50 (0.27-0.81)** | long QT (12) **-44.6**, short (14) **+43.3** | **no** (within, bias, slope, tails) |
| | QTc | 12.9 ms | 78% | **+13.9** | **0.23** | | no |

- **Verdict: none of the three is shown in the app.** QRS duration passes on both sets of drawn pages and fails on phone photos only on the slope (0.65 against 0.8: the photo read-out compresses toward the middle, wide QRS read about 14 ms short). QT misses the primary test by 3 points on one criterion (87% within 40 ms against 90%) and fails clearly on photos (compressed to a slope of 0.50: long QT read 45 ms short, short QT 43 ms long, so false reassurance for long QT). QTc fails because its slope is low even on original signals (0.73): the 12SL QTc correction behaves differently from the Fridericia formula applied to our heart rate.
- Atrial fibrillation pages on K: QRS -4.2 ms, QT +2.5 ms (10 pages), so no AF guard was triggered on drawn pages; on photos AF QT was +27.6 ms (12 photos).
- **What this shows:** a learned model removes the compression on drawn pages (QT slope 0.83 to 0.88, against 0.61 to 0.69 for the hand-made methods) and QRS reaches 4 to 6 ms typical error; **what remains is the phone photo**: the photo read-out loses amplitude and detail in ways our digitiser emulation (pixel grid, smoothing, gain, noise) did not capture.
- No second training run was done to improve a number (stop rule). Limits: 12SL is an algorithm; photos are of one phone and one screen and were used before by earlier methods; thresholds not approved by the guide.
- May claim: "A neural network read QRS duration within 6.4 ms (92% within 20 ms) and QT within 13.1 ms (slope 0.83) of 12SL on 100 fresh digitised drawn pages, but on phone photos the slope fell to 0.65 and 0.50, so neither is shown." May NOT claim: that QRS duration, QT or QTc can be read from a phone photo.

## Changes after the freeze
- 2026-11-16: added sections 10.17 (printed-paper photos, friend's phone: straightening NOT confirmed; GREEN not safe) and 10.18 (dataset-only QRS/QT/QTc on fresh data: nothing shown). Nothing earlier changed.
- 2026-11-15 (evening): added section 10.16 (learned QRS duration and QT/QTc: passes drawn pages for QRS, fails phone photos; nothing shown). Nothing earlier changed.
- 2026-11-15: added section 11 (heart health assessment module: ECG-pattern findings model, tests, what the app shows). Nothing earlier changed.
- 2026-11-14 (late night): added sections 10.12 (risk-coverage, with the 40 new photos and the 120 simulated photos added in Amendment 1), 10.13 (cluster intervals and Bland-Altman), 10.14 (failure gallery, 10 cards) and 10.15 (reproducibility package, tested in a clean environment). Nothing earlier changed.
- 2026-11-14 (evening): added section 10.11 (simulated-photo test: straightening confirmed in simulation, 64 to 21 of 120; 1 bad GREEN). Nothing earlier changed.
- 2026-11-14 (late afternoon): added section 10.10 (P and T wave amplitude: T stopped in development; P passes on pages, fails the photo confirmation). Nothing earlier changed.
- 2026-11-14 (afternoon): added section 10.9 (QRS third attempt: not validated; QT not tested). Nothing earlier changed.
- 2026-11-14 (night): added sections 10.7 (QRS and QT on fresh data: QT not validated, QRS not validated) and 10.8 (axis validated for straightened photos). Nothing in sections 1 to 10.6 changed.
- 2026-11-14 (later): added section 10.6 (PR and QRS with my own method). Section 10.3 is superseded for PR by 10.6 and for QT by 10.5.
- 2026-11-13: added section 10 (new exploratory analyses and the dataset inventory). No number in sections 1 to 9 changed.
- 2026-11-14: added section 10.5 (better QT method, held-out test and confirmation). Section 10.3 (NeuroKit2 intervals) stays as written; its consequence line is superseded for QT only by 10.5.

### 10.19 ECG-estimated 1-year mortality risk pilot on CODE-15% (Section RISK, 2026-11-16; `results/risk_pilot/SECTION_RISK_h1.md`, `risk_status_h1.json`)
EXPLORATORY pilot, rules logged before training. Data: parts 0 to 5, 31,718 patients with a 10 s ECG and an outcome (1,134 deaths); patient-level split 70/10/20 by hash; test = 6,188 patients, 82 deaths within 1 year; tested once. Trained on public data only. Pass rules and categories are the assistant's proposal, not approved by the guide.

| Item | Result |
|---|---|
| ECG model AUROC on test | 0.713 (95% 0.653 to 0.770); rule needed 0.75 and lower end above 0.70: **FAIL** |
| Age alone / age + sex | 0.799 / 0.797 (the ECG model is worse than age alone) |
| Calibration | slope 0.62 (needs 0.8 to 1.25): **FAIL**; ECE 0.0057 (ok) |
| Categories Low / Moderate / High | observed 0.63% / 1.08% / 4.10% (increasing, High is 6.5 times Low): pass; the model over-predicts Moderate and High |
| Transfer, drawn pages (original vs digitised) | Spearman 0.88 to 0.98, same category 85 to 88%: pass |
| Transfer, simulated photos | Spearman 0.53 to 0.67, same category 58 to 75%: fail |
| Transfer, REAL straight printed-paper photos (22) | Spearman 0.43, same category 59%: **FAIL** |
| **Shown in the app** | **NO** |

- Verdict: the risk graph is NOT shown. The model does not beat age, is over-confident, and its risk number changes too much between a clean signal and a phone photo.
- Note: the fresh M group had only 59 pages digitised when the test ran (the GPU queue was still running).
- May claim: "A 1-year mortality-risk model trained only on open CODE-15% data reached AUROC 0.71 on 6,188 held-out patients, below age alone (0.80), and did not transfer to phone photos, so no risk number is shown." May NOT claim: that a risk percentage can be given from a phone photo of an ECG.

### 10.20 Printed-paper photos H2, recompressed WhatsApp copies (separate secondary set; Section H2 compressed, 2026-11-16; `results/analysis/SECTION_H2_compressed.md`)
EXPLORATORY, run once, never pooled with 10.17. 66 photos, 20 pages. Frozen finder as taken finds the page on 14 of 66. Bad as taken (V0) 31 of 66; after the orientation step + finder (V2b) 15 of 66; newly bad 2, newly good 18, exact paired p = 0.0004: **straightening confirmed on this set** (angled 24 to 12 of 39 bad, straight 7 to 3 of 27). GREEN after V2b: wrong 1 of 35 (3%); AMBER 8 of 19 bad; RED 6 of 12. PR (GREEN) typical error 9.6 ms, 100% within 40 ms; axis 6.2 deg, 84% within 30 deg.
- Reading with 10.17: the full-resolution set (22 straight photos, few bad to begin with) did NOT confirm it; the compressed set (more photos, more angled and more bad at the start) does. Both are one friend's phone; the photos of a page are not independent. May claim: "On 66 recompressed photos of printed pages, straightening cut bad readings from 31 to 15 (p = 0.0004)." May NOT claim: that this holds for full-resolution straight photos (not confirmed) or for other phones.

### 10.21 ECG + age 5-year mortality-risk pilot 2 on CODE-15% (Section RISK2, 2026-11-16; `results/risk_pilot2/SECTION_RISK2_h5.md`, `risk_status_h5.json`)
EXPLORATORY pilot 2, rules logged before the download and before training (`analysis_plan_changes.md`, "RISK PILOT 2"); a second model made after pilot 1 failed, by the user's decision. Data: parts 0 to 17, 87,371 patients with a 10 s ECG and an outcome (3,079 deaths). Train 13,330 patients (2,081 deaths within 5 years), validation 1,991 (302), best epoch 11, validation AUROC 0.814. **Sealed test (patients of parts 6 to 17, never used before): 2,323 patients, 365 deaths within 5 years**, tested once. Only people with a complete 5-year follow-up are counted, so observed rates are higher than a population risk. Thresholds and categories are the assistant's proposal, not approved by the guide.

| Item | Result |
|---|---|
| ECG + age AUROC | **0.833 (0.810 to 0.854)**; rule 0.80 with lower end above 0.75: PASS |
| Age alone / age + sex | 0.819 (0.798 to 0.840) / 0.828 (0.807 to 0.849) |
| **Added value of the ECG over age alone (paired)** | **+0.013 (-0.005 to +0.032): NOT shown** (interval includes 0): FAIL |
| Calibration | slope 1.18, ECE 0.0179: PASS |
| Categories Low (<5%) / Moderate / High (>=15%) | observed 1.65% / 7.25% / 34.72%; predicted 2.58% / 9.14% / 32.65%: PASS |
| Transfer FULL (age entered), drawn pages | Spearman 0.84 to 0.98, same category 93 to 98%; fresh L is 0.84 (needs 0.85): FAIL by 0.01 |
| Transfer FULL, simulated photos | Spearman 0.43 to 0.75, same category 73 to 83%: FAIL |
| Transfer FULL, 22 REAL straight printed photos | Spearman 0.95, same category 100%: PASS |
| Transfer ECG-ONLY (age fixed), real photos | Spearman 0.89, same category 86% (simulated photos 0.35 to 0.69) |
| **Shown in the app** | **NO** (4 of 7 rules failed: ECG adds no significant value, drawn pages by 0.01, simulated photos) |

- Reading: with age in the model the AUROC (0.833) and calibration are good, but **the ECG contributes only about +0.013 AUROC over age alone, not significant**; the number is mostly the age the user enters. The ECG helps inside age bands (50 to 69: 0.703 against 0.607 for age alone; 70 and over: 0.698 against 0.610), but those are wide, post hoc readings and not a pass rule. The risk of simulated photos moves too much (the hardest simulated set M: Spearman 0.43).
- Stop rule Wed 18 Nov: no third risk model. Reported as a negative result: no risk number or graph is shown.
- May claim: "With age as an input, a network trained on CODE-15% reached AUROC 0.83 for death within 5 years on 2,323 sealed patients, but age alone reached 0.82 and the ECG added +0.013 (not significant), and the risk was not stable on simulated photos, so no risk is shown." May NOT claim: that the ECG adds risk information beyond age; that a risk percentage can be given from a phone photo; that this is cardiac risk.

### 10.22 More disease findings: model A (PTB-XL fine labels) and model B (CODE-15% labels) (Section FIND2, 2026-11-16; `results/find2_A/SECTION_FIND2_A.md`, `results/find2_B/SECTION_FIND2_B.md`, `status.json`)
EXPLORATORY. Rules logged before any training (`analysis_plan_changes.md`, "MORE DISEASE FINDINGS" and Amendment 1); public data only; each model trained once, tested once, on the same drawn pages (T2, 300) and straightened screen photos (T3, 140) as the first findings model. Pass rules as the first findings model (proposal, not approved by the guide): at least 20 positives, AUROC at least 0.80 with lower end above 0.70 on T2; for photos also at least 20 positive photos and AUROC at least 0.75.

**Model A: 16 PTB-XL codes** (trained on 17,104 recordings; best epoch 10, validation mean AUROC 0.933; benchmark = fold 10, 2,133 recordings). Benchmark AUROC: 0.74 (non-specific conduction delay IVCD) to 0.998 (complete right and left bundle branch block); LAFB 0.982, IRBBB 0.967, PVC 0.968, 1AVB 0.945, ISCAL 0.918, NST_ 0.833, LAO/LAE 0.804.
- **Supported on drawn pages (5):** anteroseptal infarction ASMI 0.930 (0.870-0.975, 34 positives), non-diagnostic T abnormality NDT 0.850 (0.753-0.928, 25), left ventricular hypertrophy LVH 0.922 (0.875-0.961, 21), left anterior fascicular block LAFB 0.929 (0.832-0.990, 25), incomplete right bundle branch block IRBBB 0.946 (0.890-0.982, 22).
- **Not testable on drawn pages** (fewer than 20 positives of 300): IMI 15, ISC_ 11, PVC 15, 1AVB 12, IVCD 11, ISCAL 7, NST_ 8, CRBBB 8, CLBBB 2, ILMI 4, LAO/LAE 10 (their AUROCs are descriptive only; IVCD 0.757, NST_ 0.783, LAO/LAE 0.734, CLBBB 0.721 are weak).
- **On phone photos: NONE of the 16 is testable** (at most 16 positive photos, rule needs 20; CRBBB has 0). Descriptive only: LVH 0.836 (16 positives), IMI 0.937 (12), LAFB 0.921 (10), NDT 0.708 (12).
- Reading: hypertrophy that failed in the first model as a whole class (HYP, mixed labels) passes on drawn pages when only left ventricular hypertrophy (LVH) is asked.

**Model B: 6 CODE-15% labels** (92,381 training exams of 132,040 with a 10 s recording; 2,100 to 3,100 positives each; best epoch 7, validation mean AUROC 0.987; benchmark = test split of 26,346 exams, bucket >= 80). Benchmark AUROC (calibration error at most 0.004): 1dAVb 0.978 (0.974-0.982), RBBB 0.989 (0.986-0.991), LBBB 0.995 (0.994-0.996), slow heart rate SB 0.990, fast heart rate ST 0.992, AF 0.980 (0.973-0.986).
- **Supported on drawn pages (1):** AF 0.919 (0.814-0.994, 23 positives). **RBBB FAILS** (0.709, 0.592-0.822, 30 positives; the PTB-XL mapping CRBBB or IRBBB may not match the CODE-15% label: a possible label mismatch, not tested further). **Not testable** (under 20 positives): 1dAVb 12 (0.926), LBBB 2 (0.856), SB 16 (0.976), ST 12 (0.931).
- **On phone photos none is testable** (4 to 12 positives). Descriptive: AF 0.987 (0.966-1.000, 12 positives), LBBB 0.987 (4), ST 1.000 (4), 1dAVb 1.000 (4), RBBB 0.602 (8), SB 0.689 (6). Fewer than 20 positives: no claim.
- Same-condition rule (1AVB/1dAVb, CLBBB/LBBB): both pairs are untestable, so nothing was chosen between the models.

- **What this means:** the new models are very good on their own benchmarks (CODE-15% 0.98 to 0.995), but our 300 drawn pages and 140 photos hold too few positives for most of these findings (they are mostly of normal and common recordings), so most cannot be tested on our own pages or photos at all. **No new finding is supported for phone photos.** Five findings of model A (ASMI, NDT, LVH, LAFB, IRBBB) and AF of model B pass for drawn pages.
- **Not done (be honest):** the app does not use models A or B yet; a test on photos needs at least 20 positive photos per finding (a new photo set with enriched positives, which would need new recordings and photos).
- May claim: "A network trained on 132,040 CODE-15% exams found six rhythm and conduction findings with AUROC 0.98 to 0.995 on 26,346 held-out exams; on our 300 digitised drawn pages only atrial fibrillation could be confirmed (0.919); the others, and all findings on phone photos, had too few positives to test." May NOT claim: that any of these findings is validated on phone photos; that right bundle branch block works on our pages (it failed, 0.709).

### 10.23 First findings model (PTB-XL only) on NEW fresh data (Section HEALTH3, 2026-11-16; `results/health/SECTION_HEALTH3.md`, `health3_test_metrics.csv`, `findings_status_v3.json`)
EXPLORATORY, run ONCE after freezing, rules logged before (`analysis_plan_changes.md`, 2026-11-15 night + Amendment 1; user decisions: dataset-only, straight photos primary). Model unchanged (trained on PTB-XL only; Platt and thresholds from fold 9). Fresh sets never used before: L and M drawn pages (200 recordings), their simulated photos (200), and the 22 real STRAIGHT printed-paper photos of H2 (18 pages; secondary: all 52 full-resolution photos). Pass rules (proposal, not approved by the guide): drawn = pooled L+M pages, at least 20 positives, AUROC >= 0.80, lower end > 0.70; photos = that, plus pooled photos with at least 20 positives and AUROC >= 0.75, and real H2 straight photos AUROC >= 0.70.

| Finding | Pooled fresh pages (200) | Pooled fresh photos (222) | Real straight printed photos H2 (22; positives) | Supported (pages / photos) |
|---|---|---|---|---|
| Normal | 0.916 (0.860-0.959) | 0.774 | 0.914 (7) | yes / **yes** |
| MI | 0.940 (0.907-0.969) | 0.809 | 0.765 (5) | yes / **yes** |
| ST/T (STTC) | 0.924 (0.881-0.959) | 0.839 | 0.802 (6) | yes / **yes** |
| Conduction (CD) | 0.922 (0.876-0.959) | 0.758 | **0.424 (5; 0.167-0.500)** | yes / **NO** |
| Hypertrophy (HYP) | **0.749 (0.677-0.818)** | 0.738 | 0.776 (5) | **no** / no |
| AF | 0.932 (0.873-0.974) | 0.781 | no positives | yes / no (not testable on real photos) |

- L pages alone: NORM 0.956, MI 0.938, STTC 0.942, CD 0.926, HYP 0.703, AF 0.934; M pages: 0.868, 0.943, 0.903, 0.919, 0.792, 0.936. Simulated photos (L, M): MI 0.789-0.840, STTC 0.835-0.848, CD 0.771-0.790. Calibration error on photos 0.05 to 0.35 (no percentage allowed for any finding).
- **What changes: conduction disturbance (CD) fails the pre-set rule for phone photos** because on the 22 real printed-paper photos its AUROC was 0.424 (only 5 positives; the interval 0.167 to 0.500 is wide and tiny, but the rule was fixed before the photos). Infarction pattern (0.765, 5 positives) and ST/T (0.802, 6 positives) stay supported, also with very few positives. Hypertrophy still fails (0.749 on drawn pages). AF passes for drawn pages (0.932) but cannot be tested on real photos (no positive).
- **The earlier claim (10.11 in section 11.6) that conduction is found on phone photos (0.875 on screen photos) does not hold on printed paper**; it stays true only for screen photos of one phone. The app still shows CD on photos; by the rule it should not (see changes).
- Limits: the real printed-paper subset has 5 to 7 positives per finding, so every interval is wide; one other phone; photos of one page are not independent; simulated photos are a script.
- May claim: "On 200 new drawn pages the pattern network found infarction, ST/T, conduction and atrial fibrillation with AUROC 0.92 to 0.94; on photos it held for infarction and ST/T (0.81 and 0.84 pooled), but conduction failed on 22 real printed-paper photos (0.42, 5 positives)." May NOT claim: that conduction patterns are found on printed-paper photos; any percentage on photos.

### 10.24 Models A and B in the demo (2026-11-16 afternoon; `demo/health/assess.py` `extra_findings`, `dashboard.py` `extra_table`, `wording.py` EXTRA_NAMES)
By the user's decision the two public-data networks were added to the demo as a SEPARATE block "Extra patterns (research only)". Only findings that passed on clean drawn pages are included (A: anteroseptal infarction, non-specific T-wave change, left ventricular hypertrophy, left anterior fascicular block, incomplete right bundle branch block; B: atrial fibrillation). None could be tested on phone photos (fewer than 20 positive photos), so: shown only for a GREEN or AMBER straightened photo; found / not found only, no percentage; never part of the main indicator; the block carries the note and the drawn-page AUROC and positive count. Checks: demo tests 16 (health) + 19 (explanation) pass; the app's extra results equal the saved test predictions on 72 results from 12 drawn pages (0 mismatches); a RED light or an unstraightened page gives no extra patterns; run once in the live app on one example photo (GREEN; block shown, wording checker clean). Descriptive only: no claim that these patterns are validated for photos.

### 10.25 False-alarm load of the six extra patterns together (POST HOC, 2026-11-16 night; script `scratchpad` check, numbers from `results/find2_A/predictions_T2.csv`, `results/find2_B/predictions_T2.csv`)
POST HOC, found while reviewing the app output (not a pre-set rule). On the 300 clean digitised drawn pages (T2), with the frozen thresholds of networks A and B and the six extra patterns the app shows (ASMI, NDT, LVH, LAFB, IRBBB from A; AF from B): of the **183 pages with none of the six patterns, 81 (44%) had at least one extra pattern flagged** (0.64 flagged patterns per such page on average); of the **117 pages with at least one of the six, 116 (99%) had at least one flagged**. Each pattern alone wrongly flags 9 to 18 in 100 pages without it (specificity 0.82 to 0.91). The pages are the ones used in the test of each network; this is a descriptive number, not a new test.
- Consequence (done in the app, report and paper): a flagged extra pattern is shown only as a hint ("research only"), the note under the table says about 4 in 10 pages without any of the patterns still have one flagged, and the six patterns never change the main indicator.
- May claim: "The six extra patterns together flagged at least one pattern on 44% of clean pages that had none." May NOT claim: that a single flagged extra pattern means the pattern is present.

### 10.26 Positive-rich set N: networks A and B tested once on drawn pages and simulated photos (Section N, 2026-11-16 evening; `results/paper_n/SECTION_N.md`, `N_status.json`, `test_pages_metrics.csv`, `test_sim_metrics.csv`)
EXPLORATORY. Rules logged before the recordings were selected (`analysis_plan_changes.md`, "POSITIVE-RICH SET N"). 120 PTB-XL fold-10 recordings (positives per finding: AF 30, RBBB-type 29, LBBB 22, 1AVB 23, LVH 24, LAFB 35), pages drawn, digitised, and one simulated photo per page; frozen networks A and B, frozen thresholds; AUROC with a bootstrap over pages. **REAL photos were NOT provided, so the real-photo part is not done** (60 pages / 120 photos of the real-photo subset were prepared: `results/paper_n/photo_session/`).

| Pair | Drawn pages (AUROC, 95% lower) | Simulated photos | Sensitivity / specificity (pages; simulated) | Verdict |
|---|---|---|---|---|
| LVH (A) | 0.896 (0.837) pass | 0.727 **fails** | 67 / 88; 62 / 66 | passes pages, fails simulated: stays research-only |
| LAFB (A) | 0.928 (0.859) pass | 0.795 pass | 91 / 85; 71 / 88 | stays research-only (no real photos) |
| 1AVB (A) | 0.754 (0.640) **fails** | 0.707 fails | 74 / 56; 70 / 68 | fails; model B does better |
| CLBBB (A) | 0.997 (0.990) pass | 0.807 pass | 100 / 79; 77 / 80 | model B (LBBB) kept for this condition |
| AF (B) | 0.921 (0.845) pass | 0.804 pass | 93 / 77; 77 / 79 | stays research-only |
| RBBB (B) | 0.732 (0.591) **fails** | 0.575 fails | 59 / 91; 41 / 82 | fails, not shown |
| LBBB (B) | 0.976 (0.952) pass | 0.819 pass | 100 / 84; 77 / 87 | research-only (added to the block) |
| 1dAVb (B) | 0.877 (0.804) pass | 0.789 pass | 100 / 44; 87 / 43 | research-only (added), **but wrongly flags 56 to 57 in 100 pages without it** |

- **Nothing is promoted to the main findings list** (the rule needs real photos with at least 20 positives and AUROC at least 0.75). Two findings (LBBB and first-degree AV block, both from network B) were ADDED to the research-only block because they passed drawn pages and simulated photos; first-degree AV block from A and right bundle branch block from B failed on drawn pages and are not shown.
- **POST HOC (computed after seeing the app output; script `scratchpad/fa8.py` logic, predictions of the earlier tests):** with the eight patterns of the research-only block together (ASMI, NDT, LVH, LAFB, IRBBB, AF, LBBB, 1dAVb), of the **176 drawn pages (T2) with none of them 86 (49%) had at least one flagged**, and of the **88 real straightened phone photos (T3) with none of them 63 (72%)** (1.38 flags per such photo); of the pages and photos WITH one of the patterns 123 of 124 and 51 of 52 had at least one flagged. The block is therefore a weak hint and is collapsed by default in the app, with this stated in the note.
- May claim: "Six of eight network-and-finding pairs met the pre-set rule on 120 positive-rich drawn pages and five on simulated photos; no real photos of this set were available." May NOT claim: that any of these findings is validated on real phone photos; that a flagged research-only pattern is present (72% of photos without any of the patterns also got a flag).

### 10.27 New operating point for the research-only patterns (2026-11-16 late night; `results/find2_op/SECTION_OP.md`, `op_aggregate.csv`, `op7_aggregate.csv`, `thresholds_v2.json`, `app_operating_point.json`; rules in `analysis_plan_changes.md`)
EXPLORATORY, partly POST HOC. Thresholds of the 8 patterns were re-derived from VALIDATION data only (network A: PTB-XL fold 9 without our digitised recordings; network B: CODE-15% validation split) so that specificity there is 0.97 (sensitivity analysis 0.95 and 0.99). Models, calibration and training unchanged. The sets below were seen before, so this is NOT a new confirmatory test.

| Set | Share of CLEAN items (none of the patterns) with at least one flag | Items WITH a pattern flagged |
|---|---|---|
| T2, 300 drawn pages, 8 patterns, old thresholds | 86 of 176 (49%) | 123 of 124 (99%) |
| T2, 8 patterns, new thresholds (0.97) | 34 of 176 (19%) | 93 of 124 (75%) |
| T3, 140 screen photos, 8 patterns, old | 63 of 88 (72%) | 51 of 52 (98%) |
| T3, 8 patterns, new (0.97) | 26 of 88 (30%) | 40 of 52 (77%) |
| T2, **7 patterns (NDT dropped), new (used in the app)** | **34 of 194 (17.5%)** | 90 of 106 (85%) |
| T3, **7 patterns, new (used in the app)** | **24 of 94 (25.5%)** | 40 of 46 (87%) |

- Sensitivity at the new thresholds on T2 (old in brackets): ASMI 82 (94), NDT **16 (80)**, LVH 67 (81), LAFB 72 (92), IRBBB 50 (91), AF 91 (91), LBBB 50 of 2 positives (50), 1dAVb 50 (100); specificity rises to 92 to 98. On set N drawn pages (app numbers): LVH 46, LAFB 57, 1dAVb 65, AF 87, LBBB 100; simulated photos: LVH 46, LAFB 40, 1dAVb 70, AF 70, LBBB 77 (false alarms 4 to 27 in 100).
- **My rule was NOT met** (no pattern may lose more than half of its sensitivity on drawn pages: NDT lost 80%, 1dAVb exactly half). **Decision of the user: use the new thresholds and DROP NDT: a POST HOC exception, logged.** The app block has 7 patterns (ASMI, LVH, LAFB, IRBBB, AF, LBBB, 1dAVb) with the numbers above in each note.
- Supersedes the 49% and 72% quoted in 10.25 and 10.26 for the APP (those remain true for the first thresholds). Expectation written before: 20 to 35% (drawn) and 40 to 55% (photos): the photo result (25 to 30%) was better than expected.
- May claim: "Thresholds set on validation data only cut the share of clean items with a flag from 43% to 18% (drawn pages) and from 63% to 26% (screen photos) for the 7 remaining patterns, at the cost of sensitivity (exploratory, post hoc)." May NOT claim: that a flagged pattern is present; that the thresholds were confirmed on new data.

## 10.28 Set P: fresh positive-rich dataset pictures (2026-11-17; frozen networks A and B, frozen 0.97 thresholds; results/paper_p/SECTION_P.md)
- 266 pictures (PTB-XL fold 10, never used before): 40 AF, 40 RBBB-type, 26 LBBB, 40 1AVB, 40 LVH, 40 LAFB, 40 normal; one drawn page and one simulated phone photo each. Rules logged before selection (analysis_plan_changes.md).
- Drawn pages, AUROC (lower 95%) and sensitivity/specificity: LVH 0.897 (0.856) 57/91; LAFB 0.908 (0.840) 61/97; IRBBB 0.967 (0.940) 68/98; AF 0.934 (0.877) 92/86; LBBB 0.984 (0.965) 96/90; 1dAVb 0.906 (0.860) 67/93. All six pass the drawn-page rule. Normal pages with at least one flag: 6 of 40.
- Simulated photos: LVH 0.669, 52/65; LAFB 0.775, 46/96; IRBBB 0.715, 35/98; AF 0.756 (0.646), 70/85; LBBB 0.854 (0.744), 78/86; 1dAVb 0.719, 61/83. Normal photos with at least one flag: 19 of 40 (48%).
- **VERDICT: no pair met the "available" rule (AUROC at least 0.75 and sensitivity at least 0.60 and specificity at least 0.90 on simulated photos).** AF and LBBB came closest (specificity 85 and 86). All six stay research-only in the app. Expectation written before (AF, LBBB, LAFB pass) was wrong.
- May claim: "On drawn pages the six extra patterns were found with AUROC 0.90 to 0.98 on a fresh set; on simulated phone photos they fell to 0.67 to 0.85 and none met our rule." Must not claim: any of these patterns is validated for phone photos. The false-alarm rate on clean simulated photos on set P (48%) is higher than on set N (26%): quote 3 to 5 in 10.

## 10.29 QT and QRS retry on doctor-marked public data (2026-11-17; results/qt_public/)
- Data: LUDB (200 recordings, 12 leads, doctor marks) and QT Database (105 recordings). Train LUDB 1-140 + QT Database windows (148); validation LUDB 141-160; test LUDB 161-200 (40 records), run once.
- T1 (doctor marks): QT typical error 11 to 12 ms, bias -0.6 to +1.6 ms, slope 1.03 to 1.10, 97.5% within 40 ms, clean and damaged: passes all QT rules. QRS typical error 8 ms, bias -4 to -6 ms, slope 0.60 to 0.72: fails.
- T2 on set P against machine values: drawn pages QT error 40 ms, bias +32 ms, slope 0.84; simulated photos QT error 66 ms, bias +14 ms, slope 0.61, 46% within 40 ms; QRS error 38 ms (pages) and 79 ms (photos). **FAILS: QT and QRS stay "not measured".** Reason not tested separately: definition gap to the machine values plus digitiser output.
- May claim: "A model trained on doctor-marked public data measured QT within about 12 ms on held-out recordings, with and without photo-style damage, but did not meet our rules on digitised dataset pictures, so QT is still not shown." Must not claim QT is validated.

## 10.30 Set Q: retrained networks A2/B2 on a fresh set (2026-11-17; results/paper_q/SECTION_Q.md; rules in analysis_plan_changes.md before retraining)
- Retraining with strong photo-style damage; thresholds (specificity 0.97) from damaged validation data only. Set Q: 160 pictures (40 AF, 40 LAFB, 40 normal from fold 10; 40 LBBB from folds 1-9, fresh for network B only). One drawn page and one simulated photo each; tested once.
- **B2:LBBB passes the rule written beforehand: AVAILABLE.** Drawn pages: AUROC 0.987 (lower 0.971), sensitivity 100%, specificity 91%. Simulated photos: AUROC 0.841 (lower 0.739), sensitivity 72%, specificity 92%. 40 positives.
- B2:AF fails by 0.7 points of specificity (photos: AUROC 0.836, 79/89; drawn pages 0.980, 96/85). A2:LAFB fails on photo sensitivity (0.754, 43/99; drawn pages 0.967, 83/99; fold-10 pictures only, 42 positives).
- First networks on the same pictures (descriptive): LBBB 0.987 / 0.809, sensitivity 75, specificity 84 on photos (the retraining helped); AF 0.975 / 0.835; LAFB 0.948 / 0.758.
- Normal pictures flagged by at least one of the three: 0 of 40 (pages), 1 of 39 (photos).
- May claim: "Left bundle branch block was validated on dataset pictures (fresh set of 160, simulated phone photos: AUROC 0.84, sensitivity 72%, specificity 92%); it is not validated on real phone photos." Must not claim: LBBB works on real photos; AF or LAFB are validated; the result is guide-approved.
- Caution: one of three pairs passed; the lower interval end on photos (0.739) is close to the line (0.75) and there are only 40 positives; the true rate of such a pass by chance is not small.

## 10.31 Set R: replication of B2 on a new fresh set (2026-11-17 night; results/paper_r/SECTION_R.md, POOLED_QR.md, final_status.json; rules logged before selection)
- Set R: 120 new pictures (41 LBBB, 48 AF, 40 normal), never used before; drawn page and one simulated photo each; B2 frozen; tested once.
- **LBBB passes again:** drawn pages AUROC 0.960, 93/95; simulated photos AUROC 0.814 (lower 0.701), sensitivity 66, specificity 94.
- **AF passes (second test; it had missed on set Q by 0.7 points):** drawn pages 0.988, 98/90; simulated photos AUROC 0.835 (lower 0.740), sensitivity 71, specificity 93.
- Normal pictures flagged: 0 of 40 on pages, 0 of 40 on photos.
- Pooled over Q and R (descriptive): LBBB photos AUROC 0.825, 69/92 (81 positives), drawn pages 0.971; AF photos AUROC 0.835, 75/91 (95 positives), drawn pages 0.982, 97/87.
- May claim: "Left bundle branch block and atrial fibrillation passed our pre-set rules on fresh dataset pictures (drawn pages and simulated phone photos; photos: AUROC 0.83, about 70 in 100 found, 8 to 9 in 100 false alarms); they are not validated on real phone photos. AF passed on its second test after missing the specificity rule by 0.7 points on the first." Must not claim: they work on real phone photos; the rules are guide-approved; AF passed at the first attempt.
- Still research-only: LAFB (failed sensitivity on Q), 1dAVb, LVH, IRBBB, ASMI.
