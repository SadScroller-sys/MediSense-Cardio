"""
Gate 2 walking skeleton -- THROWAWAY SPIKE, not production code.

Purpose: prove one PTB-XL record can go image -> numbers on this machine, end to end.
Steps: load ground truth -> draw a simple ECG-paper-style image -> run the digitizer ->
extract features from both -> compare.

The official ECG-Image-Kit generator needs an old TensorFlow build with no wheel for
this Python version (see docs/PROGRESS-LOG.md), so this uses a minimal matplotlib
renderer instead -- good enough to prove the pipeline connects. Real tool selection
happens in Week 2 per docs/PLAN.md.
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import wfdb

ROOT = Path(__file__).resolve().parent.parent
SAMPLE_RECORD = ROOT / "data" / "sample" / "00001_lr"
OUT_DIR = ROOT / "results" / "gate2_spike"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Standard 4x3 clinical layout (3 columns of 4 leads, 10s @ 100Hz -> 2.5s per lead)
LAYOUT = [
    ["I", "AVR", "V1", "V4"],
    ["II", "AVL", "V2", "V5"],
    ["III", "AVF", "V3", "V6"],
]
MM_PER_MV = 10.0   # standard ECG paper gain
MM_PER_S = 25.0    # standard ECG paper speed
PX_PER_MM = 8.0    # rendering resolution


def render_ecg_image(record: wfdb.Record, out_path: Path) -> None:
    fs = record.fs
    sig = record.p_signal  # (samples, leads), in mV
    names = record.sig_name
    seconds_per_col = 2.5
    samples_per_col = int(seconds_per_col * fs)

    n_rows, n_cols = len(LAYOUT), len(LAYOUT[0])
    fig_w_mm = n_cols * seconds_per_col * MM_PER_S + 20
    fig_h_mm = n_rows * 40 + 20
    fig = plt.figure(figsize=(fig_w_mm / 25.4, fig_h_mm / 25.4), dpi=PX_PER_MM * 25.4 / 10)
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_xlim(0, fig_w_mm)
    ax.set_ylim(0, fig_h_mm)
    ax.invert_yaxis()
    ax.axis("off")

    # Grid: fine 1mm lines, bold 5mm lines -- standard ECG paper
    for x in np.arange(0, fig_w_mm, 1):
        ax.axvline(x, color="#f2a0a0", linewidth=0.3 if x % 5 else 0.8, zorder=0)
    for y in np.arange(0, fig_h_mm, 1):
        ax.axhline(y, color="#f2a0a0", linewidth=0.3 if y % 5 else 0.8, zorder=0)

    for r, row in enumerate(LAYOUT):
        for c, lead_name in enumerate(row):
            lead_idx = names.index(lead_name)
            start = c * samples_per_col
            end = start + samples_per_col
            trace = sig[start:end, lead_idx]
            t = np.arange(len(trace)) / fs
            x0 = 10 + c * seconds_per_col * MM_PER_S
            y0 = 20 + r * 40
            x = x0 + t * MM_PER_S
            y = y0 - trace * MM_PER_MV
            ax.plot(x, y, color="black", linewidth=0.8, zorder=2)
            ax.text(x0, y0 - 15, lead_name, fontsize=6, zorder=3)

    fig.savefig(out_path, dpi=PX_PER_MM * 25.4 / 10)
    plt.close(fig)


def main() -> int:
    print("=== Gate 2 walking skeleton ===")
    print(f"Loading ground truth record: {SAMPLE_RECORD}")
    record = wfdb.rdrecord(str(SAMPLE_RECORD))
    print(f"  {record.sig_name}, fs={record.fs}, shape={record.p_signal.shape}")

    img_path = OUT_DIR / "00001_lr_synthetic.png"
    print(f"Rendering ECG image to: {img_path}")
    render_ecg_image(record, img_path)
    print(f"  wrote {img_path.stat().st_size / 1024:.0f} KB")

    print("\nNext step (not yet run): feed this image to Open-ECG-Digitizer")
    print("  and compare its output against this record's ground truth.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
