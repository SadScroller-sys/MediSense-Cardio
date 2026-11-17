# MediSense-Cardio: methods and formulae (complete, from the first sweep to the 2026-11-11 confirmation set)

Everything below is taken from our own code (notebooks in `colab/`, scripts in `scripts/`, the safeguard in `safeguard/`) and from the rule log `docs/plan/analysis_plan_changes.md`. Where a number is a choice we made, it says so. Every analysis carries a status:

- **PRE-SPECIFIED** = the rule was written before the result was seen (MASTER_PLAN, analysis_plan_150).
- **EXPLORATORY** = added later; the rule was logged first, but the idea came after we had seen earlier data. No "confirmed" wording is used for these.
- **POST HOC** = done after seeing a result, to understand it (clean-page diagnosis, cleaned measure).

Results are not in this file; they are in `results/analysis/SECTION_*.md` and `results/FINAL_NUMBERS.md` (when written). Language rule for the report: simulated results are worded "in the simulation, within these six damage types"; real-photo results are worded "on these captures".

---

## 0. The whole method in one picture

| Stage | What we do | Tool / code |
|---|---|---|
| 1 | Take real ECG recordings with a known answer (PTB-XL, 10 s, 12 leads) | PTB-XL |
| 2 | Draw each as a paper-style page | ECG-Image-Kit (researchers' tool) |
| 3 | Damage the picture (six controlled types x levels), or use real captures (competition photos, own phone) | our functions; Arm B tool artifacts; Arm C competition data; own-phone photos |
| 4 | Turn the picture back into a signal | Open-ECG-Digitizer, unchanged |
| 5 | Measure heart rate (HR) on the true and the digitised signal by the same code | NeuroKit2 |
| 6 | Count how often the HR is wrong; test whether a warning can predict it (from the photo, from the digitised signal) | our analysis scripts |
| 7 | Build and test a traffic-light checker; test a simple photo fix (straightening) | `safeguard/`, `scripts/preprocess/` |

Words used: **wrong** = an output exists but its HR is more than 5 bpm away from the true HR. **No usable HR** = fewer than 3 beats found in lead II (or no lead II). **Bad** = wrong or no usable HR. **False reassurance** = the true recording is abnormal but the reading looks normal.

---

## 1. Data and reference (PRE-SPECIFIED)

- **Recordings:** PTB-XL (21,799 ten-second 12-lead records, 100 Hz and 500 Hz versions). Pages are drawn from the **100 Hz** record (`records100`).
- **Sample for the sweeps:** a random subset (seed 42) of a 500-record pool: **first 50** recordings = development set (seen many times); **new 100** = held-out replication, drawn with seed 42 from the 450 unused records (`scripts/analysis/select_extension_100.py`). Together 150.
- **Reference HR** = HR measured by the same code on the 100 Hz record the page was drawn from (Section 5). A recording is **reference-uncertain** if its 100 Hz and 500 Hz reference HRs differ by more than 5 bpm. It is **unreliable** if more than 20% of its versions give no output (15192 and 21205). It is **flagged** if PTB-XL marks drift, static or burst noise, electrode problems, extra beats or a pacemaker. Main verdicts must hold with and without the reference-uncertain recordings.
- **Other recordings:** Arm C (real captures) 40 recordings; Arm C extension (C+) 100 more recordings (seed 43, none in Arm C); own-phone set 1: 30 recordings (pages P01-P30, seed 44, none of the 150); own-phone set 2 (confirmation): 20 recordings (pages Q01-Q20, seed 45, none of the 150 and none of P01-P30). All selections are made before any result.

## 2. How a signal becomes a picture (paper scale)

Paper speed **25 mm/s** and gain **10 mm/mV**. At D = 200 dots per inch one pixel is 25.4 / D mm, so

- time per pixel: `dt = 25.4 / (25 D) = 1.016 / D` s (5.08 ms at 200 dpi)
- voltage per pixel: `dv = 25.4 / (10 D) = 2.54 / D` mV (0.0127 mV at 200 dpi)
- sample (t, v) lands at pixel `x = t / dt`, `y = y0 - v / dv` (y0 = baseline row of the lead).

Page size **2200 x 1700 pixels** (11 x 8.5 in at 200 dpi), the standard layout (3 x 4 leads + a long lead II strip), the same patched ECG-Image-Kit code for every set (sweeps, P01-P30, Q01-Q20). The page header shows the label (P01, Q05, ...) and not the PTB-XL id.

## 3. Damage and real captures

### 3.1 Six controlled damage types, 5 levels each (PRE-SPECIFIED)
Applied to the clean 2200 x 1700 page (`scripts/quality_proxy/degrade.py`, identical to the sweep notebooks):

| Damage | Formula | Level 1 / 2 / 3 / 4 / 5 |
|---|---|---|
| Blur | Gaussian blur, kernel k x k, OpenCV sigma = 0.3 (0.5 (k-1) - 1) + 0.8 | k = 3 / 7 / 11 / 15 / 21 |
| Rotation | rotate the page by an angle, white corners | 2 / 5 / 8 / 12 / 16 degrees |
| JPEG compression | save and reload as JPEG | quality 50 / 30 / 15 / 8 / 3 |
| Low resolution | shrink by factor f (area), enlarge back (linear) | f = 0.75 / 0.5 / 0.35 / 0.25 / 0.15 |
| Uneven brightness | `I' = I (1 - s x/(W-1))`, a left-to-right shadow ramp | s = 0.15 / 0.3 / 0.45 / 0.6 / 0.75 |
| Faded grid (low contrast) | `I' = (1-s) I + s mean(I)`, clipped to 0..255 | s = 0.15 / 0.3 / 0.45 / 0.6 / 0.75 |

- **Sweep 1 and sweep 2:** first 50 recordings x 31 versions (clean + 6 types x 5 levels). Sweep 2 is a **repeat** with intervals saved, not an independent replication.
- **New 100:** 13 versions each (clean, level 3 and level 5 of each type); the 13 versions are the ones both sets share, and pooled comparisons use only these.
- **Bridge run:** 12 of the first 50 re-digitised (156 images). Rule: if more than 5% of images change their bad/no-output label, pooled comparisons become exploratory. Result: 0 of 156 changed.

### 3.2 Researcher-style arms
- **Arm B:** ECG-Image-Kit's own artifact options (wrinkles and creases, rotation up to 10 degrees, noise, crop, colour temperature).
- **Arm C and C+ (real captures):** the public PhysioNet Challenge competition dataset "Digitization of ECG Images" (read inside Kaggle). 9 capture types per recording: C0 kit original, C1/C2 print-scan colour/black-and-white, C3 phone photo of print, C4 phone photo of screen, C5 stained or soaked, C6 extensive damage, C7/C8 mold scan colour/black-and-white. Arm C = 40 recordings x 9 = 360 images; C+ = 100 recordings x 9 = 900 images (seed 43). Same digitiser commit, weights and settings.
- **Own-phone set 1:** the 30 pages P01-P30 shown full screen on the user's laptop, photographed with the user's phone, 2 photos per page (straight on; from the side, about 30 degrees) = 60 photos (analogue of C4). **Set 2** (confirmation): 20 pages Q01-Q20, 40 photos, the same way.

## 4. The digitiser

Open-ECG-Digitizer, used **unchanged** (commit `97a15087` and its published weights `unet_weights_07072025.pt` and `lead_name_unet_weights_07072025.pt`; one fixed settings file for every run): a U-Net finds the trace and the grid, a Hough transform finds the page tilt, the grid spacing gives the pixel size, and the trace is read as a signal in microvolts at 1,000 Hz (we divide by 1,000 to get millivolts). Its mathematics is in its paper; we did not change it. Runs: Colab (sweeps) and Kaggle GPU (Arm C, C+, own phone sets, fix experiment).

## 5. Measurements

### 5.1 Heart rate
- **Original measure (pre-specified primary):** R-peaks with NeuroKit2 `ecg_peaks` on the (raw) lead II. With `RR_i` the gap between neighbouring R-peaks (s), instantaneous rate `60 / RR_i` bpm; `HR = mean over time of the rate` (`nk.ecg_rate` averaged over the signal).
- **Cleaned measure (POST HOC correction, 2026-11-08):** the same, but with `nk.ecg_clean(method="neurokit")` applied before beat finding, to **both** the reference and the digitised lead II. The original is always shown next to the cleaned one. Reason: some recordings have ambiguous beats; raw-signal detection gives one fragile number (see Section 10).
- **Wrong:** `|HR_digitised - HR_reference| > 5 bpm` (secondary 10 bpm). **No usable HR:** fewer than 3 beats. **Bad:** wrong or no usable HR. The labels of all later analyses use the cleaned measure.

### 5.2 Aligned signal-to-noise ratio (secondary)
Bring the digitised signal to 500 Hz, remove each mean, find the best shift `s` within +-0.5 s by cross-correlation, then `SNR = 10 log10( sum g(n)^2 / sum (x(n+s) - g(n))^2 )`, g = reference, x = digitised; reported with the shift and the Pearson correlation. (The old saved `snr_db` column was wrong and is never used.)

### 5.3 Intervals (secondary; NeuroKit2 wavelet delineation)
`QT` = T-wave end - QRS onset, mean over beats; `RR = 60 / HR` s. `QTc (Bazett) = QT / sqrt(RR)`; `QTc (Fridericia) = QT / RR^(1/3)` (sensitivity check; results are stated "by this method"). Prolonged: QTc >= 460 ms (women), > 450 ms (men). PR and QRS are not used as clinical measures: their references did not agree with the commercial tools.

### 5.4 False reassurance
For HR, normal = 60 to 100 bpm (convention). Five boxes: correct normal, correct abnormal, false alarm, **false reassurance**, no answer.

## 6. Statistics

- **Rate with uncertainty (Wilson 95%):** k wrong of n, `p = k/n`, z = 1.96, `centre = (p + z^2/(2n)) / (1 + z^2/n)`, `half-width = z sqrt(p(1-p)/n + z^2/(4n^2)) / (1 + z^2/n)`.
- **Recording-level bootstrap:** the unit is the recording (not the image): resample recordings with replacement (1,000 times for rate intervals, 2,000 for AUC intervals); 2.5th and 97.5th percentiles. Intervals that treat images as independent are optimistic, and the report says so.
- **Paired comparison with the clean page (sweeps):** Wilcoxon signed-rank per damage type and level, Holm correction: sort m p-values; `p_adj(i) = max over j <= i of min(1, (m - j + 1) p_(j))`.
- **Paired comparison on binary outcomes (Arm C, C+, fix experiments):** `b` = recordings bad only in the new condition, `c` = bad only in the reference condition; exact two-sided binomial test of b against b + c at p = 0.5 (exact McNemar); Holm over the family. Primary alpha 0.05.
- **Trend with damage level:** Spearman rho between level and absolute error (exploratory; the p-value ignores that one recording appears at every level).
- **Agreement:** Bland-Altman: `d = HR_digitised - HR_reference`, `bias = mean(d)`, limits `bias +- 1.96 SD(d)`; Pearson r, Spearman rho.
- **AUC:** the probability that a randomly chosen bad reading gets a higher risk than a randomly chosen good one (0.5 = guessing, 1 = perfect); interval by the recording-level bootstrap.
- **Grouped cross-validation:** 5 folds x 10 repeats; **whole recordings** are assigned to folds (permutation of recording ids, `fold = rank mod 5`), so one recording never sits in both training and test; out-of-fold probabilities are averaged over the 10 repeats.
- **Oracle:** a model told the damage type and level (one-hot, logistic regression). **Leave-one-damage-type-out:** train on five types, test on the sixth.
- **Coverage curve (gate):** flag the q% of photos with the highest risk; `caught = bad flagged / all bad`; `false flags = good flagged / all good`.
- **Sample size:** Riley's criterion for a prediction model with p predictors, shrinkage S = 0.9: `n = p / ((S - 1) ln(1 - R2/S))`; for testing a finished model, at least 100 events (Collins). Below 100 wrong readings, results are labelled descriptive/inconclusive.
- **Model used everywhere:** median imputation -> standardisation (`z = (x - mean)/sd`) -> logistic regression `p = 1 / (1 + exp(-(b0 + sum b_j z_j)))`, `class_weight="balanced"`, `max_iter = 1000`.

## 7. Photo-quality detector (PRE-SPECIFIED, claim C3)

Five scores from the picture alone (`scripts/quality_proxy/image_quality.py`; BGR image, grey = `cvtColor`):
- **blur_score** = variance of the Laplacian of the grey image (lower = blurrier); used as `blur_log = log10(blur_score + 1)`.
- **skew_deg** = median deviation from the horizontal/vertical of long lines (Canny edges + probabilistic Hough, lines at least 30% of the width): `dev = min(a mod 90, 90 - a mod 90)` for line angle a.
- **resolution_score** = share of high-frequency energy in the 2-D Fourier spectrum: `sum |F| over radius > 0.5 r_max / sum |F|`.
- **contrast_score** = standard deviation of the grey values.
- **blockiness_score** = size of the period-8 peak in the spectrum of the column-mean gradient relative to the median spectrum (decreases with JPEG damage; the regression finds its own sign).

Model: the logistic regression of Section 6, target = wrong HR (images with an output; a page with no output needs no warning). Train on the first 50 (reliable recordings, all 31 versions), score the new 100 **once**. Verdict rules (fixed in MASTER_PLAN): discriminates if AUC >= 0.70 with the lower 95% bound above 0.60; inconclusive if the new 100 hold fewer than 100 wrong readings; ceiling-limited if the oracle is itself below 0.70. Also reported: best single score, leave-one-damage-type-out, swapped direction, grouped CV on all 150, coverage curve, a standard no-reference quality baseline.

## 8. Output check (the digitised signal; Section D2, EXPLORATORY, rules logged 2026-11-07)

Features from the **digitised** signal alone (never the reference); package `safeguard/ecg_traffic_light.py`. For lead II (`ii`), `RR` from the cleaned beat finder, other leads handled the same way:

| Feature | Definition |
|---|---|
| ii_complete | share of finite samples in lead II |
| n_unreadable_leads | leads with fewer than 1,500 finite samples |
| mean_other_lead_complete | mean over the other 11 leads of `min(1, finite samples / 2500)` |
| n_beats | R-peaks found in lead II |
| hr_ii, hr_implausible | `mean(60/RR)`; 1 if HR < 30 or > 200 bpm |
| rr_cv | `SD(RR) / mean(RR)` |
| rr_max_ratio, rr_min_ratio | `max(RR)/median(RR)`, `min(RR)/median(RR)` |
| amp_log | `log10( P95(II) - P5(II) )` |
| hf_share | share of lead II power above 40 Hz |
| einthoven | `RMS(II - I - III) / RMS(II)` (means removed), where all three exist |
| goldberger | `RMS(aVR + aVL + aVF) / mean(RMS of the three)` |
| xlead_count_match | share of the other leads whose beat count equals lead II's in the same window (100 samples cut at each end) |
| xlead_count_absdiff | mean absolute beat-count difference to lead II |

Model: the logistic regression of Section 6 on these 15 features, trained on the **simulated new 100** (1,300 saved signals; images with a reading; label = wrong HR, cleaned measure; unreliable recording 21205 excluded). Test: grouped 5-fold x 10 cross-validation over the recordings; compared with photo scores alone, output alone, both, and the oracle. **Improvement criterion fixed in advance:** the within-damage AUC inside resolution level 5 and blur level 5 at least 0.70 with the lower 95% bound above 0.50. Follow-ups (rules logged before the run): feature families alone; cost on irregular rhythms (flag rate among right readings for atrial fibrillation/flutter vs others); external check on the real captures (train on simulated, apply once to Arm C / C+).

## 9. Detector agreement (EXPLORATORY, rules logged 2026-11-08)

Five beat detectors on the digitised lead II: NeuroKit raw, NeuroKit cleaned, Pan-Tompkins, Hamilton, Elgendi; each gives `HR_k = mean(60/RR)`. Features: `det_spread = max HR_k - min HR_k`, `det_std`, `det_n_agree` (detectors within 5 bpm of their median), `det_nkclean_vs_pt = |HR_nkclean - HR_PT|`, `det_n_missing`. Comparison: OUT vs OUT + DET, same CV. **Fixed rule for "added value":** pooled-140 real-capture AUC rises by at least 0.02 AND the within-damage AUC does not fall. Result: not met (+0.005); `det_spread` is shown alone and used only as a reason in the traffic light.

## 10. Clean-page diagnosis and cleaned measure (POST HOC, 2026-11-08)

- **Why:** 16 of 140 **clean** real-capture pages gave a wrong HR, so the error cannot come from damage.
- **Truth export:** the true lead II of the competition recordings, exported inside Kaggle (`results/truth/`, 140 recordings, 10 s, native sampling 250-1025 Hz), resampled to 1,000 Hz (`scipy.signal.resample`).
- **Check:** Pearson correlation between the digitised and the true lead II (median 0.98: the digitiser draws the right waveform); the five detectors of Section 9 on the TRUE signal: `spread = max - min`. A recording whose true-signal spread is > 10 bpm (15 bpm second threshold) is "HR ambiguous on the true signal". This flag is used in sensitivity analyses only, never as the primary outcome.
- **Result of the diagnosis:** the wrong clean pages come from a fragile one-number HR from raw-signal beat detection on hard rhythms, with 2 real digitiser failures; so the cleaned measure was applied to both sides (Section 5.1) and the earlier labels were recomputed (Sections J, K).

## 11. Can the photo predict failure on real captures? (Section N, EXPLORATORY, 2026-11-08)

Train and test inside the real captures (new 100 recordings, 900 images, photo scores computed in Kaggle by the same code): logistic regression on the five scores, grouped 5-fold x 10 CV by recording. Targets: T1 no output; T2 wrong HR (cleaned) among images with an output; T3 no output or wrong. Comparator: told only the capture type (C0-C8). Also T1 inside the screen photos (C4). Descriptive; AUC with recording-level 95% interval.

## 12. Own-phone confirmation set 1 (Section O, rules logged 2026-11-08 before any photo)

60 photos of 30 new pages (Section 3.2). **Frozen models, never refitted on these photos:** photo model = logistic regression on the five photo scores trained on all 900 competition-capture images (target: no output); output check = Section 8 model trained on the simulated new 100 with cleaned labels. Reference HR = PTB-XL 100 Hz lead II, cleaned measure. Primary question: does the frozen photo model rank "no output" photos above the others? Criterion: AUC >= 0.70 with the lower 95% bound above 0.50 (result: not met). Secondary: the C4-trained variant; output-check AUC for wrong HR among photos with an output; share with no output. Photos are matched to pages by file-name order (A straight, B angled), checked by eye.

## 13. Traffic-light safeguard (EXPLORATORY; rules logged 2026-11-10 before any real-data evaluation)

- **Input:** one digitised 12-lead signal (1 kHz, microvolts). **Output:** GREEN (no warning), AMBER (check by a person), RED (do not trust the heart rate), a score and plain-language reasons. It never uses the true signal.
- **Score:** `p = logistic(15 features)` of Section 8, trained once on the simulated new 100 (1,262 images with a reading, 113 wrong), packaged as numpy (median imputation, standardisation, coefficients stored in `safeguard/model.json`; reproduces scikit-learn to 1e-9).
- **Thresholds, from out-of-fold scores of the training set only:** `AMBER = 10th percentile of the scores of the wrong readings` (so at least 90% of wrong readings score at or above it; value 0.2585). `RED = lowest score t such that at least 50% of readings with score >= t are wrong` (0.7823). Light = RED if `p >= RED`, AMBER if `p >= AMBER`, else GREEN.
- **Rule by definition:** fewer than 3 beats in lead II (no usable HR) is RED ("no usable heart rate").
- **Out-of-range guard (added before any real-data evaluation, found by a unit test where pure noise got GREEN):** if any feature except `amp_log` lies outside the `[min, max]` seen in training, a GREEN becomes AMBER ("signal looks unlike the data the tool was trained on").
- **Reasons (information only, they do not change the light):** a feature beyond the 90th percentile of the right readings in training (for `rr_min_ratio` below the 10th percentile), or the five-detector spread above 15 bpm. In a GREEN light they are prefixed "minor note (did not change the light)".
- **Evaluation, once after freezing:** competition real captures (140 recordings, images with an output; cleaned labels) and the 60 own-phone photos. Per light: readings, wrong-HR rate with Wilson 95%, share of all wrong readings in AMBER + RED, share of right readings flagged; second table counts no-output images as RED. Unit tests in `safeguard/tests/`.

## 14. Straightening and enlarging (Section Q, EXPLORATORY; rules logged 2026-11-10 before the run)

Code: `scripts/preprocess/page_straighten.py`. Variants of the same photo: **V0** original; **V1 enlarge**: scale so the long side is 4096 px (Lanczos; photos already >= 4096 px are unchanged); **V2 straighten**: find the page and map its four corners to a 2200 x 1700 rectangle; **V3 straighten and enlarge**: same corners to 4400 x 3400.

- **Page finder:** shrink to 800 px, grey, Gaussian blur 7 x 7, **Otsu** threshold, morphological close (15 x 15) then open (9 x 9), largest contours (area >= 12% of the image), convex hull, polygon approximation (epsilon 1.5% to 6% of the perimeter) to a quadrilateral (else the minimum-area rectangle); corners ordered top-left, top-right, bottom-right, bottom-left; accepted if width/height is between 0.9 and 1.8.
- **Perspective correction:** `M = getPerspectiveTransform(corners, [[0,0],[W-1,0],[W-1,H-1],[0,H-1]])`, `warpPerspective` with cubic interpolation, border replicated.
- **Primary test (fix experiment, 60 photos):** per variant, bad vs V0, exact McNemar, Holm over 3 variants. Words: "improves" only if bad falls AND Holm p < 0.05; "worsens" if bad rises AND Holm p < 0.05; else "no clear change". The fix was designed after seeing the failures of these same photos, so the result is exploratory.
- **Confirmation on new photos (Section Q2; rules logged 2026-11-11 before any new photo existed):** 40 photos of 20 new pages (Q01-Q20); methods **frozen**: V2 is the primary fix; V0 (original), V1 and V3 are run too. One exact paired test (McNemar), alpha 0.05. "Confirmed" only if bad falls AND p < 0.05; otherwise "not confirmed" and the numbers are reported as they are. Secondary (descriptive): by shot, by original size, lights on V2, pooled with the first 60 photos.

## 15. Fixed settings, in one table (reproducibility)

| Item | Value |
|---|---|
| Page | ECG-Image-Kit, 2200 x 1700 px, 200 dpi, 25 mm/s, 10 mm/mV |
| Digitiser | Open-ECG-Digitizer commit 97a15087 and the two weight files above; one settings file |
| Output | 1,000 Hz, microvolts, 10 s, 12 leads (NaN where a lead is not read) |
| Wrong HR | > 5 bpm (secondary 10 bpm) |
| No usable HR | fewer than 3 beats in lead II |
| HR measure | `nk.ecg_clean(neurokit)` -> `nk.ecg_peaks` -> mean of `nk.ecg_rate` (cleaned); original without the cleaning step |
| Seeds | 42 (first 50 and new 100; bridge six random), 43 (C+), 44 (P01-P30), 45 (Q01-Q20) |
| Logistic model | median imputation, standardisation, `class_weight="balanced"`, `max_iter=1000` |
| Cross-validation | 5-fold x 10, whole recordings held out |
| Bootstrap | recordings resampled with replacement, 2,000 (AUC), 1,000 (rates) |
| Straighten sizes | 2200 x 1700 (V2); 4400 x 3400 (V3); enlarge long side 4096 |
| Traffic light | AMBER 0.2585, RED 0.7823; guard on 14 features (not `amp_log`) |

## 16. Chronological list of analyses with status

| Date | Analysis | Status |
|---|---|---|
| Sweeps 1-2 | Damage sweeps, first 50 recordings | PRE-SPECIFIED (design); sweep 2 = repeat |
| 2026-11 early | New 100 held-out replication (C1, C2, C3, bridge run) | PRE-SPECIFIED (MASTER_PLAN) |
| 11-04 | Arm C: 40 real-capture recordings x 9 types | PRE-SPECIFIED design, small sample |
| 11-07 | D2 output check; C+ extension (100 more real recordings) | EXPLORATORY (rules logged before) |
| 11-08 | Clean-page diagnosis; cleaned measure | POST HOC |
| 11-08 | Multi-detector features (rule not met); can the photo predict on real captures (Section N) | EXPLORATORY |
| 11-08/10 | Own-phone set 1 (Section O) | EXPLORATORY confirmation; photo model criterion not met |
| 11-10 | Traffic-light safeguard (Section P) | EXPLORATORY |
| 11-10 | Straighten / enlarge fix experiment (Section Q) | EXPLORATORY |
| 11-11 | Confirmation of the fix on 40 new photos (Section Q2) | rules fixed before the photos; result pending |

## 17. Honest limits to say out loud

Simulated damage on computer-drawn pages (the digitiser was trained on a similar generator); one digitiser; 150 recordings in the sweeps; real captures hold fewer than 100 wrong readings; own-phone sets: one phone, one screen, photos of a laptop screen, 30 + 20 recordings, the two photos of a page are not independent; the heart-rate reference depends on the sampling rate for 16% of recordings and on the beat finder; intervals (QT, QTc) are only moderate even on clean recordings; the traffic light was trained on simulated damage and checks the signal, not the truth (irregular rhythms are flagged more often); no claim that the warning helps patients; not a medical device.
