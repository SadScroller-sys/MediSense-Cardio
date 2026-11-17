"""T1: frozen model on LUDB test records 161-200 (doctor marks), clean and damaged (3 fixed damage draws), run ONCE. Writes results/qt_public/T1_metrics.csv.
Usage: demo\.venv-gpu\Scripts\python.exe -I scripts/analysis/qt_public_test_T1.py"""
import os
import sys

import numpy as np
import pandas as pd
import torch

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "demo"))
from health import intervals_ml as I  # noqa: E402

OUT = ROOT + "/results/qt_public/"
if os.path.exists(OUT + "T1_metrics.csv"):
    sys.exit("T1 was already run once.")
exec(open(ROOT + "/scripts/analysis/qt_public_train.py").read().split("def damage")[1].split("def stretch")[0].join(["def damage", ""]).replace("def damage", "def damage", 1)) if False else None
dev = "cuda" if torch.cuda.is_available() else "cpu"
src = open(ROOT + "/scripts/analysis/qt_public_train.py").read()
ns = dict(np=np, torch=torch, I=I)
exec("def damage" + src.split("def damage")[1].split("def stretch")[0], ns)
L = np.load(OUT + "ludb.npz")
te = L["rec"] >= 161
X, y = L["X"][te], np.stack([L["qrs"], L["qt"]], 1)[te]
net = I.IntervalNet(n_in=24, n_out=2).to(dev)
net.load_state_dict(torch.load(OUT + "model.pt", map_location=dev))
net.eval()
mask = I.layout_masks(dev)
MU = torch.tensor([110.0, 420.0], device=dev)
SD = torch.tensor([25.0, 45.0], device=dev)
rows = []
for cond, seed in (("clean", None), ("damaged", 11), ("damaged", 12), ("damaged", 13)):
    x = torch.from_numpy(X).to(dev)
    if seed is not None:
        np.random.seed(seed); g = torch.Generator(device=dev); g.manual_seed(seed)
        x = ns["damage"](x, g)
    with torch.no_grad():
        p = (net(I.make_input(x, mask)) * SD + MU).cpu().numpy()
    for k, nm in enumerate(("QRS", "QT")):
        e = p[:, k] - y[:, k]
        sl = np.polyfit(y[:, k], p[:, k], 1)[0]
        w = 20 if nm == "QRS" else 40
        rows.append(dict(condition=cond, seed=seed, target=nm, n=len(e), mae=np.abs(e).mean(), median_abs=np.median(np.abs(e)), within=float((np.abs(e) <= w).mean()), within_ms=w, bias=e.mean(), slope=sl,
                         pass_rule=bool((np.abs(e).mean() <= (10 if nm == "QRS" else 20)) and (np.abs(e) <= w).mean() >= 0.9 and abs(e.mean()) <= (5 if nm == "QRS" else 10) and sl >= 0.8)))
T = pd.DataFrame(rows)
T.to_csv(OUT + "T1_metrics.csv", index=False)
print(T.round(3).to_string(index=False))
