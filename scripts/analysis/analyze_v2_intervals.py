"""Local analysis of the v2 sweep (PR/QRS/QT/QTc), mirroring the structure of the
v1 Colab analysis notebooks (Part1 cleaning, Part1b per-record failures, Part2
outcome classification) but run locally against results/v2_intervals/results_v2.csv
-- no GPU needed for analysis, only the sweep itself needed Colab.

Reconstructs the same 50-record sample (pool seed=42, SCOPE_N=50) from the local
PTB-XL database files, exactly matching the notebook's Step 1 logic, so record
labels (is_abnormal, diagnostic_class, sex) can be joined in for classification.
"""
import ast
import numpy as np
import pandas as pd
from scipy import stats

DATA_DIR = r"D:\Capstone Project\data\ptbxl"
RESULTS_PATH = r"D:\Capstone Project\results\v2_intervals\results_v2.csv"
OUT_DIR = r"D:\Capstone Project\results\v2_intervals"

pd.set_option("display.width", 160)
pd.set_option("display.max_columns", 30)

# ---------------------------------------------------------------------------
# Step 1 (reconstructed): the same 50-record sample as the sweep notebook
# ---------------------------------------------------------------------------
database = pd.read_csv(f"{DATA_DIR}/ptbxl_database.csv")
scp_statements = pd.read_csv(f"{DATA_DIR}/scp_statements.csv").rename(columns={"Unnamed: 0": "code"})
code_to_class = dict(zip(scp_statements["code"], scp_statements["diagnostic_class"]))


def dominant_class(scp_codes_str):
    codes = ast.literal_eval(scp_codes_str)
    if not codes:
        return None
    top_code = max(codes, key=codes.get)
    return code_to_class.get(top_code)


database["diagnostic_class"] = database["scp_codes"].apply(dominant_class)
database["is_abnormal"] = database["diagnostic_class"].notna() & (database["diagnostic_class"] != "NORM")

