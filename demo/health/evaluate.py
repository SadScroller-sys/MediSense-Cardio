"""Test the frozen ECG-pattern model ONCE (rules: docs/plan/analysis_plan_changes.md, 2026-11-15 "Heart health module").
T1 = fold 10 minus our digitised recordings; T2 = clean digitised drawn pages (new 100, fresh F, sealed G); T3 = straightened phone photos (P, Q, G001-G020).
Writes results/health/SECTION_HEALTH.md, health_test_metrics.csv and findings_status.json (what the app may show). Refuses to run twice (rule: run ONCE).
Usage: demo\\.venv-gpu\\Scripts\\python.exe demo/health/evaluate.py"""
import json
import os
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, roc_curve

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")))
from health import data as D  # noqa: E402
from health import model as M  # noqa: E402

OUTF = M.OUT + "health_test_metrics.csv"
if os.path.exists(OUTF) and "--force" not in sys.argv:
    sys.exit("The test was already run once (rule: run ONCE).")
B = 2000
rng = np.random.RandomState(54)
dev = "cuda" if __import__("torch").cuda.is_available() else "cpu"
net, cal = M.load_model(dev)
db, Y = D.load_db()
X = D.load_ptbxl100(db)
ex = D.excluded_ids()
ok = ~db.index.isin(ex)
f9 = np.flatnonzero((db.strat_fold.values == 9) & ok)
f10 = np.flatnonzero((db.strat_fold.values == 10) & ok)


def probs_from_signals(idx):
    Z = np.stack([D.page_layout_from_signal(np.asarray(X[i], np.float32)) for i in idx])
    return M.calibrated(cal, M.logits_from_inputs(net, Z, dev)), M.logits_from_inputs(net, Z, dev)


def ece(p, y, bins=10):
    e, n = 0.0, len(p)
    edges = np.linspace(0, 1, bins + 1)
    for a, b in zip(edges[:-1], edges[1:]):
        m = (p >= a) & ((p < b) if b < 1 else (p <= b))
        if m.any():
            e += m.sum() / n * abs(p[m].mean() - y[m].mean())
    return float(e)


def auc_ci(y, p, groups):
    if y.sum() < 2 or (1 - y).sum() < 2:
        return float("nan"), float("nan"), float("nan")
    a = roc_auc_score(y, p)
    uniq = pd.unique(groups)
    idx = {g: np.flatnonzero(groups == g) for g in uniq}
    vals = []
    for _ in range(B):
        pick = rng.choice(len(uniq), len(uniq), replace=True)
        ix = np.concatenate([idx[uniq[j]] for j in pick])
        if 0 < y[ix].sum() < len(ix):
            vals.append(roc_auc_score(y[ix], p[ix]))
    return float(a), float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


# thresholds: Youden J on fold 9 (the same fold that fixed the calibration), then frozen
P9, _ = probs_from_signals(f9)
thr = {}
for k, c in enumerate(D.CLASSES):
    fpr, tpr, th = roc_curve(Y.values[f9, k], P9[:, k])
    thr[c] = float(th[np.argmax(tpr - fpr)])

sets = {}
P1, _ = probs_from_signals(f10)
sets["T1 fold 10 (benchmark)"] = (P1, Y.values[f10], db.index[f10].values)
ds = D.digitised_sets()
for tag, name in (("T2", "T2 drawn pages, digitised"), ("T3", "T3 straightened phone photos")):
    d = ds[ds.set == tag].reset_index(drop=True)
    Z = np.stack([D.digitised_to_input({k: v for k, v in np.load(p).items()}) for p in d.path])
    P = M.calibrated(cal, M.logits_from_inputs(net, Z, dev))
    sets[name] = (P, Y.loc[d.ecg_id].values, d.group.values)
    pd.DataFrame(np.column_stack([d.name, d.ecg_id, d.group, P]), columns=["name", "ecg_id", "group"] + D.CLASSES).to_csv(M.OUT + f"predictions_{tag}.csv", index=False)

