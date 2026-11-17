"""RISK PILOT 2, step 2: train ONCE (rules: docs/plan/analysis_plan_changes.md, 2026-11-16). 5-year death, ECG + age, patient split by hash (seed 62): bucket < 70 train, 70 to 79 validation, >= 80 test; the SEALED TEST = bucket >= 80 AND part >= 6.
Bucket >= 80 patients of parts 0 to 5 (the pilot-1 test patients) are excluded from everything. Test is NOT touched here.
Usage: demo\\.venv-gpu\\Scripts\\python.exe -I scripts/analysis/section_RISK2_train.py"""
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
from health import risk as R  # noqa: E402

H = 5.0
DD = os.path.join(ROOT, "data", "code15") + os.sep
OUT = os.path.join(ROOT, "results", "risk_pilot2") + os.sep
os.makedirs(OUT, exist_ok=True)
SEED, EPOCHS, PATIENCE, BS = 42, 30, 6, 256
torch.manual_seed(SEED)
np.random.seed(SEED)
dev = "cuda" if torch.cuda.is_available() else "cpu"
X = np.load(DD + "risk2_x250_f16.npy", mmap_mode="r")
m = pd.read_csv(DD + "risk2_meta.csv")


def bucket(pid):
    return int(hashlib.md5(f"62-{pid}".encode()).hexdigest(), 16) % 100


m["bucket"] = m.patient_id.map(bucket)
m["split"] = np.where(m.bucket < 70, "train", np.where(m.bucket < 80, "val", np.where(m.part >= 6, "test", "excluded_pilot1_test")))
ev = m.death & (m.timey <= H)
ok = ev | ((~m.death) & (m.timey >= H))                    # alive with follow-up under 5 years: censored, excluded
m["y"] = ev.astype(int)
m["usable"] = ok
m["age_in"] = R.age_in(m.age.values)
m.to_csv(OUT + "split_h5.csv", index=False)
tr, va = np.flatnonzero(ok & (m.split == "train")), np.flatnonzero(ok & (m.split == "val"))
print(f"5-year y: train {len(tr)} ({int(m.y.values[tr].sum())} events), validation {len(va)} ({int(m.y.values[va].sum())} events); sealed test untouched ({int((ok & (m.split == 'test')).sum())} patients)", flush=True)
y = m.y.values.astype(np.float32)
agev = m.age_in.values.astype(np.float32)
mask = I.layout_masks(dev)
net = R.RiskNet().to(dev)
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
        out.append(net(I.make_input(xb, mask, emulate, g), torch.from_numpy(agev[ii]).to(dev)).squeeze(1).cpu().numpy())
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
        loss = lossf(net(I.make_input(xb, mask, True, gen), torch.from_numpy(agev[sel]).to(dev)).squeeze(1), yb)
        opt.zero_grad()
        loss.backward()
        opt.step()
        tot += float(loss.detach()) * len(sel)
    sched.step()
    auc = roc_auc_score(y[va_sorted], logits(va_sorted, True))
    log.append(dict(epoch=ep, train_loss=tot / len(tr), val_auroc=auc))
    print(f"epoch {ep:2d} loss {tot / len(tr):.4f} validation AUROC {auc:.4f}", flush=True)
    if auc > best:
        best, best_ep, bad = auc, ep, 0
        torch.save(net.state_dict(), OUT + "model_h5.pt")
    else:
        bad += 1
        if bad >= PATIENCE:
            print("early stop", flush=True)
            break
pd.DataFrame(log).to_csv(OUT + "training_log_h5.csv", index=False)
net.load_state_dict(torch.load(OUT + "model_h5.pt", map_location=dev))
lv = logits(va_sorted, False)
lr = LogisticRegression(C=1e6, max_iter=1000).fit(lv[:, None], y[va_sorted])
json.dump(dict(horizon_years=H, best_epoch=best_ep, val_auroc=best, platt=dict(a=float(lr.coef_[0, 0]), b=float(lr.intercept_[0])), seed=SEED, n_train=int(len(tr)), n_val=int(len(va)),
               note="Platt fitted on the validation split (original, non-emulated input); sealed test untouched"), open(OUT + "calibration_h5.json", "w"), indent=1)
print("saved; best epoch", best_ep, "validation AUROC", round(best, 4), flush=True)
