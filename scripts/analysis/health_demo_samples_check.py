"""End-to-end check of the heart health module on the six demo sample photos (simulated phone photos of Q-set pages, whose recordings are excluded from training).
Runs the real app path (straighten -> digitise -> traffic light -> PR/axis -> assessment) and writes results/health/demo_samples_check.md. Descriptive, 6 photos only.
Usage: demo\.venv-gpu\Scripts\python.exe scripts/analysis/health_demo_samples_check.py"""
import glob
import os
import sys

import cv2

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "demo"))
import axis_deg as AXD  # noqa: E402
import pipeline as P  # noqa: E402
import pr_interval as PRI  # noqa: E402
from health import assess as HA  # noqa: E402

TRUTH = {"sample1_straight_clean.jpg": "normal ECG", "sample2_angled_left.jpg": "left ventricular hypertrophy, non-specific ischemic signs, non-specific intraventricular conduction delay",
         "sample3_angled_from_below.jpg": "complete left bundle branch block (conduction)", "sample4_dim_uneven_light.jpg": "incomplete right bundle branch block (conduction) and non-specific ST changes",
         "sample5_far_and_small.jpg": "left ventricular hypertrophy; possible old inferior heart attack (likelihood 15 of 100)", "sample6_blurry_and_angled.jpg": "normal ECG (likelihood 80 of 100)"}
rows = ["# Heart health module on the six demo photos (descriptive; 6 photos, one fixed seed)", "",
        "| Photo | PTB-XL label of the source recording | Light | Overall indicator | Supported findings found | Supported findings not found | Not available |", "|---|---|---|---|---|---|---|"]
for f in sorted(glob.glob(os.path.join(ROOT, "demo", "new_samples", "sample*.jpg"))):
    r = P.run(cv2.imread(f))
    pr = ax = float("nan")
    if r.get("leads") is not None and r["light"] == "GREEN" and r["page_found"]:
        pr, ax = PRI.pr_from_leads(r["leads"]), AXD.axis_from_leads(r["leads"])
    a = HA.assess(r.get("leads"), r["light"], r["reasons"], r["page_found"], r["hr"], r["n_beats"], (r.get("features") or {}).get("rr_cv"), pr, ax, no_output=bool(r["error"]))
    name = os.path.basename(f)
    fl = a["findings"]
    rows.append(f"| {name} | {TRUTH.get(name, '?')} | {r['light']} | {a['overall']['label']} | {'; '.join(x['cls'] for x in fl if x['state'] == 'supported' and x['detected']) or '-'} | "
                f"{'; '.join(x['cls'] for x in fl if x['state'] == 'supported' and not x['detected']) or '-'} | {'; '.join(x['cls'] for x in fl if x['state'] != 'supported') or '-'} |")
    print(rows[-1], "| wording problems:", a["wording_problems"], flush=True)
rows += ["", "Reading: only 6 photos, so this shows the path works and what the output looks like, not accuracy (accuracy is in SECTION_HEALTH.md)."]
open(os.path.join(ROOT, "results", "health", "demo_samples_check.md"), "w", encoding="utf-8").write("\n".join(rows) + "\n")
