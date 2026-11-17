"""Section H (EXPLORATORY / REPLICATION; rules fixed in docs/plan/analysis_plan_changes.md, 2026-11-07, "Arm C extension"):
100 more real-capture recordings (900 images: 9 capture types x 100), read on Kaggle with the same digitiser as Arm C (40 recordings, 360 images).

Outcomes (same as MASTER_PLAN / Arm C): no output; wrong HR = output exists and |digitised - reference| > 5 bpm (secondary > 10); bad = either.
Rates: Wilson 95%; recording = unit (one image per recording per capture type). Test vs clean kit page C0: exact paired (McNemar-exact) with Holm over 8 comparisons.
Models trained ONLY on simulated damage, applied once to the real captures:
  photo detector  = five photo scores + logistic regression, trained on first 50 + new 100 simulated (images with output; target wrong5), plus the same for target 'bad'
  output gate (D2) = 15 output features + logistic regression, trained on the new-100 simulated images with output.
Writes results/analysis/sectionH_*.csv and SECTION_H.md.
"""
import os
import sys
import warnings

import numpy as np
import pandas as pd
from scipy.stats import binomtest
from sklearn.metrics import roc_auc_score

warnings.filterwarnings("ignore")
src = open("D:/Capstone Project/scripts/analysis/section_D2.py", encoding="utf-8").read().split("preds = {}")[0]
exec(compile(src, "section_D2_prefix", "exec"))      # d (simulated, photo scores), te, y, OUT_COLS, X_COLS, sig_model, auc_ci
ROOT = "D:/Capstone Project/"
OUT = ROOT + "results/analysis/"
NAMES = {"C0_kit_original": "C0 clean kit page", "C1_print_scan_colour": "C1 print-scan colour", "C2_print_scan_bw": "C2 print-scan black/white",
         "C3_phone_photo_print": "C3 phone photo of print", "C4_phone_photo_screen": "C4 phone photo of screen", "C5_stained_soaked_photo": "C5 stained/soaked",
         "C6_extensive_damage_photo": "C6 extensive damage", "C7_mold_scan_colour": "C7 mould scan colour", "C8_mold_scan_bw": "C8 mould scan b/w"}
AXES_C = list(NAMES)


def wilson(k, n, z=1.96):
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return c - h, c + h


def pct(k, n):
    lo, hi = wilson(k, n)
    return f"{k}/{n} = {100 * k / n:.0f}% ({100 * lo:.0f}-{100 * hi:.0f})"


def holm(ps):
    ps = np.array(ps, float)
    o = np.argsort(ps)
    adj = np.empty_like(ps)
    run = 0
    for rank, i in enumerate(o):
        run = max(run, (len(ps) - rank) * ps[i])
        adj[i] = min(1.0, run)
    return adj


def md_table(t):
    head = "| " + " | ".join(map(str, t.columns)) + " |\n|" + "---|" * len(t.columns) + "\n"
    return head + "\n".join("| " + " | ".join(str(z) for z in r) + " |" for r in t.itertuples(index=False))


# ------------------------------------------------------------------ data
new = pd.read_csv(ROOT + "results/armCext/results_armCext_all.csv")
old = pd.read_csv(ROOT + "results/armC/results_armC.csv")
assert len(new) == 900 and len(old) == 360 and not set(new.record) & set(old.record)
new["set"], old["set"] = "armC_new100", "armC_first40"
cols = ["set", "variant_id", "record", "axis", "gt_hr", "dig_hr", "diff_bpm", "snr_aligned_db"]
allc = pd.concat([old[cols], new[cols]], ignore_index=True)
allc["none"] = allc.dig_hr.isna()
allc["wrong5"] = allc.diff_bpm > 5
allc["wrong10"] = allc.diff_bpm > 10
allc["bad"] = allc.none | allc.wrong5
allc["rec"] = allc.set + "_" + allc.record.astype(str)
POPS = {"new100": allc[allc.set == "armC_new100"], "pooled140": allc}

