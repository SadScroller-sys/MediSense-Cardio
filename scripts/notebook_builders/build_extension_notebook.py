"""Builds colab/MediSense_Cardio_Extension_150.ipynb: extends the study from 50 to 150 recordings.

Reads (never modifies) colab/MediSense_Cardio_FullSweep_v2_Intervals.ipynb and results/extension/selected_100.csv.
Everything proven in the v2 sweep notebook is copied verbatim; only these things change (each replacement is asserted):
  * Step 1: the 100 selected recordings are embedded in the notebook (no file upload needed) instead of drawing a sample
  * Step 2: also fetches the 500 Hz version of each recording (reference intervals at 500 Hz, as in the journal analysis)
  * Step 4: levels 3 and 5 only (6 damage types x 2 levels + clean = 13 versions per recording = 1,300 images)
  * Step 5/7: results go to results_extension.csv (v2 results are never touched)
  * Step 7: the digitised lead II of every image is SAVED to Drive, and a correctly aligned SNR is computed
    (the v2 SNR compared 100 Hz truth with 1,000 Hz output sample by sample and was invalid)
  * provenance (tool commits, weights) is written to Drive
"""
import ast
import json
import os
import re

import pandas as pd

ROOT = "D:/Capstone Project"
v2 = json.load(open(f"{ROOT}/colab/MediSense_Cardio_FullSweep_v2_Intervals.ipynb", encoding="utf-8"))["cells"]
sel = pd.read_csv(f"{ROOT}/results/extension/selected_100.csv")
assert len(sel) == 100 and sel["sex_lbl"].value_counts().to_dict() == {"male": 51, "female": 49}


def src(i):
    return "".join(v2[i]["source"])


def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": [l + "\n" for l in text.split("\n")]}


def code(text):
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [],
            "source": [l + "\n" for l in text.split("\n")]}


def copy_cell(i):
    c = json.loads(json.dumps(v2[i]))
    c["outputs"] = []
    c["execution_count"] = None
    return c


def sub(text, old, new, count=1):
    assert text.count(old) == count, f"expected {count} occurrence(s) of {old[:60]!r}, found {text.count(old)}"
    return text.replace(old, new)


cells = []

# ----------------------------------------------------------------------------------------------- intro
cells.append(md("""# MediSense-Cardio -- Extension: 100 more recordings (50 -> 150)

**What this notebook does:** adds **100 new PTB-XL recordings** to the study (the first 50 are in `results_v2.csv` and are
not touched). The new recordings were chosen before any result was seen (rules in `scripts/analysis/select_extension_100.py`):
human-validated labels, 51 male + 49 female so the combined 150 is 75 + 75, 50 normal + 50 abnormal, about 30% carrying a
PTB-XL quality flag. They come from the same 500-record pool as the first 50, so their clean pages are already on Drive.

**Damage design (smaller than the first sweep, to fit the time):** the same **6 damage types**, but only **levels 3 and 5**
(middle and worst) + the clean image = **13 versions per recording = 1,300 images** (about 7 hours on a Colab GPU).
Levels 1, 2 and 4 are not run for the new recordings.

**What is new compared with the first sweep (v2):**
1. **All 12 digitised leads of every image are saved to Drive** (`extension_digitized_12lead/`, one compressed file per image,
   about 200 MB in total), so new metrics, for example interval measurements that use several leads, never need another
   10-hour digitising run.
2. A **correctly aligned SNR** is computed (the v2 SNR compared a 100 Hz truth with a 1,000 Hz output sample by sample and was invalid).
3. Reference intervals are also computed from the **500 Hz** record (`gt500_*` columns), as in the journal analysis.
4. Tool versions (Open-ECG-Digitizer, ecg-image-kit commit, weights) are written to `extension_provenance.json`.

Results go to `results_extension.csv` (a separate file). **The notebook is resumable:** `Runtime -> Run all`; if it stops,
run it again until the last cell of Step 7 prints `ALL VARIANTS COMPLETE`."""))

