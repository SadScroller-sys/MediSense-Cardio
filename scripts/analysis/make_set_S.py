"""Creates the scripts of set S from the set R scripts (same generator and settings; only names, count and seeds change), and selects set S.
Set S (rules: docs/plan/analysis_plan_changes.md, 2026-11-18 'SET S'): 300 PTB-XL recordings drawn at random (seed 91) from fold 10, never used in any earlier set.
Usage: python -I scripts/analysis/make_set_S.py      (writes scripts/analysis/make_sim_photos_S.py, digitise_sim_photos_S.py, results/paper_s/selected_S.csv)"""
import glob
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "demo"))
from health import data as D  # noqa: E402

OUT = ROOT + "/results/paper_s/"
os.makedirs(OUT, exist_ok=True)
SA = ROOT + "/scripts/analysis/"
# ---- scripts of the picture steps, copied from set R
s = open(SA + "make_sim_photos_R.py", encoding="utf-8").read()
for a, b in (("paper_r", "paper_s"), ("range(1, 121)", "range(1, 301)"), ('f"R{n:03d}"', 'f"S{n:03d}"'), ("default_rng(82)", "default_rng(92)"), ("Set N", "Set S")):
    assert a in s, a
    s = s.replace(a, b)
open(SA + "make_sim_photos_S.py", "w", encoding="utf-8").write(s)
t = open(SA + "digitise_sim_photos_R.py", encoding="utf-8").read()
for a, b in (("paper_r", "paper_s"), ("(expected 120)", "(expected 300)"), ("Set N", "Set S")):
    assert a in t, a
    t = t.replace(a, b)
open(SA + "digitise_sim_photos_S.py", "w", encoding="utf-8").write(t)
# ---- selection
db = pd.read_csv(ROOT + "/data/ptbxl/ptbxl_database.csv")
db["record"] = db["filename_lr"].str.split("/").str[-1]
used = set(int(x) for x in D.excluded_ids())
for f in glob.glob(ROOT + "/results/**/selected*.csv", recursive=True):
    try:
        c = pd.read_csv(f)
        if "ecg_id" in c.columns:
            used |= set(c.ecg_id.astype(int))
    except Exception:
        pass
pool = db[(db.strat_fold == 10) & ~db.ecg_id.isin(used)]
print("fold-10 recordings never used:", len(pool), "of", int((db.strat_fold == 10).sum()))
S = pool.sample(n=300, random_state=np.random.RandomState(91)).sort_values("record").reset_index(drop=True)
S["page"] = [f"S{i + 1:03d}" for i in range(len(S))]
S[["page", "ecg_id", "record", "filename_lr", "sex", "age", "strat_fold", "scp_codes"]].to_csv(OUT + "selected_S.csv", index=False)
Y = D.load_db()
Y = Y[1] if isinstance(Y, tuple) else Y
mi = S.ecg_id.map(lambda e: float(Y.loc[int(e), "MI"]))
print("set S:", len(S), "recordings | MI positives:", int(mi.sum()), f"({mi.mean() * 100:.1f}%)")
