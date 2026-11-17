"""Builds colab/MediSense_Cardio_FixExperiment_Kaggle.ipynb (step 4: simple fixes for angled, low-resolution photos of a screen).
Rules fixed before the run: docs/plan/analysis_plan_changes.md (2026-11-10, 'Simple-fix experiment'). Uses the same 60 photos (Kaggle dataset `ownphotos`), makes V1 enlarge, V2 straighten, V3 straighten+enlarge,
digitises the 180 images with the same digitiser set-up cells as Arm C (copied verbatim, asserted). The preprocessing code is copied from scripts/preprocess/page_straighten.py."""
import ast
import json

ROOT = "D:/Capstone Project"
src = json.load(open(f"{ROOT}/colab/MediSense_Cardio_ArmCext_All100_Kaggle.ipynb", encoding="utf-8"))["cells"]


def t(i):
    return "".join(src[i]["source"])


c_install, c_dig, c_cfg = t(6), t(7), t(8)
assert "pip', 'install'" in c_install and "Digitiser ready." in c_dig and "def write_digitizer_config" in c_cfg
page = open(f"{ROOT}/scripts/preprocess/page_straighten.py", encoding="utf-8").read()
page_code = page.split('"""', 2)[2].lstrip()
assert "def straighten" in page_code and "def enlarge" in page_code


def md(x):
    return {"cell_type": "markdown", "metadata": {}, "source": [l + "\n" for l in x.split("\n")]}


def code(x):
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": [l + "\n" for l in x.split("\n")]}


