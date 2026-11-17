"""Builds colab/MediSense_Cardio_FullSweep_v2_Results_Overview.ipynb.

The Step 8 results-overview cells of MediSense_Cardio_FullSweep_v2_Intervals.ipynb, packaged on their
own so they can run in about a minute on Colab (no GPU, no digitiser): they only read the finished
results_v2.csv from Drive.
"""
import json
import os

cells = []


def md(*lines):
    return {"cell_type": "markdown", "metadata": {}, "source": "\n".join(lines).splitlines(keepends=True)}


def code(*lines):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
            "source": "\n".join(lines).splitlines(keepends=True)}


cells.append(md(
    "# MediSense-Cardio -- Full Sweep v2: Results Overview (Step 8)",
    "",
    "**What this is:** the Step 8 results overview from `MediSense_Cardio_FullSweep_v2_Intervals.ipynb`, on its own.",
    "The 10.5-hour sweep (50 real ECG pages x 31 damaged versions = 1,550 tests) has already finished and its",
    "results are saved on Drive as `results_v2.csv`. This notebook only reads that file, so it needs no GPU and",
    "no digitiser and runs in about a minute.",
))
cells.append(md("## Step 0 -- Mount Google Drive and load the finished results"))
cells.append(code(
    "from google.colab import drive",
    "drive.mount('/content/drive')",
    "",
    "import os",
    "import pandas as pd",
    "",
    "STUDY_DIR = '/content/drive/MyDrive/MediSense-Cardio-Study'",
    "RESULTS_PATH = f'{STUDY_DIR}/results_v2.csv'",
    "",
    "results_so_far = pd.read_csv(RESULTS_PATH)",
    "N_TOTAL = 50 * 31  # 50 real records x (6 damage types x 5 levels + 1 clean)",
    "AXES = ['blur', 'rotate', 'jpeg', 'resolution', 'brightness', 'gridcontrast']",
))
cells.append(md(
    "## Step 8 -- Results overview",
    "",
    "Average heart-rate error for every damage type and level, and how many rows have a measured PR / QRS / QT / QTc.",
))
cells.append(code(
    "print(f\"{len(results_so_far)}/{N_TOTAL} variants have results so far.\")",
    "",
    "summary = results_so_far.groupby(['axis', 'level'])['diff_bpm'].agg(['mean', 'count']).round(3)",
    "print(\"\\nAverage heart-rate error by axis and level (higher level = more degradation):\")",
    "display(summary)",
    "for col in ('diff_pr_ms', 'diff_qrs_ms', 'diff_qt_ms', 'diff_qtc_ms'):",
    "    n_ok = int(results_so_far[col].notna().sum())",
    "    mean_val = results_so_far[col].mean() if n_ok else float('nan')",
    "    print(f\"{col}: {n_ok}/{len(results_so_far)} rows have a value, mean={mean_val:.1f}ms\" if n_ok else f\"{col}: 0 rows have a value yet\")",
))
cells.append(code(
    "import matplotlib.pyplot as plt",
    "",
    "fig, axs = plt.subplots(2, 3, figsize=(15, 8), sharey=True)",
    "clean_mean = results_so_far[results_so_far['axis'] == 'clean']['diff_bpm'].mean()",
    "for ax_name, ax in zip(AXES, axs.flat):",
    "    sub = results_so_far[results_so_far['axis'] == ax_name]",
    "    if len(sub) == 0:",
    "        continue",
    "    by_level = sub.groupby('level')['diff_bpm'].mean()",
    "    levels_x = [0] + list(by_level.index)",
    "    means_y = [clean_mean] + list(by_level.values)",
    "    ax.plot(levels_x, means_y, marker='o')",
    "    ax.set_title(ax_name)",
    "    ax.set_xlabel('degradation level (0 = clean)')",
    "axs[0, 0].set_ylabel('mean HR error (bpm)')",
    "axs[1, 0].set_ylabel('mean HR error (bpm)')",
    "fig.suptitle('Heart-rate error vs. degradation level, by axis')",
    "plt.tight_layout()",
    "plt.show()",
))

nb = {
    "cells": cells,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "name": "python3"},
        "language_info": {"name": "python"},
        "colab": {"provenance": [], "name": "MediSense_Cardio_FullSweep_v2_Results_Overview.ipynb"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}
out = os.path.join(os.path.dirname(__file__), "..", "..", "colab", "MediSense_Cardio_FullSweep_v2_Results_Overview.ipynb")
with open(out, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1)
print("wrote", os.path.abspath(out))
