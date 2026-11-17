"""Evaluates the FROZEN traffic-light tool once on (a) the competition real captures (Arm C 40 + extension 100) and (b) the 60 own-phone photos.
Rules: docs/plan/analysis_plan_changes.md 2026-11-10. Cleaned labels (Sections J, O). Writes results/analysis/sectionP_*.csv and SECTION_P.md.
Run:  python -I safeguard/evaluate_safeguard.py"""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
import glob
import sys
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
ROOT = "D:/Capstone Project/"
OUT = ROOT + "results/analysis/"


def work(path):
    import ecg_traffic_light as T
    r = T.check_npz(path)
    return dict(variant_id=os.path.basename(path)[:-4], light=r["light"], score=r["score"], reasons="; ".join(r["reasons"]), detector_spread_bpm=r["detector_spread_bpm"])


def wilson(k, n, z=1.96):
    if n == 0:
        return (np.nan, np.nan)
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return c - h, c + h


def table(df, wrong_col="wrong"):
    rows = []
    totw = int(df[wrong_col].sum())
    totr = int((~df[wrong_col]).sum())
    for lt in ("GREEN", "AMBER", "RED"):
        g = df[df.light == lt]
        k, n = int(g[wrong_col].sum()), len(g)
        lo, hi = wilson(k, n)
        rows.append(dict(light=lt, readings=n, wrong=k, wrong_rate=(f"{100 * k / n:.1f}% ({100 * lo:.1f}-{100 * hi:.1f})" if n else "n/a"),
                         share_of_all_wrong=f"{100 * k / totw:.0f}%" if totw else "n/a", share_of_all_right=f"{100 * (n - k) / totr:.0f}%" if totr else "n/a"))
    return pd.DataFrame(rows)


if __name__ == "__main__":
    from concurrent.futures import ProcessPoolExecutor
    sys.path.insert(0, ROOT + "safeguard")
    import evaluate_safeguard as me
    dirs = [ROOT + "results/armCext/armCext_digitized_12lead_all/", ROOT + "results/armC/armC_digitized_12lead/", ROOT + "results/ownphotos/kaggle_out/ownphotos_digitized_12lead/"]
    files = [f for d in dirs for f in sorted(glob.glob(d + "*.npz"))]
    assert len(files) == 900 + 360 + 60, len(files)
    with ProcessPoolExecutor(6) as ex:
        res = list(ex.map(me.work, files, chunksize=4))
    lt = pd.DataFrame(res)
    lt.to_csv(OUT + "sectionP_lights_all.csv", index=False)
    print("DONE", len(lt))
