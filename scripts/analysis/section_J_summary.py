"""Section J summary: rates and paired tests against the clean kit page with the CLEANED heart-rate measurement (sectionJ_remeasured.csv), next to the original measurement."""
import numpy as np
import pandas as pd
from scipy.stats import binomtest

ROOT = "D:/Capstone Project/"
d = pd.read_csv(ROOT + "results/analysis/sectionJ_remeasured.csv")
d["rec"] = d.set + "_" + d.record.astype(str)
d["none"] = d.dig_hr.isna()
d["lost2"] = d.dig_hr.notna() & d.dig_hr_clean.isna()
d["w_old"] = d.diff_bpm > 5
d["w_new"] = d.diff_clean > 5
d["w_new10"] = d.diff_clean > 10
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


out = []
for pop, g in (("new100", d[d.set == "armC_new100"]), ("pooled140", d)):
    c0 = g[g.axis == "C0_kit_original"].set_index("rec")
    tmp = []
    for ax in NAMES:
        x = g[g.axis == ax].set_index("rec")
        n = len(x)
        r = dict(population=pop, capture=NAMES[ax], recordings=n, no_output=pct(int(x.none.sum()), n), wrong_original=pct(int(x.w_old.sum()), n),
                 wrong_cleaned=pct(int(x.w_new.sum()), n), wrong_cleaned_gt10=pct(int(x.w_new10.sum()), n),
                 median_abs_err_cleaned=round(float(x.diff_clean.median()), 2), p90_abs_err_cleaned=round(float(x.diff_clean.quantile(0.9)), 1))
        if ax != "C0_kit_original":
            a = x.w_new.reindex(c0.index).astype(bool).values
            b = c0.w_new.astype(bool).values
            w_, bt = int((a & ~b).sum()), int((~a & b).sum())
            r["_p"] = binomtest(w_, w_ + bt, 0.5).pvalue if w_ + bt else 1.0
            r["worse/better_than_C0"] = f"{w_}/{bt}"
        tmp.append(r)
    ph = holm([t["_p"] for t in tmp if "_p" in t]); k = 0
    for t in tmp:
        if "_p" in t:
            t["p_exact"] = round(t.pop("_p"), 4); t["p_holm"] = round(ph[k], 4); k += 1
        out.append(t)
o = pd.DataFrame(out)
o.to_csv(ROOT + "results/analysis/sectionJ_rates_cleaned.csv", index=False)
pd.set_option("display.width", 280); pd.set_option("display.max_colwidth", 40)
print(o.to_string(index=False))
for pop, g in (("new100", d[d.set == "armC_new100"]), ("pooled140", d)):
    print(pop, "wrong (all types) original:", int(g.w_old.sum()), "cleaned:", int(g.w_new.sum()), "| real C1-C8 original:", int(g[g.axis != 'C0_kit_original'].w_old.sum()),
          "cleaned:", int(g[g.axis != 'C0_kit_original'].w_new.sum()), "| lost output after cleaning:", int(g.lost2.sum()))
w = d[d.axis == "C0_kit_original"]
print("clean page: wrong original", int(w.w_old.sum()), "-> cleaned", int(w.w_new.sum()), "| both", int((w.w_old & w.w_new).sum()))
print("clean page still wrong after cleaning:\n", w[w.w_new][["set", "record", "gt_hr_clean", "dig_hr_clean", "diff_clean"]].round(1).to_string(index=False))
# how many of the 16 old-wrong turn right
print("recordings: wrong on clean page originally 16 ->", int(w.w_old.sum()), "; wrong in cleaned view that were right originally:", int((~w.w_old & w.w_new).sum()))
# error size distribution cleaned
wr = d[d.w_new]
print("cleaned wrong readings:", len(wr), "| 5-10 bpm:", int((wr.diff_clean <= 10).sum()), "| >20:", int((wr.diff_clean > 20).sum()), "| median", round(float(wr.diff_clean.median()), 1))
