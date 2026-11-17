"""Section H, step 0b: match every printed-paper photo to its drawn page H01-H20 by IMAGE CONTENT (SIFT features + RANSAC homography against results/paper_h/pages/H*.png).
Uses only the drawn page images (no digitiser output, no true signal, no ECG result). Also gives the shot type (straight or angled) from the projected page outline.
Rules: docs/plan/analysis_plan_changes.md, 2026-11-15 night (Section H amendment and provenance correction). A photo is matched if the best page has at least 25 inliers and at least 1.5 times the second best.
Usage: python -I scripts/analysis/paper_h_match.py "<photos folder>"  -> results/paper_h/photo_id_map.csv"""
import glob
import os
import sys

import cv2
import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
PH = os.path.join(ROOT, "results", "paper_h") + os.sep
folder = sys.argv[1]
OUTNAME = sys.argv[2] if len(sys.argv) > 2 else "photo_id_map.csv"
sift = cv2.SIFT_create(nfeatures=4000)
bf = cv2.BFMatcher()
pages = {}
for f in sorted(glob.glob(PH + "pages/H*.png")):
    g = cv2.cvtColor(cv2.imread(f), cv2.COLOR_BGR2GRAY)
    g = cv2.resize(g, (1100, 850))
    pages[os.path.basename(f)[:3]] = sift.detectAndCompute(g, None)
print(len(pages), "pages loaded", flush=True)
sel = pd.read_csv(PH + "selected_h_20.csv").set_index("page")
rows = []
for f in sorted(glob.glob(os.path.join(folder, "*.jpg"))):
    img = cv2.imread(f)
    h, w = img.shape[:2]
    x = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE) if h > w else img
    s = 1600.0 / max(x.shape[:2])
    g = cv2.cvtColor(cv2.resize(x, None, fx=s, fy=s, interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY)
    kp, ds = sift.detectAndCompute(g, None)
    best = []
    for pid, (pk, pd_) in pages.items():
        if ds is None or pd_ is None:
            continue
        m = [a for a, b in bf.knnMatch(pd_, ds, k=2) if a.distance < 0.75 * b.distance] if len(ds) > 2 else []
        if len(m) < 8:
            best.append((0, pid, None))
            continue
        src = np.float32([pk[a.queryIdx].pt for a in m]).reshape(-1, 1, 2)
        dst = np.float32([kp[a.trainIdx].pt for a in m]).reshape(-1, 1, 2)
        H, mask = cv2.findHomography(src, dst, cv2.RANSAC, 6.0)
        best.append((int(mask.sum()) if mask is not None else 0, pid, H))
    best.sort(key=lambda t: -t[0])
    n1, p1, H1 = best[0]
    n2 = best[1][0]
    ratio = float("nan")
    if H1 is not None:
        corners = cv2.perspectiveTransform(np.float32([[0, 0], [1099, 0], [1099, 849], [0, 849]]).reshape(-1, 1, 2), H1).reshape(4, 2)
        lh, rh = np.linalg.norm(corners[3] - corners[0]), np.linalg.norm(corners[2] - corners[1])
        th, bh = np.linalg.norm(corners[1] - corners[0]), np.linalg.norm(corners[2] - corners[3])
        ratio = float(max(min(lh, rh) / max(lh, rh), min(th, bh) / max(th, bh)) if False else min(min(lh, rh) / max(lh, rh), min(th, bh) / max(th, bh)))
    ok = bool(n1 >= 25 and n1 >= 1.5 * max(n2, 1))
    rows.append(dict(file=os.path.basename(f), kind="full" if max(h, w) >= 3000 else "compressed", page=p1 if ok else "", ecg_id=int(sel.loc[p1, "ecg_id"]) if ok else -1, inliers=n1, second=n2, second_page=best[1][1],
                     matched=ok, outline_ratio=ratio, width=w, height=h))
    print(os.path.basename(f), "->", p1 if ok else "UNMATCHED", n1, n2, flush=True)
d = pd.DataFrame(rows)
d["shot"] = np.where(d.outline_ratio < 0.88, "angled", "straight")
d.to_csv(PH + OUTNAME, index=False)
print(d.groupby("kind").agg(photos=("file", "size"), matched=("matched", "sum")).to_string())
print("pages covered by the full-resolution set:", sorted(d[(d.kind == "full") & d.matched].page.unique()))
