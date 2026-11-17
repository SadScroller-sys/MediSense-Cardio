"""RISK PILOT 2, step 1 (rules: docs/plan/analysis_plan_changes.md, 2026-11-16): prepare CODE-15% parts 6 to 17 the same way as pilot 1 (patients with an outcome on the first exam, 10 s recording, 250 Hz), one part at a time
(each part is unzipped, read, then the 3.7 GB HDF5 is deleted), then join with the pilot-1 arrays (parts 0 to 5) into data/code15/risk2_x250_f16.npy + risk2_meta.csv. Resumable (finished parts are skipped).
Usage: demo\\.venv-gpu\\Scripts\\python.exe -I scripts/analysis/section_RISK2_prepare.py"""
import os
import zipfile

import h5py
import numpy as np
import pandas as pd
from scipy.signal import resample_poly

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
DD = os.path.join(ROOT, "data", "code15") + os.sep
PD = DD + "risk2_parts" + os.sep
os.makedirs(PD, exist_ok=True)
d = pd.read_csv(DD + "exams.csv")
d["part"] = d.trace_file.str.extract(r"part(\d+)")[0].astype(int)
first = d[d.death.notna() & d.age.notna()].copy()
for part in range(6, 18):
    if os.path.exists(PD + f"meta_{part}.csv"):
        continue
    zf = DD + f"exams_part{part}.zip"
    if not os.path.exists(zf):
        print("part", part, "not downloaded yet: stop here", flush=True)
        raise SystemExit(1)
    hf = DD + f"exams_part{part}.hdf5"
    with zipfile.ZipFile(zf) as z:
        name = [n for n in z.namelist() if n.endswith(".hdf5")][0]
        z.extract(name, DD)
        if os.path.basename(name) != os.path.basename(hf):
            os.replace(DD + name, hf)
    rows, X = [], []
    with h5py.File(hf, "r") as f:
        idkey = "exam_id" if "exam_id" in f else "id_exam"
        sigkey = "tracings" if "tracings" in f else "signal"
        ids = f[idkey][:]
        want = first[first.part == part].set_index("exam_id")
        pos = {int(e): i for i, e in enumerate(ids)}
        sel = sorted((pos[e], e) for e in want.index if e in pos)
        for k in range(0, len(sel), 500):
            blk = sel[k:k + 500]
            arr = f[sigkey][blk[0][0]:blk[-1][0] + 1]
            for i, e in blk:
                x = arr[i - blk[0][0]].astype(np.float32)
                nz = np.flatnonzero(np.abs(x).sum(1) > 0)
                if len(nz) < 3900:
                    continue
                s = x[nz[0]:nz[0] + 4000].T
                if s.shape[1] < 4000:
                    continue
                y = resample_poly(s, 5, 8, axis=1)
                if not np.isfinite(y).all():
                    continue
                X.append(y.astype(np.float16))
                r = want.loc[e]
                rows.append(dict(exam_id=int(e), patient_id=int(r.patient_id), death=bool(r.death), timey=float(r.timey), age=float(r.age), is_male=bool(r.is_male), part=part))
    os.remove(hf)
    np.save(PD + f"x_{part}.npy", np.stack(X))
    pd.DataFrame(rows).to_csv(PD + f"meta_{part}.csv", index=False)
    print("part", part, "kept", len(rows), flush=True)

# join with the pilot-1 arrays (parts 0 to 5; patients with a known age only)
m0 = pd.read_csv(DD + "risk_meta.csv")
X0 = np.load(DD + "risk_x250_f16.npy", mmap_mode="r")
keep0 = np.flatnonzero(m0.age.notna().values)
metas = [m0.iloc[keep0]] + [pd.read_csv(PD + f"meta_{p}.csv") for p in range(6, 18)]
meta = pd.concat(metas, ignore_index=True)
out = np.lib.format.open_memmap(DD + "risk2_x250_f16.npy", mode="w+", dtype=np.float16, shape=(len(meta), 12, 2500))
n = 0
for k in range(0, len(keep0), 2000):
    ii = keep0[k:k + 2000]
    out[n:n + len(ii)] = X0[ii]
    n += len(ii)
for p in range(6, 18):
    xp = np.load(PD + f"x_{p}.npy")
    out[n:n + len(xp)] = xp
    n += len(xp)
assert n == len(meta)
out.flush()
meta.to_csv(DD + "risk2_meta.csv", index=False)
print("saved", len(meta), "patients; deaths", int(meta.death.sum()), flush=True)
open(DD + "risk2_prepare_done.flag", "w").write("done\n")
