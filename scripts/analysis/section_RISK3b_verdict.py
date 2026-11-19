"""RISK PILOT 3b: verdict (rules: docs/plan/analysis_plan_changes.md, 2026-11-18 evening). Run after section_RISK3b_age_from_ecg.py.
Writes results/risk_pilot3/SECTION_RISK3B.md and risk3b_status.json.
Usage: demo\\.venv-gpu\\Scripts\\python.exe -I scripts/analysis/section_RISK3b_verdict.py"""
import json
import os

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
OUT = os.path.join(ROOT, "results", "risk_pilot3") + os.sep
d = pd.read_csv(OUT + "oof_agepred.csv")
t = pd.read_csv(OUT + "oof.csv")[["patient_id", "p_cal", "p_age"]]
d = d.merge(t, on="patient_id", how="left")
y = d.y.values.astype(int)
mae = float(np.mean(np.abs(d.age_pred - d.age)))
corr = float(np.corrcoef(d.age_pred, d.age)[0, 1])
bias = float(np.mean(d.age_pred - d.age))
auc_pred, auc_true, auc_agepred = float(roc_auc_score(y, d.p_pred)), float(roc_auc_score(y, d.p_cal)), float(roc_auc_score(y, d.age_pred))
rng = np.random.default_rng(2026)
pos, neg = np.flatnonzero(y == 1), np.flatnonzero(y == 0)
B = []
for _ in range(1000):
    ii = np.concatenate([rng.choice(pos, len(pos)), rng.choice(neg, len(neg))])
    B.append(roc_auc_score(y[ii], d.p_pred.values[ii]))
lo, hi = float(np.percentile(B, 2.5)), float(np.percentile(B, 97.5))
p = np.clip(d.p_pred.values, 1e-6, 1 - 1e-6)
slope_platt = float(LogisticRegression(C=1e6, max_iter=1000).fit(np.log(p / (1 - p))[:, None], y).coef_[0, 0])
cat = np.where(d.p_pred < 0.05, 0, np.where(d.p_pred < 0.15, 1, 2))
rate = [float(y[cat == k].mean()) if (cat == k).any() else float("nan") for k in range(3)]
cnt = [int((cat == k).sum()) for k in range(3)]
st = dict(n=int(len(d)), events=int(y.sum()), age_mae=mae, age_corr=corr, age_bias=bias, auroc_est_age=auc_pred, auroc_est_age_lo95=lo, auroc_est_age_hi95=hi, auroc_true_age=auc_true,
          auroc_age_pred_alone=auc_agepred, slope_after_platt=slope_platt, category_rates=rate, category_counts=cnt,
          pass_age_error=bool(mae <= 10.0), pass_auroc=bool(auc_pred >= 0.75 and lo > 0.72))
st["use_in_app"] = bool(st["pass_age_error"] and st["pass_auroc"])
json.dump(st, open(OUT + "risk3b_status.json", "w"), indent=1)
md = ["# Risk pilot 3b: risk with the age estimated from the ECG (5-fold, out-of-fold)", "",
      "Rules written before the run: docs/plan/analysis_plan_changes.md (2026-11-18 evening). Same limits as pilot 3: not a blind test, clean ECGs, one cohort, no photos.", "",
      f"Patients {st['n']}, events {st['events']}.", "", "| Quantity | Value |", "|---|---|",
      f"| Age error of the ECG-estimated age (mean absolute) | {mae:.2f} years (bias {bias:+.2f}, correlation {corr:.3f}) |",
      f"| AUROC of the risk with the ESTIMATED age (95% interval) | {auc_pred:.3f} ({lo:.3f} to {hi:.3f}) |",
      f"| AUROC of the risk with the TRUE age (pilot 3) | {auc_true:.3f} |",
      f"| AUROC of the estimated age alone | {auc_agepred:.3f} |",
      f"| Calibration slope after Platt scaling (descriptive) | {slope_platt:.2f} |",
      "| Observed 5-year rate, lower / middle / higher group | " + " / ".join(f"{r * 100:.1f}% (n={c})" for r, c in zip(rate, cnt)) + " |", "",
      "## Verdict (rules for using it in the app)", "", "| Rule | Result |", "|---|---|",
      f"| Mean absolute age error at most 10 years | {st['pass_age_error']} |",
      f"| AUROC with the estimated age at least 0.75 and lower end above 0.72 | {st['pass_auroc']} |",
      f"| **Use the estimated age in the app when no age is typed** | **{st['use_in_app']}** |"]
open(OUT + "SECTION_RISK3B.md", "w", encoding="utf-8").write("\n".join(md))
print("\n".join(md))
