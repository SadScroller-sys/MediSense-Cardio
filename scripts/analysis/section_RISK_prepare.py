"""ECG-estimated mortality RISK PILOT (CODE-15%), step 1: unzip the downloaded HDF5 parts, keep the patients that carry an outcome (first exam) with a 10 s recording, resample to 250 Hz, store.
Rules: docs/plan/analysis_plan_changes.md, 2026-11-15 night "ECG-estimated mortality RISK PILOT". Output: data/code15/risk_x250_f16.npy (N, 12, 2500), data/code15/risk_meta.csv.
Usage: demo\\.venv-gpu\\Scripts\\python.exe scripts/analysis/section_RISK_prepare.py [last_part=3]"""
import os
import sys
import zipfile

import h5py
import numpy as np
import pandas as pd
from scipy.signal import resample_poly

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
DD = os.path.join(ROOT, "data", "code15") + os.sep
LAST = int(sys.argv[1]) if len(sys.argv) > 1 else 3
d = pd.read_csv(DD + "exams.csv")
d["part"] = d.trace_file.str.extract(r"part(\d+)")[0].astype(int)
first = d[d.death.notna() & (d.part <= LAST)].copy()
rows, X = [], []
for part in range(LAST + 1):
    zf = DD + f"exams_part{part}.zip"
    if not os.path.exists(zf):
        print("part", part, "not downloaded yet: skipped", flush=True)
        continue
    hf = DD + f"exams_part{part}.hdf5"
    if not os.path.exists(hf):
        with zipfile.ZipFile(zf) as z:
            name = [n for n in z.namelist() if n.endswith(".hdf5")][0]
            z.extract(name, DD)
            if os.path.basename(name) != os.path.basename(hf):
                os.replace(DD + name, hf)
    with h5py.File(hf, "r") as f:
        print("keys:", list(f.keys()), {k: f[k].shape for k in f.keys()}, flush=True)
        idkey = "exam_id" if "exam_id" in f else "id_exam"
        sigkey = "tracings" if "tracings" in f else "signal"
        ids = f[idkey][:]
        want = first[first.part == part].set_index("exam_id")
        pos = {int(e): i for i, e in enumerate(ids)}
        sel = [(pos[e], e) for e in want.index if e in pos]
        sel.sort()
        for k in range(0, len(sel), 500):
            blk = sel[k:k + 500]
            arr = f[sigkey][blk[0][0]:blk[-1][0] + 1]                  # (n, 4096, 12), contiguous read
            for i, e in blk:
                x = arr[i - blk[0][0]].astype(np.float32)             # (4096, 12), 400 Hz
                nz = np.flatnonzero(np.abs(x).sum(1) > 0)
                if len(nz) < 3900:                                      # 7 s recording (zero padded): not usable for the 10 s page layout
                    continue
                s = x[nz[0]:nz[0] + 4000].T                             # (12, 4000)
                if s.shape[1] < 4000:
                    continue
                y = resample_poly(s, 5, 8, axis=1)                      # 400 Hz -> 250 Hz, 2500 samples
                if not np.isfinite(y).all():
                    continue
                X.append(y.astype(np.float16))
                r = want.loc[e]
                rows.append(dict(exam_id=int(e), patient_id=int(r.patient_id), death=bool(r.death), timey=float(r.timey), age=float(r.age), is_male=bool(r.is_male), part=part))
        print("part", part, "kept so far", len(rows), flush=True)
np.save(DD + "risk_x250_f16.npy", np.stack(X))
pd.DataFrame(rows).to_csv(DD + "risk_meta.csv", index=False)
print("saved", len(rows), "patients; deaths", int(sum(r["death"] for r in rows)))
