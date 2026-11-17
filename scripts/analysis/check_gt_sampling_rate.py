"""Does the ~20 ms clean-image interval 'noise floor' come from ground truth being 100 Hz?

The sweep computed ground-truth PR/QRS/QT/QTc from PTB-XL's 100 Hz records (10 ms per sample), but the
digitized signal is 1000 Hz. Recompute the ground truth from the SAME records at 500 Hz and compare the
clean-image bias of the digitized values against each.
"""
import ast
import numpy as np
import pandas as pd
import neurokit2 as nk
import wfdb

D = r"D:\Capstone Project\data\ptbxl"
res = pd.read_csv(r"D:\Capstone Project\results\v2_intervals\results_v2_clean.csv")
clean = res[(res["axis"] == "clean") & res["reliable"]].copy()

db = pd.read_csv(f"{D}/ptbxl_database.csv")
db["record"] = db["filename_lr"].apply(lambda p: p.split("/")[-1])
hr_path = dict(zip(db["record"], db["filename_hr"]))


def intervals(sig, fs):
    out = dict(pr=np.nan, qrs=np.nan, qt=np.nan, qtc=np.nan, hr=np.nan)
    try:
        c = nk.ecg_clean(sig, sampling_rate=fs, method="neurokit")
        _, r = nk.ecg_peaks(c, sampling_rate=fs)
        if r["ECG_R_Peaks"].sum() < 3:
            return out
        hr = float(np.nanmean(nk.ecg_rate(r, sampling_rate=fs, desired_length=len(c))))
        _, w = nk.ecg_delineate(c, r, sampling_rate=fs, method="dwt")
        g = lambda k: np.array(w.get(k, []), dtype=float)

        def md(a, b):
            n = min(len(a), len(b))
            d = (b[:n] - a[:n])
            d = d[~np.isnan(d)]
            return float(np.mean(d)) / fs * 1000 if len(d) else np.nan

        out["hr"] = hr
        out["pr"] = md(g("ECG_P_Onsets"), g("ECG_R_Onsets"))
        out["qrs"] = md(g("ECG_R_Onsets"), g("ECG_R_Offsets"))
        out["qt"] = md(g("ECG_R_Onsets"), g("ECG_T_Offsets"))
        if not np.isnan(out["qt"]) and hr > 0:
            out["qtc"] = out["qt"] / np.sqrt(60.0 / hr)
    except Exception:
        pass
    return out


rows = []
for rec in clean["record"]:
    r = wfdb.rdrecord(f"{D}/{hr_path[rec]}")
    sig = r.p_signal[:, r.sig_name.index("II")]
    iv = intervals(sig, r.fs)
    rows.append({"record": rec, **{f"gt500_{k}": v for k, v in iv.items()}, "fs500": r.fs})
gt500 = pd.DataFrame(rows)
m = clean.merge(gt500, on="record")

print(f"records: {len(m)}, fs of hr files: {sorted(m['fs500'].unique())}")
print(f"\n{'measure':<6} {'bias vs 100Hz GT':>18} {'bias vs 500Hz GT':>18} {'MAE 100Hz':>10} {'MAE 500Hz':>10}   (digitized - GT, ms)")
for name, dig, g100, g500 in [("PR", "dig_pr_ms", "gt_pr_ms", "gt500_pr"),
                              ("QRS", "dig_qrs_ms", "gt_qrs_ms", "gt500_qrs"),
                              ("QT", "dig_qt_ms", "gt_qt_ms", "gt500_qt"),
                              ("QTc", "dig_qtc_ms", "gt_qtc_ms", "gt500_qtc")]:
    d100 = (m[dig] - m[g100]).dropna()
    d500 = (m[dig] - m[g500]).dropna()
    print(f"{name:<6} {d100.mean():>18.1f} {d500.mean():>18.1f} {d100.abs().mean():>10.1f} {d500.abs().mean():>10.1f}")

print("\nGT self-consistency (100 Hz vs 500 Hz, same record):")
for name, a, b in [("QT", "gt_qt_ms", "gt500_qt"), ("QTc", "gt_qtc_ms", "gt500_qtc"), ("QRS", "gt_qrs_ms", "gt500_qrs")]:
    d = (m[a] - m[b]).dropna()
    print(f"  {name}: mean diff {d.mean():.1f} ms, mean |diff| {d.abs().mean():.1f} ms")
m.to_csv(r"D:\Capstone Project\results\v2_intervals\journal\gt_sampling_rate_check.csv", index=False)
