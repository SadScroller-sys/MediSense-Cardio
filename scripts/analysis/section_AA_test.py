"""Section AA: freeze the digitised-input offsets (--freeze, development pages only) and test the frozen model ONCE (--test).
Rules: docs/plan/analysis_plan_changes.md, 2026-11-15 "Section AA". --freeze fits ONE offset per target on the digitised development pages (new 100 and fresh F, clean) and writes offsets_digitised.json.
--test refuses to run twice. Tests: T1 fold 10 originals (information), T2 primary = sealed K pages, T2b = sealed G pages, T3 = 140 straightened phone photos.
Usage: demo\\.venv-gpu\\Scripts\\python.exe scripts/analysis/section_AA_test.py --freeze   then   ... --test"""
import json
import os
import sys

import numpy as np
import pandas as pd
import torch

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "demo"))
from health import data as D  # noqa: E402
from health import intervals_ml as I  # noqa: E402

dev = "cuda" if torch.cuda.is_available() else "cpu"
cal = json.load(open(I.OUT + "calibration.json"))
mu, sd = np.array(cal["mu"]), np.array(cal["sd"])
off_orig = np.array(cal["fold9_original"]["bias"])
net = I.IntervalNet().to(dev)
net.load_state_dict(torch.load(I.OUT + "model.pt", map_location=dev))
net.eval()
db = pd.read_csv(D.PT + "ptbxl_database.csv").set_index("ecg_id").sort_index()
x12 = pd.read_csv(ROOT + "/data/ptbxl_plus/12sl_features.csv").set_index("ecg_id")
Kdf = pd.read_csv(I.OUT + "selected_K_100.csv")
rng = np.random.RandomState(55)
B = 2000


@torch.no_grad()
def predict(X24):
    out = []
    for i in range(0, len(X24), 128):
        out.append(net(torch.from_numpy(np.ascontiguousarray(X24[i:i + 128])).to(dev)).cpu().numpy())
    return (np.concatenate(out) * sd + mu) - off_orig         # model output minus the original-signal offset (fold 9)


def digitised_items(df, hr=True):
    """df rows (path, ecg_id, group, name) -> inputs (N, 24, 2500) and the heart rate of each (cleaned measure of the app)."""
    from pipeline import hr_clean
    Xs, hrs = [], []
    for p in df.path:
        z = np.load(p)
        leads = {k: z[k].astype(float) for k in z.files}
        Xs.append(I.digitised_to_input250(leads))
        h = float("nan")
        if hr and "II" in leads:
            try:
                h, _ = hr_clean(leads["II"] / 1000.0, 1000)
            except Exception:
                pass
        hrs.append(h)
    return np.stack(Xs), np.array(hrs)


ds = D.digitised_sets()
dev_df = ds[(ds.set == "T2") & ds.source.isin(["new100", "fresh F"])].reset_index(drop=True)
g_df = ds[(ds.set == "T2") & (ds.source == "sealed G")].reset_index(drop=True)
t3_df = ds[ds.set == "T3"].reset_index(drop=True)
k_df = pd.DataFrame(dict(name=Kdf.page, ecg_id=Kdf.ecg_id, group=Kdf.page, path=[I.OUT.replace("\\", "/") + f"K/k_digitized_12lead/{p}.npz" for p in Kdf.page]))
k_df = k_df[[os.path.exists(p) for p in k_df.path]].reset_index(drop=True)

if "--freeze" in sys.argv:
    Xd, _ = digitised_items(dev_df, hr=False)
    P = predict(Xd)
    T = x12.loc[dev_df.ecg_id, I.TARGETS].values
    ok = np.isfinite(P).all(1) & np.isfinite(T).all(1)
    off = (P[ok] - T[ok]).mean(0)
    json.dump(dict(offset_digitised=off.tolist(), n_dev_pages=int(ok.sum()), note="fitted once on the clean digitised development pages (new 100 and fresh F); subtract from the model output"), open(I.OUT + "offsets_digitised.json", "w"), indent=1)
    print("digitised offsets (QRS, QT) ms:", off.round(2), "from", int(ok.sum()), "pages")
    sys.exit(0)

OUTF = I.OUT + "aa_test_per_item.csv"
if os.path.exists(OUTF) and "--force" not in sys.argv:
    sys.exit("The test was already run once (rule: run ONCE).")
