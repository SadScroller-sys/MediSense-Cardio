"""New operating point for the 8 research-only patterns (rules: docs/plan/analysis_plan_changes.md, 2026-11-16 late night 'NEW OPERATING POINT'). EXPLORATORY.
Thresholds are chosen ONLY from validation data (network A: PTB-XL fold 9 without our digitised recordings; network B: CODE-15% validation split) so that specificity there is 0.97 (primary), 0.95 and 0.99 (sensitivity analysis).
Then, on the sets seen before (T2 drawn pages, T3 screen photos, set N drawn pages, set N simulated photos), sensitivity, specificity and the share of clean items with at least one flag are reported at the old and the new thresholds.
Writes results/find2_op/: thresholds_v2.json, op_per_pattern.csv, op_aggregate.csv, SECTION_OP.md. Refuses to run twice (--force to override).
Usage: demo\\.venv-gpu\\Scripts\\python.exe -I scripts/analysis/section_OP_thresholds.py"""
import json
import os
import sys

import numpy as np
import pandas as pd
import torch

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "demo"))
from health import data as D  # noqa: E402
from health import find2 as F  # noqa: E402
from health import model as M  # noqa: E402

OUT = ROOT + "/results/find2_op/"
os.makedirs(OUT, exist_ok=True)
if os.path.exists(OUT + "thresholds_v2.json") and "--force" not in sys.argv:
    sys.exit("The new operating point was already derived once (rule: no further tuning).")
PAT = [("A", "ASMI"), ("A", "NDT"), ("A", "LVH"), ("A", "LAFB"), ("A", "IRBBB"), ("B", "AF"), ("B", "LBBB"), ("B", "1dAVb")]
SPECS = {"s95": 0.95, "s97": 0.97, "s99": 0.99}
mask = M.layout_masks("cpu")
db, _ = D.load_db()
YA, YB = F.labels_A(db), F.labels_B_from_ptbxl(db)


def load(folder, names):
    cal = json.load(open(folder + "calibration.json"))
    net = M.EcgNet(n_out=len(names))
    net.load_state_dict(torch.load(folder + "model.pt", map_location="cpu"))
    net.eval()
    return net, np.array([cal["platt"][c]["a"] for c in names]), np.array([cal["platt"][c]["b"] for c in names])


netA, aA, bA = load(F.OUT_A, F.A_CODES)
netB, aB, bB = load(F.OUT_B, F.B_LABELS)
stA = json.load(open(F.OUT_A + "status.json"))["classes"]
stB = json.load(open(F.OUT_B + "status.json"))["classes"]
old = {f"{m}:{c}": (stA if m == "A" else stB)[c]["threshold"] for m, c in PAT}

# ---------------------------------------------------------------- validation probabilities (clean recordings, no digitised data)
X = D.load_ptbxl100(db)
ok = ~db.index.isin(D.excluded_ids())
f9 = np.flatnonzero((db.strat_fold.values == 9) & ok)
Z = np.stack([D.page_layout_from_signal(np.asarray(X[i], np.float32)) for i in f9])
with torch.no_grad():
    lgA = np.concatenate([netA(torch.from_numpy(Z[i:i + 512])).numpy() for i in range(0, len(Z), 512)])
PA = 1 / (1 + np.exp(-(lgA * aA + bA)))
yA = YA.values[f9]
XB = np.load(F.DD + "find2_x100_f16.npy", mmap_mode="r")
mB = pd.read_csv(F.OUT_B + "split.csv")
va = np.sort(np.flatnonzero(mB.split == "val"))
out = []
with torch.no_grad():
    for i in range(0, len(va), 512):
        xb = torch.from_numpy(np.asarray(XB[va[i:i + 512]], np.float32))
        out.append(netB(M.make_input(xb, mask)).numpy())
PB = 1 / (1 + np.exp(-(np.concatenate(out) * aB + bB)))
yB = mB[F.B_LABELS].values[va]
thr = {}
for m, c in PAT:
    p, y = (PA[:, F.A_CODES.index(c)], yA[:, F.A_CODES.index(c)]) if m == "A" else (PB[:, F.B_LABELS.index(c)], yB[:, F.B_LABELS.index(c)])
    neg = p[y == 0]
    thr[f"{m}:{c}"] = {k: float(np.quantile(neg, s)) for k, s in SPECS.items()}
    thr[f"{m}:{c}"]["old_youden"] = old[f"{m}:{c}"]
    thr[f"{m}:{c}"]["validation_negatives"] = int(len(neg))
    thr[f"{m}:{c}"]["validation_positives"] = int((y == 1).sum())
json.dump(dict(rule="docs/plan/analysis_plan_changes.md 2026-11-16 late night", primary="s97", thresholds=thr), open(OUT + "thresholds_v2.json", "w"), indent=1)
print("thresholds derived from validation data only", flush=True)

