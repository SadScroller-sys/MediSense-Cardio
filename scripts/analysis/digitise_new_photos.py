"""Straighten and digitise the user's NEW phone photos of the pages G001-G020 exactly like every other run: the page finder (scripts/preprocess/page_straighten.py, 2200 x 1700) then the demo's
pipeline.digitise_image() (same Open-ECG-Digitizer commit, weights and settings). Needs the GPU environment:
  demo\\.venv-gpu\\Scripts\\python.exe -I scripts/analysis/digitise_new_photos.py <photos_folder>
Photos are matched to pages by file-name order, 2 per page (first straight, second angled) as in Sections O, Q and Q2. Writes results/fresh_g/photos_digitized_12lead/<photo>__V2_straighten.npz.
Prints no accuracy number."""
import glob
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

folder = sys.argv[1]
files = sorted(f for f in glob.glob(os.path.join(folder, "*")) if f.lower().endswith((".jpg", ".jpeg", ".png", ".heic")))
out_dir = ROOT + "results/fresh_g/photos_digitized_12lead/"
os.makedirs(out_dir, exist_ok=True)
print(len(files), "photos found (expected 40)")
t0 = time.time()
for i, f in enumerate(files):
    name = os.path.splitext(os.path.basename(f))[0]
    out = out_dir + name + "__V2_straighten.npz"
    if os.path.exists(out):
        continue
    img = cv2.imread(f)
    if img is None:
        print("cannot read", f)
        continue
    straight, found = straighten(img, 2200, 1700)
    leads, tool_out = P.digitise_image(straight)
    if leads is None:
        np.savez(out, **{L: np.full(10000, np.nan) for L in P.LEADS})
    else:
        np.savez(out, **{L: np.asarray(leads[L], float) for L in P.LEADS if L in leads})
    print(f"{i + 1}/{len(files)} {name} page_found={found} output={'yes' if leads is not None else 'NO'} (total {round(time.time() - t0)} s)", flush=True)
print("done")
