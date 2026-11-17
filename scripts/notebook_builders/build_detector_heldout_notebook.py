"""Builds colab/MediSense_Cardio_Detector_Heldout.ipynb -- the stronger test of the photo-quality detector.

Why this exists: the Calibration notebook scored the detector on only 6 rare false-reassurance events, fit
and scored on the SAME data (AUC 0.785, optimistic). This notebook asks the same question properly:
  - a target with many more cases ("the reading is badly wrong" or unreadable),
  - whole RECORDS held out (all 31 versions of a recording stay together, never split across train/test),
  - honest baselines: each signal alone, and an "oracle" that is told the exact damage type and level,
  - a leave-one-damage-type-out stress test,
  - a demo of how much a careless random split would inflate the score.

The damage and signal code (Steps 1-3) is copied VERBATIM from the saved MediSense_Cardio_Calibration.ipynb,
so the signals are identical to the ones already reported. This builder only READS that notebook.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
COLAB = os.path.join(HERE, "..", "..", "colab")
SRC = os.path.join(COLAB, "MediSense_Cardio_Calibration.ipynb")
OUT = os.path.join(COLAB, "MediSense_Cardio_Detector_Heldout.ipynb")


def md(*lines):
    return {"cell_type": "markdown", "metadata": {}, "source": [l + "\n" for l in lines]}


def code(*lines):
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [],
            "source": [l + "\n" for l in lines]}


src = json.load(open(SRC, encoding="utf-8"))["cells"]
# cells 1..6 of the saved Calibration notebook = Step 1 (load), Step 2 (damage code), Step 3 (signals)
reused = []
for c in src[1:7]:
    c = dict(c)
    if c["cell_type"] == "code":
        c["outputs"] = []
        c["execution_count"] = None
    reused.append(c)
assert "def compute_signals" in "".join(reused[5]["source"]), "unexpected Calibration notebook layout"
assert "def degrade_blur" in "".join(reused[3]["source"]), "unexpected Calibration notebook layout"

cells = []
cells.append(md(
    "# MediSense-Cardio -- A stronger test of the photo-quality detector",
    "",
    "**The question:** from the photo alone, can we tell that the digitiser's reading is probably wrong?",
    "",
    "**Why the earlier test was weak:** the Calibration notebook scored the detector on only **6 rare",
    "false-reassurance events**, and it was fit and scored on the same data (AUC 0.785). That number is",
    "optimistic. This notebook asks the same question more carefully:",
    "",
    "1. **A bigger target** -- \"the reading is badly wrong, or could not be read at all\". This has many more",
    "   cases than 6, so the result is far less shaky.",
    "2. **Whole recordings are held out.** All 31 damaged versions of one recording stay together, either all",
    "   in training or all in testing. Otherwise the model could recognise a recording instead of the damage.",
    "3. **Honest comparisons** -- each signal alone, and an \"oracle\" that is simply told the exact damage",
    "   type and level (the best a damage-aware model could do).",
    "4. **A stress test** -- train without one damage type, then test on that unseen type.",
    "",
    "**Run time:** Step 3 is the slow cell (about 20 minutes on Colab's CPU). The analysis after it takes a few",
    "minutes. Steps 1 to 3 are the same code as the Calibration notebook, so the signals are identical.",
    "",
    "**Everything is saved to Drive** (`quality_signals_v2.csv`, `detector_heldout_results.csv`,",
    "`detector_heldout_roc.png`) so the analysis can be repeated without redoing Step 3.",
))
cells.extend(reused)

cells.append(md(
    "## Step 4: join the signals to the real errors, save them, and define what counts as a bad reading",
    "",
    "**What this does:** matches each picture's signals to its real measured error. It then saves the signals",
    "to Drive. It keeps only the *reliable* records, using the same rule as the main study (at most 6 of 31",
    "versions unreadable). Finally it defines the targets **before looking at any model result**, so none of",
    "them can be picked because it happens to look good.",
    "",
    "A reading counts as **bad** if it could not be read, or if it is wrong by more than a fixed tolerance:",
    "heart rate by more than 5 bpm (and, as a stricter check, 10 bpm); QTc by more than 60 ms; QRS by more than",
    "100 ms. The QTc and QRS tolerances are roughly the 95th percentile of the error on the *undamaged*",
    "pictures, rounded -- in other words \"worse than almost every clean picture\". The first target (heart rate,",
    "5 bpm) is the **primary** one; the others are reported the same way, whatever they show.",
))
cells.append(code(
    "import numpy as np",
    "",
    "merged = results.merge(signals_df, on='variant_id', how='inner', suffixes=('', '_sig'))",
    "print(f'Matched {len(merged)} of {len(results)} real results rows to a computed signal row.')",
    "assert len(merged) == len(results), 'Join failed -- fix this before trusting anything below.'",
    "",
    "SIGNALS_PATH = f'{STUDY_DIR}/quality_signals_v2.csv'",
    "signals_df.to_csv(SIGNALS_PATH, index=False)",
    "print(f'Saved {SIGNALS_PATH}: {os.path.getsize(SIGNALS_PATH)/1024:.0f} KB, exists on Drive = {os.path.exists(SIGNALS_PATH)}')",
    "",
    "# Same reliability rule as the main study: drop records with more than 6 of 31 versions unreadable.",
    "per_record_unreadable = merged.groupby('record')['dig_hr'].apply(lambda s: s.isna().sum())",
    "reliable_records = sorted(per_record_unreadable[per_record_unreadable <= 6].index)",
    "m = merged[merged['record'].isin(reliable_records)].reset_index(drop=True)",
    "print(f'Reliable records: {len(reliable_records)} of {merged[\"record\"].nunique()}  ->  {len(m)} tests')",
    "",
    "unread = m['dig_hr'].isna()",
    "TARGETS = {",
    "    'HR wrong by >5 bpm (or unreadable)':   unread | (m['diff_bpm'].abs() > 5),",
    "    'HR wrong by >10 bpm (or unreadable)':  unread | (m['diff_bpm'].abs() > 10),",
    "    'QTc wrong by >60 ms (or missing)':     m['diff_qtc_ms'].isna() | (m['diff_qtc_ms'].abs() > 60),",
    "    'QRS wrong by >100 ms (or missing)':    m['diff_qrs_ms'].isna() | (m['diff_qrs_ms'].abs() > 100),",
    "}",
    "PRIMARY = 'HR wrong by >5 bpm (or unreadable)'",
    "print()",
    "for name, y_ in TARGETS.items():",
    "    print(f'{name:40s} bad readings: {int(y_.sum()):4d} of {len(y_)}  ({100*y_.mean():.1f}%)')",
    "",
    "# The five signals. Blur varies over several orders of magnitude, so it is put on a log scale for the",
    "# linear model (this does not depend on the data, so it cannot leak anything).",
    "FEATS = ['blur_score', 'skew_deg', 'resolution_score', 'contrast_score', 'blockiness_score']",
    "X_all = m[FEATS].copy()",
    "X_all['blur_score'] = np.log10(X_all['blur_score'] + 1)",
    "sev_all = (m['axis'] + '_' + m['level'].astype(str)).to_frame('axis_level')   # for the oracle baseline",
    "groups_all = m['record'].values",
    "axes_all = m['axis'].values",
))

cells.append(md(
    "## Step 5: the held-out test",
    "",
    "**What this does:** for each target it trains a small logistic regression on the five signals and scores it",
    "**only on recordings it never saw** (5 folds of recordings, repeated 10 times with different random fold",
    "assignments, predictions averaged). It reports the AUC (0.5 = guessing, 1.0 = perfect) with a 95% interval",
    "that is computed by re-drawing whole *recordings* (so the 31 versions of a recording are never treated as",
    "31 independent samples).",
    "",
    "Two comparisons put the number in context:",
    "- **Best single signal** -- is the combination of five signals any better than the best one on its own?",
    "- **Oracle severity** -- a model told the exact damage type and level of every picture. If the signals get",
    "  close to this, they recover most of what is knowable about how damaged the picture is.",
))
cells.append(code(
    "from sklearn.pipeline import make_pipeline",
    "from sklearn.impute import SimpleImputer",
    "from sklearn.preprocessing import StandardScaler, OneHotEncoder",
    "from sklearn.linear_model import LogisticRegression",
    "from sklearn.metrics import roc_auc_score, roc_curve",
    "",
    "def signal_model():",
    "    return make_pipeline(SimpleImputer(strategy='median'), StandardScaler(),",
    "                         LogisticRegression(max_iter=1000, class_weight='balanced'))",
    "",
    "def severity_model():   # the oracle: told the exact damage type and level",
    "    return make_pipeline(OneHotEncoder(handle_unknown='ignore'),",
    "                         LogisticRegression(max_iter=1000, class_weight='balanced'))",
    "",
    "def grouped_oof(X, y, make_model, groups, n_splits=5, repeats=10, seed=0):",
    "    \"\"\"Out-of-fold predictions where whole recordings are held out. Returns (mean prediction, AUC per repeat).\"\"\"",
    "    rng = np.random.RandomState(seed)",
    "    recs = np.unique(groups)",
    "    total = np.zeros(len(y)); aucs = []",
    "    for _ in range(repeats):",
    "        perm = rng.permutation(recs)",
    "        fold_of = {r: i % n_splits for i, r in enumerate(perm)}",
    "        folds = np.array([fold_of[g] for g in groups])",
    "        p = np.full(len(y), np.nan)",
    "        for f in range(n_splits):",
    "            tr, te = folds != f, folds == f",
    "            if y[tr].sum() == 0 or y[tr].sum() == tr.sum():",
    "                p[te] = y[tr].mean()",
    "                continue",
    "            p[te] = make_model().fit(X[tr], y[tr]).predict_proba(X[te])[:, 1]",
    "        aucs.append(roc_auc_score(y, p)); total += p",
    "    return total / repeats, np.array(aucs)",
    "",
    "def cluster_bootstrap_auc(y, p, groups, n_boot=1000, seed=1):",
    "    rng = np.random.RandomState(seed)",
    "    recs = np.unique(groups)",
    "    idx_of = {r: np.where(groups == r)[0] for r in recs}",
    "    out = []",
    "    for _ in range(n_boot):",
    "        pick = rng.choice(recs, size=len(recs), replace=True)",
    "        idx = np.concatenate([idx_of[r] for r in pick])",
    "        if y[idx].min() == y[idx].max():",
    "            continue",
    "        out.append(roc_auc_score(y[idx], p[idx]))",
    "    return np.percentile(out, [2.5, 97.5])",
    "",
    "def evaluate(label, y_bool, keep):",
    "    \"\"\"Run the whole comparison on the rows selected by `keep` (a boolean array).\"\"\"",
    "    y = np.asarray(y_bool).astype(int)[keep]",
    "    Xs = X_all[keep].reset_index(drop=True)",
    "    sev = sev_all[keep].reset_index(drop=True)",
    "    gs = groups_all[keep]",
    "    p_sig, a_sig = grouped_oof(Xs, y, signal_model, gs)",
    "    lo, hi = cluster_bootstrap_auc(y, p_sig, gs)",
    "    single_auc, single_pred = {}, {}",
    "    for f in FEATS:",
    "        pf, _ = grouped_oof(Xs[[f]], y, signal_model, gs, repeats=5)",
    "        single_auc[f] = roc_auc_score(y, pf); single_pred[f] = pf",
    "    best = max(single_auc, key=single_auc.get)",
    "    p_sev, a_sev = grouped_oof(sev, y, severity_model, gs)",
    "    row = {'target': label, 'bad readings': f'{int(y.sum())} of {len(y)}',",
    "           'AUC: 5 signals': round(roc_auc_score(y, p_sig), 3), '95% interval': f'{lo:.2f} to {hi:.2f}',",
    "           'best single signal': f'{best} ({single_auc[best]:.3f})',",
    "           'AUC: oracle severity': round(roc_auc_score(y, p_sev), 3)}",
    "    return row, dict(y=y, p_sig=p_sig, p_best=single_pred[best], best=best, p_sev=p_sev)",
    "",
    "all_rows = np.ones(len(m), dtype=bool)",
    "table, store = [], {}",
    "for name, y_ in TARGETS.items():",
    "    row, st = evaluate(name, y_.values, all_rows)",
    "    table.append(row); store[name] = st",
    "    print('done:', name)",
    "",
    "# Secondary check: drop recordings that are already wrong on their own CLEAN picture, so the remaining",
    "# bad readings are much more likely to be caused by the damage and not by a hard recording.",
    "clean_bad = pd.Series(TARGETS[PRIMARY].values, index=m.index)[m['axis'] == 'clean']",
    "clean_bad.index = m.loc[clean_bad.index, 'record']",
    "hard = set(clean_bad[clean_bad].index)",
    "keep_damage_only = ~m['record'].isin(hard).values",
    "row, st = evaluate(PRIMARY + '  [recordings already wrong when clean removed]', TARGETS[PRIMARY].values, keep_damage_only)",
    "table.append(row)",
    "print(f'done: damage-only check (removed {len(hard)} hard recordings)')",
    "",
    "results_table = pd.DataFrame(table)",
    "pd.set_option('display.max_colwidth', 80); pd.set_option('display.width', 250)",
    "display(results_table)",
    "RESULTS_OUT = f'{STUDY_DIR}/detector_heldout_results.csv'",
    "results_table.to_csv(RESULTS_OUT, index=False)",
    "print(f'Saved {RESULTS_OUT}, exists on Drive = {os.path.exists(RESULTS_OUT)}')",
))

cells.append(md(
    "## Step 6: how much would a careless random split inflate the score?",
    "",
    "**What this does:** repeats the primary test but splits **pictures at random** (so versions of the same",
    "recording land in both training and testing). A big gap between this number and the held-out number",
    "means the model was partly recognising recordings, not damage -- which is why the held-out number is the",
    "one to trust.",
))
cells.append(code(
    "from sklearn.model_selection import StratifiedKFold, cross_val_predict",
    "",
    "y_primary = store[PRIMARY]['y']",
    "p_leaky = cross_val_predict(signal_model(), X_all, y_primary,",
    "                            cv=StratifiedKFold(5, shuffle=True, random_state=0), method='predict_proba')[:, 1]",
    "auc_leaky = roc_auc_score(y_primary, p_leaky)",
    "auc_held = roc_auc_score(y_primary, store[PRIMARY]['p_sig'])",
    "print(f'Pictures split at random (NOT by recording):  AUC = {auc_leaky:.3f}   <- inflated, do not report')",
    "print(f'Whole recordings held out (the real test):    AUC = {auc_held:.3f}   <- the number to trust')",
))

cells.append(md(
    "## Step 7: stress test -- an unseen damage type",
    "",
    "**What this does:** for each damage type in turn, train on the other five (plus the clean pictures), then",
    "test on the held-out damage type, on held-out recordings. This asks: *can the detector warn about a kind of",
    "damage it was never trained on?* The signals were designed around these same six damage types, so a",
    "weak result here is a warning that real-world photo problems (glare, folds, perspective) are not covered.",
))
cells.append(code(
    "def leave_one_damage_out(X, y, groups, axes, n_splits=5, seed=0):",
    "    rng = np.random.RandomState(seed)",
    "    recs = np.unique(groups); perm = rng.permutation(recs)",
    "    fold_of = {r: i % n_splits for i, r in enumerate(perm)}",
    "    folds = np.array([fold_of[g] for g in groups])",
    "    out = []",
    "    for ax in sorted(set(axes) - {'clean'}):",
    "        p = np.full(len(y), np.nan)",
    "        for f in range(n_splits):",
    "            tr = (folds != f) & (axes != ax)",
    "            te = (folds == f) & (axes == ax)",
    "            if y[tr].sum() == 0:",
    "                continue",
    "            p[te] = signal_model().fit(X[tr], y[tr]).predict_proba(X[te])[:, 1]",
    "        mask = axes == ax",
    "        yy, pp = y[mask], p[mask]",
    "        n_bad = int(yy.sum())",
    "        auc = roc_auc_score(yy, pp) if 0 < n_bad < len(yy) else float('nan')",
    "        out.append({'unseen damage type': ax, 'bad readings': f'{n_bad} of {len(yy)}',",
    "                    'AUC on unseen type': 'too few bad readings' if n_bad < 8 else round(auc, 3)})",
    "    return pd.DataFrame(out)",
    "",
    "lodo = leave_one_damage_out(X_all, y_primary, groups_all, axes_all)",
    "display(lodo)",
))

cells.append(md(
    "## Step 8: what would a warning gate actually do?",
    "",
    "**What this does:** takes the held-out predictions for the primary target and asks: *if we flag the most",
    "suspicious 10%, 20% or 30% of pictures, how many of the bad readings do we catch, and how many good",
    "readings do we wrongly flag?* Then it draws the ROC curves and saves the picture to Drive.",
))
cells.append(code(
    "s = store[PRIMARY]",
    "gate = []",
    "for frac in (0.10, 0.20, 0.30):",
    "    flag = s['p_sig'] >= np.quantile(s['p_sig'], 1 - frac)",
    "    gate.append({'flag the most suspicious': f'{frac:.0%} of pictures',",
    "                 'bad readings caught': f\"{100 * flag[s['y'] == 1].mean():.0f}%\",",
    "                 'good readings wrongly flagged': f\"{100 * flag[s['y'] == 0].mean():.0f}%\"})",
    "display(pd.DataFrame(gate))",
    "",
    "import matplotlib.pyplot as plt",
    "fig, ax = plt.subplots(figsize=(6.5, 6.5))",
    "for label, p in [('5 photo signals (recordings held out)', s['p_sig']),",
    "                 (f\"best single signal: {s['best']}\", s['p_best']),",
    "                 ('oracle: told the exact damage type and level', s['p_sev'])]:",
    "    fpr, tpr, _ = roc_curve(s['y'], p)",
    "    ax.plot(fpr, tpr, lw=2, label=f'{label}  (AUC {roc_auc_score(s[\"y\"], p):.2f})')",
    "ax.plot([0, 1], [0, 1], 'k--', label='guessing (AUC 0.50)')",
    "ax.set_xlabel('good readings wrongly flagged'); ax.set_ylabel('bad readings caught')",
    "ax.set_title('Can the photo alone warn that the reading is wrong?\\n(heart rate off by >5 bpm or unreadable)')",
    "ax.legend(loc='lower right', fontsize=8); ax.grid(alpha=0.3)",
    "ROC_OUT = f'{STUDY_DIR}/detector_heldout_roc.png'",
    "plt.savefig(ROC_OUT, dpi=150, bbox_inches='tight')",
    "print(f'Saved {ROC_OUT}, exists on Drive = {os.path.exists(ROC_OUT)}')",
    "plt.show()",
))

cells.append(md(
    "## How to read the results -- and what this still does NOT show",
    "",
    "- **AUC** is the chance that a randomly chosen bad reading gets a higher warning score than a randomly",
    "  chosen good one. 0.5 is guessing; 1.0 is perfect.",
    "- Compare **5 signals** with **oracle severity**. If the signals are far below the oracle, the photo",
    "  signals are missing information about the damage. If they are close, the signals recover most of what",
    "  can be known.",
    "- Compare the **held-out** AUC with the **random-split** AUC. The gap shows how much a careless test",
    "  would have flattered the detector.",
    "- **Still true after this test:** there are only 49 recordings; the damage is simulated on computer-drawn",
    "  pages, not real phone photos; one digitiser was tested; and the signals were designed around the same",
    "  six damage types that were injected. A good number here is evidence for the *prototype*, not proof that",
    "  it works on real photos.",
    "- The earlier AUC of 0.785 (6 events, same data) should not be quoted as a held-out result.",
))

nb = {
    "cells": cells,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "name": "python3"},
        "language_info": {"name": "python"},
        "colab": {"provenance": [], "name": "MediSense_Cardio_Detector_Heldout.ipynb"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1)
print("wrote", os.path.abspath(OUT), "with", len(cells), "cells")
