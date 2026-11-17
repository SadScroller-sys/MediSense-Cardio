"""MORE DISEASE FINDINGS: test the FROZEN model ONCE (rules: docs/plan/analysis_plan_changes.md, 2026-11-16 + Amendment 1). Refuses to run twice.
T1 = fold 10 (A) or the CODE-15% test split, patient bucket >= 80 (B); T2 = 300 digitised drawn pages; T3 = 140 straightened phone photos (labels from PTB-XL codes; mapping in demo/health/find2.py).
Decision thresholds = Youden J on the validation fold/split. Pass rules as the first findings model: supported on drawn pages = at least 20 positives in T2, AUROC >= 0.80, lower end > 0.70; supported on photos = that plus at least 20 positive photos
and AUROC >= 0.75 on T3. Writes results/find2_<A|B>/SECTION_FIND2_<A|B>.md, test_metrics.csv, status.json.
Usage: demo\\.venv-gpu\\Scripts\\python.exe -I scripts/analysis/section_FIND2_test.py A|B"""
import json
import os
import sys

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import roc_auc_score, roc_curve

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "demo"))
from health import data as D  # noqa: E402
from health import find2 as F  # noqa: E402
from health import model as M  # noqa: E402

WHICH = sys.argv[1]
assert WHICH in ("A", "B")
OUT = F.OUT_A if WHICH == "A" else F.OUT_B
NAMES = F.A_CODES if WHICH == "A" else F.B_LABELS
DESC = F.A_NAMES if WHICH == "A" else F.B_NAMES
OUTF = OUT + "test_metrics.csv"
if os.path.exists(OUTF) and "--force" not in sys.argv:
    sys.exit("The test was already run once (rule: run ONCE).")
dev = "cuda" if torch.cuda.is_available() else "cpu"
cal = json.load(open(OUT + "calibration.json"))
K = len(NAMES)
net = M.EcgNet(n_out=K).to(dev)
net.load_state_dict(torch.load(OUT + "model.pt", map_location=dev))
net.eval()
mask = M.layout_masks(dev)
BOOT = 2000 if WHICH == "A" else 1000
rng = np.random.RandomState(54)
a_ = np.array([cal["platt"][c]["a"] for c in NAMES])
b_ = np.array([cal["platt"][c]["b"] for c in NAMES])


@torch.no_grad()
def probs_from_array(Xarr, idx=None, bs=512):
    out = []
    n = len(Xarr) if idx is None else len(idx)
    for i in range(0, n, bs):
        ii = np.arange(i, min(i + bs, n)) if idx is None else np.sort(idx[i:i + bs])
        xb = torch.from_numpy(np.asarray(Xarr[ii], np.float32)).to(dev)
        out.append(net(M.make_input(xb, mask)).cpu().numpy())
    lg = np.concatenate(out)
    return 1 / (1 + np.exp(-(lg * a_ + b_)))


@torch.no_grad()
def probs_from_x24(Z, bs=256):
    out = []
    for i in range(0, len(Z), bs):
        out.append(net(torch.from_numpy(np.ascontiguousarray(Z[i:i + bs])).to(dev)).cpu().numpy())
    lg = np.concatenate(out)
    return 1 / (1 + np.exp(-(lg * a_ + b_)))


def ece(p, y, bins=10):
    e, n = 0.0, len(p)
    edges = np.linspace(0, 1, bins + 1)
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (p >= lo) & ((p < hi) if hi < 1 else (p <= hi))
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
    for _ in range(BOOT):
        pick = rng.choice(len(uniq), len(uniq), replace=True)
        ix = np.concatenate([idx[uniq[j]] for j in pick])
        if 0 < y[ix].sum() < len(ix):
            vals.append(roc_auc_score(y[ix], p[ix]))
    return float(a), float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


db, _ = D.load_db()
Ylab = F.labels_A(db) if WHICH == "A" else F.labels_B_from_ptbxl(db)
sets = {}
if WHICH == "A":
    X = D.load_ptbxl100(db)
    ex = D.excluded_ids()
    ok = ~db.index.isin(ex)
    f9 = np.flatnonzero((db.strat_fold.values == 9) & ok)
    f10 = np.flatnonzero((db.strat_fold.values == 10) & ok)
    Zl = np.stack([D.page_layout_from_signal(np.asarray(X[i], np.float32)) for i in f9])
    P_val, Y_val = probs_from_x24(Zl), Ylab.values[f9]
    Zt = np.stack([D.page_layout_from_signal(np.asarray(X[i], np.float32)) for i in f10])
    sets["T1 fold 10 (benchmark)"] = (probs_from_x24(Zt), Ylab.values[f10], db.index[f10].values)
else:
    X = np.load(F.DD + "find2_x100_f16.npy", mmap_mode="r")
    m = pd.read_csv(OUT + "split.csv")
    va = np.flatnonzero(m.split == "val")
    te = np.flatnonzero(m.split == "test")
    P_val, Y_val = probs_from_array(X, np.sort(va)), m[F.B_LABELS].values[np.sort(va)]
    te = np.sort(te)
    sets["T1 CODE-15% test split (benchmark)"] = (probs_from_array(X, te), m[F.B_LABELS].values[te], m.patient_id.values[te])
