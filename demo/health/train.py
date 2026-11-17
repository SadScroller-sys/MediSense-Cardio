"""Train the ECG-pattern model ONCE (rules: docs/plan/analysis_plan_changes.md, 2026-11-15). Folds 1-8 minus our digitised recordings; fold 9 chooses the epoch and fits Platt calibration.
Fold 10 and our digitised sets are NOT touched here. Usage: demo\\.venv-gpu\\Scripts\\python.exe -I demo/health/train.py   (run from the project folder; or without -I)."""
import json
import os
import sys
import time

import numpy as np
import torch
import torch.nn as nn
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

sys.path.insert(0, os.path.join(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")), ))
from health import data as D  # noqa: E402
from health import model as M  # noqa: E402

SEED, EPOCHS, PATIENCE, BS = 42, 40, 8, 128
torch.manual_seed(SEED)
np.random.seed(SEED)
os.makedirs(M.OUT, exist_ok=True)
dev = "cuda" if torch.cuda.is_available() else "cpu"
print("device", dev, flush=True)

db, Y = D.load_db()
X = D.load_ptbxl100(db)
ex = D.excluded_ids()
ok = ~db.index.isin(ex)
tr = np.flatnonzero((db.strat_fold.values <= 8) & ok)
va = np.flatnonzero((db.strat_fold.values == 9) & ok)
print("train", len(tr), "fold 9", len(va), "removed", int((~ok).sum()), flush=True)
Xtr = torch.from_numpy(np.asarray(X[tr], np.float32)).to(dev)
Ytr = torch.from_numpy(Y.values[tr]).to(dev)
Xva = torch.from_numpy(np.asarray(X[va], np.float32)).to(dev)
Yva = Y.values[va]
mask = M.layout_masks(dev)
net = M.EcgNet().to(dev)
print("parameters", sum(p.numel() for p in net.parameters()), flush=True)
opt = torch.optim.AdamW(net.parameters(), lr=1e-3, weight_decay=1e-2)
sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=EPOCHS)
lossf = nn.BCEWithLogitsLoss()
gen = torch.Generator(device=dev)
gen.manual_seed(SEED)


@torch.no_grad()
def val_logits():
    net.eval()
    out = []
    for i in range(0, len(va), 512):
        out.append(net(M.make_input(Xva[i:i + 512], mask)).cpu().numpy())
    return np.concatenate(out)


best, best_ep, bad, log = -1, -1, 0, []
for ep in range(1, EPOCHS + 1):
    net.train()
    perm = torch.randperm(len(tr), device=dev, generator=gen)
    tot, t0 = 0.0, time.time()
    for i in range(0, len(tr), BS):
        idx = perm[i:i + BS]
        xb = M.make_input(Xtr[idx], mask, augment=True, gen=gen)
        loss = lossf(net(xb), Ytr[idx])
        opt.zero_grad()
        loss.backward()
        opt.step()
        tot += float(loss) * len(idx)
    sched.step()
    lg = val_logits()
    aucs = [roc_auc_score(Yva[:, k], lg[:, k]) for k in range(6)]
    mean_auc = float(np.mean(aucs))
    log.append(dict(epoch=ep, train_loss=tot / len(tr), fold9_mean_auroc=mean_auc, **{f"fold9_{c}": a for c, a in zip(D.CLASSES, aucs)}, seconds=round(time.time() - t0, 1)))
    print(f"epoch {ep:2d} loss {tot / len(tr):.4f} fold-9 mean AUROC {mean_auc:.4f}  " + " ".join(f"{c} {a:.3f}" for c, a in zip(D.CLASSES, aucs)) + f"  {time.time() - t0:.0f}s", flush=True)
    if mean_auc > best:
        best, best_ep, bad = mean_auc, ep, 0
        torch.save(net.state_dict(), M.OUT + "model.pt")
    else:
        bad += 1
        if bad >= PATIENCE:
            print("early stop", flush=True)
            break
import pandas as pd  # noqa: E402

pd.DataFrame(log).to_csv(M.OUT + "training_log.csv", index=False)
net.load_state_dict(torch.load(M.OUT + "model.pt", map_location=dev))
lg = val_logits()
platt = {}
for k, c in enumerate(D.CLASSES):
    lr = LogisticRegression(C=1e6, max_iter=1000).fit(lg[:, [k]], Yva[:, k])
    platt[c] = dict(a=float(lr.coef_[0, 0]), b=float(lr.intercept_[0]))
json.dump(dict(seed=SEED, best_epoch=best_ep, fold9_mean_auroc=best, n_train=int(len(tr)), n_fold9=int(len(va)), platt=platt, classes=D.CLASSES, note="Platt scaling fitted on fold 9 only"),
          open(M.OUT + "calibration.json", "w"), indent=1)
print("saved model and calibration; best epoch", best_ep, "fold-9 mean AUROC", round(best, 4), flush=True)
