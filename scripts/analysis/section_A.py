"""Section A (MASTER_PLAN section 4b items 7 and 13): signal quality (aligned SNR) and paired heart-rate error against each image's own clean version.

Reads (never modifies): results/extension/results_extension.csv (new 100, has snr_aligned_db),
                        results/bridge/results_bridge.csv (12 recordings of the first 50, has snr_aligned_db),
                        results/v2_intervals/results_v2.csv (first 50; its saved snr_db is INVALID and is never used here; heart rates only),
                        results/extension/reference_check_150.csv, data/ptbxl/ptbxl_database.csv.
Writes: results/analysis/sectionA_*.csv and results/analysis/SECTION_A.md

Exploratory throughout (MASTER_PLAN). Definitions as in section_C.py.
  Aligned SNR = lead II, shift of up to +-0.5 s, offset removed, digitised vs the 100 Hz record the page was drawn from.
  It is computed only when the digitiser gave an output. For the first 50 no valid SNR exists (digitised signals were not kept in sweep 2),
  so SNR results are on the new 100 (in-distribution: the digitiser was trained on pages from the same generator family) plus the 12 bridge recordings as a small check.
  'Acceptable SNR' (this script's definition, fixed before looking at the cases): at or above the 10th percentile of the clean-page SNR of the same recordings.
  Paired test (item 7): for each damage type and level, |HR error| of the damaged page vs |HR error| of the same recording's clean page,
  Wilcoxon signed-rank (two-sided, zero differences dropped), Holm over the 12 damage x level comparisons within each population.
  Bland-Altman: signed error = digitised - reference, images with output; bias, SD, limits of agreement bias +- 1.96 SD.
"""
import os

import numpy as np
import pandas as pd
from scipy.stats import spearmanr, wilcoxon

ROOT = "D:/Capstone Project"
OUT = f"{ROOT}/results/analysis"
os.makedirs(OUT, exist_ok=True)
AXES = ["resolution", "blur", "rotate", "jpeg", "brightness", "gridcontrast"]
SHARED = {0, 3, 5}
rng = np.random.default_rng(42)

v = pd.read_csv(f"{ROOT}/results/v2_intervals/results_v2.csv")
e = pd.read_csv(f"{ROOT}/results/extension/results_extension.csv")
b = pd.read_csv(f"{ROOT}/results/bridge/results_bridge.csv")
v["set"], e["set"], b["set"] = "first50", "new100", "bridge12"
base = ["set", "record", "axis", "level", "gt_hr", "dig_hr", "diff_bpm"]
d = pd.concat([v[base], e[base + ["snr_aligned_db"]], b[base + ["snr_aligned_db"]]], ignore_index=True)
d["none"] = d.dig_hr.isna()
d["wrong5"] = d.diff_bpm > 5
d["signed"] = d.dig_hr - d.gt_hr
assert d.loc[d.set == "first50", "snr_aligned_db"].isna().all()   # nothing valid for the first 50

# unreliable recordings (same rule as section_C.py)
nv = d[d.set.isin(["first50", "new100"])].groupby(["set", "record"]).none.sum().reset_index()
UNREL = set(nv[nv.apply(lambda r: r.none > {"first50": 6, "new100": 2}[r.set], axis=1)].record)
d = d[~d.record.isin(UNREL)]
print("excluded unreliable:", sorted(UNREL))

n100 = d[(d.set == "new100") & d.level.isin(SHARED)]
br12 = d[d.set == "bridge12"]
f50 = d[(d.set == "first50")]
all150 = d[d.set.isin(["first50", "new100"]) & d.level.isin(SHARED)]


def q(s):
    return pd.Series({"n_with_snr": int(s.notna().sum()), "median": s.median(), "q25": s.quantile(.25), "q75": s.quantile(.75)})


# ------------------------------------------------------------- 1. SNR by damage type and level
snr_tab = []
for name, x in (("new100", n100), ("bridge12", br12)):
    g = x.groupby(["axis", "level"]).snr_aligned_db.apply(q).unstack().reset_index()
    g.insert(0, "population", name)
    g["n_images"] = x.groupby(["axis", "level"]).size().values
    snr_tab.append(g)
