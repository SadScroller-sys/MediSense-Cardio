"""Shared constants and comparison helpers for the ECG digitization pipeline.

Factored out of gate2_compare.py / multi_sample_compare.py / real_image_compare.py,
which had this logic duplicated three times with copy-paste drift between them.
Those three scripts are left as-is; this module is what the harness (and any new
script) should import instead of re-deriving the same numbers a fourth time.
"""
import neurokit2 as nk
import numpy as np
import pandas as pd
import wfdb

# Open-ECG-Digitizer's own internal output rate for its "_timeseries_canonical.csv"
# files, regardless of the input image's actual page timing. Confirmed in the Day 1
# spike (10000 rows / 10s page = 1000 Hz) and consistent across every run since.
FS_CANONICAL = 1000.0

# The tool documents its CSV output in microvolts; ground-truth WFDB records are in
# millivolts, so every digitized signal needs this conversion before comparison.
UV_TO_MV = 1000.0


def load_ground_truth(record_path, lead="II"):
    """Load a WFDB ground-truth record. Returns (signal_mv, fs, all_lead_names)."""
    record = wfdb.rdrecord(record_path)
    lead_idx = record.sig_name.index(lead)
    signal = record.p_signal[:, lead_idx]
    return signal, record.fs, record.sig_name


def load_digitized(csv_path, lead="II"):
    """Load one lead from a digitizer '_timeseries_canonical.csv', converted to mV.

    NaN padding (columns for leads/time the digitizer didn't recover) is dropped,
    not zero-filled -- a dropped sample is a missing measurement, not a zero reading.
    """
    df = pd.read_csv(csv_path)
    signal_uv = df[lead].dropna().to_numpy()
    return signal_uv / UV_TO_MV


def extract_hr(signal, fs):
    """Return (mean_hr_bpm, n_beats) for one lead. (nan, n) if too few beats to trust."""
    try:
        peaks, _ = nk.ecg_peaks(signal, sampling_rate=fs)
        n_beats = int(peaks["ECG_R_Peaks"].sum())
        if n_beats < 2:
            return float("nan"), n_beats
        hr = np.nanmean(nk.ecg_rate(peaks, sampling_rate=fs, desired_length=len(signal)))
        return hr, n_beats
    except Exception:
        return float("nan"), 0


def compare_heart_rate(gt_record_path, digitized_csv_path, lead="II"):
    """One-call ground-truth-vs-digitized HR comparison.

    Same computation as multi_sample_compare.py's per-record loop body, as a
    reusable function instead of copy-pasted per script.
    """
    gt_signal, fs_gt, _ = load_ground_truth(gt_record_path, lead)
    gt_hr, n_gt_beats = extract_hr(gt_signal, fs_gt)

    dig_signal = load_digitized(digitized_csv_path, lead)
    dig_hr, n_dig_beats = extract_hr(dig_signal, FS_CANONICAL)

    diff = abs(gt_hr - dig_hr) if not np.isnan(dig_hr) else float("nan")
    dig_duration_s = len(dig_signal) / FS_CANONICAL

    return {
        "gt_hr": gt_hr,
        "dig_hr": dig_hr,
        "diff_bpm": diff,
        "gt_beats": n_gt_beats,
        "dig_beats": n_dig_beats,
        "dig_duration_s": dig_duration_s,
    }
