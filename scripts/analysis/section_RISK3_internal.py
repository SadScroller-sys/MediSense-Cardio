"""RISK PILOT 3, internal validation: calibration by decile, baselines, subgroups, decision curve. ONE run (rules: docs/plan/analysis_plan_changes.md, 2026-11-18 night, late).
Uses the out-of-fold predictions (results/risk_pilot3/oof.csv and oof_agepred.csv). INTERNAL validation only: same cohort, cross-validated. Refuses to run twice.
Writes results/risk_pilot3/SECTION_RISK3_INTERNAL.md, internal_status.json, fig_internal_validation.png.
Usage: demo\\.venv-gpu\\Scripts\\python.exe -I scripts/analysis/section_RISK3_internal.py"""
import json
import os

import matplotlib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
OUT = os.path.join(ROOT, "results", "risk_pilot3") + os.sep
if os.path.exists(OUT + "internal_status.json"):
    print("internal validation was already run once: results are in results/risk_pilot3/. Refusing to run twice.")
    raise SystemExit(1)
d = pd.read_csv(OUT + "oof.csv").merge(pd.read_csv(OUT + "oof_agepred.csv")[["patient_id", "p_pred", "age_pred"]], on="patient_id", how="left")
m = pd.read_csv(os.path.join(ROOT, "data", "code15", "risk2_meta.csv"), usecols=["patient_id", "is_male", "age"]).drop_duplicates("patient_id")
d = d.merge(m[["patient_id", "is_male"]], on="patient_id", how="left")
y = d.y.values.astype(int)
P = d.p_cal.values
rng = np.random.default_rng(2026)


def wilson(k, n, z=1.96):
    if n == 0:
        return (np.nan, np.nan)
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (c - h, c + h)


def boot_auc(yv, scores, n=1000):
    pos, neg = np.flatnonzero(yv == 1), np.flatnonzero(yv == 0)
    out = {k: [] for k in scores}
    for _ in range(n):
        ii = np.concatenate([rng.choice(pos, len(pos)), rng.choice(neg, len(neg))])
        for k, s in scores.items():
            out[k].append(roc_auc_score(yv[ii], s[ii]))
    return {k: (float(roc_auc_score(yv, scores[k])), float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))) for k, v in out.items()}, out


# ---- (1) calibration by decile
order = np.argsort(P)
dec = []
for i, idx in enumerate(np.array_split(order, 10), start=1):
    k, n = int(y[idx].sum()), len(idx)
    lo, hi = wilson(k, n)
    dec.append(dict(decile=i, n=n, predicted=float(P[idx].mean()), observed=k / n, lo=lo, hi=hi, within5=bool(lo - 0.05 <= P[idx].mean() <= hi + 0.05)))
D10 = pd.DataFrame(dec)
lg = np.log(np.clip(P, 1e-6, 1 - 1e-6) / (1 - np.clip(P, 1e-6, 1 - 1e-6)))
cal = LogisticRegression(C=1e6, max_iter=1000).fit(lg[:, None], y)
slope, intercept = float(cal.coef_[0, 0]), float(cal.intercept_[0])
ece = float(sum(len(c) / len(P) * abs(P[c].mean() - y[c].mean()) for c in np.array_split(order, 10)))
n_within = int(D10.within5.sum())

# ---- (2) baselines inside the same folds
age = d.age.values.astype(float)
sex = d.is_male.fillna(0).values.astype(float)
p_as = np.zeros(len(d))
for k in range(5):
    tr, te = d.fold.values != k, d.fold.values == k
    lr = LogisticRegression(C=1e6, max_iter=1000).fit(np.c_[age[tr], sex[tr]], y[tr])
    p_as[te] = lr.predict_proba(np.c_[age[te], sex[te]])[:, 1]
res, bs = boot_auc(y, {"ECG + age": P, "Age alone": d.p_age.values, "Age + sex": p_as})
diff_as = np.array(bs["ECG + age"]) - np.array(bs["Age + sex"])
dlo, dhi = float(np.percentile(diff_as, 2.5)), float(np.percentile(diff_as, 97.5))
brier = {k: float(brier_score_loss(y, v)) for k, v in (("ECG + age", P), ("Age alone", d.p_age.values), ("Age + sex", p_as))}

