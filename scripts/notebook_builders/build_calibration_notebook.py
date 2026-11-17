"""Builds colab/MediSense_Cardio_Calibration.ipynb -- the real next step after the methodology demo.

The methodology notebook proved the signals work (they detect a known rotation correctly). It did
NOT prove they are useful for the actual goal (docs/PLAN.md, Contribution 2): predicting whether a
damaged photo will cause a real measurement error, or a false-reassurance event, using only the
signals computable from the photo -- no ground truth.

This notebook does that, on the REAL 1,550-test study data, not a demo sample:
  Step 1: load the real results file (results_v2.csv) and the 50 real clean pages, from Drive.
  Step 2: regenerate all 1,550 degraded images locally (same degrade code as the sweep notebooks,
          pure CPU, no GPU) -- these were never saved anywhere, so they must be rebuilt.
  Step 3: compute all five Tier-1 signals for every one of the 1,550 images.
  Step 4: join the signals to the REAL measured errors by variant_id, and check the join worked.
  Step 5: correlation -- do the signals move together with the real error?
  Step 6: the actual test Contribution 2 must pass -- can the signals predict a real
          false-reassurance event? (AUC)
  Step 7: honest conclusion, stated from whatever the numbers actually say.
"""
import json
import os as _os

N_PAGES = int(_os.environ.get("N_PAGES", "50"))
IS_SUBSET = N_PAGES < 50


def md(*lines):
    return {"cell_type": "markdown", "metadata": {}, "source": [l + "\n" for l in lines]}


def code(*lines):
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [],
            "source": [l + "\n" for l in lines]}


cells = []

intro_lines = [
    "# MediSense-Cardio -- Calibration: do the quality signals predict the real error?"
    + (f" (quick {N_PAGES}-page check)" if IS_SUBSET else ""),
    "",
    "**Where this fits:** the previous notebook (Methodology, Explained) proved the tilt-detection",
    "method works on a known test case. This notebook is the actual next step of the project: check",
    "whether the five signals -- computed from a photo alone, no ground truth -- actually predict the",
    "real errors already measured in the big 1,550-test experiment. This is the real deliverable of",
    "Contribution 2 in the project plan, not a demo.",
]
if IS_SUBSET:
    intro_lines += [
        "",
        f"**This is the quick {N_PAGES}-page version**, for a fast live check: it uses only the first",
        f"{N_PAGES} of the 50 real study pages ({N_PAGES * 31} of the real 1,550 tests), so Step 3 finishes",
        "in well under a minute instead of several. The numbers below are real, not fabricated -- they are",
        "just computed on a smaller, honestly-labelled slice of the real study. The full 50-page version",
        "(`MediSense_Cardio_Calibration.ipynb`) is the one whose conclusion should be trusted/reported;",
        "this one is for demonstrating the method runs correctly, quickly.",
    ]
intro_lines += [
    "",
    "**How to use this notebook:** same as before -- read each explanation, run the code cell below",
    "it, look at the real output. Everything here runs on the real study data, not a small sample.",
]
cells.append(md(*intro_lines))

cells.append(md(
"## Step 1: load the real results and the real clean pages",
"",
"**What this does:** loads `results_v2.csv`, the file produced by the actual 1,550-test",
"experiment (the same file the papers' numbers come from), and the real clean, undamaged",
"pages the experiment started from" + (f" (first {N_PAGES} of 50, for speed)." if IS_SUBSET else "."),
))
step1_lines = [
"from google.colab import drive",
"drive.mount('/content/drive')",
"",
"import os, glob",
"import pandas as pd",
"",
"STUDY_DIR = '/content/drive/MyDrive/MediSense-Cardio-Study'",
"RESULTS_PATH = f'{STUDY_DIR}/results_v2.csv'",
"CLEAN_DIR = f'{STUDY_DIR}/images_clean'",
"",
"results = pd.read_csv(RESULTS_PATH)",
"print(f'Loaded {len(results)} rows from results_v2.csv (the real experiment).')",
"print(f'Columns: {list(results.columns)}')",
"",
"# IMPORTANT: images_clean on Drive may hold more pages than the 50 actually used in the",
"# real study (e.g. the wider sampling pool) -- picking any 50 by filename order would silently",
"# join against the wrong pages later. Keep only the clean files whose record is ACTUALLY one of",
"# the 50 records in results_v2.csv, so every kept page is guaranteed to join.",
"sample_records = set(results['record'].unique())",
"print(f'{len(sample_records)} distinct records in results_v2.csv (the real study sample).')",
"all_clean_files = sorted(glob.glob(f'{CLEAN_DIR}/*.png'))",
"clean_files = [p for p in all_clean_files",
"               if os.path.basename(p).replace('-0.png', '') in sample_records]",
"print(f'{len(clean_files)} of {len(all_clean_files)} files in images_clean match a real study record.')",
f"clean_files = clean_files[:{N_PAGES}]" + (f"  # quick check: only the first {N_PAGES} of the real study's 50 pages" if IS_SUBSET else ""),
"print(f'\\nUsing {len(clean_files)} real clean study pages.')",
"assert len(results) > 0 and len(clean_files) > 0, 'Could not find the real study files on Drive.'",
]
if not IS_SUBSET:
    step1_lines += [
        "assert len(clean_files) == len(sample_records), \\",
        "    'Expected every one of the real study records to have a matching clean file -- investigate before trusting anything below.'",
    ]
