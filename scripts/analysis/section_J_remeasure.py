"""Section J (re-measurement, post hoc; logged in docs/plan/analysis_plan_changes.md 2026-11-08):
The Arm C notebooks found the beats with neurokit2 on the RAW signal (no nk.ecg_clean) for both the true and the digitised lead II.
Diagnosis (Section I2) showed that this raw step is fragile. Here BOTH signals get the standard cleaning step (nk.ecg_clean, method 'neurokit') before the beats are found;
everything else is identical to the notebook (heart rate = mean of nk.ecg_rate, digitised lead II with NaN dropped and microvolt -> millivolt, 1000 Hz; true lead II at its own rate).
Writes results/analysis/sectionJ_remeasured.csv (one row per image) and SECTION_J.md."""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
ROOT = "D:/Capstone Project/"


def hr_clean(sig, fs):
    import neurokit2 as nk
    x = nk.ecg_clean(sig, sampling_rate=fs, method="neurokit")
    p, _ = nk.ecg_peaks(x, sampling_rate=fs)
    return float(np.nanmean(nk.ecg_rate(p, sampling_rate=fs, desired_length=len(sig))))


def work(args):
    kind, key, fs, payload = args
    try:
        if kind == "truth":
            return key, hr_clean(payload, fs)
        z = np.load(payload, allow_pickle=False)
        s = np.asarray(z["II"], dtype=float)
        s = s[np.isfinite(s)] / 1000.0
        return key, (hr_clean(s, 1000) if len(s) > 10 else np.nan)
    except Exception:
        return key, np.nan


if __name__ == "__main__":
    from concurrent.futures import ProcessPoolExecutor
    z = np.load(ROOT + "results/truth/truth_lead_II.npz")
    m = pd.read_csv(ROOT + "results/truth/truth_meta.csv")
    fs = dict(zip(m["id"].astype(str), m["fs"]))
    new = pd.read_csv(ROOT + "results/armCext/results_armCext_all.csv")
    old = pd.read_csv(ROOT + "results/armC/results_armC.csv")
    new["set"], old["set"] = "armC_new100", "armC_first40"
    d = pd.concat([old, new], ignore_index=True)
    dirs = {"armC_new100": ROOT + "results/armCext/armCext_digitized_12lead_all/", "armC_first40": ROOT + "results/armC/armC_digitized_12lead/"}
    jobs = [("truth", str(r), float(fs[str(r)]), np.asarray(z["r" + str(r)], dtype=float)) for r in sorted(d.record.astype(str).unique())]
    jobs += [("dig", v, 1000.0, dirs[s] + v + ".npz") for v, s, dh in zip(d.variant_id, d.set, d.dig_hr) if pd.notna(dh)]
    with ProcessPoolExecutor(6) as ex:
        res = dict(ex.map(work, jobs, chunksize=8))
    d["gt_hr_clean"] = d.record.astype(str).map(lambda r: res[r])
    d["dig_hr_clean"] = d.variant_id.map(lambda v: res.get(v, np.nan))
    d.loc[d.dig_hr.isna(), "dig_hr_clean"] = np.nan                      # no output stays no output
    d["diff_clean"] = (d.dig_hr_clean - d.gt_hr_clean).abs()
    d.to_csv(ROOT + "results/analysis/sectionJ_remeasured.csv", index=False)
    print("DONE", len(d), "truth NaN:", int(d.gt_hr_clean.isna().sum()), "dig NaN where output existed:", int((d.dig_hr.notna() & d.dig_hr_clean.isna()).sum()))
