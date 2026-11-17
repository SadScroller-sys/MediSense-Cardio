"""Builds colab/MediSense_Cardio_ArmB_GeneratorArtifacts.ipynb  ("Arm B": the researchers' own artifact options).

Reuses the proven cells of colab/MediSense_Cardio_Extension_150.ipynb (read only). What is new:
  * 30 recordings (every 3rd of selected_100.csv by ecg_id; rule fixed before any result) are re-rendered with ECG-Image-Kit's OWN artifact options:
        B1  --wrinkles                       (creases + wrinkle texture)
        B2  --augment -rot 10 -noise 25 -t 6500   (random rotation up to 10 degrees, added noise, crop, colour temperature; needs imgaug)
        B3  --wrinkles --augment ...         (both)
    Handwriting (--hw_text) is NOT used: it needs heavy extra libraries.
  * the same digitiser, the same metrics (heart rate, intervals, aligned SNR) and the same saving of all 12 leads, to Drive folder armB_digitized_12lead
  * results go to results_armB.csv. The clean page of each recording (already on Drive) is included as the reference.
Exploratory arm: it does not change any rule of docs/plan/MASTER_PLAN.md.
"""
import ast
import json
import os
import re

import pandas as pd

ROOT = "D:/Capstone Project"
ext = json.load(open(f"{ROOT}/colab/MediSense_Cardio_Extension_150.ipynb", encoding="utf-8"))["cells"]
sel = pd.read_csv(f"{ROOT}/results/extension/selected_100.csv").sort_values("ecg_id").reset_index(drop=True)
sub30 = sel.iloc[::3].iloc[:30].reset_index(drop=True)
assert len(sub30) == 30
print("Arm B records: sex", sub30.sex_lbl.value_counts().to_dict(), "| abnormal", int(sub30.is_abnormal.sum()), "| flagged", int(sub30.flagged.sum()))


def text_of(i):
    return "".join(ext[i]["source"])


def find(substr, kind="code"):
    r = [i for i, c in enumerate(ext) if c["cell_type"] == kind and substr in text_of(i)]
    assert r, substr
    return r[0]


def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": [l + "\n" for l in text.split("\n")]}


def code(text):
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [],
            "source": [l + "\n" for l in text.split("\n")]}


def copy_cell(i):
    c = json.loads(json.dumps(ext[i])); c["outputs"] = []; c["execution_count"] = None
    return c


def sub(text, old, new, count=1):
    assert text.count(old) == count, f"expected {count} of {old[:70]!r}, found {text.count(old)}"
    return text.replace(old, new)


cells = [md("""# MediSense-Cardio -- Arm B: the generator's own artifacts (wrinkles, creases, rotation, noise, crop, colour temperature)

**Why:** the researchers who built ECG-Image-Kit (and the PhysioNet Challenge) test digitisers on pages with realistic artifacts. Our main study uses six damage types
that we wrote ourselves. This small arm adds the tool's **own** artifact options, so the study also shows how the same digitiser behaves on those.

**What it does:** 30 recordings (a fixed rule, no result seen), each page re-drawn three ways with ECG-Image-Kit options:
**B1** wrinkles + creases, **B2** the tool's augmentation (random rotation up to 10 degrees, added noise, crop, colour temperature), **B3** both.
The clean page of each recording is the reference. Then the same digitiser, the same measurements (heart rate, intervals, aligned SNR), all 12 digitised leads saved to Drive.
About 30 x 4 = 120 images, roughly 40 minutes. Results: `results_armB.csv` on Drive. It is exploratory and changes no rule of the master plan.

**First run advice:** the augmentation (B2, B3) needs the library `imgaug`, which can fail on new NumPy versions. The notebook tests this on one record first and tells you clearly if B2/B3 cannot be made.
Run all, then run again if it stops."""),
         copy_cell(find("Mount Google Drive", "markdown")), copy_cell(find("drive.mount")), copy_cell(find("pip install -q wfdb")),
         md("## Step 1 -- The 30 recordings (embedded; every 3rd of the extension list)")]

