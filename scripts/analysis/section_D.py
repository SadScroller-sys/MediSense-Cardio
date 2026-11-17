"""Section D (MASTER_PLAN section 4 C3 and inventory items 15-17, 19): can the five photo-quality scores warn that a heart-rate reading is wrong?

Rules fixed BEFORE any result was looked at (2026-11-07):
  * Scores: blur_score (log10(x+1)), skew_deg, resolution_score, contrast_score, blockiness_score (quality_signals_*.csv).
  * Model: median imputation, standardisation, logistic regression (class_weight='balanced', max_iter=1000) -- same as the first held-out test.
  * C3 target: wrong heart rate (|digitised - reference| > 5 bpm), counted ONLY on images where the digitiser gave a reading
    (a page with no output needs no warning: the user sees there is no reading). Secondary, descriptive: 'bad' = wrong or no output.
  * Train on the first 50 (reliable ones, all 31 versions); score the new 100 (13 versions) ONCE. Unreliable recordings excluded
    (15192, 21205). AUC interval: recording-level bootstrap (2,000).
  * Verdict (MASTER_PLAN): INCONCLUSIVE if the new 100 hold fewer than 100 wrong readings; CEILING-LIMITED if the oracle (told the exact damage type
    and level) is itself below 0.70; 'discriminates within these six damage types' only if AUC >= 0.70 and the lower 95% bound > 0.60. The word 'usable' is not used.
  * Always reported with: oracle, best single score (chosen on the first 50 only), leave-one-damage-type-out, swapped direction, grouped CV on all 150
    (13 shared versions), continuous-target correlation, coverage curve.
Not done (stated limits): the digitiser-output feature 'unreadable leads' (no saved first-50 signals) and a standard no-reference quality baseline.
Reads (never modifies) results/detector/quality_signals_*.csv, results/v2_intervals/results_v2.csv, results/extension/results_extension.csv.
Writes results/analysis/sectionD_*.csv and SECTION_D.md."""
import os
import warnings

import numpy as np
import pandas as pd
from scipy.stats import rankdata, spearmanr
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

warnings.filterwarnings("ignore")
ROOT = "D:/Capstone Project"
OUT = f"{ROOT}/results/analysis"
os.makedirs(OUT, exist_ok=True)
FEATS = ["blur_score", "skew_deg", "resolution_score", "contrast_score", "blockiness_score"]
AXES = ["resolution", "blur", "rotate", "jpeg", "brightness", "gridcontrast"]
SHARED = {0, 3, 5}
UNREL = {"15192_lr", "21205_lr"}

# ------------------------------------------------------------------ data
v = pd.read_csv(f"{ROOT}/results/v2_intervals/results_v2.csv")
e = pd.read_csv(f"{ROOT}/results/extension/results_extension.csv")
sv = pd.read_csv(f"{ROOT}/results/detector/quality_signals_v2.csv")
se = pd.read_csv(f"{ROOT}/results/detector/quality_signals_ext.csv")
keep = ["variant_id", "record", "axis", "level", "dig_hr", "diff_bpm"]
f50 = v[keep].merge(sv[["variant_id"] + FEATS], on="variant_id", how="inner")
n100 = e[keep].merge(se[["variant_id"] + FEATS], on="variant_id", how="inner")
assert len(f50) == 1550 and len(n100) == 1300
f50["set"], n100["set"] = "first50", "new100"
d = pd.concat([f50, n100], ignore_index=True)
d = d[~d.record.isin(UNREL)].reset_index(drop=True)
d["out"] = d.dig_hr.notna()
d["wrong5"] = (d.diff_bpm > 5)
d["bad"] = ~d.out | d.wrong5
d["blur_log"] = np.log10(d.blur_score + 1)
X_COLS = ["blur_log", "skew_deg", "resolution_score", "contrast_score", "blockiness_score"]
d["axlv"] = d.axis + "_" + d.level.astype(str)
rng = np.random.RandomState(7)


def sig_model():
    return make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), LogisticRegression(max_iter=1000, class_weight="balanced"))


def sev_model():
    return make_pipeline(OneHotEncoder(handle_unknown="ignore"), LogisticRegression(max_iter=1000, class_weight="balanced"))


def auc_ci(y, p, groups, B=2000, seed=1):
    r = np.random.RandomState(seed)
    recs = np.unique(groups)
    idx = {g: np.where(groups == g)[0] for g in recs}
    vals = []
    for _ in range(B):
        pick = r.choice(recs, len(recs), replace=True)
        ii = np.concatenate([idx[g] for g in pick])
        if y[ii].min() == y[ii].max():
            continue
        vals.append(roc_auc_score(y[ii], p[ii]))
    return float(roc_auc_score(y, p)), np.percentile(vals, [2.5, 97.5])