# ----------------------------------------------------------------------------------------------- step 0
for i in (1, 2, 3):
    cells.append(copy_cell(i))

# ----------------------------------------------------------------------------------------------- step 1
cells.append(md("""## Step 1 -- The 100 selected recordings (embedded below)

These are fixed. The cell checks that none of them is among the first 50 recordings (`results_v2.csv` on Drive) and, in the next
cell, that the PTB-XL label file agrees with the embedded sex of every recording."""))
rows = sel[["ecg_id", "filename_lr", "sex_lbl", "age", "diagnostic_class", "is_abnormal", "flagged"]].to_dict("records")
# empty values must become None: repr(float('nan')) is the bare word nan, which is not valid Python in the notebook
rows = [{k: (None if isinstance(v, float) and v != v else v) for k, v in r.items()} for r in rows]
assert not any(isinstance(v, float) and v != v for r in rows for v in r.values())
row_lines = ",\n".join("    " + repr(r) for r in rows)
cells.append(code(f"""import pandas as pd, numpy as np, os, ast, ssl, urllib.request

SELECTED = [
{row_lines}
]
sample = pd.DataFrame(SELECTED)
assert len(sample) == 100 and sample['ecg_id'].is_unique
print(f"Embedded selection: {{len(sample)}} recordings -- sex {{sample['sex_lbl'].value_counts().to_dict()}}, "
      f"abnormal {{int(sample['is_abnormal'].sum())}}, flagged {{int(sample['flagged'].sum())}}.")

V2_RESULTS = f'{{STUDY_DIR}}/results_v2.csv'
if os.path.exists(V2_RESULTS):
    first50 = set(pd.read_csv(V2_RESULTS)['record'].unique())
    new_ids = set(sample['filename_lr'].str.split('/').str[-1])
    assert not (first50 & new_ids), f"overlap with the first 50: {{sorted(first50 & new_ids)[:5]}}"
    print(f"No overlap with the {{len(first50)}} records already in results_v2.csv.")
else:
    print("results_v2.csv not found on Drive: overlap check skipped.")
sample.head()"""))
cells.append(code("""BASE = 'https://physionet.org/files/ptb-xl/1.0.3/'
ctx = ssl.create_default_context()
with urllib.request.urlopen(BASE + 'ptbxl_database.csv', context=ctx) as r:
    with open('ptbxl_database_ext.csv', 'wb') as f:
        f.write(r.read())
dbx = pd.read_csv('ptbxl_database_ext.csv')[['ecg_id', 'sex', 'age', 'filename_hr', 'validated_by_human']]
sample = sample.merge(dbx[['ecg_id', 'sex', 'filename_hr', 'validated_by_human']], on='ecg_id', how='left')
assert sample['sex'].notna().all(), 'every selected record must be found in the PTB-XL label file'
# PTB-XL convention: 0 = male, 1 = female
assert (sample['sex'].map({0: 'male', 1: 'female'}) == sample['sex_lbl']).all(), 'embedded sex disagrees with PTB-XL'
assert sample['validated_by_human'].all(), 'every selected record must have human-validated labels'
print('Sex, ids and human-validation of all 100 recordings agree with the PTB-XL label file.')"""))

# ----------------------------------------------------------------------------------------------- step 2
cells.append(md("""## Step 2 -- Fetch the recordings (100 Hz as in the first sweep, and 500 Hz for the reference intervals)"""))
s9 = src(9)
s9 = sub(s9, "os.makedirs('/content/data/full', exist_ok=True)",
         "os.makedirs('/content/data/full', exist_ok=True)\nos.makedirs('/content/data/full500', exist_ok=True)")
