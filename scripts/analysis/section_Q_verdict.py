"""Set Q verdict: the pass rule of docs/plan/analysis_plan_changes.md 2026-11-17 applied to results/paper_q/test_pages_metrics.csv and test_sim_metrics.csv for the decision pairs A2:LAFB, B2:AF, B2:LBBB.
AVAILABLE only if ALL hold: at least 20 positives; AUROC at least 0.80 with lower end above 0.70 on drawn pages AND at least 0.75 on simulated photos; sensitivity at least 0.60 and specificity at least 0.90 on simulated photos.
Writes results/paper_q/Q_status.json and SECTION_Q.md. Usage: python -I scripts/analysis/section_Q_verdict.py"""
import json
import os

import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
PQ = ROOT + "/results/paper_q/"
pg = pd.read_csv(PQ + "test_pages_metrics.csv").set_index("pair")
sm = pd.read_csv(PQ + "test_sim_metrics.csv").set_index("pair")
status = {}
for pair in pg.index:
    a, b = pg.loc[pair], sm.loc[pair]
    dec = a.role == "decision"
    ok_pg = bool(a.positives >= 20 and a.auroc >= 0.80 and a.lo95 > 0.70)
    ok_auc = bool(b.positives >= 20 and b.auroc >= 0.75)
    ok_op = bool(b.sensitivity >= 0.60 and b.specificity >= 0.90)
    avail = bool(dec and ok_pg and ok_auc and ok_op)
    if not dec:
        verdict = "descriptive only (first network)"
    elif avail:
        verdict = "AVAILABLE: validated on dataset pictures (drawn pages and simulated photos)"
    else:
        why = [w for w, f in (("the drawn-page rule", ok_pg), ("simulated-photo AUROC of 0.75", ok_auc), ("sensitivity 0.60 and specificity 0.90 on simulated photos", ok_op)) if not f]
        verdict = "stays research-only: fails " + "; ".join(why)
    status[pair] = dict(decision=bool(dec), pages_pos=int(a.positives), pages_auroc=float(a.auroc), pages_lo95=float(a.lo95), pages_sens=float(a.sensitivity), pages_spec=float(a.specificity),
                        sim_pos=int(b.positives), sim_auroc=float(b.auroc), sim_lo95=float(b.lo95), sim_sens=float(b.sensitivity), sim_spec=float(b.specificity), threshold=float(b.threshold),
                        pass_pages=ok_pg, pass_sim_auc=ok_auc, pass_sim_operating_point=ok_op, available=avail, verdict=verdict)
nrm = dict(pages=[int(pg.normal_pictures.iloc[0]), int(pg.normal_flagged_by_any_of_3.iloc[0])], sim=[int(sm.normal_pictures.iloc[0]), int(sm.normal_flagged_by_any_of_3.iloc[0])])
json.dump(dict(rule="docs/plan/analysis_plan_changes.md 2026-11-17", normal_pictures_flagged=nrm, pairs=status), open(PQ + "Q_status.json", "w"), indent=1)
md = ["# Section Q: retrained networks A2 and B2, fresh set Q, tested once", "",
      f"NORMAL pictures flagged by at least one of the three tested patterns: drawn pages {nrm['pages'][1]} of {nrm['pages'][0]}; simulated photos {nrm['sim'][1]} of {nrm['sim'][0]}.", "",
      "| Pair | Drawn pages: positives, AUROC (lower 95%), sens / spec | Simulated photos: positives, AUROC (lower 95%), sens / spec | Verdict |", "|---|---|---|---|"]
for pair, s in status.items():
    md.append(f"| {pair} | {s['pages_pos']}, {s['pages_auroc']:.3f} ({s['pages_lo95']:.3f}), {100 * s['pages_sens']:.0f} / {100 * s['pages_spec']:.0f} | {s['sim_pos']}, {s['sim_auroc']:.3f} ({s['sim_lo95']:.3f}), {100 * s['sim_sens']:.0f} / {100 * s['sim_spec']:.0f} | {s['verdict']} |")
open(PQ + "SECTION_Q.md", "w", encoding="utf-8").write("\n".join(md) + "\n")
print("\n".join(md))
