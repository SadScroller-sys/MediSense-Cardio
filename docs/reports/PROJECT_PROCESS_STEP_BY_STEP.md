# MediSense-Cardio: the whole process, step by step

Source: `results/FINAL_NUMBERS.md`, `docs/reports/METHODS_AND_FORMULAE.md`, `docs/reports/CODE_MAP.md`, `docs/plan/EXPLANATION_WORDING.md`, `docs/plan/HEART_HEALTH_MODULE_PLAN.md`, and the code (`scripts/`, `safeguard/`, `demo/`).
Nothing here is new. Where a detail is not written in those files (for example the layers of a neural network), this page says so instead of guessing.

Every process below has the same parts: **Purpose, Input, Steps, Output, Rule and verdict, Code.**

Words used in the whole project
- **Wrong reading:** the digitizer gave a heart rate, but it is more than 5 beats per minute (bpm) away from the true heart rate.
- **No usable heart rate:** fewer than 3 beats found in lead II.
- **Bad reading:** wrong, or no usable heart rate.
- **Pre-specified:** the rule was written before the result was seen. **Exploratory:** the rule was logged first, but the idea came after earlier data had been seen. **Post hoc:** done after a result, to understand it.
- **Test once:** a frozen model or method is run on its test data one time only. The scripts refuse a second run.

---

## Process 0. Question, plan and rule log

**Purpose.** Decide what is tested and how, before any result exists.

**Steps**
1. Read the literature in six areas: ECG digitization, signal quality, abstention and deferral, patient-facing explanations, data and ECG background, and methodological standards.
2. Write the question: when a photo of an ECG is damaged, do the numbers read from it go wrong, how can a user be told, and which numbers may be shown?
3. Write three claims. C1: which damage makes the heart rate wrong. C2: failures follow the recording. C3: the photo alone can predict failures.
4. Write the rules (what counts as wrong, the tests, the pass limits) in `docs/plan/MASTER_PLAN.md` and `docs/plan/analysis_plan_changes.md`.
5. For every later analysis, add its rule to the change log **before** running it, and label it pre-specified, exploratory or post hoc.

**Output.** A rule log and a claims register. **Code.** None (documents).

---

## Process 1. Choosing the recordings and the reference

**Purpose.** Get real ECGs whose true answer is known.

**Input.** PTB-XL: 21,799 ten-second 12-lead ECGs, in 100 Hz and 500 Hz versions. PTB-XL+ adds interval values from two commercial algorithms (12SL and Glasgow).

**Steps**
1. Fix a random pool of 500 recordings with a seed. The first 50 are the development set. A second random draw of 100 from the 450 unused recordings (seed 42) is the held-out set. Together: 150 recordings.
2. Take the 100 Hz version of each recording; pages are drawn from it.
3. Define the reference heart rate: the heart rate that the same measurement code gives on the 100 Hz recording the page was drawn from.
4. Mark a recording **reference-uncertain** if its 100 Hz and 500 Hz reference heart rates differ by more than 5 bpm. This is 20 of 150 (13%). Mark it **unreliable** if more than 20% of its versions give no output; two recordings (15192 and 21205) are excluded, which leaves 148 for the tables.
5. For later tests choose other recordings with other seeds, and check that none overlaps with any test set: competition real captures (seed 43), own phone photos (seed 44 and 45), and the fresh sets of later phases.
6. Make every selection before any result is seen.

**Output.** The recording lists (`results/extension/...`). **Rule.** Main conclusions must also hold without the reference-uncertain recordings. **Code.** `scripts/analysis/select_extension_100.py`.

---

## Process 2. Drawing the paper page

**Purpose.** Turn a recorded signal into a paper-style ECG page.

