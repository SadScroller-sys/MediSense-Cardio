"""Train the QRS/QT network on doctor-marked public data (rules: docs/plan/analysis_plan_changes.md 2026-11-16 night). LUDB records 1-140 + QT Database windows; validation LUDB 141-160 (damaged). Test records 161-200 are NOT touched here.
Usage: demo\.venv-gpu\Scripts\python.exe -I scripts/analysis/qt_public_train.py"""
import json
import os
import sys

import numpy as np
import torch
import torch.nn.functional as Fn

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "demo"))
from health import intervals_ml as I  # noqa: E402

OUT = ROOT + "/results/qt_public/"
dev = "cuda" if torch.cuda.is_available() else "cpu"
torch.manual_seed(70)
np.random.seed(70)
L = np.load(OUT + "ludb.npz")
Qd = np.load(OUT + "qtdb.npz")
rec = L["rec"]
tr = rec <= 140
va = (rec >= 141) & (rec <= 160)
Xl, yl = L["X"], np.stack([L["qrs"], L["qt"]], 1)
# 500 Hz -> 250 Hz already done in the parser (block mean of 2); QTDB is 250 Hz
Xtr = np.concatenate([Xl[tr], Qd["X"]]); ytr = np.concatenate([yl[tr], np.stack([Qd["qrs"], Qd["qt"]], 1)])
w_tr = np.concatenate([np.ones(tr.sum()), np.full(len(Qd["X"]), 0.5)]).astype(np.float32)
Xva, yva = Xl[va], yl[va]
print("train items", len(Xtr), "(LUDB", int(tr.sum()), "+ QTDB windows", len(Qd["X"]), ") | validation", len(Xva), flush=True)
mask = I.layout_masks(dev)
MU = torch.tensor([110.0, 420.0], device=dev)
SD = torch.tensor([25.0, 45.0], device=dev)


def damage(x, gen=None):
    """stronger than I.emulate: extra smoothing, per-lead gain, dropped pieces, more noise and wander, on top of I.emulate."""
    B = x.shape[0]
    x = I.emulate(x, gen)
    x = x * (0.8 + 0.4 * torch.rand(B, 12, 1, device=x.device, generator=gen))
    x = x + (0.01 + 0.03 * torch.rand(B, 1, 1, device=x.device, generator=gen)) * torch.randn(x.shape, device=x.device, generator=gen)
    s = I._smooth(x, 1.0 + 2.0 * float(np.random.rand()))
    sel = torch.rand(B, device=x.device, generator=gen) < 0.5
    x = torch.where(sel.view(-1, 1, 1), s, x)
    # dropped pieces: hold the last value for 60-200 ms in 30% of leads
    for _ in range(2):
        st = int(np.random.randint(0, I.T - 60)); ln = int(np.random.randint(15, 50))
        m = (torch.rand(B, 12, 1, device=x.device, generator=gen) < 0.15)
        seg = x[:, :, st:st + 1].expand(-1, -1, min(ln, I.T - st))
        x[:, :, st:st + seg.shape[2]] = torch.where(m, seg, x[:, :, st:st + seg.shape[2]])
    return x


def stretch(x, y):
    """random time stretch 0.85-1.15 of each item; durations scale by the same factor."""
    B = x.shape[0]
    out = torch.empty_like(x)
    s = 0.85 + 0.3 * torch.rand(B, device=x.device)
    for i in range(B):
        n = max(int(round(I.T * float(s[i]))), 400)
        z = Fn.interpolate(x[i:i + 1], size=n, mode="linear", align_corners=False)[0]
        if n >= I.T:
            a = int(torch.randint(0, n - I.T + 1, (1,)))
            out[i] = z[:, a:a + I.T]
        else:
            out[i] = z.repeat(1, (I.T // n) + 1)[:, :I.T]
    return out, y * (n_ratio := s.view(-1, 1))


def batch(X, y, idx, train, gen=None):
    x = torch.from_numpy(X[idx]).to(dev); t = torch.from_numpy(y[idx]).float().to(dev)
    if train:
        x, t = stretch(x, t)
        x = torch.roll(x, int(np.random.randint(0, I.T)), dims=2)
    return I.make_input(damage(x, gen), mask), (t - MU) / SD


net = I.IntervalNet(n_in=24, n_out=2).to(dev)
opt = torch.optim.AdamW(net.parameters(), 1e-3, weight_decay=1e-2)
EP, BS = 120, 32
sched = torch.optim.lr_scheduler.OneCycleLR(opt, 2e-3, total_steps=EP * int(np.ceil(len(Xtr) / BS)))
gv = torch.Generator(device=dev); gv.manual_seed(5)
best, hist = 1e9, []
for ep in range(EP):
    net.train()
    perm = np.random.permutation(len(Xtr))
    for k in range(0, len(perm), BS):
        idx = perm[k:k + BS]
        if len(idx) < 4:
            continue
        xb, tb = batch(Xtr, ytr, idx, True)
        w = torch.from_numpy(w_tr[idx]).to(dev)
        loss = (Fn.smooth_l1_loss(net(xb), tb, reduction="none").mean(1) * w).mean()
        opt.zero_grad(); loss.backward(); opt.step(); sched.step()
    net.eval()
    with torch.no_grad():
        gv.manual_seed(5); st0 = np.random.get_state(); np.random.seed(5)
        xv, _ = batch(Xva, yva, np.arange(len(Xva)), False, gv); np.random.set_state(st0)
        pr = net(xv) * SD + MU
    err = (pr.cpu().numpy() - yva)
    mae = np.abs(err).mean(0)
    hist.append(dict(epoch=ep, qrs_mae=float(mae[0]), qt_mae=float(mae[1])))
    sc = mae[0] / 10 + mae[1] / 20
    if sc < best:
        best = sc
        torch.save(net.state_dict(), OUT + "model.pt")
        bj = dict(epoch=ep, qrs_mae=float(mae[0]), qt_mae=float(mae[1]), qrs_bias=float(err[:, 0].mean()), qt_bias=float(err[:, 1].mean()))
    if ep % 10 == 0:
        print(ep, "val MAE QRS %.1f QT %.1f ms | best epoch %d" % (mae[0], mae[1], bj["epoch"]), flush=True)
json.dump(dict(best=bj, history=hist, train_items=int(len(Xtr)), val_items=int(len(Xva)), note="validation = LUDB 141-160, damaged; model.pt = best validation epoch"), open(OUT + "train_status.json", "w"), indent=1)
print("best", bj)
