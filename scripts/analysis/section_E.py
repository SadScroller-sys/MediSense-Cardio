"""Section E (MASTER_PLAN 4b item 19): the coverage curve. If the photos with the highest predicted risk are flagged (retake the photo, or a human checks the
reading), how many wrong readings are caught and how many right readings are wrongly flagged? Exploratory; NO statistical guarantee is claimed, and the effect
of a flag on people is untested.

Rules fixed before running (2026-11-07):
  * Risk scores: (A) held-out: logistic regression on the five photo scores trained on the first 50 recordings, scored on the new 100 (same model as C3);
                 (B) grouped 5-fold cross-validation (10 repeats) over all 150 recordings, 13 shared versions each.
  * Primary target: wrong heart rate (> 5 bpm), images with a reading only. Secondary: bad = wrong OR no output (all images).
  * Gate: flag the top 10, 20, 30% of photos by predicted risk. caught = wrong readings flagged / all wrong readings; good flagged = right readings flagged /
    all right readings; wrong among kept = wrong readings among unflagged photos / unflagged photos. 95% intervals: bootstrap over recordings (2,000), the
    flagging quantile recomputed inside every resample.
  * Comparisons: random gate (expected caught = flagged share), oracle gate (told damage type and level; ties broken at random), best single score (blur, chosen on the first 50).
  * Heart-rate false reassurance (true HR outside 60-100 bpm, digitised inside; convention) among the new 100: how many events the gate flags.
Reuses the data preparation and models of scripts/analysis/section_D.py (executed up to its C3 block)."""
import os
import warnings

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

warnings.filterwarnings("ignore")
ROOT = "D:/Capstone Project/"
OUT = ROOT + "results/analysis/"
src = open(ROOT + "scripts/analysis/section_D.py", encoding="utf-8").read().split("# ------------------------------------------------------------------ C3")[0]
exec(compile(src, "section_D_prefix", "exec"))          # defines d, train, test, X_COLS, sig_model, sev_model, target, SHARED, ...
ROOT = "D:/Capstone Project/"                           # section_D defines ROOT/OUT without the trailing slash: reset ours
OUT = ROOT + "results/analysis/"

FRACS = (0.10, 0.20, 0.30)
CURVE = tuple(np.round(np.arange(0.05, 0.55, 0.05), 2))
B = 2000
jit = np.random.RandomState(11)


def flag_top(p, frac):
    """boolean flag of the top frac by p; ties broken by a fixed random jitter so a tied score never flags more than asked."""
    n = int(np.ceil(frac * len(p)))
    order = np.lexsort((jit_cache[id(p)], -p)) if id(p) in jit_cache else np.argsort(-p, kind="stable")
    f = np.zeros(len(p), bool)
    f[order[:n]] = True
    return f


jit_cache = {}


def metrics(y, p, frac):
    f = flag_top(p, frac)
    nb, ng = y.sum(), (y == 0).sum()
    return dict(caught=f[y == 1].sum() / nb if nb else np.nan, good_flagged=f[y == 0].sum() / ng if ng else np.nan,
                kept_wrong=y[~f].mean() if (~f).any() else np.nan)


def gate_table(y, p, groups, label, fracs=FRACS, boot=True, seed=5):
    jit_cache[id(p)] = jit.rand(len(p))
    rs = np.random.RandomState(seed)
    recs = np.unique(groups)
    idx = {g: np.where(groups == g)[0] for g in recs}
    rows = []
    boots = {fr: [] for fr in fracs}
    if boot:
        for _ in range(B):
            pick = rs.choice(recs, len(recs), replace=True)
            ii = np.concatenate([idx[g] for g in pick])
            yy, pp = y[ii], p[ii]
            if yy.sum() == 0 or (yy == 0).sum() == 0:
                continue
            jit_cache[id(pp)] = jit_cache[id(p)][ii]
            for fr in fracs:
                boots[fr].append(metrics(yy, pp, fr))
            del jit_cache[id(pp)]
    for fr in fracs:
        m = metrics(y, p, fr)
        r = dict(gate=label, flag_top=f"{int(fr * 100)}%")
        for k, fmt in (("caught", "{:.0f}%"), ("good_flagged", "{:.0f}%"), ("kept_wrong", "{:.1f}%")):
            r[k] = fmt.format(100 * m[k])
            if boot and boots[fr]:
                lo, hi = np.nanpercentile([b[k] for b in boots[fr]], [2.5, 97.5])
                r[k] += f" ({100 * lo:.0f}-{100 * hi:.0f})" if k != "kept_wrong" else f" ({100 * lo:.1f}-{100 * hi:.1f})"
        r["wrong_overall"] = f"{100 * y.mean():.1f}%"
        r["random_gate_caught"] = f"{int(fr * 100)}%"
        rows.append(r)
    return pd.DataFrame(rows)


