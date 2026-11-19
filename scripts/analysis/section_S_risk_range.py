"""Risk range on the fresh pictures of set S (descriptive; rules: docs/plan/analysis_plan_changes.md, 2026-11-18 'SET S', part 2). ONE run. Frozen pilot-3 risk models and age networks.
For each simulated photo of S: the estimate from the digitised picture (true age, or the age estimated from the picture) against the estimate from the clean PTB-XL signal with the true age; coverage of the displayed range.
Writes results/risk_pilot3/S_range.csv, SECTION_RISK3_S.md. Refuses to run twice.
Usage: demo\\.venv-gpu\\Scripts\\python.exe -I scripts/analysis/section_S_risk_range.py"""
import json
import os
import sys

import numpy as np
import pandas as pd
import torch
from scipy.stats import spearmanr

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "demo"))
from health import data as D  # noqa: E402
from health import intervals_ml as I  # noqa: E402
from health import risk as R  # noqa: E402

OUT = ROOT + "/results/risk_pilot3/"
if os.path.exists(OUT + "S_range.csv"):
    print("the S range test was already run once. Refusing to run twice.")
    raise SystemExit(1)
if not os.path.exists(ROOT + "/results/paper_s/S_pictures_done.flag"):
    print("set S is not fully digitised yet.")
    raise SystemExit(1)
dev = "cuda" if torch.cuda.is_available() else "cpu"
db = pd.read_csv(D.PT + "ptbxl_database.csv").set_index("ecg_id").sort_index()
X250 = I.load_ptbxl250(db)
pos = {e: n for n, e in enumerate(db.index)}
s = pd.read_csv(ROOT + "/results/paper_s/selected_S.csv")
items = []
for _, r in s.iterrows():
    f = ROOT + f"/results/paper_s/P_sim/dig_v2/{r.page}_{'straight' if int(r.page[1:]) % 2 else 'angled'}.npz"
    if os.path.exists(f):
        items.append((r.page, int(r.ecg_id), f))
print("pictures:", len(items), flush=True)
ages = np.clip(np.array([float(db.loc[e, "age"]) for _, e, _ in items]), 16, 90)
rawx = np.stack([np.asarray(X250[pos[e]], np.float32) for _, e, _ in items])
digx = np.stack([I.digitised_to_input250({k: v.astype(float) for k, v in np.load(f).items()}) for _, _, f in items])
ok = np.isfinite(digx).all(axis=(1, 2))
print("pictures with a complete digitised signal:", int(ok.sum()), flush=True)
info = json.load(open(OUT + "fold_info.json"))
mask_t = I.layout_masks(dev)
rn = []
for k, f in enumerate(info):
    net = R.RiskNet().to(dev)
    net.load_state_dict(torch.load(OUT + f"model_fold{k}.pt", map_location=dev))
    net.eval()
    rn.append((net, f["platt_a"], f["platt_b"]))
an = []
for k in range(5):
    net = I.IntervalNet(n_in=24, n_out=1).to(dev)
    net.load_state_dict(torch.load(OUT + f"agenet_fold{k}.pt", map_location=dev))
    net.eval()
    an.append(net)


def x24(arr, clean):
    out = []
    with torch.no_grad():
        for i in range(0, len(arr), 128):
            xb = torch.from_numpy(np.ascontiguousarray(arr[i:i + 128], dtype=np.float32)).to(dev)
            out.append((I.make_input(xb, mask_t, False) if clean else xb).cpu())
    return torch.cat(out)


def est_age(x):
    with torch.no_grad():
        a = np.mean([np.concatenate([n(x[i:i + 256].to(dev)).squeeze(1).cpu().numpy() for i in range(0, len(x), 256)]) for n in an], axis=0)
    return np.clip(a * R.AGE_SCALE + R.AGE_MEAN, 16, 90)


def risk(x, age_years):
    ag = torch.from_numpy(R.age_in(np.asarray(age_years, np.float32)).astype(np.float32))
    ps = []
    with torch.no_grad():
        for net, a, b in rn:
            lg = np.concatenate([net(x[i:i + 256].to(dev), ag[i:i + 256].to(dev)).squeeze(1).cpu().numpy() for i in range(0, len(x), 256)])
            ps.append(1.0 / (1.0 + np.exp(-(a * lg + b))))
    return np.mean(ps, axis=0)


xc, xd = x24(rawx, True), x24(np.nan_to_num(digx), False)
ad = est_age(xd)
p_clean, p_true, p_est = risk(xc, ages), risk(xd, ages), risk(xd, ad)
cat = lambda p: np.where(p < 0.05, 0, np.where(p < 0.15, 1, 2))  # noqa: E731
rows = []
for label, pe, hw in (("true age (typed or dataset age)", p_true, 0.10), ("age estimated from the picture (nothing typed)", p_est, 0.12)):
    d = np.abs(p_clean[ok] - pe[ok])
    rows.append(dict(version=label, n=int(ok.sum()), spearman=float(spearmanr(p_clean[ok], pe[ok])[0]), same_group=float(np.mean(cat(p_clean[ok]) == cat(pe[ok]))), mean_abs_diff=float(d.mean()),
                     coverage=float(np.mean(d <= hw)), half_width=hw, age_error=float(np.mean(np.abs(ad[ok] - ages[ok]))) if "estimated" in label else float("nan")))
T = pd.DataFrame(rows)
T.to_csv(OUT + "S_range.csv", index=False)
md = ["# Risk range on the fresh pictures of set S (descriptive)", "", "Rules written before the set was selected: docs/plan/analysis_plan_changes.md (2026-11-18 night, late, 'SET S', part 2). Frozen pilot-3 models; simulated phone photos of 300 random fold-10 recordings. NOT an outcome validation.", "",
      "| Age used for the picture | n | Spearman | Same group | Mean abs. difference | Range covers the clean value |", "|---|---|---|---|---|---|"]
for _, r in T.iterrows():
    md.append(f"| {r.version} | {int(r.n)} | {r.spearman:.2f} | {r.same_group * 100:.0f}% | {r.mean_abs_diff * 100:.1f} points | {r.coverage * 100:.0f}% (plus or minus {r.half_width * 100:.0f}) |")
md += ["", "Target: coverage at least 80%: " + ", ".join(f"{r.version}: {'met' if r.coverage >= 0.8 else 'NOT met'}" for _, r in T.iterrows()) + "."]
open(OUT + "SECTION_RISK3_S.md", "w", encoding="utf-8").write("\n".join(md))
print("\n".join(md))
