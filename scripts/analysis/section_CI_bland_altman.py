"""Section CI: Bland-Altman pictures and cluster-bootstrap intervals from EXISTING per-image files (2026-11-14, exploratory, descriptive).
Rules logged BEFORE this script ran: docs/plan/analysis_plan_changes.md, "Section CI". Nothing is refitted.
Usage: python -I scripts/analysis/section_CI_bland_altman.py -> results/analysis/SECTION_CI.md, sectionCI_*.csv, sectionCI_bland_altman.png
"""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
R = os.path.join(ROOT, "results") + os.sep
A = R + "analysis" + os.sep
B = 2000
rng = np.random.RandomState(53)


def wrap(d):
    return (np.asarray(d, float) + 180.0) % 360.0 - 180.0


def cluster_ci(df, group, stat, n_out):
    """cluster bootstrap of stat(df) -> array of n_out numbers; returns (point, lo, hi) arrays."""
    rng = np.random.RandomState(53)          # own stream per interval: the numbers do not depend on the order of the calls
    pt = np.asarray(stat(df), float)
    g = df[group].to_numpy()
    uniq = pd.unique(g)
    idx = {u: np.where(g == u)[0] for u in uniq}
    out = np.empty((B, n_out))
    for i in range(B):
        pick = rng.choice(len(uniq), len(uniq), replace=True)
        ix = np.concatenate([idx[uniq[j]] for j in pick])
        out[i] = stat(df.iloc[ix])
    lo, hi = np.nanpercentile(out, [2.5, 97.5], axis=0)
    return pt, lo, hi


def ba_stat(col):
    def f(d):
        x = d[col].to_numpy(float)
        x = x[np.isfinite(x)]
        m, s = x.mean(), x.std(ddof=1)
        return [m, m - 1.96 * s, m + 1.96 * s, np.median(np.abs(x)), len(x)]
    return f


ROWS = []


def add(measure, cond, n_clusters, names, pt, lo, hi, fmt="{:.2f}"):
    for nm, a, b, c in zip(names, pt, lo, hi):
        ROWS.append(dict(measure=measure, condition=cond, clusters=n_clusters, statistic=nm, value=round(float(a), 3), lo95=round(float(b), 3), hi95=round(float(c), 3)))


# ---------------------------------------------------------------- simulated heart rate (Section A basis: diff_bpm = digitised - reference, original measure)
v2 = pd.read_csv(R + "v2_intervals/results_v2.csv")
ex = pd.read_csv(R + "extension/results_extension.csv")
v2 = v2[v2.record != "15192_lr"]
ex = ex[ex.record != "21205_lr"]
sim = pd.concat([v2, ex], ignore_index=True)
sim["mean_hr"] = (sim.dig_hr + sim.gt_hr) / 2
sim["signed"] = sim.dig_hr - sim.gt_hr          # signed error, as in Section A (the saved diff_bpm is the absolute difference)
HR = {}
for name, ax_, lv in (("clean page", "clean", 0), ("resolution level 5", "resolution", 5), ("blur level 5", "blur", 5)):
    d = sim[(sim.axis == ax_) & (sim.level == lv) & sim.dig_hr.notna()].copy()
    HR[name] = d
    pt, lo, hi = cluster_ci(d, "record", ba_stat("signed"), 5)
    add("Heart rate (bpm), simulated, all 150 minus 2 unreliable", name, d.record.nunique(), ["bias", "lower limit", "upper limit", "median abs error", "n images"], pt, lo, hi)
chk = HR["clean page"].signed
print("CHECK clean page: bias %.2f, limits %.1f to %.1f (frozen: -0.03, -3.2 to +3.1), n=%d" % (chk.mean(), chk.mean() - 1.96 * chk.std(ddof=1), chk.mean() + 1.96 * chk.std(ddof=1), len(chk)))

