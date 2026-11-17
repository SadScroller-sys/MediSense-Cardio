"""Section O (CONFIRMATION on the user's own phone; rules fixed beforehand in docs/plan/analysis_plan_changes.md 2026-11-08, 'Own-phone confirmation set').
Usage: python -I scripts/analysis/section_O_ownphotos.py <results_dir_with_Kaggle_outputs> <features_csv_for_the_npz_folder>
  results_dir: folder with results_ownphotos.csv, ownphotos_quality_signals.csv, ownphotos_digitized_12lead/
  features_csv: output of  python -I scripts/analysis/section_features_dir.py <results_dir>/ownphotos_digitized_12lead <features_csv> <n_photos>
Photos are matched to pages by file name order: 2 photos per page (A straight, B angled), pages P01...; the match is printed and must be checked by eye.
Frozen models (no refitting on the new photos): photo model = logistic regression on five photo scores trained on all 900 competition-capture images of the new 100 recordings (target: no output);
variant trained on the competition screen photos (C4) only; output check = logistic regression on the 15 output features trained on the simulated new 100 with cleaned labels."""
import os
import sys
import warnings

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

warnings.filterwarnings("ignore")
RES, FEAT = sys.argv[1].rstrip("/\\"), sys.argv[2]
src = open("D:/Capstone Project/scripts/analysis/section_D2.py", encoding="utf-8").read().split("preds = {}")[0]
exec(compile(src, "section_D2_prefix", "exec"))          # te, y, OUT_COLS, X_COLS, sig_model, auc_ci
ROOT = "D:/Capstone Project/"
OUT = ROOT + "results/analysis/"
OWN = ROOT + "results/ownphotos/"


def hr_clean(sig, fs):
    import neurokit2 as nk
    x = nk.ecg_clean(sig, sampling_rate=fs, method="neurokit")
    p, _ = nk.ecg_peaks(x, sampling_rate=fs)
    return float(np.nanmean(nk.ecg_rate(p, sampling_rate=fs, desired_length=len(sig))))


def fmt(a, ci):
    return f"{a:.3f} ({ci[0]:.2f} to {ci[1]:.2f})"


# ---------------------------------------------------------------- photos -> pages
r = pd.read_csv(RES + "/results_ownphotos.csv")
q = pd.read_csv(RES + "/ownphotos_quality_signals.csv")
ph = r.merge(q, on="variant_id").sort_values("variant_id").reset_index(drop=True)
n = len(ph)
ph["page"] = [f"P{i // 2 + 1:02d}" for i in range(n)]
ph["shot"] = ["A_straight" if i % 2 == 0 else "B_angled" for i in range(n)]
print(f"{n} photos -> {ph.page.nunique()} pages. Check by eye: first rows of the matching\n", ph[["variant_id", "page", "shot"]].head(6).to_string(index=False))
assert n == 60 and ph.page.nunique() == 30, "expected 60 photos / 30 pages; check the matching before using any result"

# ---------------------------------------------------------------- reference heart rate (PTB-XL 100 Hz lead II, cleaned and original method)
import wfdb
ref = {}
for pg in ph.page.unique():
    rec = wfdb.rdrecord(OWN + f"source_records/{pg}")
    s = rec.p_signal[:, rec.sig_name.index("II")]
    ref[pg] = (hr_clean(s, rec.fs),)
ph["gt_hr_clean"] = ph.page.map(lambda p: ref[p][0])

# ---------------------------------------------------------------- digitised heart rate (cleaned), output features
fe = pd.read_csv(FEAT)
ph = ph.merge(fe, on="variant_id", how="left")
dig = {}
for v in ph.variant_id[ph.has_output]:
    z = np.load(f"{RES}/ownphotos_digitized_12lead/{v}.npz")
    s = np.asarray(z["II"], dtype=float)
    s = s[np.isfinite(s)] / 1000.0
    try:
        dig[v] = hr_clean(s, 1000) if len(s) > 10 else np.nan
    except Exception:
        dig[v] = np.nan
ph["dig_hr_clean"] = ph.variant_id.map(dig)
ph["none"] = ph.dig_hr_clean.isna()
ph["wrong_c"] = (ph.dig_hr_clean - ph.gt_hr_clean).abs() > 5
ph["blur_log"] = np.log10(ph.blur_score + 1)

# ---------------------------------------------------------------- frozen photo models
J = pd.read_csv(OUT + "sectionJ_remeasured.csv")
J = J[J.set == "armC_new100"]
qa = pd.read_csv(ROOT + "results/armCext/armCext_quality_signals_all.csv")
qa["blur_log"] = np.log10(qa.blur_score + 1)
tr = J.merge(qa[["variant_id"] + X_COLS], on="variant_id")
tr["none"] = tr.dig_hr.isna()
m_all = sig_model().fit(tr[X_COLS], tr.none.astype(int).values)
c4 = tr[tr.axis == "C4_phone_photo_screen"]
m_c4 = sig_model().fit(c4[X_COLS], c4.none.astype(int).values)
ph["p_none_all"] = m_all.predict_proba(ph[X_COLS])[:, 1]
ph["p_none_c4"] = m_c4.predict_proba(ph[X_COLS])[:, 1]