cells.append(code(*step1_lines))

cells.append(md(
"## Step 2: rebuild the 1,550 damaged pictures",
"",
"**What this does:** the damaged versions of each page were never saved anywhere -- the original",
"experiment measured them and moved on. So we rebuild them here, using the exact same damage code",
"as the sweep notebook (same kernel sizes, same angles, same everything), applied to the real",
"clean pages. This is pure image processing, no GPU needed -- it takes a couple of minutes for all",
"1,550, not the ~10 hours the original digitising experiment took.",
))
cells.append(code(
"import cv2",
"import numpy as np",
"",
"def degrade_blur(img, level):",
"    k = [3, 7, 11, 15, 21][level - 1]",
"    return cv2.GaussianBlur(img, (k, k), 0)",
"",
"def degrade_rotate(img, level):",
"    angle = [2, 5, 8, 12, 16][level - 1]",
"    h, w = img.shape[:2]",
"    M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)",
"    return cv2.warpAffine(img, M, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255))",
"",
"def degrade_jpeg(img, level):",
"    quality = [50, 30, 15, 8, 3][level - 1]",
"    ok, enc = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, quality])",
"    return cv2.imdecode(enc, cv2.IMREAD_COLOR)",
"",
"def degrade_resolution(img, level):",
"    factor = [0.75, 0.5, 0.35, 0.25, 0.15][level - 1]",
"    h, w = img.shape[:2]",
"    small = cv2.resize(img, (max(1, int(w * factor)), max(1, int(h * factor))), interpolation=cv2.INTER_AREA)",
"    return cv2.resize(small, (w, h), interpolation=cv2.INTER_LINEAR)",
"",
"def degrade_brightness(img, level):",
"    strength = [0.15, 0.3, 0.45, 0.6, 0.75][level - 1]",
"    h, w = img.shape[:2]",
"    gradient = np.tile(np.linspace(1.0, 1.0 - strength, w), (h, 1)).astype(np.float32)",
"    gradient = cv2.merge([gradient, gradient, gradient])",
"    return np.clip(img.astype(np.float32) * gradient, 0, 255).astype(np.uint8)",
"",
"def degrade_grid_contrast(img, level):",
"    strength = [0.15, 0.3, 0.45, 0.6, 0.75][level - 1]",
"    mean_val = img.mean()",
"    return np.clip(img.astype(np.float32) * (1 - strength) + mean_val * strength, 0, 255).astype(np.uint8)",
"",
"AXES = {'blur': degrade_blur, 'rotate': degrade_rotate, 'jpeg': degrade_jpeg,",
"        'resolution': degrade_resolution, 'brightness': degrade_brightness,",
"        'gridcontrast': degrade_grid_contrast}",
"LEVELS = [1, 2, 3, 4, 5]",
"print(f'{len(AXES)} damage types x {len(LEVELS)} levels + 1 clean = {len(AXES)*5+1} versions per page')",
))

