"""Heart health module, SECOND MODEL: test the FROZEN model once on FRESH data (rules: docs/plan/analysis_plan_changes.md, 2026-11-15 night, with Amendment 1).
Fresh pages = L + M (200 recordings). Fresh photos = L simulated + M simulated + the real printed-paper photos H (40, if provided), pooled and separately. Refuses to run twice.
Usage: demo\\.venv-gpu\\Scripts\\python.exe scripts/analysis/section_HEALTH2_test.py"""
import glob
import json
import os
import sys

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import roc_auc_score

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "demo"))
from health import data as D  # noqa: E402
from health import model as M  # noqa: E402

OUTF = M.OUT + "health2_test_metrics.csv"
if os.path.exists(OUTF) and "--force" not in sys.argv:
    sys.exit("The test was already run once (rule: run ONCE).")
dev = "cuda" if torch.cuda.is_available() else "cpu"
cal = json.load(open(M.OUT + "calibration_v2.json"))
net = M.EcgNet().to(dev)
net.load_state_dict(torch.load(M.OUT + "model_v2.pt", map_location=dev))
net.eval()
db, Y = D.load_db()
IM = ROOT + "/results/intervals_ml/"
rng = np.random.RandomState(60)
B = 2000


def probs(paths):
    X = np.stack([D.digitised_to_input({k: v.astype(float) for k, v in np.load(p).items()}) for p in paths])
    with torch.no_grad():
        lg = np.concatenate([net(torch.from_numpy(X[i:i + 64]).to(dev)).cpu().numpy() for i in range(0, len(X), 64)])
    a = np.array([cal["platt"][c]["a"] for c in D.CLASSES])
    b = np.array([cal["platt"][c]["b"] for c in D.CLASSES])
    return 1 / (1 + np.exp(-(lg * a + b)))


def gather(tag, sel_csv, folder, pat, sim=False):
    s = pd.read_csv(IM + sel_csv).set_index("page")
    paths, ids, groups = [], [], []
    for f in sorted(glob.glob(IM + folder + "/" + pat)):
        page = os.path.basename(f)[:4]
        if page in s.index:
            paths.append(f)
            ids.append(int(s.loc[page, "ecg_id"]))
            groups.append(page)
    return dict(paths=paths, ids=np.array(ids), groups=np.array(groups))


parts = {"L pages": gather("L", "selected_L_100.csv", "L/l_digitized_12lead", "*.npz"), "M pages": gather("M", "selected_M_100.csv", "M/m_digitized_12lead", "*.npz"),
         "L simulated photos": gather("L", "selected_L_100.csv", "L_sim/dig_v2", "*.npz"), "M simulated photos": gather("M", "selected_M_100.csv", "M_sim/dig_v2", "*.npz")}
sys.path.insert(0, ROOT + "/scripts/analysis")
import h2_photos  # noqa: E402

_hp, _hi, _hg = h2_photos.primary_items()
if len(_hp) >= 30:           # set H2: full-resolution printed-paper photos taken by the user's friend (different phone), straightened variant V2b
    parts["H2 real photos (printed paper, friend's phone)"] = dict(paths=_hp, ids=np.array(_hi), groups=np.array(_hg))
else:
    print("H2 photos not available (fewer than 30 digitised): the real-photo condition cannot be met", flush=True)
P = {k: probs(v["paths"]) for k, v in parts.items()}
Yp = {k: Y.loc[v["ids"]].values for k, v in parts.items()}
G = {k: v["groups"] for k, v in parts.items()}


def pool(keys):
    return np.concatenate([P[k] for k in keys]), np.concatenate([Yp[k] for k in keys]), np.concatenate([G[k] for k in keys])


sets = {k: (P[k], Yp[k], G[k]) for k in parts}
sets["POOLED fresh pages (L + M)"] = pool(["L pages", "M pages"])
_hk = "H2 real photos (printed paper, friend's phone)"
photo_keys = ["L simulated photos", "M simulated photos"] + ([_hk] if _hk in parts else [])
sets["POOLED fresh photos (" + " + ".join(k.split(" ")[0] for k in photo_keys) + ")"] = pool(photo_keys)


def ece(p, y, bins=10):
    e = 0.0
    edges = np.linspace(0, 1, bins + 1)
    for a, b in zip(edges[:-1], edges[1:]):
        m = (p >= a) & ((p < b) if b < 1 else (p <= b))
        if m.any():
            e += m.sum() / len(p) * abs(p[m].mean() - y[m].mean())
    return float(e)


