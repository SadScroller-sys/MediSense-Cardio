"""Section RC: risk-coverage curves from EXISTING predictions (2026-11-14, exploratory, descriptive).
Rules were logged BEFORE this script ran: docs/plan/analysis_plan_changes.md, "Section RC". Nothing is fitted or retrained; saved scores and labels are read.
Coverage = share of images that are answered (the riskiest ones are not answered). Selective risk = share of bad readings among the answered images.
Usage: python -I scripts/analysis/section_RC_risk_coverage.py   -> results/analysis/SECTION_RC.md, sectionRC_*.csv, sectionRC_risk_coverage.png
"""
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
R = os.path.join(ROOT, "results") + os.sep
A = os.path.join(ROOT, "results", "analysis") + os.sep
B_RESAMPLES = 2000
SEED = 52
TABLE_COV = np.array([0.70, 0.80, 0.90, 1.00])
PLOT_COV = np.round(np.arange(0.30, 1.0001, 0.01), 2)
AURC_COV = np.round(np.arange(0.05, 1.0001, 0.01), 2)

# ---------------------------------------------------------------- data (saved files only)
comp = pd.read_csv(A + "sectionP_competition_lights_labels.csv")
comp["bad"] = comp["wrong_or_none"].astype(bool)
ph = pd.read_csv(A + "sectionH_photo_scores_scored.csv")[["variant_id", "p_bad"]]
compB = comp.merge(ph, on="variant_id", how="inner")
own = pd.read_csv(A + "sectionP_own_lights_labels.csv")
own_ph = pd.read_csv(A + "sectionO_ownphotos_scored.csv")[["variant_id", "p_bad"]]
own = own.drop(columns=[c for c in ("p_bad",) if c in own.columns]).merge(own_ph, on="variant_id", how="inner")
own["bad"] = own["bad"].astype(bool)
own["group"] = own["page"]
comp["group"] = comp["record"]
compB["group"] = compB["record"]

DATASETS = {
    "A": dict(name="Competition real captures (1,260 images, 140 recordings)", df=comp, scores={"Traffic light": "score"}),
    "B": dict(name="Arm C+ subset (900 images, 100 recordings)", df=compB, scores={"Traffic light": "score", "Photo detector": "p_bad"}),
    "C": dict(name="Own phone set 1 (60 photos, 30 pages)", df=own, scores={"Traffic light": "score", "Photo detector": "p_bad"}),
}


# ---- Amendment 1 (logged before the run): the 40 confirmation photos (Section Q2) and the 120 simulated photos (Section Z); traffic-light scores recomputed by the
# frozen tool from the saved digitised signals, and checked against the saved lights.
sys.path.insert(0, os.path.join(ROOT, "safeguard"))
import ecg_traffic_light as TL  # noqa: E402

CHECK = []


def recompute(df, path_of, tag):
    sc, li = [], []
    for _, r in df.iterrows():
        f = path_of(r)
        if os.path.exists(f):
            z = np.load(f)
            c = TL.check({k: z[k].astype(float) for k in z.files})
        else:
            c = TL.check({})
        sc.append(c["score"])
        li.append(c["light"])
    out = df.copy()
    out["score"], out["light_recomputed"] = sc, li
    mism = int((out["light"] != out["light_recomputed"]).sum())
    CHECK.append(dict(set=tag, images=len(out), light_mismatches=mism))
    print(f"CHECK {tag}: {len(out)} images, recomputed light differs from the saved light on {mism}", flush=True)
    return out


q2 = pd.read_csv(A + "sectionQ2_all_variants.csv")
q2["bad"] = q2["bad"].astype(bool)
q2["group"] = q2["page"]
qdir = R + "ownphotos2/confirm_out/confirm_digitized_12lead/"
q0 = recompute(q2[q2.variant == "V0_original"].reset_index(drop=True), lambda r: qdir + f"{r.photo}__V0_original.npz", "D0 photos as taken")
qs = recompute(q2[q2.variant == "V2_straighten"].reset_index(drop=True), lambda r: qdir + f"{r.photo}__V2_straighten.npz", "D2 straightened")
zz = pd.read_csv(A + "sectionZ_all.csv")
zz["bad"] = zz["bad"].astype(bool)
zz["group"] = zz["page"]
z0 = recompute(zz[zz.variant == "v0"].reset_index(drop=True), lambda r: R + f"fresh_sim/dig_v0/{r.photo}.npz", "E0 simulated as made")
zs = recompute(zz[zz.variant == "v2"].reset_index(drop=True), lambda r: R + f"fresh_sim/dig_v2/{r.photo}.npz", "E2 simulated straightened")
pd.DataFrame(CHECK).to_csv(A + "sectionRC_light_recompute_check.csv", index=False)
DATASETS["D0"] = dict(name="Confirmation photos as taken (40 photos, 20 pages)", df=q0, scores={"Traffic light": "score"})
DATASETS["D2"] = dict(name="Confirmation photos straightened (40 photos, 20 pages)", df=qs, scores={"Traffic light": "score"})
DATASETS["E0"] = dict(name="Simulated photos as made (120 photos, 60 pages)", df=z0, scores={"Traffic light": "score"})
DATASETS["E2"] = dict(name="Simulated photos straightened (120 photos, 60 pages)", df=zs, scores={"Traffic light": "score"})


