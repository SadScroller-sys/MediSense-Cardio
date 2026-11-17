"""ROC and calibration figures for the public-data networks A (PTB-XL, 16 codes) and B (CODE-15%, 6 labels) on their held-out benchmarks (A: PTB-XL fold 10; B: CODE-15% test split, patient bucket >= 80).
This RE-COMPUTES the benchmark probabilities with the FROZEN models (no new test, nothing retrained or re-tuned) and CHECKS that the AUROCs equal the ones recorded by section_FIND2_test.py (test_metrics.csv) before drawing.
Output: docs/reports/figures/fig_find2_roc_calibration.png (+ .pdf) and results/find2_{A,B}/benchmark_predictions.npz. Usage: demo\\.venv-gpu\\Scripts\\python.exe -I scripts/tools/make_find2_figures.py"""
import json
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import torch  # noqa: E402
from sklearn.metrics import roc_auc_score, roc_curve  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "demo"))
from health import data as D  # noqa: E402
from health import find2 as F  # noqa: E402
from health import model as M  # noqa: E402

dev = "cpu"                                   # the GPU is busy with the digitiser; these networks are small
mask = M.layout_masks(dev)


def load(folder, names):
    cal = json.load(open(folder + "calibration.json"))
    net = M.EcgNet(n_out=len(names)).to(dev)
    net.load_state_dict(torch.load(folder + "model.pt", map_location=dev))
    net.eval()
    a = np.array([cal["platt"][c]["a"] for c in names])
    b = np.array([cal["platt"][c]["b"] for c in names])
    return net, a, b


@torch.no_grad()
def probs(net, a, b, X, idx=None, bs=512):
    n = len(X) if idx is None else len(idx)
    out = []
    for i in range(0, n, bs):
        ii = np.arange(i, min(i + bs, n)) if idx is None else np.sort(idx[i:i + bs])
        xb = torch.from_numpy(np.asarray(X[ii], np.float32)).to(dev)
        out.append(net(M.make_input(xb, mask)).numpy())
    return 1 / (1 + np.exp(-(np.concatenate(out) * a + b)))


# ---------------------------------------------------------------- model A: PTB-XL fold 10
db, _ = D.load_db()
YA = F.labels_A(db)
X = D.load_ptbxl100(db)
ok = ~db.index.isin(D.excluded_ids())
f10 = np.flatnonzero((db.strat_fold.values == 10) & ok)
netA, aA, bA = load(F.OUT_A, F.A_CODES)
Z = np.stack([D.page_layout_from_signal(np.asarray(X[i], np.float32)) for i in f10])
with torch.no_grad():
    lg = np.concatenate([netA(torch.from_numpy(Z[i:i + 512])).numpy() for i in range(0, len(Z), 512)])
PA = 1 / (1 + np.exp(-(lg * aA + bA)))
yA = YA.values[f10]
# ---------------------------------------------------------------- model B: CODE-15% test split
XB = np.load(F.DD + "find2_x100_f16.npy", mmap_mode="r")
mB = pd.read_csv(F.OUT_B + "split.csv")
te = np.sort(np.flatnonzero(mB.split == "test"))
netB, aB, bB = load(F.OUT_B, F.B_LABELS)
PB = probs(netB, aB, bB, XB, te)
yB = mB[F.B_LABELS].values[te]
np.savez_compressed(F.OUT_A + "benchmark_predictions.npz", p=PA, y=yA, names=np.array(F.A_CODES))
np.savez_compressed(F.OUT_B + "benchmark_predictions.npz", p=PB, y=yB, names=np.array(F.B_LABELS))

# ---------------------------------------------------------------- consistency check against the recorded test numbers
worst = 0.0
for folder, names, P, Y, tag in ((F.OUT_A, F.A_CODES, PA, yA, "T1 fold 10"), (F.OUT_B, F.B_LABELS, PB, yB, "T1 CODE-15%")):
    t = pd.read_csv(folder + "test_metrics.csv")
    t = t[t.set.str.startswith("T1")].set_index("cls")
    for k, c in enumerate(names):
        d = abs(roc_auc_score(Y[:, k], P[:, k]) - float(t.loc[c, "auroc"]))
        worst = max(worst, d)
