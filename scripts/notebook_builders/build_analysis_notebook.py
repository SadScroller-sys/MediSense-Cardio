"""Builds colab/MediSense_Cardio_Analysis_Part1.ipynb -- clean the sweep results (Part 1 of the analysis)."""
import json, os

def md(*l): return {"cell_type": "markdown", "metadata": {}, "source": [x + "\n" for x in l]}
def code(*l): return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": [x + "\n" for x in l]}

cells = []
cells.append(md(
"# MediSense-Cardio -- Analysis Part 1: clean the sweep results",
"",
"Reads `results.csv` from the study folder on Drive and produces a clean, trustworthy table:",
"1. keep only the **50-record study sample** (drop stray rows from earlier scope changes),",
"2. drop duplicate rows,",
"3. check that all 1,550 expected tests are present,",
"4. count how many tests the digitizer **could not read at all** (a separate failure type from a wrong reading),",
"5. summarise heart-rate error per damage type and level, and save `results_clean.csv` + `summary_by_axis_level.csv`.",
"",
"Runs fine on a CPU runtime (no GPU needed). Run all; it asks for Drive access once.",
))
cells.append(code(
"from google.colab import drive",
"drive.mount('/content/drive')",
"import os, numpy as np, pandas as pd",
"STUDY_DIR = '/content/drive/MyDrive/MediSense-Cardio-Study'",
"print(sorted(os.listdir(STUDY_DIR))[:12], '...')",
))
cells.append(md("## 1. Rebuild the exact 50-record sample (same rule and seed as the sweep)"))
cells.append(code(
"pool = pd.read_csv(f'{STUDY_DIR}/sample_500.csv', dtype={'filename_lr': str})",
"SCOPE_N, seed = 50, 42",
"normal = pool[~pool['is_abnormal']]; abnormal = pool[pool['is_abnormal']]",
"sample = pd.concat([",
"    normal.sample(n=min(len(normal), SCOPE_N // 2), random_state=seed),",
"    abnormal.sample(n=min(len(abnormal), SCOPE_N - SCOPE_N // 2), random_state=seed),",
"]).reset_index(drop=True)",
"sample['record'] = sample['filename_lr'].str.split('/').str[-1] + '-0'   # matches results 'record' naming",
"print(len(sample), 'records:', int(sample['is_abnormal'].sum()), 'abnormal /', int((~sample['is_abnormal']).sum()), 'normal')",
"print(sample['diagnostic_class'].value_counts().to_dict())",
))
cells.append(md("## 2. Load results, keep only the sample, remove duplicates"))
cells.append(code(
"raw = pd.read_csv(f'{STUDY_DIR}/results.csv')",
"print('rows in file:', len(raw), '| columns:', list(raw.columns))",
"print('record id examples:', raw['record'].head(3).tolist())",
"",
"# 'record' in results is the ground-truth id (e.g. 01462_lr); align with the sample's record ids",
"sample['rid'] = sample['filename_lr'].str.split('/').str[-1]",
"in_scope = raw[raw['record'].isin(sample['rid'])]",
"print('rows in the 50-record sample:', len(in_scope), '| stray rows removed:', len(raw) - len(in_scope))",
"dups = in_scope.duplicated(subset='variant_id', keep=False).sum()",
"clean = in_scope.drop_duplicates(subset='variant_id', keep='last').copy()",
"print('duplicate rows removed:', len(in_scope) - len(clean), '| unique tests kept:', len(clean))",
"print('EXPECTED 1550 ->', 'OK' if len(clean) == 1550 else f'MISMATCH ({1550 - len(clean)} missing)')",
"",
"clean = clean.merge(sample[['rid', 'is_abnormal', 'diagnostic_class']], left_on='record', right_on='rid', how='left').drop(columns='rid')",
"print('records with labels:', clean['is_abnormal'].notna().mean())",
))
cells.append(md("## 3. Unreadable pictures (digitizer produced no usable heart rate)"))
cells.append(code(
"clean['unreadable'] = clean['dig_hr'].isna()",
"print('unreadable overall:', int(clean['unreadable'].sum()), 'of', len(clean), f\"({100*clean['unreadable'].mean():.1f}%)\")",
"fail = clean.groupby(['axis', 'level'])['unreadable'].agg(['sum', 'count'])",
"fail['pct_unreadable'] = (100 * fail['sum'] / fail['count']).round(1)",
"display(fail)",
"print('unreadable by clean/abnormal:'); display(clean.groupby('is_abnormal')['unreadable'].mean().round(3))",
))
cells.append(md("## 4. Heart-rate error per damage type and level (readable pictures only)"))
cells.append(code(
"clean['diff_bpm'] = pd.to_numeric(clean['diff_bpm'], errors='coerce')",
"g = clean.groupby(['axis', 'level'])",
"summary = pd.DataFrame({",
"    'n_tests': g.size(),",
"    'n_readable': g['diff_bpm'].count(),",
"    'mean_err_bpm': g['diff_bpm'].mean(),",
"    'median_err_bpm': g['diff_bpm'].median(),",
"    'p90_err_bpm': g['diff_bpm'].quantile(0.9),",
"    'pct_err_over_5bpm': g['diff_bpm'].apply(lambda s: 100 * (s.dropna() > 5).mean()),",
"}).round(2)",
"display(summary)",
))
cells.append(code(
"import matplotlib.pyplot as plt",
"axes_order = ['blur', 'resolution', 'jpeg', 'gridcontrast', 'brightness', 'rotate']",
"base = clean[clean['axis'] == 'clean']['diff_bpm'].mean()",
"fig, axs = plt.subplots(2, 3, figsize=(14, 7), sharey=True)",
"for a, ax in zip(axes_order, axs.flat):",
"    s = summary.loc[a]",
"    xs = [0] + list(s.index)",
"    ax.plot(xs, [base] + list(s['mean_err_bpm']), marker='o', label='mean')",
"    ax.plot(xs, [clean[clean['axis']=='clean']['diff_bpm'].median()] + list(s['median_err_bpm']), marker='s', linestyle='--', label='median')",
"    ax.set_title(a); ax.set_xlabel('level (0 = clean)')",
"axs[0, 0].set_ylabel('heart-rate error (bpm)'); axs[1, 0].set_ylabel('heart-rate error (bpm)')",
"axs[0, 0].legend(); fig.suptitle('Heart-rate error vs damage level (50 records, cleaned)')",
"plt.tight_layout(); plt.show()",
))
cells.append(md("## 5. Save the cleaned files"))
cells.append(code(
"clean.to_csv(f'{STUDY_DIR}/results_clean.csv', index=False)",
"summary.to_csv(f'{STUDY_DIR}/summary_by_axis_level.csv')",
"fail.to_csv(f'{STUDY_DIR}/unreadable_by_axis_level.csv')",
"chk = pd.read_csv(f'{STUDY_DIR}/results_clean.csv')",
"print('saved & verified:', len(chk), 'rows in results_clean.csv')",
))

nb = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "name": "python3"},
      "language_info": {"name": "python"}, "colab": {"provenance": [], "name": "MediSense_Cardio_Analysis_Part1.ipynb"}},
      "nbformat": 4, "nbformat_minor": 0}
out = os.environ.get("NB_OUT", "MediSense_Cardio_Analysis_Part1.ipynb")
json.dump(nb, open(out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("Wrote", out, len(cells), "cells")
