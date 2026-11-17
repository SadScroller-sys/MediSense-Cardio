"""Extra analyses for the journal version (docs/JOURNAL-PLAN.md items 1-4), run on the v2 sweep only.

1. T1 signal fidelity: snr_db vs degradation, per axis/level.
2. Formal statistics: each degraded level vs the SAME record's clean image (paired Wilcoxon signed-rank),
   Holm-corrected across the 6 axes x 5 levels, with median paired difference as the effect size.
3. Agreement on clean images: Bland-Altman bias and 95% limits of agreement for HR and QTc.
4. Per-diagnostic-class breakdown of error at the worst levels.

All outputs go to results/v2_intervals/journal/. Uses the reliable-record subset produced by
analyze_v2_intervals.py (results_v2_clean.csv, column `reliable`).
"""
import os
import numpy as np
import pandas as pd
from scipy import stats

BASE = r"D:\Capstone Project\results\v2_intervals"
OUT = os.path.join(BASE, "journal")
os.makedirs(OUT, exist_ok=True)

df = pd.read_csv(os.path.join(BASE, "results_v2_clean.csv"))
rel = df[df["reliable"]].copy()
AXES = ["blur", "rotate", "jpeg", "resolution", "brightness", "gridcontrast"]
METRICS = {"diff_bpm": "HR", "diff_pr_ms": "PR", "diff_qrs_ms": "QRS", "diff_qt_ms": "QT", "diff_qtc_ms": "QTc"}

print(f"Reliable tests: {len(rel)} ({rel['record'].nunique()} records)")

# ---------------------------------------------------------------- 1. SNR (T1)
print("\n=== 1. SNR (dB) by axis/level, reliable records ===")
snr_rows = []
clean_snr = rel[rel["axis"] == "clean"]["snr_db"]
snr_rows.append({"axis": "clean", "level": 0, "n": int(clean_snr.notna().sum()),
                 "median": clean_snr.median(), "q1": clean_snr.quantile(.25), "q3": clean_snr.quantile(.75)})
for ax in AXES:
    for lv in range(1, 6):
        s = rel[(rel["axis"] == ax) & (rel["level"] == lv)]["snr_db"]
        snr_rows.append({"axis": ax, "level": lv, "n": int(s.notna().sum()),
                         "median": s.median(), "q1": s.quantile(.25), "q3": s.quantile(.75)})
snr = pd.DataFrame(snr_rows).round(2)
snr.to_csv(os.path.join(OUT, "t1_snr_by_axis_level.csv"), index=False)
print(snr.to_string(index=False))

# ---------------------------------------------- 2. paired tests vs own clean image
print("\n=== 2. Paired Wilcoxon: degraded level vs same record's clean image (Holm-corrected) ===")


def holm(pvals):
    p = np.asarray(pvals, dtype=float)
    order = np.argsort(p)
    m = len(p)
    adj = np.empty(m)
    running = 0.0
    for rank, idx in enumerate(order):
        val = (m - rank) * p[idx]
        running = max(running, val)
        adj[idx] = min(1.0, running)
    return adj


clean_by_rec = rel[rel["axis"] == "clean"].set_index("record")
test_rows = []
for col, name in METRICS.items():
    rows = []
    for ax in AXES:
        for lv in range(1, 6):
            sub = rel[(rel["axis"] == ax) & (rel["level"] == lv)].set_index("record")
            common = sub.index.intersection(clean_by_rec.index)
            a = sub.loc[common, col]
            b = clean_by_rec.loc[common, col]
            ok = a.notna() & b.notna()
            a, b = a[ok], b[ok]
            n = len(a)
            if n < 6 or np.allclose(a.values, b.values):
                p, stat = np.nan, np.nan
            else:
                stat, p = stats.wilcoxon(a.values, b.values)
            rows.append({"metric": name, "axis": ax, "level": lv, "n_pairs": n,
                         "median_excess": float((a - b).median()) if n else np.nan, "p_raw": p})
    tmp = pd.DataFrame(rows)
    valid = tmp["p_raw"].notna()
    tmp.loc[valid, "p_holm"] = holm(tmp.loc[valid, "p_raw"].values)
    test_rows.append(tmp)
tests = pd.concat(test_rows, ignore_index=True)
tests["sig_holm_0.05"] = tests["p_holm"] < 0.05
tests.round({"median_excess": 2, "p_raw": 4, "p_holm": 4}).to_csv(
    os.path.join(OUT, "paired_tests_vs_clean.csv"), index=False)
for name in METRICS.values():
    sig = tests[(tests["metric"] == name) & (tests["sig_holm_0.05"])]
    print(f"{name}: {len(sig)}/30 cells significant after Holm. "
          f"Axes involved: {sorted(sig['axis'].unique())}; lowest significant level per axis: "
          f"{ {ax: int(g['level'].min()) for ax, g in sig.groupby('axis')} }")

# ------------------------------------------------- 3. Bland-Altman on clean images
print("\n=== 3. Bland-Altman on CLEAN images (digitized minus ground truth) ===")
clean = rel[rel["axis"] == "clean"]
ba_rows = []
for gt, dg, name, unit in [("gt_hr", "dig_hr", "HR", "bpm"), ("gt_pr_ms", "dig_pr_ms", "PR", "ms"),
                           ("gt_qrs_ms", "dig_qrs_ms", "QRS", "ms"), ("gt_qt_ms", "dig_qt_ms", "QT", "ms"),
                           ("gt_qtc_ms", "dig_qtc_ms", "QTc", "ms")]:
    d = (clean[dg] - clean[gt]).dropna()
    bias, sd = d.mean(), d.std(ddof=1)
    ba_rows.append({"measure": name, "unit": unit, "n": len(d), "bias": bias, "sd": sd,
                    "loa_low": bias - 1.96 * sd, "loa_high": bias + 1.96 * sd,
                    "mean_abs_error": d.abs().mean()})
ba = pd.DataFrame(ba_rows).round(2)
ba.to_csv(os.path.join(OUT, "bland_altman_clean.csv"), index=False)
print(ba.to_string(index=False))

# ----------------------------------------------------------- 4. per-class breakdown
print("\n=== 4. Per-class median error: clean vs worst level of blur and resolution ===")
cls_rows = []
for cls, g in rel.groupby("diagnostic_class", dropna=False):
    label = cls if isinstance(cls, str) else "unlabelled/NORM-other"
    row = {"class": label, "n_records": g["record"].nunique()}
    for col, name in [("diff_bpm", "HR"), ("diff_qtc_ms", "QTc")]:
        row[f"{name}_clean"] = g[g["axis"] == "clean"][col].median()
        row[f"{name}_blur5"] = g[(g["axis"] == "blur") & (g["level"] == 5)][col].median()
        row[f"{name}_res5"] = g[(g["axis"] == "resolution") & (g["level"] == 5)][col].median()
    cls_rows.append(row)
cls_df = pd.DataFrame(cls_rows).round(2)
cls_df.to_csv(os.path.join(OUT, "per_class_error.csv"), index=False)
print(cls_df.to_string(index=False))

print("\nDONE ->", OUT)