rows = []
for sname, (P, Yv, groups) in sets.items():
    for k, c in enumerate(D.CLASSES):
        y, p = Yv[:, k].astype(int), P[:, k]
        a, lo, hi = auc_ci(y, p, groups)
        pred = p >= thr[c]
        rows.append(dict(set=sname, cls=c, n=len(y), positives=int(y.sum()), clusters=len(pd.unique(groups)), auroc=a, lo95=lo, hi95=hi, ece=ece(p, y), brier=float(np.mean((p - y) ** 2)),
                         sensitivity=float(pred[y == 1].mean()) if y.sum() else float("nan"), specificity=float((~pred[y == 0]).mean()) if (y == 0).sum() else float("nan"), threshold=thr[c]))
T = pd.DataFrame(rows)
T.to_csv(OUTF, index=False)

# --- pass rules (fixed before any result)
status = {}
for c in D.CLASSES:
    t1 = T[(T.set.str.startswith("T1")) & (T.cls == c)].iloc[0]
    t2 = T[(T.set.str.startswith("T2")) & (T.cls == c)].iloc[0]
    t3 = T[(T.set.str.startswith("T3")) & (T.cls == c)].iloc[0]
    drawn = bool(t2.positives >= 20 and t2.auroc >= 0.80 and t2.lo95 > 0.70)
    photo = bool(drawn and t3.positives >= 20 and t3.auroc >= 0.75)
    status[c] = dict(supported_drawn_pages=drawn, supported_phone_photos=photo,
                     testable_drawn=bool(t2.positives >= 20), testable_photos=bool(t3.positives >= 20),
                     show_percentage_photos=bool(photo and t1.ece <= 0.10), show_percentage_drawn=bool(drawn and t1.ece <= 0.10),
                     threshold=thr[c], T1_auroc=t1.auroc, T2_auroc=t2.auroc, T2_lo95=t2.lo95, T3_auroc=t3.auroc, T1_ece=t1.ece)
json.dump(dict(rules="docs/plan/analysis_plan_changes.md 2026-11-15", classes=status), open(M.OUT + "findings_status.json", "w"), indent=1)

md = ["# Section HEALTH: ECG-pattern model, test once (EXPLORATORY; rules logged before training)", "",
      "Rules: `docs/plan/analysis_plan_changes.md`, 'Heart health module'. Model trained once on PTB-XL folds 1-8 minus our digitised recordings, epoch and calibration from fold 9. "
      "Findings are ECG PATTERNS, not cardiac risk (no outcome data exists). The pass rules are the assistant's proposal, not approved by the guide.", ""]
for sname in sets:
    md += [f"## {sname}", "", "| Class | n | Positives | Clusters | AUROC (95% interval) | Calibration error | Brier | Sensitivity | Specificity |", "|---|---|---|---|---|---|---|---|---|"]
    for _, r in T[T.set == sname].iterrows():
        md.append(f"| {r.cls} | {r.n} | {r.positives} | {r.clusters} | {r.auroc:.3f} ({r.lo95:.3f} to {r.hi95:.3f}) | {r.ece:.3f} | {r.brier:.3f} | {r.sensitivity:.2f} | {r.specificity:.2f} |")
    md.append("")
md += ["## What the app may show (pass rules applied)", "", "| Class | Testable on drawn pages | Supported for drawn pages | Testable on photos | Supported for phone photos | Percentage allowed (photos) |", "|---|---|---|---|---|---|"]
for c, s in status.items():
    md.append(f"| {c} | {s['testable_drawn']} | {s['supported_drawn_pages']} | {s['testable_photos']} | {s['supported_phone_photos']} | {s['show_percentage_photos']} |")
md += ["", "Rules: supported for drawn pages = at least 20 positives, AUROC at least 0.80 on T2 and its lower interval end above 0.70; supported for phone photos = that, plus at least 20 positive photos and AUROC at least 0.75 on T3 (point estimate); "
       "a percentage only for a supported finding whose calibration error on T1 is at most 0.10. Decision thresholds = Youden J on fold 9. Intervals: bootstrap over recordings (pages for photos), 2,000 resamples. The two photos of a page are not independent."]
open(M.OUT + "SECTION_HEALTH.md", "w", encoding="utf-8").write("\n".join(md) + "\n")
print("\n".join(md))
