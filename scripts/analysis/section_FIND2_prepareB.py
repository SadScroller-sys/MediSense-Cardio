"""MORE DISEASE FINDINGS, model B, step 1 (rules: docs/plan/analysis_plan_changes.md, 2026-11-16 + Amendment 1): from the 18 downloaded CODE-15% zips keep EVERY exam with a 10 s recording and a label row, 400 Hz -> 100 Hz (1,000 samples),
store as float16. One part at a time (unzip, read, delete the 3.7 GB HDF5); resumable. Output: data/code15/find2_x100_f16.npy (N, 12, 1000) and find2_meta.csv (exam_id, patient_id, part, age, the six labels).
Usage: demo\\.venv-gpu\\Scripts\\python.exe -I scripts/analysis/section_FIND2_prepareB.py"""
import os
import zipfile

import h5py
import numpy as np
import pandas as pd
from scipy.signal import resample_poly

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
DD = os.path.join(ROOT, "data", "code15") + os.sep
PD = DD + "find2_parts" + os.sep
os.makedirs(PD, exist_ok=True)
LAB = ["1dAVb", "RBBB", "LBBB", "SB", "ST", "AF"]
d = pd.read_csv(DD + "exams.csv")
d["part"] = d.trace_file.str.extract(r"part(\d+)")[0].astype(int)
d = d[d[LAB].notna().all(axis=1) & d.patient_id.notna()]
for part in range(18):
    if os.path.exists(PD + f"meta_{part}.csv"):
        continue
    zf = DD + f"exams_part{part}.zip"
    hf = DD + f"exams_part{part}.hdf5"
    if not os.path.exists(hf):
        with zipfile.ZipFile(zf) as z:
            name = [n for n in z.namelist() if n.endswith(".hdf5")][0]
            z.extract(name, DD)
            if os.path.basename(name) != os.path.basename(hf):
                os.replace(DD + name, hf)
    rows, X = [], []
    with h5py.File(hf, "r") as f:
        ids = f["exam_id"][:]
        want = d[d.part == part].set_index("exam_id")
        pos = {int(e): i for i, e in enumerate(ids)}
        sel = sorted((pos[e], e) for e in want.index if e in pos)
        for k in range(0, len(sel), 500):
            blk = sel[k:k + 500]
            arr = f["tracings"][blk[0][0]:blk[-1][0] + 1]
            for i, e in blk:
                x = arr[i - blk[0][0]].astype(np.float32)
                nz = np.flatnonzero(np.abs(x).sum(1) > 0)
                if len(nz) < 3900:
                    continue
                s = x[nz[0]:nz[0] + 4000].T
                if s.shape[1] < 4000:
                    continue
                y = resample_poly(s, 1, 4, axis=1)
                if not np.isfinite(y).all():
                    continue
                X.append(y.astype(np.float16))
                r = want.loc[e]
                rows.append(dict(exam_id=int(e), patient_id=int(r.patient_id), part=part, age=float(r.age), **{k_: int(bool(r[k_])) for k_ in LAB}))
    os.remove(hf)
    np.save(PD + f"x_{part}.npy", np.stack(X))
    pd.DataFrame(rows).to_csv(PD + f"meta_{part}.csv", index=False)
    print("part", part, "kept", len(rows), flush=True)

meta = pd.concat([pd.read_csv(PD + f"meta_{p}.csv") for p in range(18)], ignore_index=True)
out = np.lib.format.open_memmap(DD + "find2_x100_f16.npy", mode="w+", dtype=np.float16, shape=(len(meta), 12, 1000))
n = 0
for p in range(18):
    xp = np.load(PD + f"x_{p}.npy")
    out[n:n + len(xp)] = xp
    n += len(xp)
assert n == len(meta)
out.flush()
meta.to_csv(DD + "find2_meta.csv", index=False)
print("saved", len(meta), "exams;", {k: int(meta[k].sum()) for k in LAB}, flush=True)
open(DD + "find2_prepare_done.flag", "w").write("done\n")
