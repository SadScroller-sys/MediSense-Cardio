"""How many unused pool records are available for the extension, by sex / long-QT label / PTB-XL quality flag?

Rebuilds the original 500-record pool and 50-record sample exactly as analyze_v2_intervals.py does (seed 42) and checks that
the rebuilt sample equals the records in results_v2.csv. Candidates = pool minus those 50.
"""
import ast
import pandas as pd

DATA = "D:/Capstone Project/data/ptbxl"
db = pd.read_csv(f"{DATA}/ptbxl_database.csv")
scp = pd.read_csv(f"{DATA}/scp_statements.csv").rename(columns={"Unnamed: 0": "code"})
c2c = dict(zip(scp["code"], scp["diagnostic_class"]))


def dominant_class(s):
    codes = ast.literal_eval(s)
    if not codes:
        return None
    return c2c.get(max(codes, key=codes.get))


db["diagnostic_class"] = db["scp_codes"].apply(dominant_class)
db["is_abnormal"] = db["diagnostic_class"].notna() & (db["diagnostic_class"] != "NORM")
seed, POOL_N, SCOPE_N = 42, 500, 50
pool = pd.concat([db[~db["is_abnormal"]].sample(n=POOL_N // 2, random_state=seed),
                  db[db["is_abnormal"]].sample(n=POOL_N - POOL_N // 2, random_state=seed)]).reset_index(drop=True)
sample = pd.concat([pool[~pool["is_abnormal"]].sample(n=SCOPE_N // 2, random_state=seed),
                    pool[pool["is_abnormal"]].sample(n=SCOPE_N - SCOPE_N // 2, random_state=seed)]).reset_index(drop=True)
sample["record"] = sample["filename_lr"].str.split("/").str[-1]

res = pd.read_csv("D:/Capstone Project/results/v2_intervals/results_v2.csv")
same = set(sample["record"]) == set(res["record"])
print("rebuilt 50-record sample matches results_v2.csv:", same)

flags = ["baseline_drift", "static_noise", "burst_noise", "electrodes_problems", "extra_beats", "pacemaker"]
cand = pool[~pool["ecg_id"].isin(sample["ecg_id"])].copy()
cand["rec"] = cand["filename_lr"].str.split("/").str[-1]
cand["flagged"] = cand[flags].apply(lambda r: any(str(x).strip() not in ("", "nan") for x in r), axis=1)
cand["long_qt_label"] = cand["scp_codes"].apply(lambda s: "LNGQT" in ast.literal_eval(s))
cand["sex_lbl"] = cand["sex"].map({0: "male", 1: "female"})
print("candidates:", len(cand), "| sex:", cand["sex_lbl"].value_counts().to_dict())
print("human validated:", int(cand["validated_by_human"].sum()), "of", len(cand))
print("flagged:", int(cand["flagged"].sum()), "| long-QT label:", int(cand["long_qt_label"].sum()))
print("\nby sex (count, long-QT label, flagged, flagged+validated, long-QT+validated):")
g = cand.groupby("sex_lbl").agg(n=("rec", "size"), longqt=("long_qt_label", "sum"), flagged=("flagged", "sum"),
                               validated=("validated_by_human", "sum"))
print(g)
print("\nabnormal vs normal among candidates:", cand["is_abnormal"].value_counts().to_dict())
print("\nsex coding check vs the 50: ", sample.merge(res[res.axis == 'clean'][['record', 'sex']], on='record')
      .groupby(['sex_x', 'sex_y']).size().to_dict())
print("age of candidates (min, median, max):", cand["age"].min(), cand["age"].median(), cand["age"].max())
