"""Repeat variation of the demo pipeline (2026-11-14, exploratory; part of the reproducibility package).

Question: the digitiser has a random tie-break in its line tracer, so the same photo can give slightly different numbers on two runs.
How big is that variation for heart rate, PR interval and axis, and can a traffic light change between two runs of the same photo?

Rule written BEFORE the run (descriptive only, no pass/fail): run each of the 10 demo photos (6 in demo/new_samples, 4 in demo/examples)
through the full pipeline (straighten -> digitise -> cleaned heart rate -> traffic light -> PR and axis by the frozen methods) REPEATS times,
on the GPU, with nothing changed between runs. Report, per photo and overall: the spread (max - min) of the heart rate, PR and axis, and
whether the light changed.
Usage: demo\\.venv-gpu\\Scripts\\python.exe scripts/analysis/repeat_variation_demo.py     (resumes if the CSV already holds runs)
"""
import glob
import os
import sys

import cv2
import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "demo"))
import axis_deg as AXD  # noqa: E402
import pipeline as P  # noqa: E402
import pr_interval as PRI  # noqa: E402

REPEATS = int(os.environ.get("REPEATS", "3"))
OUT = os.path.join(ROOT, "results", "reproducibility", os.environ.get("REPEAT_OUT", "repeat_variation_runs.csv"))   # REPEAT_OUT=repeat_variation_seeded_runs.csv for the seeded test
photos = sorted(glob.glob(os.path.join(ROOT, "demo", "new_samples", "sample*.jpg"))) + sorted(glob.glob(os.path.join(ROOT, "demo", "examples", "example*.jpg")))
rows = pd.read_csv(OUT).to_dict("records") if os.path.exists(OUT) else []
done = {(r["photo"], r["run"]) for r in rows}
for run in range(1, REPEATS + 1):
    for f in photos:
        name = os.path.basename(f)
        if (name, run) in done:
            continue
        img = cv2.imread(f)
        r = P.run(img)
        pr = ax = float("nan")
        if r.get("leads") is not None:
            try:
                pr = PRI.pr_from_leads(r["leads"])
            except Exception:
                pass
            try:
                ax = AXD.axis_from_leads(r["leads"])
            except Exception:
                pass
        rr = (r.get("features") or {}).get("rr_cv")
        rows.append(dict(photo=name, run=run, hr=r["hr"], n_beats=r["n_beats"], light=r["light"], score=r.get("score"), rr_cv=rr, pr_ms=pr, axis_deg=ax,
                         seconds=round(r["seconds"], 1), device=P.LAST_DEVICE))
        pd.DataFrame(rows).to_csv(OUT, index=False)
        print(name, run, rows[-1]["hr"], rows[-1]["light"], pr, ax, flush=True)
print("done", len(rows))
