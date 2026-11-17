"""Section I3 (sensitivity, exploratory, post hoc): flag recordings whose TRUE lead II gives a heart rate the peak detectors cannot agree on
(spread of 5 detectors on the TRUE signal > 10 bpm; 15 bpm also shown), then repeat the real-capture rates and the paired tests against C0 among the NOT flagged recordings.
Original definition stays the primary result. Needs results/analysis/sectionI2_truth_vs_digitised.csv."""
import numpy as np
import pandas as pd
from scipy.stats import binomtest

ROOT = "D:/Capstone Project/"
i2 = pd.read_csv(ROOT + "results/analysis/sectionI2_truth_vs_digitised.csv")
sp = i2.set_index("record").truth_spread_bpm
new = pd.read_csv(ROOT + "results/armCext/results_armCext_all.csv")
old = pd.read_csv(ROOT + "results/armC/results_armC.csv")
d = pd.concat([old, new], ignore_index=True)
d["none"] = d.dig_hr.isna()
d["wrong5"] = d.diff_bpm > 5
d["bad"] = d.none | d.wrong5
d["spread"] = d.record.map(sp)
assert d.spread.notna().all()
NAMES = {"C0_kit_original": "C0 clean kit page", "C1_print_scan_colour": "C1 print-scan colour", "C2_print_scan_bw": "C2 print-scan b/w", "C3_phone_photo_print": "C3 phone photo of print",
         "C4_phone_photo_screen": "C4 phone photo of screen", "C5_stained_soaked_photo": "C5 stained/soaked", "C6_extensive_damage_photo": "C6 extensive damage",
         "C7_mold_scan_colour": "C7 mould scan colour", "C8_mold_scan_bw": "C8 mould scan b/w"}


def wilson(k, n, z=1.96):
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return c - h, c + h


def pct(k, n):
    lo, hi = wilson(k, n)
    return f"{k}/{n} = {100 * k / n:.0f}% ({100 * lo:.0f}-{100 * hi:.0f})"


def holm(ps):
    ps = np.array(ps, float); o = np.argsort(ps); adj = np.empty_like(ps); run = 0
    for r, i in enumerate(o):
        run = max(run, (len(ps) - r) * ps[i]); adj[i] = min(1.0, run)
    return adj


rows, flag_rows = [], []
for thr in (10, 15):
    flagged = set(d[(d.axis == "C0_kit_original") & (d.spread > thr)].record)
    recs = d.drop_duplicates("record")
    c0 = d[d.axis == "C0_kit_original"]
    nf = c0.record.isin(flagged)
    flag_rows.append(dict(threshold_bpm=thr, recordings_flagged=f"{len(flagged)}/140", clean_page_wrong_in_flagged=pct(int(c0[nf].wrong5.sum()), int(nf.sum())),
                          clean_page_wrong_in_not_flagged=pct(int(c0[~nf].wrong5.sum()), int((~nf).sum())),
                          wrong_clean_pages_inside_flag=f"{int(c0[nf].wrong5.sum())}/{int(c0.wrong5.sum())}"))
    g = d[~d.record.isin(flagged)]
    c0g = g[g.axis == "C0_kit_original"].set_index("record")
    tmp = []
    for ax in NAMES:
        x = g[g.axis == ax].set_index("record")
        n = len(x)
        r = dict(threshold_bpm=thr, capture=NAMES[ax], recordings=n, no_output=pct(int(x.none.sum()), n), wrong_gt5=pct(int(x.wrong5.sum()), n))
        if ax != "C0_kit_original":
            a = x.wrong5.reindex(c0g.index).astype(bool).values
            b = c0g.wrong5.astype(bool).values
            w_, bt = int((a & ~b).sum()), int((~a & b).sum())
            p = binomtest(w_, w_ + bt, 0.5).pvalue if w_ + bt else 1.0
            r["_p"] = p; r["worse_than_C0/better"] = f"{w_}/{bt}"
        tmp.append(r)
    ph = holm([t["_p"] for t in tmp if "_p" in t])
    k = 0
    for t in tmp:
        if "_p" in t:
            t["p_exact"] = round(t.pop("_p"), 4); t["p_holm"] = round(ph[k], 4); k += 1
        rows.append(t)
sens = pd.DataFrame(rows)
flg = pd.DataFrame(flag_rows)
sens.to_csv(ROOT + "results/analysis/sectionI3_sensitivity_rates.csv", index=False)
flg.to_csv(ROOT + "results/analysis/sectionI3_flag_summary.csv", index=False)
pd.set_option("display.width", 250)
print(flg.to_string(index=False)); print()
print(sens.to_string(index=False))
