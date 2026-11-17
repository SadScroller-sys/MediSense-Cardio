"""Deterministic image degradation, identical to the functions embedded in the Colab sweep notebooks
(scripts/notebook_builders/build_fullsweep_v2_notebook.py, ~line 305 onward). Kept as its own module so the
Phase 2b quality-proxy work can regenerate the exact same degraded pages locally (pure OpenCV, no GPU) from the
clean rendered pages, instead of duplicating this logic a third time.

IMPORTANT: if the notebook's degrade_* functions or LEVELS table are ever changed, mirror the change here too,
or the quality-proxy calibration will silently train against a different degradation than the one that produced
results_v2.csv.
"""
import cv2
import numpy as np


def degrade_blur(img, level):
    k = [3, 7, 11, 15, 21][level - 1]
    return cv2.GaussianBlur(img, (k, k), 0)


def degrade_rotate(img, level):
    angle = [2, 5, 8, 12, 16][level - 1]
    h, w = img.shape[:2]
    center = (w / 2, h / 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(img, M, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255))


def degrade_jpeg(img, level):
    quality = [50, 30, 15, 8, 3][level - 1]
    ok, enc = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, quality])
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


AXES = {
    'blur': degrade_blur,
    'rotate': degrade_rotate,
    'jpeg': degrade_jpeg,
    'resolution': degrade_resolution,
    'brightness': degrade_brightness,
    'gridcontrast': degrade_grid_contrast,
}
LEVELS = [1, 2, 3, 4, 5]
