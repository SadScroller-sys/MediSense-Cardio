"""Set N test (rules: docs/plan/analysis_plan_changes.md, 2026-11-16 evening 'POSITIVE-RICH SET N'). Tests the FROZEN networks A and B on set N, one PART at a time, each part ONCE (refuses to run twice):
  pages : the 120 digitised drawn pages            results/paper_n/n_digitized_12lead/N###.npz
  sim   : the 120 simulated photos (1 per page)    results/paper_n/N_sim/dig_v2/N###_<shot>.npz
  real  : the real photos (matched to pages)       results/paper_n/photos_dig/<stem>__V2b.npz + results/paper_n/real_photo_map.csv (columns photo, page)
Eight model-and-finding pairs: A: LVH, LAFB, 1AVB, CLBBB; B: AF, RBBB (CRBBB or IRBBB), LBBB, 1dAVb. AUROC with a 95% bootstrap over PAGES (the photos of a page are one cluster), positives, sensitivity and specificity at the frozen
decision threshold. A photo with no usable digitiser output is excluded and counted. Verdict (pass rules) is made by section_N_verdict.py after the parts.
Usage: demo\\.venv-gpu\\Scripts\\python.exe -I scripts/analysis/section_N_test.py pages|sim|real"""
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
assert PART in ("pages", "sim", "real")
PN = ROOT + "/results/paper_n/"
OUTF = PN + f"test_{PART}_metrics.csv"
if os.path.exists(OUTF) and "--force" not in sys.argv:
    sys.exit(f"Part '{PART}' was already tested once (rule: run ONCE).")
sel = pd.read_csv(PN + "selected_N.csv").set_index("page")
# (model, output name in that model, column of selected_N that defines the positives, display name)
PAIRS = [("A", "LVH", "LVH", "LVH (A)"), ("A", "LAFB", "LAFB", "LAFB (A)"), ("A", "1AVB", "AVB1", "1AVB (A)"), ("A", "CLBBB", "LBBB", "CLBBB (A)"),
         ("B", "AF", "AF", "AF (B)"), ("B", "RBBB", "RBBB", "RBBB (B)"), ("B", "LBBB", "LBBB", "LBBB (B)"), ("B", "1dAVb", "AVB1", "1dAVb (B)")]
mask = M.layout_masks("cpu")
nets = {}
for tag, folder, names in (("A", F.OUT_A, F.A_CODES), ("B", F.OUT_B, F.B_LABELS)):
    cal = json.load(open(folder + "calibration.json"))
    net = M.EcgNet(n_out=len(names))
    net.load_state_dict(torch.load(folder + "model.pt", map_location="cpu"))
    net.eval()
    st = json.load(open(folder + "status.json"))["classes"]
    nets[tag] = (net, names, cal, st)


def probs(tag, X24):
    net, names, cal, _ = nets[tag]
    with torch.no_grad():
        lg = net(torch.from_numpy(np.ascontiguousarray(X24))).numpy()
    a = np.array([cal["platt"][c]["a"] for c in names])
    b = np.array([cal["platt"][c]["b"] for c in names])
    return 1 / (1 + np.exp(-(lg * a + b)))


# ---------------------------------------------------------------- the items of this part
items = []                                      # (item name, page, path)
if PART == "pages":
    for p in sel.index:
        items.append((p, p, PN + f"n_digitized_12lead/{p}.npz"))
elif PART == "sim":
    for f in sorted(glob.glob(PN + "N_sim/dig_v2/N*.npz")):
        nm = os.path.basename(f)[:-4]
        items.append((nm, nm[:4], f))
else:
    mp = pd.read_csv(PN + "real_photo_map.csv")
    for _, r in mp.iterrows():
        f = PN + f"photos_dig/{os.path.splitext(r.photo)[0]}__V2b.npz"
        if os.path.exists(f):
            items.append((os.path.splitext(r.photo)[0], r.page, f))
rows_used, X24, excluded = [], [], 0
for nm, page, f in items:
    leads = {k: np.asarray(v, float) for k, v in np.load(f).items()}
    ii = leads.get("II")
    if ii is None or np.isfinite(ii).sum() < 500:
        excluded += 1                           # no usable digitiser output
        continue
    rows_used.append((nm, page))
    X24.append(D.digitised_to_input(leads))
X24 = np.stack(X24)
P = {t: probs(t, X24) for t in ("A", "B")}
pages = np.array([p for _, p in rows_used])
pd.DataFrame({"item": [n for n, _ in rows_used], "page": pages, **{f"A_{c}": P["A"][:, nets["A"][1].index(c)] for c in nets["A"][1]}, **{f"B_{c}": P["B"][:, nets["B"][1].index(c)] for c in nets["B"][1]}}).to_csv(PN + f"test_{PART}_predictions.csv", index=False)
rng = np.random.RandomState(65)
B = 2000
rows = []
for tag, out, col, disp in PAIRS:
    k = nets[tag][1].index(out)
    p = P[tag][:, k]
    y = sel.loc[pages, col].astype(int).values
    thr = nets[tag][3][out]["threshold"]
    auc = roc_auc_score(y, p) if 0 < y.sum() < len(y) else float("nan")
    ups = pd.unique(pages)
    idx = {g: np.flatnonzero(pages == g) for g in ups}
    vals = []
    for _ in range(B):
        ix = np.concatenate([idx[ups[j]] for j in rng.choice(len(ups), len(ups), replace=True)])
        if 0 < y[ix].sum() < len(ix):
            vals.append(roc_auc_score(y[ix], p[ix]))
    lo, hi = (float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))) if vals else (float("nan"), float("nan"))
    pred = p >= thr
    rows.append(dict(part=PART, pair=disp, model=tag, finding=out, n=len(y), positives=int(y.sum()), pages=len(ups), auroc=auc, lo95=lo, hi95=hi,
                     sensitivity=float(pred[y == 1].mean()) if y.sum() else float("nan"), specificity=float((~pred[y == 0]).mean()), threshold=thr, excluded_no_output=excluded))
T = pd.DataFrame(rows)
T.to_csv(OUTF, index=False)
print(f"part {PART}: {len(rows_used)} items used, {excluded} excluded (no usable output)")
print(T[["pair", "n", "positives", "auroc", "lo95", "hi95", "sensitivity", "specificity"]].round(3).to_string(index=False))
