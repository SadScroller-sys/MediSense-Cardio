"""Section I (diagnosis, exploratory): why does the CLEAN kit page (C0) of some real-capture recordings give a wrong heart rate?
Uses only the saved digitised signals of C0 (first 40 + new 100 recordings) and results tables; the reference (true) signals are NOT on this computer.
For each recording: digitised lead II completeness, beat count, RR sequence irregularity, HR by 5 different peak detectors (all on the digitised signal), and amplitude/noise features.
Question: does another detector on the digitised signal give the reference HR (-> detector fragility) or do all agree with the digitiser's own HR (-> signal lost/changed or reference problem)?"""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
import sys
import warnings
import zipfile

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
ROOT = "D:/Capstone Project/"
FS = 1000


def hr_from(sig, method, clean):
    import neurokit2 as nk
    x = nk.ecg_clean(sig, sampling_rate=FS, method="neurokit") if clean else sig
    r = np.asarray(nk.ecg_peaks(x, sampling_rate=FS, method=method)[1]["ECG_R_Peaks"])
    if len(r) < 3:
        return np.nan, len(r), r
    rr = np.diff(r) / FS
    return float(60.0 / rr.mean()), len(r), r


def one(args):
    vid, path = args
    z = np.load(path, allow_pickle=False)
    ii = np.asarray(z["II"], dtype=float)
    out = dict(variant_id=vid, n_samples_II=int(np.isfinite(ii).sum()), n_nan_II=int((~np.isfinite(ii)).sum()))
    s = ii[np.isfinite(ii)] / 1000.0                  # same as the notebook: drop NaN, microvolt -> millivolt
    out["amp_p95_p5_mV"] = float(np.percentile(s, 95) - np.percentile(s, 5))
    for name, (m, c) in {"notebook_raw": ("neurokit", False), "neurokit_clean": ("neurokit", True), "pantompkins": ("pantompkins1985", True),
                         "hamilton": ("hamilton2002", True), "elgendi": ("elgendi2010", True)}.items():
        try:
            hr, n, r = hr_from(s, m, c)
        except Exception:
            hr, n, r = np.nan, 0, np.array([])
        out["hr_" + name], out["n_" + name] = hr, n
        if name == "notebook_raw" and len(r) >= 3:
            rr = np.diff(r) / FS
            out["rr_cv"] = float(rr.std() / rr.mean())
            out["rr_max_over_median"] = float(rr.max() / np.median(rr))
            out["rr_min_over_median"] = float(rr.min() / np.median(rr))
            out["n_rr_gt_1p6_median"] = int((rr > 1.6 * np.median(rr)).sum())
            out["n_rr_lt_0p6_median"] = int((rr < 0.6 * np.median(rr)).sum())
    return out


if __name__ == "__main__":
    from concurrent.futures import ProcessPoolExecutor
    new = pd.read_csv(ROOT + "results/armCext/results_armCext_all.csv")
    old = pd.read_csv(ROOT + "results/armC/results_armC.csv")
    new["set"], old["set"] = "new100", "first40"
    d = pd.concat([old, new], ignore_index=True)
    d = d[d.axis == "C0_kit_original"].reset_index(drop=True)
    dirs = {"new100": ROOT + "results/armCext/armCext_digitized_12lead_all/", "first40": ROOT + "results/armC/armC_digitized_12lead/"}
    items = [(r.variant_id, dirs[r.set] + r.variant_id + ".npz") for r in d.itertuples()]
    assert all(os.path.exists(p) for _, p in items), "missing npz"
    with ProcessPoolExecutor(6) as ex:
        res = list(ex.map(one, items))
    f = pd.DataFrame(res)
    d = d.merge(f, on="variant_id")
    d["wrong5"] = d.diff_bpm > 5
    d.to_csv(ROOT + "results/analysis/sectionI_clean_page_diagnosis.csv", index=False)
    print("DONE", len(d), "wrong:", int(d.wrong5.sum()))
