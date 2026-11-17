"""Select the 20 PRINTED-PAPER pages H01-H20 (seed 51). Rules fixed BEFORE any code ran: docs/plan/analysis_plan_changes.md, 2026-11-14 (night), Section H.
Same rules as select_fresh_sets_g.py (human-validated records; 5 male abnormal, 5 male normal, 5 female abnormal, 5 female normal; about 30% flagged), with a 12SL value for QRS, QT, PR and
frontal axis, and none of them in the 1,300 earlier recordings or G001-G100.
Writes results/paper_h/selected_h_20.csv and selection_summary.md.   python -I scripts/analysis/select_paper_20.py"""
import ast
import os

import numpy as np
import pandas as pd

ROOT = "D:/Capstone Project/"
OUT = ROOT + "results/paper_h/"
os.makedirs(OUT, exist_ok=True)
SEED = 51

db = pd.read_csv(ROOT + "data/ptbxl/ptbxl_database.csv")
scp = pd.read_csv(ROOT + "data/ptbxl/scp_statements.csv").rename(columns={"Unnamed: 0": "code"})
c2c = dict(zip(scp["code"], scp["diagnostic_class"]))
codes = db["scp_codes"].apply(ast.literal_eval)
db["diagnostic_class"] = [c2c.get(max(c, key=c.get)) if c else None for c in codes]
db["is_abnormal"] = db["diagnostic_class"].notna() & (db["diagnostic_class"] != "NORM")
db["record"] = db["filename_lr"].str.split("/").str[-1]
flags = ["baseline_drift", "static_noise", "burst_noise", "electrodes_problems", "extra_beats", "pacemaker"]
db["flagged"] = db[flags].apply(lambda r: any(str(x).strip() not in ("", "nan") for x in r), axis=1)
db["sex_lbl"] = db["sex"].map({0: "male", 1: "female"})

used = set(pd.read_csv(ROOT + "results/extension/reference_check_150.csv").ecg_id) | set(pd.read_csv(ROOT + "results/extension/selected_100.csv").ecg_id)
used |= set(pd.read_csv(ROOT + "results/ownphotos/pages_mapping.csv").ecg_id) | set(pd.read_csv(ROOT + "results/ownphotos2/pages_mapping.csv").ecg_id)
used |= set(pd.read_csv(ROOT + "results/fresh/selected_fresh_100.csv").ecg_id) | set(pd.read_csv(ROOT + "results/fresh/selected_dev_1000.csv").ecg_id)
assert len(used) == 1300, len(used)
used |= set(pd.read_csv(ROOT + "results/fresh_g/selected_g_100.csv").ecg_id)
assert len(used) == 1400, len(used)

x12 = pd.read_csv(ROOT + "data/ptbxl_plus/12sl_features.csv").set_index("ecg_id")
need = ["QRS_Dur_Global", "QT_Int_Global", "PR_Int_Global", "R_AxisFrontal_Global"]
ok_ids = set(x12.index[x12[need].notna().all(axis=1)])
cand = db[~db.ecg_id.isin(used) & db.ecg_id.isin(ok_ids) & (db["validated_by_human"] == True)]  # noqa: E712
QUOTA = {("male", True): 5, ("male", False): 5, ("female", True): 5, ("female", False): 5}
rng = np.random.RandomState(SEED)
picked = []
for (sex, ab), n in QUOTA.items():
    cell = cand[(cand.sex_lbl == sex) & (cand.is_abnormal == ab)]
    n_flag = min(int(round(n * 0.30)), int(cell.flagged.sum()))
    picked.append(cell[cell.flagged].sample(n=n_flag, random_state=rng.randint(1 << 30)))
    picked.append(cell[~cell.flagged].sample(n=n - n_flag, random_state=rng.randint(1 << 30)))
h = pd.concat(picked).sort_values("record").reset_index(drop=True)
h["page"] = [f"H{i + 1:02d}" for i in range(len(h))]
assert len(h) == 20 and not (set(h.ecg_id) & used)
cols = ["page", "ecg_id", "record", "filename_lr", "sex_lbl", "age", "diagnostic_class", "is_abnormal", "flagged", "validated_by_human", "strat_fold"]
h[[c for c in cols if c in h.columns]].to_csv(OUT + "selected_h_20.csv", index=False)
af = int(h.scp_codes.apply(lambda s: ("AFIB" in ast.literal_eval(s)) or ("AFLT" in ast.literal_eval(s))).sum())
L = ["# Printed-paper pages H01-H20 (seed 51, scripts/analysis/select_paper_20.py)", "",
     f"Already used and excluded: {len(used)} recordings. Candidates: {len(cand)}.", "",
     f"Selected: {len(h)} recordings; sex {h.sex_lbl.value_counts().to_dict()}; abnormal {int(h.is_abnormal.sum())}; flagged {int(h.flagged.sum())}; atrial fibrillation or flutter label {af}."]
open(OUT + "selection_summary.md", "w", encoding="utf-8").write("\n".join(L) + "\n")
print("\n".join(L))
