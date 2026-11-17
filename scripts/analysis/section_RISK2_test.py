"""RISK PILOT 2, step 3: test the FROZEN model ONCE on the SEALED test split (bucket >= 80, parts 6 to 17), with the age baselines, the paired AUROC difference over age alone, and the transfer check on our digitised ECGs
(rules: docs/plan/analysis_plan_changes.md, 2026-11-16 'RISK PILOT 2'). Refuses to run twice; refuses to run before the M set is fully digitised.
Usage: demo\\.venv-gpu\\Scripts\\python.exe -I scripts/analysis/section_RISK2_test.py"""
import glob
import json
import os
import sys

import numpy as np
import pandas as pd
import torch
from scipy.stats import spearmanr
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "demo"))
from health import data as D  # noqa: E402
from health import intervals_ml as I  # noqa: E402
from health import risk as R  # noqa: E402

OUT = os.path.join(ROOT, "results", "risk_pilot2") + os.sep
OUTF = OUT + "risk_test_metrics_h5.csv"
if os.path.exists(OUTF) and "--force" not in sys.argv:
    sys.exit("The test was already run once (rule: run ONCE).")
if not os.path.exists(ROOT + "/results/intervals_ml/M_all_done.flag"):
    sys.exit("The M set is not fully digitised yet (rule: transfer groups complete before the test).")
dev = "cuda" if torch.cuda.is_available() else "cpu"
cal = json.load(open(OUT + "calibration_h5.json"))
net = R.RiskNet().to(dev)
net.load_state_dict(torch.load(OUT + "model_h5.pt", map_location=dev))
net.eval()
mask_t = I.layout_masks(dev)
rng = np.random.RandomState(63)
B = 1000
a_pl, b_pl = cal["platt"]["a"], cal["platt"]["b"]


def to_prob(lg):
    return 1 / (1 + np.exp(-(a_pl * lg + b_pl)))


def logit_raw(raw, age_in):                   # (N, 12, 2500) mV -> logits
    out = []
    with torch.no_grad():
        for i in range(0, len(raw), 256):
            xb = torch.from_numpy(np.ascontiguousarray(raw[i:i + 256], dtype=np.float32)).to(dev)
            out.append(net(I.make_input(xb, mask_t, False), torch.from_numpy(np.asarray(age_in[i:i + 256], np.float32)).to(dev)).squeeze(1).cpu().numpy())
    return np.concatenate(out)


def logit_x24(X24, age_in):
    out = []
    with torch.no_grad():
        for i in range(0, len(X24), 128):
            out.append(net(torch.from_numpy(np.ascontiguousarray(X24[i:i + 128])).to(dev), torch.from_numpy(np.asarray(age_in[i:i + 128], np.float32)).to(dev)).squeeze(1).cpu().numpy())
    return np.concatenate(out)


# ---------------------------------------------------------------- sealed test split (once)
X = np.load(os.path.join(ROOT, "data", "code15") + os.sep + "risk2_x250_f16.npy", mmap_mode="r")
m = pd.read_csv(OUT + "split_h5.csv")
te = np.flatnonzero(m.usable & (m.split == "test"))
tr = np.flatnonzero(m.usable & (m.split == "train"))
LG = logit_raw(np.stack([np.asarray(X[i], np.float32) for i in te]), m.age_in.values[te])
P = to_prob(LG)
y = m.y.values[te]
print(f"sealed test: {len(te)} patients, {int(y.sum())} events", flush=True)
pa_age = LogisticRegression(max_iter=1000).fit(m[["age"]].astype(float).values[tr], m.y.values[tr]).predict_proba(m[["age"]].astype(float).values[te])[:, 1]
pa_as = LogisticRegression(max_iter=1000).fit(m[["age", "is_male"]].astype(float).values[tr], m.y.values[tr]).predict_proba(m[["age", "is_male"]].astype(float).values[te])[:, 1]


def boot(y, ps):
    """ps = dict name -> score; returns point, lo, hi for each and the paired difference of the first two."""
    names = list(ps)
    v = {k: [] for k in names}
    dv = []
    for _ in range(B):
        ix = rng.choice(len(y), len(y), replace=True)
        if 0 < y[ix].sum() < len(ix):
            a = {k: roc_auc_score(y[ix], ps[k][ix]) for k in names}
            for k in names:
                v[k].append(a[k])
            dv.append(a[names[0]] - a[names[1]])
    res = {k: (float(roc_auc_score(y, ps[k])), float(np.percentile(v[k], 2.5)), float(np.percentile(v[k], 97.5))) for k in names}
    diff = (float(roc_auc_score(y, ps[names[0]]) - roc_auc_score(y, ps[names[1]])), float(np.percentile(dv, 2.5)), float(np.percentile(dv, 97.5)))
    return res, diff