s9 = sub(s9, "    record_ids.append(rid)",
         "    if not os.path.exists(f'/content/data/full500/{rid}.hea'):\n"
         "        rel_hr = os.path.dirname(row['filename_hr']); rid_hr = os.path.basename(row['filename_hr'])\n"
         "        rec_hr = wfdb.rdrecord(rid_hr, pn_dir=f'ptb-xl/1.0.3/{rel_hr}')\n"
         "        wfdb.wrsamp(rid, fs=rec_hr.fs, units=rec_hr.units, sig_name=rec_hr.sig_name,\n"
         "                    p_signal=rec_hr.p_signal, write_dir='/content/data/full500')\n"
         "    record_ids.append(rid)")
cells.append(code(s9))

# ----------------------------------------------------------------------------------------------- step 3 (verbatim)
for i in (10, 11, 12, 13):
    cells.append(copy_cell(i))

# ----------------------------------------------------------------------------------------------- step 4
cells.append(md("""## Step 4 -- The 6 damage types, levels 3 and 5 only, and the variant list

Identical damage code to the first sweep (reused verbatim). Only the list of levels is shorter: level 3 (middle) and level 5
(worst). With the clean image that is 6 x 2 + 1 = **13 versions per recording**."""))
s15 = src(15)
s15 = sub(s15, "LEVELS = [1, 2, 3, 4, 5]", "LEVELS = [3, 5]  # extension: middle and worst level only")
s15 = sub(s15, "x (6 axes x 5 levels + 1 clean) = {len(clean_images) * 31}).",
          "x (6 axes x {len(LEVELS)} levels + 1 clean) = {len(clean_images) * (6 * len(LEVELS) + 1)}).")
cells.append(code(s15))

# ----------------------------------------------------------------------------------------------- step 5
cells.append(md("""## Step 5 -- Load the results checkpoint and compute what is left

Separate file `results_extension.csv`; `results_v2.csv` (the first 50 recordings) is never read for writing."""))
s17 = src(17)
s17 = sub(s17, "results_v2.csv", "results_extension.csv")
cells.append(code(s17))

# ----------------------------------------------------------------------------------------------- step 6 (verbatim) + provenance
cells.append(copy_cell(18))
for i in (19, 20, 21):
    cells.append(copy_cell(i))
cells.append(code("""import subprocess, json, datetime

def sh(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.strip()

prov = {
    'written_utc': datetime.datetime.utcnow().isoformat() + 'Z',
    'open_ecg_digitizer_commit': sh('git -C /content/Open-ECG-Digitizer rev-parse HEAD'),
    'ecg_image_kit_commit': sh('git -C /content/ecg-image-kit rev-parse HEAD'),
    'digitizer_weights': sorted(os.listdir('/content/Open-ECG-Digitizer/weights')) if os.path.isdir('/content/Open-ECG-Digitizer/weights') else [],
    'levels': LEVELS,
    'axes': list(AXES.keys()),
    'n_records': len(record_ids),
    'device': device,
}
with open(f'{STUDY_DIR}/extension_provenance.json', 'w') as f:
    json.dump(prov, f, indent=2)
print(json.dumps(prov, indent=2))"""))

# ----------------------------------------------------------------------------------------------- step 7
cells.append(md("""## Step 7 -- Digitise in checkpointed sub-batches (same loop as the first sweep)

Each sub-batch: damage the images, digitise them, compute heart rate / PR / QRS / QT / QTc (100 Hz truth, as in the first sweep,
and 500 Hz truth), compute the aligned SNR, **save the digitised lead II to Drive**, then save the results file and read it back to
verify. If the notebook stops, run it again."""))
s23 = src(23)

