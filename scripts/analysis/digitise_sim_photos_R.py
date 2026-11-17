"""Set N: digitise the 120 simulated photos of N once, V2 only = straightened by the page finder (scripts/preprocess/page_straighten.py, 2200 x 1700).
Same digitiser, commit and settings as every other run (demo/pipeline.py digitise_image). Resumable. Needs the GPU environment:
  demo\\.venv-gpu\\Scripts\\python.exe -I scripts/analysis/digitise_sim_photos.py
Writes results/fresh_sim/dig_v0/<photo>.npz, dig_v2/<photo>.npz and results/fresh_sim/digitise_log.csv. Prints no accuracy number."""
import csv
import os
import sys
import time

import cv2
import numpy as np

ROOT = "D:/Capstone Project/"
sys.path.insert(0, ROOT + "demo")
sys.path.insert(0, ROOT + "scripts/preprocess")
import pipeline as P  # noqa: E402
from page_straighten import straighten  # noqa: E402

OUT = ROOT + "results/paper_r/P_sim/"
for d in ("dig_v2",):
    os.makedirs(OUT + d, exist_ok=True)
photos = sorted(f[:-4] for f in os.listdir(OUT + "photos") if f.endswith(".jpg"))
print(len(photos), "photos (expected 120)", flush=True)
logp = OUT + "digitise_log.csv"
new = not os.path.exists(logp)
lf = open(logp, "a", newline="")
w = csv.writer(lf)
if new:
    w.writerow(["photo", "variant", "page_found", "output"])
t0 = time.time()


def save(path, leads):
    if leads is None:
        np.savez(path, **{L: np.full(10000, np.nan) for L in P.LEADS})
    else:
        np.savez(path, **{L: np.asarray(leads[L], float) for L in P.LEADS if L in leads})


for i, name in enumerate(photos):
    img = cv2.imread(OUT + f"photos/{name}.jpg")
    for variant in ("v2",):
        path = OUT + f"dig_{variant}/{name}.npz"
        if os.path.exists(path):
            continue
        if variant == "v2":
            x, found = straighten(img, 2200, 1700)
        else:
            x, found = img, ""
        leads, _ = P.digitise_image(x)
        save(path, leads)
        w.writerow([name, variant, found, "yes" if leads is not None else "NO"])
        lf.flush()
    print(f"{i + 1}/{len(photos)} {name} done (total {round(time.time() - t0)} s)", flush=True)
print("done")
