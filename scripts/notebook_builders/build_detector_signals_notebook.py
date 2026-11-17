"""Builds colab/MediSense_Cardio_Detector_Signals_New100.ipynb.

Section D / C3 needs the five photo-quality scores for the 1,300 pages of the NEW 100 recordings (clean + 6 damage types x levels 3 and 5).
The scores come from the page images only (no digitiser, no GPU). The damage code is copied VERBATIM from the Extension notebook
(cell with `def degrade_blur`) and the score code VERBATIM from the Detector_Heldout notebook (`def compute_signals`), so the new
scores are computed exactly like the first-50 scores and exactly on the pages the digitiser saw.
The notebook only computes and saves the scores; the C3 analysis (train on the first 50, score once on the new 100, oracle, best single
score, swapped direction, grouped CV, coverage) is done locally by scripts/analysis/section_D.py.
Reads, never modifies, the two source notebooks."""
import ast
import json
import os
import re

ROOT = "D:/Capstone Project"
ext = json.load(open(f"{ROOT}/colab/MediSense_Cardio_Extension_150.ipynb", encoding="utf-8"))["cells"]
hel = json.load(open(f"{ROOT}/colab/MediSense_Cardio_Detector_Heldout.ipynb", encoding="utf-8"))["cells"]

# ---- verbatim code pulled from the proven notebooks
deg_src = next("".join(c["source"]) for c in ext if c["cell_type"] == "code" and "def degrade_blur" in "".join(c["source"]))
deg_funcs = deg_src.split("# Only the CURRENT scope")[0].rstrip() + "\n"
assert "LEVELS = [3, 5]" in deg_funcs and "def degrade_grid_contrast" in deg_funcs
sig_src = next("".join(c["source"]) for c in hel if c["cell_type"] == "code" and "def compute_signals" in "".join(c["source"]))
sig_funcs = sig_src.split("rows = []")[0].rstrip() + "\n"
assert "def compute_signals" in sig_funcs and "blockiness_score" in sig_funcs
hel_deg = next("".join(c["source"]) for c in hel if c["cell_type"] == "code" and "def degrade_blur" in "".join(c["source"]))
assert "LEVELS = [1, 2, 3, 4, 5]" in hel_deg


def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": [l + "\n" for l in text.split("\n")]}


def code(text):
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [],
            "source": [l + "\n" for l in text.split("\n")]}


cells = []
cells.append(md("""# MediSense-Cardio -- Photo-quality scores for the new 100 recordings (question C3)

**What this notebook does:** computes the **five photo-quality scores** (blur, skew, resolution, contrast, blockiness) for the
**1,300 pages of the new 100 recordings**: the clean page + 6 damage types x levels 3 and 5 = 13 versions per recording.
It is the same code, applied to the same pages, as the first-50 test, so the two sets of scores can be compared.

**Why:** question **C3** asks whether a detector trained on the first 50 recordings can warn about wrong heart rates on
recordings it has never seen. The analysis itself runs later on the laptop. This notebook only produces the scores.

**What it needs:** nothing new. The clean pages and `results_extension.csv` are already on Drive (study folder).
**No GPU and no digitiser.** About 15-25 minutes on Colab's CPU. **Resumable:** if it stops, press `Runtime -> Run all`; it continues
from the last saved record.

**Output:** `quality_signals_ext.csv` in the study folder (1,300 rows). The last cell prints `ALL SIGNALS COMPLETE`.
Download `quality_signals_ext.csv` and `quality_signals_v2.csv` from Drive when it finishes."""))

cells.append(md("""## Step 0 -- Mount Google Drive and check the study folder

**What this does:** connects to the study folder and checks that the files this notebook needs are there."""))
cells.append(code("""from google.colab import drive
drive.mount('/content/drive')

import os, glob
import numpy as np
import pandas as pd

STUDY_DIR = '/content/drive/MyDrive/MediSense-Cardio-Study'
CLEAN_DIR = f'{STUDY_DIR}/images_clean'
EXT_RESULTS = f'{STUDY_DIR}/results_extension.csv'
SIGNALS_EXT = f'{STUDY_DIR}/quality_signals_ext.csv'
SIGNALS_V2 = f'{STUDY_DIR}/quality_signals_v2.csv'

assert os.path.isdir(STUDY_DIR), 'Study folder not found: add the shortcut to My Drive first'
assert os.path.exists(EXT_RESULTS), 'results_extension.csv not found on Drive'
assert os.path.isdir(CLEAN_DIR), 'images_clean not found on Drive'
print('Study folder:', STUDY_DIR)
print('results_extension.csv found; clean pages on Drive:', len(glob.glob(f'{CLEAN_DIR}/*.png')))
print('quality_signals_v2.csv (first 50) found:', os.path.exists(SIGNALS_V2))"""))