aligned_snr_fn = '''def aligned_snr(gt500, dig_1000hz):
    """Challenge-style aligned SNR on one lead (lead II), in dB.
    dig_1000hz is the digitised signal at 1,000 Hz (mV); gt500 is the 500 Hz reference (mV).
    The digitised signal is brought to 500 Hz, both means are removed (vertical offset), and the best time shift within
    +-0.5 s is applied before SNR = 10*log10(sum(gt^2) / sum((dig - gt)^2)). Also returns the shift (ms) and Pearson r."""
    from scipy.signal import resample_poly, correlate, correlation_lags
    assert FS_CANONICAL == 1000.0
    d = resample_poly(np.asarray(dig_1000hz, dtype=float), 1, 2)
    g = np.asarray(gt500, dtype=float)
    n = min(len(g), len(d))
    if n < 500:
        return float('nan'), float('nan'), float('nan')
    g = g[:n] - np.mean(g[:n]); x = d[:n] - np.mean(d[:n])
    max_lag = 250  # 0.5 s at 500 Hz
    c = correlate(g, x, mode='full'); lags = correlation_lags(len(g), len(x), mode='full')
    keep = (lags >= -max_lag) & (lags <= max_lag)
    best = int(lags[keep][np.argmax(c[keep])])  # g[n + best] is aligned with x[n]
    if best >= 0:
        g2 = g[best:]; x2 = x[:len(g2)]
    else:
        x2 = x[-best:]; g2 = g[:len(x2)]
    g2 = g2 - np.mean(g2); x2 = x2 - np.mean(x2)
    noise = np.sum((x2 - g2) ** 2)
    if noise <= 0 or np.sum(g2 ** 2) <= 0:
        return float('nan'), float('nan'), float('nan')
    snr = float(10 * np.log10(np.sum(g2 ** 2) / noise))
    pcc = float(np.corrcoef(g2, x2)[0, 1])
    return snr, best / 500.0 * 1000.0, pcc

'''
s23 = sub(s23, "def compute_metrics(batch_df, digitized_dir):",
          "os.makedirs(f'{STUDY_DIR}/extension_digitized_II', exist_ok=True)\n\n" + aligned_snr_fn + "def compute_metrics(batch_df, digitized_dir):")

gt500_block = """        # Reference values from the 500 Hz record (as in the journal analysis); NaN if it cannot be read.
        gt500_sig = None
        try:
            rec500 = wfdb.rdrecord(f'/content/data/full500/{gt_rid}')
            gt500_sig = rec500.p_signal[:, rec500.sig_name.index('II')]
            gt500_hr = np.nanmean(nk.ecg_rate(nk.ecg_peaks(gt500_sig, sampling_rate=rec500.fs)[0],
                                              sampling_rate=rec500.fs, desired_length=len(gt500_sig)))
            gt500_iv = extract_intervals(gt500_sig, rec500.fs, gt500_hr)
        except Exception:
            gt500_hr = float('nan')
            gt500_iv = {'pr_ms': float('nan'), 'qrs_ms': float('nan'), 'qt_ms': float('nan'), 'qtc_ms': float('nan')}
        row.update({
            'gt500_hr': round(gt500_hr, 1) if not np.isnan(gt500_hr) else None,
            'gt500_pr_ms': round(gt500_iv['pr_ms'], 1) if not np.isnan(gt500_iv['pr_ms']) else None,
            'gt500_qrs_ms': round(gt500_iv['qrs_ms'], 1) if not np.isnan(gt500_iv['qrs_ms']) else None,
            'gt500_qt_ms': round(gt500_iv['qt_ms'], 1) if not np.isnan(gt500_iv['qt_ms']) else None,
            'gt500_qtc_ms': round(gt500_iv['qtc_ms'], 1) if not np.isnan(gt500_iv['qtc_ms']) else None,
        })

        if not os.path.exists(csv_path):"""
s23 = sub(s23, "        if not os.path.exists(csv_path):", gt500_block)

s23 = sub(s23, "'diff_pr_ms': None, 'diff_qrs_ms': None,", "'diff_pr_ms': None, 'diff_qrs_ms': None,")  # sanity: the anchor must exist
s23 = sub(s23, "row.update({'dig_hr': None, 'diff_bpm': None, 'snr_db': None,",
          "row.update({'dig_hr': None, 'diff_bpm': None, 'snr_aligned_db': None, 'snr_lag_ms': None, 'snr_pcc': None,")

