"""Set N verdict: applies the pass rules logged in docs/plan/analysis_plan_changes.md (2026-11-16 evening, 'POSITIVE-RICH SET N') to the part results written by section_N_test.py. Writes results/paper_n/N_status.json and SECTION_N.md.
Rules: a finding is 'supported for phone photos' only if ALL hold: pages: >= 20 positives, AUROC >= 0.80 and lower end > 0.70; simulated photos: >= 20 positives, AUROC >= 0.75; real photos (if available: >= 20 positive real photos with
usable output): AUROC >= 0.75 (point estimate). Without real photos a finding that passes pages and simulated photos is 'supported on simulated photos only' and STAYS research-only. A finding that fails on pages is removed from the
research-only block. Same condition in A and B (1AVB with 1dAVb, CLBBB with LBBB): shown once, from the model with the higher lower interval end on real photos (simulated if none); a tie goes to B.
Usage: python -I scripts/analysis/section_N_verdict.py"""
import json
import os

import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
PN = ROOT + "/results/paper_n/"
parts = {}
for p in ("pages", "sim", "real"):
    f = PN + f"test_{p}_metrics.csv"
    if os.path.exists(f):
        parts[p] = pd.read_csv(f).set_index("pair")
assert "pages" in parts and "sim" in parts, "the pages part and the simulated-photo part must have been tested"
have_real = "real" in parts and (parts["real"].positives >= 20).any()
status = {}
for pair in parts["pages"].index:
    pg, sm = parts["pages"].loc[pair], parts["sim"].loc[pair]
    ok_pg = bool(pg.positives >= 20 and pg.auroc >= 0.80 and pg.lo95 > 0.70)
    ok_sm = bool(sm.positives >= 20 and sm.auroc >= 0.75)
    rl = parts["real"].loc[pair] if "real" in parts else None
    real_testable = bool(rl is not None and rl.positives >= 20)
    ok_rl = bool(real_testable and rl.auroc >= 0.75)
    if not ok_pg:
        verdict = "FAILS on drawn pages: removed from the research-only block"
    elif not ok_sm:
        verdict = "passes drawn pages, fails simulated photos: stays research-only"
    elif real_testable and ok_rl:
        verdict = "SUPPORTED FOR PHONE PHOTOS (pages, simulated and real photos)"
    elif real_testable and not ok_rl:
        verdict = "passes pages and simulated photos, FAILS real photos: stays research-only"
    else:
        verdict = "passes pages and simulated photos; real photos not testable or not provided: stays research-only"
    status[pair] = dict(pages_auroc=float(pg.auroc), pages_lo95=float(pg.lo95), pages_pos=int(pg.positives), sim_auroc=float(sm.auroc), sim_lo95=float(sm.lo95), sim_pos=int(sm.positives),
                        real_auroc=float(rl.auroc) if rl is not None else None, real_lo95=float(rl.lo95) if rl is not None else None, real_pos=int(rl.positives) if rl is not None else 0,
                        sens_real=float(rl.sensitivity) if rl is not None else None, spec_real=float(rl.specificity) if rl is not None else None,
                        sens_sim=float(sm.sensitivity), spec_sim=float(sm.specificity), sens_pages=float(pg.sensitivity), spec_pages=float(pg.specificity),
                        pass_pages=ok_pg, pass_sim=ok_sm, pass_real=ok_rl, real_testable=real_testable, verdict=verdict, supported_for_photos=bool(ok_pg and ok_sm and ok_rl))
# same condition in A and B
pairs = [("1AVB (A)", "1dAVb (B)"), ("CLBBB (A)", "LBBB (B)")]
for a, b in pairs:
    key = "real_lo95" if (have_real and status[a]["real_testable"] and status[b]["real_testable"]) else "sim_lo95"
    pick = a if status[a][key] > status[b][key] else b
    other = b if pick == a else a
    status[pick]["same_condition_choice"] = "shown (higher lower interval end on " + ("real" if key == "real_lo95" else "simulated") + " photos; a tie goes to B)"
    status[other]["same_condition_choice"] = "not shown: the other model covers the same condition and did better"
    if status[other]["supported_for_photos"]:
        status[other]["supported_for_photos"] = False
json.dump(dict(rules="docs/plan/analysis_plan_changes.md 2026-11-16 evening", real_photos_available=have_real, pairs=status), open(PN + "N_status.json", "w"), indent=1)
md = ["# Section N: positive-rich set N, networks A and B tested once on drawn pages, simulated photos and real photos", "",
      "Rules: `docs/plan/analysis_plan_changes.md`, 'POSITIVE-RICH SET N' (logged before the recordings were selected). Pass rules are the team's proposal, not approved by the guide. Real photos available for the verdict: **" + str(have_real) + "**.", "",
      "| Pair | Pages: positives, AUROC (95%) | Simulated photos: positives, AUROC (95%) | Real photos: positives, AUROC (95%) | Sensitivity / specificity (real, else simulated) | Verdict |", "|---|---|---|---|---|---|"]
for pair, s in status.items():
    real = f"{s['real_pos']}, {s['real_auroc']:.3f} ({s['real_lo95']:.3f}-{s['real_hi95'] if False else s['real_lo95']:.3f})" if False else (f"{s['real_pos']}, {s['real_auroc']:.3f}" if s["real_auroc"] == s["real_auroc"] and s["real_auroc"] is not None else "not provided")
    sn, sp = (s["sens_real"], s["spec_real"]) if s["real_testable"] else (s["sens_sim"], s["spec_sim"])
    md.append(f"| {pair} | {s['pages_pos']}, {s['pages_auroc']:.3f} ({s['pages_lo95']:.3f}-) | {s['sim_pos']}, {s['sim_auroc']:.3f} ({s['sim_lo95']:.3f}-) | {real} | {100 * sn:.0f} / {100 * sp:.0f} | {s['verdict']}" + (f"; {s['same_condition_choice']}" if "same_condition_choice" in s else "") + " |")
open(PN + "SECTION_N.md", "w", encoding="utf-8").write("\n".join(md) + "\n")
print("\n".join(md))
