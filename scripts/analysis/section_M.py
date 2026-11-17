"""Section M (EXPLORATORY; rules fixed beforehand in docs/plan/analysis_plan_changes.md 2026-11-08): does adding detector-agreement features improve the output check?
OUT = 15 output features; OUT+DET = OUT + 5 detector-agreement features. Labels: cleaned wrong HR > 5 bpm (Sections J, K).
Writes results/analysis/sectionM_*.csv and SECTION_M.md."""
import warnings

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

warnings.filterwarnings("ignore")
src = open("D:/Capstone Project/scripts/analysis/section_D2.py", encoding="utf-8").read().split("preds = {}")[0]
exec(compile(src, "section_D2_prefix", "exec"))          # te, y, OUT_COLS, X_COLS, sig_model, auc_ci, oof
ROOT = "D:/Capstone Project/"
OUT = ROOT + "results/analysis/"
DET = ["det_spread", "det_std", "det_n_agree", "det_nkclean_vs_pt", "det_n_missing"]
M = pd.read_csv(OUT + "sectionM_detector_features.csv")


def md_table(t):
    head = "| " + " | ".join(map(str, t.columns)) + " |\n|" + "---|" * len(t.columns) + "\n"
    return head + "\n".join("| " + " | ".join(str(z) for z in r) + " |" for r in t.itertuples(index=False))


def fmt(a, ci):
    return f"{a:.3f} ({ci[0]:.2f} to {ci[1]:.2f})"


def diff_ci(yy, p1, p2, groups, B=2000, seed=3):
    r = np.random.RandomState(seed)
    recs = np.unique(groups)
    idx = {g: np.where(groups == g)[0] for g in recs}
    v = []
    for _ in range(B):
        ii = np.concatenate([idx[g] for g in r.choice(recs, len(recs), replace=True)])
        if yy[ii].min() == yy[ii].max():
            continue
        v.append(roc_auc_score(yy[ii], p2[ii]) - roc_auc_score(yy[ii], p1[ii]))
    d0 = roc_auc_score(yy, p2) - roc_auc_score(yy, p1)
    return d0, np.percentile(v, [2.5, 97.5])


# ---------------------------------------------------------------- simulated, cleaned labels
K = pd.read_csv(OUT + "sectionK_remeasured_sim.csv")
K["wrong_c"] = K.diff_clean > 5
sim = te.merge(K[["variant_id", "wrong_c", "dig_hr_clean"]], on="variant_id", how="left").merge(M, on="variant_id", how="left").reset_index(drop=True)
sim = sim[sim.dig_hr_clean.notna()].reset_index(drop=True)
assert sim[DET].notna().any(axis=1).all()
ys = sim.wrong_c.astype(int).values
gs = sim.record.values
SETS = {"OUT (15 output features)": OUT_COLS, "OUT + DET (+5 detector-agreement)": OUT_COLS + DET, "DET alone (5 features)": DET}
pred = {k: oof(sim[c], ys, gs, sig_model) for k, c in SETS.items()}
rows = []
for k, p in pred.items():
    a, ci = auc_ci(ys, p, gs, B=1000)
    r = dict(model=k, overall_auc=fmt(a, ci))
    for ax, lv in (("resolution", 5), ("blur", 5)):
        mk = ((sim.axis == ax) & (sim.level == lv)).values
        aw, cw = auc_ci(ys[mk], p[mk], gs[mk], B=1000)
        r[f"within {ax} level {lv}"] = fmt(aw, cw)
    rows.append(r)
sim_tab = pd.DataFrame(rows)
simw = {}
for ax, lv in (("resolution", 5), ("blur", 5)):
    mk = ((sim.axis == ax) & (sim.level == lv)).values
    simw[(ax, lv)] = (roc_auc_score(ys[mk], pred["OUT (15 output features)"][mk]), roc_auc_score(ys[mk], pred["OUT + DET (+5 detector-agreement)"][mk]))
srow = []
for ax, lv in (("resolution", 5), ("blur", 5)):
    mk = ((sim.axis == ax) & (sim.level == lv)).values
    for c in DET:
        v = sim.loc[mk, c].astype(float)
        ok = v.notna().values
        a = roc_auc_score(ys[mk][ok], v[ok])
        srow.append(dict(damage=f"{ax} level {lv}", feature=c, auc=round(max(a, 1 - a), 3), higher_means="worse" if a >= 0.5 else "better"))
single = pd.DataFrame(srow)

