"""Select the FRESH positive-rich dataset set P (rules: docs/plan/analysis_plan_changes.md, 2026-11-16 late night 'FRESH POSITIVE-RICH DATASET SET P'). Seed 66. Writes results/paper_p/selected_P.csv (page P001 and up).
Run: python -I scripts/analysis/select_P_fresh.py"""
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "demo"))
from health import data as D  # noqa: E402
from health import find2 as F  # noqa: E402

OUT = ROOT + "/results/paper_p/"
os.makedirs(OUT, exist_ok=True)
SEED = 66
db = pd.read_csv(ROOT + "/data/ptbxl/ptbxl_database.csv")
db["record"] = db["filename_lr"].str.split("/").str[-1]
used = set(D.excluded_ids())
for f in ("results/fresh/selected_dev_1000.csv", "results/fresh/selected_fresh_100.csv", "results/fresh_g/selected_g_100.csv", "results/intervals_ml/selected_K_100.csv", "results/intervals_ml/selected_L_100.csv",
          "results/intervals_ml/selected_M_100.csv", "results/paper_h/selected_h_20.csv", "results/extension/selected_100.csv", "results/paper_n/selected_N.csv"):
    p = ROOT + "/" + f
    if os.path.exists(p):
        used |= set(pd.read_csv(p).ecg_id.astype(int))
codes = db.scp_codes.apply(F._codes)
db["AF"] = [F.has(c, "AFIB") or F.has(c, "AFLT") for c in codes]
db["RBBB"] = [F.has(c, "CRBBB") or F.has(c, "IRBBB") for c in codes]
db["LBBB"] = [F.has(c, "CLBBB") for c in codes]
db["AVB1"] = [F.has(c, "1AVB") for c in codes]
db["LVH"] = [F.has(c, "LVH") for c in codes]
db["LAFB"] = [F.has(c, "LAFB") for c in codes]
db["ASMI"] = [F.has(c, "ASMI") for c in codes]
FIND = ["AF", "RBBB", "LBBB", "AVB1", "LVH", "LAFB"]
db["NORMAL"] = pd.Series([F.has(c, "NORM") for c in codes], index=db.index) & ~db[FIND + ["ASMI"]].any(axis=1)
cand = db[(db.strat_fold == 10) & ~db.ecg_id.isin(used)].copy()
print("fold-10 recordings not used anywhere:", len(cand), {f: int(cand[f].sum()) for f in FIND + ["NORMAL"]})
rng = np.random.RandomState(SEED)
picked, group = [], {}
for f in FIND + ["NORMAL"]:
    pool = cand[cand[f] & ~cand.ecg_id.isin(picked)]
    n = min(40, len(pool))
    s = pool.sample(n=n, random_state=rng.randint(1 << 30))
    picked += s.ecg_id.tolist()
    for e in s.ecg_id:
        group[e] = f
P = cand[cand.ecg_id.isin(picked)].sort_values("record").reset_index(drop=True)
P["page"] = [f"P{i + 1:03d}" for i in range(len(P))]
P["group"] = P.ecg_id.map(group)
P[["page", "ecg_id", "record", "filename_lr", "sex", "age", "strat_fold", "group"] + FIND + ["ASMI", "NORMAL"]].to_csv(OUT + "selected_P.csv", index=False)
print("P:", len(P), "pages | chosen per group:", {f: int((P.group == f).sum()) for f in FIND + ["NORMAL"]}, "| positives per finding in P (incl. overlap):", {f: int(P[f].sum()) for f in FIND})
