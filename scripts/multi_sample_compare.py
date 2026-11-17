"""Compare digitizer output against ground truth across multiple real records."""
import neurokit2 as nk
import numpy as np
import pandas as pd
import wfdb

RECORD_IDS = ["00001_lr", "00002_lr", "00003_lr", "00004_lr", "00005_lr", "00006_lr"]
FS_CANONICAL = 1000.0

results = []
for rid in RECORD_IDS:
    record = wfdb.rdrecord(f"data/sample/{rid}")
    fs_gt = record.fs
    lead_idx = record.sig_name.index("II")
    gt_signal = record.p_signal[:, lead_idx]

    digitized = pd.read_csv(f"results/multi_sample_test/digitized/{rid}-0_timeseries_canonical.csv")
    dig_signal_mv = digitized["II"].dropna().to_numpy() / 1000.0

    gt_peaks, _ = nk.ecg_peaks(gt_signal, sampling_rate=fs_gt)
    gt_hr = np.nanmean(nk.ecg_rate(gt_peaks, sampling_rate=fs_gt, desired_length=len(gt_signal)))
    n_gt_beats = int(gt_peaks["ECG_R_Peaks"].sum())

    try:
        dig_peaks, _ = nk.ecg_peaks(dig_signal_mv, sampling_rate=FS_CANONICAL)
        n_dig_beats = int(dig_peaks["ECG_R_Peaks"].sum())
        dig_hr = np.nanmean(nk.ecg_rate(dig_peaks, sampling_rate=FS_CANONICAL, desired_length=len(dig_signal_mv)))
    except Exception as e:
        dig_hr, n_dig_beats = float("nan"), 0

    diff = abs(gt_hr - dig_hr) if not np.isnan(dig_hr) else float("nan")
    dig_duration = len(dig_signal_mv) / FS_CANONICAL

    results.append({
        "record": rid, "gt_hr": gt_hr, "dig_hr": dig_hr, "diff_bpm": diff,
        "gt_beats": n_gt_beats, "dig_beats": n_dig_beats, "dig_duration_s": dig_duration,
    })
    print(f"{rid}: true={gt_hr:.1f} bpm ({n_gt_beats} beats) | "
          f"read={dig_hr:.1f} bpm ({n_dig_beats} beats, {dig_duration:.1f}s recovered) | "
          f"diff={diff:.1f} bpm")

df = pd.DataFrame(results)
print("\n=== Summary ===")
valid = df.dropna(subset=["diff_bpm"])
print(f"Records with a usable heart-rate reading: {len(valid)}/{len(df)}")
if len(valid):
    print(f"Average difference from the true heart rate: {valid['diff_bpm'].mean():.2f} bpm")
    print(f"Best case: {valid['diff_bpm'].min():.2f} bpm off")
    print(f"Worst case: {valid['diff_bpm'].max():.2f} bpm off")
df.to_csv("results/multi_sample_test/summary.csv", index=False)
