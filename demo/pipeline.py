"""MediSense-Cardio demo pipeline: photo of an ECG page -> straighten -> Open-ECG-Digitizer -> heart rate + traffic light.

Uses EXACTLY the pieces of the study, unchanged:
  scripts/preprocess/page_straighten.py   (page finder + perspective correction, the fix confirmed in Section Q2)
  scripts/tools/Open-ECG-Digitizer        (commit 97a15087, the two published weight files, the same settings file as every run of the study)
  safeguard/ecg_traffic_light.py          (15 output features -> logistic score -> GREEN / AMBER / RED)
Research prototype, not a medical device.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import time
import warnings

import cv2
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
DIG_DIR = os.path.join(ROOT, "scripts", "tools", "Open-ECG-Digitizer")
sys.path.insert(0, os.path.join(ROOT, "scripts", "preprocess"))
sys.path.insert(0, os.path.join(ROOT, "safeguard"))
import ecg_traffic_light as T  # noqa: E402
from page_straighten import straighten  # noqa: E402

LEADS = T.LEADS
LAST_DEVICE = "cpu"
LAST_META = {}


def device_name():
    import torch
    return "cuda" if torch.cuda.is_available() else "cpu"


def _config_text(images_path, output_path, device):
    # identical to write_digitizer_config() in the Kaggle notebooks of the study
    f = lambda p: p.replace("\\", "/")
    return f"""MODEL:
  class_path: 'src.model.inference_wrapper.InferenceWrapper'
  KWARGS:
    config:
      SIGNAL_EXTRACTOR:
        class_path: 'src.model.signal_extractor.SignalExtractor'
        KWARGS: {{}}
      PERSPECTIVE_DETECTOR:
        class_path: 'src.model.perspective_detector.PerspectiveDetector'
        KWARGS:
          num_thetas: 250
      DEWARPER:
        class_path: 'src.model.dewarper.Dewarper'
        KWARGS:
          abs_peak_threshold: 0.1
      SEGMENTATION_MODEL:
        class_path: 'src.model.unet.UNet'
        weight_path: './weights/unet_weights_07072025.pt'
        KWARGS:
          num_in_channels: 3
          num_out_channels: 4
          dims: [32, 64, 128, 256, 320, 320, 320, 320]
          depth: 2
      CROPPER:
        class_path: 'src.model.cropper.Cropper'
        KWARGS:
          granularity: 80
          percentiles: [0.02, 0.98]
          alpha: 0.85
      PIXEL_SIZE_FINDER:
        class_path: 'src.model.pixel_size_finder.PixelSizeFinder'
        KWARGS:
          min_number_of_grid_lines: 30
          max_number_of_grid_lines: 70
          lower_grid_line_factor: 0.5
      LAYOUT_IDENTIFIER:
        class_path: 'src.model.lead_identifier.LeadIdentifier'
        config_path: 'src/config/lead_layouts_george-moody-2024.yml'
        unet_config_path: 'src/config/lead_name_unet.yml'
        unet_weight_path: './weights/lead_name_unet_weights_07072025.pt'
        KWARGS:
          debug: false
          device: '{device}'
          possibly_flipped: false
          target_num_samples: 10000
          required_valid_samples: 2
    device: '{device}'
    resample_size: 3000
    rotate_on_resample: true
    enable_timing: false
    apply_dewarping: false
DATA:
  images_path: '{f(images_path)}'
  image_extensions: ['.png', '.jpg', '.jpeg', '.JPG']
  save_mode: 'all'
  layout_should_include_substring: false
  output_path: '{f(output_path)}'
  clear_output_dir_if_exists: true
