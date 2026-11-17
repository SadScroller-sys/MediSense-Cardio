"""Frontal QRS axis for the MediSense-Cardio demo.
It runs EXACTLY the method that passed our pre-set tests (Section W, scripts/analysis/section_W_axis.py): the candidate is read from the frozen file results/analysis/sectionW_frozen.json
(all six limb leads, dominant deflection). No calibration: angles are never rescaled or offset. No second implementation.
It is shown to the user only for GREEN photos that were straightened, as a number of degrees without any verdict word (see demo/explain.py).
Research prototype. Not a medical device."""
import importlib.util
import json
import os

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
CANDIDATE = json.load(open(os.path.join(ROOT, "results", "analysis", "sectionW_frozen.json"), encoding="utf-8"))["candidate"]
_W = None


def _load():
    global _W
    if _W is None:
        spec = importlib.util.spec_from_file_location("section_W", os.path.join(ROOT, "scripts", "analysis", "section_W_axis.py"))
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        _W = m
    return _W


def axis_from_leads(leads):
    """leads: dict lead -> array (microvolts, 1 kHz, NaN = not read) exactly as the digitiser saves it. Returns the frontal QRS axis in degrees (-180 to 180), or NaN."""
    W = _load()
    T = W.T
    dig = {L: np.asarray(leads[L], float) / 1000.0 for L in W.LEADS if L in leads and leads[L] is not None}
    if "II" not in dig:
        return float("nan")
    win = {L: T.longest_run(np.isfinite(dig[L])) for L in dig}
    res = W.measure_record(dig, 1000, win, T.lead2_rpeaks(dig["II"], 1000))
    v = res.get(CANDIDATE, float("nan"))
    return float(v) if v is not None and np.isfinite(v) else float("nan")
