"""RISK PILOT 3: five-fold cross-validation on all usable patients, ONE run (rules: docs/plan/analysis_plan_changes.md, 2026-11-18 day). Same network, inputs and training settings as pilot 2; nothing is tuned.
Out-of-fold (OOF) predictions: every patient is predicted once, by a model that never saw them. Writes results/risk_pilot3/oof.csv and fold models. The script refuses to run twice.
Usage: demo\\.venv-gpu\\Scripts\\python.exe -I scripts/analysis/section_RISK3_cv.py"""
import copy
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
OUT = os.path.join(ROOT, "results", "risk_pilot3") + os.sep
os.makedirs(OUT, exist_ok=True)
if os.path.exists(OUT + "oof.csv"):
    print("pilot 3 was already run once: its result is in results/risk_pilot3/. Refusing to run twice.")
    raise SystemExit(1)
SEED, EPOCHS, PATIENCE, BS = 42, 30, 6, 256
dev = "cuda" if torch.cuda.is_available() else "cpu"
X = np.load(DD + "risk2_x250_f16.npy", mmap_mode="r")
m = pd.read_csv(DD + "risk2_meta.csv")
h = lambda tag, pid: int(hashlib.md5(f"{tag}-{pid}".encode()).hexdigest(), 16) % 100  # noqa: E731
m["fold"] = m.patient_id.map(lambda p: h("63", p) % 5)
m["vb"] = m.patient_id.map(lambda p: h("63v", p))
ev = m.death & (m.timey <= H)
ok = (ev | ((~m.death) & (m.timey >= H))).values
y = ev.astype(np.float32).values
agev = R.age_in(m.age.values).astype(np.float32)
mask = I.layout_masks(dev)
all_idx = np.flatnonzero(ok)
print(f"usable patients {len(all_idx)}, events {int(y[all_idx].sum())}", flush=True)


@torch.no_grad()
def logits(net, idx, emulate):
    net.eval()
    g = torch.Generator(device=dev)
    g.manual_seed(1234)
    out = []
    for i in range(0, len(idx), 512):
        ii = np.sort(idx[i:i + 512])
        xb = torch.from_numpy(np.asarray(X[ii], np.float32)).to(dev)
        out.append(net(I.make_input(xb, mask, emulate, g), torch.from_numpy(agev[ii]).to(dev)).squeeze(1).cpu().numpy())
    return np.concatenate(out)


rows, info = [], []
for k in range(5):
    torch.manual_seed(SEED + k)
    np.random.seed(SEED + k)
    te = np.sort(all_idx[m.fold.values[all_idx] == k])
    rest = all_idx[m.fold.values[all_idx] != k]
    va = np.sort(rest[m.vb.values[rest] < 15])
    tr = rest[m.vb.values[rest] >= 15]
    print(f"fold {k}: train {len(tr)} ({int(y[tr].sum())} events), validation {len(va)}, held-out {len(te)} ({int(y[te].sum())} events)", flush=True)
    net = R.RiskNet().to(dev)
    opt = torch.optim.AdamW(net.parameters(), lr=1e-3, weight_decay=1e-2)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=EPOCHS)
    lossf = nn.BCEWithLogitsLoss()
    gen = torch.Generator(device=dev)
    gen.manual_seed(SEED + k)
    best, best_ep, bad, best_state = -1, -1, 0, None
    for ep in range(1, EPOCHS + 1):
        net.train()
        perm = np.random.permutation(len(tr))
        for i in range(0, len(tr), BS):
            sel = np.sort(tr[perm[i:i + BS]])
            xb = torch.from_numpy(np.asarray(X[sel], np.float32)).to(dev)
            loss = lossf(net(I.make_input(xb, mask, True, gen), torch.from_numpy(agev[sel]).to(dev)).squeeze(1), torch.from_numpy(y[sel]).to(dev))
            opt.zero_grad()
            loss.backward()
            opt.step()
        sched.step()
        auc = roc_auc_score(y[va], logits(net, va, True))
        if auc > best:
            best, best_ep, bad, best_state = auc, ep, 0, copy.deepcopy(net.state_dict())
        else:
            bad += 1
            if bad >= PATIENCE:
                break
    net.load_state_dict(best_state)
    torch.save(best_state, OUT + f"model_fold{k}.pt")
    lv = logits(net, va, False)
    pl = LogisticRegression(C=1e6, max_iter=1000).fit(lv[:, None], y[va])
    lt = logits(net, te, False)
    p_cal = pl.predict_proba(lt[:, None])[:, 1]
    la = LogisticRegression(C=1e6, max_iter=1000).fit(agev[rest][:, None], y[rest])
    p_age = la.predict_proba(agev[te][:, None])[:, 1]
    info.append(dict(fold=k, best_epoch=best_ep, val_auroc=float(best), heldout_auroc=float(roc_auc_score(y[te], lt)), platt_a=float(pl.coef_[0, 0]), platt_b=float(pl.intercept_[0])))
    print(f"fold {k}: best epoch {best_ep}, validation AUROC {best:.4f}, held-out AUROC {info[-1]['heldout_auroc']:.4f}", flush=True)
    for j, i in enumerate(te):
        rows.append((int(m.patient_id.values[i]), k, int(y[i]), float(m.age.values[i]), float(lt[j]), float(p_cal[j]), float(p_age[j])))
pd.DataFrame(rows, columns=["patient_id", "fold", "y", "age", "logit", "p_cal", "p_age"]).to_csv(OUT + "oof.csv", index=False)
json.dump(info, open(OUT + "fold_info.json", "w"), indent=1)
print("saved OOF predictions for", len(rows), "patients", flush=True)
