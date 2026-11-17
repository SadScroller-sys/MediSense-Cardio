"""Simple preparations of a photo of an ECG page shown on a screen, before the digitiser reads it (step 4 of the plan; rules in docs/plan/analysis_plan_changes.md, 2026-11-10).
enlarge(img)          : long side -> 4096 px (Lanczos); a photo that is already 4096 px or larger is left as it is.
straighten(img, w, h) : find the bright page, map its four corners to a w x h rectangle (perspective correction, cubic). Returns (image, ok); ok is False if no page was found (image returned unchanged)."""
import cv2
import numpy as np


def enlarge(img, long_side=4096):
    h, w = img.shape[:2]
    if max(h, w) >= long_side:
        return img
    s = long_side / max(h, w)
    return cv2.resize(img, (int(round(w * s)), int(round(h * s))), interpolation=cv2.INTER_LANCZOS4)


def _order(pts):
    pts = np.asarray(pts, dtype=np.float32).reshape(4, 2)
    s = pts.sum(axis=1)
    d = np.diff(pts, axis=1).ravel()
    return np.array([pts[np.argmin(s)], pts[np.argmin(d)], pts[np.argmax(s)], pts[np.argmax(d)]], dtype=np.float32)      # tl, tr, br, bl


def find_page_quad(img):
    h, w = img.shape[:2]
    sc = 800.0 / max(h, w)
    small = cv2.resize(img, (int(w * sc), int(h * sc)), interpolation=cv2.INTER_AREA)
    gray = cv2.GaussianBlur(cv2.cvtColor(small, cv2.COLOR_BGR2GRAY), (7, 7), 0)
    _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    th = cv2.morphologyEx(th, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
    th = cv2.morphologyEx(th, cv2.MORPH_OPEN, np.ones((9, 9), np.uint8))
    cnts, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return None
    best = None
    for c in sorted(cnts, key=cv2.contourArea, reverse=True)[:3]:
        area = cv2.contourArea(c)
        if area < 0.12 * small.shape[0] * small.shape[1]:
            continue
        hull = cv2.convexHull(c)
        peri = cv2.arcLength(hull, True)
        quad = None
        for eps in (0.015, 0.02, 0.03, 0.04, 0.06):
            ap = cv2.approxPolyDP(hull, eps * peri, True)
            if len(ap) == 4:
                quad = ap.reshape(4, 2)
                break
        if quad is None:
            quad = cv2.boxPoints(cv2.minAreaRect(hull))
        q = _order(quad)
        wd = (np.linalg.norm(q[1] - q[0]) + np.linalg.norm(q[2] - q[3])) / 2
        ht = (np.linalg.norm(q[3] - q[0]) + np.linalg.norm(q[2] - q[1])) / 2
        if ht < 1 or not (0.9 < wd / ht < 1.8):
            continue
        best = q / sc
        break
    return best


def straighten(img, out_w=2200, out_h=1700):
    q = find_page_quad(img)
    if q is None:
        return img, False
    dst = np.array([[0, 0], [out_w - 1, 0], [out_w - 1, out_h - 1], [0, out_h - 1]], dtype=np.float32)
    M = cv2.getPerspectiveTransform(q.astype(np.float32), dst)
    return cv2.warpPerspective(img, M, (out_w, out_h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE), True
