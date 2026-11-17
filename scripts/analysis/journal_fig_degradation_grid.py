"""Journal figure: ONE real rendered record (PTB-XL 00001_lr, ECG-Image-Kit page) shown at every degradation
axis and selected levels. The degradation functions are copied verbatim from the sweep notebook
(scripts/notebook_builders/build_fullsweep_notebook.py, Step 4) so the figure shows exactly what the sweep did.
Each degradation is applied to the FULL page (as in the sweep) and a lead-II strip is cropped for display.
"""
import cv2
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SRC = r"D:\Capstone Project\results\multi_sample_test\images\00001_lr-0.png"
OUT = r"D:\Capstone Project\docs\journal\figures"
import os
os.makedirs(OUT, exist_ok=True)


def degrade_blur(img, level):
    k = [3, 7, 11, 15, 21][level - 1]
    return cv2.GaussianBlur(img, (k, k), 0)


def degrade_rotate(img, level):
    angle = [2, 5, 8, 12, 16][level - 1]
    h, w = img.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
    return cv2.warpAffine(img, M, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255))


def degrade_jpeg(img, level):
    quality = [50, 30, 15, 8, 3][level - 1]
    ok, enc = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, quality])
    return cv2.imdecode(enc, cv2.IMREAD_COLOR)


def degrade_resolution(img, level):
    factor = [0.75, 0.5, 0.35, 0.25, 0.15][level - 1]
    h, w = img.shape[:2]
    small = cv2.resize(img, (max(1, int(w * factor)), max(1, int(h * factor))), interpolation=cv2.INTER_AREA)
    return cv2.resize(small, (w, h), interpolation=cv2.INTER_LINEAR)


def degrade_brightness(img, level):
    strength = [0.15, 0.3, 0.45, 0.6, 0.75][level - 1]
    h, w = img.shape[:2]
    gradient = np.tile(np.linspace(1.0, 1.0 - strength, w), (h, 1)).astype(np.float32)
    gradient = cv2.merge([gradient, gradient, gradient])
    return np.clip(img.astype(np.float32) * gradient, 0, 255).astype(np.uint8)


def degrade_grid_contrast(img, level):
    strength = [0.15, 0.3, 0.45, 0.6, 0.75][level - 1]
    mean_val = img.mean()
    return np.clip(img.astype(np.float32) * (1 - strength) + mean_val * strength, 0, 255).astype(np.uint8)


AXES = [("Blur", degrade_blur, "Gaussian kernel {}", [3, 7, 11, 15, 21]),
        ("Rotation", degrade_rotate, "{}\u00b0", [2, 5, 8, 12, 16]),
        ("JPEG", degrade_jpeg, "quality {}", [50, 30, 15, 8, 3]),
        ("Resolution", degrade_resolution, "\u00d7{}", [0.75, 0.5, 0.35, 0.25, 0.15]),
        ("Brightness", degrade_brightness, "shadow {}%", [15, 30, 45, 60, 75]),
        ("Grid contrast", degrade_grid_contrast, "fade {}%", [15, 30, 45, 60, 75])]
LEVELS = [1, 3, 5]

img = cv2.imread(SRC, cv2.IMREAD_COLOR)
# lead II strip (row 2 of the page), chosen from the rendered page above
Y0, Y1, X0, X1 = 860, 1060, 120, 1000


def crop(im, angle=0.0):
    """Crop the lead-II strip. For rotation, follow the trace: move the crop centre through the same rotation."""
    cy, cx = (Y0 + Y1) / 2, (X0 + X1) / 2
    if angle:
        h, w = im.shape[:2]
        M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
        cx, cy = M @ np.array([cx, cy, 1.0])
    hh, hw = (Y1 - Y0) // 2, (X1 - X0) // 2
    y0 = int(np.clip(cy - hh, 0, im.shape[0] - 2 * hh)); x0 = int(np.clip(cx - hw, 0, im.shape[1] - 2 * hw))
    return cv2.cvtColor(im[y0:y0 + 2 * hh, x0:x0 + 2 * hw], cv2.COLOR_BGR2RGB)


plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 7})
fig, axs = plt.subplots(len(AXES), 1 + len(LEVELS), figsize=(7.2, 5.4))
for r, (name, fn, fmt, params) in enumerate(AXES):
    axs[r, 0].imshow(crop(img))
    if r == 0:
        axs[r, 0].set_title("clean (level 0)", fontsize=7, loc="left")
    axs[r, 0].set_ylabel(name, fontsize=7.5, rotation=0, ha="right", va="center", labelpad=6)
    for c, lv in enumerate(LEVELS, start=1):
        out = fn(img, lv)
        axs[r, c].imshow(crop(out, params[lv - 1] if name == "Rotation" else 0.0))
        p = params[lv - 1]
        label = f"level {lv}: " + fmt.format(p)
        axs[r, c].set_title(label if r == 0 else f"level {lv}: " + fmt.format(p), fontsize=6.5, loc="left")
for a in axs.flat:
    a.set_xticks([])
    a.set_yticks([])
    for s in a.spines.values():
        s.set_linewidth(0.4)
        s.set_color("#999999")
fig.text(0.01, 0.005, "One PTB-XL record (00001_lr) rendered with ECG-Image-Kit; lead II strip shown. Levels 2 and 4 "
         "omitted for space; all five levels were tested.", fontsize=6, color="#52514e")
fig.tight_layout(rect=(0.04, 0.02, 1, 1), h_pad=0.4, w_pad=0.3)
for ext in ("png", "pdf"):
    fig.savefig(os.path.join(OUT, f"fig_degradation_grid.{ext}"), dpi=300)
print("saved", OUT)
