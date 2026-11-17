"""Digitise every page image of a folder with the same Open-ECG-Digitizer (commit 97a15087, same weights and settings file) that every other run used:
the demo's pipeline.digitise_image() (reproduced the Kaggle numbers to two decimals). Needs the GPU environment:
  demo\\.venv-gpu\\Scripts\\python.exe -I scripts/analysis/digitise_pages_generic.py <pages_dir> <out_dir> <log_csv>
Resumes where it stopped. A page with no digitiser output is saved as an all-NaN signal (it counts as "no value"). Prints no accuracy number."""
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

pages_dir, out_dir, log_csv = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(out_dir, exist_ok=True)
pages = sorted(glob.glob(os.path.join(pages_dir, "*.png")))
log, t0 = [], time.time()
for i, path in enumerate(pages):
    name = os.path.basename(path)[:-4]
    out = os.path.join(out_dir, name + ".npz")
    if os.path.exists(out):
        continue
    t = time.time()
    leads, tool_out = P.digitise_image(cv2.imread(path))
    if leads is None:
        np.savez(out, **{L: np.full(10000, np.nan) for L in P.LEADS})
        log.append(dict(page=name, ok=False, seconds=round(time.time() - t), note=tool_out[-200:].replace("\n", " ")))
    else:
        np.savez(out, **{L: np.asarray(leads[L], float) for L in P.LEADS if L in leads})
        log.append(dict(page=name, ok=True, seconds=round(time.time() - t), note=""))
    pd.DataFrame(log).to_csv(log_csv, index=False)
    print(f"{i + 1}/{len(pages)} {name} ok={log[-1]['ok']} {log[-1]['seconds']} s (total {round(time.time() - t0)} s)", flush=True)
print("done", len(glob.glob(os.path.join(out_dir, "*.npz"))), "digitised files")
