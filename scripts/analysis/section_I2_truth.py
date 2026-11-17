"""Section I2 (diagnosis, exploratory): TRUE vs DIGITISED lead II on the clean kit page (C0) of the 140 real-capture recordings.
Inputs: results/truth/truth_lead_II.npz (true lead II, native sampling rate, 10 s), digitised C0 npz, results tables.
Question: for the clean pages with a wrong heart rate (>5 bpm), is the REFERENCE heart rate (peak detector on the true signal), the DIGITISED signal, or the one-number HR method at fault?"""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
ROOT = "D:/Capstone Project/"
METHODS = {"nk_raw": ("neurokit", False), "nk_clean": ("neurokit", True), "pantompkins": ("pantompkins1985", True), "hamilton": ("hamilton2002", True), "elgendi": ("elgendi2010", True)}


def peaks(sig, fs, method, clean):
    import neurokit2 as nk
    x = nk.ecg_clean(sig, sampling_rate=fs, method="neurokit") if clean else sig
    return np.asarray(nk.ecg_peaks(x, sampling_rate=fs, method=method)[1]["ECG_R_Peaks"], dtype=float) / fs     # seconds


def hr_mean_rr(t):
    return float(60.0 / np.diff(t).mean()) if len(t) >= 3 else np.nan


def hr_notebook(sig, fs):
    import neurokit2 as nk
    p, _ = nk.ecg_peaks(sig, sampling_rate=fs)
    return float(np.nanmean(nk.ecg_rate(p, sampling_rate=fs, desired_length=len(sig))))


def match(a, b, tol=0.06):
    """a, b: peak times (s). Best constant lag in +-0.5 s, then greedy matching within tol. Returns lag, matched, only_a, only_b."""
    best = (0, -1, None)
    for lag in np.arange(-0.5, 0.5001, 0.01):
        n = sum(np.min(np.abs(b - (x + lag))) <= tol for x in a) if len(b) else 0
        if n > best[1]:
            best = (lag, n, None)
    lag = best[0]
    used, m = set(), 0
    for x in a:
        if not len(b):
            break
        j = int(np.argmin(np.abs(b - (x + lag))))
        if abs(b[j] - (x + lag)) <= tol and j not in used:
            used.add(j); m += 1
    return float(lag), m, len(a) - m, len(b) - m


def one(args):
    from scipy.signal import resample
    rid, fs, path, tru, vid = args
    z = np.load(path, allow_pickle=False)
    dig = np.asarray(z["II"], dtype=float)
    dig = dig[np.isfinite(dig)] / 1000.0
    out = dict(variant_id=vid, record=rid, fs=fs)
    out["hr_truth_notebook_method"] = hr_notebook(tru, fs)
    out["hr_dig_notebook_method"] = hr_notebook(dig, 1000)
    tru1k = resample(tru, int(round(len(tru) * 1000 / fs)))
    ns = min(len(tru1k), len(dig))
    a, b = tru1k[:ns], dig[:ns]
    # shape agreement on the common 10 s window (best lag +-300 ms)
    best = -2
    for lag in range(-300, 301, 5):
        x = a[max(0, lag): ns + min(0, lag)]
        y = b[max(0, -lag): ns + min(0, -lag)]
        n = min(len(x), len(y))
        if n > 2000:
            c = np.corrcoef(x[:n], y[:n])[0, 1]
            best = max(best, c)
    out["pcc_true_vs_dig"] = float(best)
    pk_t, pk_d = {}, {}
    for k, (m, c) in METHODS.items():
        try:
            pk_t[k] = peaks(tru, fs, m, c)
        except Exception:
            pk_t[k] = np.array([])
        try:
            pk_d[k] = peaks(dig, 1000, m, c)
        except Exception:
            pk_d[k] = np.array([])
        out["hr_truth_" + k], out["n_truth_" + k] = hr_mean_rr(pk_t[k]), len(pk_t[k])
        out["hr_dig_" + k], out["n_dig_" + k] = hr_mean_rr(pk_d[k]), len(pk_d[k])
    # same detector, matched beats: truth vs digitised (neurokit cleaned)
    lag, mt, only_t, only_d = match(pk_t["nk_clean"], pk_d["nk_clean"])
    out.update(match_lag_s=lag, beats_matched=mt, beats_only_in_truth=only_t, beats_only_in_dig=only_d)
    lag, mt, only_t, only_d = match(pk_t["nk_raw"], pk_d["nk_raw"])
    out.update(rawmatch_matched=mt, rawmatch_only_truth=only_t, rawmatch_only_dig=only_d)
    # agreement among detectors on the TRUE signal (spread) and a consensus truth HR
    h = [out["hr_truth_" + k] for k in METHODS]
    out["truth_spread_bpm"] = float(np.nanmax(h) - np.nanmin(h))
    out["truth_consensus_hr"] = float(np.nanmedian(h))
    h = [out["hr_dig_" + k] for k in METHODS]
    out["dig_spread_bpm"] = float(np.nanmax(h) - np.nanmin(h))
    out["dig_consensus_hr"] = float(np.nanmedian(h))
    return out


if __name__ == "__main__":
    from concurrent.futures import ProcessPoolExecutor
    z = np.load(ROOT + "results/truth/truth_lead_II.npz")
    m = pd.read_csv(ROOT + "results/truth/truth_meta.csv")
    new = pd.read_csv(ROOT + "results/armCext/results_armCext_all.csv")
    old = pd.read_csv(ROOT + "results/armC/results_armC.csv")
    new["set"], old["set"] = "new100", "first40"
    d = pd.concat([old, new], ignore_index=True)
    d = d[d.axis == "C0_kit_original"].reset_index(drop=True)
    dirs = {"new100": ROOT + "results/armCext/armCext_digitized_12lead_all/", "first40": ROOT + "results/armC/armC_digitized_12lead/"}
    fs = dict(zip(m["id"].astype(str), m["fs"]))
    items = [(str(r.record), float(fs[str(r.record)]), dirs[r.set] + r.variant_id + ".npz", np.asarray(z["r" + str(r.record)], dtype=float), r.variant_id) for r in d.itertuples()]
    with ProcessPoolExecutor(6) as ex:
        res = list(ex.map(one, items, chunksize=2))
    f = pd.DataFrame(res).drop(columns=["record", "fs"])
    d = d.merge(f, on="variant_id")
    d["wrong5"] = d.diff_bpm > 5
    d.to_csv(ROOT + "results/analysis/sectionI2_truth_vs_digitised.csv", index=False)
    print("DONE", len(d))
