"""Per-test comparison of Sweep 1 (heart rate only) and Sweep 2 (v2, intervals) on the SAME test ids.
Answers: are the false-reassurance events the same tests? how well do per-test HR values agree between sweeps?
Sweep 1 file: results_clean.csv (Drive, downloaded 2026-09-25). Sweep 1 reliable = 44 records (6 excluded, Part 1b).
Sweep 2 reliable = 49 records (15192_lr excluded)."""
import numpy as np
import pandas as pd

V1_EXCLUDED = ["00102_lr", "08150_lr", "13316_lr", "00053_lr", "18151_lr", "19059_lr"]
v1 = pd.read_csv(r"C:/Users/Nihar Sai/Downloads/results_clean.csv")
v2 = pd.read_csv(r"D:\Capstone Project\results\v2_intervals\results_v2_clean.csv")


def band(x):
    return np.nan if pd.isna(x) else ("slow" if x < 60 else "fast" if x > 100 else "normal")


m = v1.merge(v2[["variant_id", "gt_hr", "dig_hr", "diff_bpm", "reliable"]], on="variant_id", suffixes=("_1", "_2"))
print("same test ids:", len(m), "of", len(v1), len(v2))
print("ground-truth HR identical where both present:", int((m.gt_hr_1.sub(m.gt_hr_2).abs() < 0.06).sum()), "of",
      int(m.gt_hr_1.notna().sum()))

both = m[~m.record.isin(V1_EXCLUDED) & m.reliable].copy()
print("records in both reliable sets:", both.record.nunique())
print("tests with a value in both sweeps:", int(both.dig_hr_1.notna().mul(both.dig_hr_2.notna()).sum()),
      "of", len(both))
print("readable in v1 only:", int((both.dig_hr_1.notna() & both.dig_hr_2.isna()).sum()),
      "| readable in v2 only:", int((both.dig_hr_1.isna() & both.dig_hr_2.notna()).sum()),
      "| unreadable in both:", int((both.dig_hr_1.isna() & both.dig_hr_2.isna()).sum()))

bp = both.dropna(subset=["dig_hr_1", "dig_hr_2"])
d = (bp.dig_hr_1 - bp.dig_hr_2).abs()
print(f"digitised HR difference between sweeps: median {d.median():.2f}, mean {d.mean():.2f}, "
      f"p95 {d.quantile(.95):.2f}, max {d.max():.1f} bpm; identical to 0.1 bpm in {(d < 0.15).mean()*100:.0f}% of tests")
print("clean images only:", bp[bp.axis == "clean"].pipe(lambda x: (x.dig_hr_1 - x.dig_hr_2).abs().describe().round(2).to_dict()))
print("\ntests differing by >5 bpm between sweeps:")
big = bp[(bp.dig_hr_1 - bp.dig_hr_2).abs() > 5]
print(big[["variant_id", "gt_hr_1", "dig_hr_1", "dig_hr_2"]].round(1).to_string(index=False))

# unreadable patterns per axis/level
print("\nunreadable counts by axis (reliable records in both):")
u = both.assign(u1=both.dig_hr_1.isna(), u2=both.dig_hr_2.isna()).groupby("axis")[["u1", "u2"]].sum()
print(u)
sd_agree = both[both.dig_hr_1.isna() | both.dig_hr_2.isna()]
print("silent-drop tests:", len(sd_agree), "| same in both:", int((sd_agree.dig_hr_1.isna() & sd_agree.dig_hr_2.isna()).sum()))

# false reassurance events (same rule as Part 2 / hr_outcomes_v2)
def events(df, gt, dig, diff):
    df = df.assign(gb=df[gt].apply(band), db=df[dig].apply(band))
    r = df[df.gb.isin(["slow", "fast"]) & (df.db == "normal") & (df[diff] > 10)]
    return set(r.variant_id)


s1 = events(v1[~v1.record.isin(V1_EXCLUDED)], "gt_hr", "dig_hr", "diff_bpm")
s2 = events(v2[v2.reliable], "gt_hr", "dig_hr", "diff_bpm")
print("\nreal HR false-reassurance events: sweep1", len(s1), "sweep2", len(s2), "| in both:", len(s1 & s2))
print("only sweep1:", sorted(s1 - s2)); print("only sweep2:", sorted(s2 - s1)); print("both:", sorted(s1 & s2))
