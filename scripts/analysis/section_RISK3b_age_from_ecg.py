"""RISK PILOT 3b: age estimated from the ECG, so the risk range can be shown without typing an age. ONE run (rules: docs/plan/analysis_plan_changes.md, 2026-11-18 evening).
For each of the five pilot-3 folds: train an age network on at most 30,000 patients outside the held-out fold, predict the age of the held-out patients, then apply the pilot-3 risk model of that fold with the ESTIMATED age.
Writes results/risk_pilot3/oof_agepred.csv, agenet_fold*.pt, agenet_info.json. Refuses to run twice.
Usage: demo\\.venv-gpu\\Scripts\\python.exe -I scripts/analysis/section_RISK3b_age_from_ecg.py"""
import copy
import hashlib
import json
import os
import sys

import numpy as np
import pandas as pd
import torch
import torch.nn as nn

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "demo"))
from health import intervals_ml as I  # noqa: E402
from health import risk as R  # noqa: E402

H = 5.0
DD = os.path.join(ROOT, "data", "code15") + os.sep
OUT = os.path.join(ROOT, "results", "risk_pilot3") + os.sep
if os.path.exists(OUT + "oof_agepred.csv"):
    print("pilot 3b was already run once: its result is in results/risk_pilot3/. Refusing to run twice.")
    raise SystemExit(1)
SEED, EPOCHS, PATIENCE, BS, MAXN = 42, 12, 4, 256, 30000
dev = "cuda" if torch.cuda.is_available() else "cpu"
X = np.load(DD + "risk2_x250_f16.npy", mmap_mode="r")
m = pd.read_csv(DD + "risk2_meta.csv")
h = lambda tag, pid: int(hashlib.md5(f"{tag}-{pid}".encode()).hexdigest(), 16) % 100  # noqa: E731
m["fold"] = m.patient_id.map(lambda p: h("63", p) % 5)
m["vb"] = m.patient_id.map(lambda p: h("63v", p))
ev = m.death & (m.timey <= H)
ok = (ev | ((~m.death) & (m.timey >= H))).values
y = ev.astype(np.float32).values
age = m.age.values.astype(np.float32)
age_ok = np.isfinite(age) & (age >= 16) & (age <= 90)
ain = R.age_in(np.where(age_ok, age, 60.0)).astype(np.float32)       # standardised age (the network's own scale)
mask = I.layout_masks(dev)
info_risk = json.load(open(OUT + "fold_info.json"))
all_idx = np.flatnonzero(ok)
rng = np.random.RandomState(SEED)


@torch.no_grad()
def predict_age(net, idx, emulate=False):
    net.eval()
    g = torch.Generator(device=dev)
    g.manual_seed(1234)
    out = []
    for i in range(0, len(idx), 512):
        ii = np.sort(idx[i:i + 512])
        xb = torch.from_numpy(np.asarray(X[ii], np.float32)).to(dev)
        out.append(net(I.make_input(xb, mask, emulate, g)).squeeze(1).cpu().numpy())
    return np.concatenate(out) * R.AGE_SCALE + R.AGE_MEAN


rows, info = [], []
for k in range(5):
    torch.manual_seed(SEED + k)
    np.random.seed(SEED + k)
    pool = np.flatnonzero((m.fold.values != k) & age_ok)
    if len(pool) > MAXN:
        pool = np.sort(rng.choice(pool, MAXN, replace=False))
    va = np.sort(pool[m.vb.values[pool] < 10])
    tr = pool[m.vb.values[pool] >= 10]
    te = np.sort(all_idx[m.fold.values[all_idx] == k])
    print(f"fold {k}: age network train {len(tr)}, validation {len(va)}, held-out risk patients {len(te)}", flush=True)
    net = I.IntervalNet(n_in=24, n_out=1).to(dev)
    opt = torch.optim.AdamW(net.parameters(), lr=1e-3, weight_decay=1e-2)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=EPOCHS)
    lossf = nn.MSELoss()
    gen = torch.Generator(device=dev)
    gen.manual_seed(SEED + k)
    best, best_ep, bad, best_state = 1e9, -1, 0, None
    for ep in range(1, EPOCHS + 1):
        net.train()
        perm = np.random.permutation(len(tr))
        for i in range(0, len(tr), BS):
            sel = np.sort(tr[perm[i:i + BS]])
            xb = torch.from_numpy(np.asarray(X[sel], np.float32)).to(dev)
            loss = lossf(net(I.make_input(xb, mask, True, gen)).squeeze(1), torch.from_numpy(ain[sel]).to(dev))
            opt.zero_grad()
            loss.backward()
            opt.step()
        sched.step()
        mae = float(np.mean(np.abs(predict_age(net, va, True) - age[va])))
        print(f"  epoch {ep:2d} validation age error {mae:.2f} years", flush=True)
        if mae < best:
            best, best_ep, bad, best_state = mae, ep, 0, copy.deepcopy(net.state_dict())
        else:
            bad += 1
            if bad >= PATIENCE:
                break
    net.load_state_dict(best_state)
    torch.save(best_state, OUT + f"agenet_fold{k}.pt")
    a_pred = predict_age(net, te, False)
    # pilot-3 risk model of the same fold, with the ESTIMATED age
    rnet = R.RiskNet().to(dev)
    rnet.load_state_dict(torch.load(OUT + f"model_fold{k}.pt", map_location=dev))
    rnet.eval()
    pa, pb = info_risk[k]["platt_a"], info_risk[k]["platt_b"]
    lg = []
    with torch.no_grad():
        g = torch.Generator(device=dev)
        g.manual_seed(1234)
        for i in range(0, len(te), 512):
            ii = np.sort(te[i:i + 512])
            xb = torch.from_numpy(np.asarray(X[ii], np.float32)).to(dev)
            ag = torch.from_numpy(R.age_in(a_pred[i:i + 512]).astype(np.float32)).to(dev)
            lg.append(rnet(I.make_input(xb, mask, False, g), ag).squeeze(1).cpu().numpy())
    lg = np.concatenate(lg)
    p_pred = 1.0 / (1.0 + np.exp(-(pa * lg + pb)))
    info.append(dict(fold=k, best_epoch=best_ep, val_age_mae=float(best), heldout_age_mae=float(np.mean(np.abs(a_pred - age[te])))))
    print(f"fold {k}: best epoch {best_ep}, validation age error {best:.2f}, held-out age error {info[-1]['heldout_age_mae']:.2f}", flush=True)
    for j, i in enumerate(te):
        rows.append((int(m.patient_id.values[i]), k, int(y[i]), float(age[i]), float(a_pred[j]), float(lg[j]), float(p_pred[j])))
pd.DataFrame(rows, columns=["patient_id", "fold", "y", "age", "age_pred", "logit_pred", "p_pred"]).to_csv(OUT + "oof_agepred.csv", index=False)
json.dump(info, open(OUT + "agenet_info.json", "w"), indent=1)
print("saved", len(rows), "predictions", flush=True)
