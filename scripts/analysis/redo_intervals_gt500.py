"""Redo the interval error + QTc outcome analysis using 500 Hz ground truth (instead of the 100 Hz records the
sweep notebook used). Digitized values are unchanged (they come from the sweep); only the ground truth side is
recomputed from the same PTB-XL records at 500 Hz (see check_gt_sampling_rate.py).
"""
import numpy as np
import pandas as pd
from scipy import stats

B = r"D:\Capstone Project\results\v2_intervals"
res = pd.read_csv(f"{B}/results_v2_clean.csv")
g500 = pd.read_csv(f"{B}/journal/gt_sampling_rate_check.csv")[
    ["record", "gt500_pr", "gt500_qrs", "gt500_qt", "gt500_qtc"]]

df = res[res["reliable"]].merge(g500, on="record", how="left")
df["gt_pr_ms"], df["gt_qrs_ms"], df["gt_qt_ms"], df["gt_qtc_ms"] = (
    df["gt500_pr"], df["gt500_qrs"], df["gt500_qt"], df["gt500_qtc"])
for m in ["pr", "qrs", "qt", "qtc"]:
    df[f"diff_{m}_ms"] = (df[f"dig_{m}_ms"] - df[f"gt_{m}_ms"]).abs()
THR = {"female": 460.0, "male": 450.0}
df["gt_qtc_abnormal"] = df.apply(lambda r: (r["gt_qtc_ms"] > THR[r["sex"]]) if pd.notna(r["gt_qtc_ms"]) else np.nan, axis=1)
df["dig_qtc_abnormal"] = df.apply(lambda r: (r["dig_qtc_ms"] > THR[r["sex"]]) if pd.notna(r["dig_qtc_ms"]) else np.nan, axis=1)

print("=== Median error by axis/level with 500 Hz ground truth (ms) ===")
print(f"{'axis':<13}{'lvl':>4}   {'PR':>6}{'QRS':>7}{'QT':>7}{'QTc':>7}")
for ax in ["clean", "blur", "resolution", "rotate", "jpeg", "brightness", "gridcontrast"]:
    for lv in ([0] if ax == "clean" else [1, 3, 5]):
        s = df[(df["axis"] == ax) & (df["level"] == lv)]
        print(f"{ax:<13}{lv:>4}   {s['diff_pr_ms'].median():>6.1f}{s['diff_qrs_ms'].median():>7.1f}"
              f"{s['diff_qt_ms'].median():>7.1f}{s['diff_qtc_ms'].median():>7.1f}")


def classify(r):
    if pd.isna(r["dig_qtc_ms"]):
        return "silent_drop"
    if pd.isna(r["gt_qtc_abnormal"]):
        return "gt_unavailable"
    g, d = bool(r["gt_qtc_abnormal"]), bool(r["dig_qtc_abnormal"])
    return "false_reassurance" if (g and not d) else "false_alarm" if (d and not g) else "correct"


df["out"] = df.apply(classify, axis=1)
clean_out = df[df["axis"] == "clean"].set_index("record")["out"]
df["clean_ok"] = df["record"].map(clean_out) != "false_reassurance"
fr = df["out"] == "false_reassurance"
real = fr & df["clean_ok"] & (df["diff_qtc_ms"] > 10)
at_risk_recs = df[df["gt_qtc_abnormal"] == True]["record"].nunique()
usable = df[(df["gt_qtc_abnormal"] == True) & df["clean_ok"]]["record"].nunique()
print(f"\nAt-risk records (500 Hz GT, truly prolonged QTc): {at_risk_recs}; usable (correct on clean): {usable}")
print(f"False-reassurance events total: {int(fr.sum())}; already wrong on own clean image: {int((fr & ~df['clean_ok']).sum())}; "
      f"REAL (correct on clean, >10 ms off): {int(real.sum())}")
print("\nReal events by axis/level:")
print(df[real].groupby(["axis", "level"]).size().to_string() if real.any() else "  none")
print("\nClean-image outcome counts:", df[df["axis"] == "clean"]["out"].value_counts().to_dict())
df.to_csv(f"{B}/journal/intervals_gt500_outcomes.csv", index=False)
