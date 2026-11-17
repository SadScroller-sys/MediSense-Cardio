"""Section L (EXPLORATORY, post hoc; logged 2026-11-08): repeat the output check (D2) and the photo detector with the CLEANED heart-rate labels (Sections J, K).
(1) Simulated new 100: cross-validated AUC with cleaned labels (does the simulated result survive the correction?).
(2) Real captures: models trained on the simulated new 100 with cleaned labels, applied once to the real captures scored with cleaned labels (Arm C 140 recordings; photo scores exist only for the new 100).
(3) Comparison: the models trained with the ORIGINAL labels, scored against the cleaned labels.
Writes results/analysis/sectionL_*.csv and SECTION_L.md."""
import warnings

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

warnings.filterwarnings("ignore")
src = open("D:/Capstone Project/scripts/analysis/section_D2.py", encoding="utf-8").read().split("preds = {}")[0]
exec(compile(src, "section_D2_prefix", "exec"))          # d, te, y, groups, OUT_COLS, X_COLS, FEATS, sig_model, auc_ci, oof
ROOT = "D:/Capstone Project/"
OUT = ROOT + "results/analysis/"


def md_table(t):
    head = "| " + " | ".join(map(str, t.columns)) + " |\n|" + "---|" * len(t.columns) + "\n"
    return head + "\n".join("| " + " | ".join(str(z) for z in r) + " |" for r in t.itertuples(index=False))


def fmt(a, ci):
    return f"{a:.3f} ({ci[0]:.2f} to {ci[1]:.2f})"


# ---------------------------------------------------------------- (1) simulated, cleaned labels
K = pd.read_csv(OUT + "sectionK_remeasured_sim.csv")
K["wrong_c"] = (K.diff_clean > 5)
sim = te.merge(K[["variant_id", "wrong_c", "dig_hr_clean"]], on="variant_id", how="left").reset_index(drop=True)
sim = sim[sim.dig_hr_clean.notna()].reset_index(drop=True)
ys = sim.wrong_c.astype(int).values
gs = sim.record.values
print("simulated images with reading:", len(sim), "wrong (cleaned):", int(ys.sum()), "wrong (original):", int(y.sum()))
rows = []
for name, cols in (("output features", OUT_COLS), ("photo scores", X_COLS), ("both", X_COLS + OUT_COLS)):
    p = oof(sim[cols], ys, gs, sig_model)
    a, ci = auc_ci(ys, p, gs, B=1000)
    r = dict(model=name, overall_auc=fmt(a, ci))
    for ax, lv in (("resolution", 5), ("blur", 5)):
        mk = ((sim.axis == ax) & (sim.level == lv)).values
        aw, cw = auc_ci(ys[mk], p[mk], gs[mk], B=1000)
        r[f"within {ax} level {lv}"] = fmt(aw, cw)
    rows.append(r)
sim_tab = pd.DataFrame(rows)

# ---------------------------------------------------------------- (2),(3) real captures
J = pd.read_csv(OUT + "sectionJ_remeasured.csv")
J["rec"] = J.set + "_" + J.record.astype(str)
J["w_c"] = J.diff_clean > 5
fe = pd.concat([pd.read_csv(OUT + "sectionH_armCext_features.csv"), pd.read_csv(OUT + "sectionD2b_armC_features.csv")], ignore_index=True)
ac = J.merge(fe, on="variant_id", how="left")
ac = ac[ac.dig_hr_clean.notna()].reset_index(drop=True)
assert ac[OUT_COLS].notna().any(axis=1).all()
q = pd.read_csv(ROOT + "results/armCext/armCext_quality_signals_all.csv")
q["blur_log"] = np.log10(q.blur_score + 1)
ac = ac.merge(q[["variant_id"] + X_COLS], on="variant_id", how="left")
m_out_c = sig_model().fit(sim[OUT_COLS], ys)
m_out_o = sig_model().fit(te[OUT_COLS], y)
m_ph_c = sig_model().fit(sim[X_COLS], ys)
ac["p_out_c"] = m_out_c.predict_proba(ac[OUT_COLS])[:, 1]
ac["p_out_o"] = m_out_o.predict_proba(ac[OUT_COLS])[:, 1]
hasph = ac[X_COLS].notna().all(axis=1)
ac["p_ph_c"] = np.nan
ac.loc[hasph, "p_ph_c"] = m_ph_c.predict_proba(ac.loc[hasph, X_COLS])[:, 1]