"""


# ---- repeatable output (added 2026-11-15) -------------------------------------------------------------------------------------------------
# Open-ECG-Digitizer breaks ties in its line tracer with `torch.randn(...) * 1e-6` (src/model/signal_extractor.py, _get_pixel_vals) and never seeds torch,
# so two runs of the same photo can differ (PR up to 22 ms and axis up to 11 degrees in our repeat test). The digitiser code is NOT changed: the demo starts it
# through a two-line bootstrap that seeds torch first. The seed is fixed in advance (42, the digitiser's own file-order seed), not chosen by looking at results.
# Set the environment variable DEMO_DIGITISER_SEED=none to get the unseeded behaviour of the study runs.
DIGITISER_SEED = os.environ.get("DEMO_DIGITISER_SEED", "42")
_BOOT = ("import sys, runpy, torch; torch.manual_seed({seed}); sys.argv = ['src.digitize', '--config', sys.argv[1]]; "
         "runpy.run_module('src.digitize', run_name='__main__', alter_sys=True)")


def _run_digitiser(cfg):
    """Run the digitiser on a settings file; seeded unless DEMO_DIGITISER_SEED=none."""
    if DIGITISER_SEED.lower() == "none":
        return subprocess.run([sys.executable, "-m", "src.digitize", "--config", cfg], cwd=DIG_DIR, capture_output=True, text=True)
    return subprocess.run([sys.executable, "-c", _BOOT.format(seed=int(DIGITISER_SEED)), cfg], cwd=DIG_DIR, capture_output=True, text=True)


def digitise_image(img_bgr, device=None):
    """Run the digitiser on one BGR image. Returns ({lead: float array (1 kHz, microvolts)} or None, tool_output)."""
    device = device or device_name()
    tmp = tempfile.mkdtemp(prefix="medisense_")
    try:
        imgs, outd = os.path.join(tmp, "in"), os.path.join(tmp, "out")
        os.makedirs(imgs)
        cv2.imwrite(os.path.join(imgs, "page.png"), img_bgr)
        cfg = os.path.join(tmp, "config.yml")
        with open(cfg, "w") as fh:
            fh.write(_config_text(imgs, outd, device))
        r = _run_digitiser(cfg)
        csv = os.path.join(outd, "page_timeseries_canonical.csv")
        global LAST_DEVICE
        LAST_DEVICE = device
        if not os.path.exists(csv) and device == "cuda":
            # GPU failed (for example out of memory on a 4 GB card): try again on the CPU, same settings
            with open(cfg, "w") as fh:
                fh.write(_config_text(imgs, outd, "cpu"))
            r = _run_digitiser(cfg)
            LAST_DEVICE = "cpu (GPU run failed)"
        if not os.path.exists(csv):
            return None, (r.stdout + r.stderr)[-1500:]
        d = pd.read_csv(csv)
        global LAST_META
        LAST_META = {}
        mp = os.path.join(outd, "digitization_metadata.csv")
        if os.path.exists(mp):
            try:
                LAST_META = pd.read_csv(mp).iloc[0].to_dict()   # layout name, layout match cost, flipped flag (what the digitiser recognised)
            except Exception:
                LAST_META = {}
        return {c: d[c].to_numpy(dtype="float32").astype(float) for c in d.columns}, ""
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def hr_clean(sig_mv, fs=1000):
    """Heart rate, cleaned measure of the study: nk.ecg_clean(neurokit) -> nk.ecg_peaks -> mean of nk.ecg_rate. Returns (hr or nan, n_beats)."""
    import neurokit2 as nk
    s = np.asarray(sig_mv, float)
    s = s[np.isfinite(s)]
    if len(s) < 10 * 100:
        return float("nan"), 0
    x = nk.ecg_clean(s, sampling_rate=fs, method="neurokit")
    p, info = nk.ecg_peaks(x, sampling_rate=fs)
    n = int(len(info.get("ECG_R_Peaks", [])))
    if n < 3:
        return float("nan"), n
    return float(np.nanmean(nk.ecg_rate(p, sampling_rate=fs, desired_length=len(s)))), n


def orient(img_bgr):
    """A photo taller than wide (a phone held upright over a landscape page) is turned a quarter turn counter-clockwise before the page finder runs: the same step that was fixed and tested
    on the printed-paper photos (Section H2, 'V2b'). Returns (image, turned)."""
    if img_bgr.shape[0] > img_bgr.shape[1]:
        return cv2.rotate(img_bgr, cv2.ROTATE_90_COUNTERCLOCKWISE), True
    return img_bgr, False


def run(img_bgr, device=None):
    """Whole pipeline on a photo (BGR array). Returns a dict with everything the page shows."""
    t0 = time.time()
    out = dict(error=None, notes=[])
    img_bgr, turned = orient(img_bgr)
    if turned:
        out["notes"].append("The photo was taller than wide, so it was turned a quarter turn before the page was looked for.")
    straight, found = straighten(img_bgr, 2200, 1700)
    out["page_found"] = bool(found)
    out["straightened"] = straight
    if not found:
        out["notes"].append("The page edges were not found, so the photo was used as it is (the straightening step was skipped).")
    leads, tool_out = digitise_image(straight, device)
    out["tool_output"] = tool_out
    if leads is None:
        out.update(error="The digitiser gave no output for this photo.", light="RED", reasons=["no usable heart rate (the digitiser gave no output)"],
                   hr=float("nan"), n_beats=0, leads=None, seconds=time.time() - t0)
        return out
    out["leads"] = leads
    out["meta"] = dict(LAST_META)
    ii = leads.get("II")
    hr, nb = hr_clean(ii / 1000.0) if ii is not None else (float("nan"), 0)
    chk = T.check(leads)
    out.update(light=chk["light"], score=chk["score"], reasons=chk["reasons"], hr=hr, n_beats=nb,
               detector_spread=chk.get("detector_spread_bpm"), features=chk.get("features"), seconds=time.time() - t0)
    return out


def run_plain(img_bgr, device=None):
    """The same pipeline WITHOUT the straightening step (to show what the fix changes)."""
    t0 = time.time()
    leads, tool_out = digitise_image(img_bgr, device)
    if leads is None:
        return dict(light="RED", hr=float("nan"), n_beats=0, reasons=["no usable heart rate (the digitiser gave no output)"], seconds=time.time() - t0)
    ii = leads.get("II")
    hr, nb = hr_clean(ii / 1000.0) if ii is not None else (float("nan"), 0)
    chk = T.check(leads)
    return dict(light=chk["light"], score=chk["score"], reasons=chk["reasons"], hr=hr, n_beats=nb, seconds=time.time() - t0)
