# How the closest papers write their methods and formulae (read 2026-11-11, for our Methods section)

Read from the PDFs in `C:\ECG research\ECG_Papers\A._ECG_Digitisation` (04_8013 engrXiv, 03_2604 VLM-in-the-Loop, 01_2510 Open-ECG-Digitizer). Only the metric/method parts were checked this time; the earlier full reviews are in `section_A_review.md` etc.

## What they do (copy this style)
1. **Every metric has a numbered equation and every step is named.** engrXiv 8013 defines its score in three steps: alignment (Eq. 5, shift by cross-correlation, bound S = 100 samples), per-image SNR (Eq. 6), clipping at a floor (Eq. 7), dataset score (Eq. 8). They say why each step is there.
2. **Hidden choices are stated** (e.g. averaging in the linear domain lets easy images dominate). We should state ours in the same way: cleaned heart-rate measure, 5 bpm limit, how "no usable heart rate" is counted.
3. **Settings go in a table or appendix** (VLM-in-the-Loop: Appendix C hyperparameters, a table of thresholds such as Hough threshold 1200, grid coverage > 5 %). Our equivalent: one table with the digitiser commit, weights, image size (2200 x 1700), straightening size, thresholds of the traffic light.
4. **Thresholds are compared on named alternatives** (VLM-in-the-Loop compares an SQI threshold, which is too strict, with a Jrat threshold, which is too loose). Our traffic light should likewise be compared with simple alternatives (done: output check alone, detector agreement alone).
5. **Open-ECG-Digitizer reports SNR, RMSE, correlation per lead with mean and s.d.**; they do not report heart-rate error. Our heart-rate error (> 5 bpm) is a different, clinically closer measure, which is our stated difference.

## Formulae our Methods section must contain
- Heart rate: clean with the NeuroKit filter, find R-peaks, HR = mean(60 / RR) in bpm; original measure kept next to it.
- Wrong reading: |HR_digitised - HR_true| > 5 bpm; "no usable heart rate" = fewer than 3 beats in lead II; bad = either.
- The 15 output features (list with one-line definitions: Einthoven residual, Goldberger residual, RR coefficient of variation, ...).
- Logistic score p = 1 / (1 + exp(-(b0 + sum b_j z_j))), z = standardised feature; AMBER and RED thresholds from out-of-fold scores.
- AUC with recording-level bootstrap interval; grouped 5-fold x 10 cross-validation.
- Wilson interval for a proportion; exact McNemar test (binomial on the discordant pairs); Holm correction.
- Straightening: Otsu threshold -> largest bright quadrilateral -> perspective transform to 2200 x 1700 (cubic interpolation).
- Photo scores (five) with one-line definitions.

## Two papers filed in Downloads on 2026-11-09 (not in the main folder)
- Zhou et al., Life 2021, 11, 1013: ECG quality assessment with a deep model plus conditional GAN data augmentation (signal-quality classification).
- Huerta Herraiz et al., Entropy 2020, 22, 733: deep-learning quality assessment of AF recordings from portable/wearable devices.
Both are about judging the quality of an ECG SIGNAL, which is what our output check / traffic light does. They are related work for that part; they should be cited after the abstracts and their evaluation sections are read. Not yet done.