def row(mask, label, score):
    x = ac[mask & ac[score].notna()]
    yy = x.w_c.astype(int).values
    if yy.sum() < 5:
        return dict(subset=label, score=score, images=len(x), wrong_cleaned=int(yy.sum()), auc="too few (<5)")
    a, ci = auc_ci(yy, x[score].values, x.rec.values, B=2000)
    return dict(subset=label, score=score, images=len(x), wrong_cleaned=int(yy.sum()), auc=fmt(a, ci))


isnew = ac.set == "armC_new100"
real = ac.axis != "C0_kit_original"
rr = []
for sc in ("p_out_c", "p_out_o"):
    rr += [row(isnew, "new 100, all 9 types", sc), row(isnew & real, "new 100, real C1-C8", sc), row(ac.set == "armC_first40", "first 40", sc), row(ac.rec != "x", "pooled 140, all", sc), row(real, "pooled 140, real C1-C8", sc)]
rr += [row(isnew, "new 100, all 9 types", "p_ph_c"), row(isnew & real, "new 100, real C1-C8", "p_ph_c")]
rtab = pd.DataFrame(rr)

g = []
for sub, mk in (("pooled 140, real C1-C8", real), ("new 100, real C1-C8", isnew & real)):
    x = ac[mk]
    yy = x.w_c.astype(int).values
    for fr in (0.1, 0.2, 0.3):
        f = x.p_out_c.values >= np.quantile(x.p_out_c.values, 1 - fr)
        g.append(dict(subset=sub, flag_top=f"{int(fr * 100)}%", wrong_caught=f"{100 * f[yy == 1].mean():.0f}%", right_flagged=f"{100 * f[yy == 0].mean():.0f}%",
                      wrong_among_kept=f"{100 * yy[~f].mean():.1f}%", wrong_overall=f"{100 * yy.mean():.1f}%"))
gtab = pd.DataFrame(g)

sim_tab.to_csv(OUT + "sectionL_simulated_cleaned_labels.csv", index=False)
rtab.to_csv(OUT + "sectionL_real_captures.csv", index=False)
gtab.to_csv(OUT + "sectionL_real_gate.csv", index=False)
L = ["# Section L (EXPLORATORY, post hoc): output check and photo detector with the corrected (cleaned) heart-rate labels\n",
     f"*Generated by `scripts/analysis/section_L.py`. Cleaned labels: Sections J and K. Simulated new 100: {len(sim)} images with a reading, {int(ys.sum())} wrong (cleaned) vs {int(y.sum())} (original). "
     f"Real captures: {len(ac)} images with a reading, {int(ac.w_c.sum())} wrong (cleaned), far below the 100 events recommended: descriptive only.*\n",
     "## (1) Simulated damage, cleaned labels (cross-validated, whole recordings held out)\n", md_table(sim_tab) + "\n",
     "## (2),(3) Real captures: models trained on simulated damage, applied once, scored with cleaned labels\n",
     "`p_out_c` = output check trained with cleaned labels; `p_out_o` = trained with the original labels; `p_ph_c` = photo detector (new 100 only has photo scores; trained on the simulated new 100 with cleaned labels).\n",
     md_table(rtab) + "\n", "## Gate on real captures (output check, cleaned labels)\n", md_table(gtab) + "\n"]
open(OUT + "SECTION_L.md", "w", encoding="utf-8").write("\n".join(L))
pd.set_option("display.width", 250)
print(sim_tab.to_string(index=False)); print()
print(rtab.to_string(index=False)); print()
print(gtab.to_string(index=False))
