"""Write LaTeX tables for the journal manuscript straight from the data (no retyped numbers).
Outputs docs/journal/tables/*.tex and prints Wilson intervals quoted in the text.
"""
import numpy as np
import pandas as pd
from scipy import stats

T = r"D:\Capstone Project\docs\journal\tables"
d = pd.read_csv(r"D:\Capstone Project\results\v2_intervals\journal\intervals_gt500_outcomes.csv")
tests = pd.read_csv(f"{T}/paired_tests_gt500.csv")
ba = pd.read_csv(f"{T}/bland_altman_clean_gt500.csv")
pcl = pd.read_csv(f"{T}/per_class_gt500.csv")
step3 = pd.read_csv(f"{T}/step3_six_record_validation.csv")
COLS = [("diff_bpm", "HR"), ("diff_pr_ms", "PR"), ("diff_qrs_ms", "QRS"), ("diff_qt_ms", "QT"), ("diff_qtc_ms", "QTc")]


def med(sub, c):
    x = sub[c].dropna()
    if not len(x):
        return "--"
    return f"{x.median():.2f}" if c == "diff_bpm" else f"{x.median():.1f}"


# ---- Table: blur and resolution, all levels, median error
lines = [r"\begin{table}[ht]", r"\centering\small",
         r"\caption{Median absolute error against ground truth, by level, for the two axes that matter (49 reliable records; intervals against 500\,Hz ground truth; heart rate in bpm, intervals in ms). Level 0 is the clean image.}\label{tab:intervals}",
         r"\begin{tabular}{@{}llrrrrr@{}}", r"\toprule", r"Axis & Level & HR & PR & QRS & QT & QTc \\", r"\midrule"]
clean = d[d.axis == "clean"]
lines.append("Clean & 0 & " + " & ".join(med(clean, c) for c, _ in COLS) + r" \\")
for ax, name in [("blur", "Blur"), ("resolution", "Low resolution")]:
    lines.append(r"\midrule")
    for lv in range(1, 6):
        sub = d[(d.axis == ax) & (d.level == lv)]
        lines.append(f"{name if lv == 1 else ''} & {lv} & " + " & ".join(med(sub, c) for c, _ in COLS) + r" \\")
lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
open(f"{T}/tab_intervals.tex", "w", encoding="utf-8").write("\n".join(lines))

# ---- Table: the other four axes, range of level medians
lines = [r"\begin{table}[ht]", r"\centering\small",
         r"\caption{The four axes that did not matter: lowest--highest of the five level medians of absolute error (49 reliable records). Compare the clean-image medians in Table~\ref{tab:intervals}.}\label{tab:flat}",
         r"\begin{tabular}{@{}lccccc@{}}", r"\toprule", r"Axis & HR (bpm) & PR (ms) & QRS (ms) & QT (ms) & QTc (ms) \\", r"\midrule"]
for ax, name in [("rotate", "Tilt"), ("jpeg", "JPEG"), ("gridcontrast", "Grid contrast"), ("brightness", "Uneven lighting")]:
    cells = []
    for c, _ in COLS:
        m = [d[(d.axis == ax) & (d.level == lv)][c].median() for lv in range(1, 6)]
        f = 2 if c == "diff_bpm" else 1
        cells.append(f"{min(m):.{f}f}--{max(m):.{f}f}")
    lines.append(f"{name} & " + " & ".join(cells) + r" \\")
lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
open(f"{T}/tab_flat.tex", "w", encoding="utf-8").write("\n".join(lines))

# ---- Table: paired tests, effect size at level 5 and lowest significant level
lines = [r"\begin{table}[ht]", r"\centering\small",
         r"\caption{Paired comparison of each degraded level with the same record's clean image (Wilcoxon signed-rank, Holm-corrected over 30 comparisons per metric). ``Lowest sig.\ level'' is the lowest level with adjusted $p<0.05$; the effect is the median paired excess error at level~5 (bpm for HR, ms otherwise).}\label{tab:tests}",
         r"\begin{tabular}{@{}llccc@{}}", r"\toprule", r"Metric & Axis & Lowest sig.\ level & Effect at level 5 & Significant cells (of 5) \\", r"\midrule"]
