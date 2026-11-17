"""Re-run the QTc false-reassurance analysis with Fridericia as well as Bazett, and show how
the count changes with the error tolerance (none, 10 ms, 20 ms).

Reads results/v2_intervals/results_v2.csv only. Does not change any saved result.
Definitions mirror scripts/analysis/analyze_v2_intervals.py:
  * reliable record = at most 6 of 31 versions unreadable (dig_hr missing)
  * false reassurance = truth abnormal, digitised normal
  * "real" = also (a) the same record is not already wrong on its own clean image and
             (b) the digitised QTc is under-read by more than the tolerance (diff = truth - digitised)
Thresholds: QTc >= 450 ms (male), >= 460 ms (female), the AHA/ACCF/HRS values used in the paper.
"""
import numpy as np
import pandas as pd
from scipy import stats

df = pd.read_csv("D:/Capstone Project/results/v2_intervals/results_v2.csv")

unread = df.groupby("record")["dig_hr"].apply(lambda s: s.isna().sum())
reliable = set(unread[unread <= 6].index)
df = df[df["record"].isin(reliable)].copy()
print(f"reliable records: {len(reliable)} of {df['record'].nunique() + (50 - len(reliable))}; tests: {len(df)}")


def qtc(qt_ms, hr, kind):
    rr = 60.0 / hr
    return qt_ms / (np.sqrt(rr) if kind == "bazett" else np.cbrt(rr))


def thr(sex):
    return np.where(sex == "female", 460.0, 450.0)


# sanity check: our Bazett recomputation must reproduce the stored columns
chk = qtc(df["gt_qt_ms"], df["gt_hr"], "bazett")
print("Bazett recomputation vs stored gt_qtc_ms: max abs diff = %.2f ms" % np.nanmax(np.abs(chk - df["gt_qtc_ms"])))
stored_ab = df["gt_qtc_abnormal"].astype(bool)
mine_ab = (chk >= thr(df["sex"])).astype(bool)
print("ground-truth abnormal flag agreement with stored column: %.4f" % (stored_ab == mine_ab).mean())


def run(kind, tol):
    d = df.copy()
    d["gt_q"] = qtc(d["gt_qt_ms"], d["gt_hr"], kind)
    d["dig_q"] = qtc(d["dig_qt_ms"], d["dig_hr"], kind)
    t = thr(d["sex"])
    d["gt_ab"] = d["gt_q"] >= t
    d["dig_ab"] = d["dig_q"] >= t
    d["diff"] = d["gt_q"] - d["dig_q"]
    d["usable"] = d["dig_q"].notna()
    d["fr"] = d["usable"] & d["gt_ab"] & ~d["dig_ab"]
    clean_fr = d[d["axis"] == "clean"].set_index("record")["fr"]
    d["clean_ok"] = ~d["record"].map(clean_fr).fillna(False).astype(bool)
    d["real_fr"] = d["fr"] & d["clean_ok"] & (d["diff"] > tol)
    at_risk_records = d[d["gt_ab"]]["record"].nunique()
    ar = d[d["gt_ab"] & d["clean_ok"] & (d["axis"] != "clean")]
    n = len(ar)
    k = int(ar["real_fr"].sum())
    lo, hi = stats.binomtest(k, n).proportion_ci(confidence_level=0.95, method="wilson") if n else (np.nan, np.nan)
    return dict(formula=kind, tol_ms=tol, at_risk_records=at_risk_records,
                usable_at_risk_records=ar["record"].nunique(), at_risk_tests=n,
                false_reassurance_all=int(d["fr"].sum()), real_FR_events=k,
                real_FR_records=ar[ar["real_fr"]]["record"].nunique(),
                real_FR_rate=round(k / n, 4) if n else np.nan, wilson95=f"{lo:.3f}-{hi:.3f}")


rows = [run(k, tol) for k in ("bazett", "fridericia") for tol in (0, 10, 20)]
out = pd.DataFrame(rows)
pd.set_option("display.width", 250)
print(out.to_string(index=False))

# where do the events sit, per formula (tolerance 10 ms), by damage type
for kind in ("bazett", "fridericia"):
    d = df.copy()
    d["gt_q"] = qtc(d["gt_qt_ms"], d["gt_hr"], kind)
    d["dig_q"] = qtc(d["dig_qt_ms"], d["dig_hr"], kind)
    t = thr(d["sex"])
    d["gt_ab"] = d["gt_q"] >= t
    d["fr"] = d["dig_q"].notna() & d["gt_ab"] & ~(d["dig_q"] >= t)
    d["diff"] = d["gt_q"] - d["dig_q"]
    cf = d[d["axis"] == "clean"].set_index("record")["fr"]
    d["ok"] = ~d["record"].map(cf).fillna(False).astype(bool)
    ev = d[d["fr"] & d["ok"] & (d["diff"] > 10) & (d["axis"] != "clean")]
    print(f"\n{kind}: real false-reassurance events by damage type:", ev.groupby("axis").size().to_dict(),
          "| by record:", ev.groupby("record").size().to_dict())

# how the ground-truth abnormal set changes with the formula
g = df[df["axis"] == "clean"].copy()
for kind in ("bazett", "fridericia"):
    g["ab_" + kind] = qtc(g["gt_qt_ms"], g["gt_hr"], kind) >= thr(g["sex"])
print("\nrecords truly prolonged (clean image, ground truth): Bazett %d, Fridericia %d; flip to normal with Fridericia: %d; flip to abnormal: %d"
      % (g["ab_bazett"].sum(), g["ab_fridericia"].sum(),
         (g["ab_bazett"] & ~g["ab_fridericia"]).sum(), (~g["ab_bazett"] & g["ab_fridericia"]).sum()))

# measurement error on clean images
c = df[df["axis"] == "clean"]
for kind in ("bazett", "fridericia"):
    e = (qtc(c["dig_qt_ms"], c["dig_hr"], kind) - qtc(c["gt_qt_ms"], c["gt_hr"], kind)).abs()
    print(f"{kind}: clean-image |QTc error| median {e.median():.1f} ms, 95th percentile {e.quantile(.95):.1f} ms")
