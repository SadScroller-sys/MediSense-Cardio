"""Copies a mix of dataset pictures (simulated phone photos of set N, made from PTB-XL recordings) into demo/dataset_examples/ so they can be used as the demo's examples and uploaded by hand. Fixed rule, no choice by hand:
for each of six findings (AF, LBBB, 1dAVb, LVH, LAFB, IRBBB) the first two cases (in name order) that have the finding and a GREEN light, then the first two GREEN cases with none of the nine patterns. Writes KEY.csv (true answers) and README.md.
All 120 pictures are in results/paper_n/N_sim/photos/ (the gallery lists every one). Usage: python -I scripts/tools/make_dataset_examples.py"""
import csv
import json
import os
import shutil

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
d = json.load(open(ROOT + "/results/paper_n/gallery_cache.json", encoding="utf-8"))
OUT = ROOT + "/demo/dataset_examples/"
if os.path.isdir(OUT):
    shutil.rmtree(OUT)
os.makedirs(OUT)
cases = d["cases"]
picked = []
for k in ("AF", "LBBB", "1dAVb", "LVH", "LAFB", "IRBBB"):
    n = 0
    for c in cases:
        if c["truth"][k] and c["light"] == "GREEN" and c["name"] not in [p["name"] for p in picked]:
            picked.append(c)
            n += 1
            if n == 2:
                break
n = 0
for c in cases:
    if not any(c["truth"].values()) and c["light"] == "GREEN":
        picked.append(c)
        n += 1
        if n == 2:
            break
for c in picked:
    shutil.copyfile(ROOT + f"/results/paper_n/N_sim/photos/{c['name']}.jpg", OUT + c["name"] + ".jpg")
with open(OUT + "KEY.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["file", "true patterns (dataset labels)", "light on the cached run", "true heart rate (bpm)"])
    for c in picked:
        w.writerow([c["name"] + ".jpg", ", ".join(k for k, v in c["truth"].items() if v) or "none of the 9", c["light"], "" if c["hr_true"] is None else round(c["hr_true"])])
open(OUT + "README.md", "w", encoding="utf-8").write(
    "# Dataset pictures for the demo\n\nSimulated phone photos made from PTB-XL recordings (set N); NOT real phone photos. They are the demo's example pictures. After a check the app shows the true answer from the dataset labels next to what the tool said "
    "(the file name starts with the page id, for example N037). `KEY.csv` lists the true answers of these examples. **All 120 pictures** are in `results/paper_n/N_sim/photos/`; any of them can be uploaded by hand, and the tab 'Dataset gallery (instant results)' lists every one.\n")
print(len(picked), "pictures copied to", OUT)
