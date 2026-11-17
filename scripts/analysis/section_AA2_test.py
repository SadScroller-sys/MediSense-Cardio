"""Section AA second attempt: test the FROZEN fine-tuned model ONCE on fresh data (rules: docs/plan/analysis_plan_changes.md, 2026-11-15 evening).
Fresh tests: L pages (100 new recordings, digitised drawn pages), L simulated photos (100, straightened, a SIMULATION), H real photos (40 photos of the printed pages H01-H20, if provided).
A parameter is shown in the app only if it passes on the L pages AND on the REAL H2 photos; the simulated photos must not contradict. Refuses to run twice.
Usage: demo\\.venv-gpu\\Scripts\\python.exe scripts/analysis/section_AA2_test.py"""
import glob
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

OUTF = I.OUT + "aa2_test_per_item.csv"
if os.path.exists(OUTF) and "--force" not in sys.argv:
    sys.exit("The test was already run once (rule: run ONCE).")
dev = "cuda" if torch.cuda.is_available() else "cpu"
cal = json.load(open(I.OUT + "calibration_aa2.json"))
MU, SD = np.array(cal["mu"]), np.array(cal["sd"])
net = I.IntervalNet(n_out=3).to(dev)
net.load_state_dict(torch.load(I.OUT + "model_aa2.pt", map_location=dev))
net.eval()
x12 = pd.read_csv(ROOT + "/data/ptbxl_plus/12sl_features.csv").set_index("ecg_id")
db = pd.read_csv(D.PT + "ptbxl_database.csv").set_index("ecg_id")
COLS = ["QRS_Dur_Global", "QT_Int_Global", "QT_IntFridericia_Global"]
NAMES = ["QRS", "QT", "QTc (Fridericia, direct)"]
rng = np.random.RandomState(59)
B = 2000
af_ids = {i for i in db.index if any(k in str(db.loc[i, "scp_codes"]) for k in ("AFIB", "AFLT"))}


@torch.no_grad()
def predict(paths):
    X = np.stack([I.digitised_to_input250({k: v.astype(float) for k, v in np.load(p).items()}) for p in paths])
    out = []
    for i in range(0, len(X), 64):
        out.append(net(torch.from_numpy(X[i:i + 64]).to(dev)).cpu().numpy())
    return np.concatenate(out) * SD + MU


L = pd.read_csv(I.OUT + "selected_L_100.csv")
sets = {}
l_items = [(p, e) for p, e in zip(L.page, L.ecg_id) if os.path.exists(I.OUT + f"L/l_digitized_12lead/{p}.npz")]
sets["L pages (fresh, digitised drawn pages)"] = dict(paths=[I.OUT + f"L/l_digitized_12lead/{p}.npz" for p, _ in l_items], ids=np.array([e for _, e in l_items]), groups=np.array([p for p, _ in l_items]))
sp = [(f, os.path.basename(f)[:4], int(L.set_index("page").loc[os.path.basename(f)[:4], "ecg_id"])) for f in sorted(glob.glob(I.OUT + "L_sim/dig_v2/*.npz"))]
sets["L simulated photos (a simulation)"] = dict(paths=[f for f, _, _ in sp], ids=np.array([e for _, _, e in sp]), groups=np.array([p for _, p, _ in sp]))
sys.path.insert(0, ROOT + "/scripts/analysis")
import h2_photos  # noqa: E402

_hp, _hi, _hg = h2_photos.primary_items()
if len(_hp) >= 30:           # set H2: full-resolution printed-paper photos taken by the user's friend (different phone), straightened variant V2b
    sets["H2 real photos (printed paper, friend's phone)"] = dict(paths=_hp, ids=np.array(_hi), groups=np.array(_hg))
else:
    print("H2 photos not available (fewer than 30 digitised): the real-photo condition cannot be met", flush=True)


def metrics(true, pred, groups, tol):
    ok = np.isfinite(pred)
    d = dict(n=len(true), with_value=float(ok.mean()))
    t, p, g = true[ok], pred[ok], groups[ok]
    e = p - t
    d.update(typical=float(np.median(np.abs(e))), within=float(np.mean(np.abs(e) <= tol)), bias=float(e.mean()), slope=float(np.polyfit(t, p, 1)[0]))
    uniq = pd.unique(g)
    idx = {u: np.flatnonzero(g == u) for u in uniq}
    bb, ss = [], []
    for _ in range(B):
        ix = np.concatenate([idx[uniq[j]] for j in rng.choice(len(uniq), len(uniq), replace=True)])
        bb.append(e[ix].mean())
        ss.append(np.polyfit(t[ix], p[ix], 1)[0])
    d.update(bias_lo=float(np.percentile(bb, 2.5)), bias_hi=float(np.percentile(bb, 97.5)), slope_lo=float(np.percentile(ss, 2.5)), slope_hi=float(np.percentile(ss, 97.5)))
    return d


def tail(true, pred, lo=None, hi=None):
    m = np.isfinite(pred) & ((true >= hi) if hi is not None else (true <= lo))
    return (int(m.sum()), float((pred[m] - true[m]).mean())) if m.sum() >= 3 else (int(m.sum()), float("nan"))


RULES = [dict(tol=20, typical=10, within=0.90, bias=5, tails=[("hi", 120, 20)]), dict(tol=40, typical=20, within=0.90, bias=10, tails=[("hi", 450, 25), ("lo", 350, 25)]),
         dict(tol=50, typical=25, within=0.90, bias=10, tails=[])]