# ---- (3) subgroups
sub_rows = []
for name, mk in (("Women", sex == 0), ("Men", sex == 1), ("Age under 50", age < 50), ("Age 50 to 69", (age >= 50) & (age < 70)), ("Age 70 and over", age >= 70)):
    yy = y[mk]
    if yy.sum() < 5 or (yy == 0).sum() < 5:
        continue
    r, _ = boot_auc(yy, {"a": P[mk], "b": p_as[mk]}, n=500)
    sub_rows.append(dict(group=name, n=int(mk.sum()), events=int(yy.sum()), auc_ecg_age=r["a"][0], lo=r["a"][1], hi=r["a"][2], auc_age_sex=r["b"][0], too_small=bool(yy.sum() < 100), ecg_higher=bool(r["a"][0] > r["b"][0])))
S = pd.DataFrame(sub_rows)
sub_target = bool(S[~S.too_small].ecg_higher.all()) if len(S[~S.too_small]) else False

# ---- (4) decision curve
prev = float(y.mean())
dc = []
for t in (0.05, 0.10, 0.15):
    sel = P >= t
    nb = (np.sum(sel & (y == 1)) / len(y)) - (np.sum(sel & (y == 0)) / len(y)) * t / (1 - t)
    nb_all = prev - (1 - prev) * t / (1 - t)
    nb_as = (np.sum((p_as >= t) & (y == 1)) / len(y)) - (np.sum((p_as >= t) & (y == 0)) / len(y)) * t / (1 - t)
    dc.append(dict(threshold=t, nb_ecg_age=float(nb), nb_age_sex=float(nb_as), nb_treat_all=float(nb_all)))
DC = pd.DataFrame(dc)

# ---- version with the estimated age
est = d.p_pred.values
auc_est = float(roc_auc_score(y, est))
lg2 = np.log(np.clip(est, 1e-6, 1 - 1e-6) / (1 - np.clip(est, 1e-6, 1 - 1e-6)))
slope_est = float(LogisticRegression(C=1e6, max_iter=1000).fit(lg2[:, None], y).coef_[0, 0])
ece_est = float(sum(len(c) / len(est) * abs(est[c].mean() - y[c].mean()) for c in np.array_split(np.argsort(est), 10)))

# ---- figure
fig, ax = plt.subplots(1, 2, figsize=(11, 4.6))
ax[0].plot([0, 0.8], [0, 0.8], "--", color="#8a8984", label="perfect")
ax[0].errorbar(D10.predicted, D10.observed, yerr=[D10.observed - D10.lo, D10.hi - D10.observed], fmt="o", color="#2a78d6", capsize=3, label="decile of predicted risk")
ax[0].set_xlabel("Predicted 5-year chance of death (calibrated ECG + age)")
ax[0].set_ylabel("Observed 5-year rate (95% interval)")
ax[0].set_title(f"Calibration, {n_within} of 10 deciles within 5 points", fontsize=11)
ax[0].legend(loc="upper left")
th = np.linspace(0.02, 0.4, 60)
nb_e = [(np.sum((P >= t) & (y == 1)) / len(y)) - (np.sum((P >= t) & (y == 0)) / len(y)) * t / (1 - t) for t in th]
nb_a = [(np.sum((p_as >= t) & (y == 1)) / len(y)) - (np.sum((p_as >= t) & (y == 0)) / len(y)) * t / (1 - t) for t in th]
ax[1].plot(th, nb_e, color="#2a78d6", label="ECG + age")
ax[1].plot(th, nb_a, color="#eb6834", label="age + sex")
ax[1].plot(th, [prev - (1 - prev) * t / (1 - t) for t in th], color="#8a8984", label="treat all")
ax[1].axhline(0, color="black", lw=0.8, label="treat none")
ax[1].set_ylim(-0.02, 0.17)
ax[1].set_xlabel("Threshold (chance of death)")
ax[1].set_ylabel("Net benefit")
ax[1].set_title("Decision curve", fontsize=11)
ax[1].legend()
fig.suptitle("Risk pilot 3: internal validation (cross-validated, same cohort, 19,048 patients). Not external validation.", fontsize=10)
fig.tight_layout()
fig.savefig(OUT + "fig_internal_validation.png", dpi=150)