def risk_at(score, bad, jit, cov):
    """selective risk at each coverage in cov: lowest-risk share kept (ties by fixed jitter)."""
    order = np.lexsort((jit, score))
    b = bad[order].astype(float)
    cum = np.cumsum(b)
    n = len(b)
    k = np.clip(np.ceil(np.asarray(cov) * n - 1e-9).astype(int), 1, n)
    return cum[k - 1] / k


def oracle_at(bad, cov):
    n = len(bad)
    ngood = int((~bad).sum())
    k = np.clip(np.ceil(np.asarray(cov) * n - 1e-9).astype(int), 1, n)
    return np.maximum(0, k - ngood) / k


def bootstrap(df, col, cov_all):
    """cluster bootstrap (recordings or pages): returns array (B, len(cov_all)) of selective risk."""
    rng = np.random.RandomState(SEED)
    groups = df["group"].to_numpy()
    uniq = pd.unique(groups)
    idx_by = {g: np.where(groups == g)[0] for g in uniq}
    s = df[col].to_numpy(float)
    bad = df["bad"].to_numpy(bool)
    jit = np.random.RandomState(SEED).rand(len(df))
    out = np.empty((B_RESAMPLES, len(cov_all)))
    for i in range(B_RESAMPLES):
        pick = rng.choice(len(uniq), len(uniq), replace=True)
        ix = np.concatenate([idx_by[uniq[j]] for j in pick])
        out[i] = risk_at(s[ix], bad[ix], jit[ix], cov_all)
    return out


COV_ALL = np.unique(np.concatenate([PLOT_COV, AURC_COV, TABLE_COV]))
pos = {round(c, 2): i for i, c in enumerate(COV_ALL)}
tab_rows, aurc_rows, op_rows, curves = [], [], [], {}
aurc_idx = [pos[round(c, 2)] for c in AURC_COV]
for key, ds in DATASETS.items():
    df = ds["df"].reset_index(drop=True)
    bad = df["bad"].to_numpy(bool)
    jit = np.random.RandomState(SEED).rand(len(df))
    overall = bad.mean()
    orc = oracle_at(bad, COV_ALL)
    curves[(key, "oracle")] = orc
    curves[(key, "random")] = np.full(len(COV_ALL), overall)
    for sname, col in ds["scores"].items():
        pt = risk_at(df[col].to_numpy(float), bad, jit, COV_ALL)
        bs = bootstrap(df, col, COV_ALL)
        lo, hi = np.percentile(bs, [2.5, 97.5], axis=0)
        curves[(key, sname)] = (pt, lo, hi)
        for c in TABLE_COV:
            i = pos[round(c, 2)]
            k = int(np.ceil(c * len(df) - 1e-9))
            tab_rows.append(dict(dataset=key, score=sname, coverage=c, images_answered=k, selective_risk_pct=round(100 * pt[i], 2), lo95_pct=round(100 * lo[i], 2),
                                 hi95_pct=round(100 * hi[i], 2), random_pct=round(100 * overall, 2), oracle_pct=round(100 * orc[i], 2)))
        a_pt = pt[aurc_idx].mean()
        a_bs = bs[:, aurc_idx].mean(axis=1)
        aurc_rows.append(dict(dataset=key, score=sname, aurc_pct=round(100 * a_pt, 2), lo95_pct=round(100 * np.percentile(a_bs, 2.5), 2),
                              hi95_pct=round(100 * np.percentile(a_bs, 97.5), 2), random_pct=round(100 * overall, 2),
                              oracle_aurc_pct=round(100 * orc[aurc_idx].mean(), 2), images=len(df), bad_images=int(bad.sum())))
    # operating points of the traffic light (A, B, C all carry the light)
    for label, keep in (("GREEN only", ["GREEN"]), ("GREEN + AMBER", ["GREEN", "AMBER"])):
        m = df["light"].isin(keep).to_numpy()
        op_rows.append(dict(dataset=key, answered=label, coverage_pct=round(100 * m.mean(), 1), images_answered=int(m.sum()),
                            bad_among_answered=int(bad[m].sum()), selective_risk_pct=round(100 * bad[m].mean(), 2) if m.any() else float("nan"),
                            random_pct=round(100 * overall, 2)))

