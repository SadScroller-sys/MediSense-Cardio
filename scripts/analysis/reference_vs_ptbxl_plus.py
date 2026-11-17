"""How close are our reference intervals (NeuroKit2, from results_v2.csv clean rows) to the independent PTB-XL+ algorithms?

PTB-XL+ (Strodthoff et al. 2023) gives global PR / QRS / QT / QTc / heart rate from Marquette 12SL, Glasgow and ECGDeli for every
PTB-XL record. For our 50 recordings we compare:
  * NeuroKit2 reference (gt_* columns; lead II, 100 Hz record) vs each algorithm
  * the algorithms against each other (this is the yardstick: how far apart independent tools are on the same ECGs)
Writes results/reference_vs_ptbxl_plus.md.
"""
import numpy as np
import pandas as pd

P = "D:/Capstone Project/data/ptbxl_plus/"
db = pd.read_csv("D:/Capstone Project/data/ptbxl/ptbxl_database.csv")
db["record"] = db["filename_lr"].str.split("/").str[-1]
res = pd.read_csv("D:/Capstone Project/results/v2_intervals/results_v2.csv")
clean = res[res.axis == "clean"].merge(db[["record", "ecg_id"]], on="record", how="left")
assert clean["ecg_id"].notna().all() and len(clean) == 50

feat = {}
for name, f in (("12SL", "12sl_features.csv"), ("Glasgow", "unig_features.csv"), ("ECGDeli", "ecgdeli_features.csv")):
    feat[name] = pd.read_csv(P + f, low_memory=False).set_index("ecg_id")

# quantity -> (NeuroKit2 column, PTB-XL+ column)
Q = {"heart rate (bpm)": ("gt_hr", "HR__Global"), "PR (ms)": ("gt_pr_ms", "PR_Int_Global"),
     "QRS (ms)": ("gt_qrs_ms", "QRS_Dur_Global"), "QT (ms)": ("gt_qt_ms", "QT_Int_Global"),
     "QTc Bazett (ms)": ("gt_qtc_ms", "QT_IntBazett_Global")}


def get(name, col):
    d = feat[name]
    if col not in d.columns:
        return pd.Series(np.nan, index=clean["ecg_id"])
    return d.reindex(clean["ecg_id"].values)[col].set_axis(clean["ecg_id"].values)


def summarize(a, b):
    m = a.notna() & b.notna()
    if m.sum() < 5:
        return None
    d = (a[m] - b[m])
    return dict(n=int(m.sum()), bias=d.mean(), mad=d.abs().median(), p90=d.abs().quantile(0.9),
                rho=pd.Series(a[m]).corr(pd.Series(b[m]), method="spearman"))


lines = ["# Our reference intervals vs PTB-XL+ algorithms (2026-11-04)\n",
         "50 recordings (clean-image rows of results_v2.csv). Difference = first minus second. bias = mean difference; "
         "MAD = median absolute difference; p90 = 90th percentile of the absolute difference; rho = Spearman correlation.\n",
         "Algorithms: Marquette 12SL and Glasgow (commercial, from a median beat) and ECGDeli (open). PTB-XL+ global values are in ms or bpm.\n"]
rows = []
for q, (nk_col, ptb_col) in Q.items():
    nk = pd.Series(clean[nk_col].values, index=clean["ecg_id"].values)
    for alg in feat:
        s = summarize(nk, get(alg, ptb_col))
        if s:
            rows.append({"quantity": q, "comparison": f"NeuroKit2 - {alg}", **s})
    for a, b in (("12SL", "Glasgow"), ("12SL", "ECGDeli"), ("Glasgow", "ECGDeli")):
        s = summarize(get(a, ptb_col), get(b, ptb_col))
        if s:
            rows.append({"quantity": q, "comparison": f"{a} - {b}", **s})
tab = pd.DataFrame(rows).round({"bias": 1, "mad": 1, "p90": 1, "rho": 2})
FENCE = "`" * 3
for q in Q:
    lines.append(f"## {q}\n" + FENCE + "\n" + tab[tab.quantity == q].drop(columns="quantity").to_string(index=False) + "\n" + FENCE + "\n")

# QTc with Fridericia, and the proportion of recordings called prolonged by each source
thr = np.where(clean["sex"] == "female", 460.0, 450.0)
nk_qt, nk_hr = clean["gt_qt_ms"].values, clean["gt_hr"].values
rows2 = [{"source": "NeuroKit2 Bazett (our reference)", "prolonged": int((clean["gt_qtc_ms"].values >= thr).sum())},
         {"source": "NeuroKit2 Fridericia", "prolonged": int(((nk_qt / np.cbrt(60 / nk_hr)) >= thr).sum())}]
for alg in feat:
    for col, label in (("QT_IntBazett_Global", "Bazett"), ("QT_IntFridericia_Global", "Fridericia")):
        v = get(alg, col)
        if v.notna().sum() > 40:
            rows2.append({"source": f"{alg} {label}", "prolonged": int((v.values >= thr).sum()), "n": int(v.notna().sum())})
lines.append("## Recordings called prolonged QTc (female >= 460 ms, male >= 450 ms), out of 50\n" + FENCE + "\n"
             + pd.DataFrame(rows2).to_string(index=False) + "\n" + FENCE + "\n")
text = "\n".join(lines)
print(text)
open("D:/Capstone Project/results/reference_vs_ptbxl_plus.md", "w", encoding="utf-8").write(text)
