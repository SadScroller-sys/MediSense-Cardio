"""Builds colab/MediSense_Cardio_Bridge_Run.ipynb from the (already built, running) Extension notebook.

Bridge run (MASTER_PLAN phase 2): re-digitise 12 of the FIRST 50 recordings in the new environment, 13 versions each
(clean + 6 damage types x levels 3 and 5 = 156 images), to test whether the digitiser is repeatable between runs.
The 12 = the 6 records that fail in most versions in sweep 2 (00102, 08150, 13316, 00053, 18151, 19059; known from the first
sweep) + 6 drawn at random (seed 42) from the 44 reliable records. The rule is fixed here, before the run.
Reads, never modifies, colab/MediSense_Cardio_Extension_150.ipynb."""
import ast
import json
import os
import re

import numpy as np
import pandas as pd

ROOT = "D:/Capstone Project"
ext = json.load(open(f"{ROOT}/colab/MediSense_Cardio_Extension_150.ipynb", encoding="utf-8"))["cells"]
v2 = pd.read_csv(f"{ROOT}/results/v2_intervals/results_v2.csv")
db = pd.read_csv(f"{ROOT}/data/ptbxl/ptbxl_database.csv")

first50 = sorted(v2.record.unique())
assert len(first50) == 50
FAIL6 = ["00102_lr", "08150_lr", "13316_lr", "00053_lr", "18151_lr", "19059_lr"]
assert set(FAIL6) <= set(first50)
reliable = [r for r in first50 if r not in FAIL6]
assert len(reliable) == 44
rng = np.random.default_rng(42)
others = sorted(rng.choice(reliable, 6, replace=False).tolist())
chosen = FAIL6 + others
rows = []
for r in chosen:
    eid = int(r.split("_")[0])
    x = db[db.ecg_id == eid]
    assert len(x) == 1
    x = x.iloc[0]
    rows.append({"ecg_id": eid, "record": r, "filename_lr": x.filename_lr,
                 "sex_lbl": "female" if x.sex == 1 else "male", "age": float(x.age),
                 "group": "fails_in_sweep2" if r in FAIL6 else "random_reliable"})
os.makedirs(f"{ROOT}/results/bridge", exist_ok=True)
pd.DataFrame(rows).to_csv(f"{ROOT}/results/bridge/bridge_selected_12.csv", index=False)
print(pd.DataFrame(rows)[["record", "sex_lbl", "age", "group"]].to_string(index=False))


def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": [l + "\n" for l in text.split("\n")]}


def code(text):
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [],
            "source": [l + "\n" for l in text.split("\n")]}


cells = [json.loads(json.dumps(c)) for c in ext]
for c in cells:
    if c["cell_type"] == "code":
        c["outputs"] = []
        c["execution_count"] = None

cells[0] = md("""# MediSense-Cardio -- Bridge run: are the digitiser's results repeatable?

**What this notebook does:** takes **12 of the first 50 recordings** (already digitised in sweep 2) and digitises their pages again
in the current environment: the clean page + 6 damage types x levels 3 and 5 = **13 versions per recording = 156 images**
(about 1 hour on a Colab GPU). Nothing else in the study is touched.

**Why:** in sweeps 1 and 2 the same images gave 163 and 30 unreadable results, so the digitiser's output is not repeatable between
runs. This run measures how much a result changes between runs, so we know whether the first 50 and the new 100 recordings can be
compared (rule in `docs/plan/MASTER_PLAN.md`: more than 5% label changes -> pooled comparisons become exploratory).

**The 12 recordings (rule fixed before the run):** the 6 records that failed in most versions in sweep 2 (00102, 08150, 13316,
00053, 18151, 19059) + 6 drawn at random (seed 42) from the 44 reliable records.

Results go to `results_bridge.csv`. **Resumable:** `Runtime -> Run all`; if it stops, run it again until the last cell of Step 7 prints
`ALL VARIANTS COMPLETE`. **Run it only after the main extension run has finished** (one Colab session at a time).""")
cells[4] = md("""## Step 1 -- The 12 selected recordings (embedded below)

These are fixed. The cell checks that all 12 are among the first 50 recordings (`results_v2.csv` on Drive) and, in the next cell,
that the PTB-XL label file agrees with the embedded sex of every recording.""")