snr_tab = pd.concat(snr_tab, ignore_index=True).round(2)
snr_tab["axis"] = pd.Categorical(snr_tab.axis, ["clean"] + AXES, ordered=True)
snr_tab = snr_tab.sort_values(["population", "axis", "level"]).reset_index(drop=True)
snr_tab.to_csv(f"{OUT}/sectionA_snr_by_axis_level.csv", index=False)

clean_snr = n100[n100.axis == "clean"].snr_aligned_db.dropna()
clean_summary = dict(n=int(len(clean_snr)), median=clean_snr.median(), q10=clean_snr.quantile(.10), q25=clean_snr.quantile(.25),
                     q75=clean_snr.quantile(.75), min=clean_snr.min(), max=clean_snr.max())
THRESH = clean_snr.quantile(.10)

# ------------------------------------------------------------- 2. SNR vs heart-rate error
x = n100[n100.snr_aligned_db.notna() & n100.dig_hr.notna()].copy()


def boot_rho(df, col, B=2000):
    recs = df.record.unique()
    idx = {r: df.index[df.record == r].to_numpy() for r in recs}
    vals = []
    for _ in range(B):
        pick = rng.choice(recs, len(recs), replace=True)
        ii = np.concatenate([idx[r] for r in pick])
        vals.append(spearmanr(df.loc[ii, "snr_aligned_db"], df.loc[ii, col])[0])
    return np.nanpercentile(vals, [2.5, 97.5])


def auc_low_snr_predicts_wrong(df, B=2000):
    from scipy.stats import rankdata

    def auc(s):
        pos, neg = s[s.wrong5].snr_aligned_db, s[~s.wrong5].snr_aligned_db
        if len(pos) == 0 or len(neg) == 0:
            return np.nan
        r = rankdata(np.r_[pos, neg])
        u = r[: len(pos)].sum() - len(pos) * (len(pos) + 1) / 2
        return 1 - u / (len(pos) * len(neg))      # P(random wrong page has LOWER snr than a random right page)
    recs = df.record.unique()
    idx = {r: df.index[df.record == r].to_numpy() for r in recs}
    vals = []
    for _ in range(B):
        pick = rng.choice(recs, len(recs), replace=True)
        vals.append(auc(df.loc[np.concatenate([idx[r] for r in pick])]))
    return auc(df), np.nanpercentile(vals, [2.5, 97.5])


rows = []
for name, sub in [("all 13 versions", x)] + [(a, x[x.axis.isin(["clean", a])]) for a in AXES]:
    rho, p = spearmanr(sub.snr_aligned_db, sub.diff_bpm)
    lo, hi = boot_rho(sub, "diff_bpm", 1000)
    rho2, _ = spearmanr(sub.snr_aligned_db, sub.wrong5.astype(int))
    auc, (alo, ahi) = auc_low_snr_predicts_wrong(sub, 1000)
    rows.append(dict(subset=name, n=len(sub), n_wrong5=int(sub.wrong5.sum()), spearman_snr_vs_abs_error=round(rho, 3),
                     boot95=f"{lo:.2f} to {hi:.2f}", spearman_snr_vs_wrong5=round(rho2, 3),
                     auc_low_snr_flags_wrong=round(auc, 3), auc_boot95=f"{alo:.2f} to {ahi:.2f}"))
corr = pd.DataFrame(rows)
corr.to_csv(f"{OUT}/sectionA_snr_vs_error.csv", index=False)

# ------------------------------------------------------------- 3. acceptable SNR but wrong heart rate
acc_wrong = x[(x.snr_aligned_db >= THRESH) & x.wrong5]
low_right = x[(x.snr_aligned_db < THRESH) & ~x.wrong5]
cross = pd.crosstab(x.snr_aligned_db >= THRESH, x.wrong5).rename(index={True: "SNR acceptable", False: "SNR low"},
                                                                  columns={True: "HR wrong >5", False: "HR right"})
