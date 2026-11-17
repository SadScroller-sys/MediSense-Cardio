"""Select set N: 120 PTB-XL fold-10 recordings rich in six findings (AF, RBBB-type, LBBB, 1AVB, LVH, LAFB; 20 positives each, seed 63). Rules: docs/plan/analysis_plan_changes.md, 2026-11-16 evening 'POSITIVE-RICH SET N'.
Writes results/paper_n/selected_N.csv (page N001-N120, the six finding flags, and the real-photo subset 'real' = the first 10 chosen pages of each finding). Run: python -I scripts/analysis/select_N_enriched.py"""
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "demo"))
from health import data as D  # noqa: E402
from health import find2 as F  # noqa: E402

OUT = ROOT + "/results/paper_n/"
os.makedirs(OUT, exist_ok=True)
SEED = 63
db = pd.read_csv(ROOT + "/data/ptbxl/ptbxl_database.csv")
db["record"] = db["filename_lr"].str.split("/").str[-1]
used = set(D.excluded_ids())
for f in ("results/fresh/selected_dev_1000.csv", "results/fresh/selected_fresh_100.csv", "results/fresh_g/selected_g_100.csv", "results/intervals_ml/selected_K_100.csv", "results/intervals_ml/selected_L_100.csv",
          "results/intervals_ml/selected_M_100.csv", "results/paper_h/selected_h_20.csv", "results/extension/selected_100.csv"):
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
FIND = ["AF", "RBBB", "LBBB", "AVB1", "LVH", "LAFB"]
cand = db[(db.strat_fold == 10) & ~db.ecg_id.isin(used)].copy()
print("fold-10 candidates not used anywhere:", len(cand), {f: int(cand[f].sum()) for f in FIND})
rng = np.random.RandomState(SEED)
picked, real = [], set()
for f in FIND:
    pool = cand[cand[f] & ~cand.ecg_id.isin(picked)]
    s = pool.sample(n=20, random_state=rng.randint(1 << 30))
    ids = s.ecg_id.tolist()
    picked += ids
    real |= set(ids[:10])
N = cand[cand.ecg_id.isin(picked)].sort_values("record").reset_index(drop=True)
assert len(N) == 120 and not (set(N.ecg_id) & used)
N["page"] = [f"N{i + 1:03d}" for i in range(len(N))]
N["real"] = N.ecg_id.isin(real)
N[["page", "ecg_id", "record", "filename_lr", "sex", "age", "strat_fold", "real"] + FIND].to_csv(OUT + "selected_N.csv", index=False)
print("N:", len(N), "pages; real-photo subset:", int(N.real.sum()), "pages; positives per finding in N:", {f: int(N[f].sum()) for f in FIND}, "| in the real subset:", {f: int(N[N.real][f].sum()) for f in FIND})