rows = sub30[["ecg_id", "filename_lr", "sex_lbl", "age", "diagnostic_class", "is_abnormal", "flagged"]].to_dict("records")
rows = [{k: (None if isinstance(v, float) and v != v else v) for k, v in r.items()} for r in rows]
row_lines = ",\n".join("    " + repr(r) for r in rows)
cells.append(code(f"""import pandas as pd, numpy as np, os, ast, ssl, urllib.request

SELECTED = [
{row_lines}
]
sample = pd.DataFrame(SELECTED)
assert len(sample) == 30 and sample['ecg_id'].is_unique
print(f"Arm B: {{len(sample)}} recordings -- sex {{sample['sex_lbl'].value_counts().to_dict()}}, abnormal {{int(sample['is_abnormal'].sum())}}, flagged {{int(sample['flagged'].sum())}}.")"""))
cells.append(copy_cell(find("ptbxl_database_ext.csv")))
cells.append(md("## Step 2 -- Fetch the recordings (100 Hz and 500 Hz)"))
cells.append(copy_cell(find("sex_by_rid = {}")))
cells.append(md("## Step 3 -- Draw tool, then the three artifact versions of each page"))
for key in ("git clone --depth 1 https://github.com/alphanumericslab/ecg-image-kit.git", "requirements_core ="):
    cells.append(copy_cell(find(key)))
cells.append(copy_cell(find("already_rendered")))   # makes sure the clean pages are on local disk as the reference

cells.append(code("""# imgaug is needed only for the augmentation (B2, B3). Old imgaug breaks on NumPy 2 (it uses np.sctypes), and the drawing tool runs as a
# SEPARATE program, so a fix inside this notebook is not enough. We write a tiny startup file (sitecustomize.py) that every Python process picks up.
import subprocess, sys, os
r = subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', 'imgaug'], capture_output=True, text=True)
print('pip install imgaug:', 'ok' if r.returncode == 0 else 'FAILED\\n' + r.stderr[-600:])
SHIM_DIR = '/content/shim'
os.makedirs(SHIM_DIR, exist_ok=True)
with open(f'{SHIM_DIR}/sitecustomize.py', 'w') as f:
    f.write('''import numpy as _np
if not hasattr(_np, 'sctypes'):
    _np.sctypes = {'int': [_np.int8, _np.int16, _np.int32, _np.int64], 'uint': [_np.uint8, _np.uint16, _np.uint32, _np.uint64],
                   'float': [_np.float16, _np.float32, _np.float64], 'complex': [_np.complex64, _np.complex128],
                   'others': [bool, object, bytes, str]}
''')
TOOL_ENV = dict(os.environ, PYTHONPATH=SHIM_DIR + os.pathsep + os.environ.get('PYTHONPATH', ''))
# Second fix: the wrinkle code passes a NumPy number to cv2.subtract, which newer OpenCV versions reject. A plain Python float works everywhere.
_cp = '/content/ecg-image-kit/codes/ecg-image-generator/CreasesWrinkles/creases.py'
_t = open(_cp).read()
if 'shift = mean - 0.4' in _t:
    open(_cp, 'w').write(_t.replace('shift = mean - 0.4', 'shift = float(mean - 0.4)'))
    print('wrinkle code patched (float shift)')
t = subprocess.run([sys.executable, '-c', 'import imgaug; print(imgaug.__version__)'], capture_output=True, text=True, env=TOOL_ENV)
IMGAUG_OK = (t.returncode == 0)
print('imgaug usable by the drawing tool:', IMGAUG_OK, t.stdout.strip() if IMGAUG_OK else t.stderr[-400:])
if not IMGAUG_OK:
    print('B2 and B3 will be skipped; only B1 (wrinkles/creases) will run.')"""))

