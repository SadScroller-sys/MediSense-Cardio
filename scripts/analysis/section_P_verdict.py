"""Set P verdict: applies the pass rule logged in docs/plan/analysis_plan_changes.md (2026-11-16 late night, 'FRESH POSITIVE-RICH DATASET SET P') to results/paper_p/test_pages_metrics.csv and test_sim_metrics.csv.
A pair of the research-only block is AVAILABLE (validated on dataset pictures) only if ALL hold: at least 20 positives; AUROC at least 0.80 with lower end above 0.70 on the drawn pages AND at least 0.75 on the simulated photos; at the frozen 0.97 threshold sensitivity
at least 0.60 and specificity at least 0.90 on the simulated photos. A pair that fails the drawn-page rule is removed from the block; otherwise it stays research-only. A:1AVB and B:RBBB are descriptive only (not in the block, never promoted).
Writes results/paper_p/P_status.json and SECTION_P.md. Usage: python -I scripts/analysis/section_P_verdict.py"""
import json
import os

import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
PP = ROOT + "/results/paper_p/"
pg = pd.read_csv(PP + "test_pages_metrics.csv").set_index("pair")
sm = pd.read_csv(PP + "test_sim_metrics.csv").set_index("pair")
BLOCK = ["A:LVH", "A:LAFB", "A:IRBBB", "B:AF", "B:LBBB", "B:1dAVb"]
status = {}
for pair in pg.index:
    a, b = pg.loc[pair], sm.loc[pair]
    ok_pg = bool(a.positives >= 20 and a.auroc >= 0.80 and a.lo95 > 0.70)
    ok_auc_sm = bool(b.positives >= 20 and b.auroc >= 0.75)
    ok_op_sm = bool(b.sensitivity >= 0.60 and b.specificity >= 0.90)
    promotable = pair in BLOCK
    if not promotable:
        verdict = "descriptive only (not in the block, never promoted)"
    elif not ok_pg:
        verdict = "FAILS the drawn-page rule: removed from the research-only block"
    elif ok_auc_sm and ok_op_sm:
        verdict = "AVAILABLE: validated on dataset pictures (drawn pages and simulated photos)"
    else:
        why = []
        if not ok_auc_sm:
            why.append("simulated-photo AUROC below 0.75")
        if not ok_op_sm:
            why.append("sensitivity below 0.60 or specificity below 0.90 on simulated photos")
        verdict = "stays research-only: " + "; ".join(why)
    status[pair] = dict(promotable=promotable, pages_pos=int(a.positives), pages_auroc=float(a.auroc), pages_lo95=float(a.lo95), pages_sens=float(a.sensitivity), pages_spec=float(a.specificity),
                        sim_pos=int(b.positives), sim_auroc=float(b.auroc), sim_lo95=float(b.lo95), sim_sens=float(b.sensitivity), sim_spec=float(b.specificity), threshold=float(b.threshold),
                        pass_pages=ok_pg, pass_sim_auc=ok_auc_sm, pass_sim_operating_point=ok_op_sm, available=bool(promotable and ok_pg and ok_auc_sm and ok_op_sm), verdict=verdict)
nrm = dict(pictures_pages=int(pg.normal_pictures.iloc[0]), flagged_pages=int(pg.normal_flagged_by_any.iloc[0]), pictures_sim=int(sm.normal_pictures.iloc[0]), flagged_sim=int(sm.normal_flagged_by_any.iloc[0]))
json.dump(dict(rule="docs/plan/analysis_plan_changes.md 2026-11-16 late night", normal_pictures=nrm, pairs=status), open(PP + "P_status.json", "w"), indent=1)
md = ["# Section P: fresh positive-rich dataset set P, networks A and B tested once on drawn pages and simulated photos", "",
      "Rules logged before the recordings were selected. Pass rules are the team's proposal, not approved by the guide. Real photos are not part of the verdict.", "",
      f"NORMAL pictures flagged by at least one of the 6 patterns of the block: drawn pages {nrm['flagged_pages']} of {nrm['pictures_pages']}; simulated photos {nrm['flagged_sim']} of {nrm['pictures_sim']}.", "",
      "| Pair | Drawn pages: positives, AUROC (lower 95%), sens / spec | Simulated photos: positives, AUROC (lower 95%), sens / spec | Verdict |", "|---|---|---|---|"]
for pair, s in status.items():
    md.append(f"| {pair} | {s['pages_pos']}, {s['pages_auroc']:.3f} ({s['pages_lo95']:.3f}), {100 * s['pages_sens']:.0f} / {100 * s['pages_spec']:.0f} | {s['sim_pos']}, {s['sim_auroc']:.3f} ({s['sim_lo95']:.3f}), {100 * s['sim_sens']:.0f} / {100 * s['sim_spec']:.0f} | {s['verdict']} |")
open(PP + "SECTION_P.md", "w", encoding="utf-8").write("\n".join(md) + "\n")
print("\n".join(md))