**Input.** One recording and ECG-Image-Kit (a researchers' tool, one patched copy used for every set).

**Steps**
1. Set the paper scale: 25 mm/s speed, 10 mm/mV gain, 200 dots per inch.
2. One pixel is 25.4/200 mm, so the time step is 5.08 ms per pixel and the voltage step is 0.0127 mV per pixel. In general dt = 1.016/D s and dv = 2.54/D mV.
3. For each sample (t, v) of a lead, compute the pixel position x = t/dt and y = y0 − v/dv, where y0 is the baseline row of that lead.
4. Use the standard layout: three rows by four leads, plus a long lead II strip.
5. Write the page on a 2200 × 1700 px canvas (11 × 8.5 inches). The header shows the page label (for example P01), not the PTB-XL number.

**Output.** One clean page image per recording. **Code.** ECG-Image-Kit in `scripts/tools/ecg-image-kit/` (patched `gen_ecg_image_from_data.py`), called from the notebooks.

---

## Process 3. Damaging the page (simulation)

**Purpose.** Measure which kind and amount of damage makes the reading wrong.

**Input.** The clean 2200 × 1700 page.

**Steps.** Apply one damage type at a time, at five levels:
1. **Blur:** Gaussian blur with a k × k kernel, k = 3, 7, 11, 15, 21.
2. **Rotation:** rotate the page by 2, 5, 8, 12, 16 degrees, white corners.
3. **JPEG compression:** save and reload at quality 50, 30, 15, 8, 3.
4. **Low resolution:** shrink by a factor f (area method), then enlarge back (linear), f = 0.75, 0.5, 0.35, 0.25, 0.15.
5. **Uneven brightness:** I′ = I (1 − s·x/(W−1)), a left-to-right shadow ramp, s = 0.15 to 0.75.
6. **Faded grid:** I′ = (1 − s)·I + s·mean(I), clipped to 0–255, s = 0.15 to 0.75.
7. The first 50 recordings get 31 versions (clean plus 6 types × 5 levels). The new 100 get 13 versions (clean, level 3 and level 5 of each type).

**Output.** The damaged pages. **Code.** `scripts/quality_proxy/degrade.py`.

---

## Process 4. Digitizing and measuring the heart rate

**Purpose.** Turn each picture back into a signal and compare its heart rate with the true one.

**Input.** The page image (clean, damaged or photographed).

**Steps**
1. Run **Open-ECG-Digitizer**, unchanged (commit 97a15087, its published weights, one fixed settings file for every run).
2. Inside it, a U-Net (a neural network that labels each pixel) finds the trace and the grid; a Hough transform (a line finder) finds the page tilt; the grid spacing gives the size of a pixel in mm; the trace is read out as a signal at 1,000 Hz, in microvolts. Leads that cannot be read are returned as missing values.
3. On lead II of both the true and the digitized signal, apply the same cleaning filter (`nk.ecg_clean`, NeuroKit method).
4. Find the R-peaks with NeuroKit2.
5. For each pair of neighbouring R-peaks, RR is the gap in seconds, the instantaneous rate is 60/RR, and the heart rate is the mean rate over the signal.
6. Call the reading **wrong** if it differs from the reference by more than 5 bpm (10 bpm as a secondary check), and **no usable heart rate** if fewer than 3 beats are found.
7. Because the digitizer is slightly non-deterministic, repeated runs on one image can differ a little. This is reported.

**Output.** One row per image: output or not, heart rate, wrong or not. **Code.** `scripts/tools/Open-ECG-Digitizer/` (run from inside that folder: `python -m src.digitize --config <settings>.yml`); the sweeps run in the Colab notebooks.

**Note on the cleaned measure (post hoc, 8 Nov).** 16 of 140 *clean* real-capture pages gave a wrong rate, so damage could not be the cause. The reason was a fragile one-number rate from raw-signal beat detection on hard rhythms, plus 2 real digitizer failures. So the cleaning step was applied to both the reference and the digitized signal, and the earlier labels were recomputed. The original measure is always shown next to the cleaned one.

---

## Process 5. The pre-specified claims (C1, C2, C3)

**Purpose.** Answer the first question with rules written in advance.

**Steps**
1. **C1:** for each damage type and level, count wrong readings on the held-out 100 and give a Wilson 95% interval (centre = (p + z²/2n)/(1 + z²/n), z = 1.96). Compare with the clean page by a paired Wilcoxon signed-rank test with Holm correction.
2. **C2:** check whether failures cluster by recording (descriptive).
3. **C3:** compute five scores from the picture alone and train a logistic regression to predict a wrong heart rate:
   - blur = variance of the Laplacian;
   - tilt = median angle of long lines (Canny edges plus Hough) from the horizontal and vertical;
   - resolution = share of high-frequency energy in the 2-D Fourier spectrum;
   - contrast = standard deviation of grey values;
   - blockiness = the period-8 peak left by JPEG.
   Train on the first 50, score the new 100 **once**. Verdict rule fixed in advance: it "discriminates" if AUC ≥ 0.70 with the lower 95% bound above 0.60; it is "inconclusive" if the new 100 hold fewer than 100 wrong readings.
4. Add the comparisons: an oracle model told the damage type and level, leave-one-damage-type-out, and a standard no-reference quality baseline.

**Bridge run (repeatability).** Re-digitize 12 of the first 50 recordings (156 images). Rule: if more than 5% of images change their bad/good label, pooled comparisons become exploratory. Result: 0 of 156 changed, so the first sweep and its repeat were pooled. The second sweep is a repeat, not an independent replication.

**Output and verdict.** C1 supported: only very low resolution (shrunk to 15%) and heavy blur made the heart rate wrong often (47.5% and 17.2% of pages on the held-out set). C3 inconclusive, and the honest reading is negative. **Code.** `scripts/analysis/section_C.py`, `section_D.py`.

---

## Process 6. The reliability check (traffic light)

**Purpose.** Tell the user when a reading should not be trusted, using only the digitized signal.

**Input.** One digitized 12-lead signal. It never uses the true signal.

**Steps**
1. Compute 15 features: share of readable samples in lead II; number of unreadable leads; mean completeness of the other 11 leads; number of beats in lead II; heart rate and a flag when it is below 30 or above 200 bpm; RR variation (SD of RR divided by mean RR); the largest and smallest RR ratio to the median; signal amplitude (log of the 5th–95th percentile range); the share of lead II power above 40 Hz; the Einthoven check RMS(II − I − III)/RMS(II); the Goldberger check RMS(aVR + aVL + aVF)/mean RMS of the three; whether the other leads show the same beat count as lead II; and the mean beat-count difference.
2. Fill gaps with the median and standardise: z = (x − mean)/sd.
3. Compute the risk score by logistic regression, p = 1/(1 + exp(−(b0 + Σ b_j·z_j))), balanced class weights, trained **once** on the simulated new 100 (1,262 images with a reading, 113 wrong).
4. Set two thresholds from out-of-fold training scores only. AMBER = the 10th percentile of the scores of the wrong readings (0.2585), so at least 90% of wrong readings reach AMBER or RED. RED = the lowest score at or above which at least half of the readings are wrong (0.7823).
5. Give the light: RED if p ≥ RED; AMBER if p ≥ AMBER; otherwise GREEN.
6. Apply two extra rules. A reading with fewer than 3 beats is RED by definition. If any feature (except amplitude) lies outside the range seen in training, a GREEN becomes AMBER.
7. Attach reasons (information only; they do not change the light).
8. Freeze the model in `safeguard/model.json`. Evaluate once on the real captures.

**Output.** GREEN, AMBER or RED with reasons. GREEN means "no warning raised", not "the heart rate is correct". **Verdict.** On 917 real-capture readings with GREEN, 2 were wrong (0.2%). **Code.** `safeguard/` (`ecg_traffic_light.py`, `train_safeguard.py`, `evaluate_safeguard.py`).

---

## Process 7. Real captures and own phone photos

**Purpose.** Check the results on real pictures, not only simulated damage.

**Steps**
1. **Competition dataset (Arm C and C+):** 140 recordings × 9 capture types (kit original, print-scan colour and black-and-white, phone photo of print, phone photo of screen, stained, extensively damaged, mouldy scan colour and black-and-white) = 1,260 images; 1,201 gave a reading. Run through the same digitizer, in Kaggle.
2. **Own phone set 1:** 30 recordings drawn as pages, shown full screen on a laptop, photographed with a phone twice each (straight on, and from the side at about 30 degrees) = 60 photos. Reference = the PTB-XL 100 Hz lead II, cleaned measure.
3. **Frozen models:** apply the photo model (trained on the 900 competition images) and the output check (trained on simulated damage) without refitting on these photos.
4. Photos are matched to pages by file-name order and checked by eye.

**Output.** Rates of wrong readings per capture type; the photo model did not meet its criterion on own photos. The largest practical problem on real photos was geometry (tilt and perspective).

---

## Process 8. Straightening the photograph (the fix)

**Purpose.** Correct page tilt and perspective before digitizing.

**Input.** A phone photo.

**Steps**
1. Shrink the photo to 800 px, convert to grey, blur 7 × 7.
2. Apply the **Otsu threshold** (it picks the light/dark split automatically).
3. Clean with a morphological close (15 × 15) then open (9 × 9).
4. Take the largest contours (area at least 12% of the image), the convex hull, and reduce it to a four-sided polygon (tolerance 1.5% to 6% of the perimeter), or the minimum-area rectangle if that fails.
5. Order the corners: top-left, top-right, bottom-right, bottom-left.
6. Compute the perspective transform M = getPerspectiveTransform(corners, target corners) and apply it with cubic interpolation, border replicated, to a 2200 × 1700 px rectangle.
7. Accept the result only if width/height is between 0.9 and 1.8; otherwise keep the original photo.
8. The enlarge-only variant scales the long side to 4096 px (Lanczos); a fourth variant does both.

**Tests**
- **Development (first 60 photos):** four variants compared with the original by an exact McNemar test, Holm-corrected. Bad readings fell from 20 to 2 (Holm p = 0.0001). Exploratory, because the idea came from these photos.
- **Confirmation (40 new photos of 20 new pages), rule written before the photos existed:** bad readings fell from 14 to 2 of 40; newly bad 0, newly good 12; exact McNemar p = 0.0005. Confirmed. Enlarging alone did not help.
- **Larger check:** 120 simulated phone photographs (tilt, screen edge, vignette, noise, blur, shadow, smaller page).

**Code.** `scripts/preprocess/page_straighten.py`; `section_Q_fixexp.py`, `section_Q2_confirm.py`, `section_Z_sim_photos.py`.

---

## Process 9. Printed paper photographed by another person

**Purpose.** Test whether the results hold for another phone and for real paper.

**Steps**
1. A friend photographed 20 printed pages with an unknown phone and sent them by a messaging app (80 photos, then 40 more). These form set H2 and are never pooled with the team's own photos.
2. Match each photo to its page by image content (checked against 16 of 16 page identifiers read by eye).
3. Because the phone was held upright, turn a photo taller than wide by 90 degrees before the page finder runs. This step was fixed before any photo was digitized.
4. Primary set: the 22 straight full-resolution photos. Secondary sets, reported separately: all 52 full-resolution photos and 66 recompressed copies.
5. Run straightening, the digitizer and the traffic light, then count bad readings.

**Result.** Straightening helped on the 66 recompressed copies (31 to 15 bad, p = 0.0004), but not on the 22 straight full-resolution photos (3 to 2, p = 1.0). GREEN readings were wrong for 2 of 19 photos, so GREEN is not a guarantee on printed paper.

---

## Process 10. Validating each measurement

**Purpose.** Decide which numbers may be shown to a user.

**Rule.** A measurement is shown only if it passes a validation written before the test. The value measured on the digitized photo is compared with the PTB-XL+ reference. The test is run once on a sealed set, then once on a confirmation set. Calibration may only shift a value (an offset, plus a rate term for QT), never rescale it, because rescaling shrinks all values toward the mean and hides errors.

**Heart rate.** Already validated (clean-page limits of agreement −3.2 to +3.1 bpm).

**PR interval (own median-beat method)**
1. Cut the signal to the page layout; take a median beat per lead.
2. Find the P-wave start by the tangent method and the QRS onset by slope; PR = the gap; take the median over leads.
3. Develop on the first 50 original signals; choose the method and one constant offset (+5.8 ms) and freeze them.
4. Test once on the held-out 100: typical error 7.3 ms. Confirm once on 100 own phone photos after straightening: 12.0 ms, 95% within 40 ms.
5. Rule: typical error 20 ms or less, 90% within 40 ms, mean bias within 10 ms, 90% of recordings with a value. **Met** for straightened photos with a steady rhythm. It is not met for unstraightened photos or heavy blur.

**Frontal QRS axis**
1. Take the net QRS deflection of each of the six limb leads (dominant-deflection definition) and fit the axis vector by least squares. Nothing is fitted or rescaled.
2. Frozen on 1,000 development recordings; one test on 100 fresh pages; one confirmation on 100 phone photos.
3. Reference: 12SL R_AxisFrontal_Global. Rule: median circular error 10 degrees or less, at least 90% within 30 degrees, mean error within 10 degrees, at least 90% category agreement, at least 90% with a value. **Met** on fresh pages and on straightened phone photos.

**QT and QRS duration (not validated, several attempts)**
1. First attempt with the standard NeuroKit2 wavelet method: failed even on the original signal (typical errors 36 ms QT, 78 ms PR, 84 ms QRS).
2. Own median-beat method: QRS onset by slope, T end by the tangent method, median over leads, offset −40.5 ms for QT. Met the rule on the held-out original signal, but not on drawn pages and photos with fresh data.
3. Second and third attempts on fresh data (1,000 development recordings, a test on 100 fresh pages, a confirmation on phone photos; combined leads). QT stopped in development; QRS duration not validated.
4. A neural network for QRS duration and QT trained once on PTB-XL folds 1 to 8 (12SL labels, a fixed digitizer emulation during training, one offset, no slope). QRS passed on fresh drawn pages (4.1 ms, slope 0.89) but not on simulated or real photos (bias +8 to +11 ms, compressed slope 0.65). QT failed even on fresh drawn pages.
5. A retry on doctor-marked public data (LUDB and the QT Database): not validated either.

**P-wave and T-wave amplitude.** Only lead II amplitude was tried, against the 12SL value. It was not validated. The ST segment was not attempted, because the two commercial algorithms disagree on P duration, T duration and ST amplitude, so no reference exists.

**Detector agreement (exploratory).** Five beat detectors (NeuroKit raw and cleaned, Pan-Tompkins, Hamilton, Elgendi) were added as features (spread, standard deviation, number agreeing). The rule for "added value" (real-capture AUC rises by 0.02 or more) was not met (+0.005).

**Code.** `scripts/analysis/section_S`, `T`, `U`, `V`, `W`, `X`, `Y`, and `demo/pr_interval.py`, `demo/axis_deg.py`.

---

## Process 11. ECG pattern findings (the guide's request of 15 Nov)

**Purpose.** Show an "ECG pattern" finding (never a diagnosis and never risk), only where a pass rule is met.

**Steps**
1. **First network (PTB-XL):** a small 1-D convolutional network, about 0.5 million parameters. Input: 12 leads cut to the page-layout windows plus mask channels, 100 Hz. Six labels: normal, infarction (MI), ST/T change (STTC), conduction disturbance (CD), hypertrophy (HYP), atrial fibrillation/flutter (AF).
2. Train **once** on PTB-XL folds 1 to 8 (17,104 recordings). Fold 9 (2,142) sets the stopping epoch (7) and the Platt calibration. Remove the 420 recordings that appear in any digitized or photo set from training.
3. Test once on three data: T1 fold 10 (2,133 recordings), T2 digitized drawn pages (300), T3 straightened phone photos (140 photos of 70 pages).
4. Pass rule (proposal, not approved by the guide): at least 20 positives; on drawn pages AUROC at least 0.80 with the lower 95% end above 0.70; on photos also at least 20 positive photos and AUROC at least 0.75.
5. **More patterns:** model A (16 finer PTB-XL codes) and model B (six CODE-15% labels: first-degree AV block, right and left bundle branch block, slow and fast heart rate, atrial fibrillation; 132,040 exams). Each trained once, tested once, same rules.
6. **Fresh sets:** N (positive-rich), P (266 new recordings, simulated photos), Q (a retrain A2/B2 with stronger photo-style damage: gain per lead, noise, baseline wander, held pieces, time shifts), R (120 new pictures: 41 left bundle branch block, 48 atrial fibrillation, 40 normal, same frozen network), S (300 random fold-10 recordings, 66 positives). Each set was chosen after the rule was logged and before its data were used.
7. **Operating point:** a strict threshold at specificity 0.97, frozen before the fresh-set tests.
8. **Infarction percentage:** calibrate the score on simulated photos, weighted to the PTB-XL prevalence 25.1%.
   - First attempt: fit on sets N + P (386 simulated photos), test once on Q + R (280, 64 positives). Slope 0.95 (pass), Brier 0.165 against 0.188 (pass), calibration error 0.061 against a limit of 0.05 (**fail**). No percentage was shown.
   - Second attempt, rules written before set S was selected: fit on N, P, Q, R (666 photos), p = sigmoid(0.337 × logit(score) − 0.944). Test once on set S (300 simulated photos): slope 1.15, calibration error 0.040, Brier 0.145 against 0.184 raw and 0.172 prevalence only: all pass. AUROC 0.773; sensitivity 76%, specificity 66% at threshold 0.279.

**Result.** Infarction and ST/T change passed on straightened photos (AUROC 0.81 and 0.84 on new photos). Conduction failed on printed paper (AUROC 0.42, 5 positives). Left bundle branch block and atrial fibrillation passed on dataset pictures only and are shown as research-only. The infarction percentage is shown, labelled as a second attempt on simulated photos, calibrated to the PTB-XL population, not tested on real photos. **Code.** `demo/health/` (`model.py`, `train.py`, `evaluate.py`, `assess.py`), `scripts/analysis/section_FIND2_train.py`, `section_Q_train.py`, `section_*_test.py`, `section_MI_photocal*.py`.

---

## Process 12. Mortality-risk pilots

**Purpose.** Test whether a risk estimate could be shown from the ECG.

**Steps**
1. **Pilot 1:** CODE-15% parts 0 to 5: 31,718 patients with a 10 s ECG and an outcome (1,134 deaths). Patient-level split 70/10/20 by hash. A network on the ECG alone; test = 6,188 patients, 82 deaths within 1 year; tested once. AUROC 0.713 (0.653 to 0.770) against the rule 0.75 with lower end above 0.70: **failed**; age alone scored 0.799.
2. **Pilot 2** (decided after pilot 1 failed, rules logged before the download): all 18 parts, 87,371 patients (3,079 deaths); a five-year horizon; age as an input. Train 13,330, validation 1,991, sealed test 2,323 patients with 365 deaths within 5 years, tested once. AUROC 0.833 (0.810 to 0.854) against 0.819 for age alone: the AUROC and the calibration (slope 1.18) passed, but the gain from the ECG, +0.013, was not significant (interval −0.005 to +0.032), and the risk was not stable on simulated photos. 4 of 7 rules failed, so nothing was shown.
3. **Pilot 3:** five-fold cross-validation on all 19,048 usable patients (2,965 events; not a blind test). AUROC 0.811 (0.803 to 0.820) against 0.798 for age alone; observed five-year rates 2.2%, 8.3%, 32.3% across the groups; calibration slope 0.76 against the rule of 0.8 to 1.25: **failed** (0.94 after Platt scaling, descriptive only). Stage 2 was not run.
4. **Age from the ECG:** a five-fold network estimates age (error 9.27 years); the risk AUROC with the estimated age was 0.795. Both app rules passed.
5. **Range on pictures:** the pictures of earlier tests (1,080) and the 300 of set S showed that the displayed range (±10 points with true age, ±12 with estimated age) contained the clean-ECG estimate for 88 to 97% of drawn pages but only 61 to 73% of photographs, so on photographs the real uncertainty is larger than the range.
6. **Internal validation** (same cohort, not external): calibration slope 0.94, observed within 5 points of predicted in 10 of 10 deciles (top decile overestimated, 57% against 51%), a small gain over age and sex (+0.008).

**Display decision (not a result).** The demo shows a separate, research-only risk range for a GREEN straightened photo, as an average of the five fold models with per-fold Platt scaling. It runs higher than population risk, because only people with a complete five-year follow-up were counted. No validated risk is claimed. **Code.** `scripts/analysis/section_RISK*.py`.

---

## Process 13. The demonstration and the explanation safeguards

**Purpose.** Show only validated information, in fixed wording.

**Steps (what happens when a photo is uploaded)**
1. The photo comes in (JPG, JPEG or PNG). The page is found and straightened (Process 8).
2. Open-ECG-Digitizer runs with a fixed random seed, so the same photo gives the same answer (Process 4).
3. The traffic light gives GREEN, AMBER or RED (Process 6).
4. The heart rate is shown with the light and its resting range. PR interval is shown only if the light is GREEN, the page was straightened, the value lies between 50 and 400 ms and the rhythm is steady (RR variation 0.12 or less). The axis is shown in degrees only under a GREEN light on a straightened page.
5. QT, QRS duration, P wave, T wave and ST segment are listed as "not measured by this tool".
6. On a GREEN or AMBER straightened photo, two ECG patterns (infarction, ST/T change) are shown as found or not found; the infarction percentage appears as in Process 11; seven further patterns sit in a separate research-only block without a percentage. The risk range sits in its own research-only box (Process 12).
7. A RED light or no output says nothing about the heart.
8. Every sentence comes from a fixed list in `demo/explain.py`. A wording checker blocks forbidden words (a verdict on health, "you have ...", "normal ECG", "dangerous", advice on medicine, a diagnosis, any verdict on the axis or an interval) and replaces them with a safe fallback sentence.
9. 19 automated tests run over all combinations of light, heart rate, PR value, rhythm steadiness and axis. Charts (heart-rate gauge, strongest-pattern donut, risk-rate dial, heart diagram) are display only, drawn with Plotly.

**Code.** `demo/` (`app.py`, `pipeline.py`, `explain.py`, `pr_interval.py`, `axis_deg.py`, `health/`), tests `demo/tests/`. Start with `demo\run_demo.bat` and open http://127.0.0.1:7860.

---

## Process 14. Checking and reproducing the numbers

**Steps**
1. Every number in the report is taken from `results/FINAL_NUMBERS.md` (frozen on 11 Nov, with later sections marked "after the freeze").
2. `python -I scripts/analysis/final_numbers_recompute.py` recomputes 36 headline numbers from the raw files and prints MATCH or DIFFERENT. All 36 match. It is a second script by the same author, not a second person, and it does not re-run the digitizer.
3. Numbers that are never quoted are listed (for example the saved `snr_db` column, which was wrong).
4. A written list of what may and may not be claimed sits in `FINAL_NUMBERS.md` section 6.
5. `reproducibility/REPRODUCE.md` lists versions, tool commits, patches and a one-page check for a second person.

---

## What this page does not contain
- The layers and training settings of the neural networks (learning rate, epochs for each model). Those are in `demo/health/model.py` and the training scripts.
- The full per-damage tables of Process 5 and the full results of each analysis. Those are in `results/FINAL_NUMBERS.md` and `results/analysis/SECTION_*.md`.
- The guide's approval of the pass thresholds. They are still the team's proposal.
