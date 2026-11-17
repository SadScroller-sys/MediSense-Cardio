"""Summary of the SEEDED repeat test (rule and success criterion logged in docs/plan/analysis_plan_changes.md, 2026-11-15, before the run).
Success criterion: every photo gives identical heart rate, light, PR and axis in both runs. Then the seeded values are compared with the earlier unseeded runs and
with the study values of the four example photos. Usage: python -I scripts/analysis/repeat_variation_seeded_summary.py
Writes results/reproducibility/repeat_variation_seeded_summary.md."""
import os

import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
D = os.path.join(ROOT, "results", "reproducibility") + os.sep
s = pd.read_csv(D + "repeat_variation_seeded_runs.csv")
u = pd.read_csv(D + "repeat_variation_runs.csv")
STUDY = {"example2_straight_photo_green.jpg": (55.03, "GREEN"), "example1_angled_photo_fixed_by_straightening.jpg": (62.56, "GREEN"),
         "example3_angled_photo_amber.jpg": (106.28, "AMBER"), "example4_hard_page_red.jpg": (65.90, "RED")}


def same(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    return bool(np.all((np.isnan(a) & np.isnan(b)) | (np.abs(a - b) <= 1e-9)))


rows = []
for ph, g in s.groupby("photo"):
    r1, r2 = g[g.run == g.run.min()].iloc[0], g[g.run == g.run.max()].iloc[0]
    ident = dict(hr=same(r1.hr, r2.hr), pr=same(r1.pr_ms, r2.pr_ms), axis=same(r1.axis_deg, r2.axis_deg), light=(r1.light == r2.light), score=same(r1.score, r2.score))
    uu = u[u.photo == ph]
    rows.append(dict(photo=ph, runs=len(g), identical=all(ident.values()), hr=r1.hr, light=r1.light, pr=r1.pr_ms, axis=r1.axis_deg,
                     unseeded_hr_mean=uu.hr.mean(), unseeded_pr_range=(uu.pr_ms.max() - uu.pr_ms.min()), pr_in_unseeded_range=bool(uu.pr_ms.min() - 1e-6 <= r1.pr_ms <= uu.pr_ms.max() + 1e-6) if np.isfinite(r1.pr_ms) else None,
                     unseeded_axis_values=", ".join(f"{v:.1f}" for v in sorted(set(np.round(uu.axis_deg, 1))))))
t = pd.DataFrame(rows)
ok = bool(t.identical.all()) and len(t) == 10
md = ["# Seeded demo: repeat test (descriptive)", "",
      f"Same 10 demo photos, {int(s.run.max())} runs each, seeded digitiser (seed 42), GPU. **Success criterion (fixed before the run): identical heart rate, light, PR, axis and score in both runs for every photo. Result: {'MET' if ok else 'NOT MET'}** "
      f"({int(t.identical.sum())} of {len(t)} photos identical).", "",
      "| Photo | Runs | Identical | HR (bpm) | Light | PR (ms) | Axis (deg) | Earlier unseeded HR mean | Earlier unseeded PR range (ms) | Seeded PR inside that range | Earlier unseeded axis values |", "|---|---|---|---|---|---|---|---|---|---|---|"]
for _, r in t.iterrows():
    md.append(f"| {r.photo} | {r.runs} | {'yes' if r.identical else '**NO**'} | {r.hr:.2f} | {r.light} | {'' if not np.isfinite(r.pr) else f'{r.pr:.1f}'} | {r.axis:.1f} | {r.unseeded_hr_mean:.2f} | {'' if not np.isfinite(r.unseeded_pr_range) else f'{r.unseeded_pr_range:.1f}'} | {r.pr_in_unseeded_range} | {r.unseeded_axis_values} |")
md += ["", "**Against the study values of the four example photos (Kaggle run, unseeded):**", "", "| Photo | Study HR / light | Seeded demo HR / light | Difference (bpm) |", "|---|---|---|---|"]
for ph, (hr, li) in STUDY.items():
    r = t[t.photo == ph].iloc[0]
    md.append(f"| {ph} | {hr} / {li} | {r.hr:.2f} / {r.light} | {r.hr - hr:+.2f} |")
md += ["", "Reading: the seed removes the run-to-run variation; the seeded demo shows one fixed draw of the tie-break, which can differ slightly from the unseeded study values (a 1e-6 perturbation). The study results themselves were produced unseeded and are unchanged. Limits: 10 photos, 2 runs, one computer and one GPU."]
open(D + "repeat_variation_seeded_summary.md", "w", encoding="utf-8").write("\n".join(md) + "\n")
print("\n".join(md))