cells = [
    md("""# MediSense-Cardio -- simple fixes for angled, low-resolution photos (Kaggle, GPU)

**Why:** angled photos of an ECG page on a screen failed most often (Section O). Do simple preparations before the digitiser reads the photo reduce the failures? Rules were fixed before this run (docs/plan/analysis_plan_changes.md, 2026-11-10).
**What it does:** takes the same 60 photos, makes three prepared versions of each (V1 enlarge, V2 straighten the page, V3 straighten and enlarge), digitises all 180 images with the same digitiser and settings, and saves the results. The comparison with the originals is done afterwards on your computer.

**Steps (Kaggle):**
1. New notebook -> File -> Import notebook -> upload this file.
2. File -> Add input -> choose your dataset `ownphotos` (the same 60 photos; already on your Kaggle account).
3. Settings: Accelerator = GPU, Internet = On.
4. Save Version -> Save & Run All (Commit). About 1 to 1.5 hours. When the Logs show `ALL PREPARED PHOTOS DIGITISED`, open Output, download the zip and tell me."""),
    md("## Step 1 -- Find the photos and make the three prepared versions"),
    code("""import os, glob, json, time, shutil, subprocess, sys, datetime
import numpy as np, pandas as pd
WORK = '/kaggle/working'; TMP = '/tmp/fixexp'; INPUT_ROOT = '/kaggle/input'
DIG_DIR = f'{TMP}/Open-ECG-Digitizer'
os.makedirs(WORK, exist_ok=True); os.makedirs(TMP, exist_ok=True)
photos = sorted(p for p in glob.glob(INPUT_ROOT + '/**/*', recursive=True) if os.path.isfile(p) and p.lower().endswith(('.jpg', '.jpeg', '.png')))
print(f'{len(photos)} photo files found')
assert len(photos) == 60, 'expected the 60 photos of the dataset ownphotos: File -> Add input -> ownphotos'
names = [os.path.basename(p) for p in photos]
assert len(set(names)) == 60"""),
    code(page_code),
    code("""VAR_DIR = f'{TMP}/variants'; os.makedirs(VAR_DIR, exist_ok=True)
rows = []; found = {}
for p in photos:
    stem = os.path.splitext(os.path.basename(p))[0]
    img = cv2.imread(p)
    v1 = enlarge(img)
    v2, ok2 = straighten(img, 2200, 1700)
    v3, ok3 = straighten(img, 4400, 3400)
    found[stem] = bool(ok2 and ok3)
    for tag, im in (('V1_enlarge', v1), ('V2_straighten', v2), ('V3_straighten_big', v3)):
        path = f'{VAR_DIR}/{stem}__{tag}.png'
        cv2.imwrite(path, im)
        rows.append({'variant_id': f'{stem}__{tag}', 'photo': stem, 'variant': tag, 'source_path': path, 'page_found': found[stem] if tag != 'V1_enlarge' else True,
                     'img_h': im.shape[0], 'img_w': im.shape[1]})
all_variants = pd.DataFrame(rows)
all_variants.drop(columns='source_path').to_csv(f'{WORK}/fixexp_variants.csv', index=False)
print(len(all_variants), 'prepared images; photos where the page was found:', sum(found.values()), 'of 60')"""),
    md("## Step 2 -- Install the tools and set up the digitiser (same as the main study)"),
    code(c_install), code(c_dig), code(c_cfg),
    code("""FS_CANONICAL = 1000.0
OUT_NPZ = f'{WORK}/fixexp_digitized_12lead'; os.makedirs(OUT_NPZ, exist_ok=True)
RESULTS_PATH = f'{WORK}/results_fixexp.csv'
def run_batch(batch):
    imgs, outd = f'{TMP}/images_batch', f'{TMP}/digitized_batch'
    for d in (imgs, outd):
        if os.path.exists(d): shutil.rmtree(d)
    os.makedirs(imgs)
    for _, v in batch.iterrows():
        shutil.copy(v['source_path'], f'{imgs}/{v["variant_id"]}.png')
    write_digitizer_config(imgs, outd)
    t0 = time.time()
    r = subprocess.run([sys.executable, '-m', 'src.digitize', '--config', f'{DIG_DIR}/batch_config.yml'], cwd=DIG_DIR, capture_output=True, text=True)
    rows = []
    for _, v in batch.iterrows():
        vid = v['variant_id']; csv_path = f'{outd}/{vid}_timeseries_canonical.csv'
        row = {'variant_id': vid, 'has_output': False, 'n_II_samples': 0}
        if os.path.exists(csv_path):
            dg = pd.read_csv(csv_path)
            np.savez_compressed(f'{OUT_NPZ}/{vid}.npz', **{c: dg[c].to_numpy(dtype='float32') for c in dg.columns})
            row['has_output'] = True
            if 'II' in dg.columns: row['n_II_samples'] = int(dg['II'].notna().sum())
        rows.append(row)
    return pd.DataFrame(rows), time.time() - t0, (r.stdout + r.stderr)
results_so_far = pd.read_csv(RESULTS_PATH) if os.path.exists(RESULTS_PATH) else pd.DataFrame()
done = set(results_so_far['variant_id']) if len(results_so_far) else set()
remaining = all_variants[~all_variants['variant_id'].isin(done)].reset_index(drop=True)
print(f'{len(all_variants)} images in total, {len(remaining)} still to do.')"""),
    md("## Step 3 -- Digitise all 180 prepared images (checkpointed; smoke test first)"),
    code("""smoke, secs, tool_out = run_batch(remaining.iloc[:2].reset_index(drop=True))
print(smoke.to_string()); print(f'smoke test took {secs:.0f} s for 2 images')
if not smoke['has_output'].any() and ('Traceback' in tool_out or 'Error' in tool_out[-1800:]):
    print(tool_out[-1800:]); raise SystemExit('STOPPED on purpose: paste the output above into the chat.')
SUBBATCH_SIZE = 10; SESSION_TIME_BUDGET_S = 5 * 3600; session_start = time.time()
while len(remaining) > 0 and (time.time() - session_start) < SESSION_TIME_BUDGET_S:
    batch = remaining.iloc[:SUBBATCH_SIZE].reset_index(drop=True)
    br, secs, _ = run_batch(batch)
    results_so_far = pd.concat([results_so_far, br], ignore_index=True).drop_duplicates(subset='variant_id', keep='last')
    tmp_path = RESULTS_PATH + '.tmp'; results_so_far.to_csv(tmp_path, index=False); os.replace(tmp_path, RESULTS_PATH)
    assert len(pd.read_csv(RESULTS_PATH)) == len(results_so_far), 'SAVE VERIFY FAILED'
    remaining = remaining.iloc[SUBBATCH_SIZE:].reset_index(drop=True)
    print(f'Checkpointed {len(batch)} images ({secs/len(batch):.1f} s/image). Done {len(results_so_far)}/{len(all_variants)}, {len(remaining)} remaining.')
print('ALL PREPARED PHOTOS DIGITISED. Download: results_fixexp.csv, fixexp_variants.csv, and the folder fixexp_digitized_12lead.' if len(remaining) == 0 else f'{len(remaining)} images remaining: run this cell again.')
print(results_so_far.merge(all_variants[['variant_id', 'variant']], on='variant_id').groupby('variant').has_output.sum().to_string())"""),
]
nb = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "name": "python3", "language": "python"}, "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 5}
json.dump(nb, open(f"{ROOT}/colab/MediSense_Cardio_FixExperiment_Kaggle.ipynb", "w", encoding="utf-8"), indent=1)
for c in cells:
    if c["cell_type"] == "code":
        ast.parse("".join(c["source"]))
print("written", len(cells), "cells; all code cells compile")
