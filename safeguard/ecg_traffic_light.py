"""ECG digitiser traffic light: is the heart rate read from a digitised ECG trustworthy?

Input : one digitised 12-lead ECG as the Open-ECG-Digitizer saves it (1000 Hz, microvolts, 10 s, NaN where a lead was not read), as a dict
        {"I": array, "II": array, ... "V6": array} or an .npz file with those keys.
Output: GREEN (no warning), AMBER (check by a person) or RED (do not trust the heart rate), a score, and plain-language reasons.
It NEVER needs the true signal. It looks only at the digitised signal: beat regularity, agreement between the 12 leads (Einthoven and Goldberger rules),
how complete the leads are, and whether five standard beat detectors agree.

Model and thresholds: safeguard/model.json (built once by safeguard/train_safeguard.py from the simulated new 100 only; rules fixed in
docs/plan/analysis_plan_changes.md, 2026-11-10). Needs: numpy, neurokit2.   This is a research prototype, not a medical device.
"""
import json
import os
import warnings

import numpy as np

warnings.filterwarnings("ignore")
FS = 1000
LEADS = ["I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6"]
FEATURES = ["ii_complete", "n_unreadable_leads", "mean_other_lead_complete", "n_beats", "hr_ii", "hr_implausible", "rr_cv", "rr_max_ratio", "rr_min_ratio",
            "amp_log", "hf_share", "einthoven", "goldberger", "xlead_count_match", "xlead_count_absdiff"]
_MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model.json")


# ------------------------------------------------------------------ features (identical to scripts/analysis/section_D2_features.py)
def _prep(sig, min_s=1.5, min_fill=0.9):
    sig = np.asarray(sig, dtype=float)
    idx = np.where(np.isfinite(sig))[0]
    if len(idx) == 0:
        return None
    a0, b0 = int(idx[0]), int(idx[-1]) + 1
    seg = sig[a0:b0].copy()
    fin = np.isfinite(seg)
    if len(seg) < min_s * FS or fin.mean() < min_fill:
        return None
    if not fin.all():
        seg[~fin] = np.interp(np.where(~fin)[0], np.where(fin)[0], seg[fin])
    return a0, seg


def _rms(x):
    return float(np.sqrt(np.mean(np.square(x))))


def output_features(leads):
    """The 15 output features of one digitised ECG (leads: dict of 12 arrays)."""
    import neurokit2 as nk
    L = {k: np.asarray(leads[k], dtype=float) if k in leads else np.full(10000, np.nan) for k in LEADS}
    out = {}
    ii = L["II"]
    out["ii_complete"] = float(np.isfinite(ii).mean())
    cnt = {k: int(np.isfinite(v).sum()) for k, v in L.items()}
    out["n_unreadable_leads"] = int(sum(1 for k in LEADS if cnt[k] < 1500))
    out["mean_other_lead_complete"] = float(np.mean([min(1.0, cnt[k] / 2500.0) for k in LEADS if k != "II"]))
    nan = np.nan
    for k in FEATURES[3:]:
        out[k] = nan
    p2 = _prep(ii, min_s=3.0)
    if p2 is None:
        return out
    a2, seg2 = p2
    try:
        cl = nk.ecg_clean(seg2, sampling_rate=FS, method="neurokit")
        rpk = np.asarray(nk.ecg_peaks(cl, sampling_rate=FS)[1]["ECG_R_Peaks"])
    except Exception:
        return out
    out["n_beats"] = int(len(rpk))
    out["amp_log"] = float(np.log10(max(1e-6, np.percentile(seg2, 95) - np.percentile(seg2, 5))))
    f = np.abs(np.fft.rfft(seg2 - seg2.mean())) ** 2
    fr = np.fft.rfftfreq(len(seg2), 1 / FS)
    out["hf_share"] = float(f[fr > 40].sum() / max(1e-12, f.sum()))
    if len(rpk) >= 3:
        rr = np.diff(rpk) / FS
        hr = float(np.mean(60.0 / rr))
        out["hr_ii"] = hr
        out["hr_implausible"] = float(hr < 30 or hr > 200)
        out["rr_cv"] = float(np.std(rr) / np.mean(rr))
        out["rr_max_ratio"] = float(rr.max() / np.median(rr))
        out["rr_min_ratio"] = float(rr.min() / np.median(rr))
    m = np.isfinite(L["I"]) & np.isfinite(L["II"]) & np.isfinite(L["III"])
    if m.sum() >= 1000:
        i_, ii_, iii_ = (L[k][m] - L[k][m].mean() for k in ("I", "II", "III"))
        out["einthoven"] = float(_rms(ii_ - i_ - iii_) / max(1e-9, _rms(ii_)))
    m = np.isfinite(L["aVR"]) & np.isfinite(L["aVL"]) & np.isfinite(L["aVF"])
    if m.sum() >= 1000:
        a_, b_, c_ = (L[k][m] - L[k][m].mean() for k in ("aVR", "aVL", "aVF"))
        out["goldberger"] = float(_rms(a_ + b_ + c_) / max(1e-9, np.mean([_rms(a_), _rms(b_), _rms(c_)])))
    match, diffs = [], []
    for k in LEADS:
        if k == "II":
            continue
        pr = _prep(L[k])
        if pr is None:
            continue
        a0, seg = pr
        try:
            c = nk.ecg_clean(seg, sampling_rate=FS, method="neurokit")
            pk = np.asarray(nk.ecg_peaks(c, sampling_rate=FS)[1]["ECG_R_Peaks"]) + a0
        except Exception:
            continue
        lo, hi = a0 + 100, a0 + len(seg) - 100
        n_lead = int(((pk >= lo) & (pk < hi)).sum())
        n_ref = int((((rpk + a2) >= lo) & ((rpk + a2) < hi)).sum())
        match.append(float(n_lead == n_ref))
        diffs.append(abs(n_lead - n_ref))
    if match:
        out["xlead_count_match"] = float(np.mean(match))
        out["xlead_count_absdiff"] = float(np.mean(diffs))
    return out


