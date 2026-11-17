"""One source of truth for the journal manuscript's numbers and tables.

Intervals (PR/QRS/QT/QTc) use the 500 Hz ground truth; heart rate uses the original ground truth (the sweep's
100 Hz-derived HR, whose agreement with 500 Hz HR is reported below). Reliable = 49 records (v2 run).
Outputs: docs/journal/tables/*.csv and a printed block of every number quoted in the text.
"""
import os
import numpy as np
import pandas as pd
from scipy import stats

B = r"D:\Capstone Project\results\v2_intervals"
T = r"D:\Capstone Project\docs\journal\tables"
os.makedirs(T, exist_ok=True)
d = pd.read_csv(f"{B}/journal/intervals_gt500_outcomes.csv")          # reliable rows, 500 Hz interval GT
chk = pd.read_csv(f"{B}/journal/gt_sampling_rate_check.csv")          # clean rows with gt500_* and gt_hr
allrows = pd.read_csv(f"{B}/results_v2_clean.csv")
AXES = ["blur", "rotate", "jpeg", "resolution", "brightness", "gridcontrast"]
M = {"diff_bpm": "HR (bpm)", "diff_pr_ms": "PR (ms)", "diff_qrs_ms": "QRS (ms)", "diff_qt_ms": "QT (ms)", "diff_qtc_ms": "QTc (ms)"}
P = {}

# ---------------------------------------------------- sample composition (all 50 records)
db = pd.read_csv(r"D:\Capstone Project\data\ptbxl\ptbxl_database.csv")
db["record"] = db["filename_lr"].apply(lambda p: p.split("/")[-1])
s = allrows.drop_duplicates("record")[["record", "sex", "diagnostic_class", "is_abnormal"]].merge(
    db[["record", "age"]], on="record", how="left")
s["diagnostic_class"] = s["diagnostic_class"].fillna("(none)")
comp = s.groupby("diagnostic_class").agg(records=("record", "size")).reset_index()
comp.to_csv(f"{T}/sample_composition.csv", index=False)
P["n_records"] = len(s); P["male"] = int((s.sex == "male").sum()); P["female"] = int((s.sex == "female").sum())
P["age_median"] = float(s.age.median()); P["age_min"] = int(s.age.min()); P["age_max"] = int(s.age.max())
P["class_counts"] = dict(zip(comp.diagnostic_class, comp.records))

# ---------------------------------------------------- full summary table (median [IQR]) per axis/level/metric
rows = []
for ax in ["clean"] + AXES:
    for lv in ([0] if ax == "clean" else range(1, 6)):
        sub = d[(d.axis == ax) & (d.level == lv)]
        r = {"axis": ax, "level": lv, "n": len(sub)}
        for c, name in M.items():
            x = sub[c].dropna()
            r[name] = f"{x.median():.1f} [{x.quantile(.25):.1f}-{x.quantile(.75):.1f}]" if len(x) else ""
            r[name + " n"] = len(x)
        rows.append(r)
pd.DataFrame(rows).to_csv(f"{T}/error_by_axis_level_median_iqr.csv", index=False)

# ---------------------------------------------------- paired Wilcoxon + Holm (500 Hz GT for intervals)
def holm(p):
    p = np.asarray(p, float); o = np.argsort(p); m = len(p); adj = np.empty(m); run = 0.0
    for k, i in enumerate(o):
        run = max(run, (m - k) * p[i]); adj[i] = min(1.0, run)
    return adj

clean = d[d.axis == "clean"].set_index("record")
out = []
for c, name in M.items():
    rr = []
    for ax in AXES:
        for lv in range(1, 6):
            sub = d[(d.axis == ax) & (d.level == lv)].set_index("record")
            idx = sub.index.intersection(clean.index)
            a, b = sub.loc[idx, c], clean.loc[idx, c]
            ok = a.notna() & b.notna(); a, b = a[ok], b[ok]
            p = stats.wilcoxon(a, b)[1] if len(a) >= 6 and not np.allclose(a, b) else np.nan
            rr.append({"metric": name, "axis": ax, "level": lv, "n_pairs": len(a),
                       "median_excess": float((a - b).median()), "p_raw": p})
    t = pd.DataFrame(rr); v = t.p_raw.notna()
    t.loc[v, "p_holm"] = holm(t.loc[v, "p_raw"])
    out.append(t)
