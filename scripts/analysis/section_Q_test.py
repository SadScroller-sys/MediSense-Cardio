"""Set Q test (rules: docs/plan/analysis_plan_changes.md, 2026-11-17 'ONE MORE ROUND, SET Q'). Tests the retrained networks A2 (LAFB, on the fold-10 pictures only) and B2 (AF, LBBB, all pictures) at their frozen
specificity-0.97 thresholds from DAMAGED validation data (results/find2_A2|B2/thresholds_q.json), one PART at a time, each ONCE: pages (drawn pages) or sim (simulated phone photos).
The first networks A and B (thresholds_v2.json, specificity 0.97) are also run on the same pictures, DESCRIPTIVELY, to show whether the retraining helped.
Reports AUROC with a 95% bootstrap over pages (2000, seed 73), positives, sensitivity and specificity, and the share of NORMAL pictures flagged by at least one of the three tested patterns.
Usage: demo\\.venv-gpu\\Scripts\\python.exe -I scripts/analysis/section_Q_test.py pages|sim"""
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
from health import find2 as F  # noqa: E402
from health import model as M  # noqa: E402

PART = sys.argv[1]
assert PART in ("pages", "sim")
PQ = ROOT + "/results/paper_q/"
OUTF = PQ + f"test_{PART}_metrics.csv"
if os.path.exists(OUTF) and "--force" not in sys.argv:
    sys.exit(f"Part '{PART}' was already tested once (rule: run ONCE).")
sel = pd.read_csv(PQ + "selected_Q.csv").set_index("page")
db, _ = D.load_db()
LAB = {"A": F.labels_A(db), "B": F.labels_B_from_ptbxl(db)}
thr_old = json.load(open(ROOT + "/results/find2_op/thresholds_v2.json"))["thresholds"]
thr_new = {**json.load(open(ROOT + "/results/find2_A2/thresholds_q.json"))["thresholds"], **json.load(open(ROOT + "/results/find2_B2/thresholds_q.json"))["thresholds"]}
SETS = {"A": (F.OUT_A, F.A_CODES), "B": (F.OUT_B, F.B_LABELS), "A2": (ROOT + "/results/find2_A2/", F.A_CODES), "B2": (ROOT + "/results/find2_B2/", F.B_LABELS)}
nets = {}
for tag, (folder, names) in SETS.items():
    cal = json.load(open(folder + "calibration.json"))
    net = M.EcgNet(n_out=len(names))
    net.load_state_dict(torch.load(folder + "model.pt", map_location="cpu"))
    net.eval()
    nets[tag] = (net, names, cal)


def probs(tag, X24):
    net, names, cal = nets[tag]
    with torch.no_grad():
        lg = net(torch.from_numpy(np.ascontiguousarray(X24))).numpy()
    a = np.array([cal["platt"][c]["a"] for c in names])
    b = np.array([cal["platt"][c]["b"] for c in names])
    return 1 / (1 + np.exp(-(lg * a + b)))


items = []
if PART == "pages":
    for p in sel.index:
        items.append((p, p, PQ + f"q_digitized_12lead/{p}.npz"))
else:
    for f in sorted(glob.glob(PQ + "P_sim/dig_v2/Q*.npz")):
        nm = os.path.basename(f)[:-4]
        items.append((nm, nm[:4], f))
used, X24, excluded = [], [], 0
for nm, page, f in items:
    leads = {k: np.asarray(v, float) for k, v in np.load(f).items()}
    ii = leads.get("II")
    if ii is None or np.isfinite(ii).sum() < 500:
        excluded += 1
        continue
    used.append((nm, page))
    X24.append(D.digitised_to_input(leads))
X24 = np.stack(X24)
P = {t: probs(t, X24) for t in SETS}
pages = np.array([p for _, p in used])
ids = sel.loc[pages, "ecg_id"].astype(int).values
fold10 = sel.loc[pages, "fold10"].values.astype(bool)
cols = {f"{t}_{c}": P[t][:, nets[t][1].index(c)] for t, cs in (("A2", ["LAFB"]), ("B2", ["AF", "LBBB"])) for c in cs}
pd.DataFrame({"item": [n for n, _ in used], "page": pages, **cols}).to_csv(PQ + f"test_{PART}_predictions.csv", index=False)
# decision pairs (retrained) and descriptive pairs (first networks)
PAIRS = [("A2", "LAFB", "A", True), ("B2", "AF", "B", False), ("B2", "LBBB", "B", False), ("A", "LAFB", "A", True), ("B", "AF", "B", False), ("B", "LBBB", "B", False)]
rng = np.random.RandomState(73)
rows = []
flag_any = np.zeros(len(pages), bool)
for tag, c, labsrc, only10 in PAIRS:
    k = nets[tag][1].index(c)
    p_all = P[tag][:, k]
    y_all = LAB[labsrc][c].loc[ids].values > 0
    keep = fold10 if only10 else np.ones(len(pages), bool)
    p, y, pg = p_all[keep], y_all[keep], pages[keep]
    thr = (thr_new if tag in ("A2", "B2") else thr_old)[f"{tag}:{c}"]["s97"]
    fl = p >= thr
    if tag in ("A2", "B2"):
        flag_any |= keep & (p_all >= thr)
    auc = roc_auc_score(y, p) if 0 < y.sum() < len(y) else float("nan")
    ups = pd.unique(pg)
    idx = {g: np.flatnonzero(pg == g) for g in ups}
    vals = []
    for _ in range(2000):
        ix = np.concatenate([idx[ups[j]] for j in rng.choice(len(ups), len(ups), replace=True)])
        if 0 < y[ix].sum() < len(ix):
            vals.append(roc_auc_score(y[ix], p[ix]))
    lo, hi = (float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))) if vals else (float("nan"), float("nan"))
    rows.append(dict(part=PART, pair=f"{tag}:{c}", role="decision" if tag in ("A2", "B2") else "descriptive", n=int(len(y)), positives=int(y.sum()), pages=len(ups), auroc=auc, lo95=lo, hi95=hi,
                     sensitivity=float(fl[y].mean()) if y.any() else float("nan"), specificity=float((~fl[~y]).mean()), threshold=thr, excluded_no_output=excluded))
T = pd.DataFrame(rows)
normal = (sel.loc[pages, "group"] == "NORMAL").values
T["normal_pictures"] = int(normal.sum())
T["normal_flagged_by_any_of_3"] = int(flag_any[normal].sum())
T.to_csv(OUTF, index=False)
print(f"part {PART}: {len(used)} items used, {excluded} excluded; NORMAL pictures flagged by at least one of A2:LAFB, B2:AF, B2:LBBB: {int(flag_any[normal].sum())} of {int(normal.sum())}")
print(T[["pair", "role", "n", "positives", "auroc", "lo95", "sensitivity", "specificity"]].round(3).to_string(index=False))