rows, items = [], []
for sname, s in sets.items():
    P = predict(s["paths"])
    for j, (pn, col) in enumerate(zip(NAMES, COLS)):
        r = RULES[j]
        true = x12.loc[s["ids"], col].values.astype(float)
        pr = P[:, j]
        m = metrics(true, pr, s["groups"], r["tol"])
        tails = {f"{k}{th}": tail(true, pr, **({"hi": th} if k == "hi" else {"lo": th})) for k, th, _ in r["tails"]}
        passed = bool(m["with_value"] >= 0.90 and m["typical"] <= r["typical"] and m["within"] >= r["within"] and abs(m["bias"]) <= r["bias"] and m["slope"] >= 0.8
                      and all(np.isfinite(tails[f"{k}{th}"][1]) and abs(tails[f"{k}{th}"][1]) <= lim for k, th, lim in r["tails"]))
        af = np.array([i in af_ids for i in s["ids"]])
        afm = np.isfinite(pr) & af
        rows.append(dict(set=sname, parameter=pn, passed_all_rules=passed, **m, **{f"tail_{k}_n": v[0] for k, v in tails.items()}, **{f"tail_{k}_mean_error": v[1] for k, v in tails.items()},
                         af_n=int(afm.sum()), af_bias=float((pr[afm] - true[afm]).mean()) if afm.sum() >= 3 else float("nan")))
        for i in range(len(true)):
            items.append(dict(set=sname, name=os.path.basename(s["paths"][i]), ecg_id=s["ids"][i], parameter=pn, true=true[i], pred=pr[i]))
pd.DataFrame(items).to_csv(OUTF, index=False)
R = pd.DataFrame(rows)
R.to_csv(I.OUT + "aa2_test_metrics.csv", index=False)
status = {}
for j, pn in enumerate(NAMES):
    g = lambda key: R[(R.parameter == pn) & R.set.str.startswith(key)]  # noqa: E731
    l_ = g("L pages").iloc[0]
    sim = g("L simulated").iloc[0]
    h_ = g("H2 real")
    contra = bool(l_.passed_all_rules and (sim.typical > RULES[j]["typical"] or abs(sim.bias) > RULES[j]["bias"]))
    status[pn] = dict(passed_L_pages=bool(l_.passed_all_rules), passed_L_sim=bool(sim.passed_all_rules), sim_contradicts=contra,
                      passed_H_real=bool(h_.iloc[0].passed_all_rules) if len(h_) else None, shown_in_app=bool(l_.passed_all_rules and not contra and len(h_) and h_.iloc[0].passed_all_rules),
                      af_bias_L=float(l_.af_bias), needs_af_guard=bool(np.isfinite(l_.af_bias) and abs(l_.af_bias) > 25))
json.dump(status, open(I.OUT + "aa2_status.json", "w"), indent=1)
md = ["# Section AA second attempt: fine-tuned learned model, test once on FRESH data (EXPLORATORY; rules logged before any code of this attempt ran)", "",
      "Rules: `docs/plan/analysis_plan_changes.md` (2026-11-15 evening). The thresholds are the assistant's proposal, not approved by the guide. Reference = 12SL. Fine-tuned on development data only (cross-validated); L pages, L simulated photos and H photos were never used for training or choosing anything.", ""]
for sname in sets:
    md += [f"## {sname}", "", "| Parameter | n | With value | Typical error (ms) | Within tolerance | Bias ms (95% interval) | Slope on 12SL (95% interval) | Tails (n, mean error ms) | AF (n, bias) | All rules met |", "|---|---|---|---|---|---|---|---|---|---|"]
    for _, r in R[R.set == sname].iterrows():
        tl = "; ".join(f"{c.replace('tail_', '').replace('_n', '')}: {int(r[c])}, {r[c.replace('_n', '_mean_error')]:+.1f}" for c in R.columns if c.startswith("tail_") and c.endswith("_n") and np.isfinite(r[c]) and r[c] > 0)
        md.append(f"| {r.parameter} | {int(r.n)} | {r.with_value:.0%} | {r.typical:.1f} | {r.within:.0%} | {r.bias:+.1f} ({r.bias_lo:+.1f} to {r.bias_hi:+.1f}) | {r.slope:.2f} ({r.slope_lo:.2f} to {r.slope_hi:.2f}) | {tl} | {int(r.af_n)}, {r.af_bias:+.1f} | **{'YES' if r.passed_all_rules else 'no'}** |")
    md.append("")
md += ["## Verdict", "", "| Parameter | Passed on L pages | Passed on L simulated photos | Simulation contradicts | Passed on REAL H photos | Shown in the app |", "|---|---|---|---|---|---|"]
for pn, s in status.items():
    md.append(f"| {pn} | {s['passed_L_pages']} | {s['passed_L_sim']} | {s['sim_contradicts']} | {s['passed_H_real']} | **{s['shown_in_app']}** |")
md += ["", "A parameter is shown in the app only if it passes on the L pages and on the REAL H photos (printed paper, real phone); H photos not provided = not shown."]
open(I.OUT + "SECTION_AA2.md", "w", encoding="utf-8").write("\n".join(md) + "\n")
print("\n".join(md))