def target(x, kind):
    """returns (subset frame, y). primary: images with output, y = wrong5. secondary: all images, y = bad."""
    if kind == "primary":
        x = x[x.out]
        return x, x.wrong5.astype(int).values
    return x, x.bad.astype(int).values


def fmt(auc, ci):
    return f"{auc:.3f} ({ci[0]:.2f} to {ci[1]:.2f})"


train = d[d.set == "first50"]
test = d[d.set == "new100"]
results = {}
lines = []

# ------------------------------------------------------------------ C3: train on first 50, score new 100 once
for kind in ("primary", "secondary"):
    tr, ytr = target(train, kind)
    te, yte = target(test, kind)
    m = sig_model().fit(tr[X_COLS], ytr)
    p = m.predict_proba(te[X_COLS])[:, 1]
    auc, ci = auc_ci(yte, p, te.record.values)
    # oracle: told the exact damage type and level
    mo = sev_model().fit(tr[["axlv"]], ytr)
    po = mo.predict_proba(te[["axlv"]])[:, 1]
    aucO, ciO = auc_ci(yte, po, te.record.values)
    # single scores: direction + choice made on the first 50 only
    single = []
    for f in X_COLS:
        a_tr = roc_auc_score(ytr, tr[f].fillna(tr[f].median()))
        sign = 1 if a_tr >= 0.5 else -1
        a_te = roc_auc_score(yte, sign * te[f].fillna(tr[f].median()))
        single.append(dict(score=f, auc_train_first50=round(max(a_tr, 1 - a_tr), 3), direction="higher=worse" if sign == 1 else "lower=worse", auc_test_new100=round(a_te, 3)))
    single = pd.DataFrame(single).sort_values("auc_train_first50", ascending=False).reset_index(drop=True)
    best = single.iloc[0]
    results[kind] = dict(n_test=len(te), n_bad=int(yte.sum()), n_train=len(tr), n_train_bad=int(ytr.sum()), auc=auc, ci=ci, oracle=aucO, ciO=ciO,
                         single=single, best=best, p=p, te=te, y=yte, po=po)

prim = results["primary"]
n_wrong = prim["n_bad"]
if n_wrong < 100:
    verdict = f"INCONCLUSIVE (the new 100 hold {n_wrong} wrong readings; the rule needs at least 100)"
elif prim["oracle"] < 0.70:
    verdict = "CEILING-LIMITED (the oracle is itself below 0.70)"
elif prim["auc"] >= 0.70 and prim["ci"][0] > 0.60:
    verdict = "DISCRIMINATES within these six damage types"
else:
    verdict = "does NOT demonstrate discrimination (AUC below 0.70 or lower bound at or below 0.60)"

# ------------------------------------------------------------------ extras
# swapped direction: train on new 100, test first 50 (shared versions only)
tr_s, ytr_s = target(test, "primary")
te_s, yte_s = target(train[train.level.isin(SHARED)], "primary")
ps = sig_model().fit(tr_s[X_COLS], ytr_s).predict_proba(te_s[X_COLS])[:, 1]
sw_auc, sw_ci = auc_ci(yte_s, ps, te_s.record.values)
sw_n_bad = int(yte_s.sum())

# grouped CV on all 150 (13 shared versions each)
pool = d[d.level.isin(SHARED)].reset_index(drop=True)
pool_p, ypool = target(pool, "primary")
pool_p = pool_p.reset_index(drop=True)


def grouped_oof(X, y, groups, n_splits=5, repeats=10, seed=0, model=sig_model):
    r = np.random.RandomState(seed)
    recs = np.unique(groups)
    tot = np.zeros(len(y))
    for _ in range(repeats):
        perm = r.permutation(recs)
        fold_of = {g: i % n_splits for i, g in enumerate(perm)}
        folds = np.array([fold_of[g] for g in groups])
        p = np.full(len(y), np.nan)
        for f in range(n_splits):
            trn, tst = folds != f, folds == f
            p[tst] = model().fit(X[trn], y[trn]).predict_proba(X[tst])[:, 1]
        tot += p
    return tot / repeats


g150 = pool_p.record.values
p_cv = grouped_oof(pool_p[X_COLS], ypool, g150)
cv_auc, cv_ci = auc_ci(ypool, p_cv, g150, B=1000)
p_cv_o = grouped_oof(pool_p[["axlv"]], ypool, g150, model=sev_model)
cvo_auc, cvo_ci = auc_ci(ypool, p_cv_o, g150, B=1000)