cells.append(md("""## Step 1 -- The 1,300 pages of the new 100 recordings

**What this does:** reads the list of versions from `results_extension.csv` (the file of the run that was digitised) and checks that every
recording has its clean page. Nothing is chosen here: the list is exactly the 1,300 images that were digitised."""))
cells.append(code("""ext = pd.read_csv(EXT_RESULTS)
assert len(ext) == 1300 and ext['record'].nunique() == 100, 'unexpected results_extension.csv'
records = sorted(ext['record'].unique())
missing = [r for r in records if not os.path.exists(f'{CLEAN_DIR}/{r}-0.png')]
assert not missing, f'{len(missing)} clean pages missing on Drive: {missing[:5]}'
print(f'{len(records)} recordings, {len(ext)} versions to score; every clean page is on Drive.')
print(ext.groupby(['axis', 'level']).size().to_string())"""))

cells.append(md("""## Step 2 -- Damage code and score code (copied word for word)

**What this does:** defines the six damage functions (copied from the Extension notebook, the code that made the pages the digitiser
saw) and the five-score function (copied from the earlier detector notebook that scored the first 50). Nothing is changed."""))
cells.append(code("import cv2\nimport numpy as np\n\n" + deg_funcs + "\n\n" + sig_funcs +
                  "\nprint('damage functions:', list(AXES), '| levels used here:', LEVELS)"))

cells.append(md("""## Step 3 -- Compute the five scores for all 1,300 pages (resumable)

**What this does:** for each recording it loads the clean page, builds the 13 versions (clean + 6 damages x levels 3 and 5), computes the five
scores of each, and **saves to Drive after every 10 recordings**. If the session stops, run it again: finished recordings are skipped."""))
cells.append(code("""import time

done = pd.read_csv(SIGNALS_EXT) if os.path.exists(SIGNALS_EXT) else pd.DataFrame()
done_records = set(done['record']) if len(done) else set()
print(f'{len(done_records)} recordings already scored on Drive; {len(records) - len(done_records)} to do.')

rows = done.to_dict('records') if len(done) else []
t0 = time.time(); n_new = 0
for i, rec in enumerate(records):
    if rec in done_records:
        continue
    img = cv2.imread(f'{CLEAN_DIR}/{rec}-0.png')
    assert img is not None, f'cannot read clean page of {rec}'
    rows.append(dict(variant_id=f'{rec}-0__clean0', record=rec, axis='clean', level=0, **compute_signals(img)))
    for axis, fn in AXES.items():
        for level in LEVELS:
            rows.append(dict(variant_id=f'{rec}-0__{axis}{level}', record=rec, axis=axis, level=level,
                             **compute_signals(fn(img, level))))
    n_new += 1
    if n_new % 10 == 0 or i == len(records) - 1:
        pd.DataFrame(rows).to_csv(SIGNALS_EXT, index=False)
        print(f'  {len(set(r["record"] for r in rows))}/{len(records)} recordings scored; saved; {time.time() - t0:.0f} s this session')
pd.DataFrame(rows).to_csv(SIGNALS_EXT, index=False)
print('Done with Step 3.')"""))

cells.append(md("""## Step 4 -- Check: same code, same scores as the first 50

**What this does:** the first-50 scores are in `quality_signals_v2.csv` on Drive (from the earlier detector notebook). This cell re-computes a few of them
with the code above and checks that they agree, so we know the new and the old scores are comparable. If `quality_signals_v2.csv` is missing,
the next cell rebuilds it (about 20 minutes)."""))
cells.append(code("""if os.path.exists(SIGNALS_V2):
    old = pd.read_csv(SIGNALS_V2)
    print(f'quality_signals_v2.csv: {len(old)} rows, {old["record"].nunique()} recordings')
    FEATS = ['blur_score', 'skew_deg', 'resolution_score', 'contrast_score', 'blockiness_score']
    ALL_FUNCS = AXES
    checks = []
    for rec in sorted(old['record'].unique())[:3]:
        img = cv2.imread(f'{CLEAN_DIR}/{rec}-0.png')
        assert img is not None, f'first-50 clean page missing for {rec}'
        for axis, level in [('clean', 0), ('blur', 3), ('resolution', 5), ('rotate', 5)]:
            vid = f'{rec}-0__{axis}{level}'
            im = img if axis == 'clean' else ALL_FUNCS[axis](img, level)
            new = compute_signals(im)
            ref = old[old['variant_id'] == vid].iloc[0]
            for f in FEATS:
                a, b = new[f], ref[f]
                same = (a is None and pd.isna(b)) or (a is not None and not pd.isna(b) and abs(a - b) <= 1e-6 * max(1.0, abs(b)))
                checks.append(same)
                if not same:
                    print('MISMATCH', vid, f, a, b)
    print(f'{sum(checks)} of {len(checks)} re-computed scores equal the saved first-50 scores.')
    assert all(checks), 'new and old scores are NOT computed identically -- stop and tell Claude'
    SIGNALS_V2_READY = True
else:
    SIGNALS_V2_READY = False
    print('quality_signals_v2.csv not found: run the next cell to rebuild it.')"""))
