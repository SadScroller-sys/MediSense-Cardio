"""Do the damage-type conclusions change when recordings with PTB-XL quality flags are removed?

Bad reading = heart rate unreadable or off by more than 5 bpm (primary target of the held-out detector test).
Sets compared (reliable records only, at most 6 of 31 versions unreadable):
  all        every reliable record (49)
  no_flags   records with none of PTB-XL's flags (baseline_drift, static_noise, burst_noise, electrodes_problems,
             extra_beats, pacemaker)
  no_top5    all except the five records with most bad readings
Reads data/ptbxl/ptbxl_database.csv and results/v2_intervals/results_v2.csv. Prints tables, writes results/flagged_recordings_effect.md.
"""
import numpy as np
import pandas as pd

db = pd.read_csv("D:/Capstone Project/data/ptbxl/ptbxl_database.csv")
db["rec"] = db["filename_lr"].str.split("/").str[-1]
res = pd.read_csv("D:/Capstone Project/results/v2_intervals/results_v2.csv")
unread = res.groupby("record")["dig_hr"].apply(lambda s: s.isna().sum())
rel = set(unread[unread <= 6].index)
r = res[res["record"].isin(rel)].copy()
r["bad"] = r["dig_hr"].isna() | (r["diff_bpm"].abs() > 5)
r["rec"] = r["record"].str.replace(r"-0$", "", regex=True)

flags = ["baseline_drift", "static_noise", "burst_noise", "electrodes_problems", "extra_beats", "pacemaker"]
fl = db.set_index("rec")[flags]
flagged = {rec for rec in r["rec"].unique() if rec in fl.index and fl.loc[rec].notna().any()
           and (fl.loc[rec].astype(str).str.strip() != "").any()}
per = r.groupby("rec")["bad"].sum().sort_values(ascending=False)
top5 = set(per.index[:5])

sets = {"all": r, "no_flags": r[~r["rec"].isin(flagged)], "no_top5": r[~r["rec"].isin(top5)]}
out = []
out.append("# Effect of PTB-XL-flagged and hard recordings on the damage-type results (2026-11-04)\n")
out.append("Target: heart rate unreadable or off by more than 5 bpm. Script: scripts/analysis/flagged_recordings_effect.py.\n")
out.append(f"Flagged records among the 49: {len(flagged)} ({sorted(flagged)}).\nTop-5 hardest: {sorted(top5)}.\n")

summ = []
for name, d in sets.items():
    summ.append({"set": name, "records": d["rec"].nunique(), "tests": len(d), "bad": int(d["bad"].sum()),
                 "bad_rate_%": round(100 * d["bad"].mean(), 1),
                 "clean_bad_%": round(100 * d[d.axis == "clean"]["bad"].mean(), 1)})
FENCE = "`" * 3


def block(frame, index=True):
    return FENCE + "\n" + frame.to_string(index=index) + "\n" + FENCE + "\n"


out.append("## Overall\n" + block(pd.DataFrame(summ), index=False))

for name, d in sets.items():
    t = d[d.axis != "clean"].groupby(["axis", "level"])["bad"].mean().mul(100).round(1).unstack()
    out.append(f"## Bad-reading rate (%) by damage type and level: {name}\n" + block(t))

# ranking of damage types at level 5 and pooled over levels
rank = {}
for name, d in sets.items():
    dd = d[d.axis != "clean"]
    rank[name] = {"level5": dd[dd.level == 5].groupby("axis")["bad"].mean().mul(100).round(1).sort_values(ascending=False).to_dict(),
                  "pooled": dd.groupby("axis")["bad"].mean().mul(100).round(1).sort_values(ascending=False).to_dict()}
for k in ("level5", "pooled"):
    out.append(f"## Ranking of damage types, {k} (bad rate %)\n")
    for name in sets:
        out.append(f"- {name}: " + ", ".join(f"{a} {v}" for a, v in rank[name][k].items()))
    out.append("")

text = "\n".join(out)
print(text)
open("D:/Capstone Project/results/flagged_recordings_effect.md", "w", encoding="utf-8").write(text)