def auc_ci(y, p, groups):
    if y.sum() < 2 or (1 - y).sum() < 2:
        return float("nan"), float("nan"), float("nan")
    uniq = pd.unique(groups)
    idx = {g: np.flatnonzero(groups == g) for g in uniq}
    v = []
    for _ in range(B):
        ix = np.concatenate([idx[uniq[j]] for j in rng.choice(len(uniq), len(uniq), replace=True)])
        if 0 < y[ix].sum() < len(ix):
            v.append(roc_auc_score(y[ix], p[ix]))
    return float(roc_auc_score(y, p)), float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))


rows = []
for sname, (Pp, Yv, g) in sets.items():
    for k, c in enumerate(D.CLASSES):
        y, p = Yv[:, k].astype(int), Pp[:, k]
        a, lo, hi = auc_ci(y, p, g)
        pred = p >= cal["thresholds"][c]
        rows.append(dict(set=sname, cls=c, n=len(y), positives=int(y.sum()), clusters=len(pd.unique(g)), auroc=a, lo95=lo, hi95=hi, ece=ece(p, y), brier=float(np.mean((p - y) ** 2)),
                         sensitivity=float(pred[y == 1].mean()) if y.sum() else float("nan"), specificity=float((~pred[y == 0]).mean())))
T = pd.DataFrame(rows)
T.to_csv(OUTF, index=False)
pk = [s for s in sets if s.startswith("POOLED fresh photos")][0]
status = {}
for c in D.CLASSES:
    pg = T[(T.set == "POOLED fresh pages (L + M)") & (T.cls == c)].iloc[0]
    ph = T[(T.set == pk) & (T.cls == c)].iloc[0]
    hr = T[(T.set.str.startswith("H2 real")) & (T.cls == c)]
    drawn = bool(pg.positives >= 20 and pg.auroc >= 0.80 and pg.lo95 > 0.70)
    h_ok = bool(len(hr) and np.isfinite(hr.iloc[0].auroc) and hr.iloc[0].auroc >= 0.70)
    photo = bool(drawn and ph.positives >= 20 and ph.auroc >= 0.75 and h_ok)
    status[c] = dict(supported_drawn_pages=drawn, supported_phone_photos=photo, testable_drawn=bool(pg.positives >= 20), testable_photos=bool(ph.positives >= 20), real_H_ok=h_ok if len(hr) else None,
                     show_percentage_photos=bool(photo and ph.ece <= 0.10), threshold=cal["thresholds"][c], pages_auroc=pg.auroc, pages_lo95=pg.lo95, photos_auroc=ph.auroc, photos_ece=ph.ece,
                     sens_photos=ph.sensitivity, spec_photos=ph.specificity)
json.dump(dict(rules="docs/plan/analysis_plan_changes.md 2026-11-15 night + Amendment 1", classes=status), open(M.OUT + "findings_status_v2.json", "w"), indent=1)
md = ["# Heart health module, SECOND MODEL: test once on FRESH data (EXPLORATORY; rules logged before any code of this model ran)", "",
      "Fine-tuned on development data only (cross-validated; Platt and thresholds from out-of-fold predictions). L, M and H were never used for anything but this single test. Pass rules are the assistant's proposal, not approved by the guide. Findings are ECG patterns, not risk.", ""]
for sname in sets:
    md += [f"## {sname}", "", "| Class | n | Positives | Clusters | AUROC (95% interval) | Calibration error | Brier | Sensitivity | Specificity |", "|---|---|---|---|---|---|---|---|---|"]
    for _, r in T[T.set == sname].iterrows():
        md.append(f"| {r.cls} | {r.n} | {r.positives} | {r.clusters} | {r.auroc:.3f} ({r.lo95:.3f} to {r.hi95:.3f}) | {r.ece:.3f} | {r.brier:.3f} | {r.sensitivity:.2f} | {r.specificity:.2f} |")
    md.append("")
md += ["## What the app may show (pass rules applied)", "", "| Class | Testable on pages | Supported for drawn pages | Testable on photos | Real H photos OK | Supported for phone photos | Percentage allowed |", "|---|---|---|---|---|---|---|"]
for c, s in status.items():
    md.append(f"| {c} | {s['testable_drawn']} | {s['supported_drawn_pages']} | {s['testable_photos']} | {s['real_H_ok']} | **{s['supported_phone_photos']}** | {s['show_percentage_photos']} |")
open(M.OUT + "SECTION_HEALTH2.md", "w", encoding="utf-8").write("\n".join(md) + "\n")
print("\n".join(md))
