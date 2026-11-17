"""Do the recordings that cause most bad heart-rate readings carry PTB-XL's own signal-quality flags?

Reads data/ptbxl/ptbxl_database.csv (PTB-XL metadata) and results/v2_intervals/results_v2.csv.
Bad reading = HR unreadable or wrong by more than 5 bpm (same primary target as the held-out detector test).
Reliable records only (at most 6 of 31 versions unreadable). Prints a table; saves nothing.
"""
import numpy as np
import pandas as pd

db = pd.read_csv("D:/Capstone Project/data/ptbxl/ptbxl_database.csv")
db["record"] = db["filename_lr"].str.split("/").str[-1]
res = pd.read_csv("D:/Capstone Project/results/v2_intervals/results_v2.csv")
res["rec"] = res["record"].str.replace(r"-0$", "", regex=True)

unread = res.groupby("record")["dig_hr"].apply(lambda s: s.isna().sum())
rel = set(unread[unread <= 6].index)
r = res[res["record"].isin(rel)].copy()
r["bad"] = r["dig_hr"].isna() | (r["diff_bpm"].abs() > 5)

per = r.groupby("record").agg(bad=("bad", "sum"), n=("bad", "size")).reset_index()
per["rec"] = per["record"].str.replace(r"-0$", "", regex=True)
flags = ["baseline_drift", "static_noise", "burst_noise", "electrodes_problems", "extra_beats", "pacemaker"]
m = per.merge(db[["record"] + flags + ["validated_by_human", "age", "sex"]], left_on="rec", right_on="record", how="left", suffixes=("", "_db"))
for f in flags:
    m[f + "_flag"] = m[f].notna() & (m[f].astype(str).str.strip() != "")

print(f"records: {len(m)}; bad readings total: {int(m['bad'].sum())} of {int(m['n'].sum())}")
print("\nTop recordings by number of bad readings, with PTB-XL flags (value shown if flagged):")
top = m.sort_values("bad", ascending=False).head(8)
for _, row in top.iterrows():
    fl = {f: str(row[f]).strip() for f in flags if row[f + "_flag"]}
    print(f"  {row['rec']}: {int(row['bad'])}/{int(row['n'])} bad | flags: {fl if fl else 'none'}")

print("\nBad-reading rate by PTB-XL flag (any flag vs none):")
m["any_flag"] = m[[f + "_flag" for f in flags]].any(axis=1)
for name, g in m.groupby("any_flag"):
    print(f"  any flag = {name}: {len(g)} records, {int(g['bad'].sum())} bad of {int(g['n'].sum())} tests ({100*g['bad'].sum()/g['n'].sum():.1f}%)")
for f in flags:
    g = m[m[f + "_flag"]]
    if len(g):
        print(f"  {f}: {len(g)} records, {int(g['bad'].sum())} bad of {int(g['n'].sum())} ({100*g['bad'].sum()/g['n'].sum():.1f}%)")
print("\nhuman-validated labels among these records: %d of %d" % (m["validated_by_human"].astype(bool).sum(), len(m)))
