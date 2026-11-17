"""D2 (EXPLORATORY; rules fixed in docs/plan/analysis_plan_changes.md on 2026-11-07 before any result): can features of the digitiser's OUTPUT catch the silent failures?
New 100 recordings only (the first 50 have no saved signals), images with a reading, target = wrong heart rate > 5 bpm. Grouped 5-fold cross-validation x10 over recordings.
Feature sets: PHOTO (five photo scores), OUT (output features, results/analysis/sectionD2_features.csv), BOTH; oracle = told damage type and level.
Improvement criterion (fixed in advance): within-damage AUC inside resolution level 5 and blur level 5 at least 0.70 with the lower 95% bound above 0.50.
Reuses the data preparation of section_D.py (executed up to its C3 block). Writes results/analysis/sectionD2_*.csv and SECTION_D2.md."""
import warnings

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

warnings.filterwarnings("ignore")
src = open("D:/Capstone Project/scripts/analysis/section_D.py", encoding="utf-8").read().split("# ------------------------------------------------------------------ C3")[0]
exec(compile(src, "section_D_prefix", "exec"))          # d, X_COLS (photo), sig_model, sev_model, target, auc_ci ...
ROOT = "D:/Capstone Project/"
OUT = ROOT + "results/analysis/"

OUT_COLS = ["ii_complete", "n_unreadable_leads", "mean_other_lead_complete", "n_beats", "hr_ii", "hr_implausible", "rr_cv", "rr_max_ratio", "rr_min_ratio",
            "amp_log", "hf_share", "einthoven", "goldberger", "xlead_count_match", "xlead_count_absdiff"]
feat = pd.read_csv(OUT + "sectionD2_features.csv")
nd = d[d.set == "new100"].merge(feat, on="variant_id", how="left")
assert len(feat) == 1300 and nd[OUT_COLS].notna().any(axis=1).all()
te, y = target(nd, "primary")
te = te.reset_index(drop=True)
groups = te.record.values
print(f"images with a reading: {len(te)}, wrong readings: {int(y.sum())}, recordings: {te.record.nunique()}")
SETS = {"PHOTO (five photo scores)": X_COLS, "OUTPUT (digitised-signal features)": OUT_COLS, "BOTH": X_COLS + OUT_COLS}


def folds_for(groups, n_splits, seed):
    r = np.random.RandomState(seed)
    perm = r.permutation(np.unique(groups))
    fold_of = {g: i % n_splits for i, g in enumerate(perm)}
    return np.array([fold_of[g] for g in groups])


def oof(X, yy, groups, model, n_splits=5, repeats=10, seed=0):
    tot = np.zeros(len(yy))
    for rep in range(repeats):
        folds = folds_for(groups, n_splits, seed + rep)
        p = np.full(len(yy), np.nan)
        for f in range(n_splits):
            trn, tst = folds != f, folds == f
            p[tst] = model().fit(X[trn], yy[trn]).predict_proba(X[tst])[:, 1]
        tot += p
    return tot / repeats


preds = {}
for name, cols in SETS.items():
    preds[name] = oof(te[cols], y, groups, sig_model)
preds["ORACLE (told damage type and level)"] = oof(te[["axlv"]], y, groups, sev_model)

# overall AUC with recording-level interval
rows = []
for name, p in preds.items():
    a, ci = auc_ci(y, p, groups, B=1000)
    rows.append(dict(model=name, auc=round(a, 3), ci95=f"{ci[0]:.2f} to {ci[1]:.2f}"))
overall = pd.DataFrame(rows)


# within one damage type and level
def within(mask, p):
    yy, pp, gg = y[mask], p[mask], groups[mask]
    a, ci = auc_ci(yy, pp, gg, B=1000)
    return a, ci, int(yy.sum()), int(mask.sum())


wrows = []
for ax, lv in (("resolution", 5), ("blur", 5)):
    mk = ((te.axis == ax) & (te.level == lv)).values
    for name, p in preds.items():
        if name.startswith("ORACLE"):
            continue
        a, ci, nb, n = within(mk, p)
        wrows.append(dict(damage=f"{ax} level {lv}", images=n, wrong=nb, model=name, auc_within_damage=round(a, 3), ci95=f"{ci[0]:.2f} to {ci[1]:.2f}"))
wd = pd.DataFrame(wrows)

# single features inside the two hard damage types (direction free): which output feature separates wrong from right?
srows = []
for ax, lv in (("resolution", 5), ("blur", 5)):
    mk = ((te.axis == ax) & (te.level == lv)).values
    for c in OUT_COLS + X_COLS:
        v = te.loc[mk, c].astype(float)
        yy = y[mk]
        ok = v.notna().values
        if ok.sum() < 20 or yy[ok].min() == yy[ok].max():
            continue
        a = roc_auc_score(yy[ok], v[ok])
        srows.append(dict(damage=f"{ax} level {lv}", feature=c, auc=round(max(a, 1 - a), 3), higher_means=("worse" if a >= 0.5 else "better")))
single = pd.DataFrame(srows).sort_values(["damage", "auc"], ascending=[True, False])

# leave one damage type out (train without it, test on it)
lrows = []
axes_arr = te.axis.values
for name, cols in SETS.items():
    folds = folds_for(groups, 5, 0)
    for ax in ["resolution", "blur", "rotate", "jpeg", "brightness", "gridcontrast"]:
        p = np.full(len(y), np.nan)
        for f in range(5):
            trn = (folds != f) & (axes_arr != ax)
            tst = (folds == f) & (axes_arr == ax)
            p[tst] = sig_model().fit(te.loc[trn, cols], y[trn]).predict_proba(te.loc[tst, cols])[:, 1]
        mk = axes_arr == ax
        nb = int(y[mk].sum())
        lrows.append(dict(model=name, unseen_damage=ax, wrong=nb, auc=("too few wrong (<8)" if nb < 8 else round(roc_auc_score(y[mk], p[mk]), 3))))