cells.append(code("""# Only runs if quality_signals_v2.csv was missing. Rebuilds the first-50 scores (31 versions x 50 recordings), same code.
if not SIGNALS_V2_READY:
    v2 = pd.read_csv(f'{STUDY_DIR}/results_v2.csv')
    f50 = sorted(v2['record'].unique())
    assert len(f50) == 50
    ALL_LEVELS = [1, 2, 3, 4, 5]
    rows50 = []
    for i, rec in enumerate(f50):
        img = cv2.imread(f'{CLEAN_DIR}/{rec}-0.png')
        assert img is not None, f'cannot read clean page of {rec}'
        rows50.append(dict(variant_id=f'{rec}-0__clean0', record=rec, axis='clean', level=0, **compute_signals(img)))
        for axis, fn in AXES.items():
            for level in ALL_LEVELS:
                rows50.append(dict(variant_id=f'{rec}-0__{axis}{level}', record=rec, axis=axis, level=level, **compute_signals(fn(img, level))))
        if (i + 1) % 10 == 0:
            print(f'  {i + 1}/50 recordings done')
    pd.DataFrame(rows50).to_csv(SIGNALS_V2, index=False)
    print('Saved', SIGNALS_V2, len(rows50), 'rows')
else:
    print('Nothing to rebuild: quality_signals_v2.csv is already on Drive.')"""))

cells.append(md("""## Step 5 -- Final check and what to download

**What this does:** joins the scores to `results_extension.csv` (every one of the 1,300 images must match), re-reads the saved file from Drive,
and prints `ALL SIGNALS COMPLETE`. Then download **`quality_signals_ext.csv`** and **`quality_signals_v2.csv`** from the study folder and
tell Claude."""))
cells.append(code("""sig = pd.read_csv(SIGNALS_EXT)
m = ext.merge(sig, on='variant_id', how='inner', suffixes=('', '_sig'))
assert len(sig) == 1300 and sig['variant_id'].is_unique, f'expected 1,300 unique rows, got {len(sig)}'
assert len(m) == 1300, 'join with results_extension.csv failed'
print(f'Verified on Drive: {len(sig)} rows in quality_signals_ext.csv, all 1,300 match results_extension.csv.')
print('Missing skew values (too few lines found):', int(sig['skew_deg'].isna().sum()))
print(sig.groupby(['axis', 'level'])[['blur_score', 'resolution_score', 'contrast_score']].median().round(3).to_string())
print('\\nALL SIGNALS COMPLETE -- download quality_signals_ext.csv and quality_signals_v2.csv from the study folder.')"""))

for n, c in enumerate(cells):
    if c["cell_type"] != "code":
        continue
    text = "\n".join((l[: len(l) - len(l.lstrip())] + "pass" if re.match(r"^\s*(!|%)", l) else l)
                     for l in "".join(c["source"]).split("\n"))
    try:
        ast.parse(text)
    except SyntaxError as e:
        raise SystemExit(f"cell {n} does not compile: {e}")

nb = {"cells": cells,
      "metadata": {"kernelspec": {"display_name": "Python 3", "name": "python3"}, "language_info": {"name": "python"},
                   "colab": {"provenance": [], "name": "MediSense_Cardio_Detector_Signals_New100.ipynb"}},
      "nbformat": 4, "nbformat_minor": 0}
out = os.environ.get("NB_OUT", f"{ROOT}/colab/MediSense_Cardio_Detector_Signals_New100.ipynb")
json.dump(nb, open(out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(f"Wrote {out}: {len(cells)} cells, all code cells compile.")
