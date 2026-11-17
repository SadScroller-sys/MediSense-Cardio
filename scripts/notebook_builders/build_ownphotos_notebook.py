"""Builds colab/MediSense_Cardio_OwnPhotos_Kaggle.ipynb.

The user photographs ECG pages (ECG-Image-Kit pages P01-P30 shown on a laptop screen) with their own phone: 60 photos. This notebook (Kaggle, GPU) digitises every photo with the
SAME digitiser, commit, weights and settings as Arm C and computes the five photo scores with the SAME code as the competition-capture run. It saves, per photo: the 12-lead digitised signal
(.npz) and the photo scores. Everything else (matching photos to pages, reference heart rate, labels, frozen models) is done locally. Rules: docs/plan/analysis_plan_changes.md (2026-11-08).
Digitiser set-up cells and the photo-score function are copied verbatim from colab/MediSense_Cardio_ArmCext_All100_Kaggle.ipynb (asserted)."""
import json
import os

ROOT = "D:/Capstone Project"
src = json.load(open(f"{ROOT}/colab/MediSense_Cardio_ArmCext_All100_Kaggle.ipynb", encoding="utf-8"))["cells"]


def text(i):
    return "".join(src[i]["source"])


def md(t):
    return {"cell_type": "markdown", "metadata": {}, "source": [l + "\n" for l in t.split("\n")]}


def code(t):
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": [l + "\n" for l in t.split("\n")]}


# ---- verbatim pieces (asserted)
c_install, c_digitiser, c_config = text(6), text(7), text(8)
assert "pip', 'install'" in c_install and "def sh(" in c_install
assert "git clone https://github.com/Ahus-AIM/Open-ECG-Digitizer.git" in c_digitiser and "Digitiser ready." in c_digitiser
assert "def write_digitizer_config" in c_config and "target_num_samples: 10000" in c_config
sig_src = text(20)
sig_funcs = sig_src.split("SIG_PATH = ")[0].rstrip() + "\n"
assert "def compute_signals" in sig_funcs and "blockiness_score" in sig_funcs

