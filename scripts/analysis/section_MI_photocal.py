"""Heart-attack (MI) pattern percentage from photos: fit a calibration on sets N + P, test ONCE on sets Q + R (rules: docs/plan/analysis_plan_changes.md, 2026-11-18 night, late).
Score = the MI value of the app's own findings() on the digitised simulated phone photo; label = PTB-XL superclass MI. Weighted to the PTB-XL population prevalence.
Writes results/health/MI_photo_calibration.json, SECTION_MI_PHOTOCAL.md, fig_MI_photocal.png. Refuses to run twice.
Usage: demo\\.venv-gpu\\Scripts\\python.exe -I scripts/analysis/section_MI_photocal.py"""
import glob
import json
import os
import sys

import matplotlib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "demo"))
from health import assess as A  # noqa: E402
from health import data as D  # noqa: E402

OUT = ROOT + "/results/health/"
if os.path.exists(OUT + "MI_photo_calibration.json"):
    print("the MI photo calibration was already run once: results are in results/health/. Refusing to run twice.")
    raise SystemExit(1)
Y = D.load_db()
if isinstance(Y, tuple):
    Y = Y[1]
prev_pop = float(Y["MI"].mean())
R = ROOT + "/results/"
SETS = {"N": ("paper_n/selected_N.csv", "paper_n/N_sim/dig_v2"), "P": ("paper_p/selected_P.csv", "paper_p/P_sim/dig_v2"), "Q": ("paper_q/selected_Q.csv", "paper_q/P_sim/dig_v2"), "R": ("paper_r/selected_R.csv", "paper_r/P_sim/dig_v2")}
rows = []
for k, (csv, d) in SETS.items():
    s = pd.read_csv(R + csv).set_index("page")
    for f in sorted(glob.glob(R + d + f"/{k}*.npz")):
        pg = os.path.basename(f)[:4]
        if pg not in s.index:
            continue
        leads = {kk: np.asarray(v, float) for kk, v in np.load(f).items()}
        fl, _ = A.findings(leads, "GREEN", True)
        mi = next((x for x in fl if x["cls"] == "MI"), None)
        if mi is None or mi.get("p_internal") is None or mi["state"] != "supported":
            continue
        rows.append(dict(set=k, page=pg, ecg_id=int(s.loc[pg, "ecg_id"]), score=float(mi["p_internal"]), y=int(Y.loc[int(s.loc[pg, "ecg_id"]), "MI"])))
d = pd.DataFrame(rows)
print(d.groupby("set").agg(n=("y", "size"), positives=("y", "sum")), flush=True)
d["prev_set"] = d.groupby("set").y.transform("mean")
d["w"] = np.where(d.y == 1, prev_pop / d.prev_set, (1 - prev_pop) / (1 - d.prev_set))
lg = lambda p: np.log(np.clip(p, 1e-6, 1 - 1e-6) / (1 - np.clip(p, 1e-6, 1 - 1e-6)))  # noqa: E731
fit = d[d.set.isin(["N", "P"])]
test = d[d.set.isin(["Q", "R"])].copy()
cal = LogisticRegression(C=1e6, max_iter=1000).fit(lg(fit.score.values)[:, None], fit.y.values, sample_weight=fit.w.values)
a_, b_ = float(cal.coef_[0, 0]), float(cal.intercept_[0])
test["p"] = 1 / (1 + np.exp(-(a_ * lg(test.score.values) + b_)))
y, w = test.y.values, test.w.values


def ece_w(p, y, w, bins=5):
    o = np.argsort(p)
    cw = np.cumsum(w[o]) / w.sum()
    out = 0.0
    for i in range(bins):
        m = (cw > i / bins) & (cw <= (i + 1) / bins + 1e-12)
        idx = o[m]
        if len(idx):
            out += w[idx].sum() / w.sum() * abs(np.average(p[idx], weights=w[idx]) - np.average(y[idx], weights=w[idx]))
    return float(out)


