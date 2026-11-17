"""Phase 2b spike: do the five Tier-1 quality signals actually move the way they should as each axis gets
worse? Run on the 6 local demo images (00001-00006, from the Step-3 six-record validation) since the real
50-record sweep's clean pages are on Drive only (see PROGRESS-LOG). This is a cheap correctness check before
spending any time fetching the real sample -- the project's own habit (Day 1 spike, Gate 2 spike, dry-run
before GPU time) applied to this stage.

For each demo image: apply every axis at every level (identical degrade code to the sweep notebooks,
scripts/quality_proxy/degrade.py), compute the five signals, and report the correlation (Spearman) between
level and the one signal each axis is supposed to move. A working signal should show a clear monotonic trend;
a signal with near-zero correlation on its own axis is not doing its job and needs re-thinking before it goes
anywhere near the real calibration.
"""
import glob
import cv2
import numpy as np
from scipy.stats import spearmanr

from degrade import AXES, LEVELS
from image_quality import compute_quality_signals

IMAGES = sorted(glob.glob(r"D:\Capstone Project\results\multi_sample_test\images\*.png"))
print(f"Using {len(IMAGES)} local demo images: {[p.split(chr(92))[-1] for p in IMAGES]}\n")

# which signal each axis is primarily expected to move, and in which direction
EXPECTED = {
    "blur": ("blur_score", "down"),
    "rotate": ("skew_deg", "up"),
    "jpeg": ("blockiness_score", "down"),  # confirmed direction 2026-09-28, opposite of the naive guess
    "resolution": ("resolution_score", "down"),
    "brightness": ("contrast_score", None),   # direction not obvious a priori; report only
    "gridcontrast": ("contrast_score", "down"),
}

rows = []
for img_path in IMAGES:
    clean = cv2.imread(img_path)
    if clean is None:
        print("SKIP (unreadable):", img_path); continue
    clean_sig = compute_quality_signals(clean)
    rows.append({"record": img_path.split("\\")[-1], "axis": "clean", "level": 0, **clean_sig})
    for axis, fn in AXES.items():
        for level in LEVELS:
            degraded = fn(clean, level)
            sig = compute_quality_signals(degraded)
            rows.append({"record": img_path.split("\\")[-1], "axis": axis, "level": level, **sig})

import csv
out_path = r"D:\Capstone Project\results\quality_proxy_spike.csv"
with open(out_path, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["record", "axis", "level", "blur_score", "skew_deg",
                                       "resolution_score", "contrast_score", "blockiness_score"])
    w.writeheader()
    for r in rows:
        w.writerow(r)
print(f"Wrote {len(rows)} rows to {out_path}\n")

print(f"{'axis':<14}{'signal':<18}{'expected':<10}{'spearman rho':<14}{'verdict'}")
for axis, (signal, direction) in EXPECTED.items():
    sub = [r for r in rows if r["axis"] == axis and r[signal] is not None]
    levels = [r["level"] for r in sub]
    vals = [r[signal] for r in sub]
    if len(set(levels)) < 2:
        print(f"{axis:<14}{signal:<18}{'?':<10}{'n/a':<14}not enough data"); continue
    rho, p = spearmanr(levels, vals)
    if direction == "up":
        ok = rho > 0.3
    elif direction == "down":
        ok = rho < -0.3
    else:
        ok = None
    verdict = "OK" if ok else ("report only" if ok is None else "WEAK/WRONG DIRECTION")
    print(f"{axis:<14}{signal:<18}{str(direction):<10}{rho:<14.3f}{verdict}")

# also report skew_deg's None-rate (grid can disappear under heavy blur/resolution loss)
n_none = sum(1 for r in rows if r["skew_deg"] is None)
print(f"\nskew_deg returned None (too few lines detected) for {n_none}/{len(rows)} rows.")
