"""ECG-estimated mortality RISK PILOT (CODE-15%), step 3: test the FROZEN model ONCE on the untouched test split, add the age baselines, and run the TRANSFER CHECK on our digitised ECGs
(rules: docs/plan/analysis_plan_changes.md, 2026-11-15 night). Refuses to run twice. Writes results/risk_pilot/SECTION_RISK.md, risk_test_metrics.csv, risk_status.json.
Usage: demo\\.venv-gpu\\Scripts\\python.exe scripts/analysis/section_RISK_test.py [--horizon 1]"""
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

H = float(sys.argv[sys.argv.index("--horizon") + 1]) if "--horizon" in sys.argv else 1.0
TAG = f"h{int(H)}"
DD = os.path.join(ROOT, "data", "code15") + os.sep
OUT = os.path.join(ROOT, "results", "risk_pilot") + os.sep
OUTF = OUT + f"risk_test_metrics_{TAG}.csv"
if os.path.exists(OUTF) and "--force" not in sys.argv:
    sys.exit("The test was already run once (rule: run ONCE).")
dev = "cuda" if torch.cuda.is_available() else "cpu"
cal = json.load(open(OUT + f"calibration_{TAG}.json"))
net = I.IntervalNet(n_out=1).to(dev)
net.load_state_dict(torch.load(OUT + f"model_{TAG}.pt", map_location=dev))
net.eval()
mask_t = I.layout_masks(dev)
rng = np.random.RandomState(63)
B = 1000


def prob_from_raw(raw):                       # (N, 12, 2500) mV float32 -> calibrated probability
    out = []
    with torch.no_grad():
        for i in range(0, len(raw), 256):
            xb = torch.from_numpy(np.ascontiguousarray(raw[i:i + 256], dtype=np.float32)).to(dev)
            out.append(net(I.make_input(xb, mask_t, False)).squeeze(1).cpu().numpy())
    lg = np.concatenate(out)
    return 1 / (1 + np.exp(-(cal["platt"]["a"] * lg + cal["platt"]["b"]))), lg


def prob_from_x24(X24):                       # (N, 24, 2500) digitised input -> calibrated probability
    out = []
    with torch.no_grad():
        for i in range(0, len(X24), 128):
            out.append(net(torch.from_numpy(np.ascontiguousarray(X24[i:i + 128])).to(dev)).squeeze(1).cpu().numpy())
    lg = np.concatenate(out)
    return 1 / (1 + np.exp(-(cal["platt"]["a"] * lg + cal["platt"]["b"])))


# ---------------------------------------------------------------- test split (once)
X = np.load(DD + "risk_x250_f16.npy", mmap_mode="r")
m = pd.read_csv(OUT + f"split_{TAG}.csv")
te = np.flatnonzero(m.usable & (m.split == "test"))
tr = np.flatnonzero(m.usable & (m.split == "train"))
P, LG = prob_from_raw(np.stack([np.asarray(X[i], np.float32) for i in te]))
y = m.y.values[te]
print(f"test: {len(te)} patients, {int(y.sum())} events", flush=True)


def boot_auc(y, p):
    v = []
    for _ in range(B):
        ix = rng.choice(len(y), len(y), replace=True)
        if 0 < y[ix].sum() < len(ix):
            v.append(roc_auc_score(y[ix], p[ix]))
    return float(roc_auc_score(y, p)), float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))


def ece_q(p, y, bins=10):
    order = np.argsort(p)
    e = 0.0
    for chunk in np.array_split(order, bins):
        e += len(chunk) / len(p) * abs(p[chunk].mean() - y[chunk].mean())
    return float(e)


auc, lo, hi = boot_auc(y, P)
slope_fit = LogisticRegression(C=1e6, max_iter=1000).fit(LG[:, None], y)
cal_slope, cal_int = float(slope_fit.coef_[0, 0]), float(slope_fit.intercept_[0])
rows = [dict(item="ECG model (calibrated)", auroc=auc, lo95=lo, hi95=hi, auprc=float(average_precision_score(y, P)), brier=float(np.mean((P - y) ** 2)), ece=ece_q(P, y),
             cal_slope=cal_slope, cal_intercept=cal_int, n=len(y), events=int(y.sum()))]