def detector_spread(leads):
    """Heart rate from five standard beat detectors on lead II; returns (spread in bpm, list of the five rates). For the reasons only."""
    import neurokit2 as nk
    s = np.asarray(leads["II"], dtype=float)
    s = s[np.isfinite(s)] / 1000.0
    hrs = []
    for m, c in (("neurokit", False), ("neurokit", True), ("pantompkins1985", True), ("hamilton2002", True), ("elgendi2010", True)):
        try:
            x = nk.ecg_clean(s, sampling_rate=FS, method="neurokit") if c else s
            r = np.asarray(nk.ecg_peaks(x, sampling_rate=FS, method=m)[1]["ECG_R_Peaks"], dtype=float) / FS
            hrs.append(float(60.0 / np.diff(r).mean()) if len(r) >= 3 else np.nan)
        except Exception:
            hrs.append(np.nan)
    a = np.array(hrs)
    ok = np.isfinite(a)
    return (float(a[ok].max() - a[ok].min()) if ok.sum() >= 2 else np.nan), hrs


# ------------------------------------------------------------------ model (numpy only)
def load_model(path=_MODEL_PATH):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def score_from_features(feat, model=None):
    """Logistic risk score in [0, 1] from the 15 features (median imputation, standardisation, logistic regression: all stored in model.json)."""
    model = model or load_model()
    x = np.array([feat.get(k, np.nan) for k in model["features"]], dtype=float)
    med = np.array(model["impute_median"], dtype=float)
    x = np.where(np.isfinite(x), x, med)
    z = (x - np.array(model["scaler_mean"])) / np.array(model["scaler_scale"])
    s = float(np.dot(z, np.array(model["coef"])) + model["intercept"])
    return float(1.0 / (1.0 + np.exp(-s)))


def load_npz(path):
    z = np.load(path, allow_pickle=False)
    return {k: np.asarray(z[k], dtype=float) for k in z.files}


def check(leads, model=None):
    """Returns {'light': 'GREEN'|'AMBER'|'RED', 'score': float, 'reasons': [str], 'features': dict, 'detector_spread_bpm': float}."""
    model = model or load_model()
    feat = output_features(leads)
    reasons = []
    n_beats, hr = feat.get("n_beats"), feat.get("hr_ii")
    no_hr = (n_beats is None) or not np.isfinite(n_beats) or n_beats < 3 or hr is None or not np.isfinite(hr)
    score = score_from_features(feat, model)
    if no_hr:
        light = "RED"
        reasons.append("no usable heart rate: fewer than 3 beats found in lead II")
    else:
        light = "RED" if score >= model["red_threshold"] else ("AMBER" if score >= model["amber_threshold"] else "GREEN")
    p90 = model["reason_p90"]
    msgs = {"rr_cv": "beat spacing is irregular", "rr_max_ratio": "one beat gap is much longer than the others (a missed beat?)",
            "rr_min_ratio": "one beat gap is much shorter than the others (an extra beat?)", "einthoven": "leads I, II and III disagree with each other (should satisfy II = I + III)",
            "goldberger": "aVR, aVL and aVF disagree with each other (should add up to zero)", "xlead_count_absdiff": "other leads count a different number of beats than lead II",
            "n_unreadable_leads": "several leads could not be read"}
    for k, m in msgs.items():
        v = feat.get(k)
        if v is not None and np.isfinite(v) and v > p90.get(k, np.inf):
            reasons.append(m)
    sp = np.nan
    if not no_hr and "II" in leads:
        sp, _ = detector_spread(leads)
        if np.isfinite(sp) and sp > model["detector_spread_note_bpm"]:
            reasons.append(f"five beat detectors disagree about the heart rate by {sp:.0f} bpm")
    if light == "GREEN":                                    # out-of-range guard (rule added 2026-11-10, before any real-data evaluation)
        odd = [k for k in model.get("guard_features", []) if feat.get(k) is not None and np.isfinite(feat[k])
               and (feat[k] < model["train_min"][k] or feat[k] > model["train_max"][k])]
        if odd:
            light = "AMBER"
            reasons.append("signal looks unlike the data the tool was trained on (" + ", ".join(odd[:3]) + ")")
    if light == "GREEN" and not reasons:
        reasons.append("beats are regular and the leads agree")
    elif light == "GREEN":                                  # minor notes only: they did not change the light
        reasons = ["minor note (did not change the light): " + x for x in reasons]
    return dict(light=light, score=score, reasons=reasons, features=feat, detector_spread_bpm=sp)


def check_npz(path, model=None):
    return check(load_npz(path), model)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("usage: python safeguard/ecg_traffic_light.py file1.npz [file2.npz ...]")
        raise SystemExit(1)
    for p in sys.argv[1:]:
        r = check_npz(p)
        print(f"{os.path.basename(p)}: {r['light']}  (score {r['score']:.2f})  " + "; ".join(r["reasons"]))
