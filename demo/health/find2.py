"""More disease findings, models A (PTB-XL fine labels) and B (CODE-15% labels). Rules: docs/plan/analysis_plan_changes.md, 2026-11-16 'MORE DISEASE FINDINGS' (+ Amendment 1).
Research prototype. Not a medical device."""
import ast
import hashlib
import os

import numpy as np
import pandas as pd

from . import data as D

ROOT = D.ROOT
OUT_A = os.path.join(ROOT, "results", "find2_A") + os.sep
OUT_B = os.path.join(ROOT, "results", "find2_B") + os.sep
DD = os.path.join(ROOT, "data", "code15") + os.sep
A_CODES = ["ASMI", "NDT", "LVH", "IMI", "LAFB", "ISC_", "IRBBB", "PVC", "1AVB", "IVCD", "ISCAL", "NST_", "CRBBB", "CLBBB", "ILMI", "LAO/LAE"]
A_NAMES = {"ASMI": "anteroseptal infarction", "NDT": "non-diagnostic T abnormality", "LVH": "left ventricular hypertrophy", "IMI": "inferior infarction", "LAFB": "left anterior fascicular block", "ISC_": "non-specific ischaemia",
           "IRBBB": "incomplete right bundle branch block", "PVC": "premature ventricular beats", "1AVB": "first-degree AV block", "IVCD": "non-specific conduction delay", "ISCAL": "anterolateral ischaemia",
           "NST_": "non-specific ST change", "CRBBB": "complete right bundle branch block", "CLBBB": "complete left bundle branch block", "ILMI": "inferolateral infarction", "LAO/LAE": "left atrial enlargement"}
B_LABELS = ["1dAVb", "RBBB", "LBBB", "SB", "ST", "AF"]
B_NAMES = {"1dAVb": "first-degree AV block", "RBBB": "right bundle branch block", "LBBB": "left bundle branch block", "SB": "slow heart rate (sinus bradycardia)", "ST": "fast heart rate (sinus tachycardia)", "AF": "atrial fibrillation"}
RHYTHM = {"SBRAD", "STACH", "AFIB", "AFLT"}              # rhythm codes carry likelihood 0 in PTB-XL: present when listed


def _codes(s):
    return ast.literal_eval(s)


def has(codes, name):
    if name in RHYTHM:
        return name in codes
    return codes.get(name, 0) >= 50


def labels_A(db):
    rows = [[float(has(_codes(s), c)) for c in A_CODES] for s in db.scp_codes]
    return pd.DataFrame(rows, index=db.index, columns=A_CODES).astype(np.float32)


def labels_B_from_ptbxl(db):
    """The six CODE-15% labels as defined on PTB-XL records (for the tests on our digitised sets)."""
    rows = []
    for s in db.scp_codes:
        c = _codes(s)
        rows.append([has(c, "1AVB"), has(c, "CRBBB") or has(c, "IRBBB"), has(c, "CLBBB"), has(c, "SBRAD"), has(c, "STACH"), has(c, "AFIB") or has(c, "AFLT")])
    return pd.DataFrame(rows, index=db.index, columns=B_LABELS).astype(np.float32)


def bucket(pid):
    return int(hashlib.md5(f"62-{pid}".encode()).hexdigest(), 16) % 100