# leave-one-damage-type-out on the pooled 150 (clean always in training, held-out type scored on held-out recordings)
lodo = []
recs = np.unique(g150)
perm = np.random.RandomState(0).permutation(recs)
fold_of = {g: i % 5 for i, g in enumerate(perm)}
folds = np.array([fold_of[g] for g in g150])
axes_arr = pool_p.axis.values
for ax in AXES:
    p = np.full(len(ypool), np.nan)
    for f in range(5):
        trn = (folds != f) & (axes_arr != ax)
        tst = (folds == f) & (axes_arr == ax)
        p[tst] = sig_model().fit(pool_p.loc[trn, X_COLS], ypool[trn]).predict_proba(pool_p.loc[tst, X_COLS])[:, 1]
    mk = axes_arr == ax
    nb = int(ypool[mk].sum())
    lodo.append(dict(unseen_damage=ax, images=int(mk.sum()), wrong_readings=nb,
                     auc=("too few wrong readings (<8)" if nb < 8 else round(roc_auc_score(ypool[mk], p[mk]), 3))))
lodo = pd.DataFrame(lodo)

# continuous target: predicted risk vs |error| (new 100, images with output)
te = prim["te"]
rho, prho = spearmanr(prim["p"], te.diff_bpm)

# coverage curve on the new 100 (primary target)
cov = []
for frac in (0.10, 0.20, 0.30):
    flag = prim["p"] >= np.quantile(prim["p"], 1 - frac)
    y = prim["y"]
    cov.append(dict(flag_top=f"{int(frac * 100)}% of photos", wrong_readings_caught=f"{100 * flag[y == 1].mean():.0f}%",
                    good_readings_flagged=f"{100 * flag[y == 0].mean():.0f}%",
                    wrong_rate_among_kept=f"{100 * y[~flag].mean():.1f}%", wrong_rate_overall=f"{100 * y.mean():.1f}%"))
cov = pd.DataFrame(cov)

# exploratory: inside ONE damage type and level, can the scores tell which pages are wrong? (new 100, same model as C3)
wd = []
te_ = prim["te"].assign(p=prim["p"], y=prim["y"])
for ax_, lv_ in [("resolution", 5), ("blur", 5)]:
    g_ = te_[(te_.axis == ax_) & (te_.level == lv_)]
    wd.append(dict(damage=f"{ax_} level {lv_}", images=len(g_), wrong_readings=int(g_.y.sum()),
                   auc_within_damage=round(roc_auc_score(g_.y, g_.p), 3)))
wd = pd.DataFrame(wd)
wd.to_csv(f"{OUT}/sectionD_within_damage.csv", index=False)

# item 15: the five scores against error on all 150 (images with output), Spearman with recording-level bootstrap
sc = []
allo = d[d.out & d.level.isin(SHARED)].reset_index(drop=True)
for f in X_COLS:
    rho_f = spearmanr(allo[f].fillna(allo[f].median()), allo.diff_bpm)[0]
    idx = {g: np.where(allo.record.values == g)[0] for g in allo.record.unique()}
    rs = np.random.RandomState(3)
    bs = []
    for _ in range(500):
        pick = rs.choice(list(idx), len(idx), replace=True)
        ii = np.concatenate([idx[g] for g in pick])
        bs.append(spearmanr(allo.loc[ii, f].fillna(allo[f].median()), allo.loc[ii, "diff_bpm"])[0])
    lo, hi = np.percentile(bs, [2.5, 97.5])
    sc.append(dict(score=f, spearman_with_abs_error=round(rho_f, 3), boot95=f"{lo:.2f} to {hi:.2f}"))
sc = pd.DataFrame(sc)

