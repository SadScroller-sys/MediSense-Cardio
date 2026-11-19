"""ROC lines of the two patterns the app shows on photos (heart-attack pattern, ST/T-wave change), on the 966 simulated phone photos of sets N, P, Q, R and S (descriptive; not a new test).
x = wrongly flagged (in 100 photos without the pattern), y = found (in 100 photos with the pattern); the dot is the app's threshold. Score = the app's own findings() value (network 2); labels = PTB-XL superclass.
Writes results/health/roc_photos.csv and fig_roc_photos.png (copied to demo/assets by the caller).
Usage: demo\\.venv-gpu\\Scripts\\python.exe -I scripts/analysis/make_roc_photos.py"""
import glob
import json
import os
import sys

import matplotlib
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, roc_curve

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "demo"))
from health import assess as A  # noqa: E402
from health import data as D  # noqa: E402

OUT = ROOT + "/results/health/"
Y = D.load_db()
Y = Y[1] if isinstance(Y, tuple) else Y
R = ROOT + "/results/"
SETS = {"N": ("paper_n/selected_N.csv", "paper_n/N_sim/dig_v2"), "P": ("paper_p/selected_P.csv", "paper_p/P_sim/dig_v2"), "Q": ("paper_q/selected_Q.csv", "paper_q/P_sim/dig_v2"),
        "R": ("paper_r/selected_R.csv", "paper_r/P_sim/dig_v2"), "S": ("paper_s/selected_S.csv", "paper_s/P_sim/dig_v2")}
thr = {c: json.load(open(R + "health/findings_status_v3.json", encoding="utf-8"))["classes"][c]["threshold"] for c in ("MI", "STTC")}
rows = []
for k, (csv, d) in SETS.items():
    s = pd.read_csv(R + csv).set_index("page")
    for f in sorted(glob.glob(R + d + f"/{k}*.npz")):
        pg = os.path.basename(f)[:4]
        if pg not in s.index:
            continue
        leads = {kk: np.asarray(v, float) for kk, v in np.load(f).items()}
        fl, _ = A.findings(leads, "GREEN", True)
        row = dict(set=k, page=pg, ecg_id=int(s.loc[pg, "ecg_id"]))
        for c in ("MI", "STTC"):
            x = next((q for q in fl if q["cls"] == c and q["state"] == "supported"), None)
            row[c + "_score"] = float(x["p_internal"]) if x and x.get("p_internal") is not None else np.nan
            row[c + "_y"] = int(Y.loc[row["ecg_id"], c])
        rows.append(row)
d = pd.DataFrame(rows)
d.to_csv(OUT + "roc_photos.csv", index=False)
print("pictures:", len(d), "| MI positives", int(d.MI_y.sum()), "| STTC positives", int(d.STTC_y.sum()), flush=True)
fig, ax = plt.subplots(figsize=(5.4, 5.0))
ax.plot([0, 100], [0, 100], "--", color="#8a8984", label="guessing")
for c, col, nm in (("MI", "#eb6834", "Heart-attack pattern"), ("STTC", "#2a78d6", "ST/T-wave change")):
    m = np.isfinite(d[c + "_score"])
    y, s = d.loc[m, c + "_y"].values, d.loc[m, c + "_score"].values
    fpr, tpr, _ = roc_curve(y, s)
    auc = roc_auc_score(y, s)
    ax.plot(fpr * 100, tpr * 100, color=col, lw=2.2, label=f"{nm}: AUROC {auc:.2f}")
    sens, spec = float(np.mean(s[y == 1] >= thr[c])), float(np.mean(s[y == 0] < thr[c]))
    ax.plot([(1 - spec) * 100], [sens * 100], "o", color=col, ms=8, mec="white")
    ax.annotate(f"app threshold: found {sens * 100:.0f}, flagged {(1 - spec) * 100:.0f}", ((1 - spec) * 100 + 2, sens * 100 - 6 if c == "MI" else sens * 100 + 5), fontsize=7.5, color=col)
    print(c, f"AUROC {auc:.3f}", f"sens {sens:.2f} spec {spec:.2f}", flush=True)
ax.set_xlabel("Wrongly flagged (in 100 photos without the pattern)")
ax.set_ylabel("Found (in 100 photos with the pattern)")
ax.set_title(f"ROC lines on {len(d)} simulated phone photos (sets N, P, Q, R, S)", fontsize=9)
ax.legend(loc="lower right", fontsize=8)
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
fig.tight_layout()
fig.savefig(OUT + "fig_roc_photos.png", dpi=150)
print("saved")
