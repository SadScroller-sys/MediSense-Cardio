"""Select set R (rules: docs/plan/analysis_plan_changes.md 2026-11-17 'ONE MORE ROUND, REPLICATION ON A NEW FRESH SET R'). Seed 71. Writes results/paper_r/selected_R.csv (page R001 and up).
40 AF, 40 LAFB, 40 NORMAL from fold 10 (fresh for A and B) and 40 LBBB (CLBBB) from folds 1-9 (fresh for B only; flagged in column fold10).
Run: python -I scripts/analysis/select_Q_fresh.py"""
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "demo"))
from health import data as D  # noqa: E402
from health import find2 as F  # noqa: E402

OUT = ROOT + "/results/paper_r/"
os.makedirs(OUT, exist_ok=True)
db = pd.read_csv(ROOT + "/data/ptbxl/ptbxl_database.csv")
db["record"] = db["filename_lr"].str.split("/").str[-1]
used = set(D.excluded_ids())
for f in ("results/fresh/selected_dev_1000.csv", "results/fresh/selected_fresh_100.csv", "results/fresh_g/selected_g_100.csv", "results/intervals_ml/selected_K_100.csv", "results/intervals_ml/selected_L_100.csv",
          "results/intervals_ml/selected_M_100.csv", "results/paper_h/selected_h_20.csv", "results/extension/selected_100.csv", "results/paper_n/selected_N.csv", "results/paper_p/selected_P.csv", "results/paper_q/selected_Q.csv"):
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
fresh = db[~db.ecg_id.isin(used)]
f10 = fresh[fresh.strat_fold == 10]
rng = np.random.RandomState(81)
picked, group = [], {}
for g, pool in (("LBBB", fresh[(fresh.strat_fold < 10) & fresh.LBBB]), ("AF", fresh[fresh.AF]), ("NORMAL", f10[f10.NORMAL])):
    pool = pool[~pool.ecg_id.isin(picked)]
    s = pool.sample(n=min(40, len(pool)), random_state=rng.randint(1 << 30))
    picked += s.ecg_id.tolist()
    for e in s.ecg_id:
        group[e] = g
Q = db[db.ecg_id.isin(picked)].sort_values("record").reset_index(drop=True)
Q["page"] = [f"R{i + 1:03d}" for i in range(len(Q))]
Q["group"] = Q.ecg_id.map(group)
Q["fold10"] = Q.strat_fold == 10
Q[["page", "ecg_id", "record", "filename_lr", "sex", "age", "strat_fold", "group", "fold10"] + FIND + ["ASMI", "NORMAL"]].to_csv(OUT + "selected_R.csv", index=False)
print("Q:", len(Q), "| per group:", {g: int((Q.group == g).sum()) for g in ["LBBB", "AF", "NORMAL"]}, "| fold-10 pictures:", int(Q.fold10.sum()))