# ------------------------------------------------------------------ save + report
prim["single"].to_csv(f"{OUT}/sectionD_single_scores.csv", index=False)
lodo.to_csv(f"{OUT}/sectionD_leave_one_damage_out.csv", index=False)
cov.to_csv(f"{OUT}/sectionD_coverage.csv", index=False)
sc.to_csv(f"{OUT}/sectionD_scores_vs_error.csv", index=False)
summary = pd.DataFrame([
    dict(analysis="C3 primary: train first 50 -> score new 100 (wrong HR, images with output)", n_images=prim["n_test"], wrong_readings=prim["n_bad"], auc=round(prim["auc"], 3), ci95=f"{prim['ci'][0]:.2f} to {prim['ci'][1]:.2f}"),
    dict(analysis="  oracle (told damage type and level)", n_images=prim["n_test"], wrong_readings=prim["n_bad"], auc=round(prim["oracle"], 3), ci95=f"{prim['ciO'][0]:.2f} to {prim['ciO'][1]:.2f}"),
    dict(analysis="C3 secondary: bad = wrong or no output (all images)", n_images=results["secondary"]["n_test"], wrong_readings=results["secondary"]["n_bad"], auc=round(results["secondary"]["auc"], 3), ci95=f"{results['secondary']['ci'][0]:.2f} to {results['secondary']['ci'][1]:.2f}"),
    dict(analysis="  oracle, secondary", n_images=results["secondary"]["n_test"], wrong_readings=results["secondary"]["n_bad"], auc=round(results["secondary"]["oracle"], 3), ci95=f"{results['secondary']['ciO'][0]:.2f} to {results['secondary']['ciO'][1]:.2f}"),
    dict(analysis="Swapped: train new 100 -> test first 50 (shared versions)", n_images=len(yte_s), wrong_readings=sw_n_bad, auc=round(sw_auc, 3), ci95=f"{sw_ci[0]:.2f} to {sw_ci[1]:.2f}"),
    dict(analysis="Grouped 5-fold CV on all 150 (13 shared versions)", n_images=len(ypool), wrong_readings=int(ypool.sum()), auc=round(cv_auc, 3), ci95=f"{cv_ci[0]:.2f} to {cv_ci[1]:.2f}"),
    dict(analysis="  oracle, same CV", n_images=len(ypool), wrong_readings=int(ypool.sum()), auc=round(cvo_auc, 3), ci95=f"{cvo_ci[0]:.2f} to {cvo_ci[1]:.2f}"),
])
summary.to_csv(f"{OUT}/sectionD_summary.csv", index=False)


def md_table(t):
    head = "| " + " | ".join(map(str, t.columns)) + " |\n|" + "---|" * len(t.columns) + "\n"
    return head + "\n".join("| " + " | ".join(str(z) for z in r) + " |" for r in t.itertuples(index=False))


L = ["# Section D results: can the photo alone warn that a heart-rate reading is wrong? (C3)\n",
     "*Generated by `scripts/analysis/section_D.py`. Rules fixed before the results were seen (see the script header).*\n",
     f"## C3 verdict: **{verdict}**\n",
     f"- Trained on {prim['n_train']} images of the first 50 ({prim['n_train_bad']} wrong readings); scored once on {prim['n_test']} images of the new 100 "
     f"({prim['n_bad']} wrong readings; images where the digitiser gave no reading are left out of the primary target).",
     f"- AUC = **{prim['auc']:.3f}** (95% recording-level interval {prim['ci'][0]:.2f} to {prim['ci'][1]:.2f}). Oracle told the exact damage type and level: "
     f"**{prim['oracle']:.3f}** ({prim['ciO'][0]:.2f} to {prim['ciO'][1]:.2f}).",
     f"- Best single score, chosen on the first 50 only: **{prim['best']['score']}** ({prim['best']['direction']}), AUC on the new 100 = {prim['best']['auc_test_new100']}.",
     "- The word 'usable' is not used. The verdict is worded 'within these six damage types' because the scores were designed around the same six damage types.\n",
     "## All analyses\n", md_table(summary) + "\n",
     "## Each score on its own (direction and choice from the first 50)\n", md_table(prim["single"]) + "\n",
     "## Leave-one-damage-type-out (all 150, 13 shared versions): can it warn about a damage type it was never trained on?\n", md_table(lodo) + "\n",
     "## Coverage curve on the new 100: flag the photos with the highest risk\n", md_table(cov) + "\n",
     "## Exploratory: inside one damage type and level (can the scores tell WHICH pages are wrong?)\n", md_table(wd) + "\n",
     "An AUC near 0.5 here means the detector recognises how damaged a page is, not which damaged pages will fail.\n",
     f"## Continuous target: predicted risk vs absolute error (new 100, images with output): Spearman rho = {rho:.3f}\n",
     "## The five scores against absolute heart-rate error (all 150, shared versions; Spearman, recording-level bootstrap)\n", md_table(sc) + "\n",
     "## Not done (limits)\n- 'Unreadable leads' as a feature (saved 12-lead signals exist only for the new 100) and a standard no-reference image-quality baseline.\n"]
open(f"{OUT}/SECTION_D.md", "w", encoding="utf-8").write("\n".join(L))

pd.set_option("display.width", 250)
print("VERDICT:", verdict)
print(summary.to_string(index=False))
print("\nsingle scores:\n", prim["single"].to_string(index=False))
print("\nLODO:\n", lodo.to_string(index=False))
print("\ncoverage:\n", cov.to_string(index=False))
print("\nrho risk vs |error|:", round(rho, 3), "p", prho)
print("\nscores vs error:\n", sc.to_string(index=False))