s23 = sub(s23, "        dig_signal = digitized['II'].dropna().to_numpy() / 1000.0\n",
          "        dig_signal = digitized['II'].dropna().to_numpy() / 1000.0\n"
          "        # keep ALL 12 leads exactly as the digitiser wrote them (microvolts, 1,000 Hz, NaN where a lead is missing)\n"
          "        np.savez_compressed(f'{STUDY_DIR}/extension_digitized_12lead/{v[\"variant_id\"]}.npz',\n"
          "                            **{c: digitized[c].to_numpy(dtype='float32') for c in digitized.columns})\n")
s23 = sub(s23, "os.makedirs(f'{STUDY_DIR}/extension_digitized_II', exist_ok=True)",
          "os.makedirs(f'{STUDY_DIR}/extension_digitized_12lead', exist_ok=True)")

snr_old = re.compile(r"        snr_db = None\n        if len\(dig_signal\) > 10:\n.*?snr_db = float\(10 \* np\.log10\(signal_power / noise_power\)\)\n", re.S)
assert len(snr_old.findall(s23)) == 1, "old SNR block not found exactly once"
s23 = snr_old.sub("""        snr_aligned, snr_lag, snr_pcc = float('nan'), float('nan'), float('nan')
        if len(dig_signal) > 10 and gt500_sig is not None:
            snr_aligned, snr_lag, snr_pcc = aligned_snr(gt500_sig, dig_signal)
""", s23)
s23 = sub(s23, "            'snr_db': round(snr_db, 1) if snr_db is not None else None,\n",
          "            'snr_aligned_db': round(snr_aligned, 2) if not np.isnan(snr_aligned) else None,\n"
          "            'snr_lag_ms': round(snr_lag, 1) if not np.isnan(snr_lag) else None,\n"
          "            'snr_pcc': round(snr_pcc, 3) if not np.isnan(snr_pcc) else None,\n")

s23 = sub(s23, "results_v2_backup_", "results_extension_backup_")
s23 = sub(s23, "rows in results_v2.csv", "rows in results_extension.csv")
cells.append(code(s23))

# ----------------------------------------------------------------------------------------------- step 8 (summary, copied)
cells.append(md("""## Step 8 -- Results overview (uses everything completed so far, across all sessions)

Safe to run at any point. It also shows the new aligned SNR next to the heart-rate error."""))
cells.append(copy_cell(25))
cells.append(code("""if len(results_so_far) > 0:
    print('Aligned SNR (dB) by damage type and level (median over recordings):')
    display(results_so_far.groupby(['axis', 'level'])['snr_aligned_db'].median().round(1).unstack())
    c = results_so_far[results_so_far['axis'] == 'clean']['snr_aligned_db']
    print(f"Clean images: median aligned SNR {c.median():.1f} dB (n={int(c.notna().sum())}); "
          f"median |time shift| {results_so_far[results_so_far['axis']=='clean']['snr_lag_ms'].abs().median():.0f} ms")"""))
cells.append(copy_cell(26))

nb = {
    "cells": cells,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "name": "python3"},
        "language_info": {"name": "python"},
        "colab": {"provenance": [], "name": "MediSense_Cardio_Extension_150.ipynb"},
    },
    "nbformat": 4,
    "nbformat_minor": 0,
}

# ----------------------------------------------------------------------------------------------- checks
magic = re.compile(r"^\s*(!|%)")
for n, c in enumerate(cells):
    if c["cell_type"] != "code":
        continue
    text = "".join(c["source"])
    text = "\n".join((l[: len(l) - len(l.lstrip())] + "pass" if magic.match(l) else l) for l in text.split("\n"))
    try:
        ast.parse(text)
    except SyntaxError as e:
        raise SystemExit(f"cell {n} does not compile: {e}")
out_path = os.environ.get("NB_OUT", f"{ROOT}/colab/MediSense_Cardio_Extension_150.ipynb")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)
print(f"Wrote {out_path}: {len(cells)} cells, all code cells compile.")
