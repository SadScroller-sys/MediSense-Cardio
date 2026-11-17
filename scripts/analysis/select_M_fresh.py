"""Select the fresh test set M (100 NEW recordings, seed 60; hypertrophy and atrial fibrillation rich) for Section AA. Rules: docs/plan/analysis_plan_changes.md, 2026-11-15 "Section AA second attempt". Writes results/intervals_ml/selected_M_100.csv.
Run: python -I scripts/analysis/select_K_sealed.py"""
import ast
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "demo"))
from health import data as D  # noqa: E402

OUT = ROOT + "/results/intervals_ml/"
os.makedirs(OUT, exist_ok=True)
SEED = 60
db = pd.read_csv(ROOT + "/data/ptbxl/ptbxl_database.csv")
db["record"] = db["filename_lr"].str.split("/").str[-1]
flags = ["baseline_drift", "static_noise", "burst_noise", "electrodes_problems", "extra_beats", "pacemaker"]
db["flagged"] = db[flags].apply(lambda r: any(str(x).strip() not in ("", "nan") for x in r), axis=1)
db["sex_lbl"] = db["sex"].map({0: "male", 1: "female"})
x12 = pd.read_csv(ROOT + "/data/ptbxl_plus/12sl_features.csv").set_index("ecg_id")
used = set(D.excluded_ids()) | set(pd.read_csv(ROOT + "/results/fresh/selected_dev_1000.csv").ecg_id) | set(pd.read_csv(ROOT + "/results/fresh/selected_fresh_100.csv").ecg_id) | set(pd.read_csv(ROOT + "/results/fresh_g/selected_g_100.csv").ecg_id) | set(pd.read_csv(ROOT + "/results/intervals_ml/selected_K_100.csv").ecg_id) | set(pd.read_csv(ROOT + "/results/intervals_ml/selected_L_100.csv").ecg_id)
ok = x12.index[x12.QRS_Dur_Global.notna() & x12.QT_Int_Global.notna() & x12.QT_IntFridericia_Global.notna()]
cand = db[~db.ecg_id.isin(used) & db.ecg_id.isin(ok) & (db.validated_by_human == True)].copy()  # noqa: E712
cand["qrs"] = cand.ecg_id.map(x12.QRS_Dur_Global)
cand["qt"] = cand.ecg_id.map(x12.QT_Int_Global)
cand["af"] = cand.scp_codes.apply(lambda s: ("AFIB" in ast.literal_eval(s)) or ("AFLT" in ast.literal_eval(s)))
rng = np.random.RandomState(SEED)
picked = []


def take(df, n):
    df = df[~df.ecg_id.isin(picked)]
    s = df.sample(n=min(n, len(df)), random_state=rng.randint(1 << 30))
    picked.extend(s.ecg_id.tolist())


import sys as _s
_sc = pd.read_csv(ROOT + "/data/ptbxl/scp_statements.csv", index_col=0)
_dc = _sc[_sc.diagnostic == 1].diagnostic_class
cand["hyp"] = cand.scp_codes.apply(lambda t: any(_dc.get(k) == "HYP" for k in ast.literal_eval(t)))
take(cand[cand.hyp & cand.af], 8)
take(cand[cand.hyp], max(0, 35 - int(cand[cand.ecg_id.isin(picked)].hyp.sum())))
take(cand[cand.af], max(0, 25 - int(cand[cand.ecg_id.isin(picked)].af.sum())))
take(cand, 100 - len(picked))
M = cand[cand.ecg_id.isin(picked)].sort_values("record").reset_index(drop=True)
assert len(M) == 100 and not (set(M.ecg_id) & used)
M["page"] = [f"M{i + 1:03d}" for i in range(len(M))]
M[["page", "ecg_id", "record", "filename_lr", "sex_lbl", "age", "flagged", "strat_fold", "qrs", "qt", "af", "hyp"]].to_csv(OUT + "selected_M_100.csv", index=False)
print(len(cand), "candidates; M: HYP", int(M.hyp.sum()), "AF", int(M.af.sum()), "flagged", int(M.flagged.sum()))
