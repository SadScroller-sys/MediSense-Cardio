"""Section C (MASTER_PLAN section 4 / 4b items 1-6, 8): wrong-heart-rate and no-output rates by damage type and level.

Reads (never modifies):  results/v2_intervals/results_v2.csv  (first 50, development set)
                         results/extension/results_extension.csv (new 100, held-out replication in the same pool)
                         results/extension/reference_check_150.csv (reference-uncertain flag)
                         data/ptbxl/ptbxl_database.csv (PTB-XL noise / beat / pacemaker flags)
Writes:                  results/analysis/sectionC_*.csv and results/analysis/SECTION_C.md

Definitions (fixed in docs/plan/MASTER_PLAN.md section 4):
  no output   = digitiser gave no heart rate
  wrong HR    = output exists and |digitised - reference| > 5 bpm   (secondary > 10 bpm)  <- confirmatory outcome
  bad         = no output OR wrong > 5 bpm                          <- only as a secondary column
  reference-uncertain = 100 Hz and 500 Hz references differ by > 5 bpm (results/extension/reference_check_150.csv)
  flagged     = PTB-XL has any non-empty value in baseline_drift, static_noise, burst_noise, electrodes_problems, extra_beats, pacemaker
  unreliable  = more than 20% of the recording's versions give no output (first 50: > 6 of 31; new 100: > 2 of 13) -> excluded and listed
Rate denominators: every recording in the cell (no-output images count in the denominator and not as 'wrong').
Intervals: Wilson 95% (one image per recording per cell, so the recording is the unit).
"""
import os

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = "D:/Capstone Project"
OUT = f"{ROOT}/results/analysis"
os.makedirs(OUT, exist_ok=True)
SHARED_LEVELS = {0, 3, 5}
AXES = ["resolution", "blur", "rotate", "jpeg", "brightness", "gridcontrast"]


def wilson(k, n, z=1.96):
    if n == 0:
        return (np.nan, np.nan)
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return c - h, c + h


# ---------------------------------------------------------------- data
v = pd.read_csv(f"{ROOT}/results/v2_intervals/results_v2.csv")
e = pd.read_csv(f"{ROOT}/results/extension/results_extension.csv")
v["set"], e["set"] = "first50", "new100"
cols = ["set", "record", "axis", "level", "sex", "gt_hr", "dig_hr", "diff_bpm"]
d = pd.concat([v[cols], e[cols]], ignore_index=True)
d["ecg_id"] = d.record.str.split("_").str[0].astype(int)
d["none"] = d.dig_hr.isna()
d["wrong5"] = d.diff_bpm > 5          # diff_bpm = |digitised - reference|, NaN when no output -> False
d["wrong10"] = d.diff_bpm > 10
d["bad"] = d.none | d.wrong5
d["out"] = ~d.none

ref = pd.read_csv(f"{ROOT}/results/extension/reference_check_150.csv")
d = d.merge(ref[["record", "reference_uncertain"]], on="record", how="left")
assert d.reference_uncertain.notna().all()

db = pd.read_csv(f"{ROOT}/data/ptbxl/ptbxl_database.csv")
FLAGS = ["baseline_drift", "static_noise", "burst_noise", "electrodes_problems", "extra_beats", "pacemaker"]
db["flagged"] = db[FLAGS].apply(lambda s: s.notna() & (s.astype(str).str.strip() != ""), axis=0).any(axis=1)
d = d.merge(db[["ecg_id", "flagged", "age"]], on="ecg_id", how="left")
assert d.flagged.notna().all()

# unreliable recordings (rule from the plan)
nv = d.groupby(["set", "record"]).none.sum().reset_index()
limit = {"first50": 6, "new100": 2}
unrel = nv[nv.apply(lambda r: r.none > limit[r.set], axis=1)]
UNREL = set(unrel.record)
d["unreliable"] = d.record.isin(UNREL)

nrec = d.groupby("set").record.nunique().to_dict()
print("recordings per set:", nrec)
print("unreliable (excluded):", unrel.to_dict("records"))
print("flagged recordings:", d.drop_duplicates("record").groupby("set").flagged.sum().to_dict(),
      "| reference-uncertain:", d.drop_duplicates("record").groupby("set").reference_uncertain.sum().to_dict())

