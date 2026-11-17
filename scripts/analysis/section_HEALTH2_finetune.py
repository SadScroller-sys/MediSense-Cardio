"""Heart health module, SECOND MODEL: fine-tune model 1 on real digitised development data (rules: docs/plan/analysis_plan_changes.md, 2026-11-15 night, with Amendment 1).
Development data = clean digitised pages (new 100, fresh F, sealed G, sealed K), 140 real phone photos, 118 simulated photos of G021-G080 (V2). NOT used: L, M, H. 5-fold CV grouped by recording
chooses the epochs; Platt calibration and Youden thresholds are fitted on the out-of-fold predictions; ONE final model. Usage: demo\\.venv-gpu\\Scripts\\python.exe scripts/analysis/section_HEALTH2_finetune.py"""
import json
import os
import sys

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, roc_curve

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "demo"))
from health import data as D  # noqa: E402
from health import model as M  # noqa: E402

SEED, MAX_EP, BS = 42, 30, 32
torch.manual_seed(SEED)
np.random.seed(SEED)
dev = "cuda" if torch.cuda.is_available() else "cpu"
OUT = M.OUT
db, Y = D.load_db()
ds = D.digitised_sets()
Kdf = pd.read_csv(ROOT + "/results/intervals_ml/selected_K_100.csv")
items = [dict(kind="page", ecg_id=int(r.ecg_id), path=r.path) for _, r in ds[ds.set == "T2"].iterrows()]
for p, e in zip(Kdf.page, Kdf.ecg_id):
    f = ROOT + f"/results/intervals_ml/K/k_digitized_12lead/{p}.npz"
    if os.path.exists(f):
        items.append(dict(kind="page", ecg_id=int(e), path=f))
items += [dict(kind="real photo", ecg_id=int(r.ecg_id), path=r.path) for _, r in ds[ds.set == "T3"].iterrows()]
selg = pd.read_csv(ROOT + "/results/fresh_g/selected_g_100.csv").set_index("page")
z = pd.read_csv(ROOT + "/results/analysis/sectionZ_all.csv")
for _, r in z[z.variant == "v2"].iterrows():
    f = ROOT + f"/results/fresh_sim/dig_v2/{r.photo}.npz"
    if os.path.exists(f) and not r["none"]:
        items.append(dict(kind="sim photo", ecg_id=int(selg.loc[r.page, "ecg_id"]), path=f))
dfi = pd.DataFrame(items)
Xd = np.stack([D.digitised_to_input({k: v.astype(float) for k, v in np.load(p).items()}) for p in dfi.path])
Yd = Y.loc[dfi.ecg_id].values.astype(np.float32)
print("development items", len(dfi), dfi.kind.value_counts().to_dict(), "recordings", dfi.ecg_id.nunique(), "positives", Yd.sum(0).astype(int).tolist(), flush=True)
mask = M.layout_masks(dev)


def train_one(tr_idx, epochs, eval_idx=None):
    net = M.EcgNet().to(dev)
    net.load_state_dict(torch.load(OUT + "model.pt", map_location=dev))
    opt = torch.optim.AdamW([{"params": net.body.parameters(), "lr": 3e-5}, {"params": net.head.parameters(), "lr": 1e-4}], weight_decay=1e-2)
    lossf = nn.BCEWithLogitsLoss()
    Xt, Yt = torch.from_numpy(Xd[tr_idx]).to(dev), torch.from_numpy(Yd[tr_idx]).to(dev)
    gen = torch.Generator(device=dev)
    gen.manual_seed(SEED)
    hist = []
    for ep in range(1, epochs + 1):
        net.train()
        perm = torch.randperm(len(tr_idx), device=dev, generator=gen)
        for i in range(0, len(tr_idx), BS):
            idx = perm[i:i + BS]
            if len(idx) < 4:
                continue
            xb = Xt[idx] + 0.005 * torch.randn(Xt[idx].shape, device=dev, generator=gen) * (torch.arange(24, device=dev) < 12).float().view(1, 24, 1)
            loss = lossf(net(xb), Yt[idx])
            opt.zero_grad()
            loss.backward()
            opt.step()
        if eval_idx is not None:
            net.eval()
            with torch.no_grad():
                hist.append(net(torch.from_numpy(Xd[eval_idx]).to(dev)).cpu().numpy())
    return net, hist


rec = dfi.ecg_id.values
uniq = np.unique(rec)
fold_of = dict(zip(uniq, np.random.RandomState(SEED).permutation(len(uniq)) % 5))
fold = np.array([fold_of[e] for e in rec])
oof = {ep: np.full(Yd.shape, np.nan, np.float32) for ep in range(1, MAX_EP + 1)}
for k in range(5):
    tr, te = np.flatnonzero(fold != k), np.flatnonzero(fold == k)
    _, hist = train_one(tr, MAX_EP, te)
    for ep, p in enumerate(hist, start=1):
        oof[ep][te] = p
    print("fold", k + 1, "done", flush=True)


def mean_auc(L):
    a = [roc_auc_score(Yd[:, c], L[:, c]) for c in range(6) if 5 <= Yd[:, c].sum() <= len(Yd) - 5]
    return float(np.mean(a))


scores = {ep: mean_auc(oof[ep]) for ep in oof}
best_ep = max(scores, key=scores.get)
print("CV best epoch", best_ep, "mean AUROC", round(scores[best_ep], 4), flush=True)
L = oof[best_ep]
platt, thr, rows = {}, {}, []
for k, c in enumerate(D.CLASSES):
    lr = LogisticRegression(C=1e6, max_iter=1000).fit(L[:, [k]], Yd[:, k])
    platt[c] = dict(a=float(lr.coef_[0, 0]), b=float(lr.intercept_[0]))
    p = lr.predict_proba(L[:, [k]])[:, 1]
    fpr, tpr, th = roc_curve(Yd[:, k], p)
    thr[c] = float(th[np.argmax(tpr - fpr)])
    for kind in ["all"] + sorted(dfi.kind.unique()):
        m = np.ones(len(dfi), bool) if kind == "all" else (dfi.kind.values == kind)
        if 5 <= Yd[m, k].sum() <= m.sum() - 5:
            rows.append(dict(items=kind, cls=c, n=int(m.sum()), positives=int(Yd[m, k].sum()), auroc_oof=roc_auc_score(Yd[m, k], L[m, k])))
pd.DataFrame(rows).to_csv(OUT + "health2_cv_auroc.csv", index=False)
print(pd.DataFrame(rows).pivot(index="cls", columns="items", values="auroc_oof").round(3).to_string(), flush=True)
net, _ = train_one(np.arange(len(dfi)), best_ep)
torch.save(net.state_dict(), OUT + "model_v2.pt")
json.dump(dict(epochs=best_ep, n_items=int(len(dfi)), seed=SEED, platt=platt, thresholds=thr, classes=D.CLASSES, note="Platt and Youden fitted on out-of-fold development predictions; no fresh set used"), open(OUT + "calibration_v2.json", "w"), indent=1)
print("final model saved", flush=True)