cells.append(md(
"## Step 3: compute the five signals for every one of the 1,550 pictures",
"",
"**What this does:** the same five formulae from the Methodology notebook (brightness weighting,",
"Sobel gradient magnitude, the Hough line-voting equation, line angle, median), applied to every",
"damaged version of every real page. This is the slow cell -- expect roughly 1-3 minutes for all",
"1,550 images on Colab's CPU.",
))
cells.append(code(
"def compute_signals(img):",
"    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img",
"    blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())",
"    edges = cv2.Canny(gray, 50, 150)",
"    min_len = int(0.3 * gray.shape[1])",
"    lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, minLineLength=min_len, maxLineGap=10)",
"    if lines is None or len(lines) < 3:",
"        skew_deg = None",
"    else:",
"        arr = lines.reshape(-1, 4) if lines.ndim == 3 else lines",
"        devs = []",
"        for x1, y1, x2, y2 in arr:",
"            a = np.degrees(np.arctan2(y2 - y1, x2 - x1)) % 180",
"            d = a % 90",
"            devs.append(min(d, 90 - d))",
"        skew_deg = float(np.median(devs))",
"    f = np.fft.fftshift(np.fft.fft2(gray.astype(np.float32)))",
"    mag = np.abs(f)",
"    h, w = mag.shape; cy, cx = h // 2, w // 2",
"    yy, xx = np.ogrid[:h, :w]",
"    r = np.sqrt((yy - cy) ** 2 + (xx - cx) ** 2); r_max = min(cy, cx)",
"    resolution_score = float(mag[r > 0.5 * r_max].sum() / (mag.sum() + 1e-9))",
"    contrast_score = float(gray.std())",
"    col_grad = np.mean(np.abs(np.diff(gray.astype(np.float32), axis=1)), axis=0)",
"    col_grad = col_grad - col_grad.mean()",
"    spec = np.abs(np.fft.rfft(col_grad))",
"    if len(spec) < 4:",
"        blockiness_score = 0.0",
"    else:",
"        k0 = int(round(len(col_grad) / 8))",
"        band = spec[max(1, k0 - 1):k0 + 2].mean(); bg = np.median(spec[1:])",
"        blockiness_score = float(band / (bg + 1e-6))",
"    return dict(blur_score=blur_score, skew_deg=skew_deg, resolution_score=resolution_score,",
"                contrast_score=contrast_score, blockiness_score=blockiness_score)",
"",
"rows = []",
"for i, path in enumerate(clean_files):",
"    record = os.path.basename(path).replace('-0.png', '')",
"    img = cv2.imread(path)",
"    if img is None:",
"        continue",
"    rows.append(dict(variant_id=f'{record}-0__clean0', record=record, axis='clean', level=0,",
"                      **compute_signals(img)))",
"    for axis, fn in AXES.items():",
"        for level in LEVELS:",
"            degraded = fn(img, level)",
"            rows.append(dict(variant_id=f'{record}-0__{axis}{level}', record=record, axis=axis,",
"                              level=level, **compute_signals(degraded)))",
"    if (i + 1) % 10 == 0:",
"        print(f'  {i + 1}/{len(clean_files)} pages done ({len(rows)} variants so far)')",
"",
"signals_df = pd.DataFrame(rows)",
"print(f'\\nComputed signals for {len(signals_df)} variants (expected {len(clean_files) * 31}).')",
))

cells.append(md(
"## Step 4: join the signals to the REAL measured errors, and check the join worked",
"",
"**What this does:** matches each computed signal row to its real measured error by",
"`variant_id` -- the exact identifier the original experiment used. If the join produces fewer",
"matched rows than expected, that is a real problem to see and fix, not to hide.",
))
cells.append(code(
"merged = results.merge(signals_df, on='variant_id', how='inner', suffixes=('', '_sig'))",
"print(f'Matched {len(merged)} of {len(results)} real results rows to a computed signal row.')",
"if len(merged) < len(results) * 0.95:",
"    print('WARNING: fewer than 95% matched -- check that variant_id formats agree before trusting')",
"    print('any of the numbers below.')",
"else:",
"    print('Join looks correct.')",
"merged.head()",
))

cells.append(md(
"## Step 5: correlation -- do the signals move together with the real error?",
"",
"**What this does:** Spearman correlation (a rank-based correlation, robust to the fact that",
"error doesn't rise in a straight line) between each signal and the real measured QRS-duration",
"error -- the measurement the papers found most sensitive to damage.",
))
cells.append(code(
"from scipy.stats import spearmanr",
"",
"target = 'diff_qrs_ms' if 'diff_qrs_ms' in merged.columns else 'diff_bpm'",
"print(f'Correlating each signal against real {target}:\\n')",
"for sig in ['blur_score', 'skew_deg', 'resolution_score', 'contrast_score', 'blockiness_score']:",
"    sub = merged[[sig, target]].dropna()",
"    if len(sub) < 10:",
"        print(f'{sig:<20} not enough data ({len(sub)} rows)')",
"        continue",
"    rho, p = spearmanr(sub[sig], sub[target])",
"    print(f'{sig:<20} rho = {rho:+.3f}   (n={len(sub)}, p={p:.2e})')",
))

