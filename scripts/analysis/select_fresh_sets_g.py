"""Select the NEW SEALED TEST SET G001-G100 (100 recordings, seed 47) for the third QRS/QT attempt.
Rules fixed BEFORE any code ran: docs/plan/analysis_plan_changes.md, 2026-11-14 (night, third). Same rules as select_extension_100.py / select_fresh_sets.py
(human-validated records, 25 male abnormal / 26 male normal / 25 female abnormal / 24 female normal, about 30% flagged), with a 12SL value for QRS and QT,
and none of them in: the first 50, the earlier new 100, P01-P30, Q01-Q20, F001-F100 (attempt-2 test set) or the 1,000 attempt-2 development recordings.
Writes results/fresh_g/selected_g_100.csv and selection_summary.md.  Run:  python -I scripts/analysis/select_fresh_sets_g.py"""
import ast
import os

import numpy as np
import pandas as pd

ROOT = "D:/Capstone Project/"
OUT = ROOT + "results/fresh_g/"
os.makedirs(OUT, exist_ok=True)
SEED = 47

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

x12 = pd.read_csv(ROOT + "data/ptbxl_plus/12sl_features.csv").set_index("ecg_id")
ok_ids = set(x12.index[x12["QRS_Dur_Global"].notna() & x12["QT_Int_Global"].notna()])
cand = db[~db.ecg_id.isin(used) & db.ecg_id.isin(ok_ids) & (db["validated_by_human"] == True)]  # noqa: E712
QUOTA = {("male", True): 25, ("male", False): 26, ("female", True): 25, ("female", False): 24}
rng = np.random.RandomState(SEED)
picked = []
for (sex, ab), n in QUOTA.items():
    cell = cand[(cand.sex_lbl == sex) & (cand.is_abnormal == ab)]
    n_flag = min(int(round(n * 0.30)), int(cell.flagged.sum()))
    picked.append(cell[cell.flagged].sample(n=n_flag, random_state=rng.randint(1 << 30)))
    picked.append(cell[~cell.flagged].sample(n=n - n_flag, random_state=rng.randint(1 << 30)))
g = pd.concat(picked).sort_values("record").reset_index(drop=True)
g["page"] = [f"G{i + 1:03d}" for i in range(len(g))]
assert len(g) == 100 and not (set(g.ecg_id) & used)
cols = ["page", "ecg_id", "record", "filename_lr", "sex_lbl", "age", "diagnostic_class", "is_abnormal", "flagged", "validated_by_human", "strat_fold"]
g[[c for c in cols if c in g.columns]].to_csv(OUT + "selected_g_100.csv", index=False)
af = int(g.scp_codes.apply(lambda s: ("AFIB" in ast.literal_eval(s)) or ("AFLT" in ast.literal_eval(s))).sum())
L = ["# New sealed test set G001-G100 (seed 47, scripts/analysis/select_fresh_sets_g.py)", "",
     f"Already used and excluded: {len(used)} recordings. Candidates: {len(cand)}.", "",
     f"Selected: {len(g)} recordings; sex {g.sex_lbl.value_counts().to_dict()}; abnormal {int(g.is_abnormal.sum())}; flagged {int(g.flagged.sum())}; atrial fibrillation or flutter label {af}; age min/median/max {g.age.min()}/{g.age.median()}/{g.age.max()}.",
     "", "Sealed: pages G001-G100 are drawn and digitised, the user photographs G001-G020, and no result on them is looked at before the single test."]
open(OUT + "selection_summary.md", "w", encoding="utf-8").write("\n".join(L) + "\n")
print("\n".join(L))