off_dig = np.array(json.load(open(I.OUT + "offsets_digitised.json"))["offset_digitised"])
excl = D.excluded_ids() | set(Kdf.ecg_id)
f10 = db.index[(db.strat_fold.values == 10) & ~db.index.isin(excl)]
f10 = [i for i in f10 if np.isfinite(x12.loc[i, I.TARGETS].values.astype(float)).all()]
Xall = I.load_ptbxl250(db)
pos = {e: n for n, e in enumerate(db.index)}
mask = I.layout_masks("cpu")
X1 = np.stack([I.make_input(torch.from_numpy(np.asarray(Xall[pos[i]], np.float32))[None], mask, False)[0].numpy() for i in f10])
P1 = predict(X1)
sets = {}
sets["T1 fold 10 originals (benchmark)"] = dict(ids=np.array(f10), P=P1, hr=x12.loc[f10, "HR_Ventr_Global"].values.astype(float), groups=np.array(f10), name=np.array(f10).astype(str), digitised=False)
for tag, df in (("T2 primary: sealed K pages", k_df), ("T2b: sealed G pages", g_df), ("T3: straightened phone photos", t3_df)):
    Xd, hrs = digitised_items(df)
    sets[tag] = dict(ids=df.ecg_id.values, P=predict(Xd) - off_dig, hr=hrs, groups=df.group.values, name=df.name.values, digitised=True)


def slope(t, p):
    return float(np.polyfit(t, p, 1)[0])


def metrics(true, pred, groups, tol):
    ok = np.isfinite(pred)
    n = len(true)
    t, p, g = true[ok], pred[ok], groups[ok]
    e = p - t
    d = dict(n=n, with_value=float(ok.mean()))
    if ok.sum() < 5:
        return d
    d.update(typical=float(np.median(np.abs(e))), within=float(np.mean(np.abs(e) <= tol)), bias=float(e.mean()), slope=slope(t, p))
    uniq = pd.unique(g)
    idx = {u: np.flatnonzero(g == u) for u in uniq}
    bb, ss = [], []
    for _ in range(B):
        ix = np.concatenate([idx[uniq[j]] for j in rng.choice(len(uniq), len(uniq), replace=True)])
        bb.append(e[ix].mean())
        ss.append(slope(t[ix], p[ix]))
    d.update(bias_lo=float(np.percentile(bb, 2.5)), bias_hi=float(np.percentile(bb, 97.5)), slope_lo=float(np.percentile(ss, 2.5)), slope_hi=float(np.percentile(ss, 97.5)))
    return d


def tail(true, pred, lo=None, hi=None):
    m = np.isfinite(pred) & ((true >= hi) if hi is not None else (true <= lo))
    return (int(m.sum()), float((pred[m] - true[m]).mean())) if m.sum() >= 3 else (int(m.sum()), float("nan"))


RULES = {"QRS": dict(col="QRS_Dur_Global", tol=20, typical=10, within=0.90, bias=5, slope=0.8, tails=[("hi", 120, 20)]),
         "QT": dict(col="QT_Int_Global", tol=40, typical=20, within=0.90, bias=10, slope=0.8, tails=[("hi", 450, 25), ("lo", 350, 25)]),
         "QTc (Fridericia)": dict(col="QT_IntFridericia_Global", tol=50, typical=25, within=0.90, bias=10, slope=0.8, tails=[])}
rows, items = [], []
af_ids = {i for i in db.index if any(k in str(db.loc[i, "scp_codes"]) for k in ("AFIB", "AFLT"))}
for sname, s in sets.items():
    ids = s["ids"]
    qt, qrs = s["P"][:, 1], s["P"][:, 0]
    rr = 60000.0 / s["hr"]
    qtc = qt / (rr / 1000.0) ** (1 / 3)
    preds = {"QRS": qrs, "QT": qt, "QTc (Fridericia)": qtc}
    for pname, r in RULES.items():
        true = x12.loc[ids, r["col"]].values.astype(float)
        pr = preds[pname]
        m = metrics(true, pr, s["groups"], r["tol"])
        tails = {f"{k}{th}": tail(true, pr, **({"hi": th} if k == "hi" else {"lo": th})) for k, th, _ in r["tails"]}
        passed = bool(m.get("with_value", 0) >= 0.90 and m.get("typical", 1e9) <= r["typical"] and m.get("within", 0) >= r["within"] and abs(m.get("bias", 1e9)) <= r["bias"] and m.get("slope", 0) >= r["slope"]
                      and all(np.isfinite(tails[f"{k}{th}"][1]) and abs(tails[f"{k}{th}"][1]) <= lim for k, th, lim in r["tails"]))
        af = np.array([i in af_ids for i in ids])
        afm = np.isfinite(pr) & af
        rows.append(dict(set=sname, parameter=pname, passed_all_rules=passed, **m, **{f"tail_{k}_n": v[0] for k, v in tails.items()}, **{f"tail_{k}_mean_error": v[1] for k, v in tails.items()},
                         af_n=int(afm.sum()), af_bias=float((pr[afm] - true[afm]).mean()) if afm.sum() >= 3 else float("nan")))
        for i in range(len(ids)):
            items.append(dict(set=sname, name=s["name"][i], ecg_id=ids[i], parameter=pname, true=true[i], pred=pr[i], hr=s["hr"][i]))
