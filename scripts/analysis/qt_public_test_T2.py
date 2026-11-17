"""T2: frozen public-data QRS/QT model on set P (drawn pages or simulated photos) against the PTB-XL+ 12SL reference, each part ONCE (rules: docs/plan/analysis_plan_changes.md 2026-11-16 night).
QT is AVAILABLE in the app only if T1 passed (it did: results/qt_public/T1_metrics.csv) AND on the simulated photos: typical error (mean absolute) <= 20 ms, >= 90% within 40 ms, |bias| <= 10 ms, slope >= 0.8. QRS failed T1 and stays not measured; it is reported only.
Long-QT (reference >= 450 ms) and short-QT (<= 350 ms) tails are reported separately. Writes results/qt_public/T2_<part>.csv and, for sim, T2_status.json.
Usage: demo\.venv-gpu\Scripts\python.exe -I scripts/analysis/qt_public_test_T2.py pages|sim"""
import glob
import json
import os
import sys

import numpy as np
import pandas as pd
import torch

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "demo"))
from health import intervals_ml as I  # noqa: E402

PART = sys.argv[1]
assert PART in ("pages", "sim")
OUT = ROOT + "/results/qt_public/"
PP = ROOT + "/results/paper_p/"
if os.path.exists(OUT + f"T2_{PART}.csv"):
    sys.exit(f"T2 part '{PART}' was already run once.")
dev = "cuda" if torch.cuda.is_available() else "cpu"
net = I.IntervalNet(n_in=24, n_out=2).to(dev)
net.load_state_dict(torch.load(OUT + "model.pt", map_location=dev))
net.eval()
MU = np.array([110.0, 420.0]); SD = np.array([25.0, 45.0])
sel = pd.read_csv(PP + "selected_P.csv").set_index("page")
x12 = pd.read_csv(ROOT + "/data/ptbxl_plus/12sl_features.csv").set_index("ecg_id")
items = []
if PART == "pages":
    items = [(p, p, PP + f"p_digitized_12lead/{p}.npz") for p in sel.index]
else:
    for f in sorted(glob.glob(PP + "P_sim/dig_v2/P*.npz")):
        nm = os.path.basename(f)[:-4]
        items.append((nm, nm[:4], f))
X, used = [], []
for nm, page, f in items:
    leads = {k: np.asarray(v, float) for k, v in np.load(f).items()}
    if leads.get("II") is None or np.isfinite(leads["II"]).sum() < 500:
        continue
    X.append(I.digitised_to_input250(leads)); used.append((nm, page))
X = np.stack(X)
with torch.no_grad():
    pr = np.concatenate([net(torch.from_numpy(np.ascontiguousarray(X[i:i + 64])).to(dev)).cpu().numpy() for i in range(0, len(X), 64)]) * SD + MU
ids = sel.loc[[p for _, p in used], "ecg_id"].astype(int).values
ref = x12.loc[ids, ["QRS_Dur_Global", "QT_Int_Global"]].values.astype(float)
rows = []
for k, nm, w, tmae, tbias in ((0, "QRS", 20, 10, 5), (1, "QT", 40, 20, 10)):
    ok = np.isfinite(ref[:, k])
    e = pr[ok, k] - ref[ok, k]
    sl = float(np.polyfit(ref[ok, k], pr[ok, k], 1)[0])
    r = dict(part=PART, target=nm, n=int(ok.sum()), mae=float(np.abs(e).mean()), median_abs=float(np.median(np.abs(e))), within=float((np.abs(e) <= w).mean()), within_ms=w, bias=float(e.mean()), slope=sl,
             pass_rule=bool(np.abs(e).mean() <= tmae and (np.abs(e) <= w).mean() >= 0.9 and abs(e.mean()) <= tbias and sl >= 0.8))
    if nm == "QT":
        lo, hi = ok & (ref[:, 1] <= 350), ok & (ref[:, 1] >= 450)
        r.update(n_short=int(lo.sum()), short_bias=float((pr[lo, 1] - ref[lo, 1]).mean()) if lo.any() else float("nan"), n_long=int(hi.sum()), long_bias=float((pr[hi, 1] - ref[hi, 1]).mean()) if hi.any() else float("nan"))
    rows.append(r)
T = pd.DataFrame(rows)
T.to_csv(OUT + f"T2_{PART}.csv", index=False)
print(T.round(3).to_string(index=False))
if PART == "sim":
    t1 = pd.read_csv(OUT + "T1_metrics.csv")
    t1_qt = bool(t1[t1.target == "QT"].pass_rule.all())
    qt_ok = bool(T[T.target == "QT"].pass_rule.iloc[0]) and t1_qt
    pg = OUT + "T2_pages.csv"
    json.dump(dict(qt_available=qt_ok, t1_qt_pass_all_conditions=t1_qt, qt_sim=T[T.target == "QT"].iloc[0].to_dict(), rule="docs/plan/analysis_plan_changes.md 2026-11-16 night", qrs_available=False), open(OUT + "T2_status.json", "w"), indent=1, default=float)
    print("QT available in the app:", qt_ok)
