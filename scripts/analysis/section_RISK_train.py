"""ECG-estimated mortality RISK PILOT (CODE-15%), step 2: train ONCE (rules: docs/plan/analysis_plan_changes.md, 2026-11-15 night). Primary outcome = death within 1 year (secondary 2 years, same recipe via --horizon 2).
Patient-level split by hash (seed 62): 70% train, 10% validation (early stopping and Platt calibration), 20% test (NOT touched here).
Usage: demo\\.venv-gpu\\Scripts\\python.exe scripts/analysis/section_RISK_train.py [--horizon 1]"""
import hashlib
import json
import os
import sys

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "demo"))
from health import intervals_ml as I  # noqa: E402

H = float(sys.argv[sys.argv.index("--horizon") + 1]) if "--horizon" in sys.argv else 1.0
TAG = f"h{int(H)}"
DD = os.path.join(ROOT, "data", "code15") + os.sep
OUT = os.path.join(ROOT, "results", "risk_pilot") + os.sep
os.makedirs(OUT, exist_ok=True)
SEED, EPOCHS, PATIENCE, BS = 42, 30, 6, 256
torch.manual_seed(SEED)
np.random.seed(SEED)
dev = "cuda" if torch.cuda.is_available() else "cpu"
X = np.load(DD + "risk_x250_f16.npy", mmap_mode="r")
m = pd.read_csv(DD + "risk_meta.csv")


def bucket(pid):
    return int(hashlib.md5(f"62-{pid}".encode()).hexdigest(), 16) % 100


m["bucket"] = m.patient_id.map(bucket)
m["split"] = np.where(m.bucket < 70, "train", np.where(m.bucket < 80, "val", "test"))
ev = m.death & (m.timey <= H)
ok = ev | ((~m.death) & (m.timey >= H))                    # alive with follow-up shorter than the horizon: censored, excluded
m["y"] = ev.astype(int)
m["usable"] = ok
m.to_csv(OUT + f"split_{TAG}.csv", index=False)
tr, va = np.flatnonzero(ok & (m.split == "train")), np.flatnonzero(ok & (m.split == "val"))
print(f"horizon {H} y: train {len(tr)} ({int(m.y.values[tr].sum())} events), validation {len(va)} ({int(m.y.values[va].sum())} events); test is untouched", flush=True)
y = m.y.values.astype(np.float32)
mask = I.layout_masks(dev)
net = I.IntervalNet(n_out=1).to(dev)
opt = torch.optim.AdamW(net.parameters(), lr=1e-3, weight_decay=1e-2)
sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=EPOCHS)
lossf = nn.BCEWithLogitsLoss()
gen = torch.Generator(device=dev)
gen.manual_seed(SEED)


@torch.no_grad()
def logits(idx, emulate):
    net.eval()
    g = torch.Generator(device=dev)
    g.manual_seed(1234)
    out = []
    for i in range(0, len(idx), 512):
        ii = np.sort(idx[i:i + 512])
        xb = torch.from_numpy(np.asarray(X[ii], np.float32)).to(dev)
        out.append(net(I.make_input(xb, mask, emulate, g)).squeeze(1).cpu().numpy())
    return np.concatenate(out)


best, best_ep, bad, log = -1, -1, 0, []
va_sorted = np.sort(va)
for ep in range(1, EPOCHS + 1):
    net.train()
    perm = np.random.permutation(len(tr))
    tot = 0.0
    for i in range(0, len(tr), BS):
        sel = np.sort(tr[perm[i:i + BS]])
        xb = torch.from_numpy(np.asarray(X[sel], np.float32)).to(dev)
        yb = torch.from_numpy(y[sel]).to(dev)
        loss = lossf(net(I.make_input(xb, mask, True, gen)).squeeze(1), yb)
        opt.zero_grad()
        loss.backward()
        opt.step()
        tot += float(loss) * len(sel)
    sched.step()
    auc = roc_auc_score(y[va_sorted], logits(va_sorted, True))
    log.append(dict(epoch=ep, train_loss=tot / len(tr), val_auroc=auc))
    print(f"epoch {ep:2d} loss {tot / len(tr):.4f} validation AUROC {auc:.4f}", flush=True)
    if auc > best:
        best, best_ep, bad = auc, ep, 0
        torch.save(net.state_dict(), OUT + f"model_{TAG}.pt")
    else:
        bad += 1
        if bad >= PATIENCE:
            print("early stop", flush=True)
            break
pd.DataFrame(log).to_csv(OUT + f"training_log_{TAG}.csv", index=False)
net.load_state_dict(torch.load(OUT + f"model_{TAG}.pt", map_location=dev))
lv = logits(va_sorted, False)
lr = LogisticRegression(C=1e6, max_iter=1000).fit(lv[:, None], y[va_sorted])
json.dump(dict(horizon_years=H, best_epoch=best_ep, val_auroc=best, platt=dict(a=float(lr.coef_[0, 0]), b=float(lr.intercept_[0])), seed=SEED, n_train=int(len(tr)), n_val=int(len(va)),
               note="Platt fitted on the validation split (original, non-emulated input); test split untouched"), open(OUT + f"calibration_{TAG}.json", "w"), indent=1)
print("saved; best epoch", best_ep, "validation AUROC", round(best, 4), flush=True)