for nm, cols in (("Age alone (logistic)", ["age"]), ("Age + sex (logistic)", ["age", "is_male"])):
    Xa = m[cols].astype(float).values
    lrm = LogisticRegression(max_iter=1000).fit(Xa[tr], m.y.values[tr])
    pa = lrm.predict_proba(Xa[te])[:, 1]
    a_, l_, h_ = boot_auc(y, pa)
    rows.append(dict(item=nm, auroc=a_, lo95=l_, hi95=h_, auprc=float(average_precision_score(y, pa)), brier=float(np.mean((pa - y) ** 2)), ece=ece_q(pa, y), n=len(y), events=int(y.sum())))
age = m.age.values[te]
for nm, mk in (("ECG model, age < 50", age < 50), ("ECG model, age 50 to 69", (age >= 50) & (age < 70)), ("ECG model, age 70 and over", age >= 70)):
    if 0 < y[mk].sum() < mk.sum():
        a_, l_, h_ = boot_auc(y[mk], P[mk])
        rows.append(dict(item=nm, auroc=a_, lo95=l_, hi95=h_, n=int(mk.sum()), events=int(y[mk].sum())))
T = pd.DataFrame(rows)
T.to_csv(OUTF, index=False)
# categories (proposal): Low < 1%, Moderate 1% to < 3%, High >= 3%
cat = np.where(P < 0.01, 0, np.where(P < 0.03, 1, 2))
ctab = []
for k, nm in enumerate(["Low (< 1%)", "Moderate (1% to < 3%)", "High (3% or more)"]):
    s = cat == k
    ctab.append(dict(category=nm, patients=int(s.sum()), events=int(y[s].sum()), observed_rate=float(y[s].mean()) if s.any() else float("nan"), mean_predicted=float(P[s].mean()) if s.any() else float("nan")))
C = pd.DataFrame(ctab)
dec = pd.DataFrame(dict(p=P, y=y)).assign(decile=lambda d: pd.qcut(d.p.rank(method="first"), 10, labels=False) + 1).groupby("decile").agg(predicted=("p", "mean"), observed=("y", "mean"), n=("y", "size"))
mono = bool(C.observed_rate.is_monotonic_increasing and C.observed_rate.notna().all() and len(C) == 3)
ratio_ok = bool(mono and C.observed_rate.iloc[0] > 0 and C.observed_rate.iloc[2] >= 3 * C.observed_rate.iloc[0])

# ---------------------------------------------------------------- transfer check on our digitised ECGs (NOT outcome validation)
db = pd.read_csv(D.PT + "ptbxl_database.csv").set_index("ecg_id").sort_index()
X250 = I.load_ptbxl250(db)
pos = {e: n for n, e in enumerate(db.index)}
ds = D.digitised_sets()
Kdf = pd.read_csv(ROOT + "/results/intervals_ml/selected_K_100.csv")
items = [("drawn pages (dev: new100, F, G)", r.path, int(r.ecg_id)) for _, r in ds[ds.set == "T2"].iterrows()]
items += [("drawn pages (dev: K)", ROOT + f"/results/intervals_ml/K/k_digitized_12lead/{p}.npz", int(e)) for p, e in zip(Kdf.page, Kdf.ecg_id) if os.path.exists(ROOT + f"/results/intervals_ml/K/k_digitized_12lead/{p}.npz")]
items += [("real phone photos (dev)", r.path, int(r.ecg_id)) for _, r in ds[ds.set == "T3"].iterrows()]
selg = pd.read_csv(ROOT + "/results/fresh_g/selected_g_100.csv").set_index("page")
zz = pd.read_csv(ROOT + "/results/analysis/sectionZ_all.csv")
items += [("simulated photos (dev)", ROOT + f"/results/fresh_sim/dig_v2/{r.photo}.npz", int(selg.loc[r.page, "ecg_id"])) for _, r in zz[zz.variant == "v2"].iterrows() if os.path.exists(ROOT + f"/results/fresh_sim/dig_v2/{r.photo}.npz") and not r["none"]]
for tag, sel_csv, pat, label in (("L", "selected_L_100.csv", "L/l_digitized_12lead/*.npz", "drawn pages (fresh L)"), ("M", "selected_M_100.csv", "M/m_digitized_12lead/*.npz", "drawn pages (fresh M)"),
                                 ("L", "selected_L_100.csv", "L_sim/dig_v2/*.npz", "simulated photos (fresh L)"), ("M", "selected_M_100.csv", "M_sim/dig_v2/*.npz", "simulated photos (fresh M)")):
    s = pd.read_csv(ROOT + "/results/intervals_ml/" + sel_csv).set_index("page")
    for f in sorted(glob.glob(ROOT + "/results/intervals_ml/" + pat)):
        pg = os.path.basename(f)[:4]
        if pg in s.index:
            items.append((label, f, int(s.loc[pg, "ecg_id"])))
