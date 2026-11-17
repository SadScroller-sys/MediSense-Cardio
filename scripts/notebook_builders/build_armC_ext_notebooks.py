"""Builds colab/MediSense_Cardio_ArmCext_Part1_Kaggle.ipynb and ..._Part2_Kaggle.ipynb  (Arm C extension: 100 more real-capture recordings).

Rules fixed before the run: docs/plan/analysis_plan_changes.md (2026-11-07, 'Arm C extension').
Derived from the proven Arm C notebook (colab/MediSense_Cardio_ArmC_Kaggle_RealCaptures.ipynb) by asserted text substitution, so the digitising and measurement code is identical.
Differences: 100 recordings chosen with seed 43 among the competition recordings that have every version AND are not among the 40 used in Arm C (embedded list);
the 100 are split into two halves (Part 1 = first 50 of the sorted list, Part 2 = last 50), one notebook each (about 3-4 GPU hours); output files carry the part number;
a final step computes the five photo-quality scores (code copied verbatim from the detector notebook) for every real capture.
Reads, never modifies, the source notebooks."""
import ast
import json
import os

import pandas as pd

ROOT = "D:/Capstone Project"
src = json.load(open(f"{ROOT}/colab/MediSense_Cardio_ArmC_Kaggle_RealCaptures.ipynb", encoding="utf-8"))["cells"]
hel = json.load(open(f"{ROOT}/colab/MediSense_Cardio_Detector_Heldout.ipynb", encoding="utf-8"))["cells"]
used = pd.read_csv(f"{ROOT}/results/armC/armC_selected.csv")
EXCLUDE = sorted(used["id"].astype(str).tolist())
assert len(EXCLUDE) == 40
sig_src = next("".join(c["source"]) for c in hel if c["cell_type"] == "code" and "def compute_signals" in "".join(c["source"]))
sig_funcs = sig_src.split("rows = []")[0].rstrip() + "\n"
assert "def compute_signals" in sig_funcs and "blockiness_score" in sig_funcs


def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": [l + "\n" for l in text.split("\n")]}


def code(text):
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [],
            "source": [l + "\n" for l in text.split("\n")]}


def sub(text, old, new, count=1):
    assert text.count(old) == count, f"expected {count} of {old[:80]!r}, found {text.count(old)}"
    return text.replace(old, new)