rel = d[~d.unreliable]
POPS = {
    "new100_reliable": rel[rel.set == "new100"],
    "new100_reliable_refcertain": rel[(rel.set == "new100") & ~rel.reference_uncertain],
    "first50_reliable": rel[rel.set == "first50"],
    "all150_reliable_shared": rel[rel.level.isin(SHARED_LEVELS)],
    "new100_unflagged": rel[(rel.set == "new100") & ~rel.flagged],
    "new100_unflagged_refcertain": rel[(rel.set == "new100") & ~rel.flagged & ~rel.reference_uncertain],
    "all150_unflagged_shared": rel[rel.level.isin(SHARED_LEVELS) & ~rel.flagged],
}


def rate_table(x, pop):
    rows = []
    for (ax, lv), g in x.groupby(["axis", "level"]):
        n = len(g)
        r = dict(population=pop, axis=ax, level=int(lv), n=n)
        for name, col in (("wrong5", "wrong5"), ("wrong10", "wrong10"), ("none", "none"), ("bad", "bad")):
            k = int(g[col].sum())
            lo, hi = wilson(k, n)
            r.update({f"{name}_k": k, f"{name}_pct": round(100 * k / n, 1),
                      f"{name}_lo": round(100 * lo, 1), f"{name}_hi": round(100 * hi, 1)})
        r["wrong5_among_output_pct"] = round(100 * g.wrong5.sum() / max(1, g.out.sum()), 1)
        r["median_abs_err_bpm"] = round(g.diff_bpm.median(), 2)
        rows.append(r)
    t = pd.DataFrame(rows)
    t["axis"] = pd.Categorical(t.axis, ["clean"] + AXES, ordered=True)
    return t.sort_values(["axis", "level"]).reset_index(drop=True)


rates = pd.concat([rate_table(x, p) for p, x in POPS.items()], ignore_index=True)
rates.to_csv(f"{OUT}/sectionC_rates.csv", index=False)

# ------------------------------------------------ C1 verdict (new 100, level 5)
def c1_verdict(pop):
    t = rates[(rates.population == pop) & (rates.level == 5)].set_index("axis").wrong5_pct
    t = t.reindex(AXES).astype(float)
    order = t.sort_values(ascending=False)
    res = {
        "resolution_highest": bool(t["resolution"] > t.drop("resolution").max()),
        "resolution_ge_20": bool(t["resolution"] >= 20),
        "blur_second": bool(order.index[1] == "blur"),
        "blur_ge_10": bool(t["blur"] >= 10),
        "jpeg_brightness_grid_lt_10": bool((t[["jpeg", "brightness", "gridcontrast"]] < 10).all()),
        "rotation_le_15": bool(t["rotate"] <= 15),
    }
    res["ALL_MET"] = all(res.values())
    return t.to_dict(), res


c1 = {p: c1_verdict(p) for p in ("new100_reliable", "new100_reliable_refcertain", "all150_reliable_shared")}

# ---------------------------------------------- C2 (descriptive, unflagged, level 5 and clean)
def c2_rows(pop):
    t = rates[(rates.population == pop) & ((rates.level == 5) | (rates.axis == "clean"))]
    t = t[t.axis.isin(["clean", "rotate", "jpeg", "brightness", "gridcontrast"])]
    cap = {"clean": 5, "rotate": 10, "jpeg": 5, "brightness": 5, "gridcontrast": 5}
    t = t.assign(limit_pct=t.axis.map(cap), consistent=lambda x: x.wrong5_pct <= x.limit_pct)
    return t[["population", "axis", "level", "n", "wrong5_k", "wrong5_pct", "wrong5_lo", "wrong5_hi", "none_k", "none_pct",
              "bad_pct", "limit_pct", "consistent"]]


c2 = pd.concat([c2_rows(p) for p in ("new100_unflagged", "new100_unflagged_refcertain", "all150_unflagged_shared")])
c2.to_csv(f"{OUT}/sectionC_c2_unflagged.csv", index=False)

