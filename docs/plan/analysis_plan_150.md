# Analysis plan for the 150-recording study

Written 2026-11-04, before any result from the extension run exists. Anything added or changed after the data arrive goes into
`docs/analysis_plan_changes.md` (date, what, why) and is labelled **exploratory** in every document.

## 0. What is already known, and what is not
- The first 50 recordings (results_v2.csv) have been looked at many times. They shaped the damage types, the 5 bpm threshold and the
  choice of levels. They are the **development set**.
- The new 100 recordings (results/extension/selected_100.csv, chosen by fixed rules) have not been looked at. They are the
  **confirmation set**. The headline findings are judged on the confirmation set alone, and again on all 150.

## 1. Data and exclusions
- Development set: 50 recordings, 6 damage types x 5 levels + clean (31 versions). Confirmation set: 100 recordings, 6 types x levels 3 and 5 + clean (13 versions).
- Comparisons across both sets use levels 3 and 5 only. Levels 1, 2 and 4 are reported for the development set only.
- A recording is **unreliable** if more than 20% of its versions give no heart rate (first 50: more than 6 of 31, as before; new 100: more than 2 of 13). Unreliable
  recordings are excluded from rates and listed by name. The number excluded is reported.
- The unit of analysis is the **recording**, not the image. Confidence intervals: Wilson for simple proportions; recording-level bootstrap
  (2,000 resamples) for everything that pools versions of the same recording (rates over levels, AUC).

## 2. Definitions (fixed now)
- **Bad heart-rate reading**: no heart rate, or |digitised - reference| > 5 bpm. Secondary: > 10 bpm.
- **Reference heart rate**: computed by the sweep's detector on the 100 Hz record the page was drawn from (like for like). Recordings whose 100 Hz and
  500 Hz references differ by more than 5 bpm are marked **reference-uncertain**; every heart-rate result is reported with and without them.
- **PTB-XL flagged recording**: any non-empty value in baseline_drift, static_noise, burst_noise, electrodes_problems, extra_beats, pacemaker.
- **Interval measures** (QT, QTc): NeuroKit2 continuous-wavelet delineation, median over the 12 leads, applied to the saved digitised signals and to the
  original 12-lead record at the same sampling rate. PR and QRS are **not analysed** (NeuroKit2 does not track the commercial reference; see
  results/reference_vs_ptbxl_plus.md). QTc false reassurance (truth abnormal, digitised normal; female >= 460 ms, male >= 450 ms; Fridericia as the main
  formula, Bazett as sensitivity) is reported as "by this measurement method", never as a clinical rate.
- **Aligned SNR**: lead II, +-0.5 s shift, offset removed (notebook function aligned_snr). Descriptive only.

## 3. Confirmatory questions (the only ones with a verdict)
- **C1. Which damage causes wrong heart rates?** Prediction: at level 5, low resolution has the highest bad-reading rate and is at least 20%; blur is second and at
  least 10%; JPEG, brightness and grid fading are below 10%. Judged on the confirmation set: C1 is **supported** if resolution (level 5) has a higher point estimate
  than every other damage type at level 5 and is at least 20%. It is **not supported** otherwise, and we say so.
- **C2. Is the background failure mostly the recording?** Prediction: among recordings with no PTB-XL flag and not reference-uncertain, bad-reading rates for rotation,
  JPEG, brightness and grid fading at level 5 are 5% or lower, and clean images are never bad. **Supported** if all four are 5% or lower (point estimates).
- **C3. Does the photo-quality detector work?** Train on the development set (50 recordings, all their versions); score once on the confirmation set. Same five scores,
  same logistic regression, same primary target (bad heart-rate reading). **Verdict rule:** call it **usable** only if the AUC is at least 0.70 and the lower
  bound of its 95% recording-level interval is above 0.60. Between 0.60 and 0.70, or with a lower bound at or below 0.60, we report that it **does not
  demonstrate usable detection**. We do not change the features, model or target after seeing the confirmation result.

## 4. Exploratory analyses (reported, not judged; labelled as such)
- Section A: aligned SNR by damage type and level; clean-image SNR; Spearman correlation of SNR with heart-rate error; cases with acceptable SNR but wrong heart rate.
- Section B: effect of removing PTB-XL-flagged and reference-uncertain recordings; QT and QTc agreement with 12SL on the original signals; reference-HR check on the new 100.
- Section C: bad-reading rate and error relative to the clean image, per damage type and level, with intervals; damage types we did not test (glare, creases, perspective, handwriting).
- Section D: cross-validation grouped by recording on all 150; leave-one-damage-type-out; adding the digitiser's unreadable-lead count as a feature; one standard no-reference quality baseline.
- Section E: flag the top 10, 20 and 30% of photos: share of bad readings caught and bad-reading rate among accepted photos. No statistical guarantee is claimed. The action after a flag (retake the photo, or human check) is stated; its effect on people is untested.
- Section G: calibration of the detector's probabilities (calibration curve and slope); sample-size statement against Riley's criteria; CLAIM items met and not met.
- Section F: no analysis.

## 5. Rules for running and reporting
- No re-running Colab to "improve" numbers. A failed run is repeated unchanged. All runs and their dates are logged in docs/PROGRESS-LOG.md.
- Every number in the papers, deck and diary is copied from one summary file, results/FINAL_NUMBERS.md, created at the freeze (about 10 Nov). No analysis starts after the freeze.
- Limits stated in every document: simulated damage on computer-drawn pages, one digitiser (Open-ECG-Digitizer, tool commit and weights recorded in extension_provenance.json),
  150 recordings, the digitiser was trained on images from the same generator family, intervals are method-based, PR and QRS excluded.