def ece_q(p, y, bins=10):
    order = np.argsort(p)
    return float(sum(len(c) / len(p) * abs(p[c].mean() - y[c].mean()) for c in np.array_split(order, bins)))


res, diff = boot(y, {"ECG + age": P, "Age alone": pa_age, "Age + sex": pa_as})
slope_fit = LogisticRegression(C=1e6, max_iter=1000).fit(LG[:, None], y)
cal_slope, cal_int = float(slope_fit.coef_[0, 0]), float(slope_fit.intercept_[0])
rows = []
for nm, p in (("ECG + age (calibrated)", P), ("Age alone (logistic)", pa_age), ("Age + sex (logistic)", pa_as)):
    k = {"ECG + age (calibrated)": "ECG + age", "Age alone (logistic)": "Age alone", "Age + sex (logistic)": "Age + sex"}[nm]
    a_, l_, h_ = res[k]
    rows.append(dict(item=nm, auroc=a_, lo95=l_, hi95=h_, auprc=float(average_precision_score(y, p)), brier=float(np.mean((p - y) ** 2)), ece=ece_q(p, y), cal_slope=cal_slope if k == "ECG + age" else np.nan, n=len(y), events=int(y.sum())))
age = m.age.values[te]
for nm, mk in (("ECG + age, age < 50", age < 50), ("ECG + age, age 50 to 69", (age >= 50) & (age < 70)), ("ECG + age, age 70 and over", age >= 70)):
    if 0 < y[mk].sum() < mk.sum():
        r2, _ = boot(y[mk], {"a": P[mk], "b": pa_age[mk]})
        rows.append(dict(item=nm, auroc=r2["a"][0], lo95=r2["a"][1], hi95=r2["a"][2], n=int(mk.sum()), events=int(y[mk].sum())))
        rows.append(dict(item=nm.replace("ECG + age", "Age alone"), auroc=r2["b"][0], lo95=r2["b"][1], hi95=r2["b"][2], n=int(mk.sum()), events=int(y[mk].sum())))
T = pd.DataFrame(rows)
T.to_csv(OUTF, index=False)
cat = np.where(P < 0.05, 0, np.where(P < 0.15, 1, 2))
ctab = []
for k, nm in enumerate(["Low (< 5%)", "Moderate (5% to < 15%)", "High (15% or more)"]):
    s = cat == k
    ctab.append(dict(category=nm, patients=int(s.sum()), events=int(y[s].sum()), observed_rate=float(y[s].mean()) if s.any() else float("nan"), mean_predicted=float(P[s].mean()) if s.any() else float("nan")))
C = pd.DataFrame(ctab)
dec = pd.DataFrame(dict(p=P, y=y)).assign(decile=lambda d: pd.qcut(d.p.rank(method="first"), 10, labels=False) + 1).groupby("decile").agg(predicted=("p", "mean"), observed=("y", "mean"), n=("y", "size"))
mono = bool(C.observed_rate.is_monotonic_increasing and C.observed_rate.notna().all() and len(C) == 3)
ratio_ok = bool(mono and C.observed_rate.iloc[0] > 0 and C.observed_rate.iloc[2] >= 3 * C.observed_rate.iloc[0])

# ---------------------------------------------------------------- transfer check (NOT outcome validation); age from PTB-XL given to both versions
db = pd.read_csv(D.PT + "ptbxl_database.csv").set_index("ecg_id").sort_index()
X250 = I.load_ptbxl250(db)
pos = {e: n for n, e in enumerate(db.index)}
ds = D.digitised_sets()
Kdf = pd.read_csv(ROOT + "/results/intervals_ml/selected_K_100.csv")
items = [("drawn pages (dev: new100, F, G)", r.path, int(r.ecg_id)) for _, r in ds[ds.set == "T2"].iterrows()]
items += [("drawn pages (dev: K)", ROOT + f"/results/intervals_ml/K/k_digitized_12lead/{p}.npz", int(e)) for p, e in zip(Kdf.page, Kdf.ecg_id) if os.path.exists(ROOT + f"/results/intervals_ml/K/k_digitized_12lead/{p}.npz")]
items += [("real phone photos (dev, not gated)", r.path, int(r.ecg_id)) for _, r in ds[ds.set == "T3"].iterrows()]
selg = pd.read_csv(ROOT + "/results/fresh_g/selected_g_100.csv").set_index("page")
zz = pd.read_csv(ROOT + "/results/analysis/sectionZ_all.csv")
items += [("simulated photos (dev)", ROOT + f"/results/fresh_sim/dig_v2/{r.photo}.npz", int(selg.loc[r.page, "ecg_id"])) for _, r in zz[zz.variant == "v2"].iterrows() if os.path.exists(ROOT + f"/results/fresh_sim/dig_v2/{r.photo}.npz") and not r["none"]]
for sel_csv, pat, label in (("selected_L_100.csv", "L/l_digitized_12lead/*.npz", "drawn pages (fresh L)"), ("selected_M_100.csv", "M/m_digitized_12lead/*.npz", "drawn pages (fresh M)"),
                            ("selected_L_100.csv", "L_sim/dig_v2/*.npz", "simulated photos (fresh L)"), ("selected_M_100.csv", "M_sim/dig_v2/*.npz", "simulated photos (fresh M)")):
    s = pd.read_csv(ROOT + "/results/intervals_ml/" + sel_csv).set_index("page")
    for f in sorted(glob.glob(ROOT + "/results/intervals_ml/" + pat)):
        pg = os.path.basename(f)[:4]
        if pg in s.index:
            items.append((label, f, int(s.loc[pg, "ecg_id"])))
