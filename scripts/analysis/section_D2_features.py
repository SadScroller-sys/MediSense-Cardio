"""D2 (exploratory, see docs/plan/analysis_plan_changes.md 2026-11-07): features computed from the digitiser's OUTPUT (the saved 12-lead signal) alone.
Never uses the reference. One row per image; cached to results/analysis/sectionD2_features.csv. Run time: a few minutes (6 workers)."""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
import glob
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
ROOT = "D:/Capstone Project/"
NPZ = ROOT + "results/extension/extension_digitized_12lead/extension_digitized_12lead/"
LEADS = ["I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6"]
FS = 1000


def _prep(sig, min_s=1.5, min_fill=0.9):
    sig = np.asarray(sig, dtype=float)
    idx = np.where(np.isfinite(sig))[0]
    if len(idx) == 0:
        return None
    a0, b0 = int(idx[0]), int(idx[-1]) + 1
    seg = sig[a0:b0].copy()
    fin = np.isfinite(seg)
    if len(seg) < min_s * FS or fin.mean() < min_fill:
        return None
    if not fin.all():
        seg[~fin] = np.interp(np.where(~fin)[0], np.where(fin)[0], seg[fin])
    return a0, seg


def _rms(x):
    return float(np.sqrt(np.mean(np.square(x))))


def features(path):
    import neurokit2 as nk
    z = np.load(path, allow_pickle=False)
    L = {k: np.asarray(z[k], dtype=float) for k in LEADS}
    out = dict(variant_id=os.path.basename(path)[:-4])
    ii = L["II"]
    out["ii_complete"] = float(np.isfinite(ii).mean())
    cnt = {k: int(np.isfinite(v).sum()) for k, v in L.items()}
    out["n_unreadable_leads"] = int(sum(1 for k in LEADS if cnt[k] < 1500))
    out["mean_other_lead_complete"] = float(np.mean([min(1.0, cnt[k] / 2500.0) for k in LEADS if k != "II"]))
    nan = np.nan
    for k in ("n_beats", "hr_ii", "hr_implausible", "rr_cv", "rr_max_ratio", "rr_min_ratio", "amp_log", "hf_share", "einthoven", "goldberger",
              "xlead_count_match", "xlead_count_absdiff"):
        out[k] = nan
    p2 = _prep(ii, min_s=3.0)
    if p2 is None:
        return out
    a2, seg2 = p2
    try:
        cl = nk.ecg_clean(seg2, sampling_rate=FS, method="neurokit")
        rpk = np.asarray(nk.ecg_peaks(cl, sampling_rate=FS)[1]["ECG_R_Peaks"])
    except Exception:
        return out
    out["n_beats"] = int(len(rpk))
    out["amp_log"] = float(np.log10(max(1e-6, np.percentile(seg2, 95) - np.percentile(seg2, 5))))
    f = np.abs(np.fft.rfft(seg2 - seg2.mean())) ** 2
    fr = np.fft.rfftfreq(len(seg2), 1 / FS)
    out["hf_share"] = float(f[fr > 40].sum() / max(1e-12, f.sum()))
    if len(rpk) >= 3:
        rr = np.diff(rpk) / FS
        hr = float(np.mean(60.0 / rr))
        out["hr_ii"] = hr
        out["hr_implausible"] = float(hr < 30 or hr > 200)
        out["rr_cv"] = float(np.std(rr) / np.mean(rr))
        out["rr_max_ratio"] = float(rr.max() / np.median(rr))
        out["rr_min_ratio"] = float(rr.min() / np.median(rr))
    # Einthoven: II = I + III in the window where all three leads exist
    m = np.isfinite(L["I"]) & np.isfinite(L["II"]) & np.isfinite(L["III"])
    if m.sum() >= 1000:
        i_, ii_, iii_ = (L[k][m] - L[k][m].mean() for k in ("I", "II", "III"))
        out["einthoven"] = float(_rms(ii_ - i_ - iii_) / max(1e-9, _rms(ii_)))
    # Goldberger: aVR + aVL + aVF = 0
    m = np.isfinite(L["aVR"]) & np.isfinite(L["aVL"]) & np.isfinite(L["aVF"])
    if m.sum() >= 1000:
        a_, b_, c_ = (L[k][m] - L[k][m].mean() for k in ("aVR", "aVL", "aVF"))
        out["goldberger"] = float(_rms(a_ + b_ + c_) / max(1e-9, np.mean([_rms(a_), _rms(b_), _rms(c_)])))
    # each other lead's own beat count vs lead II's in the same window
    match, diffs = [], []
    for k in LEADS:
        if k == "II":
            continue
        pr = _prep(L[k])
        if pr is None:
            continue
        a0, seg = pr
        try:
            c = nk.ecg_clean(seg, sampling_rate=FS, method="neurokit")
            pk = np.asarray(nk.ecg_peaks(c, sampling_rate=FS)[1]["ECG_R_Peaks"]) + a0
        except Exception:
            continue
        lo, hi = a0 + 100, a0 + len(seg) - 100
        n_lead = int(((pk >= lo) & (pk < hi)).sum())
        n_ref = int((((rpk + a2) >= lo) & ((rpk + a2) < hi)).sum())
        match.append(float(n_lead == n_ref))
        diffs.append(abs(n_lead - n_ref))
    if match:
        out["xlead_count_match"] = float(np.mean(match))
        out["xlead_count_absdiff"] = float(np.mean(diffs))
    return out


def run_pool(fn, items, workers=6):
    from concurrent.futures import ProcessPoolExecutor, as_completed
    res = []
    with ProcessPoolExecutor(workers) as ex:
        futs = {ex.submit(fn, it): it for it in items}
        for n, f in enumerate(as_completed(futs), 1):
            try:
                res.append(f.result(timeout=900))
            except Exception as exc:
                raise SystemExit(f"FAILED on {futs[f]}: {exc!r}")
            if n % 100 == 0 or n == len(items):
                print(f"features: {n}/{len(items)} done", flush=True)
    return res


if __name__ == "__main__":
    files = sorted(glob.glob(NPZ + "*.npz"))
    assert len(files) == 1300
    df = pd.DataFrame(run_pool(features, files))
    df.to_csv(ROOT + "results/analysis/sectionD2_features.csv", index=False)
    print(df.describe().T[["count", "mean", "std", "min", "max"]].round(3).to_string())
    print("ALL FEATURES DONE")
