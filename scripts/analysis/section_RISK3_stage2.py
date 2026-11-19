"""RISK PILOT 3, stage 2 (descriptive): does the displayed range hold on pictures? ONE run (rules: docs/plan/analysis_plan_changes.md, 2026-11-18 night). Frozen: the five pilot-3 risk models and the five age networks.
Items, ages and picture groups are built by exactly the same code as in pilot 2 (lines of section_RISK2_test.py that build `idf`, `rawx`, `digx`).
Writes results/risk_pilot3/stage2_transfer.csv, stage2_items.csv, SECTION_RISK3_STAGE2.md. Refuses to run twice.
Usage: demo\\.venv-gpu\\Scripts\\python.exe -I scripts/analysis/section_RISK3_stage2.py"""
import glob  # noqa: F401  (used by the pilot-2 item code executed below)
import json
import os
import sys

import numpy as np
import pandas as pd
import torch
from scipy.stats import spearmanr

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "demo"))
from health import data as D  # noqa: E402,F401
from health import intervals_ml as I  # noqa: E402
from health import risk as R  # noqa: E402

OUT = os.path.join(ROOT, "results", "risk_pilot3") + os.sep
if os.path.exists(OUT + "stage2_transfer.csv"):
    print("stage 2 was already run once: results are in results/risk_pilot3/. Refusing to run twice.")
    raise SystemExit(1)
dev = "cuda" if torch.cuda.is_available() else "cpu"

# ---- items: the SAME code as pilot 2 (lines 122 to 149 of section_RISK2_test.py)
src = open(os.path.join(ROOT, "scripts", "analysis", "section_RISK2_test.py"), encoding="utf-8").read().splitlines()
start = next(i for i, ln in enumerate(src) if ln.startswith("db = pd.read_csv(D.PT"))
end = next(i for i, ln in enumerate(src) if ln.startswith("a_full = R.age_in(ages)"))
ns = dict(globals())
exec("\n".join(src[start:end + 1]), ns)
idf, rawx, digx, ages = ns["idf"], ns["rawx"], ns["digx"], ns["ages"]
print("items:", len(idf), flush=True)

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


def est_age(x):                                   # (N, 24, 2500) -> years
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


xc, xd = x24(rawx, True), x24(digx, False)
ac, ad = est_age(xc), est_age(xd)
p_clean_true = risk(xc, ages)            # clean signal, true age
p_dig_true = risk(xd, ages)              # picture, true age (typed or dataset age)
p_dig_est = risk(xd, ad)                 # picture, age estimated from the picture (nothing typed)
cat = lambda p: np.where(p < 0.05, 0, np.where(p < 0.15, 1, 2))  # noqa: E731
rows = []
for g, sub in idf.groupby("group", sort=False):
    ix = sub.index.values
    for label, pd_, hw in (("true age on both (typed or dataset age)", p_dig_true, 0.10), ("age estimated from the picture (nothing typed)", p_dig_est, 0.12)):
        rows.append(dict(group=g, version=label, n=len(ix), spearman=float(spearmanr(p_clean_true[ix], pd_[ix])[0]), same_group=float(np.mean(cat(p_clean_true[ix]) == cat(pd_[ix]))),
                         mean_abs_diff=float(np.mean(np.abs(p_clean_true[ix] - pd_[ix]))), coverage=float(np.mean(np.abs(p_clean_true[ix] - pd_[ix]) <= hw)), half_width=hw,
                         age_error=float(np.mean(np.abs(ad[ix] - ages[ix]))) if "estimated" in label else float("nan")))
T = pd.DataFrame(rows)
T.to_csv(OUT + "stage2_transfer.csv", index=False)
pd.DataFrame(dict(group=idf.group, ecg_id=idf.ecg_id, age=ages, age_est_picture=ad, p_clean_true=p_clean_true, p_pic_true=p_dig_true, p_pic_est=p_dig_est)).to_csv(OUT + "stage2_items.csv", index=False)
gated = T[~T.group.str.contains("not gated")]
md = ["# Risk pilot 3, stage 2 (descriptive): does the displayed range hold on pictures?", "",
      "Rules written before the run: docs/plan/analysis_plan_changes.md (2026-11-18 night). Frozen pilot-3 models; same items and ages as pilot 2. NOT an outcome validation.", "",
      "| Group | Age used for the picture | n | Spearman | Same group | Mean abs. difference | Range covers the clean value |", "|---|---|---|---|---|---|---|"]
for _, r in T.iterrows():
    md.append(f"| {r.group} | {r.version} | {int(r.n)} | {r.spearman:.2f} | {r.same_group * 100:.0f}% | {r.mean_abs_diff * 100:.1f} points | {r.coverage * 100:.0f}% (plus or minus {r.half_width * 100:.0f}) |")
ok = {v: bool((gated[gated.version == v].coverage >= 0.80).all()) for v in gated.version.unique()}
md += ["", "## Descriptive target: coverage at least 80% in every gated group", ""] + [f"- {v}: {'met' if k else 'NOT met'}" for v, k in ok.items()]
open(OUT + "SECTION_RISK3_STAGE2.md", "w", encoding="utf-8").write("\n".join(md))
print("\n".join(md))
