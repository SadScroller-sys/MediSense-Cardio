"""Phase 2b, Tier 1: no-reference image-quality signals for a photographed/rendered ECG page.

Per docs/PLAN.md ("Contribution 2 -- Uncertainty propagation"), Tier 1 signals are computed from the image
ALONE -- no ground truth, no digitizer internals -- so they work with any digitizer and can gate an upload
before digitization even runs. Five signals, one per degradation axis we tested in Contributions 1:

    blur_score        -- Laplacian variance (higher = sharper; degrades with `blur`, and partly with `resolution`)
    skew_deg           -- estimated rotation away from axis-aligned, in degrees (degrades with `rotate`)
    resolution_score   -- high-frequency energy ratio via FFT (degrades with `resolution`, and partly with `blur`)
    contrast_score      -- global std-dev of pixel intensity (degrades with `gridcontrast`, and `brightness`)
    blockiness_score    -- 8x8 JPEG block-edge discontinuity (degrades with `jpeg`)

These are diagnostics, not a finished classifier: the actual proxy is these five signals calibrated (fit) against
the real errors already measured in results_v2.csv (Contribution 1). That calibration is the next step, once the
real 50-record clean/degraded image set is available locally (currently only on Drive; see PROGRESS-LOG).
"""
import cv2
import numpy as np


def _gray(img):
    if img.ndim == 3:
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return img


def blur_score(img):
    """Variance of the Laplacian. Lower = blurrier. Classic no-reference blur metric (Pech-Pacheco et al. 2000)."""
    g = _gray(img)
    return float(cv2.Laplacian(g, cv2.CV_64F).var())


def skew_deg(img):
    """Median deviation (degrees) of detected long lines from axis-aligned (0/90/180). Uses Canny edges + the
    probabilistic Hough transform, restricted to lines at least 30% of the image width long, so that full-width
    structural lines (lead separators, page border, grid rules) are picked up instead of short, wiggly ECG-trace
    segments, which would bias a plain "strongest votes" selection toward the trace's own slope, not the page's.
    Recovers the injected rotation angle almost exactly on the six demo images (spike-tested against the known
    `degrade_rotate` angles: 2/5/8/12/16 degrees -> measured 2.0/5.0/8.0/12.0/16.0). Returns None if too few long
    lines are found (e.g. after heavy blur has erased the grid) -- "can't tell", not "no skew"."""
    g = _gray(img)
    edges = cv2.Canny(g, 50, 150)
    min_len = int(0.3 * g.shape[1])
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=100, minLineLength=min_len, maxLineGap=10)
    if lines is None or len(lines) < 3:
        return None
    lines = lines.reshape(-1, 4) if lines.ndim == 3 else lines
    angles = []
    for x1, y1, x2, y2 in lines:
        a = np.degrees(np.arctan2(y2 - y1, x2 - x1)) % 180
        dev = a % 90
        dev = min(dev, 90 - dev)
        angles.append(dev)
    return float(np.median(angles))


def resolution_score(img):
    """Ratio of high-spatial-frequency energy to total energy in the 2D FFT magnitude spectrum. Downsample+
    upsample (our `resolution` degradation) removes high-frequency content, so this drops; heavy blur removes
    it too, so this signal and blur_score are correlated by design -- both matter for the same physical cause
    (loss of fine detail), which is exactly what the plan's Tier-1 signal set is meant to capture jointly."""
    g = _gray(img).astype(np.float32)
    f = np.fft.fftshift(np.fft.fft2(g))
    mag = np.abs(f)
    h, w = mag.shape
    cy, cx = h // 2, w // 2
    yy, xx = np.ogrid[:h, :w]
    r = np.sqrt((yy - cy) ** 2 + (xx - cx) ** 2)
    r_max = min(cy, cx)
    high = mag[r > 0.5 * r_max].sum()
    total = mag.sum() + 1e-9
    return float(high / total)


def contrast_score(img):
    """Global standard deviation of grayscale intensity. Drops when the page is faded toward its mean
    (`gridcontrast`) and is also affected by a one-sided brightness gradient (`brightness`)."""
    g = _gray(img)
    return float(g.std())


def blockiness_score(img):
    """Period-8 peak in the spectrum of the column-wise mean gradient signal, relative to the background
    spectrum. A first attempt at this (spatial boundary-vs-inner pixel differencing) was too noisy to use --
    the dense printed grid and trace swamped it. This spectral version is monotonic and strong on the spike
    test (Spearman rho = -0.94 against JPEG level across the six demo images, see
    scripts/quality_proxy/spike_validate_signals.py), but DECREASES as JPEG damage increases, the opposite of
    the naive guess that more compression means more visible blocking. Likely cause: heavy quantization on this
    content suppresses high-frequency energy overall (including at the period-8 band) faster than it suppresses
    the background spectrum used to normalise it, rather than creating a cleanly separable blocking spike -- not
    confirmed, stated as a hypothesis. Usable as a monotonic feature for calibration either way, but the
    direction should not be assumed; let the calibration step's regression find its own sign."""
    g = _gray(img).astype(np.float32)
    col_grad = np.mean(np.abs(np.diff(g, axis=1)), axis=0)
    col_grad = col_grad - col_grad.mean()
    spec = np.abs(np.fft.rfft(col_grad))
    if len(spec) < 4:
        return 0.0
    k0 = int(round(len(col_grad) / 8))
    band = spec[max(1, k0 - 1):k0 + 2].mean()
    bg = np.median(spec[1:])
    return float(band / (bg + 1e-6))


def compute_quality_signals(img):
    """All five Tier-1 signals for one image (BGR, as read by cv2.imread)."""
    return {
        "blur_score": blur_score(img),
        "skew_deg": skew_deg(img),
        "resolution_score": resolution_score(img),
        "contrast_score": contrast_score(img),
        "blockiness_score": blockiness_score(img),
    }
