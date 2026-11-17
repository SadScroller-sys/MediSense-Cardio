"""Applies the user's decision of 2026-11-16 (late night): the 7 research-only patterns use the specificity-0.97 thresholds derived from validation data (section_OP_thresholds.py), NDT is dropped from the block (POST HOC exception to the rule
that no pattern may lose more than half of its sensitivity on drawn pages; logged in docs/plan/analysis_plan_changes.md). Computes, for the 7 patterns, the share of clean items flagged on the sets seen before, and writes
results/find2_op/app_operating_point.json (thresholds, sensitivity and specificity for the notes of the app) and op7_aggregate.csv. Usage: demo\\.venv-gpu\\Scripts\\python.exe -I scripts/analysis/section_OP_apply.py"""
import json
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "demo"))
from health import data as D  # noqa: E402
from health import find2 as F  # noqa: E402

OP = ROOT + "/results/find2_op/"
thr = json.load(open(OP + "thresholds_v2.json"))["thresholds"]
PAT = [("A", "ASMI"), ("A", "LVH"), ("A", "LAFB"), ("A", "IRBBB"), ("B", "AF"), ("B", "LBBB"), ("B", "1dAVb")]            # NDT dropped
db, _ = D.load_db()
LAB = {"A": F.labels_A(db), "B": F.labels_B_from_ptbxl(db)}
selN = pd.read_csv(ROOT + "/results/paper_n/selected_N.csv").set_index("page")
sets = {"T2 drawn pages": (pd.read_csv(F.OUT_A + "predictions_T2.csv"), pd.read_csv(F.OUT_B + "predictions_T2.csv"))}
sets["T3 screen photos"] = (pd.read_csv(F.OUT_A + "predictions_T3.csv"), pd.read_csv(F.OUT_B + "predictions_T3.csv"))
for tag, f in (("set N drawn pages", "test_pages_predictions.csv"), ("set N simulated photos", "test_sim_predictions.csv")):
    d = pd.read_csv(ROOT + "/results/paper_n/" + f)
    d["ecg_id"] = d.page.map(selN.ecg_id)
    sets[tag] = (d[["ecg_id"] + [c for c in d.columns if c.startswith("A_")]].rename(columns=lambda c: c[2:] if c.startswith("A_") else c),
                 d[["ecg_id"] + [c for c in d.columns if c.startswith("B_")]].rename(columns=lambda c: c[2:] if c.startswith("B_") else c))
rows, per = [], {}
for sname, (a, b) in sets.items():
    ids = a["ecg_id"].astype(int).values
    ys = {f"{m}:{c}": LAB[m][c].loc[ids].values > 0 for m, c in PAT}
    pos_any = np.any(list(ys.values()), axis=0)
    for vname, key in (("old Youden", "old_youden"), ("new, specificity 0.97 (used)", "s97")):
        flags = {f"{m}:{c}": (a if m == "A" else b)[c].astype(float).values >= thr[f"{m}:{c}"][key] for m, c in PAT}
        anyfl = np.any(list(flags.values()), axis=0)
        rows.append(dict(set=sname, variant=vname, items=len(ids), clean_items=int((~pos_any).sum()), clean_flagged=int(anyfl[~pos_any].sum()), clean_flagged_pct=100 * float(anyfl[~pos_any].mean()),
                         flags_per_clean_item=float(np.sum(list(flags.values()), axis=0)[~pos_any].mean()), pattern_items=int(pos_any.sum()), pattern_items_flagged=int(anyfl[pos_any].sum()), pattern_items_flagged_pct=100 * float(anyfl[pos_any].mean())))
        if key == "s97":
            for k, fl in flags.items():
                y = ys[k]
                per.setdefault(k, {})[sname] = dict(positives=int(y.sum()), sens=float(fl[y].mean()) if y.any() else None, spec=float((~fl[~y]).mean()))
G = pd.DataFrame(rows)
G.to_csv(OP + "op7_aggregate.csv", index=False)
app = {}
for m, c in PAT:
    k = f"{m}:{c}"
    n_tested = k in ("A:LVH", "A:LAFB", "B:AF", "B:LBBB", "B:1dAVb")
    pages = per[k]["set N drawn pages"] if n_tested else per[k]["T2 drawn pages"]            # set N has more positives for the patterns it was built for
    sim = per[k]["set N simulated photos"] if n_tested else None
    app[k] = dict(threshold=thr[k]["s97"], pages_set="set N drawn pages (120)" if n_tested else "T2 drawn pages (300)", pages_positives=pages["positives"], pages_sens=pages["sens"], pages_spec=pages["spec"],
                  sim_sens=sim["sens"] if sim else None, sim_spec=sim["spec"] if sim else None, sim_positives=sim["positives"] if sim else None)
new = G[G.variant.str.startswith("new")].set_index("set")
json.dump(dict(rule="docs/plan/analysis_plan_changes.md 2026-11-16 late night + user decision (NDT dropped, post hoc)", patterns=app,
               clean_flagged_pct=dict(drawn_pages=float(new.loc["T2 drawn pages", "clean_flagged_pct"]), screen_photos=float(new.loc["T3 screen photos", "clean_flagged_pct"])),
               clean_flagged=dict(drawn_pages=[int(new.loc["T2 drawn pages", "clean_flagged"]), int(new.loc["T2 drawn pages", "clean_items"])], screen_photos=[int(new.loc["T3 screen photos", "clean_flagged"]), int(new.loc["T3 screen photos", "clean_items"])])),
          open(OP + "app_operating_point.json", "w"), indent=1)
print(G[["set", "variant", "clean_items", "clean_flagged", "clean_flagged_pct", "pattern_items", "pattern_items_flagged", "pattern_items_flagged_pct", "flags_per_clean_item"]].round(1).to_string(index=False))
