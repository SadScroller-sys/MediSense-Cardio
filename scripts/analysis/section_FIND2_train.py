"""MORE DISEASE FINDINGS: train ONE model ONCE (rules: docs/plan/analysis_plan_changes.md, 2026-11-16 + Amendment 1).
A: PTB-XL fine labels (16 codes), folds 1-8 minus our digitised recordings, fold 9 = early stopping + Platt + thresholds; fold 10 and our digitised sets are NOT touched here.
B: CODE-15% labels (6), all exams with a 10 s recording, patient hash split (seed 62): bucket < 70 train, 70-79 validation; test (>= 80) is NOT touched here.
Usage: demo\\.venv-gpu\\Scripts\\python.exe -I scripts/analysis/section_FIND2_train.py A|B"""
import json
import os
import sys
import time

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "demo"))
from health import data as D  # noqa: E402
from health import find2 as F  # noqa: E402
from health import model as M  # noqa: E402

WHICH = sys.argv[1]
assert WHICH in ("A", "B")
OUT = F.OUT_A if WHICH == "A" else F.OUT_B
NAMES = F.A_CODES if WHICH == "A" else F.B_LABELS
os.makedirs(OUT, exist_ok=True)
EPOCHS, PATIENCE, BS = (40, 8, 128) if WHICH == "A" else (30, 6, 256)
SEED = 42
torch.manual_seed(SEED)
np.random.seed(SEED)
dev = "cuda" if torch.cuda.is_available() else "cpu"
mask = M.layout_masks(dev)
if WHICH == "A":
    db, _ = D.load_db()
    Yall = F.labels_A(db)
    X = D.load_ptbxl100(db)
    ex = D.excluded_ids()
    ok = ~db.index.isin(ex)
    tr = np.flatnonzero((db.strat_fold.values <= 8) & ok)
    va = np.flatnonzero((db.strat_fold.values == 9) & ok)
    Y = Yall.values
    print("A: train", len(tr), "fold 9", len(va), "positives in train:", dict(zip(NAMES, Y[tr].sum(0).astype(int))), flush=True)
else:
    X = np.load(F.DD + "find2_x100_f16.npy", mmap_mode="r")
    m = pd.read_csv(F.DD + "find2_meta.csv")
    m["bucket"] = m.patient_id.map(F.bucket)
    Y = m[F.B_LABELS].values.astype(np.float32)
    tr, va = np.flatnonzero(m.bucket < 70), np.flatnonzero((m.bucket >= 70) & (m.bucket < 80))
    m["split"] = np.where(m.bucket < 70, "train", np.where(m.bucket < 80, "val", "test"))
    m.to_csv(OUT + "split.csv", index=False)
    print("B: train", len(tr), "validation", len(va), "test untouched", int((m.bucket >= 80).sum()), "positives in train:", dict(zip(NAMES, Y[tr].sum(0).astype(int))), flush=True)
K = len(NAMES)
net = M.EcgNet(n_out=K).to(dev)
opt = torch.optim.AdamW(net.parameters(), lr=1e-3, weight_decay=1e-2)
sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=EPOCHS)
lossf = nn.BCEWithLogitsLoss()
gen = torch.Generator(device=dev)
gen.manual_seed(SEED)
va_sorted = np.sort(va)


def batch(idx):
    ii = np.sort(idx)
    return torch.from_numpy(np.asarray(X[ii], np.float32)).to(dev), torch.from_numpy(Y[ii]).to(dev)


@torch.no_grad()
def val_logits():
    net.eval()
    out = []
    for i in range(0, len(va_sorted), 512):
        xb, _ = batch(va_sorted[i:i + 512])
        out.append(net(M.make_input(xb, mask)).cpu().numpy())
    return np.concatenate(out)


def aucs(lg):
    r = []
    for k in range(K):
        y = Y[va_sorted, k]
        r.append(roc_auc_score(y, lg[:, k]) if 0 < y.sum() < len(y) else np.nan)
    return r


best, best_ep, bad, log = -1, -1, 0, []
for ep in range(1, EPOCHS + 1):
    net.train()
    perm = np.random.permutation(len(tr))
    tot, t0 = 0.0, time.time()
    for i in range(0, len(tr), BS):
        xb, yb = batch(tr[perm[i:i + BS]])
        loss = lossf(net(M.make_input(xb, mask, augment=True, gen=gen)), yb)
        opt.zero_grad()
        loss.backward()
        opt.step()
        tot += float(loss.detach()) * len(yb)
    sched.step()
    a = aucs(val_logits())
    mean_auc = float(np.nanmean(a))
    log.append(dict(epoch=ep, train_loss=tot / len(tr), val_mean_auroc=mean_auc, seconds=round(time.time() - t0, 1)))
    print(f"epoch {ep:2d} loss {tot / len(tr):.4f} validation mean AUROC {mean_auc:.4f}  {time.time() - t0:.0f}s", flush=True)
    if mean_auc > best:
        best, best_ep, bad = mean_auc, ep, 0
        torch.save(net.state_dict(), OUT + "model.pt")
    else:
        bad += 1
        if bad >= PATIENCE:
            print("early stop", flush=True)
            break
pd.DataFrame(log).to_csv(OUT + "training_log.csv", index=False)
net.load_state_dict(torch.load(OUT + "model.pt", map_location=dev))
lg = val_logits()
platt = {}
for k, c in enumerate(NAMES):
    y = Y[va_sorted, k]
    if 0 < y.sum() < len(y):
        lr = LogisticRegression(C=1e6, max_iter=1000).fit(lg[:, [k]], y)
        platt[c] = dict(a=float(lr.coef_[0, 0]), b=float(lr.intercept_[0]))
    else:
        platt[c] = dict(a=1.0, b=0.0)
json.dump(dict(which=WHICH, seed=SEED, best_epoch=best_ep, val_mean_auroc=best, n_train=int(len(tr)), n_val=int(len(va)), platt=platt, classes=NAMES, val_auroc=dict(zip(NAMES, [float(x) for x in aucs(lg)])),
               note="Platt scaling fitted on the validation fold/split only; test untouched"), open(OUT + "calibration.json", "w"), indent=1)
print("saved; best epoch", best_ep, "validation mean AUROC", round(best, 4), flush=True)
