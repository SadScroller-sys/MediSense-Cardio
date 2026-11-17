"""Draw report figures 2.1 (method pipeline) and 4.1 (wrong heart rate by damage type) for docs/reports/CAPSTONE_REPORT_DRAFT_v2.docx.
Numbers in Figure 4.1 are copied from results/FINAL_NUMBERS.md section 2.1 (new 100, worst level).
  python -I scripts/analysis/make_report_figures.py"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

OUT = "D:/Capstone Project/docs/reports/figures/"
plt.rcParams["font.family"] = "serif"

# Figure 2.1: pipeline
fig, ax = plt.subplots(figsize=(7.2, 4.6))
ax.axis("off")
ax.set_xlim(0, 10)
ax.set_ylim(0, 10)
steps = [
    ("1. ECG recording\n(PTB-XL, known answer)", 5, 9.0),
    ("2. Draw paper-style page\n(ECG-Image-Kit)", 5, 7.55),
    ("3. Damage or photograph the page\n(6 damage types, phone photos)", 5, 6.1),
    ("4. Straighten the page", 5, 4.65),
    ("5. Digitizer: picture to 12 signals\n(Open-ECG-Digitizer, unchanged)", 5, 3.2),
]
for t, x, y in steps:
    ax.add_patch(FancyBboxPatch((x - 2.2, y - 0.5), 4.4, 1.0, boxstyle="round,pad=0.05", fc="#eaf1fb", ec="black", lw=1))
    ax.text(x, y, t, ha="center", va="center", fontsize=8.5)
for i in range(len(steps) - 1):
    ax.annotate("", xy=(5, steps[i + 1][2] + 0.55), xytext=(5, steps[i][2] - 0.55), arrowprops=dict(arrowstyle="->", lw=1))
outs = [("Measurements\n(heart rate, PR, axis)", 1.9, 1.0), ("Traffic light\nGREEN / AMBER / RED", 5.0, 1.0), ("Compare with\ntrue signal", 8.1, 1.0)]
for t, x, y in outs:
    ax.add_patch(FancyBboxPatch((x - 1.35, y - 0.55), 2.7, 1.1, boxstyle="round,pad=0.05", fc="#fdf3dc", ec="black", lw=1))
    ax.text(x, y, t, ha="center", va="center", fontsize=8.5)
    ax.annotate("", xy=(x, y + 0.65), xytext=(5, 2.65), arrowprops=dict(arrowstyle="->", lw=1))
fig.tight_layout()
fig.savefig(OUT + "fig2_1_pipeline.png", dpi=200)
plt.close(fig)

# Figure 4.1: wrong heart rate at the worst level
names = ["Low resolution", "Blur", "Faded grid", "Clean page", "Brightness", "Rotation", "JPEG"]
wrong = [47.5, 17.2, 3.0, 3.0, 1.0, 0.0, 0.0]
lo = [37.9, 11.0, 1.0, 1.0, 0.2, 0.0, 0.0]
hi = [57.2, 25.8, 8.5, 8.5, 5.5, 3.7, 3.7]
fig, ax = plt.subplots(figsize=(7.2, 4.0))
yerr = [[w - l for w, l in zip(wrong, lo)], [h - w for w, h in zip(wrong, hi)]]
ax.bar(names, wrong, yerr=yerr, capsize=3, color="#4a78b5", ecolor="black")
for i, w in enumerate(wrong):
    ax.text(i, hi[i] + 1.2, f"{w:.1f}%", ha="center", fontsize=8)
ax.set_ylabel("Wrong heart rate (% of pages)")
ax.set_ylim(0, 65)
ax.set_title("Worst damage level, 99 held-out recordings (95% interval)", fontsize=10)
plt.xticks(rotation=20, ha="right", fontsize=8.5)
fig.tight_layout()
fig.savefig(OUT + "fig4_1_wrong_by_damage.png", dpi=200)
plt.close(fig)
print("figures written")