cells = []
cells.append(md("""# MediSense-Cardio -- own-phone photos of ECG pages on a screen (Kaggle, GPU)

**Why:** to confirm on a NEW phone whether the five photo scores predict that the digitiser gives no output. Rules were fixed before any photo existed (docs/plan/analysis_plan_changes.md, 2026-11-08).
**What it does:** reads your 60 photos, digitises each one with the same digitiser and settings as the main study, computes the five photo scores, and saves the results. Matching the photos to the pages
and all the statistics are done afterwards on your computer.

**Steps (Kaggle):**
1. Put your 60 photos in one folder on your computer. Kaggle -> Create -> New Dataset -> upload the folder -> name it `ownphotos` -> Create (keep it Private).
2. New notebook -> File -> Import notebook -> upload this file.
3. Right panel -> Input -> Add Input -> your dataset `ownphotos`.
4. Settings: Accelerator = GPU T4 x2 (or P100), Internet = On.
5. Save Version -> Save & Run All (Commit). About 30-40 minutes. When the Logs show `ALL OWN PHOTOS COMPLETE`, open Output and download the zip. Tell me when it is in Downloads."""))
cells.append(md("## Step 1 -- Find the photos"))
cells.append(code("""import os, glob, json, time, shutil, subprocess, sys, datetime
import numpy as np, pandas as pd

WORK = '/kaggle/working'            # what is saved and can be downloaded
TMP = '/tmp/ownphotos'              # scratch space, not saved
INPUT_ROOT = '/kaggle/input'
DIG_DIR = f'{TMP}/Open-ECG-Digitizer'
os.makedirs(WORK, exist_ok=True); os.makedirs(TMP, exist_ok=True)

exts = ('.jpg', '.jpeg', '.png')
allfiles = [p for p in glob.glob(INPUT_ROOT + '/**/*', recursive=True) if os.path.isfile(p)]
photos = sorted(p for p in allfiles if p.lower().endswith(exts))
others = sorted(set(os.path.splitext(p)[1].lower() for p in allfiles if not p.lower().endswith(exts)))
print(f'{len(photos)} photo files found. Other file types present: {others}')
if any(e in others for e in ('.heic', '.heif')):
    raise SystemExit('STOPPED on purpose: some photos are HEIC (iPhone default). Set the iPhone camera to Most Compatible (JPEG) or convert them to JPG, upload again, and Run All.')
assert len(photos) > 0, 'No photos found. Right panel -> Input -> Add Input -> choose your dataset ownphotos. Then Run All again.'
names = [os.path.basename(p) for p in photos]
assert len(set(names)) == len(names), 'Two photos have the same file name: rename them so every name is different.'
print('first five:', names[:5])
if len(photos) != 60:
    print(f'NOTE: expected 60 photos, found {len(photos)}. The notebook will still run; tell me the number.')
all_variants = pd.DataFrame({'variant_id': [os.path.splitext(n)[0] for n in names], 'source_path': photos})"""))
cells.append(md("## Step 2 -- Install the tools and set up the digitiser (same as the main study)"))
cells.append(code(c_install))
cells.append(code(c_digitiser))
cells.append(code(c_config))
cells.append(code("""# Digitiser checkpoint, per photo. A photo is read with OpenCV (so the phone's rotation flag is applied) and saved as PNG for the digitiser; the photo scores use the same pixels.
FS_CANONICAL = 1000.0
OUT_NPZ = f'{WORK}/ownphotos_digitized_12lead'
os.makedirs(OUT_NPZ, exist_ok=True)
RESULTS_PATH = f'{WORK}/results_ownphotos.csv'
LEADS = ['I', 'II', 'III', 'aVR', 'aVL', 'aVF', 'V1', 'V2', 'V3', 'V4', 'V5', 'V6']

def run_batch(batch):
    imgs, outd = f'{TMP}/images_batch', f'{TMP}/digitized_batch'
    for d in (imgs, outd):
        if os.path.exists(d):
            shutil.rmtree(d)
    os.makedirs(imgs)
    meta = {}
    for _, v in batch.iterrows():
        im = cv2.imread(v['source_path'])
        meta[v['variant_id']] = (None if im is None else im.shape[0], None if im is None else im.shape[1])
        if im is not None:
            cv2.imwrite(f'{imgs}/{v["variant_id"]}.png', im)
    write_digitizer_config(imgs, outd)
    t0 = time.time()
    r = subprocess.run([sys.executable, '-m', 'src.digitize', '--config', f'{DIG_DIR}/batch_config.yml'], cwd=DIG_DIR, capture_output=True, text=True)
    rows = []
    for _, v in batch.iterrows():
        vid = v['variant_id']
        csv_path = f'{outd}/{vid}_timeseries_canonical.csv'
        row = {'variant_id': vid, 'img_h': meta[vid][0], 'img_w': meta[vid][1], 'has_output': False, 'n_II_samples': 0, 'raw_hr_II': None}
        if os.path.exists(csv_path):
            dg = pd.read_csv(csv_path)
            np.savez_compressed(f'{OUT_NPZ}/{vid}.npz', **{c: dg[c].to_numpy(dtype='float32') for c in dg.columns})
            row['has_output'] = True
            if 'II' in dg.columns:
                sig = dg['II'].dropna().to_numpy() / 1000.0
                row['n_II_samples'] = int(len(sig))
                try:
                    pk, _ = nk.ecg_peaks(sig, sampling_rate=FS_CANONICAL)
                    row['raw_hr_II'] = round(float(np.nanmean(nk.ecg_rate(pk, sampling_rate=FS_CANONICAL, desired_length=len(sig)))), 1)
                except Exception:
                    pass
        rows.append(row)
    return pd.DataFrame(rows), time.time() - t0, (r.stdout + r.stderr)

if os.path.exists(RESULTS_PATH):
    results_so_far = pd.read_csv(RESULTS_PATH)
    print(f'Resuming: {len(results_so_far)} photos already done')
else:
    results_so_far = pd.DataFrame()
done = set(results_so_far['variant_id']) if len(results_so_far) else set()
remaining = all_variants[~all_variants['variant_id'].isin(done)].reset_index(drop=True)
print(f'{len(all_variants)} photos in total, {len(remaining)} still to do.')"""))
cells.append(md("## Step 3 -- Digitise all photos (checkpointed; smoke test on two photos first)"))
cells.append(code("""smoke, secs, tool_out = run_batch(remaining.iloc[:2].reset_index(drop=True))
print(smoke.to_string())
print(f'smoke test took {secs:.0f} s for {len(smoke)} photos')
if not smoke['has_output'].any():
    print('The digitiser made no output for the first two photos. That can be a real result (screen photos often fail) but may also be a set-up problem. Last lines of its output:')
    print(tool_out[-1800:])
    if 'Traceback' in tool_out or 'Error' in tool_out[-1800:]:
        raise SystemExit('STOPPED on purpose: paste the output above into the chat.')

SUBBATCH_SIZE = 10
SESSION_TIME_BUDGET_S = 5 * 3600
session_start = time.time()
while len(remaining) > 0 and (time.time() - session_start) < SESSION_TIME_BUDGET_S:
    batch = remaining.iloc[:SUBBATCH_SIZE].reset_index(drop=True)
    batch_results, secs, _ = run_batch(batch)
    results_so_far = pd.concat([results_so_far, batch_results], ignore_index=True).drop_duplicates(subset='variant_id', keep='last')
    tmp_path = RESULTS_PATH + '.tmp'
    results_so_far.to_csv(tmp_path, index=False)
    os.replace(tmp_path, RESULTS_PATH)
    n_on_disk = len(pd.read_csv(RESULTS_PATH))
    assert n_on_disk == len(results_so_far), f'SAVE VERIFY FAILED: disk has {n_on_disk}, memory has {len(results_so_far)}'
    remaining = remaining.iloc[SUBBATCH_SIZE:].reset_index(drop=True)
    print(f'Checkpointed {len(batch)} photos ({secs/len(batch):.1f} s/photo). Done {len(results_so_far)}/{len(all_variants)}, {len(remaining)} remaining.')
print('ALL PHOTOS DIGITISED.' if len(remaining) == 0 else f'{len(remaining)} photos remaining: run this cell again.')
print(results_so_far.has_output.value_counts().to_string())"""))
cells.append(md("## Step 4 -- The five photo scores of every photo (same code as the competition-capture run)"))
cells.append(code(sig_funcs + """
SIG_PATH = f'{WORK}/ownphotos_quality_signals.csv'
rows_sig = []
for n, (_, v) in enumerate(all_variants.iterrows(), 1):
    img = cv2.imread(v['source_path'])
    if img is None:
        print('could not read', v['source_path'])
        continue
    rows_sig.append(dict(variant_id=v['variant_id'], **compute_signals(img)))
pd.DataFrame(rows_sig).to_csv(SIG_PATH, index=False)
chk = pd.read_csv(SIG_PATH)
print(f'Verified on disk: {len(chk)} rows in {SIG_PATH} (expected {len(all_variants)}).')
prov = {'written_utc': datetime.datetime.utcnow().isoformat() + 'Z', 'open_ecg_digitizer_commit': sh(f'git -C {DIG_DIR} rev-parse HEAD', show=False).stdout.strip() if os.path.isdir(DIG_DIR) else None,
        'device': device, 'n_photos': int(len(all_variants)), 'weights': sorted(os.listdir(f'{DIG_DIR}/weights')) if os.path.isdir(f'{DIG_DIR}/weights') else None}
json.dump(prov, open(f'{WORK}/ownphotos_provenance.json', 'w'), indent=2)
print(json.dumps(prov, indent=2))
print('ALL OWN PHOTOS COMPLETE. Download: results_ownphotos.csv, ownphotos_quality_signals.csv, ownphotos_provenance.json and the folder ownphotos_digitized_12lead.')"""))

nb = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "name": "python3", "language": "python"}, "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 5}
os.makedirs(f"{ROOT}/colab", exist_ok=True)
json.dump(nb, open(f"{ROOT}/colab/MediSense_Cardio_OwnPhotos_Kaggle.ipynb", "w", encoding="utf-8"), indent=1)
print("written", len(cells), "cells")
