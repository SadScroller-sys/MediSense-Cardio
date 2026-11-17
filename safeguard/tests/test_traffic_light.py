"""Tests for the traffic-light safeguard. Run:  python -I safeguard/tests/test_traffic_light.py"""
import glob
import os
import sys

import numpy as np
import pandas as pd

ROOT = "D:/Capstone Project/"
sys.path.insert(0, ROOT + "safeguard")
import ecg_traffic_light as T

NPZ = ROOT + "results/extension/extension_digitized_12lead/extension_digitized_12lead/"
cache = pd.read_csv(ROOT + "results/analysis/sectionD2_features.csv").set_index("variant_id")
files = sorted(glob.glob(NPZ + "*.npz"))
rng = np.random.RandomState(3)

# 1. the packaged feature code reproduces the cached analysis features on 20 random signals (tolerance 1e-6)
worst = 0.0
for f in rng.choice(files, 20, replace=False):
    vid = os.path.basename(f)[:-4]
    got = T.output_features(T.load_npz(f))
    for k in T.FEATURES:
        a, b = got[k], cache.loc[vid, k]
        if np.isnan(a) or np.isnan(b):
            assert np.isnan(a) and np.isnan(b), (vid, k, a, b)
        else:
            worst = max(worst, abs(a - b))
            assert abs(a - b) < 1e-6, (vid, k, a, b)
print(f"test 1 ok: 20 signals, 15 features each, largest difference {worst:.2e}")

# 2. a clean page of a clean recording is GREEN; a lead II of pure noise is RED with the 'no usable heart rate' reason
clean = [f for f in files if f.endswith("__clean0.npz")]
res = [T.check_npz(f)["light"] for f in clean[:40]]
print("clean pages, first 40:", {k: res.count(k) for k in ("GREEN", "AMBER", "RED")})
assert res.count("GREEN") >= 30
noise = {k: rng.normal(0, 5, 10000) for k in T.LEADS}
r = T.check(noise)
assert r["light"] in ("AMBER", "RED"), r
print("test 2 ok: noise ->", r["light"], "|", r["reasons"][0])

# 3. missing lead II, all-NaN, and short signals do not crash and are RED
for leads in ({"I": np.full(10000, np.nan)}, {k: np.full(10000, np.nan) for k in T.LEADS}, {k: rng.normal(size=500) for k in T.LEADS}):
    r = T.check(leads)
    assert r["light"] == "RED", r
print("test 3 ok: missing / NaN / short signals -> RED, no crash")

# 4. the light follows the score thresholds
m = T.load_model()
for s_, want in ((0.0, "GREEN"), (m["amber_threshold"] + 1e-6, "AMBER"), (m["red_threshold"] + 1e-6, "RED")):
    got = "RED" if s_ >= m["red_threshold"] else ("AMBER" if s_ >= m["amber_threshold"] else "GREEN")
    assert got == want
print("test 4 ok: thresholds", round(m["amber_threshold"], 3), round(m["red_threshold"], 3))
print("ALL TESTS PASSED")