acc_wrong.sort_values(["axis", "level"])[["record", "axis", "level", "snr_aligned_db", "gt_hr", "dig_hr", "diff_bpm"]].round(2) \
    .to_csv(f"{OUT}/sectionA_acceptable_snr_but_wrong.csv", index=False)
by_ax_acc = acc_wrong.groupby(["axis", "level"]).size().rename("n").reset_index()
rec_counts = acc_wrong.record.value_counts()

# ------------------------------------------------------------- 4. paired test vs own clean + Bland-Altman (heart rate; all 150, shared versions)
def paired(pop, name):
    out, ba = [], []
    cl = pop[pop.axis == "clean"].set_index("record")
    for ax in AXES:
        for lv in (3, 5):
            g = pop[(pop.axis == ax) & (pop.level == lv)].set_index("record")
            j = g.join(cl[["diff_bpm", "signed"]], rsuffix="_clean", how="inner")
            j = j[j.diff_bpm.notna() & j.diff_bpm_clean.notna()]
            dd = j.diff_bpm - j.diff_bpm_clean
            nz = dd[dd != 0]
            if len(nz) >= 1:
                stat, p = wilcoxon(nz)
            else:
                p = 1.0
            out.append(dict(population=name, axis=ax, level=lv, n_pairs=len(j), n_nonzero=len(nz),
                            median_abs_err_damaged=round(j.diff_bpm.median(), 2), median_abs_err_clean=round(j.diff_bpm_clean.median(), 2),
                            median_paired_change_bpm=round(dd.median(), 2), mean_paired_change_bpm=round(dd.mean(), 2), p_wilcoxon=p))
            s = g.signed.dropna()
            ba.append(dict(population=name, axis=ax, level=lv, n=len(s), bias_bpm=round(s.mean(), 2), sd_bpm=round(s.std(), 2),
                           loa_low=round(s.mean() - 1.96 * s.std(), 1), loa_high=round(s.mean() + 1.96 * s.std(), 1)))
    s = cl.signed.dropna()
    ba.append(dict(population=name, axis="clean", level=0, n=len(s), bias_bpm=round(s.mean(), 2), sd_bpm=round(s.std(), 2),
                   loa_low=round(s.mean() - 1.96 * s.std(), 1), loa_high=round(s.mean() + 1.96 * s.std(), 1)))
    o = pd.DataFrame(out)
    m = len(o)
    order = o.p_wilcoxon.sort_values().index
    run = 0.0
    for i, ix in enumerate(order):
        run = max(run, min(1.0, (m - i) * o.loc[ix, "p_wilcoxon"]))
        o.loc[ix, "p_holm"] = run
    return o, pd.DataFrame(ba)


pw, bas = [], []
for name, pop in (("new100", d[(d.set == "new100") & d.level.isin(SHARED)]), ("all150", all150)):
    o, a = paired(pop, name)
    pw.append(o)
    bas.append(a)
pw = pd.concat(pw, ignore_index=True)
bas = pd.concat(bas, ignore_index=True)
pw["p_wilcoxon"] = pw.p_wilcoxon.map(lambda z: float(f"{z:.2g}"))
pw["p_holm"] = pw.p_holm.map(lambda z: float(f"{z:.2g}"))
pw.to_csv(f"{OUT}/sectionA_paired_vs_clean.csv", index=False)
bas.to_csv(f"{OUT}/sectionA_bland_altman.csv", index=False)

# ------------------------------------------------------------- report
def md_table(t):
    t = t.copy()
    head = "| " + " | ".join(map(str, t.columns)) + " |\n|" + "---|" * len(t.columns) + "\n"
    return head + "\n".join("| " + " | ".join("" if (isinstance(z, float) and np.isnan(z)) else str(z) for z in r) + " |"
                            for r in t.itertuples(index=False))


