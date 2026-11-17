"""Figure 4.2: the demonstration's output for sample 1 (straightened page + the traffic light and the fixed-sentence explanation, texts as returned by the app)."""
import glob, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image
page = sorted(glob.glob(os.path.expandvars("C:/Users/Nihar Sai/AppData/Local/Temp/gradio/*/image.webp")), key=os.path.getmtime)[-1]
im = Image.open(page).convert("RGB")
fig = plt.figure(figsize=(9.5, 4.6))
a = fig.add_axes([0.01, 0.08, 0.50, 0.84]); a.imshow(im); a.axis("off"); a.set_title("Page after straightening (input photo of sample 1)", fontsize=8.5)
b = fig.add_axes([0.53, 0.02, 0.46, 0.94]); b.axis("off"); b.set_xlim(0, 1); b.set_ylim(0, 1)
b.add_patch(plt.Rectangle((0, 0.86), 0.34, 0.12, fc="#2e8b57", ec="black")); b.text(0.17, 0.92, "GREEN", ha="center", va="center", color="white", fontsize=12, weight="bold")
b.text(0.37, 0.92, "Heart rate read from the photo: 57 bpm", va="center", fontsize=8.5, weight="bold")
lines = ["No warning from our checks. This is not a guarantee",
 "that the heart rate is right.", "",
 "Your ECG photo, in plain words", "",
 "Heart rate: 57 beats per minute: slow (below 60).",
 "PR interval: about 172 ms (rough estimate by our method;",
 "   typically within about 12 ms of hospital software).",
 "QRS axis: about 19 degrees (rough estimate by our method;",
 "   typically within about 5 degrees of hospital software).", "",
 "What we did not check:",
 "P wave, QRS complex, QT interval, ST segment, T wave.",
 "No heart condition was looked for. A normal heart rate",
 "does not mean a normal ECG or a healthy heart."]
for i, t in enumerate(lines):
    b.text(0.0, 0.80 - i * 0.052, t, fontsize=8, va="top", weight="bold" if t.startswith("Your ECG") or t.startswith("What we did") else "normal")
fig.savefig("D:/Capstone Project/docs/reports/figures/fig4_2_demo_output.png", dpi=200)
print("ok", page)