sys.path.insert(0, ROOT + "/scripts/analysis")
import h2_photos  # noqa: E402

_hp, _hi, _hg = h2_photos.primary_items()
items += [("REAL printed-paper STRAIGHT photos (H2, friend's phone)", f, e) for f, e in zip(_hp, _hi)]
idf = pd.DataFrame(items, columns=["group", "path", "ecg_id"])
ages = np.clip(db.loc[idf.ecg_id, "age"].astype(float).values, 16, 90)
rawx = np.stack([np.asarray(X250[pos[e]], np.float32) for e in idf.ecg_id])
digx = np.stack([I.digitised_to_input250({k: v.astype(float) for k, v in np.load(p).items()}) for p in idf.path])
a_full = R.age_in(ages)
a_fix = R.age_in(np.full(len(ages), 60.0))
catf = lambda p: np.where(p < 0.05, 0, np.where(p < 0.15, 1, 2))  # noqa: E731
o_full, d_full = to_prob(logit_raw(rawx, a_full)), to_prob(logit_x24(digx, a_full))
o_ecg, d_ecg = to_prob(logit_raw(rawx, a_fix)), to_prob(logit_x24(digx, a_fix))
tr_rows = []
for g, sub in idf.groupby("group", sort=False):
    ix = sub.index.values
    tr_rows.append(dict(group=g, n=len(ix), spearman_full=float(spearmanr(o_full[ix], d_full[ix])[0]), same_cat_full=float(np.mean(catf(o_full[ix]) == catf(d_full[ix]))), mean_abs_diff_full=float(np.mean(np.abs(o_full[ix] - d_full[ix]))),
                        spearman_ecg=float(spearmanr(o_ecg[ix], d_ecg[ix])[0]), same_cat_ecg=float(np.mean(catf(o_ecg[ix]) == catf(d_ecg[ix])))))
TR = pd.DataFrame(tr_rows)
TR.to_csv(OUT + "risk_transfer_h5.csv", index=False)
pd.DataFrame(dict(group=idf.group, ecg_id=idf.ecg_id, age=ages, full_original=o_full, full_digitised=d_full, ecg_original=o_ecg, ecg_digitised=d_ecg)).to_csv(OUT + "risk_transfer_items_h5.csv", index=False)
gated = TR[~TR.group.str.contains("not gated")]
pages_g, sim_g, real_g = gated[gated.group.str.contains("pages")], gated[gated.group.str.contains("simulated")], gated[gated.group.str.startswith("REAL")]
ok_t = lambda t: bool(len(t) and (t.spearman_full >= 0.85).all() and (t.same_cat_full >= 0.80).all())  # noqa: E731
e = T.iloc[0]
age_row = T.iloc[1]
status = dict(horizon_years=5.0, auroc=e.auroc, auroc_lo95=e.lo95, auroc_age_alone=age_row.auroc, auroc_diff_vs_age=diff[0], auroc_diff_lo95=diff[1], auroc_diff_hi95=diff[2], cal_slope=e.cal_slope, ece=e.ece,
              categories_monotone=mono, high_over_low_ratio_ok=ratio_ok, pass_discrimination=bool(e.auroc >= 0.80 and e.lo95 > 0.75), pass_ecg_adds_value=bool(diff[1] > 0),
              pass_calibration=bool(0.8 <= e.cal_slope <= 1.25 and e.ece <= 0.02), pass_categories=bool(ratio_ok), transfer_pages_ok=ok_t(pages_g), transfer_sim_ok=ok_t(sim_g), transfer_real_ok=ok_t(real_g),
              ecg_only_transfer_real_spearman=float(real_g.spearman_ecg.iloc[0]) if len(real_g) else None)
