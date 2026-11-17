"""PR interval for the MediSense-Cardio demo.
It runs EXACTLY the method that passed our pre-set tests (Section U, scripts/analysis/section_U_pr_qrs.py): the candidate and the offset are read from the frozen file
results/analysis/sectionU_frozen.json (PR = median over leads with the tangent P onset, offset +5.8 ms). No second implementation.
It is shown to the user only for GREEN photos that were straightened (see demo/explain.py); the tests were done on straightened photos.
Research prototype. Not a medical device."""
import importlib.util
import json
import os

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
FROZEN = json.load(open(os.path.join(ROOT, "results", "analysis", "sectionU_frozen.json"), encoding="utf-8"))["pr"]
PR_MIN_MS, PR_MAX_MS = 50, 400          # plausibility guard: a value outside this range is never shown
_U = None


def _load():
    global _U
    if _U is None:
        spec = importlib.util.spec_from_file_location("section_U", os.path.join(ROOT, "scripts", "analysis", "section_U_pr_qrs.py"))
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        _U = m
    return _U


def pr_from_leads(leads):
    """leads: dict lead -> array (microvolts, 1 kHz, NaN = not read) exactly as the digitiser saves it. Returns the PR interval in ms, or NaN when it cannot be measured."""
    U = _load()
    T = U.T
    dig = {L: np.asarray(leads[L], float) / 1000.0 for L in U.LEADS if L in leads and leads[L] is not None}
    if "II" not in dig:
        return float("nan")
    win = {L: T.longest_run(np.isfinite(dig[L])) for L in dig}
    res = U.measure_record(dig, 1000, win, T.lead2_rpeaks(dig["II"], 1000))
    v = res.get(FROZEN["candidate"], float("nan"))
    if v is None or not np.isfinite(v):
        return float("nan")
    v = float(v) - float(FROZEN["offset_ms"])
    return v if PR_MIN_MS <= v <= PR_MAX_MS else float("nan")