L = ["# Section A results: signal quality (aligned SNR) and paired heart-rate error\n",
     "*Generated by `scripts/analysis/section_A.py`. All exploratory (MASTER_PLAN section 4): no pass or fail here.*\n",
     "## Limits to read first\n",
     "- A valid aligned SNR exists only for the **new 100** recordings (and 12 first-50 recordings from the bridge run). The saved `snr_db` of the first 50 is invalid and is not used.",
     "- SNR is computed only when the digitiser gave an output, and only on lead II.",
     "- In-distribution: the digitiser was trained on pages from the same generator family, so these numbers describe this setup, not real-world photos.",
     "- Arm C check (2026-11-05): most SNR loss on real captures was local timing wobble of the traced signal (+5 to +7 dB when each 2 s window was shifted separately), not noise. SNR therefore mixes noise and timing distortion.",
     f"- Excluded as unreliable: {', '.join(sorted(UNREL))}.\n",
     "## 1. SNR by damage type and level (dB; median, quartiles)\n",
     md_table(snr_tab[snr_tab.population == "new100"].drop(columns="population")) + "\n",
     f"Clean pages (new 100): median {clean_summary['median']:.1f} dB, middle half {clean_summary['q25']:.1f} to {clean_summary['q75']:.1f}, "
     f"10th percentile {clean_summary['q10']:.1f}, range {clean_summary['min']:.1f} to {clean_summary['max']:.1f} (n = {clean_summary['n']}).\n",
     "Small check on 12 first-50 recordings (same 13 versions, bridge run):\n",
     md_table(snr_tab[snr_tab.population == "bridge12"].drop(columns="population")) + "\n",
     "## 2. Does a low SNR go with a wrong heart rate? (new 100, images with output)\n",
     "Spearman correlation between SNR and absolute heart-rate error (negative = lower SNR, larger error), with a recording-level bootstrap interval. "
     "AUC = chance that a wrong page has a lower SNR than a right page (0.5 = no information).\n",
     md_table(corr) + "\n",
     f"## 3. Acceptable SNR but wrong heart rate (acceptable = at or above the clean-page 10th percentile, {THRESH:.1f} dB)\n",
     md_table(cross.reset_index().rename(columns={"snr_aligned_db": "group"})) + "\n",
     f"Wrong heart rate despite an acceptable SNR: {len(acc_wrong)} images from {acc_wrong.record.nunique()} recordings "
     f"(full list: `sectionA_acceptable_snr_but_wrong.csv`). By damage type and level:\n",
     md_table(by_ax_acc) + "\n",
     "Recordings that appear most often: " + ", ".join(f"{k} ({n})" for k, n in rec_counts.head(6).items()) + ".\n",
     "## 4. Paired test: heart-rate error of each damaged page against the same recording's clean page\n",
     "Wilcoxon signed-rank on |error|, two-sided, Holm over 12 comparisons per population. 'median change' = median of (damaged error - clean error).\n",
     md_table(pw[pw.population == "all150"].drop(columns="population")) + "\n",
     "Same test on the new 100 alone: `sectionA_paired_vs_clean.csv`.\n",
     "## 5. Bland-Altman: bias and limits of agreement of the digitised heart rate (digitised minus reference, bpm; all 150, images with output)\n",
     md_table(bas[bas.population == "all150"].drop(columns="population")) + "\n"]
open(f"{OUT}/SECTION_A.md", "w", encoding="utf-8").write("\n".join(L))

pd.set_option("display.width", 250)
print("\nSNR new100:\n", snr_tab[snr_tab.population == "new100"].drop(columns="population").to_string(index=False))
print("\nclean:", {k: round(float(v_), 2) for k, v_ in clean_summary.items()}, "thresh", round(THRESH, 2))
print("\ncorr:\n", corr.to_string(index=False))
print("\ncross:\n", cross)
print("\nacc-wrong by axis/level:\n", by_ax_acc.to_string(index=False), "\nrecords:", rec_counts.head(8).to_dict())
print("\npaired all150:\n", pw[pw.population == "all150"].to_string(index=False))
print("\nBA all150:\n", bas[bas.population == "all150"].to_string(index=False))
