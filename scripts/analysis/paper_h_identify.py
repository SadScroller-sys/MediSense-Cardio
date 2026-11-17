"""Section H, step 0: facts about the printed-paper photos and contact sheets of header crops so that each photo can be matched to its page by the ID printed in the header
(rules: docs/plan/analysis_plan_changes.md, 2026-11-15 night, "Section H ... AMENDMENT 1"). NO digitiser is run here. The photo is turned 90 degrees counter-clockwise if it is taller than wide
(orientation preprocessing), the frozen page finder finds the page, the header strip is cropped from the straightened page. The shot type is computed from the page outline (ratio of the left and right edge heights).
Usage: python -I scripts/analysis/paper_h_identify.py "<photos folder>"   -> results/paper_h/photo_facts.csv and id_montage_*.jpg"""
import glob
import os
import sys

import cv2
import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts", "preprocess"))
from page_straighten import find_page_quad, straighten  # noqa: E402

folder = sys.argv[1]
OUT = os.path.join(ROOT, "results", "paper_h") + os.sep
rows, crops = [], {"full": [], "compressed": []}
for f in sorted(glob.glob(os.path.join(folder, "*.jpg"))):
    img = cv2.imread(f)
    h, w = img.shape[:2]
    kind = "full" if max(h, w) >= 3000 else "compressed"
    x = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE) if h > w else img
    q = find_page_quad(x)
    found = q is not None
    ratio = float("nan")
    if found:
        tl, tr, br, bl = [np.asarray(p, float) for p in q]
        lh, rh = np.linalg.norm(bl - tl), np.linalg.norm(br - tr)
        ratio = float(min(lh, rh) / max(lh, rh))
    rows.append(dict(file=os.path.basename(f), width=w, height=h, kind=kind, page_found_after_orientation=found, edge_ratio=ratio))
    if found:
        out, _ = straighten(x, 2200, 1700)
        hdr = cv2.resize(out[0:260, 0:1100], (550, 130))
        cv2.putText(hdr, os.path.basename(f)[12:-4], (4, 125), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA)
        crops[kind].append(hdr)
pd.DataFrame(rows).to_csv(OUT + "photo_facts.csv", index=False)
for kind, lst in crops.items():
    if not lst:
        continue
    cols = 3
    while len(lst) % cols:
        lst.append(np.full_like(lst[0], 255))
    sheet = np.vstack([np.hstack(lst[i:i + cols]) for i in range(0, len(lst), cols)])
    # split into pieces of at most 9 rows so each picture stays readable
    step = 130 * 9
    for k, y0 in enumerate(range(0, sheet.shape[0], step)):
        cv2.imwrite(OUT + f"id_montage_{kind}_{k + 1}.jpg", sheet[y0:y0 + step])
df = pd.DataFrame(rows)
print(df.groupby("kind").agg(n=("file", "size"), found=("page_found_after_orientation", "sum")).to_string())