# ---- cleaned measure (as in FINAL_NUMBERS 'wrong'), new 100 only (Section K): amendment 1, added after the first run so that both measures are shown
kk = pd.read_csv(A + "sectionK_remeasured_sim.csv")
kk = kk[kk.record != "21205_lr"].copy()
kk["signed"] = kk.dig_hr_clean - kk.gt_hr_clean
for name, ax_, lv in (("clean page", "clean", 0), ("resolution level 5", "resolution", 5), ("blur level 5", "blur", 5)):
    d = kk[(kk.axis == ax_) & (kk.level == lv) & kk.dig_hr_clean.notna()].copy()
    pt, lo, hi = cluster_ci(d, "record", ba_stat("signed"), 5)
    add("Heart rate (bpm), CLEANED measure, new 100 only", name, d.record.nunique(), ["bias", "lower limit", "upper limit", "median abs error", "n images"], pt, lo, hi)

# ---------------------------------------------------------------- PR against 12SL
pt_ = pd.read_csv(A + "sectionU_test_per_image.csv")
pr_pages = pt_[(pt_.axis == "clean") & pt_.pr_dig.notna() & pt_.ref_pr.notna()].copy()
pr_pages["diff"] = pr_pages.pr_dig - pr_pages.ref_pr
pr_pages["mean"] = (pr_pages.pr_dig + pr_pages.ref_pr) / 2
pc = pd.read_csv(A + "sectionU_confirm_per_photo.csv")
pr_ph = pc[(pc.version == "V2") & pc.pr.notna() & pc.ref_pr.notna()].copy()
pr_ph["diff"] = pr_ph.pr - pr_ph.ref_pr
pr_ph["mean"] = (pr_ph.pr + pr_ph.ref_pr) / 2


def pr_stat(d):
    x = d["diff"].to_numpy(float)
    m, s = x.mean(), x.std(ddof=1)
    return [m, m - 1.96 * s, m + 1.96 * s, np.median(np.abs(x)), 100 * np.mean(np.abs(x) <= 40), len(x), np.percentile(x, 2.5), np.percentile(x, 97.5)]


PRN = ["bias (ms)", "lower limit (ms)", "upper limit (ms)", "median abs error (ms)", "within 40 ms (%)", "n", "2.5th percentile of the differences (ms)", "97.5th percentile of the differences (ms)"]
for nm, d, g in (("digitised clean pages, held-out new 100", pr_pages, "record"), ("straightened phone photos (100 photos)", pr_ph, "page")):
    pt, lo, hi = cluster_ci(d, g, pr_stat, 8)
    add("PR interval vs 12SL", nm, d[g].nunique(), PRN, pt, lo, hi)

# ---------------------------------------------------------------- axis against 12SL (circular difference)
aw = pd.read_csv(A + "sectionW_test_per_page.csv")
ax_pages = aw[aw.axis_dig.notna() & aw.ref.notna()].copy()
ax_pages["diff"] = wrap(ax_pages.axis_dig - ax_pages.ref)
ac = pd.read_csv(A + "sectionW_confirm_per_photo.csv")
ax_ph = ac[(ac.version == "V2") & ac.axis.notna() & ac.ref.notna()].copy()
ax_ph["diff"] = wrap(ax_ph.axis - ax_ph.ref)


def ax_stat(d):
    x = d["diff"].to_numpy(float)
    m, s = x.mean(), x.std(ddof=1)
    return [m, m - 1.96 * s, m + 1.96 * s, np.median(np.abs(x)), 100 * np.mean(np.abs(x) <= 30), len(x), np.percentile(x, 2.5), np.percentile(x, 97.5)]


AXN = ["mean error (deg)", "lower limit (deg)", "upper limit (deg)", "median abs error (deg)", "within 30 deg (%)", "n", "2.5th percentile of the differences (deg)", "97.5th percentile of the differences (deg)"]
ax_pages["grp"] = ax_pages["record"] if "record" in ax_pages else ax_pages["page"]
for nm, d, g in (("100 fresh pages, digitised", ax_pages, "grp"), ("straightened phone photos (100 photos)", ax_ph, "page")):
    pt, lo, hi = cluster_ci(d, g, ax_stat, 8)
    add("Frontal QRS axis vs 12SL", nm, d[g].nunique(), AXN, pt, lo, hi)

# ---------------------------------------------------------------- bad-reading rates with page / recording clusters
q2 = pd.read_csv(A + "sectionQ2_all_variants.csv")
q2 = q2[q2.variant.isin(["V0_original", "V2_straighten"])] if q2.variant.str.startswith("V0_").any() else q2[q2.variant.isin(["V0", "V2"])]
zz = pd.read_csv(A + "sectionZ_all.csv")