row_lines = ",\n".join("    " + repr(r) for r in rows)
cells[5] = code(f"""import pandas as pd, numpy as np, os, ast, ssl, urllib.request

SELECTED = [
{row_lines}
]
sample = pd.DataFrame(SELECTED)
assert len(sample) == 12 and sample['ecg_id'].is_unique
print(f"Embedded selection: {{len(sample)}} recordings -- sex {{sample['sex_lbl'].value_counts().to_dict()}}; "
      f"groups {{sample['group'].value_counts().to_dict()}}.")

V2_RESULTS = f'{{STUDY_DIR}}/results_v2.csv'
assert os.path.exists(V2_RESULTS), 'results_v2.csv not found on Drive: the bridge run needs it'
first50 = set(pd.read_csv(V2_RESULTS)['record'].unique())
assert set(sample['record']) <= first50, f"not in the first 50: {{sorted(set(sample['record']) - first50)}}"
print(f"All 12 recordings are among the {{len(first50)}} in results_v2.csv.")
sample.head(12)""")
cells[6]["source"] = [l.replace("all 100 recordings", "all 12 recordings") for l in cells[6]["source"]]
# The extension notebook requires human-validated labels (selection rule for the NEW 100). The first 50 were chosen
# without that rule (8 of them are not human-validated, e.g. 13618, 19059), and the bridge run only compares digitiser
# output between two runs, so labels do not matter here: report the count instead of asserting.
_t = "".join(cells[6]["source"])
_old = "assert sample['validated_by_human'].all(), 'every selected record must have human-validated labels'"
assert _old in _t
_t = _t.replace(_old, "print(f\"Human-validated labels: {int(sample['validated_by_human'].sum())} of {len(sample)} "
                      "(not required for the bridge run: it only compares digitiser output between two runs).\")")
_t = _t.replace("Sex, ids and human-validation of all 12 recordings agree with the PTB-XL label file.",
                "Sex and ids of all 12 recordings agree with the PTB-XL label file.")
cells[6]["source"] = _t.splitlines(keepends=True)

total = 0
for i, c in enumerate(cells):
    if i in (0, 4, 5) or c["cell_type"] not in ("code", "markdown"):
        continue
    t = "".join(c["source"])
    for old, new in [("results_extension_backup_", "results_bridge_backup_"), ("results_extension", "results_bridge"),
                     ("extension_digitized_12lead", "bridge_digitized_12lead"),
                     ("extension_digitized_II", "bridge_digitized_II"),
                     ("extension_provenance", "bridge_provenance")]:
        total += t.count(old)
        t = t.replace(old, new)
    c["source"] = t.splitlines(keepends=True)
print("replacements:", total)

cells.append(md("""## Step 9 -- Bridge result: same images, two runs (the main output of this notebook)

Compares each image's result here with sweep 2 (`results_v2.csv`, same recording, damage type and level): output available or
not, heart-rate difference, and whether the 'wrong by more than 5 bpm' label changed. Safe to run at any point."""))
cells.append(code("""v2 = pd.read_csv(f'{STUDY_DIR}/results_v2.csv')
br = pd.read_csv(RESULTS_PATH)
m = br.merge(v2[['record', 'axis', 'level', 'dig_hr', 'diff_bpm']], on=['record', 'axis', 'level'],
             suffixes=('_bridge', '_v2'), how='left')
both = m[m['dig_hr_bridge'].notna() & m['dig_hr_v2'].notna()]
print(f"Images compared: {len(m)}")
print(f"No reading in the bridge run: {int(m['dig_hr_bridge'].isna().sum())}; no reading in sweep 2: {int(m['dig_hr_v2'].isna().sum())}")
print(f"Reading in both runs: {len(both)}; heart rates equal within 1 bpm: {int(((both['dig_hr_bridge'] - both['dig_hr_v2']).abs() < 1).sum())}")
bad_b = m['dig_hr_bridge'].isna() | (m['diff_bpm_bridge'].abs() > 5)
bad_2 = m['dig_hr_v2'].isna() | (m['diff_bpm_v2'].abs() > 5)
flip = int((bad_b != bad_2).sum())
print(f"Label (no output or wrong by >5 bpm) changed between runs: {flip} of {len(m)} = {100 * flip / len(m):.1f}%  "
      f"(rule: more than 5% -> pooled comparisons become exploratory)")
m.assign(read_bridge=m['dig_hr_bridge'].notna(), read_v2=m['dig_hr_v2'].notna()).groupby('record')[['read_bridge', 'read_v2']].sum()"""))

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
                   "colab": {"provenance": [], "name": "MediSense_Cardio_Bridge_Run.ipynb"}},
      "nbformat": 4, "nbformat_minor": 0}
out = os.environ.get("NB_OUT", f"{ROOT}/colab/MediSense_Cardio_Bridge_Run.ipynb")
json.dump(nb, open(out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(f"Wrote {out}: {len(cells)} cells, all code cells compile.")