# ------------------------------------------------------------------ H1 rates per capture type + paired test vs C0
rows, prow = [], []
for pop, g in POPS.items():
    c0 = g[g.axis == "C0_kit_original"].set_index("rec")
    ps_w, ps_b, tmp = [], [], []
    for ax in AXES_C:
        x = g[g.axis == ax].set_index("rec")
        n = len(x)
        rows.append(dict(population=pop, capture=NAMES[ax], recordings=n, no_output=pct(int(x.none.sum()), n), wrong_gt5=pct(int(x.wrong5.sum()), n),
                         wrong_gt10=pct(int(x.wrong10.sum()), n), bad=pct(int(x.bad.sum()), n),
                         median_abs_err_bpm_when_output=round(float(x.diff_bpm.median()), 2), p90_abs_err_bpm_when_output=round(float(x.diff_bpm.quantile(0.9)), 1)))
        if ax == "C0_kit_original":
            continue
        rec = {}
        for nm, col in (("wrong5", "wrong5"), ("bad", "bad")):
            a = x[col].reindex(c0.index).astype(bool).values
            b = c0[col].astype(bool).values
            worse, better = int((a & ~b).sum()), int((~a & b).sum())
            p = binomtest(worse, worse + better, 0.5).pvalue if worse + better else 1.0
            rec[nm] = (worse, better, p)
        tmp.append((ax, rec))
    ph = holm([t[1]["wrong5"][2] for t in tmp])
    pb = holm([t[1]["bad"][2] for t in tmp])
    for i, (ax, rec) in enumerate(tmp):
        prow.append(dict(population=pop, capture=NAMES[ax],
                         wrong5_worse_than_C0=rec["wrong5"][0], wrong5_better=rec["wrong5"][1], wrong5_p_exact=round(rec["wrong5"][2], 4), wrong5_p_holm=round(ph[i], 4),
                         bad_worse_than_C0=rec["bad"][0], bad_better=rec["bad"][1], bad_p_exact=round(rec["bad"][2], 4), bad_p_holm=round(pb[i], 4)))
rates = pd.DataFrame(rows)
paired = pd.DataFrame(prow)

# ------------------------------------------------------------------ H2 events, silent failures, what the wrong clean pages look like
nw = {p: int(g.wrong5.sum()) for p, g in POPS.items()}
nw_real = {p: int(g[g.axis != "C0_kit_original"].wrong5.sum()) for p, g in POPS.items()}
ev = pd.DataFrame([dict(population=p, wrong_readings_all_types=nw[p], wrong_readings_real_captures_C1_to_C8=nw_real[p],
                        rule_100_events="reached" if nw[p] >= 100 else "NOT reached") for p in POPS])
c0w = allc[(allc.axis == "C0_kit_original") & allc.wrong5].copy()
c0w["abs_err_bpm"] = c0w.diff_bpm.round(1)
c0w["ratio_dig_over_ref"] = (c0w.dig_hr / c0w.gt_hr).round(2)
c0_wrong_list = c0w[["set", "record", "gt_hr", "dig_hr", "abs_err_bpm", "ratio_dig_over_ref"]].sort_values("abs_err_bpm", ascending=False)
# of the wrong readings on real captures: how many are 'half' or 'double' (peak counting slips) ?
wr = allc[allc.wrong5 & allc.dig_hr.notna()].copy()
wr["ratio"] = wr.dig_hr / wr.gt_hr
slip = pd.DataFrame([dict(wrong_readings=len(wr), near_double_or_half=int(((wr.ratio.sub(2).abs() < 0.15) | (wr.ratio.sub(0.5).abs() < 0.08)).sum()),
                          error_5_to_10=int((wr.diff_bpm <= 10).sum()), error_over_20=int((wr.diff_bpm > 20).sum()),
                          median_error=round(float(wr.diff_bpm.median()), 1))])

# ------------------------------------------------------------------ H3 output gate (D2) applied once to the real captures
f_new = pd.read_csv(OUT + "sectionH_armCext_features.csv")
f_old = pd.read_csv(OUT + "sectionD2b_armC_features.csv")
fe = pd.concat([f_new, f_old], ignore_index=True)
ac = allc.merge(fe, on="variant_id", how="left")
assert ac[OUT_COLS].notna().any(axis=1).all() and len(ac) == 1260
model = sig_model().fit(te[OUT_COLS], y)             # new-100 simulated, images with output (D2 training set)
ac["p_out"] = np.nan
okm = ac.dig_hr.notna()
ac.loc[okm, "p_out"] = model.predict_proba(ac.loc[okm, OUT_COLS])[:, 1]


