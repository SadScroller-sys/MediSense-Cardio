"""Section N (EXPLORATORY): can the five photo scores predict failure on the REAL captures when trained on real captures (cross-validated by recording)? Rules: docs/plan/analysis_plan_changes.md 2026-11-08."""
import warnings

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

warnings.filterwarnings("ignore")
ROOT = "D:/Capstone Project/"
OUT = ROOT + "results/analysis/"
FEATS = ["blur_log", "skew_deg", "resolution_score", "contrast_score", "blockiness_score"]
J = pd.read_csv(OUT + "sectionJ_remeasured.csv")
J = J[J.set == "armC_new100"]
q = pd.read_csv(ROOT + "results/armCext/armCext_quality_signals_all.csv")
q["blur_log"] = np.log10(q.blur_score + 1)
d = J.merge(q[["variant_id"] + FEATS], on="variant_id").reset_index(drop=True)
assert len(d) == 900
d["none"] = d.dig_hr.isna()
d["wrong_c"] = d.diff_clean > 5
d["bad_c"] = d.none | d.wrong_c
d["rec"] = d.record.astype(str)


def sig():
    return make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), LogisticRegression(max_iter=1000, class_weight="balanced"))


def orc():
    return make_pipeline(OneHotEncoder(handle_unknown="ignore"), LogisticRegression(max_iter=1000, class_weight="balanced"))


def folds(groups, seed):
    r = np.random.RandomState(seed)
    perm = r.permutation(np.unique(groups))
    m = {g: i % 5 for i, g in enumerate(perm)}
    return np.array([m[g] for g in groups])


def oof(X, yy, groups, model, repeats=10):
    tot = np.zeros(len(yy))
    for rep in range(repeats):
        f = folds(groups, rep)
        p = np.full(len(yy), np.nan)
        for k in range(5):
            tr, te = f != k, f == k
            p[te] = model().fit(X[tr], yy[tr]).predict_proba(X[te])[:, 1]
        tot += p
    return tot / repeats


def auc_ci(yy, p, groups, B=1000, seed=1):
    r = np.random.RandomState(seed)
    recs = np.unique(groups)
    idx = {g: np.where(groups == g)[0] for g in recs}
    v = []
    for _ in range(B):
        ii = np.concatenate([idx[g] for g in r.choice(recs, len(recs), replace=True)])
        if yy[ii].min() == yy[ii].max():
            continue
        v.append(roc_auc_score(yy[ii], p[ii]))
    return roc_auc_score(yy, p), np.percentile(v, [2.5, 97.5])


rows = []
for lab, sub, tcol in (("T1 no output (all 900 images)", d, "none"), ("T2 wrong HR among images with output", d[~d.none], "wrong_c"),
                       ("T3 no output or wrong HR (all 900)", d, "bad_c"), ("T1 inside screen photos only (C4)", d[d.axis == "C4_phone_photo_screen"], "none"),
                       ("T3 without screen photos", d[d.axis != "C4_phone_photo_screen"], "bad_c")):
    sub = sub.reset_index(drop=True)
    yy = sub[tcol].astype(int).values
    g = sub.rec.values
    p1 = oof(sub[FEATS], yy, g, sig)
    a1, c1 = auc_ci(yy, p1, g)
    r = dict(target=lab, images=len(sub), events=int(yy.sum()), photo_scores=f"{a1:.3f} ({c1[0]:.2f} to {c1[1]:.2f})")
    if sub.axis.nunique() > 1:
        sub = sub.copy()
        p2 = oof(sub[["axis"]], yy, g, orc)
        a2, c2 = auc_ci(yy, p2, g)
        r["oracle_capture_type"] = f"{a2:.3f} ({c2[0]:.2f} to {c2[1]:.2f})"
    else:
        r["oracle_capture_type"] = "n/a (one type)"
    rows.append(r)
tab = pd.DataFrame(rows)
tab.to_csv(OUT + "sectionN_real_photo.csv", index=False)
# can the photo scores tell the capture type?
ct = []
for ax in sorted(d.axis.unique()):
    yy = (d.axis == ax).astype(int).values
    p = oof(d[FEATS], yy, d.rec.values, sig, repeats=3)
    ct.append(dict(capture=ax, auc_identify_this_capture_type=round(roc_auc_score(yy, p), 3)))
ct = pd.DataFrame(ct)
ct.to_csv(OUT + "sectionN_capture_type_identifiable.csv", index=False)
pd.set_option("display.width", 250)
pd.set_option("display.max_colwidth", 60)
print(tab.to_string(index=False))
print()
print(ct.to_string(index=False))
