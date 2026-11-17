"""Journal figures from real outputs:
 B. Step 3 validation: ground-truth vs digitized lead II for the 6-record test (clean images) + HR table.
 C. Bland-Altman on clean images (HR, QTc; QTc against the 500 Hz ground truth).
 D. Interval error vs degradation level (QRS and QTc, 500 Hz ground truth), median with IQR band.
Single hue, one measure per axis, thin marks, numbers written where useful.
"""
import os, sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, r"D:\Capstone Project")
from scripts.harness.common import load_ground_truth, load_digitized, extract_hr, FS_CANONICAL

OUT = r"D:\Capstone Project\docs\journal\figures"
TAB = r"D:\Capstone Project\docs\journal\tables"
os.makedirs(OUT, exist_ok=True); os.makedirs(TAB, exist_ok=True)
BLUE, BLUE_D, INK, MUTE, GRID = "#2a78d6", "#1b4f91", "#0b0b0b", "#52514e", "#dcdcd8"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 7, "axes.edgecolor": MUTE, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.linewidth": 0.6, "figure.dpi": 130})

# ------------------------------------------------ B. 6-record validation (Step 3)
rows = []
fig, axs = plt.subplots(2, 3, figsize=(7.2, 3.6), sharey=False)
for ax, n in zip(axs.flat, range(1, 7)):
    rid = f"{n:05d}_lr"
    folder = f"{(n // 1000) * 1000:05d}"
    gt, fs, _ = load_ground_truth(rf"D:\Capstone Project\data\ptbxl\records100\{folder}\{rid}", "II")
    dg = load_digitized(rf"D:\Capstone Project\results\multi_sample_test\digitized\{rid}-0_timeseries_canonical.csv", "II")
    gt_hr, _ = extract_hr(gt, fs)
    dg_hr, _ = extract_hr(dg, FS_CANONICAL)
    rows.append({"record": rid, "true_hr_bpm": round(gt_hr, 1),
                 "digitized_hr_bpm": round(dg_hr, 1) if not np.isnan(dg_hr) else np.nan,
                 "abs_error_bpm": round(abs(gt_hr - dg_hr), 2) if not np.isnan(dg_hr) else np.nan,
                 "digitized_seconds": round(len(dg) / FS_CANONICAL, 1)})
    t_gt, t_dg = np.arange(len(gt)) / fs, np.arange(len(dg)) / FS_CANONICAL
    ax.plot(t_gt, gt, color=MUTE, lw=0.8, label="ground truth")
    ax.plot(t_dg, dg, color=BLUE, lw=0.8, label="digitized")
    ax.set_xlim(0, 10)
    ax.set_title(f"{rid}: {rows[-1]["true_hr_bpm"]} vs {rows[-1]["digitized_hr_bpm"] if not np.isnan(rows[-1]["digitized_hr_bpm"]) else "no reading"} bpm", fontsize=7, loc="left")
    ax.grid(axis="y", color=GRID, lw=0.4)
for ax in axs[1, :]: ax.set_xlabel("time (s)")
for ax in axs[:, 0]: ax.set_ylabel("lead II (mV)")
axs[0, 0].legend(frameon=False, fontsize=6, loc="upper right")
fig.tight_layout()
for e in ("png", "pdf"): fig.savefig(os.path.join(OUT, f"fig_step3_validation.{e}"), dpi=300)
pd.DataFrame(rows).to_csv(os.path.join(TAB, "step3_six_record_validation.csv"), index=False)
print(pd.DataFrame(rows).to_string(index=False))