def two_variant_stat(v0, v2_):
    def f(d):
        a = d[d.variant == v0]["bad"].astype(float)
        b = d[d.variant == v2_]["bad"].astype(float)
        return [100 * a.mean(), 100 * b.mean(), 100 * (a.mean() - b.mean())]
    return f


print("Q2 variants:", q2.variant.unique(), " Z variants:", zz.variant.unique())
v0q, v2q = sorted(q2.variant.unique())[0], sorted(q2.variant.unique())[-1]
for nm, d, g, v0, v2_ in (("40 confirmation photos (Section Q2)", q2, "page", v0q, v2q), ("120 simulated photos (Section Z)", zz, "page", "V0", "V2")):
    if v0 not in set(d.variant) or v2_ not in set(d.variant):
        vs = sorted(d.variant.unique())
        v0, v2_ = vs[0], vs[-1]
    pt, lo, hi = cluster_ci(d, g, two_variant_stat(v0, v2_), 3)
    add("Bad readings, original vs straightened", nm, d[g].nunique(), ["original bad (%)", "straightened bad (%)", "drop (percentage points)"], pt, lo, hi)

comp = pd.read_csv(A + "sectionP_competition_lights_labels.csv")
cw = comp[~comp["none"].astype(bool)].copy()


def green_stat(d):
    g = d[d.light == "GREEN"]
    a = d[d.light == "AMBER"]
    r = d[d.light == "RED"]
    return [100 * g.wrong.astype(float).mean(), 100 * a.wrong.astype(float).mean(), 100 * r.wrong.astype(float).mean(), 100 * len(g) / len(d)]


pt, lo, hi = cluster_ci(cw, "record", green_stat, 4)
add("Traffic light, competition captures with an output", "wrong heart rate by light", cw.record.nunique(), ["GREEN wrong (%)", "AMBER wrong (%)", "RED wrong (%)", "GREEN share of readings (%)"], pt, lo, hi)

T = pd.DataFrame(ROWS)
T.to_csv(A + "sectionCI_intervals.csv", index=False)

# ---------------------------------------------------------------- figure
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e6e5e1"
BLUE, ORANGE = "#2a78d6", "#eb6834"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2, "text.color": INK})
fig, axs = plt.subplots(2, 3, figsize=(13.5, 8.2))


def ba_panel(ax, series, xlab, ylab, title, ylim=None):
    for lab, x, y, col in series:
        x, y = np.asarray(x, float), np.asarray(y, float)
        ok = np.isfinite(x) & np.isfinite(y)
        x, y = x[ok], y[ok]
        m, s = y.mean(), y.std(ddof=1)
        ax.scatter(x, y, s=14, color=col, alpha=0.55, edgecolors="none", label=f"{lab} (n={len(y)})")
        ax.axhline(m, color=col, lw=1.6)
        for lim in (m - 1.96 * s, m + 1.96 * s):
            ax.axhline(lim, color=col, lw=1.1, ls=(0, (4, 3)))
        ax.text(0.99, 0.02 + 0.075 * (col == ORANGE), f"{lab}: bias {m:+.1f}, limits {m - 1.96 * s:+.1f} to {m + 1.96 * s:+.1f}", transform=ax.transAxes, ha="right", va="bottom", fontsize=7.5, color=INK2)
    ax.axhline(0, color=GRID, lw=0.8, zorder=0)
    ax.set_xlabel(xlab)
    ax.set_ylabel(ylab)
    ax.set_title(title, fontsize=9.5, loc="left", color=INK)
    if ylim:
        ax.set_ylim(*ylim)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, fontsize=7.5, loc="upper left")


for ax, nm, lim in zip(axs[0], ("clean page", "resolution level 5", "blur level 5"), ((-12, 12), (-60, 60), (-45, 45))):
    d = HR[nm]
    ba_panel(ax, [("digitised", d.mean_hr, d.signed, BLUE)], "Mean of digitised and true heart rate (bpm)", "Digitised minus true (bpm)", f"a{['clean page','resolution level 5','blur level 5'].index(nm)+1}. Heart rate, simulated, {nm}", lim)
