"""Select the FRESH TEST SET (100 recordings) and the DEVELOPMENT SET (1,000 recordings) for the second QRS/QT attempt.
Rules fixed BEFORE any code ran: docs/plan/analysis_plan_changes.md, 2026-11-14 (night). Seed 46.
  * Fresh test set: same rules as scripts/analysis/select_extension_100.py (human-validated records, 25 male abnormal / 26 male normal / 25 female abnormal / 24 female normal, about 30% flagged),
    none of them in the first 50, the new 100, P01-P30 or Q01-Q20.
  * Development set: 1,000 further recordings (random, natural mix), not in any set above, not in the fresh test set, with a 12SL value for QRS and QT.
Writes results/fresh/selected_fresh_100.csv, selected_dev_1000.csv and selection_summary.md.  Run:  python -I scripts/analysis/select_fresh_sets.py"""
import ast
import os

import numpy as np
import pandas as pd

ROOT = "D:/Capstone Project/"
OUT = ROOT + "results/fresh/"
os.makedirs(OUT, exist_ok=True)
SEED = 46

db = pd.read_csv(ROOT + "data/ptbxl/ptbxl_database.csv")
scp = pd.read_csv(ROOT + "data/ptbxl/scp_statements.csv").rename(columns={"Unnamed: 0": "code"})
c2c = dict(zip(scp["code"], scp["diagnostic_class"]))
db["diagnostic_class"] = db["scp_codes"].apply(lambda s: (c2c.get(max(ast.literal_eval(s), key=ast.literal_eval(s).get)) if ast.literal_eval(s) else None))
db["is_abnormal"] = db["diagnostic_class"].notna() & (db["diagnostic_class"] != "NORM")
db["record"] = db["filename_lr"].str.split("/").str[-1]
flags = ["baseline_drift", "static_noise", "burst_noise", "electrodes_problems", "extra_beats", "pacemaker"]
db["flagged"] = db[flags].apply(lambda r: any(str(x).strip() not in ("", "nan") for x in r), axis=1)
db["sex_lbl"] = db["sex"].map({0: "male", 1: "female"})

ref = pd.read_csv(ROOT + "results/extension/reference_check_150.csv")
used = set(ref.ecg_id) | set(pd.read_csv(ROOT + "results/extension/selected_100.csv").ecg_id)
used |= set(pd.read_csv(ROOT + "results/ownphotos/pages_mapping.csv").ecg_id) | set(pd.read_csv(ROOT + "results/ownphotos2/pages_mapping.csv").ecg_id)
assert len(used) == 200, len(used)

x12 = pd.read_csv(ROOT + "data/ptbxl_plus/12sl_features.csv").set_index("ecg_id")
has_ref = x12["QRS_Dur_Global"].notna() & x12["QT_Int_Global"].notna()
ok_ids = set(x12.index[has_ref])

cand = db[~db.ecg_id.isin(used) & db.ecg_id.isin(ok_ids) & (db["validated_by_human"] == True)]  # noqa: E712
QUOTA = {("male", True): 25, ("male", False): 26, ("female", True): 25, ("female", False): 24}
rng = np.random.RandomState(SEED)
picked = []
for (sex, ab), n in QUOTA.items():
    cell = cand[(cand.sex_lbl == sex) & (cand.is_abnormal == ab)]
    n_flag = min(int(round(n * 0.30)), int(cell.flagged.sum()))
    picked.append(cell[cell.flagged].sample(n=n_flag, random_state=rng.randint(1 << 30)))
    picked.append(cell[~cell.flagged].sample(n=n - n_flag, random_state=rng.randint(1 << 30)))
fresh = pd.concat(picked).sort_values("record").reset_index(drop=True)
fresh["page"] = [f"F{i + 1:03d}" for i in range(len(fresh))]
assert len(fresh) == 100 and not (set(fresh.ecg_id) & used)

rest = db[~db.ecg_id.isin(used | set(fresh.ecg_id)) & db.ecg_id.isin(ok_ids)]
dev = rest.sample(n=1000, random_state=SEED).sort_values("record").reset_index(drop=True)
assert len(dev) == 1000 and not (set(dev.ecg_id) & (used | set(fresh.ecg_id)))

cols = ["page", "ecg_id", "record", "filename_lr", "sex_lbl", "age", "diagnostic_class", "is_abnormal", "flagged", "validated_by_human", "strat_fold"]
fresh[[c for c in cols if c in fresh.columns]].to_csv(OUT + "selected_fresh_100.csv", index=False)
dev[[c for c in cols if c in dev.columns and c != "page"]].to_csv(OUT + "selected_dev_1000.csv", index=False)

af = lambda ids: int(db[db.ecg_id.isin(ids)].scp_codes.apply(lambda s: ("AFIB" in ast.literal_eval(s)) or ("AFLT" in ast.literal_eval(s))).sum())
L = ["# Fresh test set and development set (seed 46, written by scripts/analysis/select_fresh_sets.py)", "",
         f"Already used (first 50, new 100, P01-P30, Q01-Q20): {len(used)} recordings. Candidates for the fresh test set (unused, human-validated, 12SL QRS and QT present): {len(cand)}.", "",
         f"Fresh test set: {len(fresh)} recordings; sex {fresh.sex_lbl.value_counts().to_dict()}; abnormal {int(fresh.is_abnormal.sum())}; flagged {int(fresh.flagged.sum())}; atrial fibrillation or flutter label {af(fresh.ecg_id)}; age min/median/max {fresh.age.min()}/{fresh.age.median()}/{fresh.age.max()}.",
         f"Development set: {len(dev)} recordings; sex {dev.sex_lbl.value_counts().to_dict()}; abnormal {int(dev.is_abnormal.sum())}; flagged {int(dev.flagged.sum())}; atrial fibrillation or flutter label {af(dev.ecg_id)}; age min/median/max {dev.age.min()}/{dev.age.median()}/{dev.age.max()}.",
         "", "The fresh test set is sealed: its pages are drawn and digitised but no result on them is looked at before the single test."]
open(OUT + "selection_summary.md", "w", encoding="utf-8").write("\n".join(L) + "\n")
print("\n".join(L))
