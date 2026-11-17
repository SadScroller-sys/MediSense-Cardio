"""Gate 2 spike -- compare digitizer output against ground truth for the leads that extracted cleanly."""
import neurokit2 as nk
import numpy as np
import pandas as pd
import wfdb

GT_RECORD = "data/sample/00001_lr"
DIGITIZED_CSV = "results/gate2_spike/digitizer_output/00001_lr_synthetic_timeseries_canonical.csv"

record = wfdb.rdrecord(GT_RECORD)
fs_gt = record.fs
leads_gt = record.sig_name

digitized = pd.read_csv(DIGITIZED_CSV)

print("=== Lead-by-lead: how much data survived digitization ===")
for lead in digitized.columns:
    n_valid = digitized[lead].notna().sum()
    print(f"  {lead:5s}: {n_valid}/{len(digitized)} samples recovered")

print("\n=== Comparing Lead II (most complete) against ground truth ===")
lead_idx = leads_gt.index("II")
gt_signal = record.p_signal[:, lead_idx]  # mV, 100 Hz, 10s

dig_signal_uv = digitized["II"].dropna().to_numpy()
dig_signal_mv = dig_signal_uv / 1000.0  # tool outputs microvolts per its README

# The tool's "canonical" CSV is on its OWN internal timeline: config says
# target_num_samples=10000 "= time * desired sample rate" for a 10s page, i.e. 1000 Hz.
# (10000 rows / 10s matches this.) Each lead only has real values where it actually
# appeared in our rendered image (~2.5s-wide column), rest is NaN padding.
FS_CANONICAL = 1000.0
dig_duration_s = len(dig_signal_mv) / FS_CANONICAL

print(f"Ground truth: {len(gt_signal)} samples @ {fs_gt} Hz = {len(gt_signal)/fs_gt:.1f}s, "
      f"range [{gt_signal.min():.3f}, {gt_signal.max():.3f}] mV")
print(f"Digitized:    {len(dig_signal_mv)} samples @ {FS_CANONICAL:.0f} Hz (tool's internal rate) "
      f"= {dig_duration_s:.2f}s, range [{dig_signal_mv.min():.3f}, {dig_signal_mv.max():.3f}] mV")
print(f"(Our render put each lead in a ~2.5s-wide column, so ~{dig_duration_s:.1f}s recovered is "
      f"close to what was actually drawn for this lead -- consistent, not a data-loss problem.)")

try:
    gt_hr = nk.ecg_rate(nk.ecg_peaks(gt_signal, sampling_rate=fs_gt)[0], sampling_rate=fs_gt, desired_length=len(gt_signal))
    print(f"\nGround truth heart rate (full 10s): {np.nanmean(gt_hr):.1f} bpm")
except Exception as e:
    print(f"\nGround truth HR extraction failed: {e}")

try:
    dig_peaks, _ = nk.ecg_peaks(dig_signal_mv, sampling_rate=FS_CANONICAL)
    n_beats = int(dig_peaks["ECG_R_Peaks"].sum())
    print(f"Digitized signal: {n_beats} R-peaks detected in {dig_duration_s:.1f}s "
          f"({'enough for a rough rate estimate' if n_beats >= 2 else 'too few beats for a reliable rate'})")
    if n_beats >= 2:
        dig_hr = nk.ecg_rate(dig_peaks, sampling_rate=FS_CANONICAL, desired_length=len(dig_signal_mv))
        print(f"Digitized heart rate (from this short segment): {np.nanmean(dig_hr):.1f} bpm")
except Exception as e:
    print(f"Digitized HR extraction failed: {e}")

print(f"\nNote: only ~{dig_duration_s:.1f}s of Lead II survived because of the layout-mismatch "
      f"issue (tool assumed a different page template than what was drawn) -- see PROGRESS-LOG.md.")