def auc_row(mask, label, score="p_out"):
    x = ac[mask & ac.dig_hr.notna()]
    yy = x.wrong5.astype(int).values
    if yy.sum() < 5:
        return dict(subset=label, images=len(x), wrong=int(yy.sum()), auc="too few wrong (<5)")
    a, ci = auc_ci(yy, x[score].values, x.rec.values, B=2000)
    return dict(subset=label, images=len(x), wrong=int(yy.sum()), auc=f"{a:.3f} ({ci[0]:.2f} to {ci[1]:.2f})")


isnew = ac.set == "armC_new100"
real = ac.axis != "C0_kit_original"
arows = [auc_row(isnew, "new 100, all 9 capture types"), auc_row(isnew & real, "new 100, real captures C1-C8"),
         auc_row(ac.set == "armC_first40", "first 40 (already seen in D2b)"), auc_row(ac.set != "x", "pooled 140, all"), auc_row(real, "pooled 140, real captures C1-C8")]
for ax in AXES_C:
    arows.append(auc_row(isnew & (ac.axis == ax), "new 100: " + NAMES[ax]))
aucs_out = pd.DataFrame(arows)

grow = []
for sub, mk in (("new 100, all types", isnew), ("new 100, real C1-C8", isnew & real), ("pooled 140, real C1-C8", real)):
    x = ac[mk & ac.dig_hr.notna()]
    yy = x.wrong5.astype(int).values
    for fr in (0.1, 0.2, 0.3):
        f = x.p_out.values >= np.quantile(x.p_out.values, 1 - fr)
        grow.append(dict(subset=sub, flag_top=f"{int(fr * 100)}%", wrong_caught=f"{100 * f[yy == 1].mean():.0f}%", right_flagged=f"{100 * f[yy == 0].mean():.0f}%",
                         wrong_among_kept=f"{100 * yy[~f].mean():.1f}%", wrong_overall=f"{100 * yy.mean():.1f}%"))
gate_out = pd.DataFrame(grow)

# ------------------------------------------------------------------ H4 photo detector applied once to the new 100 (photo scores computed on Kaggle)
q = pd.read_csv(ROOT + "results/armCext/armCext_quality_signals_all.csv")
assert len(q) == 900
ph = new[["variant_id", "record", "axis", "dig_hr", "diff_bpm"]].merge(q[["variant_id"] + FEATS], on="variant_id")
ph["blur_log"] = np.log10(ph.blur_score + 1)
ph["rec"] = ph.record.astype(str)
ph["wrong5"] = ph.diff_bpm > 5
ph["bad"] = ph.dig_hr.isna() | ph.wrong5
dtr = d[d.out]
m_p = sig_model().fit(dtr[X_COLS], dtr.wrong5.astype(int).values)
m_b = sig_model().fit(d[X_COLS], d.bad.astype(int).values)
ph["p_wrong"] = m_p.predict_proba(ph[X_COLS])[:, 1]
ph["p_bad"] = m_b.predict_proba(ph[X_COLS])[:, 1]


def ph_row(mask, label, target_col, score):
    x = ph[mask]
    if target_col == "wrong5":
        x = x[x.dig_hr.notna()]
    yy = x[target_col].astype(int).values
    if yy.sum() < 5:
        return dict(subset=label, target=target_col, images=len(x), events=int(yy.sum()), auc="too few (<5)")
    a, ci = auc_ci(yy, x[score].values, x.rec.values, B=2000)
    return dict(subset=label, target=target_col, images=len(x), events=int(yy.sum()), auc=f"{a:.3f} ({ci[0]:.2f} to {ci[1]:.2f})")


