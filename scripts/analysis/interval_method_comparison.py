"""Which interval-measurement method on the ORIGINAL PTB-XL signal agrees best with the commercial 12SL algorithm?

For our 50 recordings (500 Hz records) it measures PR, QRS, QT, QTc with NeuroKit2 using
  delineation method: dwt (what the sweep used), cwt, peak
  aggregation:        lead II only (what the sweep used) | median over the 12 leads | "global" (earliest onset to latest offset over leads)
and compares with PTB-XL+ 12SL global values (Spearman correlation, median absolute difference, mean bias).
R peaks are detected once on lead II and reused for all leads. Writes results/interval_method_comparison.md and a csv.
Run time: roughly 15 to 30 minutes.
"""
import warnings
import numpy as np
import pandas as pd
import wfdb
import neurokit2 as nk

warnings.filterwarnings("ignore")
ROOT = "D:/Capstone Project/"
db = pd.read_csv(ROOT + "data/ptbxl/ptbxl_database.csv")
db["record"] = db["filename_lr"].str.split("/").str[-1]
res = pd.read_csv(ROOT + "results/v2_intervals/results_v2.csv")
clean = res[res.axis == "clean"].merge(db[["record", "ecg_id"]], on="record")
x12 = pd.read_csv(ROOT + "data/ptbxl_plus/12sl_features.csv").set_index("ecg_id")
METHODS = ["dwt", "cwt", "peak"]


def delineate(sig, fs, rpeaks_idx, method):
    cleaned = nk.ecg_clean(sig, sampling_rate=fs, method="neurokit")
    _, waves = nk.ecg_delineate(cleaned, {"ECG_R_Peaks": rpeaks_idx}, sampling_rate=fs, method=method)
    get = lambda k: np.array(waves.get(k, []), dtype=float)
    return {k: get(k) for k in ("ECG_P_Onsets", "ECG_R_Onsets", "ECG_R_Offsets", "ECG_T_Offsets")}


def mean_ms(a, b, fs):
    n = min(len(a), len(b))
    if n == 0:
        return np.nan
    d = (b[:n] - a[:n]); d = d[np.isfinite(d)]
    return float(np.mean(d)) / fs * 1000.0 if len(d) else np.nan


def durations(w, fs):
    return {"pr": mean_ms(w["ECG_P_Onsets"], w["ECG_R_Onsets"], fs), "qrs": mean_ms(w["ECG_R_Onsets"], w["ECG_R_Offsets"], fs),
            "qt": mean_ms(w["ECG_R_Onsets"], w["ECG_T_Offsets"], fs)}


def global_durations(ws, fs):
    n = min(len(w["ECG_R_Onsets"]) for w in ws)
    st = lambda k: np.vstack([w[k][:n] for w in ws])
    with np.errstate(all="ignore"):
        p_on, r_on = np.nanmin(st("ECG_P_Onsets"), 0), np.nanmin(st("ECG_R_Onsets"), 0)
        r_off, t_off = np.nanmax(st("ECG_R_Offsets"), 0), np.nanmax(st("ECG_T_Offsets"), 0)
    return {"pr": mean_ms(p_on, r_on, fs), "qrs": mean_ms(r_on, r_off, fs), "qt": mean_ms(r_on, t_off, fs)}


