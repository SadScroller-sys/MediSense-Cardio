"""Select 100 new recordings from the unused part of the original 500-record pool, to extend the study from 50 to 150.

Rules (decided before looking at any outcome; seed 42):
  * candidates = the 450 pool records not in the first 50 (their clean pages were already rendered on Drive)
  * only records whose labels were validated by a human cardiologist (validated_by_human == True)
  * combined 150 = 75 female + 75 male: the first 50 are 26 female / 24 male, so add 49 female and 51 male
  * 50 normal + 50 abnormal among the new ones (same diagnostic split as the first sample)
  * within each sex x normal/abnormal cell, about 30% flagged records (the natural share of the pool, 137 of 450)
Writes results/extension/selected_100.csv and results/extension/selection_summary.md.
"""
import ast
import os
import numpy as np
import pandas as pd

DATA = "D:/Capstone Project/data/ptbxl"
OUT = "D:/Capstone Project/results/extension"
os.makedirs(OUT, exist_ok=True)

db = pd.read_csv(f"{DATA}/ptbxl_database.csv")
scp = pd.read_csv(f"{DATA}/scp_statements.csv").rename(columns={"Unnamed: 0": "code"})
c2c = dict(zip(scp["code"], scp["diagnostic_class"]))


def dominant_class(s):
    codes = ast.literal_eval(s)
    return c2c.get(max(codes, key=codes.get)) if codes else None


db["diagnostic_class"] = db["scp_codes"].apply(dominant_class)
db["is_abnormal"] = db["diagnostic_class"].notna() & (db["diagnostic_class"] != "NORM")
seed, POOL_N, SCOPE_N = 42, 500, 50
pool = pd.concat([db[~db["is_abnormal"]].sample(n=POOL_N // 2, random_state=seed),
                  db[db["is_abnormal"]].sample(n=POOL_N - POOL_N // 2, random_state=seed)]).reset_index(drop=True)
sample = pd.concat([pool[~pool["is_abnormal"]].sample(n=SCOPE_N // 2, random_state=seed),
                    pool[pool["is_abnormal"]].sample(n=SCOPE_N - SCOPE_N // 2, random_state=seed)]).reset_index(drop=True)
res = pd.read_csv("D:/Capstone Project/results/v2_intervals/results_v2.csv")
assert set(sample["filename_lr"].str.split("/").str[-1]) == set(res["record"]), "rebuilt sample differs from the real first 50"

flags = ["baseline_drift", "static_noise", "burst_noise", "electrodes_problems", "extra_beats", "pacemaker"]
cand = pool[~pool["ecg_id"].isin(sample["ecg_id"])].copy()
cand["record"] = cand["filename_lr"].str.split("/").str[-1]
cand["flagged"] = cand[flags].apply(lambda r: any(str(x).strip() not in ("", "nan") for x in r), axis=1)
cand["sex_lbl"] = cand["sex"].map({0: "male", 1: "female"})
cand = cand[cand["validated_by_human"] == True]  # noqa: E712

QUOTA = {("male", True): 25, ("male", False): 26, ("female", True): 25, ("female", False): 24}  # (sex, abnormal)
FLAG_SHARE = 0.30
rng = np.random.RandomState(seed)
picked = []
for (sex, ab), n in QUOTA.items():
    cell = cand[(cand["sex_lbl"] == sex) & (cand["is_abnormal"] == ab)]
    n_flag = int(round(n * FLAG_SHARE))
    fl = cell[cell["flagged"]]
    nf = cell[~cell["flagged"]]
    n_flag = min(n_flag, len(fl))
    n_non = n - n_flag
    assert len(nf) >= n_non, f"not enough unflagged in cell {sex}/{ab}: {len(nf)} < {n_non}"
    picked.append(fl.sample(n=n_flag, random_state=rng.randint(1 << 30)))
    picked.append(nf.sample(n=n_non, random_state=rng.randint(1 << 30)))
sel = pd.concat(picked).sort_values("record").reset_index(drop=True)
cols = ["ecg_id", "record", "filename_lr", "sex_lbl", "age", "diagnostic_class", "is_abnormal", "flagged", "validated_by_human", "strat_fold"]
sel[cols].to_csv(f"{OUT}/selected_100.csv", index=False)

first50 = sample.assign(sex_lbl=sample["sex"].map({0: "male", 1: "female"}))
lines = ["# Extension selection (100 new recordings), 2026-11-04\n",
         f"Candidates after rules: {len(cand)}; selected: {len(sel)}. Script: scripts/analysis/select_extension_100.py (seed 42).\n",
         "Combined sex (first 50 + new 100): " + str((pd.concat([first50["sex_lbl"], sel["sex_lbl"]]).value_counts()).to_dict()),
         "New 100 by sex: " + str(sel["sex_lbl"].value_counts().to_dict()),
         "New 100 normal / abnormal: " + str(sel["is_abnormal"].map({True: "abnormal", False: "normal"}).value_counts().to_dict()),
         f"New 100 flagged records: {int(sel['flagged'].sum())}",
         "New 100 diagnostic classes: " + str(sel["diagnostic_class"].value_counts().to_dict()),
         "New 100 age (min / median / max): %s / %s / %s" % (sel["age"].min(), sel["age"].median(), sel["age"].max()),
         "First 50 age (min / median / max): %s / %s / %s" % (first50["age"].min(), first50["age"].median(), first50["age"].max())]
text = "\n".join(lines)
print(text)
open(f"{OUT}/selection_summary.md", "w", encoding="utf-8").write(text + "\n")
