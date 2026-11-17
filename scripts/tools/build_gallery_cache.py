"""Builds the cache of the demo's 'Dataset gallery' tab: for ALL 120 simulated phone photos of set N (made from PTB-XL recordings; not real phone photos) the output of the SAME code the app runs (frozen traffic light, heart rate, PR, axis, the findings
networks with the app's thresholds), together with the true answer from the dataset labels. Nothing is selected by result: every photo is in the cache. Writes results/paper_n/gallery_cache.json (per case: light, heart rate read and true, truth and tool per pattern, the heart-health panel HTML)
and a scoreboard (hits, misses, false alarms, correct negatives per pattern over the GREEN and AMBER photos, the ones for which the app shows findings).
Usage: demo\\.venv-gpu\\Scripts\\python.exe -I scripts/tools/build_gallery_cache.py"""
import glob
import json
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "demo"))
sys.path.insert(0, os.path.join(ROOT, "safeguard"))
import axis_deg as AXD  # noqa: E402
import ecg_traffic_light as T  # noqa: E402
import pipeline as P  # noqa: E402
import pr_interval as PRI  # noqa: E402
from health import assess as HA  # noqa: E402
from health import dashboard as DBD  # noqa: E402
from health import data as D  # noqa: E402
from health import find2 as F  # noqa: E402

PN = ROOT + "/results/paper_n/"
sel = pd.read_csv(PN + "selected_N.csv").set_index("page")
db, Y = D.load_db()                                                  # Y: MI, STTC, ... superclasses of the first network
YA, YB = F.labels_A(db), F.labels_B_from_ptbxl(db)
PATTERNS = [("MI", "Heart-attack pattern (main list)"), ("STTC", "ST/T-wave change (main list)"), ("ASMI", "Anteroseptal heart attack (research only)"), ("LVH", "Left ventricular hypertrophy (research only)"),
            ("LAFB", "Left anterior fascicular block (research only)"), ("IRBBB", "Incomplete right bundle branch block (research only)"), ("AF", "Atrial fibrillation (research only)"),
            ("LBBB", "Left bundle branch block (research only)"), ("1dAVb", "First-degree AV block (research only)")]


def truth_of(ecg_id):
    return {"MI": bool(Y.loc[ecg_id, "MI"]), "STTC": bool(Y.loc[ecg_id, "STTC"]), "ASMI": bool(YA.loc[ecg_id, "ASMI"]), "LVH": bool(YA.loc[ecg_id, "LVH"]), "LAFB": bool(YA.loc[ecg_id, "LAFB"]), "IRBBB": bool(YA.loc[ecg_id, "IRBBB"]),
            "AF": bool(YB.loc[ecg_id, "AF"]), "LBBB": bool(YB.loc[ecg_id, "LBBB"]), "1dAVb": bool(YB.loc[ecg_id, "1dAVb"])}


cases = []
for f in sorted(glob.glob(PN + "N_sim/dig_v2/N*.npz")):
    name = os.path.basename(f)[:-4]
    page, shot = name.split("_")
    ecg_id = int(sel.loc[page, "ecg_id"])
    z = T.load_npz(f)
    leads = {k: np.asarray(v, float) for k, v in z.items()}
    chk = T.check(z)
    light, reasons = chk["light"], chk["reasons"]
    ii = leads.get("II")
    hr, nb = P.hr_clean(ii / 1000.0) if ii is not None and np.isfinite(ii).sum() > 500 else (float("nan"), 0)
    rr_cv = (chk.get("features") or {}).get("rr_cv")
    pr_ms = axis = float("nan")
    if light == "GREEN":
        try:
            pr_ms = PRI.pr_from_leads(leads)
        except Exception:
            pass
        try:
            axis = AXD.axis_from_leads(leads)
        except Exception:
            pass
    a = HA.assess(leads, light, reasons, True, hr, nb, rr_cv, pr_ms, axis, no_output=not np.isfinite(hr))
    det = {k: None for k, _ in PATTERNS}
    for fd in a["findings"]:
        if fd["cls"] in ("MI", "STTC") and fd["state"] == "supported":
            det[fd["cls"]] = bool(fd["detected"])
    for x in a.get("extra") or []:
        det[x["cls"]] = bool(x["detected"])
    src = db.loc[ecg_id, "filename_lr"]
    true_hr = P.hr_clean(D._read_record(src)[1].astype(float), fs=100)[0]
    cases.append(dict(name=name, page=page, shot=shot, ecg_id=ecg_id, light=light, hr_read=None if not np.isfinite(hr) else float(hr), hr_true=None if not np.isfinite(true_hr) else float(true_hr),
                      truth=truth_of(ecg_id), detected=det, panel_html=DBD.results_panel(a), indicator=a["overall"]["label"]))
    if len(cases) % 20 == 0:
        print(len(cases), "cases", flush=True)
score = {}
shown = [c for c in cases if c["light"] in ("GREEN", "AMBER")]
for k, label in PATTERNS:
    tp = sum(1 for c in shown if c["truth"][k] and c["detected"][k])
    fn = sum(1 for c in shown if c["truth"][k] and c["detected"][k] is False)
    fp = sum(1 for c in shown if not c["truth"][k] and c["detected"][k])
    tn = sum(1 for c in shown if not c["truth"][k] and c["detected"][k] is False)
    score[k] = dict(label=label, true_cases=tp + fn, hits=tp, misses=fn, false_alarms=fp, correct_negatives=tn)
summary = dict(cases=len(cases), green=sum(c["light"] == "GREEN" for c in cases), amber=sum(c["light"] == "AMBER" for c in cases), red=sum(c["light"] == "RED" for c in cases))
json.dump(dict(summary=summary, scoreboard=score, patterns=[[k, l] for k, l in PATTERNS], cases=cases), open(PN + "gallery_cache.json", "w"))
print(summary)
for k, s in score.items():
    print(k, s["true_cases"], "true |", s["hits"], "hit,", s["misses"], "missed,", s["false_alarms"], "false alarms,", s["correct_negatives"], "correct negatives")
