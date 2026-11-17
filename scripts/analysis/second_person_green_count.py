"""Third number of the second-person check: wrong heart rates among GREEN readings of the competition real captures (expected 2 of 917).
Reads only results/analysis/sectionP_competition_lights_labels.csv (one row per image: light, wrong, none). Usage: python -I scripts/analysis/second_person_green_count.py"""
import os

import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
d = pd.read_csv(os.path.join(ROOT, "results", "analysis", "sectionP_competition_lights_labels.csv"))
w = d[~d["none"].astype(bool)]                      # images with a heart-rate reading
for light in ("GREEN", "AMBER", "RED"):
    x = w[w["light"] == light]
    print(f"{light}: {int(x['wrong'].sum())} wrong of {len(x)} readings")
g = w[w["light"] == "GREEN"]
res = f"{int(g['wrong'].sum())}/{len(g)}"
print(f"GREEN wrong: {res} | reported 2/917 | {'MATCH' if res == '2/917' else 'DIFFERENT'}")
