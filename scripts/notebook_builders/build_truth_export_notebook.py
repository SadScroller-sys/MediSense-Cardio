"""Builds colab/MediSense_Cardio_TruthExport_Kaggle.ipynb.

Purpose: the clean-page diagnosis (results/analysis/SECTION_I) cannot tell whether the REFERENCE or the DIGITISED signal is at fault, because the true lead II
of the real-capture recordings exists only inside the Kaggle competition data. This small notebook copies the true lead II of the 140 Arm C recordings
(the 40 of Arm C + the 100 of the extension) out of the competition folder. CPU only, a few minutes, no download from the internet.
Reads the two selected-recordings lists; never modifies them."""
import json
import os

import pandas as pd

ROOT = "D:/Capstone Project"
a = pd.read_csv(f"{ROOT}/results/armC/armC_selected.csv")
b = pd.read_csv(f"{ROOT}/results/armCext/armCext_selected_all.csv")
IDS = sorted(set(a["id"].astype(str)) | set(b["id"].astype(str)))
assert len(IDS) == 140 and len(set(a["id"].astype(str)) & set(b["id"].astype(str))) == 0


def md(t):
    return {"cell_type": "markdown", "metadata": {}, "source": [l + "\n" for l in t.split("\n")]}


def code(t):
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": [l + "\n" for l in t.split("\n")]}


cells = [md("""# MediSense-Cardio -- copy the TRUE lead II of the 140 real-capture recordings (Kaggle, CPU)

**Why:** some clean pages give a wrong heart rate. To find out if the reference or the digitiser is at fault we need the true lead II signal, which is only inside the competition data.
**What it does:** reads the true lead II of the 140 recordings used in Arm C (40) and its extension (100) and saves them in two small files. Nothing else. No GPU, about 2-5 minutes.

**Steps (Kaggle):**
1. New notebook -> File -> Import notebook -> upload this file.
2. Right panel -> Input -> Add Input -> search "PhysioNet - Digitization of ECG Images" -> add it (same as before).
3. Settings: Accelerator = None (CPU is enough). Internet is not needed.
4. Click Save Version -> Save & Run All (Commit). When it finishes, open Output and download `truth_lead_II.npz` and `truth_meta.csv`.
5. Put both files in your Downloads folder and tell me."""),
         code("""import os, glob, json, datetime
import numpy as np, pandas as pd

IDS = %s
COMP_ROOT = '/kaggle/input'      # where Kaggle puts attached data
WORK = '/kaggle/working'         # what is saved and can be downloaded
os.makedirs(WORK, exist_ok=True)
assert len(IDS) == 140 and len(set(IDS)) == 140

found = glob.glob(COMP_ROOT + '/**/train.csv', recursive=True)
assert found, ('The competition data is not attached. Right panel -> Input -> Add Input -> search '
               '"PhysioNet - Digitization of ECG Images" -> add it. Then Run All again.')
COMP_DIR = os.path.dirname(found[0])
train = pd.read_csv(f'{COMP_DIR}/train.csv')
assert 'id' in train.columns and 'fs' in train.columns, ('train.csv does not have the columns id and fs: ' + str(list(train.columns)))
train['id'] = train['id'].astype(str)
train_fs = dict(zip(train['id'], train['fs']))
print('competition folder:', COMP_DIR, '| recordings in train.csv:', len(train))
missing = [i for i in IDS if i not in train_fs or not os.path.exists(f'{COMP_DIR}/train/{i}/{i}.csv')]
print('requested recordings without a true-signal file:', len(missing), missing[:10])
assert not missing, 'some requested recordings are missing: paste this output into the chat'""" % json.dumps(IDS)),
         code("""arrays, meta = {}, []
for rid in IDS:
    t = pd.read_csv(f'{COMP_DIR}/train/{rid}/{rid}.csv')
    assert 'II' in t.columns, f'no column II in {rid}: {list(t.columns)}'
    ii = t['II'].to_numpy(dtype='float32')              # keep NaN positions, so nothing is shifted
    arrays['r' + rid] = ii
    fin = np.isfinite(ii)
    meta.append({'id': rid, 'fs': float(train_fs[rid]), 'n_rows': int(len(t)), 'n_II': int(fin.sum()), 'n_II_nan': int((~fin).sum()),
                 'duration_s_from_II': round(float(fin.sum()) / float(train_fs[rid]), 3),
                 'II_min_mV': round(float(np.nanmin(ii)), 4), 'II_max_mV': round(float(np.nanmax(ii)), 4),
                 'columns': ' '.join(t.columns)})
np.savez_compressed(f'{WORK}/truth_lead_II.npz', **arrays)
pd.DataFrame(meta).to_csv(f'{WORK}/truth_meta.csv', index=False)
print('saved', len(arrays), 'signals')"""),
         code("""# check what was saved
z = np.load(f'{WORK}/truth_lead_II.npz')
m = pd.read_csv(f'{WORK}/truth_meta.csv')
assert len(z.files) == 140 and len(m) == 140, (len(z.files), len(m))
assert all(len(z['r' + str(i)]) == n for i, n in zip(m['id'], m['n_rows']))
print(m['fs'].value_counts().sort_index().to_string())
print('duration of the true lead II (s): min', m['duration_s_from_II'].min(), '| max', m['duration_s_from_II'].max())
print('recordings with NaN inside lead II:', int((m['n_II_nan'] > 0).sum()))
print('TRUTH EXPORT COMPLETE. Download: truth_lead_II.npz and truth_meta.csv')""")]
nb = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "name": "python3", "language": "python"}, "language_info": {"name": "python"}},
      "nbformat": 4, "nbformat_minor": 5}
os.makedirs(f"{ROOT}/colab", exist_ok=True)
json.dump(nb, open(f"{ROOT}/colab/MediSense_Cardio_TruthExport_Kaggle.ipynb", "w", encoding="utf-8"), indent=1)
print("written", len(cells), "cells,", len(IDS), "ids")
