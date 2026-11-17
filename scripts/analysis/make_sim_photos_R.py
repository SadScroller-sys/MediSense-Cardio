"""Set N (positive-rich findings set, rules in docs/plan/analysis_plan_changes.md 2026-11-16 evening): ONE simulated phone photo per page of N001-N120 (alternating straight and angled), seed 62, same generator as Section Z, L and M.
  python -I scripts/analysis/make_sim_photos.py
Writes results/fresh_sim/photos/<page>_<shot>.jpg (1440 x 1080) and results/fresh_sim/photos_meta.csv (the settings of every photo). Seed 49. A simulation, not a camera."""
import os

import cv2
import numpy as np
import pandas as pd

ROOT = "D:/Capstone Project/"
OUT = ROOT + "results/paper_r/P_sim/"
os.makedirs(OUT + "photos", exist_ok=True)
rng = np.random.default_rng(82)
W, H = 1440, 1080
rows = []


def quad_for(page_w, page_h, yaw, pitch, rot, frac):
    """Corners (TL, TR, BR, BL) of the page in the photo. yaw = side tilt, pitch = tilt from above/below (degrees), rot = in-plane rotation (degrees);
    frac = width of the page as a share of the photo width (before tilt)."""
    w = frac * W
    h = w * page_h / page_w
    cx, cy = W / 2 + rng.uniform(-0.02, 0.02) * W, H / 2 + rng.uniform(-0.02, 0.02) * H
    y_, p_ = np.radians(yaw), np.radians(pitch)
    wx = w * np.cos(y_) ** 0.5
    hy = h * np.cos(p_) ** 0.5
    # side tilt: the near side is taller than the far side
    a = 0.55 * np.sin(y_)
    b = 0.55 * np.sin(p_)
    left_h = hy * (1 + a)
    right_h = hy * (1 - a)
    top_w = wx * (1 - b)
    bot_w = wx * (1 + b)
    pts = np.array([[-top_w / 2, -left_h / 2], [top_w / 2, -right_h / 2], [bot_w / 2, right_h / 2], [-bot_w / 2, left_h / 2]], float)
    r = np.radians(rot)
    R = np.array([[np.cos(r), -np.sin(r)], [np.sin(r), np.cos(r)]])
    pts = pts @ R.T
    pts[:, 0] += cx
    pts[:, 1] += cy
    return pts.astype(np.float32)


for n in range(1, 121):
    page = f"R{n:03d}"
    img = cv2.imread(ROOT + f"results/paper_r/pages/{page}.png", cv2.IMREAD_COLOR)
    assert img is not None and img.shape[:2] == (1700, 2200), page
    ph, pw = img.shape[:2]
    for shot in (("straight" if n % 2 else "angled"),):
        extra = rng.choice(["none", "blur", "shadow", "far"], p=[0.25, 0.25, 0.25, 0.25])
        if shot == "straight":
            yaw, pitch, rot = rng.uniform(-4, 4), rng.uniform(-4, 4), rng.uniform(-3, 3)
        else:
            yaw = rng.choice([-1, 1]) * rng.uniform(20, 35)
            pitch = rng.uniform(-12, 12)
            rot = rng.uniform(-4, 4)
        frac = rng.uniform(0.55, 0.70) if extra == "far" else rng.uniform(0.78, 0.86)
        dst = quad_for(pw, ph, yaw, pitch, rot, frac)
        while (dst[:, 0].min() < 12 or dst[:, 0].max() > W - 12 or dst[:, 1].min() < 12 or dst[:, 1].max() > H - 12) and frac > 0.3:
            frac *= 0.96                              # keep the whole page in the frame, as a person taking the photo would
            dst = quad_for(pw, ph, yaw, pitch, rot, frac)
        src = np.array([[0, 0], [pw - 1, 0], [pw - 1, ph - 1], [0, ph - 1]], np.float32)
        M = cv2.getPerspectiveTransform(src, dst)
        # dark screen background with a gentle gradient
        bg = np.full((H, W, 3), rng.uniform(18, 35), np.float32)
        gx = np.linspace(0.85, 1.15, W)[None, :, None]
        bg *= gx
        warped = cv2.warpPerspective(img, M, (W, H), flags=cv2.INTER_AREA, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0)).astype(np.float32)
        mask = cv2.warpPerspective(np.full((ph, pw), 255, np.uint8), M, (W, H), flags=cv2.INTER_NEAREST)
        mask = (mask > 127)[:, :, None]
        out = np.where(mask, warped * rng.uniform(0.88, 1.0), bg)
        # vignette on all photos
        yy, xx = np.mgrid[0:H, 0:W]
        d = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
        vig = 1.0 - rng.uniform(0.12, 0.30) * d ** 2
        out *= vig[:, :, None]
        blur_sigma, shadow = 0.0, 0.0
        if extra == "blur":
            blur_sigma = float(rng.uniform(0.8, 2.0))
            out = cv2.GaussianBlur(out, (0, 0), blur_sigma)
        if extra == "shadow":
            shadow = float(rng.uniform(0.25, 0.5))
            ramp = 1.0 - shadow * (xx / (W - 1))
            if rng.random() < 0.5:
                ramp = ramp[:, ::-1]
            out *= ramp[:, :, None]
        noise = float(rng.uniform(3, 6))
        out += rng.normal(0, noise, out.shape)
        out = np.clip(out, 0, 255).astype(np.uint8)
        q = int(rng.integers(85, 93))
        name = f"{page}_{shot}"
        cv2.imwrite(OUT + f"photos/{name}.jpg", out, [cv2.IMWRITE_JPEG_QUALITY, q])
        rows.append(dict(photo=name, page=page, shot=shot, extra=extra, yaw=round(yaw, 1), pitch=round(pitch, 1), rot=round(rot, 1), page_frac=round(frac, 2), blur_sigma=round(blur_sigma, 2),
                         shadow=round(shadow, 2), noise=round(noise, 1), jpeg_q=q))
pd.DataFrame(rows).to_csv(OUT + "photos_meta.csv", index=False)
print("photos written:", len(rows))
