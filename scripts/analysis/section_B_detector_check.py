"""Section B3 support: how well do alternative R-peak detectors agree with the main heart-rate reference on the ORIGINAL signals (new 100, 500 Hz lead II)?
No damaged page is looked at. HR = mean of 60/RR (the study's definition). Writes results/analysis/sectionB_detector_agreement.csv.
Result: every alternative disagrees with the main reference on many original recordings, so a second detector is only a weak robustness check."""
import os
os.environ["OMP_NUM_THREADS"] = "1"
import warnings
import neurokit2 as nk
import numpy as np
import pandas as pd
import wfdb
warnings.filterwarnings("ignore")
ROOT = "D:/Capstone Project/"
e = pd.read_csv(ROOT + "results/extension/results_extension.csv")
gtm = e[e.axis == "clean"].set_index("record").gt_hr
recs = sorted(gtm.index)
meths = ["neurokit", "pantompkins1985", "kalidas2017", "engzeemod2012", "elgendi2010", "hamilton2002", "christov2004", "rodrigues2021"]
res = {m: [] for m in meths}
for rec in recs:
    num = rec.split("_")[0]
    f = f"{int(num) // 1000 * 1000:05d}"
    r5 = wfdb.rdrecord(ROOT + f"data/ptbxl/records500/{f}/{num}_hr")
    ii = r5.p_signal[:, r5.sig_name.index("II")]
    cl = nk.ecg_clean(ii, sampling_rate=r5.fs, method="neurokit")
    for m in meths:
        try:
            r = nk.ecg_peaks(cl, sampling_rate=r5.fs, method=m)[1]["ECG_R_Peaks"]
            hr = float(np.mean(60.0 / (np.diff(r) / r5.fs))) if len(r) >= 3 else np.nan
        except Exception:
            hr = np.nan
        res[m].append(hr)
rows = []
for m in meths:
    a = np.array(res[m])
    d = np.abs(a - gtm.loc[recs].values)
    rows.append(dict(detector=m, differ_gt5bpm_of_100=int(np.nansum(d > 5)), no_result=int(np.isnan(a).sum())))
pd.DataFrame(rows).to_csv(ROOT + "results/analysis/sectionB_detector_agreement.csv", index=False)
print(pd.DataFrame(rows).to_string(index=False))