# ---------------------------------------------- breaking point (first 50 only): smallest level with wrong5 >= 10%
bp = []
f50 = rates[rates.population == "first50_reliable"]
for ax in AXES:
    t = f50[f50.axis == ax].sort_values("level")
    hit = t[t.wrong5_pct >= 10]
    bp.append(dict(axis=ax, breaking_level=int(hit.level.min()) if len(hit) else None,
                   rates_by_level={int(l): float(p) for l, p in zip(t.level, t.wrong5_pct)}))
bp = pd.DataFrame(bp)
bp.to_csv(f"{OUT}/sectionC_breaking_point.csv", index=False)

# ---------------------------------------------- five-outcome table (HR 60-100 = normal; a convention)
def five(x):
    tn = x.gt_hr.between(60, 100)
    dn = x.dig_hr.between(60, 100)
    cat = np.select([x.none, tn & dn, ~tn & ~dn & x.out, tn & ~dn & x.out, ~tn & dn & x.out],
                    ["no_answer", "correct_normal", "correct_abnormal", "false_alarm", "false_reassurance"], "other")
    return pd.Series(cat, index=x.index)


rows = []
for pop in ("first50_reliable", "all150_reliable_shared"):
    x = POPS[pop].copy()
    x["cat"] = five(x)
    assert (x.cat != "other").all()
    ct = x.groupby(["axis", "level"]).cat.value_counts().unstack(fill_value=0)
    for c in ["correct_normal", "correct_abnormal", "false_alarm", "false_reassurance", "no_answer"]:
        if c not in ct:
            ct[c] = 0
    ct["n"] = ct.sum(axis=1)
    ct = ct.reset_index()
    ct.insert(0, "population", pop)
    rows.append(ct)
five_t = pd.concat(rows, ignore_index=True)
five_t.to_csv(f"{OUT}/sectionC_five_outcomes.csv", index=False)

# ---------------------------------------------- dose-response (first 50, reliable): level vs error, per damage type
cl = POPS["first50_reliable"]
dr = []
for ax in AXES:
    g = pd.concat([cl[cl.axis == "clean"], cl[cl.axis == ax]])  # clean = level 0 for every axis
    go = g[g.out]
    rho, p = spearmanr(go.level, go.diff_bpm)
    rho2, p2 = spearmanr(g.level, g.wrong5.astype(int))
    r = rates[(rates.population == "first50_reliable") & (rates.axis == ax)].sort_values("level").wrong5_pct.tolist()
    dr.append(dict(axis=ax, spearman_level_vs_abs_error=round(rho, 3), p_error=p, spearman_level_vs_wrong5=round(rho2, 3), p_wrong5=p2,
                   rates_levels_1_to_5=r, monotone_nondecreasing=bool(all(np.diff(r) >= 0))))
dr = pd.DataFrame(dr)
dr['p_error'] = dr.p_error.map(lambda x: float(f'{x:.2g}'))
dr['p_wrong5'] = dr.p_wrong5.map(lambda x: float(f'{x:.2g}'))
dr.to_csv(f"{OUT}/sectionC_dose_response.csv", index=False)

# ---------------------------------------------- report
def md_table(t):
    t = t.copy()
    head = "| " + " | ".join(map(str, t.columns)) + " |\n|" + "---|" * len(t.columns) + "\n"
    return head + "\n".join("| " + " | ".join("" if (isinstance(x, float) and np.isnan(x)) else str(x) for x in r) + " |" for r in t.itertuples(index=False))


def view(pop, levels=None):
    t = rates[rates.population == pop]
    if levels is not None:
        t = t[t.level.isin(levels)]
    t = t.assign(wrong_5bpm=t.apply(lambda r: f"{r.wrong5_k}/{r.n} = {r.wrong5_pct}% ({r.wrong5_lo}-{r.wrong5_hi})", axis=1),
                 no_output=t.apply(lambda r: f"{r.none_k} = {r.none_pct}%", axis=1),
                 wrong_10bpm=t.wrong10_pct.astype(str) + "%", bad_secondary=t.bad_pct.astype(str) + "%")
    return md_table(t[["axis", "level", "n", "wrong_5bpm", "wrong_10bpm", "no_output", "bad_secondary"]])


