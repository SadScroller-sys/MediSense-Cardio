"""Build the Overleaf upload zip for the IEEE paper with forward-slash paths (Windows PowerShell zips use backslashes, which Overleaf can mishandle).
Usage: python -I scripts/tools/make_paper_zip.py"""
import os
import zipfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
P = os.path.join(ROOT, "docs", "paper")
out = os.path.join(P, "medisense-cardio-paper-v2.zip")
if os.path.exists(out):
    os.remove(out)
used = ["figures/fig_pipeline.png", "figures/fig_wrong_by_damage.png", "figures/fig_results_at_a_glance.png"]
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for f in ["main_v2.tex", "references.bib"] + used:
        z.write(os.path.join(P, f), f)
with zipfile.ZipFile(out) as z:
    print(z.namelist(), os.path.getsize(out), "bytes")