# ---------------------------------------------------------------- real captures
J = pd.read_csv(OUT + "sectionJ_remeasured.csv")
J["rec"] = J.set + "_" + J.record.astype(str)
J["w_c"] = J.diff_clean > 5
fe = pd.concat([pd.read_csv(OUT + "sectionH_armCext_features.csv"), pd.read_csv(OUT + "sectionD2b_armC_features.csv")], ignore_index=True)
ac = J.merge(fe, on="variant_id", how="left").merge(M, on="variant_id", how="left")
ac = ac[ac.dig_hr_clean.notna()].reset_index(drop=True)
assert ac[OUT_COLS].notna().any(axis=1).all() and ac[DET].notna().any(axis=1).all()
m1 = sig_model().fit(sim[OUT_COLS], ys)
m2 = sig_model().fit(sim[OUT_COLS + DET], ys)
ac["p_out"] = m1.predict_proba(ac[OUT_COLS])[:, 1]
ac["p_both"] = m2.predict_proba(ac[OUT_COLS + DET])[:, 1]
isnew = (ac.set == "armC_new100").values
real = (ac.axis != "C0_kit_original").values
rr = []
res_pooled = None
for lab, mk in (("new 100, all 9 types", isnew), ("first 40", (ac.set == "armC_first40").values), ("pooled 140, all", np.ones(len(ac), bool)), ("pooled 140, real C1-C8", real)):
    x = ac[mk]
    yy = x.w_c.astype(int).values
    r = dict(subset=lab, images=len(x), wrong=int(yy.sum()))
    for nm, sc in (("OUT", "p_out"), ("OUT+DET", "p_both")):
        a, ci = auc_ci(yy, x[sc].values, x.rec.values, B=2000)
        r[nm] = fmt(a, ci)
    v = x["det_spread"].astype(float).values
    ok = np.isfinite(v)
    a = roc_auc_score(yy[ok], v[ok])
    r["det_spread alone"] = f"{max(a, 1 - a):.3f}" + (" (higher = worse)" if a >= 0.5 else " (higher = better)")
    d0, dci = diff_ci(yy, x.p_out.values, x.p_both.values, x.rec.values)
    r["OUT+DET minus OUT"] = f"{d0:+.3f} (95%: {dci[0]:+.3f} to {dci[1]:+.3f})"
    if lab == "pooled 140, all":
        res_pooled = d0
    rr.append(r)
real_tab = pd.DataFrame(rr)

g = []
x = ac[real]
yy = x.w_c.astype(int).values
for nm, sc in (("OUT", "p_out"), ("OUT+DET", "p_both")):
    for fr in (0.1, 0.2, 0.3):
        f = x[sc].values >= np.quantile(x[sc].values, 1 - fr)
        g.append(dict(model=nm, flag_top=f"{int(fr * 100)}%", wrong_caught=f"{100 * f[yy == 1].mean():.0f}%", right_flagged=f"{100 * f[yy == 0].mean():.0f}%", wrong_among_kept=f"{100 * yy[~f].mean():.1f}%"))
gate = pd.DataFrame(g)

crit_a = res_pooled is not None and res_pooled >= 0.02
crit_b = all(v[1] >= v[0] for v in simw.values())
sim_tab.to_csv(OUT + "sectionM_simulated.csv", index=False)
single.to_csv(OUT + "sectionM_single_features_sim.csv", index=False)
real_tab.to_csv(OUT + "sectionM_real_captures.csv", index=False)
gate.to_csv(OUT + "sectionM_gate_real.csv", index=False)
simtxt = ", ".join(f"{k[0]} {k[1]}: {v[0]:.3f} -> {v[1]:.3f}" for k, v in simw.items())
L = ["# Section M (EXPLORATORY): do detector-agreement features improve the output check?\n",
     "*Generated by `scripts/analysis/section_M.py`. Rules fixed beforehand (docs/plan/analysis_plan_changes.md, 2026-11-08). Cleaned labels (Sections J, K). Real captures hold far fewer than 100 wrong readings: descriptive.*\n",
     f"- **Pre-fixed rule: (a) pooled-140 real-capture AUC rises by >= 0.02: {'YES' if crit_a else 'NO'} (change {res_pooled:+.3f}); (b) simulated within-damage AUC (resolution 5, blur 5) does not fall: {'YES' if crit_b else 'NO'} "
     f"(OUT -> OUT+DET: {simtxt}). Added value counted only if both hold: {'MET' if (crit_a and crit_b) else 'NOT MET'}.**\n",
     "## Simulated new 100 (cross-validated)\n", md_table(sim_tab) + "\n", "Single detector-agreement features inside the hard damage types:\n", md_table(single) + "\n",
     "## Real captures: trained on the simulated new 100, applied once\n", md_table(real_tab) + "\n", "## Gate on real captures C1-C8\n", md_table(gate) + "\n"]
open(OUT + "SECTION_M.md", "w", encoding="utf-8").write("\n".join(L))
pd.set_option("display.width", 260)
pd.set_option("display.max_colwidth", 60)
print(sim_tab.to_string(index=False))
print()
print(single.to_string(index=False))
print()
print(real_tab.to_string(index=False))
print()
print(gate.to_string(index=False))
print("\nRULE a:", crit_a, round(res_pooled, 3), " RULE b:", crit_b, simw)