rows = []
yy = ph.none.astype(int).values
g = ph.page.values
print(f"no output: {int(yy.sum())}/{n} photos ({100 * yy.mean():.0f}%); competition screen photos: 39%")
for lab, sc in (("photo model trained on all 9 competition capture types (primary)", "p_none_all"), ("photo model trained on competition screen photos only", "p_none_c4")):
    if 0 < yy.sum() < n:
        a, ci = auc_ci(yy, ph[sc].values, g, B=2000)
        rows.append(dict(question="predict NO OUTPUT from the photo", model=lab, photos=n, events=int(yy.sum()), auc=fmt(a, ci),
                         criterion_AUC_ge_0p70_and_lower_gt_0p5="MET" if (a >= 0.70 and ci[0] > 0.5) else "NOT MET"))
    else:
        rows.append(dict(question="predict NO OUTPUT from the photo", model=lab, photos=n, events=int(yy.sum()), auc="not computable (all or none have output)", criterion_AUC_ge_0p70_and_lower_gt_0p5="n/a"))
for shot in ("A_straight", "B_angled"):
    mk = (ph.shot == shot).values
    if 0 < yy[mk].sum() < mk.sum():
        a, ci = auc_ci(yy[mk], ph.p_none_all.values[mk], g[mk], B=2000)
        rows.append(dict(question=f"predict NO OUTPUT, {shot} photos only", model="all-types model", photos=int(mk.sum()), events=int(yy[mk].sum()), auc=fmt(a, ci), criterion_AUC_ge_0p70_and_lower_gt_0p5="descriptive"))

# output check for wrong HR (cleaned), photos with an output
Kk = pd.read_csv(OUT + "sectionK_remeasured_sim.csv")
Kk["wrong_c"] = Kk.diff_clean > 5
sim = te.merge(Kk[["variant_id", "wrong_c", "dig_hr_clean"]], on="variant_id", how="left")
sim = sim[sim.dig_hr_clean.notna()].reset_index(drop=True)
m_out = sig_model().fit(sim[OUT_COLS], sim.wrong_c.astype(int).values)
wo = ph[~ph.none & ph[OUT_COLS].notna().any(axis=1)].reset_index(drop=True)
wo["p_out"] = m_out.predict_proba(wo[OUT_COLS])[:, 1]
yw = wo.wrong_c.astype(int).values
if 5 <= yw.sum() < len(yw):
    a, ci = auc_ci(yw, wo.p_out.values, wo.page.values, B=2000)
    rows.append(dict(question="predict WRONG HR (>5 bpm) from the output (descriptive)", model="output check (frozen)", photos=len(wo), events=int(yw.sum()), auc=fmt(a, ci), criterion_AUC_ge_0p70_and_lower_gt_0p5="descriptive"))
else:
    rows.append(dict(question="predict WRONG HR (>5 bpm) from the output (descriptive)", model="output check (frozen)", photos=len(wo), events=int(yw.sum()), auc="too few wrong readings (<5)", criterion_AUC_ge_0p70_and_lower_gt_0p5="descriptive"))
tab = pd.DataFrame(rows)
summ = pd.DataFrame([dict(photos=n, pages=ph.page.nunique(), no_output=int(ph.none.sum()), wrong_hr_gt5_cleaned=int(ph.wrong_c[~ph.none].sum()), with_output=int((~ph.none).sum()),
                          median_abs_error_bpm=round(float((ph.dig_hr_clean - ph.gt_hr_clean).abs().median()), 2))])
ph.to_csv(OUT + "sectionO_ownphotos_scored.csv", index=False)
tab.to_csv(OUT + "sectionO_ownphotos_results.csv", index=False)


def md_table(t):
    head = "| " + " | ".join(map(str, t.columns)) + " |\n|" + "---|" * len(t.columns) + "\n"
    return head + "\n".join("| " + " | ".join(str(z) for z in r_) + " |" for r_ in t.itertuples(index=False))


L = ["# Section O: confirmation on the user's own phone (screen photos of 30 new pages)\n",
     "*Generated by `scripts/analysis/section_O_ownphotos.py`. Rules fixed before any photo existed (docs/plan/analysis_plan_changes.md, 2026-11-08). Models frozen, not refitted on these photos. Descriptive; one phone, one screen, 30 recordings.*\n",
     "## Summary\n", md_table(summ) + "\n", "## Results\n", md_table(tab) + "\n"]
open(OUT + "SECTION_O.md", "w", encoding="utf-8").write("\n".join(L))
pd.set_option("display.width", 250)
pd.set_option("display.max_colwidth", 70)
print(summ.to_string(index=False))
print(tab.to_string(index=False))