cells.append(code("""import shutil, glob, subprocess, os
GEN_DIR = '/content/ecg-image-kit/codes/ecg-image-generator'
COMMON = '--print_header'
CONDITIONS = {
    'B1_wrinkles': f'{COMMON} --wrinkles',
    # --store_config 1 is REQUIRED with --augment: the tool then writes the lead positions to a .json file that the augmentation reads.
    # Without it the augmentation crashes (TypeError: 'NoneType' object is not subscriptable) AFTER the plain page was already saved,
    # so a half-made page looks like a success. Found by local test 2026-11-05.
    'B2_augment':  f'{COMMON} --store_config 1 --augment -rot 10 -noise 25 -t 6500',
    'B3_both':     f'{COMMON} --store_config 1 --wrinkles --augment -rot 10 -noise 25 -t 6500',
}
if not IMGAUG_OK:
    CONDITIONS = {k: v for k, v in CONDITIONS.items() if '--augment' not in v}
    print('Without imgaug only these conditions can run:', list(CONDITIONS))

ARMB_DRIVE = f'{STUDY_DIR}/armB_images'
os.makedirs(ARMB_DRIVE, exist_ok=True)
os.makedirs('/content/armB_images', exist_ok=True)

def render_condition(name, flags, rids, tries=3):
    # One record per call, up to 3 tries: the drawing tool uses random choices and can crash on a page; one crash must not stop the others.
    src = f'/content/data/render_{name}'; out = f'/content/render_out_{name}'
    if os.path.exists(out): shutil.rmtree(out)
    os.makedirs(out)
    r = None
    for rid in rids:
        for attempt in range(tries):
            if os.path.exists(src): shutil.rmtree(src)
            os.makedirs(src)
            for ext in ('.hea', '.dat'):
                shutil.copy(f'/content/data/full/{rid}{ext}', f'{src}/{rid}{ext}')
            cmd = f'cd {GEN_DIR} && python gen_ecg_images_from_data_batch.py -i {src} -o {out} {flags}'
            r = subprocess.run(cmd, shell=True, capture_output=True, text=True, env=TOOL_ENV)
            # success = the tool finished without error AND the page exists (a crash after the plain page was saved leaves a half-made page behind)
            if r.returncode == 0 and glob.glob(f'{out}/{rid}-0.png'):
                break
        else:
            # all tries failed: delete the half-made page so it can never be counted as an artifact page
            for leftover in glob.glob(f'{out}/{rid}-0.*'):
                os.remove(leftover)
    pngs = sorted(glob.glob(f'{out}/*.png'))
    return r, pngs

# smoke test on one record first, so a broken option is found in a minute and not after the whole batch
test_rid = record_ids[0]
for name, flags in list(CONDITIONS.items()):
    r, pngs = render_condition(name, flags, [test_rid])
    ok = len(pngs) == 1
    print(f'smoke test {name}: {"OK" if ok else "FAILED"} ({len(pngs)} image)')
    if not ok:
        print((r.stdout + r.stderr)[-700:])
        CONDITIONS.pop(name)
print('Conditions that will run:', list(CONDITIONS))
assert CONDITIONS, 'no artifact condition could be made: paste the messages above into the chat'"""))

cells.append(code("""# Render every condition for all 30 recordings; copy to Drive and to the local working folder under the variant name.
render_report = {}
for name, flags in CONDITIONS.items():
    r, pngs = render_condition(name, flags, record_ids)
    got = {os.path.basename(p).replace('-0.png', ''): p for p in pngs}
    miss = [rid for rid in record_ids if rid not in got]
    render_report[name] = (len(got), len(miss))
    for rid, p in got.items():
        shutil.copy(p, f'/content/armB_images/{rid}-0__{name}.png')
        shutil.copy(p, f'{ARMB_DRIVE}/{rid}-0__{name}.png')
    print(f'{name}: {len(got)} of {len(record_ids)} images made, {len(miss)} missing {miss[:3]}')"""))