pd.DataFrame(tab_rows).to_csv(A + "sectionRC_table.csv", index=False)
pd.DataFrame(aurc_rows).to_csv(A + "sectionRC_aurc.csv", index=False)
pd.DataFrame(op_rows).to_csv(A + "sectionRC_operating_points.csv", index=False)

op_df = pd.DataFrame(op_rows)

# ---------------------------------------------------------------- figure (validated default palette, slots 1 and 2, light mode)
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e6e5e1"
BLUE, ORANGE = "#2a78d6", "#eb6834"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2, "text.color": INK})
fig, axes = plt.subplots(2, 3, figsize=(13.5, 8.6))
x = 100 * PLOT_COV
sel = [pos[round(c, 2)] for c in PLOT_COV]


def decorate(ax, title, ymax):
    ax.set_title(title, fontsize=9.5, loc="left", color=INK)
    ax.set_xlabel("Coverage: share of images answered (%)")
    ax.set_xlim(30, 100.5)
    ax.set_ylim(0, ymax)
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, fontsize=8, loc="upper left", ncol=2 if ymax == 75 else 1)


def op_markers(ax, df, colr, label_text):
    for label, keep, mk in (("GREEN only", ["GREEN"], "o"), ("GREEN + AMBER", ["GREEN", "AMBER"], "s")):
        m = df["light"].isin(keep)
        ax.plot([100 * m.mean()], [100 * df["bad"][m].mean()], mk, ms=8, mfc=colr, mec="white", mew=2, zorder=5)
        if label_text:
            ax.annotate(label, (100 * m.mean(), 100 * df["bad"][m].mean()), textcoords="offset points", xytext=(0, 10), ha="center", fontsize=8, color=INK2)


for ax, key in zip(axes[0], ("A", "B", "C")):
    ds = DATASETS[key]
    df = ds["df"]
    overall = df["bad"].mean()
    ax.axhline(100 * overall, color="#8a8984", lw=1.2, ls=(0, (4, 3)), label="Random order")
    ax.plot(x, 100 * curves[(key, "oracle")][sel], color=INK2, lw=1.2, ls=":", label="Perfect order (oracle)")
    for sname, colr in (("Traffic light", BLUE), ("Photo detector", ORANGE)):
        if (key, sname) not in curves:
            continue
        pt, lo, hi = curves[(key, sname)]
        ax.fill_between(x, 100 * lo[sel], 100 * hi[sel], color=colr, alpha=0.14, lw=0)
        ax.plot(x, 100 * pt[sel], color=colr, lw=2, label=sname)
    op_markers(ax, df, BLUE, True)
    decorate(ax, f"{key}. {ds['name']}", 75 if key == "C" else max(100 * overall * 1.5, 100 * curves[(key, 'Traffic light')][2][sel].max() * 1.15, 4))
for ax, (letter, k0, k2, nm) in zip(axes[1][:2], (("D", "D0", "D2", "D. Traffic light, 40 new phone photos"), ("E", "E0", "E2", "E. Traffic light, 120 simulated photos"))):
    ymax = 0
    for key, colr, lab in ((k0, ORANGE, "Photos as taken"), (k2, BLUE, "Straightened photos")):
        df = DATASETS[key]["df"]
        pt, lo, hi = curves[(key, "Traffic light")]
        ax.axhline(100 * df["bad"].mean(), color=colr, lw=1.0, ls=(0, (4, 3)), alpha=0.55)
        ax.fill_between(x, 100 * lo[sel], 100 * hi[sel], color=colr, alpha=0.14, lw=0)
        ax.plot(x, 100 * pt[sel], color=colr, lw=2, label=lab)
        op_markers(ax, df, colr, False)
        ymax = max(ymax, 100 * df["bad"].mean() * 1.25, 100 * hi[sel].max() * 1.05)
    ax.plot([], [], color="#8a8984", lw=1.0, ls=(0, (4, 3)), label="Random order (dashed)")
    decorate(ax, nm.split(". ", 1)[1] and nm, min(ymax, 100) + 12)
axes[0][0].set_ylabel("Bad readings among answered images (%)")
axes[1][0].set_ylabel("Bad readings among answered images (%)")
# sixth panel: operating points as a table
axt = axes[1][2]
axt.axis("off")
NAMES = {"A": "A competition", "B": "B Arm C+", "C": "C own phone 1", "D0": "D as taken", "D2": "D straightened",
         "E0": "E sim. as made", "E2": "E sim. straightened"}
