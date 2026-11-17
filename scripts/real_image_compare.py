"""Compare digitizer output (from the REAL ECG-Image-Kit image) against ground truth -- full-length Lead II."""
import neurokit2 as nk
import numpy as np
import pandas as pd
import wfdb

GT_RECORD = "data/sample/00001_lr"
DIGITIZED_CSV = "results/real_ecg_image_kit_test/digitizer_output/00001_lr-0_timeseries_canonical.csv"
FS_CANONICAL = 1000.0  # tool's internal rate, confirmed in the Day 1 spike

record = wfdb.rdrecord(GT_RECORD)
fs_gt = record.fs
leads_gt = record.sig_name
lead_idx = leads_gt.index("II")
gt_signal = record.p_signal[:, lead_idx]  # mV, 100 Hz, 10s

digitized = pd.read_csv(DIGITIZED_CSV)
dig_signal_uv = digitized["II"].dropna().to_numpy()
dig_signal_mv = dig_signal_uv / 1000.0  # tool outputs microvolts

print(f"Ground truth: {len(gt_signal)} samples @ {fs_gt} Hz = {len(gt_signal)/fs_gt:.1f}s, "
      f"range [{gt_signal.min():.3f}, {gt_signal.max():.3f}] mV")
print(f"Digitized:    {len(dig_signal_mv)} samples @ {FS_CANONICAL:.0f} Hz = "
      f"{len(dig_signal_mv)/FS_CANONICAL:.1f}s, range [{dig_signal_mv.min():.3f}, {dig_signal_mv.max():.3f}] mV")

# Heart rate comparison
gt_peaks, _ = nk.ecg_peaks(gt_signal, sampling_rate=fs_gt)
gt_hr = nk.ecg_rate(gt_peaks, sampling_rate=fs_gt, desired_length=len(gt_signal))
print(f"\nGround truth heart rate: {np.nanmean(gt_hr):.1f} bpm ({int(gt_peaks['ECG_R_Peaks'].sum())} beats in {len(gt_signal)/fs_gt:.1f}s)")

dig_peaks, _ = nk.ecg_peaks(dig_signal_mv, sampling_rate=FS_CANONICAL)
n_beats = int(dig_peaks["ECG_R_Peaks"].sum())
dig_hr = nk.ecg_rate(dig_peaks, sampling_rate=FS_CANONICAL, desired_length=len(dig_signal_mv))
print(f"Digitized heart rate:    {np.nanmean(dig_hr):.1f} bpm ({n_beats} beats in {len(dig_signal_mv)/FS_CANONICAL:.1f}s)")

diff = abs(np.nanmean(gt_hr) - np.nanmean(dig_hr))
print(f"\nDifference: {diff:.1f} bpm")

# Amplitude / scale check
print(f"\nAmplitude check -- ground truth peak-to-peak: {gt_signal.max()-gt_signal.min():.3f} mV, "
      f"digitized peak-to-peak: {dig_signal_mv.max()-dig_signal_mv.min():.3f} mV")
