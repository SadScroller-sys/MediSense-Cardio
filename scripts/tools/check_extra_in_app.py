"""Check that the demo's extra-pattern block gives the same answers as the saved test predictions (models A and B) on real digitised pages. Usage: demo\\.venv-gpu\\Scripts\\python.exe -I scripts/tools/check_extra_in_app.py"""
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "demo"))
from health import assess as A  # noqa: E402
from health import data as D  # noqa: E402
from health import find2 as F  # noqa: E402

ds = D.digitised_sets()
t2 = ds[ds.set == "T2"].reset_index(drop=True)
pa = pd.read_csv(F.OUT_A + "predictions_T2.csv")
pb = pd.read_csv(F.OUT_B + "predictions_T2.csv")
import json  # noqa: E402

sa = json.load(open(F.OUT_A + "status.json"))["classes"]
sb = json.load(open(F.OUT_B + "status.json"))["classes"]
rng = np.random.RandomState(1)
rows, bad = [], 0
for i in rng.choice(len(t2), 12, replace=False):
    leads = {k: v for k, v in np.load(t2.path[i]).items()}
    ex = A.extra_findings(leads, "GREEN", True)
    for x in ex:
        pred = (pa if x["src"] == "A" else pb)
        st = sa if x["src"] == "A" else sb
        p = float(pred[pred.name == t2.name[i]][x["cls"]].iloc[0])
        want = p >= st[x["cls"]]["threshold"]
        bad += int(want != x["detected"])
        rows.append((t2.name[i], x["cls"], x["detected"], want))
print("compared", len(rows), "extra results; mismatches with the saved test predictions:", bad)
print("a RED light gives:", A.extra_findings(leads, "RED", True), "| not straightened gives:", A.extra_findings(leads, "GREEN", False))
print("first rows:", rows[:6])