st = dict(n=int(len(y)), events=int(y.sum()), calibration_slope=slope, calibration_intercept=intercept, ece=ece, deciles_within_5_points=n_within, auroc=res, auroc_diff_vs_age_sex=[float(res["ECG + age"][0] - res["Age + sex"][0]), dlo, dhi],
          brier=brier, subgroups_ecg_higher_than_age_sex=sub_target, estimated_age_version=dict(auroc=auc_est, slope=slope_est, ece=ece_est),
          target_calibration=bool(n_within >= 8), target_subgroups=sub_target)
json.dump(st, open(OUT + "internal_status.json", "w"), indent=1)
md = ["# Risk pilot 3: internal validation (cross-validated, same cohort)", "",
      "Rules written before the run: docs/plan/analysis_plan_changes.md (2026-11-18 night, late). INTERNAL validation only: the same 19,048 patients, each predicted by models that never saw them. It is not external validation.", "",
      "## 1. Calibration by decile of predicted risk", "", "| Decile | n | Predicted | Observed (95% interval) | Within 5 points |", "|---|---|---|---|---|"]
for _, r in D10.iterrows():
    md.append(f"| {int(r.decile)} | {int(r.n)} | {r.predicted * 100:.1f}% | {r.observed * 100:.1f}% ({r.lo * 100:.1f} to {r.hi * 100:.1f}) | {'yes' if r.within5 else 'no'} |")
md += ["", f"Slope {slope:.2f}, intercept {intercept:+.2f}, ECE {ece:.4f}. Deciles within 5 points: {n_within} of 10 (target 8: {'met' if n_within >= 8 else 'NOT met'}).",
       f"With the age estimated from the ECG: AUROC {auc_est:.3f}, slope {slope_est:.2f}, ECE {ece_est:.4f}.", "",
       "## 2. Against simple baselines", "", "| Model | AUROC (95% interval) | Brier |", "|---|---|---|"]
for k in ("ECG + age", "Age + sex", "Age alone"):
    a, lo, hi = res[k]
    md.append(f"| {k} | {a:.3f} ({lo:.3f} to {hi:.3f}) | {brier[k]:.4f} |")
md += ["", f"ECG + age minus age + sex: {st['auroc_diff_vs_age_sex'][0]:+.3f} (95% interval {dlo:+.3f} to {dhi:+.3f}).", "", "## 3. Subgroups", "", "| Group | n | Events | AUROC ECG + age (95% interval) | AUROC age + sex | Note |", "|---|---|---|---|---|---|"]
for _, r in S.iterrows():
    md.append(f"| {r.group} | {int(r.n)} | {int(r.events)} | {r.auc_ecg_age:.3f} ({r.lo:.3f} to {r.hi:.3f}) | {r.auc_age_sex:.3f} | {'too few events' if r.too_small else ('ECG + age higher' if r.ecg_higher else 'ECG + age NOT higher')} |")
md += ["", f"Target (ECG + age higher than age + sex in every subgroup with at least 100 events): {'met' if sub_target else 'NOT met'}.", "", "## 4. Decision curve (net benefit)", "", "| Threshold | ECG + age | Age + sex | Treat all |", "|---|---|---|---|"]
for _, r in DC.iterrows():
    md.append(f"| {r.threshold * 100:.0f} in 100 | {r.nb_ecg_age:.4f} | {r.nb_age_sex:.4f} | {r.nb_treat_all:.4f} |")
md += ["", "Limits: same cohort (one Brazilian telehealth network), clean ECGs, all-cause death, only people with a complete five-year follow-up, no photographs. External validation on a fresh cohort is future work.", "", "![internal validation](fig_internal_validation.png)"]
open(OUT + "SECTION_RISK3_INTERNAL.md", "w", encoding="utf-8").write("\n".join(md))
print("\n".join(md))
