"""Summary of the repeat-variation runs (scripts/analysis/repeat_variation_demo.py): how much the demo pipeline changes when the same photo is run again.
Descriptive only (rule logged in repeat_variation_demo.py before the run). Usage: python -I scripts/analysis/repeat_variation_summary.py
Writes results/reproducibility/repeat_variation_summary.md and repeat_variation_by_photo.csv."""
import os

import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
D = os.path.join(ROOT, "results", "reproducibility") + os.sep
d = pd.read_csv(D + "repeat_variation_runs.csv")


def circ_range(a):
    a = np.deg2rad(np.asarray(a, float))
    a = a[np.isfinite(a)]
    if len(a) < 2:
        return float("nan")
    # smallest arc containing all angles
    s = np.sort(np.mod(a, 2 * np.pi))
    gaps = np.diff(np.concatenate([s, [s[0] + 2 * np.pi]]))
    return float(np.rad2deg(2 * np.pi - gaps.max()))


rows = []
for ph, g in d.groupby("photo"):
    pr = g.pr_ms.to_numpy(float)
    rows.append(dict(photo=ph, runs=len(g), hr_range_bpm=round(float(np.nanmax(g.hr) - np.nanmin(g.hr)), 2) if g.hr.notna().any() else float("nan"),
                     lights="/".join(sorted(set(g.light))), light_changed=g.light.nunique() > 1,
                     pr_values=int(np.isfinite(pr).sum()), pr_range_ms=round(float(np.nanmax(pr) - np.nanmin(pr)), 1) if np.isfinite(pr).sum() >= 2 else float("nan"),
                     pr_present_in_some_runs_only=bool(0 < np.isfinite(pr).sum() < len(g)),
                     axis_range_deg=round(circ_range(g.axis_deg), 1), score_range=round(float(g.score.max() - g.score.min()), 4),
                     rr_cv_range=round(float(g.rr_cv.max() - g.rr_cv.min()), 4) if g.rr_cv.notna().any() else float("nan")))
t = pd.DataFrame(rows)
t.to_csv(D + "repeat_variation_by_photo.csv", index=False)
md = ["# Repeat variation of the demo pipeline (descriptive)",
      f"Same {t.photo.nunique()} demo photos, " + (f"{int(t.runs.min())} runs each" if t.runs.min() == t.runs.max() else f"{int(t.runs.min())} to {int(t.runs.max())} runs each") + ", nothing changed between runs (GPU, `demo/pipeline.py`, frozen PR and axis methods). Raw rows: `repeat_variation_runs.csv`. "
      "Rule: descriptive, no pass/fail (written in `scripts/analysis/repeat_variation_demo.py` before the run).", "",
      "| Photo | Runs | Heart-rate range (bpm) | Light(s) | PR range (ms) | PR value in some runs only | Axis range (deg) | Traffic-light score range |", "|---|---|---|---|---|---|---|---|"]
for _, r in t.iterrows():
    md.append(f"| {r.photo} | {r.runs} | {r.hr_range_bpm} | {r.lights} | {r.pr_range_ms} ({r.pr_values} values) | {'yes' if r.pr_present_in_some_runs_only else 'no'} | {r.axis_range_deg} | {r.score_range} |")
md += ["", "**Overall**", "",
       f"- Heart rate: largest range {t.hr_range_bpm.max():.2f} bpm, median range {t.hr_range_bpm.median():.2f} bpm (the 5 bpm 'wrong' limit is {5 / max(t.hr_range_bpm.max(), 1e-9):.0f} times the largest range).",
       f"- Traffic light changed between runs of the same photo on {int(t.light_changed.sum())} of {len(t)} photos.",
       f"- PR (photos with at least 2 values): largest range {t.pr_range_ms.max():.1f} ms, median {t.pr_range_ms.median():.1f} ms. A PR value appeared in some runs but not in others for {int(t.pr_present_in_some_runs_only.sum())} photos.",
       f"- Axis: largest range {t.axis_range_deg.max():.1f} degrees, median {t.axis_range_deg.median():.1f} degrees.",
       "", "Limits: 10 photos from the demo folders (simulated and real phone photos), a handful of runs each, one computer and one GPU. This measures the pipeline's own repeat variation, not photo-to-photo variation. "
       "Whether the variation comes from the digitiser's random tie-break or from GPU arithmetic was not separated."]
open(D + "repeat_variation_summary.md", "w", encoding="utf-8").write("\n".join(md) + "\n")
print("\n".join(md))
