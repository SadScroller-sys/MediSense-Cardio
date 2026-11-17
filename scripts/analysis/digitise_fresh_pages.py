"""Digitise the 100 FRESH pages F001-F100 with the same Open-ECG-Digitizer (commit 97a15087, same weights and settings file) that every other run used:
the demo's pipeline.digitise_image() (it reproduced the Kaggle numbers to two decimals; see demo/README.md). Needs the GPU environment:
  demo\\.venv-gpu\\Scripts\\python.exe -I scripts/analysis/digitise_fresh_pages.py
Resumes where it stopped. A page for which the digitiser gives no output is saved as an all-NaN signal (it counts as "no value", it does not disappear).
Writes results/fresh/fresh_digitized_12lead/F001.npz ... (12 leads, microvolts, 1,000 Hz, NaN where not read) and results/fresh/digitise_log.csv.
Sealed: this script prints no accuracy number; nothing here compares with a reference."""
import glob
import os
import sys
import time

import cv2
import numpy as np
import pandas as pd

ROOT = "D:/Capstone Project/"
sys.path.insert(0, ROOT + "demo")
import pipeline as P  # noqa: E402

OUT = ROOT + "results/fresh/fresh_digitized_12lead/"
os.makedirs(OUT, exist_ok=True)
pages = sorted(glob.glob(ROOT + "results/fresh/pages/F*.png"))
log = []
t0 = time.time()
for i, path in enumerate(pages):
    name = os.path.basename(path)[:-4]
    out = OUT + name + ".npz"
    if os.path.exists(out):
        continue
    img = cv2.imread(path)
    t = time.time()
    leads, tool_out = P.digitise_image(img)
    if leads is None:
        np.savez(out, **{L: np.full(10000, np.nan) for L in P.LEADS})
        log.append(dict(page=name, ok=False, seconds=round(time.time() - t), note=tool_out[-200:].replace("\n", " ")))
    else:
        np.savez(out, **{L: np.asarray(leads[L], float) for L in P.LEADS if L in leads})
        log.append(dict(page=name, ok=True, seconds=round(time.time() - t), note=""))
    pd.DataFrame(log).to_csv(ROOT + "results/fresh/digitise_log.csv", index=False)
    print(f"{i + 1}/{len(pages)} {name} ok={log[-1]['ok']} {log[-1]['seconds']} s (total {round(time.time() - t0)} s)", flush=True)
print("done", len(glob.glob(OUT + "*.npz")), "digitised files")