L = []
L.append("# Section C results: wrong heart rate and no output by damage type and level\n")
L.append("*Generated by `scripts/analysis/section_C.py`. Rules: `docs/plan/MASTER_PLAN.md` section 4. Descriptive tables; the only verdict here is C1 (and C2 is descriptive).*\n")
L.append("## Who is in the tables\n")
L.append(f"- Recordings: first 50 (development set) and new 100 (held-out replication, same pool). Unreliable recordings excluded: "
         + (", ".join(f"{r.record} ({r.set}, {int(r.none)} versions without output)" for r in unrel.itertuples()) or "none") + ".")
L.append(f"- Reference-uncertain recordings (100 Hz vs 500 Hz reference differ by more than 5 bpm): first 50 = "
         f"{int(d[(d.set=='first50')].drop_duplicates('record').reference_uncertain.sum())}, new 100 = "
         f"{int(d[(d.set=='new100')].drop_duplicates('record').reference_uncertain.sum())}.")
L.append(f"- PTB-XL flagged recordings: first 50 = {int(d[d.set=='first50'].drop_duplicates('record').flagged.sum())}, "
         f"new 100 = {int(d[d.set=='new100'].drop_duplicates('record').flagged.sum())}.")
L.append("- Outcome: 'wrong 5 bpm' = output exists and |digitised - reference| > 5 bpm, as a share of ALL recordings in the cell. "
         "'No output' is reported separately. 'bad' (either) is a secondary column. 95% Wilson interval in brackets.\n")

L.append("## C1: new 100, level 5 and 3, clean (the confirmatory table)\n")
L.append(view("new100_reliable") + "\n")
for p, (rt, res) in c1.items():
    L.append(f"**C1 conditions on `{p}` (level 5, wrong 5 bpm %):** " + ", ".join(f"{k} {v:.1f}" for k, v in rt.items()))
    L.append("  " + "; ".join(f"{k}: {'met' if b else 'NOT met'}" for k, b in res.items()) + "\n")
both = c1["new100_reliable"][1]["ALL_MET"] and c1["new100_reliable_refcertain"][1]["ALL_MET"]
L.append(f"**C1 verdict (must hold with and without reference-uncertain recordings): {'SUPPORTED' if both else 'NOT SUPPORTED'}**\n")

L.append("## First 50, all five levels (development set)\n")
L.append(view("first50_reliable") + "\n")
L.append("Breaking point (smallest level with wrong 5 bpm at least 10%), first 50 only:\n")
L.append(md_table(bp) + "\n")

L.append("## All 150 together, shared versions only (clean, level 3, level 5)\n")
L.append(view("all150_reliable_shared") + "\n")

L.append("## C2 (descriptive): unflagged recordings, level 5 and clean\n")
L.append(md_table(c2.drop(columns=["level"])) + "\n")

L.append("## Five-outcome table (HR 60 to 100 bpm = normal, a convention), all 150 shared versions\n")
L.append(md_table(five_t[five_t.population == "all150_reliable_shared"].drop(columns="population")) + "\n")

L.append("## Dose-response (first 50): does the error grow with the level? (exploratory; p-values ignore that the same recording appears at every level)\n")
L.append(md_table(dr) + "\n")
open(f"{OUT}/SECTION_C.md", "w", encoding="utf-8").write("\n".join(L))

# console summary
pd.set_option("display.width", 250)
print("\nC1 new100_reliable level 5:", c1["new100_reliable"][0])
for p, (rt, res) in c1.items():
    print(p, res)
print("\nC2:\n", c2[["population", "axis", "n", "wrong5_k", "wrong5_pct", "none_pct", "limit_pct", "consistent"]].to_string(index=False))
print("\nbreaking point:\n", bp.to_string(index=False))
print("\ndose-response:\n", dr.round(4).to_string(index=False))
print("wrote", OUT)