# ------------------------------------------------ C. Bland-Altman on clean images
g = pd.read_csv(r"D:\Capstone Project\results\v2_intervals\journal\gt_sampling_rate_check.csv")
fig, axs = plt.subplots(1, 2, figsize=(7.2, 2.7))
for ax, (gt, dg, name, unit) in zip(axs, [("gt_hr", "dig_hr", "Heart rate", "bpm"), ("gt500_qtc", "dig_qtc_ms", "QTc", "ms")]):
    d = (g[dg] - g[gt]); m = (g[dg] + g[gt]) / 2
    ok = d.notna()
    bias, sd = d[ok].mean(), d[ok].std(ddof=1)
    ax.scatter(m[ok], d[ok], s=9, color=BLUE, edgecolor="white", linewidth=0.3, zorder=3)
    for y, ls, lab in [(bias, "-", f"bias {bias:+.1f}"), (bias + 1.96 * sd, "--", f"+1.96 SD {bias + 1.96 * sd:+.1f}"),
                       (bias - 1.96 * sd, "--", f"\u22121.96 SD {bias - 1.96 * sd:+.1f}")]:
        ax.axhline(y, color=BLUE_D, lw=0.8, ls=ls)
        ax.text(ax.get_xlim()[1], y, " " + lab, va="center", fontsize=6, color=INK)
    ax.axhline(0, color=GRID, lw=0.6, zorder=0)
    ax.set_xlabel(f"mean of digitized and ground truth ({unit})"); ax.set_ylabel(f"digitized \u2212 ground truth ({unit})")
    ax.set_title(f"{name}, clean images (n={int(ok.sum())})", fontsize=7.5, loc="left")
fig.tight_layout(rect=(0, 0, 0.93, 1))
for e in ("png", "pdf"): fig.savefig(os.path.join(OUT, f"fig_bland_altman_clean.{e}"), dpi=300)

# ------------------------------------------------ D. interval error vs level
d = pd.read_csv(r"D:\Capstone Project\results\v2_intervals\journal\intervals_gt500_outcomes.csv")
AXES = [("blur", "Blur"), ("resolution", "Low resolution"), ("rotate", "Tilt"), ("jpeg", "JPEG"),
        ("gridcontrast", "Faded grid"), ("brightness", "Uneven lighting")]
fig, axs = plt.subplots(2, 6, figsize=(7.2, 3.2), sharex=True, sharey="row")
for r, (col, name) in enumerate([("diff_qrs_ms", "QRS duration"), ("diff_qtc_ms", "QTc")]):
    clean = d[d["axis"] == "clean"][col].dropna()
    for c, (ax_key, title) in enumerate(AXES):
        a = axs[r, c]
        sub = d[d["axis"] == ax_key]
        lv = [0] + list(range(1, 6))
        med = [clean.median()] + [sub[sub["level"] == l][col].median() for l in range(1, 6)]
        q1 = [clean.quantile(.25)] + [sub[sub["level"] == l][col].quantile(.25) for l in range(1, 6)]
        q3 = [clean.quantile(.75)] + [sub[sub["level"] == l][col].quantile(.75) for l in range(1, 6)]
        a.axhline(clean.median(), color=GRID, lw=0.8, zorder=0)
        a.fill_between(lv, q1, q3, color=BLUE, alpha=0.15, lw=0)
        a.plot(lv, med, color=BLUE_D, lw=1.2, marker="o", ms=3, mfc="white", mec=BLUE_D, mew=0.8)
        a.set_xticks(range(6))
        if r == 0: a.set_title(title, fontsize=7, loc="left")
        if r == 1: a.set_xlabel("level")
        if c == 0: a.set_ylabel(f"{name} error (ms)")
        if ax_key in ("blur", "resolution"):
            a.annotate(f"{med[-1]:.0f}", (5, med[-1]), textcoords="offset points", xytext=(-3, 4), ha="right", fontsize=6)
fig.text(0.01, 0.005, "Median with interquartile band; grey line = clean-image median. 49 reliable records; ground truth at 500 Hz.",
         fontsize=6, color=MUTE)
fig.tight_layout(rect=(0, 0.02, 1, 1))
for e in ("png", "pdf"): fig.savefig(os.path.join(OUT, f"fig_interval_error_by_level.{e}"), dpi=300)
print("figures written to", OUT)