pd.DataFrame(items).to_csv(OUTF, index=False)
R = pd.DataFrame(rows)
R.to_csv(I.OUT + "aa_test_metrics.csv", index=False)

status = {}
for pname in RULES:
    k = R[(R.parameter == pname) & R.set.str.startswith("T2 primary")].iloc[0]
    g = R[(R.parameter == pname) & R.set.str.startswith("T2b")].iloc[0]
    p3 = R[(R.parameter == pname) & R.set.str.startswith("T3")].iloc[0]
    contradicted = bool(k.passed_all_rules and (not np.isfinite(g.typical) or g.typical > RULES[pname]["typical"] or abs(g.bias) > RULES[pname]["bias"]))
    status[pname] = dict(passed_K=bool(k.passed_all_rules), passed_G=bool(g.passed_all_rules), contradicted_by_G=contradicted, passed_photos=bool(p3.passed_all_rules),
                         shown_in_app=bool(k.passed_all_rules and not contradicted and p3.passed_all_rules), af_bias_K=float(k.af_bias), needs_af_guard=bool(np.isfinite(k.af_bias) and abs(k.af_bias) > 25))
json.dump(status, open(I.OUT + "aa_status.json", "w"), indent=1)

md = ["# Section AA: learned QRS duration and QT/QTc, test once (EXPLORATORY; rules logged before any code ran)", "",
      "Rules: `docs/plan/analysis_plan_changes.md`, 'Section AA'. The pass thresholds are the assistant's proposal, not approved by the guide. Reference = 12SL. Digitised sets use the digitised-input offset fitted on the development pages. "
      "T2b (G pages) and T3 (phone photos) were used before for other methods; the new model was never tuned on them.", ""]
for sname in sets:
    md += [f"## {sname}", "", "| Parameter | n | With value | Typical error (ms) | Within tolerance | Bias ms (95% interval) | Slope on 12SL (95% interval) | Tails (n, mean error ms) | AF pages (n, bias) | All rules met |", "|---|---|---|---|---|---|---|---|---|---|"]
    for _, r in R[R.set == sname].iterrows():
        tl = "; ".join(f"{c.replace('tail_', '').replace('_n', '')}: {int(r[c])}, {r[c.replace('_n', '_mean_error')]:+.1f}" for c in R.columns if c.startswith("tail_") and c.endswith("_n") and np.isfinite(r[c]) and r[c] > 0)
        if "typical" in r and np.isfinite(r.typical):
            md.append(f"| {r.parameter} | {int(r.n)} | {r.with_value:.0%} | {r.typical:.1f} | {r.within:.0%} | {r.bias:+.1f} ({r.bias_lo:+.1f} to {r.bias_hi:+.1f}) | {r.slope:.2f} ({r.slope_lo:.2f} to {r.slope_hi:.2f}) | {tl} | {int(r.af_n)}, {r.af_bias:+.1f} | **{'YES' if r.passed_all_rules else 'no'}** |")
    md.append("")
md += ["## Verdict", "", "| Parameter | Passed on K | Passed on G | G contradicts | Passed on phone photos | Shown in the app | AF guard needed |", "|---|---|---|---|---|---|---|"]
for pn, s in status.items():
    md.append(f"| {pn} | {s['passed_K']} | {s['passed_G']} | {s['contradicted_by_G']} | {s['passed_photos']} | **{s['shown_in_app']}** | {s['needs_af_guard']} |")
md += ["", "Rules (same numbers as the earlier attempts): QT typical error at most 20 ms, at least 90% within 40 ms, |bias| at most 10 ms, slope at least 0.8, tails (QT at least 450 or at most 350 ms) |mean error| at most 25 ms; "
       "QRS typical error at most 10 ms, at least 90% within 20 ms, |bias| at most 5 ms, slope at least 0.8, true QRS at least 120 ms |mean error| at most 20 ms; QTc (Fridericia, with the heart rate of the same photo) typical error at most 25 ms, at least 90% within 50 ms, |bias| at most 10 ms, slope at least 0.8. At least 90% with a value."]
open(I.OUT + "SECTION_AA.md", "w", encoding="utf-8").write("\n".join(md) + "\n")
print("\n".join(md))
