"""RISK PILOT 3: verdict on the pooled out-of-fold predictions (rules: docs/plan/analysis_plan_changes.md, 2026-11-18 day). Run after section_RISK3_cv.py. Writes results/risk_pilot3/SECTION_RISK3.md and risk3_status.json.
Usage: demo\\.venv-gpu\\Scripts\\python.exe -I scripts/analysis/section_RISK3_verdict.py"""
import json
import os

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
OUT = os.path.join(ROOT, "results", "risk_pilot3") + os.sep
d = pd.read_csv(OUT + "oof.csv")
y, P, PA, LG = d.y.values.astype(int), d.p_cal.values, d.p_age.values, d.logit.values
rng = np.random.default_rng(2026)
pos, neg = np.flatnonzero(y == 1), np.flatnonzero(y == 0)
A, B, DV = [], [], []
for _ in range(1000):
    ii = np.concatenate([rng.choice(pos, len(pos)), rng.choice(neg, len(neg))])
    a, b = roc_auc_score(y[ii], P[ii]), roc_auc_score(y[ii], PA[ii])
    A.append(a), B.append(b), DV.append(a - b)
auc, auc_age = float(roc_auc_score(y, P)), float(roc_auc_score(y, PA))
ci = lambda v: (float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5)))  # noqa: E731
diff = auc - auc_age
dlo, dhi = ci(DV)
slope = float(LogisticRegression(C=1e6, max_iter=1000).fit(LG[:, None], y).coef_[0, 0])


def ece_q(p, y, bins=10):
    order = np.argsort(p)
    return float(sum(len(c) / len(p) * abs(p[c].mean() - y[c].mean()) for c in np.array_split(order, bins)))


ece = ece_q(P, y)
cat = np.where(P < 0.05, 0, np.where(P < 0.15, 1, 2))
rate = [float(y[cat == k].mean()) if (cat == k).any() else float("nan") for k in range(3)]
cnt = [int((cat == k).sum()) for k in range(3)]
mono = bool(all(np.isfinite(rate)) and rate[0] < rate[1] < rate[2])
ratio_ok = bool(mono and rate[0] > 0 and rate[2] >= 3 * rate[0])
per_fold = [float(roc_auc_score(g.y, g.logit)) for _, g in d.groupby("fold")]
st = dict(n=int(len(y)), events=int(y.sum()), auroc=auc, auroc_lo95=ci(A)[0], auroc_hi95=ci(A)[1], auroc_age_alone=auc_age, auroc_diff_vs_age=diff, auroc_diff_lo95=dlo, auroc_diff_hi95=dhi,
          cal_slope=slope, ece=ece, category_rates=rate, category_counts=cnt, per_fold_auroc=per_fold)
st.update(pass_discrimination=bool(auc >= 0.80 and ci(A)[0] > 0.75), pass_ecg_adds_value=bool(dlo > 0), pass_calibration=bool(0.8 <= slope <= 1.25 and ece <= 0.02), pass_categories=ratio_ok)
st["stage1_pass"] = bool(st["pass_discrimination"] and st["pass_ecg_adds_value"] and st["pass_calibration"] and st["pass_categories"])
st["shown_in_app"] = False          # stage 2 (transfer to pages and simulated photos) has not been run
json.dump(st, open(OUT + "risk3_status.json", "w"), indent=1)
md = ["# Risk pilot 3: five-fold cross-validation on all usable patients (5-year death, ECG + age)", "",
      "Rules written before the run: docs/plan/analysis_plan_changes.md (2026-11-18 day). Out-of-fold predictions of one run; NOT a blind test (the pilot-2 sealed-test patients are included).", "",
      f"Patients {st['n']}, events {st['events']}. Held-out AUROC per fold: " + ", ".join(f"{v:.3f}" for v in per_fold) + ".", "",
      "| Quantity | Value |", "|---|---|",
      f"| AUROC, ECG + age (95% interval) | {auc:.3f} ({ci(A)[0]:.3f} to {ci(A)[1]:.3f}) |",
      f"| AUROC, age alone | {auc_age:.3f} |",
      f"| Difference (ECG + age minus age alone), 95% interval | {diff:+.3f} ({dlo:+.3f} to {dhi:+.3f}) |",
      f"| Calibration slope / ECE | {slope:.2f} / {ece:.4f} |",
      "| Observed 5-year rate, Low / Moderate / High | " + " / ".join(f"{r * 100:.1f}% (n={c})" for r, c in zip(rate, cnt)) + " |", "",
      "## Verdict (stage 1)", "", "| Rule | Result |", "|---|---|",
      f"| AUROC at least 0.80, lower end above 0.75 | {st['pass_discrimination']} |",
      f"| ECG adds value: lower end of the paired difference above 0 | {st['pass_ecg_adds_value']} |",
      f"| Calibration slope 0.8 to 1.25 and ECE at most 0.02 | {st['pass_calibration']} |",
      f"| Observed rates increase across the categories and High at least 3 times Low | {st['pass_categories']} |",
      f"| **Stage 1 passed** | **{st['stage1_pass']}** |", "",
      "Stage 2 (transfer of the five fold models to drawn pages and simulated photos) has NOT been run. No percentage is shown in the app until it passes. Limits: not a blind test; clean 12-lead ECGs from one Brazilian telehealth cohort; no photos."]
open(OUT + "SECTION_RISK3.md", "w", encoding="utf-8").write("\n".join(md))
print("\n".join(md))
