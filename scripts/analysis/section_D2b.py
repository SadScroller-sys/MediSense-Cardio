"""D2 follow-ups (EXPLORATORY; rules in docs/plan/analysis_plan_changes.md, 2026-11-07): (a) feature families, (b) cost on irregular rhythms, (c) EXTERNAL check on the real captures (Arm C).
Reuses the data preparation, helpers and cross-validation of section_D2.py (executed up to its 'preds = {}' line). Writes results/analysis/sectionD2b_*.csv and SECTION_D2b.md."""
import ast
import importlib.util
import os
import zipfile

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

src = open("D:/Capstone Project/scripts/analysis/section_D2.py", encoding="utf-8").read().split("preds = {}")[0]
exec(compile(src, "section_D2_prefix", "exec"))          # te, y, groups, OUT_COLS, X_COLS, oof, sig_model, auc_ci, folds_for ...
ROOT = "D:/Capstone Project/"
OUT = ROOT + "results/analysis/"

# ------------------------------------------------------------------ (a) feature families
FAM = {"RR regularity only": ["rr_cv", "rr_max_ratio", "rr_min_ratio"],
       "cross-lead consistency only": ["einthoven", "goldberger", "xlead_count_match", "xlead_count_absdiff"],
       "completeness only": ["ii_complete", "n_unreadable_leads", "mean_other_lead_complete", "n_beats"],
       "all output features": OUT_COLS}
rows = []
p_fam = {}
for name, cols in FAM.items():
    p = oof(te[cols], y, groups, sig_model)
    p_fam[name] = p
    a, ci = auc_ci(y, p, groups, B=1000)
    r = dict(feature_family=name, overall_auc=f"{a:.3f} ({ci[0]:.2f} to {ci[1]:.2f})")
    for ax, lv in (("resolution", 5), ("blur", 5)):
        mk = ((te.axis == ax) & (te.level == lv)).values
        aw, cw = auc_ci(y[mk], p[mk], groups[mk], B=1000)
        r[f"within {ax} level {lv}"] = f"{aw:.3f} ({cw[0]:.2f} to {cw[1]:.2f})"
    rows.append(r)
fam = pd.DataFrame(rows)

# ------------------------------------------------------------------ (b) cost on irregular rhythms
db = pd.read_csv(ROOT + "data/ptbxl/ptbxl_database.csv")
db["record"] = db.filename_lr.str.split("/").str[-1]


def has_af(s):
    try:
        return any(k in ast.literal_eval(s) for k in ("AFIB", "AFLT"))
    except Exception:
        return False


db["af"] = db.scp_codes.map(has_af)
te2 = te.merge(db[["record", "af"]], on="record", how="left")
p_out = p_fam["all output features"]
flag20 = p_out >= np.quantile(p_out, 0.8)
right = (y == 0)
rows = []
for lab, mk in (("atrial fibrillation / flutter recordings", te2.af.values), ("all other recordings", ~te2.af.values)):
    n_rec = te2[mk].record.nunique()
    rr_clean = te2[mk & (te2.axis == "clean").values].rr_cv.median()
    rows.append(dict(group=lab, recordings=n_rec, images_with_right_reading=int((mk & right).sum()),
                     right_readings_flagged_at_20pct=f"{int((flag20 & mk & right).sum())}/{int((mk & right).sum())} = {100 * (flag20 & mk & right).sum() / max(1, (mk & right).sum()):.0f}%",
                     median_rr_cv_clean_pages=round(float(rr_clean), 3)))
af = pd.DataFrame(rows)