sys.path.insert(0, ROOT + "/scripts/analysis")
import h2_photos  # noqa: E402

_hp, _hi, _hg = h2_photos.primary_items()
hf = _hp if len(_hp) >= 10 else []
items += [("REAL printed-paper STRAIGHT photos (H2, friend's phone)", f, e) for f, e in zip(_hp, _hi)] if len(_hp) >= 10 else []
idf = pd.DataFrame(items, columns=["group", "path", "ecg_id"])
orig = prob_from_raw(np.stack([np.asarray(X250[pos[e]], np.float32) for e in idf.ecg_id]))[0]
dig = prob_from_x24(np.stack([I.digitised_to_input250({k: v.astype(float) for k, v in np.load(p).items()}) for p in idf.path]))
cat_o = np.where(orig < 0.01, 0, np.where(orig < 0.03, 1, 2))
cat_d = np.where(dig < 0.01, 0, np.where(dig < 0.03, 1, 2))
tr_rows = []
for g, sub in idf.groupby("group", sort=False):
    ix = sub.index.values
    tr_rows.append(dict(group=g, n=len(ix), spearman=float(spearmanr(orig[ix], dig[ix])[0]), mean_abs_diff=float(np.mean(np.abs(orig[ix] - dig[ix]))), mean_orig=float(orig[ix].mean()), mean_dig=float(dig[ix].mean()),
                        same_category=float(np.mean(cat_o[ix] == cat_d[ix]))))
TR = pd.DataFrame(tr_rows)
TR.to_csv(OUT + f"risk_transfer_{TAG}.csv", index=False)
pd.DataFrame(dict(group=idf.group, ecg_id=idf.ecg_id, risk_original=orig, risk_digitised=dig)).to_csv(OUT + f"risk_transfer_items_{TAG}.csv", index=False)
photo_groups = TR[TR.group.str.contains("photo")]
page_groups = TR[TR.group.str.contains("pages")]
transfer_pages = bool(len(page_groups) and (page_groups.spearman >= 0.85).all() and (page_groups.same_category >= 0.80).all())
transfer_photos = bool(len(photo_groups) and (photo_groups.spearman >= 0.85).all() and (photo_groups.same_category >= 0.80).all() and any(photo_groups.group.str.startswith("REAL")))
e = T.iloc[0]
status = dict(horizon_years=H, auroc=e.auroc, auroc_lo95=e.lo95, cal_slope=e.cal_slope, ece=e.ece, categories_monotone=mono, high_over_low_ratio_ok=ratio_ok,
              pass_discrimination=bool(e.auroc >= 0.75 and e.lo95 > 0.70), pass_calibration=bool(0.8 <= e.cal_slope <= 1.25 and e.ece <= 0.02), pass_categories=bool(ratio_ok),
              transfer_pages_ok=transfer_pages, transfer_photos_ok=transfer_photos, real_photos_available=bool(len(hf) >= 10))