lines = ["Answer only GREEN, or GREEN + AMBER:", "share answered, bad / answered", ""]
lines.append(f"{'set':<17}{'GREEN only':<15}{'+ AMBER':<15}")
for key, nm in NAMES.items():
    g = op_df[(op_df.dataset == key) & (op_df.answered == "GREEN only")].iloc[0]
    ga = op_df[(op_df.dataset == key) & (op_df.answered == "GREEN + AMBER")].iloc[0]
    lines.append(f"{nm:<17}{g.coverage_pct:>3.0f}% {int(g.bad_among_answered)}/{int(g.images_answered):<7}{ga.coverage_pct:>3.0f}% {int(ga.bad_among_answered)}/{int(ga.images_answered):<5}")
axt.text(0, 1, "\n".join(lines), va="top", ha="left", family="monospace", fontsize=8, color=INK2, linespacing=1.6, transform=axt.transAxes)
fig.suptitle("Risk-coverage: what is left wrong when the riskiest images are not answered (saved scores, nothing refitted)", x=0.01, ha="left", fontsize=10.5, color=INK)
fig.tight_layout(rect=(0, 0, 1, 0.96))
fig.savefig(A + "sectionRC_risk_coverage.png", dpi=170, facecolor="white")
os.makedirs(os.path.join(ROOT, "docs", "reports", "figures"), exist_ok=True)
fig.savefig(os.path.join(ROOT, "docs", "reports", "figures", "fig4_rc_risk_coverage.png"), dpi=170, facecolor="white")

# ---------------------------------------------------------------- report
T = pd.DataFrame(tab_rows)
U = pd.DataFrame(aurc_rows)
O = pd.DataFrame(op_rows)
md = ["# Section RC: risk-coverage curves from existing predictions (exploratory, descriptive)",
      "Rules: `docs/plan/analysis_plan_changes.md`, 'Section RC' (logged before this script ran) and its Amendment 1 (sets D and E added after the first run, same method; the traffic-light scores of D and E were recomputed by the frozen tool from the saved digitised signals, and the recomputed light equals the saved light on all 320 images, `sectionRC_light_recompute_check.csv`). Nothing was fitted or retrained. Bad = wrong heart rate (more than 5 bpm, cleaned measure) or no output; for the own-phone set, no usable HR or wrong. "
      "Intervals: bootstrap over recordings (A, B) or pages (C), 2,000 resamples, ranking recomputed inside each resample. No guarantee of any kind.",
      "", "Figure: `results/analysis/sectionRC_risk_coverage.png` (also `docs/reports/figures/fig4_rc_risk_coverage.png`).", ""]
for key, ds in DATASETS.items():
    n = len(ds["df"])
    nb = int(ds["df"]["bad"].sum())
    md += [f"## {key}. {ds['name']}: {nb} bad of {n} ({100 * nb / n:.1f}%)", "",
           "| Score | Coverage | Images answered | Bad among answered % (95% interval) | Random % | Oracle % |", "|---|---|---|---|---|---|"]
    for _, r in T[T.dataset == key].iterrows():
        md.append(f"| {r.score} | {int(round(100 * r.coverage))}% | {int(r.images_answered)} | {r.selective_risk_pct:.2f} ({r.lo95_pct:.2f} to {r.hi95_pct:.2f}) | {r.random_pct:.2f} | {r.oracle_pct:.2f} |")
    md += ["", "| Score | AURC % (95% interval) | Random % | Oracle % |", "|---|---|---|---|"]
    for _, r in U[U.dataset == key].iterrows():
        md.append(f"| {r.score} | {r.aurc_pct:.2f} ({r.lo95_pct:.2f} to {r.hi95_pct:.2f}) | {r.random_pct:.2f} | {r.oracle_aurc_pct:.2f} |")
    md += ["", "Traffic-light operating points:", "", "| Answered | Coverage | Images | Bad among answered | Selective risk % | Random % |", "|---|---|---|---|---|---|"]
    for _, r in O[O.dataset == key].iterrows():
        md.append(f"| {r.answered} | {r.coverage_pct}% | {int(r.images_answered)} | {int(r.bad_among_answered)} | {r.selective_risk_pct:.2f} | {r.random_pct:.2f} |")
    md.append("")
md += ["AURC = mean selective risk over coverage 0.05 to 1.00 (smaller is better). Random order gives the overall bad rate at every coverage; the oracle answers all good images first.",
       "Limits: real captures of one source set and one phone; (B) and (C) hold fewer than 100 bad readings, so they are descriptive; the images are not exchangeable calibration data, so no coverage or risk guarantee is claimed; "
       "the photo detector was trained on simulated damage with the original-measure labels and is scored here against the cleaned labels, the same as the traffic light."]
open(A + "SECTION_RC.md", "w", encoding="utf-8").write("\n".join(md) + "\n")
print("\n".join(md))