def grouped_oof(X, y, groups, n_splits=5, repeats=10, seed=0):
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
            p[tst] = sig_model().fit(X[trn], y[trn]).predict_proba(X[tst])[:, 1]
        tot += p
    return tot / repeats


# ------------------------------------------------------------------ (A) held-out: first 50 -> new 100
tabs = []
tr, ytr = target(train, "primary")
te, yte = target(test, "primary")
pA = sig_model().fit(tr[X_COLS], ytr).predict_proba(te[X_COLS])[:, 1]
gA = te.record.values
tabs.append(gate_table(yte, pA, gA, "A. photo scores, trained on first 50, scored on new 100"))
# oracle and best single score (same training data)
pO = sev_model().fit(tr[["axlv"]], ytr).predict_proba(te[["axlv"]])[:, 1]
tabs.append(gate_table(yte, pO, gA, "oracle: told damage type and level (new 100)"))
single = {f: roc_auc_score(ytr, tr[f].fillna(tr[f].median())) for f in X_COLS}
best = max(single, key=lambda f: max(single[f], 1 - single[f]))
sign = 1 if single[best] >= 0.5 else -1
pS = sign * te[best].fillna(tr[best].median()).values
tabs.append(gate_table(yte, pS, gA, f"best single score on the first 50: {best} (new 100)"))
heldout = pd.concat(tabs, ignore_index=True)

# secondary target on the new 100
tr2, ytr2 = target(train, "secondary")
te2, yte2 = target(test, "secondary")
pA2 = sig_model().fit(tr2[X_COLS], ytr2).predict_proba(te2[X_COLS])[:, 1]
sec = gate_table(yte2, pA2, te2.record.values, "secondary target (wrong OR no output), held-out new 100")

# ------------------------------------------------------------------ (B) grouped CV on all 150 (13 shared versions)
pool = d[d.level.isin(SHARED)].reset_index(drop=True)
poolp, ypool = target(pool, "primary")
poolp = poolp.reset_index(drop=True)
pB = grouped_oof(poolp[X_COLS], ypool, poolp.record.values)
cvtab = gate_table(ypool, pB, poolp.record.values, "B. grouped cross-validation, all 150 recordings")

# ------------------------------------------------------------------ what gets flagged (new 100, held-out risk, 20%)
comp = te.assign(p=pA, y=yte)
jit_cache[id(pA)] = jit.rand(len(pA))
rows = []
for fr in (0.10, 0.20, 0.30):
    comp[f"f{int(fr * 100)}"] = flag_top(pA, fr)
for (ax, lv), g in comp.groupby(["axis", "level"]):
    rows.append(dict(damage=f"{ax} {int(lv)}", photos=len(g), wrong_readings=int(g.y.sum()), flagged_at_10=int(g.f10.sum()), flagged_at_20=int(g.f20.sum()),
                     flagged_at_30=int(g.f30.sum()), wrong_caught_at_20=int((g.f20 & (g.y == 1)).sum())))
compo = pd.DataFrame(rows).sort_values("wrong_readings", ascending=False).reset_index(drop=True)

# ------------------------------------------------------------------ heart-rate false reassurance among the new 100 (images with a reading)
fr_ = comp.merge(test[["variant_id", "dig_hr"]].assign(dig=lambda x: x.dig_hr)[["variant_id", "dig"]], on="variant_id", how="left")
gtv = pd.concat([pd.read_csv(ROOT + "results/extension/results_extension.csv")[["variant_id", "gt_hr"]]]).drop_duplicates("variant_id")
fr_ = fr_.merge(gtv, on="variant_id", how="left")
fr_["fr_event"] = (~fr_.gt_hr.between(60, 100)) & fr_.dig.between(60, 100)
nev = int(fr_.fr_event.sum())
fr_rows = []
for fr in (10, 20, 30):
    fr_rows.append(dict(flag_top=f"{fr}%", false_reassurance_events=nev, flagged=int(fr_[fr_.fr_event][f"f{fr}"].sum())))
