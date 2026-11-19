"""Heart-attack (MI) pattern percentage from photos, SECOND ATTEMPT: fit a calibration on sets N + P + Q + R, test ONCE on the fresh random set S (rules: docs/plan/analysis_plan_changes.md, 2026-11-18 'SET S').
Score = the MI value of the app's own findings() on the digitised simulated phone photo; label = PTB-XL superclass MI.
Writes results/health/MI_photo_calibration_v2.json, SECTION_MI_PHOTOCAL2.md, fig_MI_photocal2.png. Refuses to run twice.
Usage: demo\\.venv-gpu\\Scripts\\python.exe -I scripts/analysis/section_MI_photocal2.py"""
import glob
import json
import os
import sys

import matplotlib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "demo"))
from health import assess as A  # noqa: E402
from health import data as D  # noqa: E402

OUT = ROOT + "/results/health/"
if os.path.exists(OUT + "MI_photo_calibration_v2.json"):
    print("the second MI photo calibration was already run once: results are in results/health/. Refusing to run twice.")
    raise SystemExit(1)
if not os.path.exists(ROOT + "/results/paper_s/S_pictures_done.flag"):
    print("set S is not fully digitised yet (rule: test only when the set is complete).")
    raise SystemExit(1)
Y = D.load_db()
Y = Y[1] if isinstance(Y, tuple) else Y
prev_pop = float(Y["MI"].mean())
R = ROOT + "/results/"
SETS = {"N": ("paper_n/selected_N.csv", "paper_n/N_sim/dig_v2"), "P": ("paper_p/selected_P.csv", "paper_p/P_sim/dig_v2"), "Q": ("paper_q/selected_Q.csv", "paper_q/P_sim/dig_v2"),
        "R": ("paper_r/selected_R.csv", "paper_r/P_sim/dig_v2"), "S": ("paper_s/selected_S.csv", "paper_s/P_sim/dig_v2")}
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
fit = d[d.set.isin(["N", "P", "Q", "R"])]
test = d[d.set == "S"].copy()
cal = LogisticRegression(C=1e6, max_iter=1000).fit(lg(fit.score.values)[:, None], fit.y.values, sample_weight=fit.w.values)
a_, b_ = float(cal.coef_[0, 0]), float(cal.intercept_[0])
test["p"] = 1 / (1 + np.exp(-(a_ * lg(test.score.values) + b_)))
y = test.y.values
prev_s = float(y.mean())


def ece_eq(p, y, bins=5):
    o = np.argsort(p)
    return float(sum(len(c) / len(p) * abs(p[c].mean() - y[c].mean()) for c in np.array_split(o, bins)))


slope = float(LogisticRegression(C=1e6, max_iter=1000).fit(lg(test.p.values)[:, None], y).coef_[0, 0])
ece = ece_eq(test.p.values, y)
b_cal, b_raw, b_prev = float(np.mean((test.p.values - y) ** 2)), float(np.mean((test.score.values - y) ** 2)), float(np.mean((prev_s - y) ** 2))
auc = float(roc_auc_score(y, test.score.values))
thr = 0.279
sens = float(np.mean(test.score.values[y == 1] >= thr))
spec = float(np.mean(test.score.values[y == 0] < thr))
st = dict(prev_population=prev_pop, prev_set_S=prev_s, a=a_, b=b_, n_fit=int(len(fit)), n_test=int(len(test)), positives_test=int(y.sum()), auroc_test=auc, sens_at_threshold=sens, spec_at_threshold=spec,
          slope=slope, ece=ece, brier_calibrated=b_cal, brier_uncalibrated=b_raw, brier_prevalence_only=b_prev,
          pass_slope=bool(0.8 <= slope <= 1.25), pass_ece=bool(ece <= 0.05), pass_brier=bool(b_cal < b_raw and b_cal < b_prev))
st["show_percentage"] = bool(st["pass_slope"] and st["pass_ece"] and st["pass_brier"])
json.dump(st, open(OUT + "MI_photo_calibration_v2.json", "w"), indent=1)
o = np.argsort(test.p.values)
px = [test.p.values[c].mean() for c in np.array_split(o, 5)]
py = [y[c].mean() for c in np.array_split(o, 5)]
fig, ax = plt.subplots(figsize=(4.8, 4.4))
ax.plot([0, 1], [0, 1], "--", color="#8a8984")
ax.plot(px, py, "o-", color="#2a78d6")
ax.set_xlabel("Predicted chance of the pattern (calibrated on N + P + Q + R)")
ax.set_ylabel("Observed share with the pattern, set S")
ax.set_title(f"Heart-attack pattern, fresh set S: slope {slope:.2f}, ECE {ece:.3f}", fontsize=9)
fig.tight_layout()
fig.savefig(OUT + "fig_MI_photocal2.png", dpi=150)
md = ["# Heart-attack pattern percentage from photos: SECOND attempt, fresh random set S (tested once)", "",
      "Rules written before the set was selected: docs/plan/analysis_plan_changes.md (2026-11-18 night, late, 'SET S'). Second attempt after a failure (first attempt: ECE 0.061 against 0.05).", "",
      f"Fit: {len(fit)} simulated photos (sets N, P, Q, R; {int(fit.y.sum())} positives), weighted to the PTB-XL prevalence {prev_pop * 100:.1f}%. Test: {len(test)} photos of set S ({int(y.sum())} positives, {prev_s * 100:.1f}%).",
      f"Calibration (frozen): p = sigmoid({a_:.3f} * logit(score) {b_:+.3f}).", "", "| Quantity (set S) | Value | Rule |", "|---|---|---|",
      f"| Calibration slope | {slope:.2f} | 0.8 to 1.25: {'pass' if st['pass_slope'] else 'FAIL'} |", f"| Expected calibration error (5 bins) | {ece:.3f} | at most 0.05: {'pass' if st['pass_ece'] else 'FAIL'} |",
      f"| Brier, calibrated / uncalibrated / prevalence only | {b_cal:.3f} / {b_raw:.3f} / {b_prev:.3f} | calibrated below both: {'pass' if st['pass_brier'] else 'FAIL'} |",
      f"| AUROC of the score | {auc:.3f} | descriptive |", f"| Sensitivity / specificity at the app threshold 0.279 | {sens * 100:.0f}% / {spec * 100:.0f}% | descriptive |", "",
      f"**Show a percentage in the app: {st['show_percentage']}**", "", "Limits: simulated phone photos of dataset recordings, one drawing program, one digitiser; second attempt (a lucky pass is more likely); not validated on real phone photos.", "", "![reliability](fig_MI_photocal2.png)"]
open(OUT + "SECTION_MI_PHOTOCAL2.md", "w", encoding="utf-8").write("\n".join(md))
print("\n".join(md))