status["shown_in_app"] = bool(status["pass_discrimination"] and status["pass_calibration"] and status["pass_categories"] and transfer_pages and transfer_photos)
json.dump(status, open(OUT + f"risk_status_{TAG}.json", "w"), indent=1)

md = [f"# Section RISK: ECG-estimated all-cause mortality risk, horizon {H:g} year, test once (PILOT; rules logged before any model was trained)", "",
      "Rules: `docs/plan/analysis_plan_changes.md` ('ECG-estimated mortality RISK PILOT'). Data: CODE-15% (open, CC-BY 4.0), patients with an outcome, 10 s recordings, ECG only (no age or sex). Categories and pass rules are the assistant's proposal, not approved by the guide. "
      "All-cause mortality, not cardiac events; one Brazilian primary-care source; largely driven by age. The transfer check is NOT outcome validation.", "",
      "## Test split (untouched until this run)", "", "| Model | n | Events | AUROC (95% interval) | AUPRC | Brier | ECE | Calibration slope |", "|---|---|---|---|---|---|---|---|"]
for _, r in T.iterrows():
    md.append(f"| {r['item']} | {int(r.n)} | {int(r.events)} | {r.auroc:.3f} ({r.lo95:.3f} to {r.hi95:.3f}) | " + (f"{r.auprc:.3f} | {r.brier:.4f} | {r.ece:.4f} | " if pd.notna(r.get('auprc')) else "| | | ") + (f"{r.cal_slope:.2f}" if pd.notna(r.get('cal_slope')) else "") + " |")
md += ["", "## Categories on the test split (proposal: Low < 1%, Moderate 1% to < 3%, High 3% or more)", "", "| Category | Patients | Events | Observed rate | Mean predicted |", "|---|---|---|---|---|"]
for _, r in C.iterrows():
    md.append(f"| {r.category} | {r.patients} | {r.events} | {100 * r.observed_rate:.2f}% | {100 * r.mean_predicted:.2f}% |")
md += ["", "Deciles of predicted risk:", "", "| Decile | Mean predicted | Observed | n |", "|---|---|---|---|"]
for k, r in dec.iterrows():
    md.append(f"| {k} | {100 * r.predicted:.2f}% | {100 * r.observed:.2f}% | {int(r.n)} |")
md += ["", "## Transfer check: the same ECG, original signal against its digitised version (no outcomes exist for these ECGs)", "", "| Group | n | Spearman | Mean absolute difference | Mean risk original | Mean risk digitised | Same category |", "|---|---|---|---|---|---|---|"]
for _, r in TR.iterrows():
    md.append(f"| {r.group} | {r.n} | {r.spearman:.2f} | {100 * r.mean_abs_diff:.2f} points | {100 * r.mean_orig:.2f}% | {100 * r.mean_dig:.2f}% | {100 * r.same_category:.0f}% |")
md += ["", "## Verdict (pass rules applied)", "", "| Rule | Result |", "|---|---|", f"| AUROC at least 0.75, lower end above 0.70 | {status['pass_discrimination']} |", f"| Calibration slope 0.8 to 1.25 and ECE at most 0.02 | {status['pass_calibration']} |",
       f"| Observed rates increase across Low, Moderate, High and High is at least 3 times Low | {status['pass_categories']} |", f"| Transfer check on digitised drawn pages (Spearman at least 0.85, at least 80% same category) | {status['transfer_pages_ok']} |",
       f"| Transfer check on photos incl. REAL printed-paper photos | {status['transfer_photos_ok']} (real photos available: {status['real_photos_available']}) |", f"| **Shown in the app** | **{status['shown_in_app']}** |"]
open(OUT + f"SECTION_RISK_{TAG}.md", "w", encoding="utf-8").write("\n".join(md) + "\n")
print("\n".join(md))