tests = pd.concat(out); tests["sig"] = tests.p_holm < 0.05
tests.to_csv(f"{T}/paired_tests_gt500.csv", index=False)
for name in M.values():
    g = tests[tests.metric == name]; sg = g[g.sig]
    P[f"sig_{name}"] = {ax: int(x.level.min()) for ax, x in sg.groupby("axis")}
    P[f"nsig_{name}"] = int(len(sg))

# ---------------------------------------------------- Bland-Altman on clean, 500 Hz GT
ba = []
for name, gt, dg in [("HR (bpm)", "gt_hr", "dig_hr"), ("PR (ms)", "gt500_pr", "dig_pr_ms"), ("QRS (ms)", "gt500_qrs", "dig_qrs_ms"),
                     ("QT (ms)", "gt500_qt", "dig_qt_ms"), ("QTc (ms)", "gt500_qtc", "dig_qtc_ms")]:
    x = (chk[dg] - chk[gt]).dropna(); sd = x.std(ddof=1)
    ba.append({"measure": name, "n": len(x), "bias": x.mean(), "sd": sd, "loa_low": x.mean() - 1.96 * sd,
               "loa_high": x.mean() + 1.96 * sd, "mean_abs_error": x.abs().mean()})
pd.DataFrame(ba).round(2).to_csv(f"{T}/bland_altman_clean_gt500.csv", index=False)
P["hr_gt_100_vs_500_mean_abs_diff"] = float((chk.gt_hr - chk.gt500_hr).abs().mean())
P["hr_clean_outliers_gt5bpm"] = int(((chk.dig_hr - chk.gt_hr).abs() > 5).sum())

# ---------------------------------------------------- reliability + missingness
P["tests_total"] = len(allrows)
P["hr_missing"] = int(allrows.dig_hr.isna().sum()); P["qtc_missing"] = int(allrows.dig_qtc_ms.isna().sum())
P["reliable_records"] = int(d.record.nunique())
P["rows_per_axis_missing_hr"] = allrows[allrows.dig_hr.isna()].groupby("axis").size().to_dict()

# ---------------------------------------------------- QTc outcomes (500 Hz GT, corrected)
fr = d.out == "false_reassurance"
real = fr & d.clean_ok & (d.diff_qtc_ms > 10)
P["qtc_fr_total"] = int(fr.sum()); P["qtc_fr_wrong_on_clean"] = int((fr & ~d.clean_ok).sum()); P["qtc_fr_real"] = int(real.sum())
P["qtc_at_risk_records"] = int(d[d.gt_qtc_abnormal == True].record.nunique())
P["qtc_at_risk_usable"] = int(d[(d.gt_qtc_abnormal == True) & d.clean_ok].record.nunique())
P["qtc_real_by_cell"] = {f"{a}{l}": int(n) for (a, l), n in d[real].groupby(["axis", "level"]).size().items()}
P["clean_outcomes"] = d[d.axis == "clean"].out.value_counts().to_dict()

# ---------------------------------------------------- per-class (QTc, HR) at clean/blur5/res5
pc = []
for cls, g in d.groupby(d.diagnostic_class.fillna("(none)")):
    r = {"class": cls, "records": g.record.nunique()}
    for c, nm in [("diff_bpm", "HR"), ("diff_qtc_ms", "QTc")]:
        r[f"{nm} clean"] = g[g.axis == "clean"][c].median()
        r[f"{nm} blur5"] = g[(g.axis == "blur") & (g.level == 5)][c].median()
        r[f"{nm} res5"] = g[(g.axis == "resolution") & (g.level == 5)][c].median()
    pc.append(r)
pd.DataFrame(pc).round(1).to_csv(f"{T}/per_class_gt500.csv", index=False)

print("=== NUMBERS QUOTED IN THE MANUSCRIPT ===")
for k, v in P.items():
    print(f"{k}: {v}")
print("\nBland-Altman clean (500 Hz GT):"); print(pd.DataFrame(ba).round(2).to_string(index=False))
print("\nPer-class:"); print(pd.DataFrame(pc).round(1).to_string(index=False))
print("\nSample composition:"); print(comp.to_string(index=False))