status["shown_in_app"] = bool(status["pass_discrimination"] and status["pass_ecg_adds_value"] and status["pass_calibration"] and status["pass_categories"] and status["transfer_pages_ok"] and status["transfer_sim_ok"] and status["transfer_real_ok"])
json.dump(status, open(OUT + "risk_status_h5.json", "w"), indent=1)

md = ["# Section RISK 2: ECG + age, all-cause mortality within 5 years, SEALED test once (PILOT 2; rules logged before the download and before any model was trained)", "",
      "Rules: `docs/plan/analysis_plan_changes.md` ('RISK PILOT 2'). Data: CODE-15% (open, CC-BY 4.0), parts 0 to 17, patients with an outcome, 10 s recordings; people with a complete 5-year follow-up only (so the observed rate is higher than a population risk). "
      "Sealed test = patients of parts 6 to 17 never used before. Categories and pass rules are the assistant's proposal, not approved by the guide. All-cause mortality, not cardiac events; largely driven by age. The transfer check is NOT outcome validation.", "",
      "## Sealed test split", "", "| Model | n | Events | AUROC (95% interval) | AUPRC | Brier | ECE | Calibration slope |", "|---|---|---|---|---|---|---|---|"]
for _, r in T.iterrows():
    md.append(f"| {r['item']} | {int(r.n)} | {int(r.events)} | {r.auroc:.3f} ({r.lo95:.3f} to {r.hi95:.3f}) | " + (f"{r.auprc:.3f} | {r.brier:.4f} | {r.ece:.4f} | " if pd.notna(r.get('auprc')) else "| | | ") + (f"{r.cal_slope:.2f}" if pd.notna(r.get('cal_slope')) else "") + " |")
md += ["", f"**Added value of the ECG over age alone (paired bootstrap, AUROC difference): {diff[0]:+.3f} (95% {diff[1]:+.3f} to {diff[2]:+.3f}).**", "",
       "## Categories on the sealed test (proposal: Low < 5%, Moderate 5% to < 15%, High 15% or more)", "", "| Category | Patients | Events | Observed rate | Mean predicted |", "|---|---|---|---|---|"]
for _, r in C.iterrows():
    md.append(f"| {r.category} | {r.patients} | {r.events} | {100 * r.observed_rate:.2f}% | {100 * r.mean_predicted:.2f}% |")
md += ["", "Deciles of predicted risk:", "", "| Decile | Mean predicted | Observed | n |", "|---|---|---|---|"]
for k, r in dec.iterrows():
    md.append(f"| {k} | {100 * r.predicted:.2f}% | {100 * r.observed:.2f}% | {int(r.n)} |")
md += ["", "## Transfer check: the same ECG (and the same age), original signal against its digitised version (no outcomes exist for these ECGs)", "",
       "FULL = what the app would show (true age entered). ECG-ONLY = age fixed at 60 for both versions, so only the ECG changes.", "",
       "| Group | n | Spearman FULL | Same category FULL | Mean abs. difference FULL | Spearman ECG-ONLY | Same category ECG-ONLY |", "|---|---|---|---|---|---|---|"]
for _, r in TR.iterrows():
    md.append(f"| {r.group} | {r.n} | {r.spearman_full:.2f} | {100 * r.same_cat_full:.0f}% | {100 * r.mean_abs_diff_full:.2f} points | {r.spearman_ecg:.2f} | {100 * r.same_cat_ecg:.0f}% |")
md += ["", "## Verdict (pass rules applied)", "", "| Rule | Result |", "|---|---|", f"| AUROC at least 0.80, lower end above 0.75 | {status['pass_discrimination']} |",
       f"| ECG adds value: lower end of the paired difference over age alone above 0 | {status['pass_ecg_adds_value']} |", f"| Calibration slope 0.8 to 1.25 and ECE at most 0.02 | {status['pass_calibration']} |",
       f"| Observed rates increase across Low, Moderate, High and High at least 3 times Low | {status['pass_categories']} |", f"| Transfer FULL on drawn pages (Spearman at least 0.85, at least 80% same category) | {status['transfer_pages_ok']} |",
       f"| Transfer FULL on simulated photos | {status['transfer_sim_ok']} |", f"| Transfer FULL on REAL straight printed-paper photos | {status['transfer_real_ok']} |", f"| **Shown in the app** | **{status['shown_in_app']}** |"]
open(OUT + "SECTION_RISK2_h5.md", "w", encoding="utf-8").write("\n".join(md) + "\n")
print("\n".join(md))
