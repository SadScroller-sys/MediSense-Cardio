"""Section H (set H2: printed-paper photos taken by the user's friend): digitise each photo in three variants (rules: docs/plan/analysis_plan_changes.md, 2026-11-15 night).
V0 = the photo exactly as taken. V2a = the frozen page finder on the photo as taken (if the finder finds no page the photo is unchanged, so V2a is a copy of V0 and is marked so).
V2b = orientation preprocessing (a photo taller than wide is turned 90 degrees counter-clockwise) + the frozen page finder (2200 x 1700), then the frozen, seeded digitiser.
Primary set first (full-resolution photos), then the recompressed copies. WA0000 (a hand holding a stack of sheets) and unmatched photos are excluded. Resumable.
Usage: demo\\.venv-gpu\\Scripts\\python.exe -I scripts/analysis/digitise_h2_photos.py "<photos folder>"   -> results/paper_h/photos_dig_H2/<stem>__V0|V2a|V2b.npz and digitise_log.csv"""
import csv
import os
import sys
import time

import cv2
import numpy as np
import pandas as pd

ROOT = "D:/Capstone Project/"
sys.path.insert(0, ROOT + "demo")
sys.path.insert(0, ROOT + "scripts/preprocess")
import pipeline as P  # noqa: E402
from page_straighten import straighten  # noqa: E402

folder = sys.argv[1]
OUT = ROOT + "results/paper_h/photos_dig_H2/"
os.makedirs(OUT, exist_ok=True)
MAPNAME = sys.argv[2] if len(sys.argv) > 2 else "photo_id_map.csv"                  # batch 1: photo_id_map.csv, batch 2: photo_id_map_set2.csv
m = pd.read_csv(ROOT + "results/paper_h/" + MAPNAME)
m = m[m.matched & (m.file != "IMG-20261115-WA0000.jpg")]
KINDS = sys.argv[3] if len(sys.argv) > 3 else "both"                          # "full", "compressed" or "both" (full first)
m = pd.concat([m[m.kind == "full"], m[m.kind == "compressed"]])
if KINDS != "both":
    m = m[m.kind == KINDS]
logp = OUT + "digitise_log.csv"
new = not os.path.exists(logp)
lf = open(logp, "a", newline="")
w = csv.writer(lf)
if new:
    w.writerow(["file", "variant", "page_found", "output"])


def save(path, leads):
    if leads is None:
        np.savez(path, **{L: np.full(10000, np.nan) for L in P.LEADS})
    else:
        np.savez(path, **{L: np.asarray(leads[L], float) for L in P.LEADS if L in leads})


t0 = time.time()
for i, f in enumerate(m.file):
    stem = f[:-4]
    img = cv2.imread(os.path.join(folder, f))
    for variant in ("V0", "V2a", "V2b"):
        path = OUT + f"{stem}__{variant}.npz"
        if os.path.exists(path):
            continue
        if variant == "V0":
            x, found = img, ""
        elif variant == "V2a":
            x, found = straighten(img, 2200, 1700)
            if not found:                                   # the frozen finder found no page: the photo is unchanged, V2a equals V0
                v0 = np.load(OUT + f"{stem}__V0.npz")
                np.savez(path, **{k: v0[k] for k in v0.files})
                w.writerow([f, variant, False, "copy of V0"])
                lf.flush()
                continue
        else:
            r = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE) if img.shape[0] > img.shape[1] else img
            x, found = straighten(r, 2200, 1700)
        leads, _ = P.digitise_image(x)
        save(path, leads)
        w.writerow([f, variant, found, "yes" if leads is not None else "NO"])
        lf.flush()
    print(f"{i + 1}/{len(m)} {f} done (total {round(time.time() - t0)} s)", flush=True)
print("done", flush=True)
