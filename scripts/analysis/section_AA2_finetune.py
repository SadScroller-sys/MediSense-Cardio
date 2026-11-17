"""Section AA second attempt: fine-tune the attempt-1 network on REAL DIGITISED development data (rules: docs/plan/analysis_plan_changes.md, 2026-11-15 evening).
Development data = clean digitised pages (new 100, fresh F, sealed G, sealed K), 140 straightened real phone photos, 120 simulated photos of G021-G080 (V2). NOT used: the fresh set L, the printed-paper H pages.
5-fold cross-validation grouped by recording chooses the number of epochs; then ONE final fine-tune on all development data. No fresh-test number is looked at.
Usage: demo\\.venv-gpu\\Scripts\\python.exe scripts/analysis/section_AA2_finetune.py"""
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

SEED, MAX_EP, BS = 42, 30, 32
torch.manual_seed(SEED)
np.random.seed(SEED)
dev = "cuda" if torch.cuda.is_available() else "cpu"
OUTD = I.OUT
COLS = ["QRS_Dur_Global", "QT_Int_Global", "QT_IntFridericia_Global"]
x12 = pd.read_csv(ROOT + "/data/ptbxl_plus/12sl_features.csv").set_index("ecg_id")
cal1 = json.load(open(OUTD + "calibration.json"))
mu1, sd1 = np.array(cal1["mu"]), np.array(cal1["sd"])
mu3, sd3 = float(x12.QT_IntFridericia_Global.mean()), float(x12.QT_IntFridericia_Global.std())
MU, SD = np.array([mu1[0], mu1[1], mu3]), np.array([sd1[0], sd1[1], sd3])

# ---------------------------------------------------------------- development items
ds = D.digitised_sets()
Kdf = pd.read_csv(OUTD + "selected_K_100.csv")
items = []
for _, r in ds[ds.set == "T2"].iterrows():
    items.append(dict(kind="page", name=r["name"], ecg_id=int(r.ecg_id), path=r.path))
for p, e in zip(Kdf.page, Kdf.ecg_id):
    f = OUTD + f"K/k_digitized_12lead/{p}.npz"
    if os.path.exists(f):
        items.append(dict(kind="page", name=p, ecg_id=int(e), path=f))
for _, r in ds[ds.set == "T3"].iterrows():
    items.append(dict(kind="real photo", name=r["name"], ecg_id=int(r.ecg_id), path=r.path))
selg = pd.read_csv(ROOT + "/results/fresh_g/selected_g_100.csv").set_index("page")
z = pd.read_csv(ROOT + "/results/analysis/sectionZ_all.csv")
for _, r in z[z.variant == "v2"].iterrows():
    f = ROOT + f"/results/fresh_sim/dig_v2/{r.photo}.npz"
    if os.path.exists(f) and not r["none"]:
        items.append(dict(kind="sim photo", name=r.photo, ecg_id=int(selg.loc[r.page, "ecg_id"]), path=f))
dfi = pd.DataFrame(items)
dfi = dfi[x12.loc[dfi.ecg_id, COLS].notna().all(1).values].reset_index(drop=True)
Xd = np.stack([I.digitised_to_input250({k: v.astype(float) for k, v in np.load(p).items()}) for p in dfi.path])
Y = x12.loc[dfi.ecg_id, COLS].values.astype(np.float32)
Yn = ((Y - MU) / SD).astype(np.float32)
print("development items", len(dfi), dfi.kind.value_counts().to_dict(), "recordings", dfi.ecg_id.nunique(), flush=True)


def load_base():
    net = I.IntervalNet(n_out=3).to(dev)
    sd_ = torch.load(OUTD + "model.pt", map_location=dev)
    hw, hb = sd_["head.weight"], sd_["head.bias"]
    w3 = hw[1] * float(sd1[1] / sd3)
    b3 = (hb[1] * float(sd1[1]) + float(mu1[1] - mu3)) / sd3
    sd_["head.weight"] = torch.cat([hw, w3[None]], 0)
    sd_["head.bias"] = torch.cat([hb, torch.tensor([float(b3)], device=hb.device)])
    net.load_state_dict(sd_)
    return net