thr = {}
for k, c in enumerate(NAMES):
    y = Y_val[:, k]
    if 0 < y.sum() < len(y):
        fpr, tpr, th = roc_curve(y, P_val[:, k])
        thr[c] = float(th[np.argmax(tpr - fpr)])
    else:
        thr[c] = 0.5
ds = D.digitised_sets()
for tag, name in (("T2", "T2 drawn pages, digitised"), ("T3", "T3 straightened phone photos")):
    d = ds[ds.set == tag].reset_index(drop=True)
    Z = np.stack([D.digitised_to_input({k: v for k, v in np.load(p).items()}) for p in d.path])
    P = probs_from_x24(Z)
    sets[name] = (P, Ylab.loc[d.ecg_id].values, d.group.values)
    pd.DataFrame(np.column_stack([d.name, d.ecg_id, d.group, P]), columns=["name", "ecg_id", "group"] + NAMES).to_csv(OUT + f"predictions_{tag}.csv", index=False)

rows = []
for sname, (P, Yv, groups) in sets.items():
    for k, c in enumerate(NAMES):
        y, p = Yv[:, k].astype(int), P[:, k]
        au, lo, hi = auc_ci(y, p, groups)
        pred = p >= thr[c]
        rows.append(dict(set=sname, cls=c, n=len(y), positives=int(y.sum()), clusters=len(pd.unique(groups)), auroc=au, lo95=lo, hi95=hi, ece=ece(p, y), brier=float(np.mean((p - y) ** 2)),
                         sensitivity=float(pred[y == 1].mean()) if y.sum() else float("nan"), specificity=float((~pred[y == 0]).mean()) if (y == 0).sum() else float("nan"), threshold=thr[c]))
T = pd.DataFrame(rows)
T.to_csv(OUTF, index=False)
status = {}
for c in NAMES:
    t1 = T[(T.set.str.startswith("T1")) & (T.cls == c)].iloc[0]
    t2 = T[(T.set.str.startswith("T2")) & (T.cls == c)].iloc[0]
    t3 = T[(T.set.str.startswith("T3")) & (T.cls == c)].iloc[0]
    drawn = bool(t2.positives >= 20 and t2.auroc >= 0.80 and t2.lo95 > 0.70)
    photo = bool(drawn and t3.positives >= 20 and t3.auroc >= 0.75)
    status[c] = dict(name=DESC[c], supported_drawn_pages=drawn, supported_phone_photos=photo, testable_drawn=bool(t2.positives >= 20), testable_photos=bool(t3.positives >= 20), threshold=thr[c],
                     T1_auroc=t1.auroc, T2_auroc=t2.auroc, T2_lo95=t2.lo95, T3_auroc=t3.auroc, T1_ece=t1.ece, T3_ece=t3.ece, T2_positives=int(t2.positives), T3_positives=int(t3.positives))
json.dump(dict(which=WHICH, rules="docs/plan/analysis_plan_changes.md 2026-11-16", classes=status), open(OUT + "status.json", "w"), indent=1)
md = [f"# Section FIND2-{WHICH}: " + ("PTB-XL fine labels" if WHICH == "A" else "CODE-15% labels") + ", test once (EXPLORATORY; rules logged before training)", "",
      "Rules: `docs/plan/analysis_plan_changes.md` ('MORE DISEASE FINDINGS' and Amendment 1). Public data only. Findings are ECG PATTERNS, not diagnoses and not risk. Pass rules and thresholds are the assistant's proposal, not approved by the guide. "
      f"Intervals: bootstrap over clusters ({BOOT} resamples); the photos of one page are not independent.", ""]
for sname in sets:
    md += [f"## {sname}", "", "| Finding | n | Positives | AUROC (95% interval) | Calibration error | Sensitivity | Specificity |", "|---|---|---|---|---|---|---|"]
    for _, r in T[T.set == sname].iterrows():
        md.append(f"| {r.cls} ({DESC[r.cls]}) | {r.n} | {r.positives} | {r.auroc:.3f} ({r.lo95:.3f} to {r.hi95:.3f}) | {r.ece:.3f} | {r.sensitivity:.2f} | {r.specificity:.2f} |")
    md.append("")
md += ["## What may be shown (pass rules applied)", "", "| Finding | Testable on drawn pages (positives) | Supported for drawn pages | Testable on photos (positives) | Supported for phone photos |", "|---|---|---|---|---|"]
for c, s in status.items():
    md.append(f"| {c} ({s['name']}) | {s['testable_drawn']} ({s['T2_positives']}) | {s['supported_drawn_pages']} | {s['testable_photos']} ({s['T3_positives']}) | {s['supported_phone_photos']} |")
open(OUT + f"SECTION_FIND2_{WHICH}.md", "w", encoding="utf-8").write("\n".join(md) + "\n")
print("\n".join(md))