print("largest difference to the recorded benchmark AUROC:", f"{worst:.2e}", "(must be tiny)", flush=True)
assert worst < 1e-3, "the recomputed benchmark does not match the recorded test numbers: do not use this figure"

# ---------------------------------------------------------------- figure
OKABE = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9", "#000000", "#999999"]


def roc_panel(ax, names, P, Y, show, title):
    for j, c in enumerate(show):
        k = names.index(c)
        fpr, tpr, _ = roc_curve(Y[:, k], P[:, k])
        ax.plot(fpr, tpr, color=OKABE[j % len(OKABE)], lw=1.8, label=f"{c}  {roc_auc_score(Y[:, k], P[:, k]):.3f}")
    ax.plot([0, 1], [0, 1], color="#9ca3af", lw=1, ls="--")
    ax.set_xlabel("False-positive rate")
    ax.set_ylabel("True-positive rate")
    ax.set_title(title, fontsize=11, loc="left", fontweight="bold")
    ax.legend(title="finding  AUROC", fontsize=8.5, title_fontsize=8.5, loc="lower right", frameon=False)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.01)
    ax.grid(alpha=0.25)


def cal_panel(ax, names, P, Y, show, title):
    edges = [0, 0.5, 0.8, 0.9, 0.95, 0.975, 0.99, 0.995, 1.0]
    for j, c in enumerate(show):
        k = names.index(c)
        p, y = P[:, k], Y[:, k]
        q = np.quantile(p, edges)
        xs, ys = [], []
        for lo, hi in zip(q[:-1], q[1:]):
            m = (p >= lo) & ((p <= hi) if hi == q[-1] else (p < hi))
            if m.sum() >= 20 and y[m].mean() > 0:
                xs.append(p[m].mean())
                ys.append(y[m].mean())
        ax.plot(xs, ys, "o-", color=OKABE[j % len(OKABE)], lw=1.4, ms=4, label=c)
    ax.plot([1e-4, 1], [1e-4, 1], color="#9ca3af", lw=1, ls="--")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(2e-3, 1)
    ax.set_ylim(2e-3, 1)
    ax.set_xlabel("Mean predicted probability (log scale)")
    ax.set_ylabel("Observed rate (log scale)")
    ax.set_title(title, fontsize=11, loc="left", fontweight="bold")
    ax.legend(fontsize=8.5, frameon=False, loc="upper left", ncol=2)
    ax.grid(alpha=0.25, which="both")


fig, axs = plt.subplots(2, 2, figsize=(12.5, 10.2), dpi=160)
roc_panel(axs[0, 0], F.B_LABELS, PB, yB, F.B_LABELS, f"B  CODE-15% labels: ROC, {len(te):,} held-out exams")
cal_panel(axs[0, 1], F.B_LABELS, PB, yB, F.B_LABELS, "B  calibration (groups of exams by predicted probability)")
showA = ["CLBBB", "CRBBB", "LAFB", "ASMI", "LVH", "IVCD"]      # the strongest, two mid, and the weakest (IVCD) for contrast
roc_panel(axs[1, 0], F.A_CODES, PA, yA, showA, f"A  PTB-XL codes: ROC, fold 10, {len(f10):,} recordings (6 of 16 shown)")
cal_panel(axs[1, 1], F.A_CODES, PA, yA, showA, "A  calibration")
fig.suptitle("Public-data networks A and B on their held-out benchmarks (frozen models, tested once)", fontsize=14, fontweight="bold", y=0.995)
fig.text(0.01, 0.003, "Research prototype. Benchmark = clean recordings, not phone photos; on our photos the same networks could not be tested for lack of positive photos (FINAL_NUMBERS 10.22).", fontsize=8.5, color="#6b7280")
fig.tight_layout(rect=(0, 0.015, 1, 0.985))
OUTF = ROOT + "/docs/reports/figures/"
for ext in ("png", "pdf"):
    fig.savefig(OUTF + "fig_find2_roc_calibration." + ext, bbox_inches="tight", facecolor="white")
print("saved", OUTF + "fig_find2_roc_calibration.png")
import shutil as _sh  # noqa: E402

_sh.copyfile(ROOT + "/docs/reports/figures/fig_find2_roc_calibration.png", ROOT + "/demo/assets/fig_find2_roc_calibration.png")      # the demo app serves its copy