ba_panel(axs[1][0], [("digitised clean pages", pr_pages["mean"], pr_pages["diff"], BLUE), ("straightened phone photos", pr_ph["mean"], pr_ph["diff"], ORANGE)],
         "Mean of our PR and 12SL PR (ms)", "Ours minus 12SL (ms)", "b. PR interval against 12SL", (-90, 90))
ax_pages["ref_"] = ax_pages.ref
ba_panel(axs[1][1], [("digitised fresh pages", ax_pages.ref, ax_pages["diff"], BLUE), ("straightened phone photos", ax_ph.ref, ax_ph["diff"], ORANGE)],
         "12SL frontal axis (degrees)", "Ours minus 12SL (degrees, wrapped)", "c. Frontal QRS axis against 12SL (x = reference axis)", (-140, 140))
qq = q2.copy()
vs = sorted(qq.variant.unique())
sx = []
for lab, v, col in (("original photos", vs[0], ORANGE), ("straightened photos", vs[-1], BLUE)):
    d = qq[(qq.variant == v) & qq.dig_hr_clean.notna()]
    sx.append((lab, (d.dig_hr_clean + d.gt_hr_clean) / 2, d.dig_hr_clean - d.gt_hr_clean, col))
ba_panel(axs[1][2], sx, "Mean of digitised and true heart rate (bpm)", "Digitised minus true (bpm, cleaned measure)", "d. Heart rate, 40 new phone photos (Section Q2)", (-60, 60))
fig.suptitle("Bland-Altman pictures (solid line = bias, dashed = 95% limits of agreement); saved per-image results, nothing refitted", x=0.01, ha="left", fontsize=10.5, color=INK)
fig.tight_layout(rect=(0, 0, 1, 0.95))
fig.savefig(A + "sectionCI_bland_altman.png", dpi=170, facecolor="white")
os.makedirs(R.replace("results" + os.sep, "") + "docs" + os.sep + "reports" + os.sep + "figures", exist_ok=True)
fig.savefig(os.path.join(ROOT, "docs", "reports", "figures", "fig4_ci_bland_altman.png"), dpi=170, facecolor="white")

# ---------------------------------------------------------------- report
md = ["# Section CI: Bland-Altman pictures and cluster-bootstrap intervals (exploratory, descriptive)",
      "Rules: `docs/plan/analysis_plan_changes.md`, 'Section CI' (logged before this script ran). Intervals: bootstrap over recordings (simulated, competition) or printed pages (phone photos), 2,000 resamples, percentile 95%. Nothing refitted; no pass/fail rule is re-applied.",
      "", "Figure: `results/analysis/sectionCI_bland_altman.png` (also `docs/reports/figures/fig4_ci_bland_altman.png`). Numbers: `sectionCI_intervals.csv`.", ""]
for m, g in T.groupby("measure", sort=False):
    md += [f"## {m}", "", "| Condition | Clusters | Statistic | Value (95% interval) |", "|---|---|---|---|"]
    for _, r in g.iterrows():
        md.append(f"| {r.condition} | {int(r.clusters)} | {r.statistic} | {r.value:.2f} ({r.lo95:.2f} to {r.hi95:.2f}) |")
    md.append("")
pr_rows = T[(T.statistic.str.startswith("within"))]
md += ["## Pre-set rule check with cluster intervals (share within tolerance; rule: at least 90%)", "", "| Measure | Condition | Share within tolerance | Lower end of the 95% interval | Lower end at or above 90%? |", "|---|---|---|---|---|"]
for _, r in pr_rows.iterrows():
    md.append(f"| {r.measure} | {r.condition} | {r.value:.1f}% | {r.lo95:.1f}% | {'yes' if r.lo95 >= 90 else 'NO (point estimate met the rule, the interval reaches below it)'} |")
md.append("")
md += ["Reading notes: the Bland-Altman limits are bias +- 1.96 standard deviations of the differences; their intervals come from resampling whole recordings. The two photos of a page are kept together when pages are resampled. "
       "The axis difference is wrapped to -180..180 degrees; the axis limits are therefore not a Gaussian statement when there are gross failures (P13: 117 to 121 degrees). Heart rate uses the original (not cleaned) measure, as in Section A, "
       "except panel d (cleaned measure, as in Section Q2). PR and axis compare against 12SL, an algorithm."]
open(A + "SECTION_CI.md", "w", encoding="utf-8").write("\n".join(md) + "\n")
print("\n".join(md))