rows = []
for i, (_, r) in enumerate(clean.iterrows()):
    num = r.record.split("_")[0]; folder = f"{int(num) // 1000 * 1000:05d}"
    rec = wfdb.rdrecord(ROOT + f"data/ptbxl/records500/{folder}/{num}_hr"); fs = rec.fs
    II = rec.p_signal[:, rec.sig_name.index("II")]
    try:
        cl = nk.ecg_clean(II, sampling_rate=fs, method="neurokit")
        _, rp = nk.ecg_peaks(cl, sampling_rate=fs)
        rpk = rp["ECG_R_Peaks"]
        hr = 60.0 / (np.median(np.diff(rpk)) / fs) if len(rpk) > 2 else np.nan
    except Exception:
        rpk, hr = np.array([]), np.nan
    out = {"ecg_id": r.ecg_id, "hr_nk": hr}
    for m in METHODS:
        per_lead = []
        for ln in rec.sig_name:
            try:
                per_lead.append(delineate(rec.p_signal[:, rec.sig_name.index(ln)], fs, rpk, m) if len(rpk) >= 3 else None)
            except Exception:
                per_lead.append(None)
        ok = [w for w in per_lead if w is not None]
        d2 = durations(per_lead[rec.sig_name.index("II")], fs) if per_lead[rec.sig_name.index("II")] is not None else {}
        dm = {q: np.nanmedian([durations(w, fs)[q] for w in ok]) if ok else np.nan for q in ("pr", "qrs", "qt")}
        dg = global_durations(ok, fs) if len(ok) >= 6 else {}
        for agg, d in (("leadII", d2), ("median12", dm), ("global", dg)):
            for q in ("pr", "qrs", "qt"):
                out[f"{m}|{agg}|{q}"] = d.get(q, np.nan)
    rows.append(out)
    print(f"{i + 1}/50 done", flush=True)

d = pd.DataFrame(rows)
d.to_csv(ROOT + "results/interval_method_comparison.csv", index=False)
ref = x12.reindex(d["ecg_id"].values)
ref_vals = {"pr": ref["PR_Int_Global"].values, "qrs": ref["QRS_Dur_Global"].values, "qt": ref["QT_Int_Global"].values}
sex = clean.set_index("ecg_id").loc[d["ecg_id"], "sex"].values
lines = []
for key in [c for c in d.columns if "|" in c]:
    m, agg, q = key.split("|")
    a, b = d[key].values, ref_vals[q]
    ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < 10:
        continue
    rho = pd.Series(a[ok]).corr(pd.Series(b[ok]), method="spearman")
    lines.append({"method": m, "aggregation": agg, "quantity": q, "n": int(ok.sum()), "rho": round(rho, 2),
                  "MAD_ms": round(float(np.median(np.abs(a[ok] - b[ok]))), 1), "bias_ms": round(float(np.mean(a[ok] - b[ok])), 1)})
# QTc Bazett / Fridericia from each QT and the lead-II HR, vs 12SL
for m in METHODS:
    for agg in ("leadII", "median12", "global"):
        qt = d[f"{m}|{agg}|qt"].values; rr = 60.0 / d["hr_nk"].values
        for lab, qtc, col in (("qtc_bazett", qt / np.sqrt(rr), "QT_IntBazett_Global"), ("qtc_fridericia", qt / np.cbrt(rr), "QT_IntFridericia_Global")):
            b = ref[col].values; ok = np.isfinite(qtc) & np.isfinite(b)
            if ok.sum() >= 10:
                lines.append({"method": m, "aggregation": agg, "quantity": lab, "n": int(ok.sum()),
                              "rho": round(pd.Series(qtc[ok]).corr(pd.Series(b[ok]), method="spearman"), 2),
                              "MAD_ms": round(float(np.median(np.abs(qtc[ok] - b[ok]))), 1), "bias_ms": round(float(np.mean(qtc[ok] - b[ok])), 1)})
tab = pd.DataFrame(lines).sort_values(["quantity", "rho"], ascending=[True, False])
FENCE = "`" * 3
text = ("# Interval measurement methods vs 12SL (original PTB-XL signal, 500 Hz, 50 recordings)\n\n"
        "rho = Spearman correlation with 12SL global value; MAD = median absolute difference; bias = mean difference (method minus 12SL).\n"
        "For reference, 12SL vs Glasgow agree with rho 0.91 to 0.93 and MAD 4 to 6.5 ms (results/reference_vs_ptbxl_plus.md).\n\n"
        + "\n".join(f"## {q}\n{FENCE}\n" + tab[tab.quantity == q].drop(columns="quantity").to_string(index=False) + f"\n{FENCE}\n" for q in tab.quantity.unique()))
open(ROOT + "results/interval_method_comparison.md", "w", encoding="utf-8").write(text)
print(text)
print("ALL DONE")