cells.append(md("## Step 4 -- Variant list: the clean page (reference) + the artifact versions"))
cells.append(code("""import cv2
AXES = {}          # no own damage functions in this arm: images are used exactly as the generator drew them
LEVELS = [0]
variant_rows = []
for rid in record_ids:
    stem = f'{rid}-0'
    clean_path = f'/content/images_clean/{stem}.png'
    assert os.path.exists(clean_path), f'clean page missing: {clean_path}'
    variant_rows.append({'stem': stem, 'axis': 'clean', 'level': 0, 'variant_id': f'{stem}__clean0', 'source_path': clean_path})
    for name in CONDITIONS:
        p = f'/content/armB_images/{stem}__{name}.png'
        if os.path.exists(p):
            variant_rows.append({'stem': stem, 'axis': name, 'level': 0, 'variant_id': f'{stem}__{name}0', 'source_path': p})
all_variants = pd.DataFrame(variant_rows)
print(len(all_variants), 'variants:', all_variants['axis'].value_counts().to_dict())"""))

cells.append(md("## Step 5 -- Results checkpoint (separate file `results_armB.csv`)"))
s5 = text_of(find("RESULTS_PATH = "))
cells.append(code(sub(s5, "results_extension.csv", "results_armB.csv")))
for key in ("Step 6 -- Set up the digitizer",):
    cells.append(copy_cell(find(key, "markdown")))
for key in ("git clone https://github.com/Ahus-AIM/Open-ECG-Digitizer.git", "pip install -q torch torchvision", "def write_digitizer_config"):
    cells.append(copy_cell(find(key)))
prov = text_of(find("extension_provenance.json"))
prov = sub(prov, "extension_provenance.json", "armB_provenance.json")
prov = sub(prov, "'n_records': len(record_ids),", "'n_records': len(record_ids),\n    'conditions': list(CONDITIONS),\n    'imgaug_ok': IMGAUG_OK,")
cells.append(code(prov))

cells.append(md("## Step 7 -- Digitise in checkpointed sub-batches (same loop as the main study)"))
s7 = text_of(find("def compute_metrics"))
s7 = sub(s7, "extension_digitized_12lead", "armB_digitized_12lead", count=s7.count("extension_digitized_12lead"))
s7 = sub(s7, "results_extension_backup_", "results_armB_backup_")
s7 = sub(s7, "rows in results_extension.csv", "rows in results_armB.csv")
s7 = sub(s7, "out_img = img if v['axis'] == 'clean' else AXES[v['axis']](img, v['level'])",
         "out_img = AXES[v['axis']](img, v['level']) if v['axis'] in AXES else img   # arm B: images are used as drawn")
cells.append(code(s7))

cells.append(md("## Step 8 -- Overview"))
cells.append(code("""results_so_far = pd.read_csv(RESULTS_PATH) if os.path.exists(RESULTS_PATH) else pd.DataFrame()
print(f'{len(results_so_far)}/{len(all_variants)} variants have results.')
if len(results_so_far) > 0:
    r = results_so_far.copy()
    r['no_output'] = r['dig_hr'].isna()
    r['wrong_hr_5bpm'] = r['diff_bpm'] > 5
    summ = r.groupby('axis').agg(n=('variant_id', 'size'), no_output=('no_output', 'sum'),
                                 wrong_hr_5bpm=('wrong_hr_5bpm', 'sum'), median_snr_db=('snr_aligned_db', 'median')).round(1)
    display(summ)"""))

nb = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "name": "python3"}, "language_info": {"name": "python"},
                                   "colab": {"provenance": [], "name": "MediSense_Cardio_ArmB_GeneratorArtifacts.ipynb"}}, "nbformat": 4, "nbformat_minor": 0}
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
out = f"{ROOT}/colab/MediSense_Cardio_ArmB_GeneratorArtifacts.ipynb"
json.dump(nb, open(out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(f"Wrote {out}: {len(cells)} cells, all code cells compile.")
