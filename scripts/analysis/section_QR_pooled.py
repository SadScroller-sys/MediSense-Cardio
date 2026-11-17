"""Pooled DESCRIPTIVE numbers for B2:LBBB and B2:AF over the two fresh sets Q (160 pictures) and R (120 pictures), computed from the stored one-time test predictions (no new model run, no new threshold).
Writes results/paper_r/final_status.json (what the app reads: pooled simulated-photo and drawn-page numbers; 'available' comes from the pre-set rule: LBBB passed on Q and again on R; AF passed on R, its second test after missing on Q)
and results/paper_r/POOLED_QR.md. Usage: demo\\.venv-gpu\\Scripts\\python.exe -I scripts/analysis/section_QR_pooled.py"""
import json
import os
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "demo"))
from health import data as D  # noqa: E402
from health import find2 as F  # noqa: E402

db, _ = D.load_db()
LAB = F.labels_B_from_ptbxl(db)
thr = json.load(open(ROOT + "/results/find2_B2/thresholds_q.json"))["thresholds"]
status = {"Q": json.load(open(ROOT + "/results/paper_q/Q_status.json"))["pairs"], "R": json.load(open(ROOT + "/results/paper_r/R_status.json"))["pairs"]}
out, md = {}, ["# Pooled over fresh sets Q and R (descriptive; the pass decisions were made on each set alone)", "", "| Pair | Part | Pictures | Positives | AUROC | Sensitivity | Specificity |", "|---|---|---|---|---|---|---|"]
for pair, c in (("B2:LBBB", "LBBB"), ("B2:AF", "AF")):
    res = {}
    for part, fn in (("pages", "test_pages_predictions.csv"), ("sim", "test_sim_predictions.csv")):
        frames = []
        for tag in ("paper_q", "paper_r"):
            sel = pd.read_csv(ROOT + f"/results/{tag}/selected_{'Q' if tag == 'paper_q' else 'R'}.csv").set_index("page")
            pr = pd.read_csv(ROOT + f"/results/{tag}/{fn}")
            pr["ecg_id"] = sel.loc[pr["page"], "ecg_id"].astype(int).values
            frames.append(pr)
        pr = pd.concat(frames)
        y = LAB[c].loc[pr.ecg_id].values > 0
        p = pr["B2_" + c].values
        fl = p >= thr[pair]["s97"]
        res[part] = dict(n=int(len(y)), positives=int(y.sum()), auroc=float(roc_auc_score(y, p)), sens=float(fl[y].mean()), spec=float((~fl[~y]).mean()))
        md.append(f"| {pair} | {part} | {res[part]['n']} | {res[part]['positives']} | {res[part]['auroc']:.3f} | {100 * res[part]['sens']:.0f} | {100 * res[part]['spec']:.0f} |")
    avail = bool(status["R"][pair]["available"] and (status["Q"][pair]["available"] if c == "LBBB" else True))
    out[pair] = dict(available=avail, decision=True, sim_auroc=res["sim"]["auroc"], sim_sens=res["sim"]["sens"], sim_spec=res["sim"]["spec"], sim_pos=res["sim"]["positives"],
                     pages_auroc=res["pages"]["auroc"], pages_sens=res["pages"]["sens"], pages_spec=res["pages"]["spec"],
                     basis="LBBB: passed the pre-set rule on set Q and again on set R. AF: missed on set Q (specificity 89.3), passed on set R (second test). Numbers shown are pooled over Q and R.")
json.dump(dict(pairs=out), open(ROOT + "/results/paper_r/final_status.json", "w"), indent=1)
open(ROOT + "/results/paper_r/POOLED_QR.md", "w", encoding="utf-8").write("\n".join(md) + "\n")
print("\n".join(md))
print({k: v["available"] for k, v in out.items()})
