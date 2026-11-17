"""Builds safeguard/model.json (run once). Rules: docs/plan/analysis_plan_changes.md, 2026-11-10 'Traffic-light safeguard'.
Training data: the simulated new 100 only (images with a reading; label = wrong HR > 5 bpm, cleaned measure, Sections J/K). No real-capture or own-photo data is used here.
Thresholds come from the out-of-fold scores (whole recordings held out, 5-fold x10), never from the data the model was fitted on."""
import json
import os
import sys
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
ROOT = "D:/Capstone Project/"
src = open(ROOT + "scripts/analysis/section_D2.py", encoding="utf-8").read().split("preds = {}")[0]
exec(compile(src, "section_D2_prefix", "exec"))          # te, OUT_COLS, sig_model, oof
sys.path.insert(0, ROOT + "safeguard")
import ecg_traffic_light as T

assert OUT_COLS == T.FEATURES, "feature order differs from the packaged tool"
K = pd.read_csv(ROOT + "results/analysis/sectionK_remeasured_sim.csv")
K["wrong_c"] = K.diff_clean > 5
sim = te.merge(K[["variant_id", "wrong_c", "dig_hr_clean"]], on="variant_id", how="left")
sim = sim[sim.dig_hr_clean.notna()].reset_index(drop=True)
ys = sim.wrong_c.astype(int).values
gs = sim.record.values
print(f"training: {len(sim)} images with a reading, {int(ys.sum())} wrong, {sim.record.nunique()} recordings")

# ---- fit the model once on all training images
pipe = sig_model().fit(sim[OUT_COLS], ys)
imp, sc, lr = pipe.steps[0][1], pipe.steps[1][1], pipe.steps[2][1]
# ---- out-of-fold scores -> thresholds
p = oof(sim[OUT_COLS], ys, gs, sig_model)
amber = float(np.quantile(p[ys == 1], 0.10))                       # >= 90% of wrong readings score at or above this
red = None
for t in np.unique(p):
    m = p >= t
    if ys[m].mean() >= 0.5:
        red = float(t)
        break
if red is None:
    red = float(np.quantile(p, 0.95))
    print("RED rule found no threshold: using the 95th percentile")
if red < amber:
    red = amber
print(f"amber threshold {amber:.4f}, red threshold {red:.4f}")
lights = np.where(p >= red, "RED", np.where(p >= amber, "AMBER", "GREEN"))
tab = pd.DataFrame({"light": lights, "wrong": ys}).groupby("light").agg(readings=("wrong", "size"), wrong=("wrong", "sum"))
tab["wrong_rate_%"] = (100 * tab.wrong / tab.readings).round(1)
print(tab.loc[[x for x in ("GREEN", "AMBER", "RED") if x in tab.index]].to_string())
# ---- reasons: 90th percentile of each feature among the RIGHT readings of the training set
right = sim[ys == 0]
p90 = {k: float(np.nanpercentile(right[k].astype(float), 90)) for k in ("rr_cv", "rr_max_ratio", "rr_min_ratio", "einthoven", "goldberger", "xlead_count_absdiff", "n_unreadable_leads")}
p90["rr_min_ratio"] = float(np.nanpercentile(right["rr_min_ratio"].astype(float), 10))          # small min ratio = an extra beat; flag below the 10th percentile
model = dict(features=OUT_COLS, impute_median=[float(x) for x in imp.statistics_], scaler_mean=[float(x) for x in sc.mean_], scaler_scale=[float(x) for x in sc.scale_],
             coef=[float(x) for x in lr.coef_[0]], intercept=float(lr.intercept_[0]), amber_threshold=amber, red_threshold=red, reason_p90=p90, detector_spread_note_bpm=15.0,
             trained_on="simulated new 100 (1,262 images with a reading, 113 wrong)", rules="docs/plan/analysis_plan_changes.md 2026-11-10",
             oof_light_table={k: dict(readings=int(v.readings), wrong=int(v.wrong)) for k, v in tab.iterrows()})
GUARD = [k for k in OUT_COLS if k != "amp_log"]
model["guard_features"] = GUARD
model["train_min"] = {k: float(np.nanmin(sim[k].astype(float))) for k in GUARD}
model["train_max"] = {k: float(np.nanmax(sim[k].astype(float))) for k in GUARD}
json.dump(model, open(ROOT + "safeguard/model.json", "w", encoding="utf-8"), indent=1)
# ---- the packaged numpy scorer must reproduce the sklearn probabilities
ps = np.array([T.score_from_features(dict(zip(OUT_COLS, r)), model) for r in sim[OUT_COLS].to_numpy(dtype=float)])
assert np.max(np.abs(ps - pipe.predict_proba(sim[OUT_COLS])[:, 1])) < 1e-9, "packaged scorer differs from sklearn"
print("packaged scorer == sklearn on all training rows. model.json written.")
