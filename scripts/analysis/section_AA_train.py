"""Section AA: train the learned QRS-duration / QT model ONCE (rules: docs/plan/analysis_plan_changes.md, 2026-11-15 "Section AA").
Folds 1-8 minus every recording of our digitised / photo sets and of the sealed set K; fold 9 chooses the epoch and the original-signal offsets. No digitised page and no fold 10 is touched here.
Usage: demo\\.venv-gpu\\Scripts\\python.exe scripts/analysis/section_AA_train.py"""
import json
import os
import sys
import time

import numpy as np
import pandas as pd
import torch
import torch.nn as nn

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "demo"))
from health import data as D  # noqa: E402
from health import intervals_ml as I  # noqa: E402

SEED, EPOCHS, PATIENCE, BS = 42, 40, 8, 128
torch.manual_seed(SEED)
np.random.seed(SEED)
os.makedirs(I.OUT, exist_ok=True)
dev = "cuda" if torch.cuda.is_available() else "cpu"
db = pd.read_csv(D.PT + "ptbxl_database.csv").set_index("ecg_id").sort_index()
x12 = pd.read_csv(ROOT + "/data/ptbxl_plus/12sl_features.csv").set_index("ecg_id").reindex(db.index)
Y = x12[I.TARGETS].values.astype(np.float32)
X = I.load_ptbxl250(db)
ex = D.excluded_ids() | set(pd.read_csv(I.OUT + "selected_K_100.csv").ecg_id)
ok = ~db.index.isin(ex) & np.isfinite(Y).all(1)
tr = np.flatnonzero((db.strat_fold.values <= 8) & ok)
va = np.flatnonzero((db.strat_fold.values == 9) & ok)
print("device", dev, "train", len(tr), "fold 9", len(va), "removed", int((~ok).sum()), flush=True)
mu, sd = Y[tr].mean(0), Y[tr].std(0)
Ytr = torch.from_numpy((Y[tr] - mu) / sd).to(dev)
mask = I.layout_masks(dev)
net = I.IntervalNet().to(dev)
print("parameters", sum(p.numel() for p in net.parameters()), flush=True)
opt = torch.optim.AdamW(net.parameters(), lr=1e-3, weight_decay=1e-2)
sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=EPOCHS)
lossf = nn.MSELoss()
gen = torch.Generator(device=dev)
gen.manual_seed(SEED)
vgen_seed = 1234


def batch(idx, emulate):
    xb = torch.from_numpy(np.asarray(X[np.sort(idx)], np.float32)).to(dev)
    return xb


@torch.no_grad()
def predict(idx, emulate, seed=vgen_seed):
    net.eval()
    g = torch.Generator(device=dev)
    g.manual_seed(seed)
    out = []
    for i in range(0, len(idx), 256):
        xb = torch.from_numpy(np.asarray(X[idx[i:i + 256]], np.float32)).to(dev)
        out.append(net(I.make_input(xb, mask, emulate, g)).cpu().numpy())
    return np.concatenate(out) * sd + mu


best, best_ep, bad, log = 1e9, -1, 0, []
for ep in range(1, EPOCHS + 1):
    net.train()
    perm = np.random.permutation(len(tr))
    tot, t0 = 0.0, time.time()
    for i in range(0, len(tr), BS):
        sel = np.sort(perm[i:i + BS])
        xb = torch.from_numpy(np.asarray(X[tr[sel]], np.float32)).to(dev)
        yb = Ytr[torch.from_numpy(sel).to(dev)]
        loss = lossf(net(I.make_input(xb, mask, True, gen)), yb)
        opt.zero_grad()
        loss.backward()
        opt.step()
        tot += float(loss) * len(sel)
    sched.step()
    pv = predict(va, True)
    mae = np.abs(pv - Y[va]).mean(0)
    score = float(np.mean(np.abs(pv - Y[va]) / sd))        # mean absolute error in standardised units, emulated digitiser input
    log.append(dict(epoch=ep, train_loss=tot / len(tr), fold9_mae_qrs_ms=mae[0], fold9_mae_qt_ms=mae[1], fold9_score=score, seconds=round(time.time() - t0, 1)))
    print(f"epoch {ep:2d} loss {tot / len(tr):.4f} fold-9 (emulated) MAE QRS {mae[0]:.2f} ms QT {mae[1]:.2f} ms score {score:.4f} {time.time() - t0:.0f}s", flush=True)
    if score < best:
        best, best_ep, bad = score, ep, 0
        torch.save(net.state_dict(), I.OUT + "model.pt")
    else:
        bad += 1
        if bad >= PATIENCE:
            print("early stop", flush=True)
            break
pd.DataFrame(log).to_csv(I.OUT + "training_log.csv", index=False)
net.load_state_dict(torch.load(I.OUT + "model.pt", map_location=dev))
po = predict(va, False)
pe = predict(va, True)
off_orig = (po - Y[va]).mean(0)
off_emul = (pe - Y[va]).mean(0)
json.dump(dict(seed=SEED, best_epoch=best_ep, targets=I.TARGETS, mu=mu.tolist(), sd=sd.tolist(), n_train=int(len(tr)), n_fold9=int(len(va)),
               fold9_original=dict(bias=off_orig.tolist(), mae=np.abs(po - Y[va]).mean(0).tolist()), fold9_emulated=dict(bias=off_emul.tolist(), mae=np.abs(pe - Y[va]).mean(0).tolist()),
               note="offsets_original = mean(pred - 12SL) on fold-9 original signals; subtract it. The extra digitised-input offset is fitted later on the development pages only."),
          open(I.OUT + "calibration.json", "w"), indent=1)
print("saved; best epoch", best_ep, "fold-9 bias (original)", off_orig.round(2), "MAE", np.abs(po - Y[va]).mean(0).round(2), flush=True)
