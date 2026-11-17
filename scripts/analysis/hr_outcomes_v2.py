"""Heart-rate patient-facing outcomes in the v2 sweep, using the SAME rules as the v1 analysis (Part 2):
slow <60, normal 60-100, fast >100 bpm; 'real' false reassurance = told normal, truth slow/fast, digitized rate
off by >10 bpm; boundary flips (<=10 bpm) reported separately; silent drop = no digitized rate.
Reliable = 49 records of the v2 run (only 15192_lr excluded).
"""
import numpy as np
import pandas as pd

d = pd.read_csv(r"D:\Capstone Project\results\v2_intervals\results_v2_clean.csv")
rel = d[d.reliable].copy()


def band(x):
    return np.nan if pd.isna(x) else ("slow" if x < 60 else "fast" if x > 100 else "normal")


rel["gt_band"] = rel.gt_hr.apply(band); rel["dig_band"] = rel.dig_hr.apply(band)
at_risk = rel[rel.gt_band.isin(["slow", "fast"])]
recs = at_risk.record.nunique()
print(f"reliable records {rel.record.nunique()}, records with slow/fast ground-truth HR (at risk): {recs} "
      f"({at_risk.drop_duplicates('record').gt_band.value_counts().to_dict()})")

fr = at_risk[(at_risk.dig_band == "normal")]
real = fr[fr.diff_bpm > 10]; border = fr[~(fr.diff_bpm > 10)]
print(f"false-reassurance events: {len(fr)} total; REAL (>10 bpm off): {len(real)}; boundary flips: {len(border)}")
print("real events by axis/level:", real.groupby(["axis", "level"]).size().to_dict())
print("real events detail:"); print(real[["record", "axis", "level", "gt_hr", "dig_hr", "diff_bpm"]].round(1).to_string(index=False))
print("boundary flips:"); print(border[["record", "axis", "level", "gt_hr", "dig_hr", "diff_bpm"]].round(1).to_string(index=False))

clean = rel[rel.axis == "clean"]
print("\nclean-image band agreement:", (clean.gt_band == clean.dig_band).sum(), "/", clean.dig_band.notna().sum(),
      "| clean rows with no HR:", int(clean.dig_hr.isna().sum()))

sd = rel[rel.dig_hr.isna()]
print("\nsilent drops by axis/level (of 49 reliable records each):")
print(sd.groupby(["axis", "level"]).size().unstack(fill_value=0).to_string())

print("\nHR error mean/median by axis and level:")
rows = []
for ax in ["clean", "blur", "resolution", "rotate", "jpeg", "brightness", "gridcontrast"]:
    for lv in ([0] if ax == "clean" else range(1, 6)):
        s = rel[(rel.axis == ax) & (rel.level == lv)].diff_bpm.dropna()
        rows.append((ax, lv, len(s), round(s.mean(), 2), round(s.median(), 2), round((s > 5).mean() * 100, 1)))
print(pd.DataFrame(rows, columns=["axis", "level", "n", "mean", "median", "pct_gt5bpm"]).to_string(index=False))