def build(part):
    cells = [json.loads(json.dumps(c)) for c in src]
    for c in cells:
        if c["cell_type"] == "code":
            c["outputs"] = []
            c["execution_count"] = None
    names = {"armC_selected.csv": f"armCext_selected_part{part}.csv", "armC_provenance.json": f"armCext_provenance_part{part}.json",
             "results_armC.csv": f"results_armCext_part{part}.csv", "armC_digitized_12lead": f"armCext_digitized_12lead_part{part}",
             "armC_quality_signals.csv": None}

    def text(i):
        return "".join(cells[i]["source"])

    def setc(i, t):
        cells[i]["source"] = t.splitlines(keepends=True)

    # --- intro
    cells[0] = md(f"""# MediSense-Cardio -- Arm C extension, part {part} of 2: more real scans and phone photos (Kaggle)

**Why:** Arm C had only 40 recordings, so every difference between capture types was "not significant". This extension digitises **50 more recordings** of the same real captures
(printed + scanned, phone photos, stained, soaked, extensively damaged, mold), so the real-photo results can be replicated. Together, parts 1 and 2 give 100 new recordings and 900 images.
Data: Kaggle competition *PhysioNet - Digitization of ECG Images* (CC BY 4.0), read inside Kaggle (nothing to download).

**What it does:** takes the fixed random choice of 100 recordings (seed 43, none of the 40 already used in Arm C), keeps the {"first" if part == 1 else "last"} 50 (part {part}),
digitises every version (about 450 images) with the same digitiser and settings as the main study, compares with the true signal (heart rate, aligned SNR, intervals), saves all 12 digitised leads,
and finally computes the five photo-quality scores of every captured page (so the photo detector can be tested on real photos too).

**Before you run (once):** right panel -> *Input* -> add the competition *PhysioNet - Digitization of ECG Images*;  *Settings* -> *Accelerator* = a GPU and *Internet* = On.
**Run:** *Save Version -> Save & Run All (Commit)* is safest (it keeps running if you close the tab), or *Run All*. About 3-4 hours on a GPU. The first cells check everything in minutes and stop with a clear message if something is wrong.
**After:** *Output* tab -> download `results_armCext_part{part}.csv`, `armCext_provenance_part{part}.json`, `armCext_selected_part{part}.csv`, `armCext_quality_signals_part{part}.csv` and the folder `armCext_digitized_12lead_part{part}`.
Part 2 is a separate notebook. Run one part at a time. Exploratory/replication arm; rules in `docs/plan/analysis_plan_changes.md`.""")

    # --- step 1 settings
    i1 = next(i for i, c in enumerate(cells) if c["cell_type"] == "code" and "N_RECORDS = 40" in "".join(c["source"]))
    t = text(i1)
    t = sub(t, "N_RECORDS = 40            # how many recordings (fixed before any result)", f"N_RECORDS = 100           # how many NEW recordings in total (fixed before any result); this notebook does half\nPART = {part}                # which half (1 = first 50 of the sorted list, 2 = last 50)")
    t = sub(t, "SEED = 42                 # fixed seed for the choice of recordings", f"SEED = 43                 # fixed seed for the choice of recordings (Arm C used 42)\nEXCLUDE = {EXCLUDE!r}   # the 40 recordings already used in Arm C: never chosen again")
    setc(i1, t)

    # --- step 2 selection
    i2 = next(i for i, c in enumerate(cells) if c["cell_type"] == "code" and "rng = np.random.default_rng(SEED)" in "".join(c["source"]))
    t = text(i2)
    t = sub(t, "rng = np.random.default_rng(SEED)\nchosen = sorted(rng.choice(full, size=min(N_RECORDS, len(full)), replace=False).tolist())",
            "candidates = [i for i in full if i not in set(EXCLUDE)]\nprint(f'{len(candidates)} recordings are available after removing the {len(EXCLUDE)} used in Arm C.')\n"
            "assert len(candidates) >= N_RECORDS, 'not enough unused recordings: paste the printout above into the chat'\n"
            "rng = np.random.default_rng(SEED)\nall_new = sorted(rng.choice(candidates, size=N_RECORDS, replace=False).tolist())\n"
            "assert not set(all_new) & set(EXCLUDE)\nhalf = N_RECORDS // 2\nchosen = all_new[:half] if PART == 1 else all_new[half:]\n"
            "print(f'All {N_RECORDS} new recordings fixed by seed {SEED}; this notebook (part {PART}) takes {len(chosen)} of them.')")
    t = sub(t, "if len(full) < 10:", "if len(full) < 10:")
    setc(i2, t)
    # the header of step 2 mentions the rule
    for i, c in enumerate(cells):
        if c["cell_type"] == "markdown" and "## Step 2 -- Choose the recordings" in "".join(c["source"]):
            cells[i] = md("## Step 2 -- Choose the recordings (fixed rule: seed 43 among recordings that have every version and the true signal, excluding the 40 used in Arm C; this part takes half)")

    # --- file names
    for i, c in enumerate(cells):
        if c["cell_type"] != "code":
            continue
        t = "".join(c["source"])
        for old, new in names.items():
            if new and old in t:
                t = t.replace(old, new)
        c["source"] = t.splitlines(keepends=True)
    # provenance: add part, exclusion
    ip = next(i for i, c in enumerate(cells) if c["cell_type"] == "code" and "'n_records': len(chosen)," in "".join(c["source"]))
    setc(ip, sub(text(ip), "    'n_records': len(chosen),", "    'n_records': len(chosen),\n    'part': PART,\n    'n_excluded_armC_recordings': len(EXCLUDE),"))

    # --- final download message and a new step for the photo scores
    il = next(i for i, c in enumerate(cells) if c["cell_type"] == "code" and "Download from the Output tab" in "".join(c["source"]))
    t = text(il)
    t = t.replace("\\nDownload from the Output tab:", "\\nNext cell: five photo scores. Download from the Output tab:")
    setc(il, t)
    cells.append(md("## Step 8 -- The five photo-quality scores of every captured page (so the photo detector can be tested on real photos)\n\n"
                    "**What this does:** applies the same five-score code as the detector notebook (blur, skew, resolution, contrast, blockiness) to every real capture, and saves them. "
                    "No digitiser, only image processing: about 10-15 minutes. Resumable."))
    cells.append(code("import cv2\nimport numpy as np\n\n" + sig_funcs + f"""
SIG_PATH = f'{{WORK}}/armCext_quality_signals_part{part}.csv'
done_sig = pd.read_csv(SIG_PATH) if os.path.exists(SIG_PATH) else pd.DataFrame()
have = set(done_sig['variant_id']) if len(done_sig) else set()
rows_sig = done_sig.to_dict('records') if len(done_sig) else []
t0 = time.time()
for n, (_, v) in enumerate(all_variants.iterrows(), 1):
    if v['variant_id'] in have:
        continue
    img = cv2.imread(v['source_path'])
    if img is None:
        continue
    rows_sig.append(dict(variant_id=v['variant_id'], record=v['stem'], axis=v['axis'], level=0, **compute_signals(img)))
    if n % 50 == 0:
        pd.DataFrame(rows_sig).to_csv(SIG_PATH, index=False)
        print(f'  {{n}}/{{len(all_variants)}} pages scored; {{time.time() - t0:.0f}} s')
pd.DataFrame(rows_sig).to_csv(SIG_PATH, index=False)
chk = pd.read_csv(SIG_PATH)
print(f'Verified on disk: {{len(chk)}} rows in {{SIG_PATH}} (expected {{len(all_variants)}}).')
print('ALL PHOTO SCORES COMPLETE. Download: results_armCext_part{part}.csv, armCext_provenance_part{part}.json, armCext_selected_part{part}.csv, '
      'armCext_quality_signals_part{part}.csv and the folder armCext_digitized_12lead_part{part}.')"""))

    for n, c in enumerate(cells):
        if c["cell_type"] == "code":
            try:
                ast.parse("".join(c["source"]))
            except SyntaxError as e:
                raise SystemExit(f"part {part} cell {n} does not compile: {e}")
    nb = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "name": "python3", "language": "python"}, "language_info": {"name": "python"}},
          "nbformat": 4, "nbformat_minor": 4}
    out = os.environ.get("NB_OUT_DIR", f"{ROOT}/colab") + f"/MediSense_Cardio_ArmCext_Part{part}_Kaggle.ipynb"
    json.dump(nb, open(out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"Wrote {out}: {len(cells)} cells, all code cells compile.")


for p in (1, 2):
    build(p)


# ---- single-notebook variant: all 100 recordings in one run (derived from the part-1 notebook by asserted substitution)
def build_single():
    p1 = open(f"{ROOT}/colab/MediSense_Cardio_ArmCext_Part1_Kaggle.ipynb", encoding="utf-8").read()
    t = p1
    t = sub(t, "chosen = all_new[:half] if PART == 1 else all_new[half:]", "chosen = all_new if PART == 0 else (all_new[:half] if PART == 1 else all_new[half:])")
    t = sub(t, "PART = 1                # which half (1 = first 50 of the sorted list, 2 = last 50)", "PART = 0                # 0 = all 100 recordings in this one notebook")
    t = t.replace("part1", "all").replace("part 1 of 2", "all 100 recordings in one run")
    t = sub(t, "digitises **50 more recordings**", "digitises **100 more recordings**")
    t = sub(t, "Together, parts 1 and 2 give 100 new recordings and 900 images.", "This single notebook does all 100 new recordings (900 images).")
    t = t.replace("keeps the first 50 (part 1)", "keeps all 100").replace("about 450 images", "about 900 images")
    t = t.replace("About 3-4 hours on a GPU.", "About 6-8 hours on a GPU (it saves every 15 images and stops cleanly after 9.5 hours; then run it again).")
    t = t.replace("Part 2 is a separate notebook. Run one part at a time. ", "")
    t = t.replace("this notebook (part {PART}) takes {len(chosen)} of them", "this notebook (part {PART}: 0 = all) takes {len(chosen)} of them")
    json.loads(t)  # still valid json
    nb = json.loads(t)
    for n, c in enumerate(nb["cells"]):
        if c["cell_type"] == "code":
            ast.parse("".join(c["source"]))
    out = f"{ROOT}/colab/MediSense_Cardio_ArmCext_All100_Kaggle.ipynb"
    open(out, "w", encoding="utf-8").write(t)
    print(f"Wrote {out}: {len(nb['cells'])} cells, all code cells compile.")


build_single()
