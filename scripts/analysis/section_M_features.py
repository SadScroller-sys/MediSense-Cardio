"""Section M features (exploratory; rules in docs/plan/analysis_plan_changes.md 2026-11-08): agreement of five heart-rate detectors on the DIGITISED lead II.
Usage: python -I scripts/analysis/section_M_features.py   (computes simulated new 100 + Arm C 40 + extension 100; cached to results/analysis/sectionM_detector_features.csv)"""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
import glob
import sys
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
ROOT = "D:/Capstone Project/"
FS = 1000
METHODS = {"nk_raw": ("neurokit", False), "nk_clean": ("neurokit", True), "pantompkins": ("pantompkins1985", True), "hamilton": ("hamilton2002", True), "elgendi": ("elgendi2010", True)}


def features(path):
    import neurokit2 as nk
    z = np.load(path, allow_pickle=False)
    s = np.asarray(z["II"], dtype=float)
    s = s[np.isfinite(s)] / 1000.0
    out = dict(variant_id=os.path.basename(path)[:-4])
    hrs = []
    for k, (m, c) in METHODS.items():
        try:
            x = nk.ecg_clean(s, sampling_rate=FS, method="neurokit") if c else s
            r = np.asarray(nk.ecg_peaks(x, sampling_rate=FS, method=m)[1]["ECG_R_Peaks"], dtype=float) / FS
            h = float(60.0 / np.diff(r).mean()) if len(r) >= 3 else np.nan
        except Exception:
            h = np.nan
        hrs.append(h)
    a = np.array(hrs)
    ok = np.isfinite(a)
    out["det_n_missing"] = int((~ok).sum())
    if ok.sum() >= 2:
        med = float(np.median(a[ok]))
        out["det_spread"] = float(a[ok].max() - a[ok].min())
        out["det_std"] = float(a[ok].std())
        out["det_n_agree"] = int((np.abs(a[ok] - med) <= 5).sum())
    else:
        out["det_spread"] = out["det_std"] = np.nan
        out["det_n_agree"] = 0
    out["det_nkclean_vs_pt"] = float(abs(a[1] - a[2])) if ok[1] and ok[2] else np.nan
    return out


if __name__ == "__main__":
    from concurrent.futures import ProcessPoolExecutor
    sys.path.insert(0, ROOT + "scripts/analysis")
    import section_M_features as me
    dirs = [ROOT + "results/extension/extension_digitized_12lead/extension_digitized_12lead/", ROOT + "results/armCext/armCext_digitized_12lead_all/", ROOT + "results/armC/armC_digitized_12lead/"]
    files = [f for d in dirs for f in sorted(glob.glob(d + "*.npz"))]
    assert len(files) == 1300 + 900 + 360, len(files)
    with ProcessPoolExecutor(6) as ex:
        res = list(ex.map(me.features, files, chunksize=8))
    pd.DataFrame(res).to_csv(ROOT + "results/analysis/sectionM_detector_features.csv", index=False)
    print("DONE", len(res))