for m in ["HR (bpm)", "PR (ms)", "QRS (ms)", "QT (ms)", "QTc (ms)"]:
    first = True
    for ax, name in [("blur", "Blur"), ("resolution", "Low resolution"), ("rotate", "Tilt"), ("jpeg", "JPEG"),
                     ("gridcontrast", "Grid contrast"), ("brightness", "Uneven lighting")]:
        g = tests[(tests.metric == m) & (tests.axis == ax)]
        sg = g[g.sig]
        low = int(sg.level.min()) if len(sg) else "none"
        eff = g[g.level == 5].median_excess.iloc[0]
        lines.append(f"{m.split(' (')[0] if first else ''} & {name} & {low} & {eff:+.2f} & {len(sg)} \\\\")
        first = False
    lines.append(r"\midrule")
lines[-1] = r"\bottomrule"
lines += [r"\end{tabular}", r"\end{table}"]
open(f"{T}/tab_tests.tex", "w", encoding="utf-8").write("\n".join(lines))

# ---- Table: Bland-Altman
lines = [r"\begin{table}[ht]", r"\centering\small",
         r"\caption{Agreement on clean images (digitised minus ground truth; intervals against 500\,Hz ground truth; $n=49$ reliable records). LoA: 95\,\% limits of agreement; MAE: mean absolute error.}\label{tab:ba}",
         r"\begin{tabular}{@{}lrrrrr@{}}", r"\toprule", r"Measure & Bias & SD & LoA low & LoA high & MAE \\", r"\midrule"]
for _, r in ba.iterrows():
    lines.append(f"{r.measure} & {r.bias:+.2f} & {r.sd:.2f} & {r.loa_low:+.1f} & {r.loa_high:+.1f} & {r.mean_abs_error:.2f} \\\\")
lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
open(f"{T}/tab_ba.tex", "w", encoding="utf-8").write("\n".join(lines))

# ---- Table: per class
lines = [r"\begin{table}[ht]", r"\centering\small",
         r"\caption{Median absolute error by diagnostic superclass on clean images and at level~5 of blur and of low resolution. Classes have 1--23 records, so this is descriptive only.}\label{tab:class}",
         r"\begin{tabular}{@{}lrrrrrrr@{}}", r"\toprule",
         r" & & \multicolumn{3}{c}{HR (bpm)} & \multicolumn{3}{c}{QTc (ms)} \\", r"\cmidrule(lr){3-5}\cmidrule(lr){6-8}",
         r"Class & Records & Clean & Blur 5 & Res.\ 5 & Clean & Blur 5 & Res.\ 5 \\", r"\midrule"]
for _, r in pcl.iterrows():
    lines.append(f"{r['class']} & {int(r.records)} & {r['HR clean']:.1f} & {r['HR blur5']:.1f} & {r['HR res5']:.1f} & "
                 f"{r['QTc clean']:.1f} & {r['QTc blur5']:.1f} & {r['QTc res5']:.1f} \\\\")
lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
open(f"{T}/tab_class.tex", "w", encoding="utf-8").write("\n".join(lines).replace("(none)", "No superclass"))

# ---- Table: step 3
lines = [r"\begin{table}[ht]", r"\centering\small",
         r"\caption{Step~3: six-record validation on undamaged rendered pages (recomputed from the saved digitiser outputs). Recovered: seconds of the 10\,s record the digitiser returned.}\label{tab:step3}",
         r"\begin{tabular}{@{}lrrrr@{}}", r"\toprule", r"Record & True HR (bpm) & Digitised HR (bpm) & Error (bpm) & Recovered (s) \\", r"\midrule"]
for _, r in step3.iterrows():
    dh = "no reading" if pd.isna(r.digitized_hr_bpm) else f"{r.digitized_hr_bpm:.1f}"
    er = "--" if pd.isna(r.abs_error_bpm) else f"{r.abs_error_bpm:.2f}"
    lines.append(f"\\texttt{{{r.record.replace('_', chr(92) + '_')}}} & {r.true_hr_bpm:.1f} & {dh} & {er} & {r.digitized_seconds:.1f} \\\\")
lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
open(f"{T}/tab_step3.tex", "w", encoding="utf-8").write("\n".join(lines))


def wil(k, n):
    lo, hi = stats.binomtest(k, n).proportion_ci(confidence_level=0.95, method="wilson")
    return f"{k}/{n} = {100*k/n:.0f}% (95% CI {100*lo:.0f}-{100*hi:.0f}%)"


print("Wilson intervals:")
for k, n in [(2, 9), (4, 9), (2, 10), (4, 10), (6, 19), (1, 19)]:
    print(" ", wil(k, n))
print("tables written to", T)
