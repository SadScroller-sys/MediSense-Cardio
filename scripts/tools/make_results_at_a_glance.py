"""One-page 'results at a glance' figure for the poster, the viva and the report: every claim, its number, and its verdict (shown / not shown / not testable). Numbers are copied from results/FINAL_NUMBERS.md
(sections 1-10.24); change them there first if a result changes. Output: docs/reports/figures/fig_results_at_a_glance.png (and .pdf). Usage: python -I scripts/tools/make_results_at_a_glance.py"""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
OUT = ROOT + "/docs/reports/figures/"
os.makedirs(OUT, exist_ok=True)
PASS, FAIL, NA = "#1b7f3b", "#b42318", "#6b7280"
# (group, claim, number, verdict, colour)
ROWS = [
    ("WARNING", "Traffic light: a GREEN heart rate is wrong", "0.2% (2 of 917 real captures)", "SHOWN", PASS),
    ("WARNING", "GREEN on printed paper (another phone)", "wrong for 2 of 19 photos", "NOT A GUARANTEE", FAIL),
    ("FIX", "Straightening the photo: screen photos", "bad readings 14 to 2 of 40 (p = 0.0005)", "CONFIRMED", PASS),
    ("FIX", "Straightening: printed paper, 66 recompressed photos", "31 to 15 bad (p = 0.0004)", "CONFIRMED", PASS),
    ("FIX", "Straightening: printed paper, 22 straight full-size photos", "3 to 2 bad (p = 1.0)", "NOT CONFIRMED", FAIL),
    ("MEASURES", "Heart rate, PR interval, QRS axis (straightened photos)", "12 ms and 4 to 6 degrees typical error", "SHOWN", PASS),
    ("MEASURES", "QT, QRS duration (second try on doctor marks)", "QT 12 ms on signals; 66 ms on pictures", "NOT SHOWN", FAIL),
    ("FINDINGS", "Heart-attack pattern, ST/T change (photos)", "AUROC 0.81 and 0.84 on new photos", "SHOWN", PASS),
    ("FINDINGS", "Conduction disturbance (printed paper)", "AUROC 0.42 on 22 photos (5 positives)", "NOT SHOWN", FAIL),
    ("FINDINGS", "Hypertrophy (first model, drawn pages and photos)", "0.75 on new drawn pages", "NOT SHOWN", FAIL),
    ("FINDINGS", "Left bundle branch block (2 fresh sets, 280 pictures)", "photos: AUROC 0.83, sens 69%, spec 92%", "DATASET ONLY", PASS),
    ("FINDINGS", "Atrial fibrillation (2 fresh sets; passed on 2nd test)", "photos: AUROC 0.84, sens 75%, spec 91%", "DATASET ONLY", PASS),
    ("FINDINGS", "4 other extra patterns incl. LAFB (sets P and Q)", "pages 0.90-0.97; photos 0.67-0.77", "RESEARCH ONLY", NA),
    ("RISK", "1-year death risk from the ECG alone", "AUROC 0.71 against 0.80 for age alone", "NOT SHOWN", FAIL),
    ("RISK", "5-year death risk, ECG plus age (sealed test)", "0.83; ECG adds +0.013 (not significant)", "NOT SHOWN", FAIL),
]
fig, ax = plt.subplots(figsize=(14, 9.4), dpi=170)
ax.set_xlim(0, 100)
ax.set_ylim(-0.5, len(ROWS) + 6.4)
ax.axis("off")
fig.patch.set_facecolor("white")
ax.text(0, len(ROWS) + 5.7, "What we found, and what we refuse to show", fontsize=20, fontweight="bold", va="center", color="#111827")
ax.text(0, len(ROWS) + 5.05, "Every rule was written before the result was seen. Negative results are reported as measured. Research prototype, not a medical device.", fontsize=11, va="center", color="#374151")
y = len(ROWS) + 3.3
last = None
for g, claim, num, verdict, col in ROWS:
    if g != last:
        y -= 0.55 if last is not None else 0.2
        ax.text(0, y + 0.62, g, fontsize=9.5, fontweight="bold", color="#6b7280", va="center")
        last = g
    ax.add_patch(FancyBboxPatch((0, y - 0.38), 100, 0.76, boxstyle="round,pad=0,rounding_size=0.15", fc="#f9fafb", ec="#e5e7eb", lw=0.8))
    ax.text(1.2, y, claim, fontsize=11.5, va="center", color="#111827")
    ax.text(52, y, num, fontsize=11, va="center", color="#374151")
    ax.add_patch(FancyBboxPatch((83.5, y - 0.27), 16, 0.54, boxstyle="round,pad=0,rounding_size=0.25", fc=col, ec=col))
    ax.text(91.5, y, verdict, fontsize=10, fontweight="bold", va="center", ha="center", color="white")
    y -= 1.0
ax.text(0, y + 0.1, "Numbers: results/FINAL_NUMBERS.md (sections 10.1 to 10.31). Pass rules are the team's proposal and have not been approved by the guide.", fontsize=9, color="#6b7280", va="center")
for ext in ("png", "pdf"):
    fig.savefig(OUT + "fig_results_at_a_glance." + ext, bbox_inches="tight", facecolor="white")
fig.savefig(OUT + "fig_results_at_a_glance_hires.png", dpi=300, bbox_inches="tight", facecolor="white")      # for the A0 poster (print resolution)
print("saved", OUT + "fig_results_at_a_glance.png")
import shutil as _sh  # noqa: E402

_sh.copyfile(ROOT + "/docs/reports/figures/fig_results_at_a_glance.png", ROOT + "/demo/assets/fig_results_at_a_glance.png")      # the demo app serves its copy