cells.append(md(
"## Step 6: the real test -- can the signals predict a false-reassurance event?",
"",
"**What this does:** this is the actual question Contribution 2 has to answer. Uses the SAME",
"QTc-based false-reassurance definition as the main 1,550-test study analysis (not a simplified",
"stand-in): ground truth QTc truly prolonged, digitised reading says normal, off by more than",
"10ms (not a threshold artefact), on a reliable record (<=20% unreadable) whose own clean image",
"was NOT already misclassified this way (baseline delineation noise, not degradation). Does a",
"simple model built only from the five signals predict which at-risk tests become a real",
"false-reassurance event? Reported as AUC (0.5 = no better than guessing, 1.0 = perfect). With",
"only a handful of real events, this number will have wide uncertainty -- reported honestly, not",
"dressed up.",
))
cells.append(code(
"from sklearn.linear_model import LogisticRegression",
"from sklearn.metrics import roc_auc_score",
"",
"# Reliable records only (<=20% of 31 variants unreadable), same threshold as the main study.",
"per_record_unreadable = merged.groupby('record')['dig_hr'].apply(lambda s: s.isna().sum())",
"reliable_records = set(per_record_unreadable[per_record_unreadable <= 6].index)",
"m = merged[merged['record'].isin(reliable_records)].copy()",
"print(f'Reliable records: {len(reliable_records)} of {merged[\"record\"].nunique()}')",
"",
"def classify_qtc(row):",
"    gt_ab, dig_ab = row['gt_qtc_abnormal'], row['dig_qtc_abnormal']",
"    if pd.isna(row['dig_qtc_ms']):",
"        return 'silent_drop'",
"    if pd.isna(gt_ab):",
"        return 'gt_unavailable'",
"    if bool(gt_ab) and not bool(dig_ab):",
"        return 'false_reassurance'",
"    if not bool(gt_ab) and bool(dig_ab):",
"        return 'false_alarm'",
"    if bool(gt_ab) and bool(dig_ab):",
"        return 'correct_abnormal'",
"    return 'correct_normal'",
"",
"m['qtc_outcome'] = m.apply(classify_qtc, axis=1)",
"",
"# A false-reassurance event only counts as real if the SAME record was also correctly",
"# classified on its own clean image (excludes baseline delineation noise, not degradation)",
"# and the digitized QTc is off from ground truth by more than 10ms (not a threshold artefact).",
"clean_outcome_by_record = m[m['axis'] == 'clean'].set_index('record')['qtc_outcome']",
"m['clean_was_correct'] = m['record'].map(clean_outcome_by_record) != 'false_reassurance'",
"m['real_fr'] = ((m['qtc_outcome'] == 'false_reassurance') & (m['diff_qtc_ms'] > 10)",
"                & m['clean_was_correct'])",
"",
"at_risk = m[(m['gt_qtc_abnormal'] == True) & (m['clean_was_correct'])].copy()",
"",
"print(f'At-risk tests (truly prolonged ground-truth QTc, reliable records): {len(at_risk)}')",
"print(f'Real false-reassurance events among them: {int(at_risk[\"real_fr\"].sum())}')",
"",
"feature_cols = ['blur_score', 'skew_deg', 'resolution_score', 'contrast_score', 'blockiness_score']",
"X = at_risk[feature_cols].fillna(at_risk[feature_cols].median())",
"y = at_risk['real_fr'].astype(int)",
"",
"if y.sum() < 3 or y.sum() == len(y):",
"    print('\\nToo few real events to fit a meaningful model -- reporting this honestly rather than')",
"    print('forcing a number that would not mean anything.')",
"else:",
"    clf = LogisticRegression(max_iter=1000, class_weight='balanced')",
"    clf.fit(X, y)",
"    pred = clf.predict_proba(X)[:, 1]",
"    auc = roc_auc_score(y, pred)",
"    print(f'\\nAUC (fit and evaluated on the same {len(at_risk)} at-risk tests, no held-out set yet):')",
"    print(f'{auc:.3f}')",
"    print('\\nNOTE: this is fit and checked on the SAME data, which is optimistic. A proper next step')",
"    print('is a held-out split once there are more real events to split across.')",
))

cells.append(md(
"## Conclusion -- stated from whatever the numbers above actually say",
"",
"Read the Step 5 and Step 6 output before writing anything here. If blur_score and",
"resolution_score correlate strongly with the real error (matching the paper's own finding that",
"only blur and low resolution matter), that is a genuine, useful result: it means an upload-time",
"quality gate is possible using signals that need no ground truth. If the AUC in Step 6 is close",
"to 0.5, that means the small number of real events is not yet enough to build a reliable",
"predictor, and the honest next step is more data, not a better-sounding claim.",
))

nb = {
    "cells": cells,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "name": "python3"},
        "language_info": {"name": "python"},
        "colab": {"provenance": [], "name": "MediSense_Cardio_Calibration.ipynb"},
    },
    "nbformat": 4,
    "nbformat_minor": 0,
}

import os
out_path = os.environ.get("NB_OUT", "MediSense_Cardio_Calibration.ipynb")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)
print(f"Wrote {out_path} -- {len(cells)} cells.")