# ------------------------------------------------------------------ (c) external: train on all new-100 images with a reading, apply once to Arm C
cache = OUT + "sectionD2b_armC_features.csv"
assert os.path.exists(cache), "run scripts/analysis/section_D2b_armC_features.py first"
fc = pd.read_csv(cache)
ac = pd.read_csv(ROOT + "results/armC/results_armC.csv").merge(fc, on="variant_id", how="inner")
assert len(ac) == 360
ac["wrong5"] = ac.diff_bpm > 5
acw = ac[ac.dig_hr.notna()].reset_index(drop=True)
yc = acw.wrong5.astype(int).values
model = sig_model().fit(te[OUT_COLS], y)
pc = model.predict_proba(acw[OUT_COLS])[:, 1]
a_c, ci_c = auc_ci(yc, pc, acw.record.values, B=2000)
rows = [dict(subset="all capture types incl. clean kit page", images=len(acw), wrong=int(yc.sum()), auc=f"{a_c:.3f} ({ci_c[0]:.2f} to {ci_c[1]:.2f})")]
real = ~acw.axis.str.startswith("C0")
a2, c2 = auc_ci(yc[real.values], pc[real.values], acw.record.values[real.values], B=2000)
rows.append(dict(subset="real captures only (C1 to C8)", images=int(real.sum()), wrong=int(yc[real.values].sum()), auc=f"{a2:.3f} ({c2[0]:.2f} to {c2[1]:.2f})"))
for ax, g in acw.groupby("axis"):
    mk = (acw.axis == ax).values
    if 0 < yc[mk].sum() < mk.sum() and yc[mk].sum() >= 3:
        rows.append(dict(subset=ax, images=int(mk.sum()), wrong=int(yc[mk].sum()), auc=f"{roc_auc_score(yc[mk], pc[mk]):.3f} (n small, no interval)"))
ext = pd.DataFrame(rows)
# single strongest feature on its own, for context
sf = []
for c in ("rr_cv", "rr_max_ratio", "einthoven", "goldberger", "xlead_count_match"):
    v = acw[c].astype(float)
    ok = v.notna().values
    a = roc_auc_score(yc[ok], v[ok])
    sf.append(dict(feature=c, auc_on_real_captures=round(max(a, 1 - a), 3), higher_means="worse" if a >= 0.5 else "better"))
sfd = pd.DataFrame(sf)
# gate on real captures
gate_rows = []
for fr in (0.1, 0.2, 0.3):
    f = pc >= np.quantile(pc, 1 - fr)
    gate_rows.append(dict(flag_top=f"{int(fr * 100)}%", wrong_caught=f"{100 * f[yc == 1].mean():.0f}%", right_flagged=f"{100 * f[yc == 0].mean():.0f}%",
                          wrong_among_kept=f"{100 * yc[~f].mean():.1f}%", wrong_overall=f"{100 * yc.mean():.1f}%"))
gate = pd.DataFrame(gate_rows)

fam.to_csv(OUT + "sectionD2b_feature_families.csv", index=False)
af.to_csv(OUT + "sectionD2b_irregular_rhythms.csv", index=False)
ext.to_csv(OUT + "sectionD2b_external_armC.csv", index=False)
gate.to_csv(OUT + "sectionD2b_external_gate.csv", index=False)


def md_table(t):
    head = "| " + " | ".join(map(str, t.columns)) + " |\n|" + "---|" * len(t.columns) + "\n"
    return head + "\n".join("| " + " | ".join(str(z) for z in r) + " |" for r in t.itertuples(index=False))


L = ["# D2 follow-up checks (EXPLORATORY): is the output-based gate real, and does it work on real captures?\n",
     "*Generated by `scripts/analysis/section_D2b.py`. Rules: `docs/plan/analysis_plan_changes.md` (2026-11-07). These follow-ups were fixed AFTER the main D2 result was seen.*\n",
     "## (a) Which checks do the work? (new 100, cross-validated, images with a reading)\n", md_table(fam) + "\n",
     "## (b) Cost: does it flag correct readings on irregular rhythms? (output features, flag the top 20%)\n", md_table(af) + "\n",
     "## (c) External check: trained on the new 100 (simulated damage), applied once to the REAL captures (Arm C)\n",
     "Only the output features can be used (the Arm C page images are not on this computer, so photo scores cannot be computed). "
     "Real captures hold fewer than 100 wrong readings, so this is descriptive.\n", md_table(ext) + "\n",
     "Single features on real captures:\n", md_table(sfd) + "\n",
     "Gate on real captures:\n", md_table(gate) + "\n"]
open(OUT + "SECTION_D2b.md", "w", encoding="utf-8").write("\n".join(L))

pd.set_option("display.width", 250)
pd.set_option("display.max_colwidth", 60)
print(fam.to_string(index=False)); print()
print(af.to_string(index=False)); print()
print(ext.to_string(index=False)); print()
print(sfd.to_string(index=False)); print()
print(gate.to_string(index=False))