slope = float(LogisticRegression(C=1e6, max_iter=1000).fit(lg(test.p.values)[:, None], y, sample_weight=w).coef_[0, 0])
ece = ece_w(test.p.values, y, w)
brier_cal = float(np.average((test.p.values - y) ** 2, weights=w))
brier_raw = float(np.average((test.score.values - y) ** 2, weights=w))
brier_prev = float(np.average((prev_pop - y) ** 2, weights=w))
auc = float(roc_auc_score(y, test.score.values))
st = dict(prev_population=prev_pop, a=a_, b=b_, n_fit=int(len(fit)), n_test=int(len(test)), positives_test=int(y.sum()), auroc_test=auc, weighted_slope=slope, weighted_ece=ece, brier_calibrated=brier_cal, brier_uncalibrated=brier_raw,
          brier_prevalence_only=brier_prev, pass_slope=bool(0.8 <= slope <= 1.25), pass_ece=bool(ece <= 0.05), pass_brier=bool(brier_cal < brier_raw))
st["show_percentage"] = bool(st["pass_slope"] and st["pass_ece"] and st["pass_brier"])
json.dump(st, open(OUT + "MI_photo_calibration.json", "w"), indent=1)
# reliability figure (weighted bins)
o = np.argsort(test.p.values)
cw = np.cumsum(w[o]) / w.sum()
px, py = [], []
for i in range(5):
    idx = o[(cw > i / 5) & (cw <= (i + 1) / 5 + 1e-12)]
    if len(idx):
        px.append(np.average(test.p.values[idx], weights=w[idx]))
        py.append(np.average(y[idx], weights=w[idx]))
fig, ax = plt.subplots(figsize=(4.8, 4.4))
ax.plot([0, 1], [0, 1], "--", color="#8a8984")
ax.plot(px, py, "o-", color="#2a78d6")
ax.set_xlabel("Predicted chance of the pattern (calibrated on N + P)")
ax.set_ylabel("Observed share with the pattern (weighted)")
ax.set_title(f"Heart-attack pattern, test sets Q + R: slope {slope:.2f}, ECE {ece:.3f}", fontsize=9)
fig.tight_layout()
fig.savefig(OUT + "fig_MI_photocal.png", dpi=150)
md = ["# Heart-attack pattern percentage from photos: calibration test (sets Q + R, tested once)", "",
      "Rules written before the run: docs/plan/analysis_plan_changes.md (2026-11-18 night, late). Simulated phone photos of PTB-XL fold-10 recordings; weights represent the PTB-XL population.", "",
      f"Population prevalence of the MI pattern in PTB-XL: {prev_pop * 100:.1f}%. Fit set N + P: {len(fit)} pictures ({int(fit.y.sum())} positives). Test set Q + R: {len(test)} pictures ({int(y.sum())} positives).",
      f"Calibration (frozen): p = sigmoid({a_:.3f} * logit(score) + {b_:+.3f}).", "", "| Quantity (test, weighted) | Value | Rule |", "|---|---|---|",
      f"| Calibration slope | {slope:.2f} | 0.8 to 1.25: {'pass' if st['pass_slope'] else 'FAIL'} |", f"| Expected calibration error (5 bins) | {ece:.3f} | at most 0.05: {'pass' if st['pass_ece'] else 'FAIL'} |",
      f"| Brier score, calibrated / uncalibrated / prevalence only | {brier_cal:.3f} / {brier_raw:.3f} / {brier_prev:.3f} | calibrated below uncalibrated: {'pass' if st['pass_brier'] else 'FAIL'} |",
      f"| AUROC of the score on the test set (unweighted) | {auc:.3f} | descriptive |", "", f"**Show a percentage in the app: {st['show_percentage']}**", "",
      "Limits: simulated phone photos of dataset recordings, one drawing program, one digitiser; sets are enriched in some patterns and the weights are a rough correction; 280 test pictures; not validated on real phone photos.", "", "![reliability](fig_MI_photocal.png)"]
open(OUT + "SECTION_MI_PHOTOCAL.md", "w", encoding="utf-8").write("\n".join(md))
print("\n".join(md))
