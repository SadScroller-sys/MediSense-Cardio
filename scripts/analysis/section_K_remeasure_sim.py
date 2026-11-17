"""Section K (re-measurement of the SIMULATED new-100 set with the cleaned heart-rate measurement; post hoc, logged 2026-11-08).
Same change as Section J: nk.ecg_clean before beat finding on BOTH the reference (PTB-XL records100 lead II, 100 Hz, exactly the reference of the extension run) and the digitised lead II (1000 Hz).
The first 50 recordings cannot be re-measured (their digitised signals were not saved). Writes results/analysis/sectionK_remeasured_sim.csv"""
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


def hr(sig, fs, clean):
    import neurokit2 as nk
    x = nk.ecg_clean(sig, sampling_rate=fs, method="neurokit") if clean else sig
    p, _ = nk.ecg_peaks(x, sampling_rate=fs)
    return float(np.nanmean(nk.ecg_rate(p, sampling_rate=fs, desired_length=len(sig))))


def ref_job(rec):
    import wfdb
    num = rec.split("_")[0]
    r = wfdb.rdrecord(ROOT + f"data/ptbxl/records100/{int(num) // 1000 * 1000:05d}/{num}_lr")
    s = r.p_signal[:, r.sig_name.index("II")]
    return rec, hr(s, r.fs, False), hr(s, r.fs, True)


def dig_job(path):
    z = np.load(path, allow_pickle=False)
    s = np.asarray(z["II"], dtype=float)
    s = s[np.isfinite(s)] / 1000.0
    if len(s) <= 10:
        return os.path.basename(path)[:-4], np.nan
    try:
        return os.path.basename(path)[:-4], hr(s, 1000, True)
    except Exception:
        return os.path.basename(path)[:-4], np.nan


if __name__ == "__main__":
    from concurrent.futures import ProcessPoolExecutor
    e = pd.read_csv(ROOT + "results/extension/results_extension.csv")
    recs = sorted(e.record.unique())
    files = sorted(glob.glob(NPZ + "*.npz"))
    assert len(files) == 1300
    with ProcessPoolExecutor(6) as ex:
        ref = {r: (a, b) for r, a, b in ex.map(ref_job, recs, chunksize=2)}
        dig = dict(ex.map(dig_job, files, chunksize=8))
    e["gt_raw_check"] = e.record.map(lambda r: ref[r][0])
    e["gt_hr_clean"] = e.record.map(lambda r: ref[r][1])
    e["dig_hr_clean"] = e.variant_id.map(dig)
    e.loc[e.dig_hr.isna(), "dig_hr_clean"] = np.nan
    e["diff_clean"] = (e.dig_hr_clean - e.gt_hr_clean).abs()
    print("reference reproduced (raw) within 0.15 bpm:", float((np.abs(e.gt_raw_check - e.gt_hr) < 0.15).mean()))
    e.to_csv(ROOT + "results/analysis/sectionK_remeasured_sim.csv", index=False)
    print("DONE", len(e))
