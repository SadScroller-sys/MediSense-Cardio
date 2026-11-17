"""Set P test (rules: docs/plan/analysis_plan_changes.md, 2026-11-16 late night 'FRESH POSITIVE-RICH DATASET SET P'). Tests the FROZEN networks A and B at the FROZEN specificity-0.97 thresholds (results/find2_op/thresholds_v2.json), one PART at a time, each ONCE:
  pages : the drawn pages P###  (results/paper_p/p_digitized_12lead/P###.npz)
  sim   : the simulated phone photos (results/paper_p/P_sim/dig_v2/P###_<shot>.npz)
Pairs: A: LVH, LAFB, IRBBB, 1AVB; B: AF, RBBB, LBBB, 1dAVb. Labels from the PTB-XL statements of the recording (same definitions as before). AUROC with a 95% bootstrap over pages; positives; sensitivity and specificity at the frozen threshold;
and the share of NORMAL-group pictures flagged by at least one of the six patterns of the research-only block. 1AVB (A) and RBBB (B) were not in the block and have no 0.97 threshold: they are tested at their old Youden thresholds, descriptively, and cannot be promoted.
Usage: demo\\.venv-gpu\\Scripts\\python.exe -I scripts/analysis/section_P_test.py pages|sim"""
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
PP = ROOT + "/results/paper_p/"
OUTF = PP + f"test_{PART}_metrics.csv"
if os.path.exists(OUTF) and "--force" not in sys.argv:
    sys.exit(f"Part '{PART}' was already tested once (rule: run ONCE).")
sel = pd.read_csv(PP + "selected_P.csv").set_index("page")
db, _ = D.load_db()
LAB = {"A": F.labels_A(db), "B": F.labels_B_from_ptbxl(db)}
thr2 = json.load(open(ROOT + "/results/find2_op/thresholds_v2.json"))["thresholds"]
PAIRS = [("A", "LVH"), ("A", "LAFB"), ("A", "IRBBB"), ("A", "1AVB"), ("B", "AF"), ("B", "RBBB"), ("B", "LBBB"), ("B", "1dAVb")]
BLOCK = [("A", "LVH"), ("A", "LAFB"), ("A", "IRBBB"), ("B", "AF"), ("B", "LBBB"), ("B", "1dAVb")]
nets = {}
for tag, folder, names in (("A", F.OUT_A, F.A_CODES), ("B", F.OUT_B, F.B_LABELS)):
    cal = json.load(open(folder + "calibration.json"))
    net = M.EcgNet(n_out=len(names))
    net.load_state_dict(torch.load(folder + "model.pt", map_location="cpu"))
    net.eval()
    nets[tag] = (net, names, cal, json.load(open(folder + "status.json"))["classes"])


def probs(tag, X24):
    net, names, cal, _ = nets[tag]
    with torch.no_grad():
        lg = net(torch.from_numpy(np.ascontiguousarray(X24))).numpy()
    a = np.array([cal["platt"][c]["a"] for c in names])
    b = np.array([cal["platt"][c]["b"] for c in names])
    return 1 / (1 + np.exp(-(lg * a + b)))


items = []
if PART == "pages":
    for p in sel.index:
        items.append((p, p, PP + f"p_digitized_12lead/{p}.npz"))
else:
    for f in sorted(glob.glob(PP + "P_sim/dig_v2/P*.npz")):
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
P = {t: probs(t, X24) for t in ("A", "B")}
pages = np.array([p for _, p in used])
ids = sel.loc[pages, "ecg_id"].astype(int).values
pd.DataFrame({"item": [n for n, _ in used], "page": pages, **{f"A_{c}": P["A"][:, nets["A"][1].index(c)] for c in nets["A"][1]}, **{f"B_{c}": P["B"][:, nets["B"][1].index(c)] for c in nets["B"][1]}}).to_csv(PP + f"test_{PART}_predictions.csv", index=False)
rng = np.random.RandomState(68)
rows = []
flag_any = np.zeros(len(pages), bool)
for tag, c in PAIRS:
    k = nets[tag][1].index(c)
    p = P[tag][:, k]
    y = LAB[tag][c].loc[ids].values > 0
    key = f"{tag}:{c}"
    thr = thr2[key]["s97"] if key in thr2 else nets[tag][3][c]["threshold"]
    fl = p >= thr
    if (tag, c) in BLOCK:
        flag_any |= fl
    auc = roc_auc_score(y, p) if 0 < y.sum() < len(y) else float("nan")
    ups = pd.unique(pages)
    idx = {g: np.flatnonzero(pages == g) for g in ups}
    vals = []
    for _ in range(2000):
        ix = np.concatenate([idx[ups[j]] for j in rng.choice(len(ups), len(ups), replace=True)])
        if 0 < y[ix].sum() < len(ix):
            vals.append(roc_auc_score(y[ix], p[ix]))
    lo, hi = (float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))) if vals else (float("nan"), float("nan"))
    rows.append(dict(part=PART, pair=key, n=len(y), positives=int(y.sum()), pages=len(ups), auroc=auc, lo95=lo, hi95=hi, sensitivity=float(fl[y].mean()) if y.any() else float("nan"), specificity=float((~fl[~y]).mean()),
                     threshold=thr, threshold_kind="0.97 (frozen)" if key in thr2 else "old Youden (descriptive only)", excluded_no_output=excluded))
T = pd.DataFrame(rows)
normal = (sel.loc[pages, "group"] == "NORMAL").values
T["normal_pictures"] = int(normal.sum())
T["normal_flagged_by_any"] = int(flag_any[normal].sum())
T.to_csv(OUTF, index=False)
print(f"part {PART}: {len(used)} items used, {excluded} excluded; normal pictures flagged by at least one of the 6 patterns: {int(flag_any[normal].sum())} of {int(normal.sum())}")
print(T[["pair", "n", "positives", "auroc", "lo95", "sensitivity", "specificity", "threshold_kind"]].round(3).to_string(index=False))