# ---------------------------------------------------------------- the sets seen before
sets = {}
sets["T2 drawn pages (300)"] = (pd.read_csv(F.OUT_A + "predictions_T2.csv"), pd.read_csv(F.OUT_B + "predictions_T2.csv"), "ecg_id")
sets["T3 screen photos (140)"] = (pd.read_csv(F.OUT_A + "predictions_T3.csv"), pd.read_csv(F.OUT_B + "predictions_T3.csv"), "ecg_id")
selN = pd.read_csv(ROOT + "/results/paper_n/selected_N.csv").set_index("page")
for tag, f in (("set N drawn pages (120)", "test_pages_predictions.csv"), ("set N simulated photos (120)", "test_sim_predictions.csv")):
    d = pd.read_csv(ROOT + "/results/paper_n/" + f)
    d["ecg_id"] = d.page.map(selN.ecg_id)
    a = d[["ecg_id"] + [c for c in d.columns if c.startswith("A_")]].rename(columns=lambda c: c[2:] if c.startswith("A_") else c)
    b = d[["ecg_id"] + [c for c in d.columns if c.startswith("B_")]].rename(columns=lambda c: c[2:] if c.startswith("B_") else c)
    sets[tag] = (a, b, "ecg_id")
LAB = {"A": YA, "B": YB}
rows, agg = [], []
VARIANTS = {"old Youden": lambda k: thr[k]["old_youden"], "spec 0.95": lambda k: thr[k]["s95"], "spec 0.97 (used)": lambda k: thr[k]["s97"], "spec 0.99": lambda k: thr[k]["s99"]}
for sname, (a, b, idc) in sets.items():
    ids = a[idc].astype(int).values
    pos_any = np.zeros(len(ids), bool)
    ys = {}
    for m, c in PAT:
        ys[f"{m}:{c}"] = LAB[m][c].loc[ids].values > 0
        pos_any |= ys[f"{m}:{c}"]
    for vname, fn in VARIANTS.items():
        flags = {}
        for m, c in PAT:
            p = (a if m == "A" else b)[c].astype(float).values
            fl = p >= fn(f"{m}:{c}")
            flags[f"{m}:{c}"] = fl
            y = ys[f"{m}:{c}"]
            rows.append(dict(set=sname, variant=vname, pattern=f"{m}:{c}", n=len(y), positives=int(y.sum()), sensitivity=float(fl[y].mean()) if y.any() else float("nan"), specificity=float((~fl[~y]).mean())))
        anyfl = np.any(list(flags.values()), axis=0)
        agg.append(dict(set=sname, variant=vname, items=len(ids), clean_items=int((~pos_any).sum()), clean_flagged=int(anyfl[~pos_any].sum()), clean_flagged_pct=100 * float(anyfl[~pos_any].mean()),
                        flags_per_clean_item=float(np.sum(list(flags.values()), axis=0)[~pos_any].mean()), pattern_items=int(pos_any.sum()), pattern_items_flagged=int(anyfl[pos_any].sum()), pattern_items_flagged_pct=100 * float(anyfl[pos_any].mean())))
R, G = pd.DataFrame(rows), pd.DataFrame(agg)
R.to_csv(OUT + "op_per_pattern.csv", index=False)
G.to_csv(OUT + "op_aggregate.csv", index=False)
md = ["# New operating point for the 8 research-only patterns (EXPLORATORY; rules logged before the thresholds were computed)", "",
      "Thresholds chosen on validation data only (specificity 0.97 there; 0.95 and 0.99 as a sensitivity analysis). The sets below were seen before for other analyses, so this is not a new confirmatory test.", "",
      "## Share of items flagged (at least one of the 8 patterns)", "", "| Set | Threshold | Clean items | Clean items flagged | Items with a pattern | Of those flagged | Flags per clean item |", "|---|---|---|---|---|---|---|"]
for _, r in G.iterrows():
    md.append(f"| {r.set} | {r.variant} | {r.clean_items} | {r.clean_flagged} ({r.clean_flagged_pct:.0f}%) | {r.pattern_items} | {r.pattern_items_flagged} ({r.pattern_items_flagged_pct:.0f}%) | {r.flags_per_clean_item:.2f} |")
md += ["", "## Sensitivity / specificity per pattern (old Youden threshold, new threshold used: specificity 0.97 on validation)", "", "| Set | Pattern | Positives | Old sens / spec | New sens / spec |", "|---|---|---|---|---|"]
for sname in sets:
    for m, c in PAT:
        o = R[(R.set == sname) & (R.pattern == f"{m}:{c}") & (R.variant == "old Youden")].iloc[0]
        nw = R[(R.set == sname) & (R.pattern == f"{m}:{c}") & (R.variant == "spec 0.97 (used)")].iloc[0]
        md.append(f"| {sname} | {m}:{c} | {o.positives} | {100 * o.sensitivity:.0f} / {100 * o.specificity:.0f} | {100 * nw.sensitivity:.0f} / {100 * nw.specificity:.0f} |")
open(OUT + "SECTION_OP.md", "w", encoding="utf-8").write("\n".join(md) + "\n")
print(G[["set", "variant", "clean_items", "clean_flagged", "clean_flagged_pct", "pattern_items", "pattern_items_flagged_pct"]].round(1).to_string(index=False))