lodo = pd.DataFrame(lrows).pivot(index="unseen_damage", columns="model", values="auc").reset_index()

# coverage (gate) with intervals
rs = np.random.RandomState(5)
jit = rs.rand(len(y))


def gate(p, fr):
    n = int(np.ceil(fr * len(p)))
    o = np.lexsort((jit[: len(p)] if len(p) <= len(jit) else rs.rand(len(p)), -p))
    f = np.zeros(len(p), bool)
    f[o[:n]] = True
    return f


def gmet(yy, p, fr):
    f = gate(p, fr)
    return f[yy == 1].sum() / yy.sum(), f[yy == 0].sum() / (yy == 0).sum(), yy[~f].mean()


recs = np.unique(groups)
idx = {g: np.where(groups == g)[0] for g in recs}
crow = []
for name in list(SETS) + ["ORACLE (told damage type and level)"]:
    p = preds[name]
    boots = {fr: [] for fr in (0.1, 0.2, 0.3)}
    for _ in range(1000):
        ii = np.concatenate([idx[g] for g in rs.choice(recs, len(recs), replace=True)])
        if y[ii].sum() == 0:
            continue
        for fr in boots:
            boots[fr].append(gmet(y[ii], p[ii], fr))
    for fr in (0.1, 0.2, 0.3):
        c, g_, k = gmet(y, p, fr)
        b = np.array(boots[fr])
        lo = np.nanpercentile(b, [2.5, 97.5], axis=0)
        crow.append(dict(model=name, flag_top=f"{int(fr * 100)}%", caught=f"{100 * c:.0f}% ({100 * lo[0, 0]:.0f}-{100 * lo[1, 0]:.0f})",
                         good_flagged=f"{100 * g_:.0f}%", kept_wrong=f"{100 * k:.1f}% ({100 * lo[0, 2]:.1f}-{100 * lo[1, 2]:.1f})", wrong_overall=f"{100 * y.mean():.1f}%"))
cov = pd.DataFrame(crow)

# criterion
both_name = "BOTH"
crit = {}
for ax in ("resolution level 5", "blur level 5"):
    for nm in ("OUTPUT (digitised-signal features)", "BOTH"):
        r = wd[(wd.damage == ax) & (wd.model == nm)].iloc[0]
        lo = float(r.ci95.split(" to ")[0])
        crit[(ax, nm)] = (float(r.auc_within_damage) >= 0.70) and (lo > 0.50)
met = all(crit[(ax, "OUTPUT (digitised-signal features)")] for ax in ("resolution level 5", "blur level 5")) or \
    all(crit[(ax, "BOTH")] for ax in ("resolution level 5", "blur level 5"))

overall.to_csv(OUT + "sectionD2_overall_auc.csv", index=False)
wd.to_csv(OUT + "sectionD2_within_damage.csv", index=False)
single.to_csv(OUT + "sectionD2_single_features.csv", index=False)
lodo.to_csv(OUT + "sectionD2_leave_one_damage_out.csv", index=False)
cov.to_csv(OUT + "sectionD2_coverage.csv", index=False)


def md_table(t):
    head = "| " + " | ".join(map(str, t.columns)) + " |\n|" + "---|" * len(t.columns) + "\n"
    return head + "\n".join("| " + " | ".join(str(z) for z in r) + " |" for r in t.itertuples(index=False))


L = ["# D2 results (EXPLORATORY): can the digitiser's output catch the silent failures?\n",
     "*Generated by `scripts/analysis/section_D2.py`. Rules were fixed in `docs/plan/analysis_plan_changes.md` (2026-11-07) before any result. "
     "New 100 recordings only; images with a reading; target = wrong heart rate > 5 bpm; whole recordings held out (5-fold x10). No verdict word is used.*\n",
     f"- Images: {len(te)}; wrong readings: {int(y.sum())}; recordings: {te.record.nunique()} (86 events are below the 100 recommended: small sample).",
     f"- **Improvement criterion (fixed in advance): within-damage AUC inside resolution level 5 and blur level 5 at least 0.70 with lower 95% bound above 0.50. Result: {'MET' if met else 'NOT MET'}.**\n",
     "## Overall AUC (cross-validated)\n", md_table(overall) + "\n",
     "## Inside one damage type and level: can it tell WHICH damaged pages fail? (0.5 = no better than guessing)\n", md_table(wd) + "\n",
     "## Which single features separate wrong from right inside the hard damage types (direction free; descriptive)\n", md_table(single.groupby("damage").head(8)) + "\n",
     "## Unseen damage type (train without it, test on it)\n", md_table(lodo) + "\n",
     "## Gate: flag the highest-risk photos (95% intervals over recordings)\n", md_table(cov) + "\n",
     "## Limits\n- 86 wrong readings, one recording set (cross-validation within it), simulated damage; the first 50 recordings cannot be used because their digitised signals were not saved.\n"
     "- The output features use the same peak detector as the target, so part of the signal is by design. A deployed check can compute exactly these features, because none uses the reference.\n"
     "- Not a verdict: exploratory, added after the main plan.\n"]
open(OUT + "SECTION_D2.md", "w", encoding="utf-8").write("\n".join(L))

pd.set_option("display.width", 250)
pd.set_option("display.max_colwidth", 50)
print(overall.to_string(index=False)); print()
print(wd.to_string(index=False)); print()
print(single.groupby("damage").head(6).to_string(index=False)); print()
print(lodo.to_string(index=False)); print()
print(cov.to_string(index=False)); print()
print("CRITERION MET" if met else "CRITERION NOT MET", crit)
