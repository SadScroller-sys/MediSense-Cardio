"""Section H, step 1: digitise the user's photos of the PRINTED pages H01-H20 twice: V0 = the photo as it is, V2 = straightened by the page finder (2200 x 1700), same digitiser, commit and settings.
Needs the GPU environment:
  demo\\.venv-gpu\\Scripts\\python.exe -I scripts/analysis/digitise_paper_photos.py <photos_folder> [set_name]
set_name defaults to H (first phone); use H2 for an optional second phone. Photos are matched to pages by file-name order, 2 per page (straight first). Resumable.
Writes results/paper_h/photos_dig_<set>/<photo>__V0.npz and __V2.npz and a log. Prints no accuracy number."""
import csv
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
name = sys.argv[2] if len(sys.argv) > 2 else "H"
files = sorted(f for f in glob.glob(os.path.join(folder, "*")) if f.lower().endswith((".jpg", ".jpeg", ".png", ".heic")))
out_dir = ROOT + f"results/paper_h/photos_dig_{name}/"
os.makedirs(out_dir, exist_ok=True)
print(len(files), "photos found (expected 40)", flush=True)
if len(files) != 40:
    sys.exit("expected exactly 40 photos (20 pages x 2): check the folder")
logp = out_dir + "digitise_log.csv"
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


for i, f in enumerate(files):
    stem = os.path.splitext(os.path.basename(f))[0]
    img = cv2.imread(f)
    if img is None:
        print("cannot read", f)
        continue
    for variant in ("V0", "V2"):
        path = out_dir + f"{stem}__{variant}.npz"
        if os.path.exists(path):
            continue
        x, found = (straighten(img, 2200, 1700) if variant == "V2" else (img, ""))
        leads, _ = P.digitise_image(x)
        save(path, leads)
        w.writerow([stem, variant, found, "yes" if leads is not None else "NO"])
        lf.flush()
    print(f"{i + 1}/{len(files)} {stem} done (total {round(time.time() - t0)} s)", flush=True)
print("done")