frt = pd.DataFrame(fr_rows)

# ------------------------------------------------------------------ coverage curve for a figure (5-50%)
curve = []
for name, y_, p_, g_ in (("held-out new 100", yte, pA, gA), ("grouped CV all 150", ypool, pB, poolp.record.values)):
    jit_cache[id(p_)] = jit.rand(len(p_))
    for fr in CURVE:
        m = metrics(y_, p_, float(fr))
        curve.append(dict(setting=name, flag_top_pct=int(round(fr * 100)), caught_pct=round(100 * m["caught"], 1), good_flagged_pct=round(100 * m["good_flagged"], 1),
                          kept_wrong_pct=round(100 * m["kept_wrong"], 2)))
curve = pd.DataFrame(curve)

heldout.to_csv(OUT + "sectionE_gate_heldout_new100.csv", index=False)
cvtab.to_csv(OUT + "sectionE_gate_cv_all150.csv", index=False)
sec.to_csv(OUT + "sectionE_gate_secondary.csv", index=False)
compo.to_csv(OUT + "sectionE_what_is_flagged.csv", index=False)
frt.to_csv(OUT + "sectionE_hr_false_reassurance.csv", index=False)
curve.to_csv(OUT + "sectionE_coverage_curve.csv", index=False)


def md_table(t):
    head = "| " + " | ".join(map(str, t.columns)) + " |\n|" + "---|" * len(t.columns) + "\n"
    return head + "\n".join("| " + " | ".join(str(z) for z in r) + " |" for r in t.itertuples(index=False))


L = ["# Section E results: the coverage curve (what a photo gate would do)\n",
     "*Generated by `scripts/analysis/section_E.py`. Exploratory. **No statistical guarantee is claimed.** The action after a flag is: retake the photo, or have a person check the reading. "
     "Its effect on people and on care is untested.*\n",
     "How to read: flag the photos with the highest predicted risk. 'caught' = share of all wrong readings that were flagged; 'good flagged' = share of right readings wrongly flagged "
     "(the cost: needless retakes); 'kept_wrong' = wrong-reading rate among the photos NOT flagged (compare with 'wrong_overall'). A random gate would catch exactly the flagged share. "
     "95% intervals: bootstrap over recordings.\n",
     "## Held-out test: trained on the first 50, scored on the new 100 (primary target: wrong heart rate > 5 bpm, images with a reading)\n", md_table(heldout) + "\n",
     "## All 150 recordings, grouped cross-validation (13 shared versions)\n", md_table(cvtab) + "\n",
     "## Secondary target: wrong OR no output (held-out, new 100)\n", md_table(sec) + "\n",
     "## What the gate flags (new 100, held-out risk): by damage type and level, sorted by wrong readings\n", md_table(compo) + "\n",
     f"## Heart-rate false reassurance in the new 100 ({nev} events: true heart rate outside 60-100 bpm, digitised inside)\n", md_table(frt) + "\n",
     "Descriptive only: the number of events is small.\n",
     "## Limits\n- The detector recognises how damaged a page is, not which damaged pages will fail (Section D: AUC 0.52 inside low-resolution level 5), so the gate mostly removes the heavily damaged photo types.\n"
     "- Simulated damage on computer-drawn pages, six damage types the scores were designed around; no real-photo problems (glare, folds, perspective) are covered.\n"
     "- A flagged photo is not 'wrong': at 20% flagged, most flagged photos still give a right reading (see 'good flagged').\n"]
open(OUT + "SECTION_E.md", "w", encoding="utf-8").write("\n".join(L))

pd.set_option("display.width", 250)
pd.set_option("display.max_colwidth", 60)
print(heldout.to_string(index=False)); print()
print(cvtab.to_string(index=False)); print()
print(sec.to_string(index=False)); print()
print(compo.head(8).to_string(index=False)); print()
print(frt.to_string(index=False)); print("events", nev)
print(curve[curve.setting == "held-out new 100"].to_string(index=False))