real_p = ph.axis != "C0_kit_original"
prow2 = [ph_row(ph.rec != "x", "all 9 types", "wrong5", "p_wrong"), ph_row(real_p, "real C1-C8", "wrong5", "p_wrong"),
         ph_row(ph.rec != "x", "all 9 types", "bad", "p_bad"), ph_row(real_p, "real C1-C8", "bad", "p_bad"),
         ph_row(ph.axis != "C4_phone_photo_screen", "without screen photos", "wrong5", "p_wrong")]
c4 = ph[ph.axis == "C4_phone_photo_screen"]
photo_out = pd.DataFrame(prow2)
medsc = ph.groupby("axis")[FEATS].median().round(2).reset_index()
medsc["axis"] = medsc.axis.map(NAMES)
# does the photo score tell WHICH screen photos get no output?
c4row = ph_row(ph.axis == "C4_phone_photo_screen", "screen photos only (who gets no output?)", "bad", "p_bad")
photo_out = pd.concat([photo_out, pd.DataFrame([c4row])], ignore_index=True)
# no-output screen photos: single-score view
nz = []
for c in FEATS:
    v_ = c4[c].astype(float)
    ok = v_.notna().values
    yy = c4.dig_hr.isna().astype(int).values[ok]
    if 0 < yy.sum() < len(yy):
        a = roc_auc_score(yy, v_.values[ok])
        nz.append(dict(photo_score=c, auc_for_no_output_in_screen_photos=round(max(a, 1 - a), 3), higher_means="no output" if a >= 0.5 else "output"))
nz = pd.DataFrame(nz)

# ------------------------------------------------------------------ write
rates.to_csv(OUT + "sectionH_rates.csv", index=False)
paired.to_csv(OUT + "sectionH_paired_vs_clean.csv", index=False)
ev.to_csv(OUT + "sectionH_events.csv", index=False)
c0_wrong_list.to_csv(OUT + "sectionH_clean_page_wrong.csv", index=False)
aucs_out.to_csv(OUT + "sectionH_output_gate_auc.csv", index=False)
gate_out.to_csv(OUT + "sectionH_output_gate_coverage.csv", index=False)
photo_out.to_csv(OUT + "sectionH_photo_detector_auc.csv", index=False)
ph.drop(columns=["rec"]).to_csv(OUT + "sectionH_photo_scores_scored.csv", index=False)
medsc.to_csv(OUT + "sectionH_photo_scores_by_capture.csv", index=False)

L = ["# Section H (EXPLORATORY / REPLICATION): 100 more real-capture recordings\n",
     "*Generated by `scripts/analysis/section_H.py`. Rules: `docs/plan/analysis_plan_changes.md` (2026-11-07, Arm C extension). New 100 recordings x 9 capture types = 900 images; "
     "pooled with the 40 earlier recordings = 140 recordings, 1,260 images. No verdict words; the 100-event rule is reported.*\n",
     "## H1. Rates per capture type (Wilson 95%)\n", md_table(rates) + "\n",
     "## H1b. Paired test against the clean kit page C0 (exact, Holm over 8 comparisons)\n", md_table(paired) + "\n",
     "## H2. Events and the wrong clean pages\n", md_table(ev) + "\n",
     "Wrong readings on the clean kit page C0 (reference vs digitiser):\n", md_table(c0_wrong_list) + "\n",
     "Pattern of all wrong readings with an output (pooled):\n", md_table(slip) + "\n",
     "## H3. Output gate (D2): trained on simulated damage, applied once to the real captures (images with a reading)\n", md_table(aucs_out) + "\n",
     "Gate on the real captures (flag the highest-risk readings):\n", md_table(gate_out) + "\n",
     "## H4. Photo detector: trained on the simulated damage, applied once to the new 100 real captures\n", md_table(photo_out) + "\n",
     "Single photo scores for 'no output' among screen photos:\n", md_table(nz) + "\n",
     "Median photo scores per capture type:\n", md_table(medsc) + "\n"]
open(OUT + "SECTION_H.md", "w", encoding="utf-8").write("\n".join(L))

pd.set_option("display.width", 250)
pd.set_option("display.max_colwidth", 60)
for t in (rates, paired, ev, c0_wrong_list, slip, aucs_out, gate_out, photo_out, nz, medsc):
    print(t.to_string(index=False)); print()
