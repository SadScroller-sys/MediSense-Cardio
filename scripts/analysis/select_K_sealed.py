"""Select the sealed test set K (100 NEW recordings, seed 56) for Section AA. Rules: docs/plan/analysis_plan_changes.md, 2026-11-15 "Section AA". Writes results/intervals_ml/selected_K_100.csv.
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
SEED = 56
db = pd.read_csv(ROOT + "/data/ptbxl/ptbxl_database.csv")
db["record"] = db["filename_lr"].str.split("/").str[-1]
flags = ["baseline_drift", "static_noise", "burst_noise", "electrodes_problems", "extra_beats", "pacemaker"]
db["flagged"] = db[flags].apply(lambda r: any(str(x).strip() not in ("", "nan") for x in r), axis=1)
db["sex_lbl"] = db["sex"].map({0: "male", 1: "female"})
x12 = pd.read_csv(ROOT + "/data/ptbxl_plus/12sl_features.csv").set_index("ecg_id")
used = set(D.excluded_ids()) | set(pd.read_csv(ROOT + "/results/fresh/selected_dev_1000.csv").ecg_id) | set(pd.read_csv(ROOT + "/results/fresh/selected_fresh_100.csv").ecg_id) | set(pd.read_csv(ROOT + "/results/fresh_g/selected_g_100.csv").ecg_id)
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


take(cand[cand.qrs >= 120], 20)
take(cand[cand.qt >= 450], 15)
take(cand[cand.qt <= 350], 10)
take(cand[cand.af], max(0, 8 - int(cand[cand.ecg_id.isin(picked)].af.sum())))
take(cand, 100 - len(picked))
K = cand[cand.ecg_id.isin(picked)].sort_values("record").reset_index(drop=True)
assert len(K) == 100 and not (set(K.ecg_id) & used)
K["page"] = [f"K{i + 1:03d}" for i in range(len(K))]
K[["page", "ecg_id", "record", "filename_lr", "sex_lbl", "age", "flagged", "strat_fold", "qrs", "qt", "af"]].to_csv(OUT + "selected_K_100.csv", index=False)
print(len(cand), "candidates; K: QRS>=120", int((K.qrs >= 120).sum()), "QT>=450", int((K.qt >= 450).sum()), "QT<=350", int((K.qt <= 350).sum()), "AF", int(K.af.sum()), "flagged", int(K.flagged.sum()))