def train_one(tr_idx, epochs, eval_idx=None):
    net = load_base()
    opt = torch.optim.AdamW([{"params": net.body.parameters(), "lr": 3e-5}, {"params": net.head.parameters(), "lr": 1e-4}], weight_decay=1e-2)
    lossf = nn.MSELoss()
    Xt, Yt = torch.from_numpy(Xd[tr_idx]).to(dev), torch.from_numpy(Yn[tr_idx]).to(dev)
    hist = []
    gen = torch.Generator(device=dev)
    gen.manual_seed(SEED)
    for ep in range(1, epochs + 1):
        net.train()
        perm = torch.randperm(len(tr_idx), device=dev, generator=gen)
        for i in range(0, len(tr_idx), BS):
            idx = perm[i:i + BS]
            if len(idx) < 4:
                continue
            xb = Xt[idx]
            xb = xb + 0.005 * torch.randn(xb.shape, device=dev, generator=gen) * (torch.arange(24, device=dev) < 12).float().view(1, 24, 1)
            loss = lossf(net(xb), Yt[idx])
            opt.zero_grad()
            loss.backward()
            opt.step()
        if eval_idx is not None:
            hist.append(evaluate(net, eval_idx))
    return net, hist


@torch.no_grad()
def evaluate(net, idx):
    net.eval()
    out = net(torch.from_numpy(Xd[idx]).to(dev)).cpu().numpy()
    return out * SD + MU


# ---------------------------------------------------------------- 5-fold CV grouped by recording
rec = dfi.ecg_id.values
uniq = np.unique(rec)
fold_of = dict(zip(uniq, np.random.RandomState(SEED).permutation(len(uniq)) % 5))
fold = np.array([fold_of[e] for e in rec])
cv_pred = {ep: np.full(Y.shape, np.nan, np.float32) for ep in range(1, MAX_EP + 1)}
t0 = time.time()
for k in range(5):
    tr, te = np.flatnonzero(fold != k), np.flatnonzero(fold == k)
    _, hist = train_one(tr, MAX_EP, te)
    for ep, p in enumerate(hist, start=1):
        cv_pred[ep][te] = p
    print(f"fold {k + 1} done {time.time() - t0:.0f}s", flush=True)
rows = []
for ep in range(1, MAX_EP + 1):
    e = cv_pred[ep] - Y
    rows.append(dict(epoch=ep, score=float(np.mean(np.abs(e) / SD)), **{f"mae_{c}": float(np.abs(e[:, j]).mean()) for j, c in enumerate(["qrs", "qt", "qtc"])}))
cvt = pd.DataFrame(rows)
cvt.to_csv(OUTD + "aa2_cv_by_epoch.csv", index=False)
best_ep = int(cvt.loc[cvt.score.idxmin(), "epoch"])
print("CV best epoch", best_ep, cvt.loc[cvt.epoch == best_ep].round(2).to_dict("records"), flush=True)

# CV picture at the chosen epoch (development numbers; may be looked at)
p = cv_pred[best_ep]
md = ["# Section AA second attempt: fine-tuning on digitised development data (cross-validation, development only)", "",
      f"Items {len(dfi)} ({dfi.kind.value_counts().to_dict()}) from {dfi.ecg_id.nunique()} recordings; 5-fold CV grouped by recording; chosen epochs {best_ep}. These are DEVELOPMENT numbers, not tests.", "",
      "| Items | Parameter | Typical error (ms) | Bias (ms) | Slope on 12SL |", "|---|---|---|---|---|"]
for kind in ["all"] + sorted(dfi.kind.unique()):
    m = np.ones(len(dfi), bool) if kind == "all" else (dfi.kind.values == kind)
    for j, c in enumerate(["QRS", "QT", "QTc direct"]):
        e = p[m, j] - Y[m, j]
        md.append(f"| {kind} ({int(m.sum())}) | {c} | {np.median(np.abs(e)):.1f} | {e.mean():+.1f} | {np.polyfit(Y[m, j], p[m, j], 1)[0]:.2f} |")
open(OUTD + "AA2_CV.md", "w", encoding="utf-8").write("\n".join(md) + "\n")
print("\n".join(md), flush=True)

# ---------------------------------------------------------------- final model on all development data
net, _ = train_one(np.arange(len(dfi)), best_ep)
torch.save(net.state_dict(), OUTD + "model_aa2.pt")
json.dump(dict(epochs=best_ep, mu=MU.tolist(), sd=SD.tolist(), targets=COLS, n_items=int(len(dfi)), seed=SEED, note="fine-tuned on all development items; no fresh test used"), open(OUTD + "calibration_aa2.json", "w"), indent=1)
print("final model saved", flush=True)