rng_seed = 42
POOL_N = 500
normal_pool_all = database[~database["is_abnormal"]]
abnormal_pool_all = database[database["is_abnormal"]]
pool = pd.concat([
    normal_pool_all.sample(n=POOL_N // 2, random_state=rng_seed),
    abnormal_pool_all.sample(n=POOL_N - POOL_N // 2, random_state=rng_seed),
]).reset_index(drop=True)[["ecg_id", "filename_lr", "diagnostic_class", "is_abnormal", "sex", "age"]]

SCOPE_N = 50
normal_in_pool = pool[~pool["is_abnormal"]]
abnormal_in_pool = pool[pool["is_abnormal"]]
sample = pd.concat([
    normal_in_pool.sample(n=min(len(normal_in_pool), SCOPE_N // 2), random_state=rng_seed),
    abnormal_in_pool.sample(n=min(len(abnormal_in_pool), SCOPE_N - SCOPE_N // 2), random_state=rng_seed),
]).reset_index(drop=True)
sample["record"] = sample["filename_lr"].apply(lambda p: p.split("/")[-1])
print(f"Reconstructed sample: {len(sample)} records -- {int(sample['is_abnormal'].sum())} abnormal, "
      f"{int((~sample['is_abnormal']).sum())} normal.")

# ---------------------------------------------------------------------------
# Part 1 -- load + clean
# ---------------------------------------------------------------------------
raw = pd.read_csv(RESULTS_PATH)
print(f"\nRaw results_v2.csv: {len(raw)} rows, {raw['variant_id'].nunique()} unique variant_ids, "
      f"{raw['record'].nunique()} unique records.")
assert len(raw) == raw["variant_id"].nunique(), "duplicate variant_ids found -- investigate before proceeding"
assert len(raw) == 1550, f"expected 1550 rows, got {len(raw)}"

df = raw.merge(sample[["record", "diagnostic_class", "is_abnormal"]], on="record", how="left")
assert df["is_abnormal"].notna().all(), "some records in results_v2.csv did not match the reconstructed sample"

# level 0 = clean; axis names as written by the sweep notebook
df["axis"] = df["axis"].astype(str)
df["level"] = df["level"].astype(int)

n_unreadable = int(df["dig_hr"].isna().sum())
print(f"Unreadable (no dig_hr): {n_unreadable}/{len(df)} ({100*n_unreadable/len(df):.1f}%)")
n_qtc_missing = int(df["dig_qtc_ms"].isna().sum())
print(f"No digitized QTc: {n_qtc_missing}/{len(df)} ({100*n_qtc_missing/len(df):.1f}%)")

# Per-record failure counts (out of 31 versions each) -- same definition as v1's Part1b
per_record = df.groupby("record").agg(
    n_unreadable=("dig_hr", lambda s: int(s.isna().sum())),
    n_qtc_missing=("dig_qtc_ms", lambda s: int(s.isna().sum())),
    is_abnormal=("is_abnormal", "first"),
).reset_index()
per_record = per_record.sort_values("n_unreadable", ascending=False)
per_record.to_csv(f"{OUT_DIR}/per_record_failures_v2.csv", index=False)
print("\nWorst records by unreadable count (dig_hr):")
print(per_record.head(10).to_string(index=False))

RELIABLE_MAX_UNREADABLE = 6  # <=20% of 31, same threshold convention as v1
reliable_records = set(per_record[per_record["n_unreadable"] <= RELIABLE_MAX_UNREADABLE]["record"])
print(f"\nReliable records (<=20% unreadable): {len(reliable_records)}/50")
unreliable = per_record[per_record["n_unreadable"] > RELIABLE_MAX_UNREADABLE]
print("Excluded as unreliable:")
print(unreliable.to_string(index=False))

df["reliable"] = df["record"].isin(reliable_records)
rel = df[df["reliable"]].copy()
print(f"\nReliable-record tests: {len(rel)} ({rel['record'].nunique()} records)")

df.to_csv(f"{OUT_DIR}/results_v2_clean.csv", index=False)

# ---------------------------------------------------------------------------
# Part 2 -- interval error vs degradation (T2 tier: PR, QRS, QT, QTc)
# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
print("INTERVAL ERROR BY AXIS AND LEVEL (reliable records only)")
print("=" * 70)

metrics = ["diff_bpm", "diff_pr_ms", "diff_qrs_ms", "diff_qt_ms", "diff_qtc_ms"]
summary_rows = []
for axis in ["clean", "blur", "rotate", "jpeg", "resolution", "brightness", "gridcontrast"]:
    sub = rel[rel["axis"] == axis]
    for level in sorted(sub["level"].unique()):
        lvl_sub = sub[sub["level"] == level]
        row = {"axis": axis, "level": level, "n": len(lvl_sub)}
        for m in metrics:
            row[f"{m}_median"] = round(lvl_sub[m].median(), 2)
            row[f"{m}_mean"] = round(lvl_sub[m].mean(), 2)
        summary_rows.append(row)
summary_by_axis_level = pd.DataFrame(summary_rows)
summary_by_axis_level.to_csv(f"{OUT_DIR}/summary_intervals_by_axis_level.csv", index=False)
print(summary_by_axis_level.to_string(index=False))

# ---------------------------------------------------------------------------
# Part 3 -- QTc-based patient-facing outcome (T3 tier, analogous to the HR one)
# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
print("QTc OUTCOME CLASSIFICATION (T3-style, analogous to the heart-rate version)")
print("=" * 70)


def classify_qtc(row):
    gt_ab = row["gt_qtc_abnormal"]
    dig_ab = row["dig_qtc_abnormal"]
    if pd.isna(row["dig_qtc_ms"]):
        return "silent_drop"
    if pd.isna(gt_ab):
        return "gt_unavailable"
    if bool(gt_ab) and not bool(dig_ab):
        return "false_reassurance"
    if not bool(gt_ab) and bool(dig_ab):
        return "false_alarm"
    if bool(gt_ab) and bool(dig_ab):
        return "correct_abnormal"
    return "correct_normal"


rel["qtc_outcome"] = rel.apply(classify_qtc, axis=1)

# IMPORTANT correction (found during review): delineation of PR/QRS/QT/QTc from a
# reconstructed signal carries a real baseline measurement bias/noise (median ~20ms
# on the CLEAN image, vs ~0.1bpm for heart rate) -- some records are already
# misclassified as false reassurance on their own undamaged clean image, purely from
# this baseline noise, not from any degradation. Counting those as "degradation
# caused this" would be wrong. A false-reassurance event only counts as REAL here if
# (a) the same record's clean-image QTc was classified correctly (not already a false
# reassurance) AND (b) the digitized QTc is off from ground truth by >10ms (same
# threshold-artefact discipline as the HR analysis).
clean_outcome_by_record = rel[rel["axis"] == "clean"].set_index("record")["qtc_outcome"]
rel["clean_was_correct"] = rel["record"].map(clean_outcome_by_record) != "false_reassurance"

fr_mask = rel["qtc_outcome"] == "false_reassurance"
real_fr_mask = fr_mask & (rel["diff_qtc_ms"] > 10) & rel["clean_was_correct"]
already_wrong_on_clean_mask = fr_mask & ~rel["clean_was_correct"]
borderline_fr_mask = fr_mask & rel["clean_was_correct"] & ~(rel["diff_qtc_ms"] > 10)
n_borderline = int(borderline_fr_mask.sum())
n_already_wrong = int(already_wrong_on_clean_mask.sum())
print(f"False-reassurance events excluded because the SAME record already misclassifies on its "
      f"own clean image (baseline delineation noise, not degradation): {n_already_wrong}")

n_at_risk_records = rel[rel["gt_qtc_abnormal"] == True]["record"].nunique()
print(f"Records with a truly prolonged ground-truth QTc: {n_at_risk_records}")
print(f"Total false-reassurance events (QTc told normal, truly prolonged): {int(fr_mask.sum())}")
print(f"  of which REAL (>10ms off): {int(real_fr_mask.sum())}")
print(f"  of which borderline/threshold artefacts (<=10ms off): {n_borderline}")

print("\nOutcome counts (reliable-record tests):")
print(rel["qtc_outcome"].value_counts().to_string())

# Pooled by axis/level with Wilson 95% CI on the real-false-reassurance rate, among
# at-risk (gt_qtc_abnormal==True) tests whose record is ALSO correctly classified on
# its own clean image (excludes records whose baseline delineation noise already
# breaks them, per the correction above).
at_risk = rel[(rel["gt_qtc_abnormal"] == True) & (rel["clean_was_correct"])].copy()
at_risk["real_fr"] = real_fr_mask.reindex(at_risk.index, fill_value=False)
n_at_risk_records_corrected = at_risk["record"].nunique()
print(f"\nAt-risk records usable for degradation analysis (correct on clean, truly prolonged QTc): "
      f"{n_at_risk_records_corrected} (of {n_at_risk_records} total at-risk)")

pooled_rows = []
for axis in ["blur", "rotate", "jpeg", "resolution", "brightness", "gridcontrast"]:
    for level in [1, 2, 3, 4, 5]:
        sub = at_risk[(at_risk["axis"] == axis) & (at_risk["level"] == level)]
        n = len(sub)
        k = int(sub["real_fr"].sum())
        if n > 0:
            ci_low, ci_high = stats.binomtest(k, n).proportion_ci(confidence_level=0.95, method="wilson")
        else:
            ci_low, ci_high = (np.nan, np.nan)
        pooled_rows.append({"axis": axis, "level": level, "n_at_risk": n, "n_real_fr": k,
                             "rate": round(k / n, 3) if n else np.nan,
                             "wilson_low": round(ci_low, 3) if n else np.nan,
                             "wilson_high": round(ci_high, 3) if n else np.nan})
pooled = pd.DataFrame(pooled_rows)
pooled.to_csv(f"{OUT_DIR}/t3_qtc_pooled.csv", index=False)
print("\nPooled real-false-reassurance rate by axis/level (Wilson 95% CI):")
print(pooled[pooled["n_real_fr"] > 0].to_string(index=False))

rel.to_csv(f"{OUT_DIR}/t3_qtc_outcomes.csv", index=False)

# ---------------------------------------------------------------------------
# Cross-check against the heart-rate outcome (does QTc surface *new* false
# reassurance cases beyond what HR already caught, or the same ones?)
# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
print("CROSS-CHECK: HR-based vs QTc-based false reassurance (same test rows)")
print("=" * 70)


def classify_hr(row):
    def band(hr):
        if pd.isna(hr):
            return None
        if hr < 60:
            return "slow"
        if hr > 100:
            return "fast"
        return "normal"
    gt_band = band(row["gt_hr"])
    dig_band = band(row["dig_hr"])
    if dig_band is None:
        return "silent_drop"
    if gt_band in ("slow", "fast") and dig_band == "normal":
        return "false_reassurance"
    return "other"


rel["hr_outcome"] = rel.apply(classify_hr, axis=1)
hr_real_fr = rel[(rel["hr_outcome"] == "false_reassurance") & (rel["diff_bpm"] > 10)]
qtc_real_fr = rel[real_fr_mask]
print(f"HR real false-reassurance events: {len(hr_real_fr)} (variant_ids: {list(hr_real_fr['variant_id'])[:10]})")
print(f"QTc real false-reassurance events: {len(qtc_real_fr)} (variant_ids: {list(qtc_real_fr['variant_id'])[:10]})")
overlap = set(hr_real_fr["variant_id"]) & set(qtc_real_fr["variant_id"])
print(f"Overlap (same test flagged by both measures): {len(overlap)}")

print("\nDONE. Outputs written to:", OUT_DIR)
