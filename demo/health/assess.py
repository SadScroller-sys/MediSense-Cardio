"""Heart health assessment logic: parameters with status and tested confidence, supported ECG-pattern findings, the overall indicator, next steps.
Reuses the existing pipeline output (traffic light, straightening, heart rate, PR and axis methods). Findings come from the model in model.py and only for classes
that passed the pass rules in results/health/findings_status.json. No risk level is ever produced. Research prototype. Not a medical device."""
import json
import os

import numpy as np

from . import data as D
from . import wording as W

ROOT = D.ROOT
OUT = os.path.join(ROOT, "results", "health") + os.sep
_MODEL = {}
# POST-HOC, MORE CAUTIOUS than the pre-set rules (logged 2026-11-15): (1) no percentage is shown on photos for any finding, because calibration on phone photos was worse than on the
# benchmark (T3 calibration error 0.08 to 0.27) and the guide asked for no arbitrary percentages; (2) the "normal-looking pattern" check is not shown as a result on photos, because it
# found only 36 in 100 normal ECGs there. Both only narrow what is shown; the pre-set pass table (results/health/SECTION_HEALTH.md) is unchanged.
POSTHOC_HIDE = {"NORM": "not reliable enough on phone photos (in our tests it recognised only 36 in 100 normal ECGs), so it is not shown as a result"}

# What we tested (results/FINAL_NUMBERS.md), shown as the confidence of each measurement. These are tested errors of the METHOD, not a per-photo probability.
CONF = {
    "hr": {"GREEN": "GREEN read: on real captures 0.2% of GREEN heart rates were wrong (2 of 917), but on printed paper photographed by another phone 2 of 19 were wrong, so a GREEN light does not prove the heart rate is right.",
           "AMBER": "AMBER read: about 7 in 100 such heart rates were wrong in our tests; have a person check it."},
    "rr": "Taken from the same beats as the heart rate, so it is as reliable as the heart rate.",
    "pr": "Tested on straightened photos: typically about 12 ms from hospital software (95 in 100 within 40 ms), and about 13 ms on printed paper. Shown only for steady beat spacing.",
    "axis": "Tested on straightened photos: typically about 4 degrees from hospital software on screen photos and about 6 degrees on printed paper (about 9 in 10 within 30 degrees).",
}
REF = {"hr": (60, 100), "rr": (600, 1000), "pr": (120, 200), "axis": (-30, 90)}


def _load():
    if "m" not in _MODEL:
        try:
            import torch
            from . import model as M
            dev = "cuda" if torch.cuda.is_available() else "cpu"
            net, cal = M.load_model(dev)
            status = json.load(open(OUT + "findings_status.json"))["classes"]
            import pandas as pd
            mt = pd.read_csv(OUT + "health_test_metrics.csv")
            t3 = mt[mt.set.str.startswith("T3")].set_index("cls")
            for c in status:
                status[c]["sens_photos"], status[c]["spec_photos"] = float(t3.loc[c, "sensitivity"]), float(t3.loc[c, "specificity"])
            try:            # the fresh-data test of the SAME model (Section HEALTH3, 2026-11-16): a finding stays supported only if it also passed there (rules logged before)
                f3 = OUT + "findings_status_v3.json"
                if os.path.exists(f3):
                    s3 = json.load(open(f3))["classes"]
                    for c in status:
                        if c in s3:
                            status[c]["supported_phone_photos"] = bool(status[c]["supported_phone_photos"] and s3[c]["supported_phone_photos"])
                            status[c]["supported_drawn_pages"] = bool(status[c]["supported_drawn_pages"] and s3[c]["supported_drawn_pages"])
            except Exception:
                pass
            net2 = cal2 = status2 = None
            try:            # model 2 (fine-tuned on real digitised data): used per class ONLY where its own fresh test passed (results/health/findings_status_v2.json)
                if os.path.exists(OUT + "findings_status_v2.json") and os.path.exists(OUT + "model_v2.pt"):
                    net2 = M.EcgNet().to(dev)
                    net2.load_state_dict(torch.load(OUT + "model_v2.pt", map_location=dev))
                    net2.eval()
                    cal2 = json.load(open(OUT + "calibration_v2.json"))
                    status2 = json.load(open(OUT + "findings_status_v2.json"))["classes"]
            except Exception:
                net2 = cal2 = status2 = None
            _MODEL["m"] = (M, net, cal, status, dev)
            _MODEL["v2"] = (net2, cal2, status2)
        except Exception as e:                       # model not trained / not tested yet: findings are simply not available
            _MODEL["m"] = (None, None, None, None, str(e)[:120])
    return _MODEL["m"]


def parameters(light, hr, rr_cv, pr_ms, axis_deg, page_found, reasons, no_output):
    """List of dicts: name, key, value, unit, ref, status, reason, confidence. Nothing is made up: a missing or unreliable value is 'Not measured' or 'Hidden' with the reason."""
    from explain import pr_shown, axis_shown
    has_hr = (hr is not None) and (hr == hr) and not no_output and light in ("GREEN", "AMBER")
    rows = []
    rows.append(dict(key="hr", name="Heart rate", unit="bpm", value=float(hr) if has_hr else None, ref=REF["hr"],
                     status=("Measured" if light == "GREEN" else "Measured, not sure") if has_hr else "Not measured",
                     reason="" if has_hr else "the read looks unreliable (RED light) or gave no output",
                     confidence=CONF["hr"].get(light, "") if has_hr else ""))
    rr = 60000.0 / hr if has_hr and hr > 0 else None
    rows.append(dict(key="rr", name="RR interval (time between beats)", unit="ms", value=rr, ref=REF["rr"], status=("Measured" if light == "GREEN" else "Measured, not sure") if rr else "Not measured",
                     reason="" if rr else "no reliable heart rate", confidence=CONF["rr"] if rr else ""))
    show_pr = pr_shown(light, pr_ms, page_found, reasons, rr_cv)
    rows.append(dict(key="pr", name="PR interval", unit="ms", value=float(pr_ms) if show_pr else None, ref=REF["pr"], status="Measured" if show_pr else "Hidden",
                     reason="" if show_pr else "shown only for a GREEN light, a straightened photo and steady beat spacing (without P waves, as in atrial fibrillation, a PR would be meaningless)",
                     confidence=CONF["pr"] if show_pr else ""))
    show_ax = axis_shown(light, axis_deg, page_found)
    rows.append(dict(key="axis", name="Frontal QRS axis", unit="degrees", value=float(axis_deg) if show_ax else None, ref=REF["axis"], status="Measured" if show_ax else "Hidden",
                     reason="" if show_ax else "shown only for a GREEN light on a straightened photo", confidence=CONF["axis"] if show_ax else ""))
    WHY = {"qrs": "failed our validation tests on photos: on clean drawn pages it was close (about 4 ms), but on phone photos it read about 8 ms too long and pulled wide QRS toward normal, so a number would mislead; a second attempt trained on doctor-marked public data also failed (it read about 5 ms too short on held-out recordings)",
           "qt": "failed our validation tests: on phone photos a long QT was read too short and a short QT too long, by about 40 ms, which could falsely reassure; a second attempt trained on doctor-marked public data was accurate on clean and damaged signals but not on our digitised dataset pictures (typical error 66 ms), so no number is shown"}
    for key, name in (("qrs", "QRS duration"), ("qt", "QT / QTc interval")):
        rows.append(dict(key=key, name=name, unit="ms", value=None, ref=None, status="Not measured", reason=WHY[key], confidence=""))
    return rows


def findings(leads, light, page_found):
    """Model findings, only for classes that passed the pass rules for phone photos. Returns (list, reason_if_none)."""
    M, net, cal, status, dev = _load()
    out = []
    if M is None:
        return [dict(cls=c, name=W.FINDING_NAMES[c], state="not_available", reason="the model has not been trained and tested yet", p=None, detected=None) for c in D.CLASSES], "model not available"
    usable = leads is not None and light in ("GREEN", "AMBER") and page_found
    net2, cal2, status2 = _MODEL.get("v2", (None, None, None))
    if usable:
        X = D.digitised_to_input(leads)[None]
        P = M.calibrated(cal, M.logits_from_inputs(net, X, dev))[0]
        if net2 is not None:
            lg2 = M.logits_from_inputs(net2, X, dev)[0]
            P2 = 1 / (1 + np.exp(-(lg2 * np.array([cal2["platt"][c]["a"] for c in D.CLASSES]) + np.array([cal2["platt"][c]["b"] for c in D.CLASSES]))))
    for k, c in enumerate(D.CLASSES):
        s = status[c]
        use2 = bool(net2 is not None and status2 and status2.get(c, {}).get("supported_phone_photos"))
        if use2 and usable and c not in POSTHOC_HIDE:
            s2 = status2[c]
            p2 = float(P2[k])
            out.append(dict(cls=c, name=W.FINDING_NAMES[c], state="supported", reason="", p=p2 if s2["show_percentage_photos"] else None, detected=bool(p2 >= s2["threshold"]),
                            auroc=s2["pages_auroc"], p_internal=p2, sens=s2["sens_photos"], spec=s2["spec_photos"], model="2"))
            continue
        if not usable:
            out.append(dict(cls=c, name=W.FINDING_NAMES[c], state="not_available", reason="the photo is not clear enough or the page was not straightened", p=None, detected=None))
        elif c in POSTHOC_HIDE:
            out.append(dict(cls=c, name=W.FINDING_NAMES[c], state="not_available", reason=POSTHOC_HIDE[c], p=None, detected=None))
        elif not s["supported_phone_photos"]:
            why = ("could not be tested on enough phone photos" if not s["testable_photos"] else "did not pass our pre-set accuracy test on phone photos")
            if c == "CD" and s["testable_photos"]:
                why = "did not pass our accuracy test on real printed-paper photos; specific conduction patterns appear only in the research-only block below, tested on drawn and simulated pages only"
            out.append(dict(cls=c, name=W.FINDING_NAMES[c], state="not_available", reason=why, p=None, detected=None))
        else:
            p = float(P[k])
            out.append(dict(cls=c, name=W.FINDING_NAMES[c], state="supported", reason="", p=None, detected=bool(p >= s["threshold"]),
                            auroc=s["T2_auroc"], p_internal=p, sens=s["sens_photos"], spec=s["spec_photos"]))
    return out, ""


_EXTRA = {}


def _load_extra():
    """Networks A and B (public data only) with their status files; only findings that passed on drawn pages are kept."""
    if "x" not in _EXTRA:
        out = []
        try:
            import torch
            from . import find2 as F
            from . import model as M
            dev = "cuda" if torch.cuda.is_available() else "cpu"
            for src, folder, names in (("A", F.OUT_A, F.A_CODES), ("B", F.OUT_B, F.B_LABELS)):
                if not (os.path.exists(folder + "model.pt") and os.path.exists(folder + "status.json") and os.path.exists(folder + "calibration.json")):
                    continue
                st = json.load(open(folder + "status.json"))["classes"]
                keep = [c for c in names if f"{src}:{c}" in W.EXTRA_NAMES and ((f"{src}:{c}" in _op().get("patterns", {})) if _op() else ((st[c]["supported_drawn_pages"] or _n_ok(src, c)) and _n_not_removed(src, c)))]
                if not keep:
                    continue
                net = M.EcgNet(n_out=len(names)).to(dev)
                net.load_state_dict(torch.load(folder + "model.pt", map_location=dev))
                net.eval()
                out.append((src, names, keep, st, json.load(open(folder + "calibration.json")), net, M, dev))
        except Exception:
            out = []
        _EXTRA["x"] = out
    return _EXTRA["x"]


def _n_status():
    """Results of the positive-rich set N (results/paper_n/N_status.json), if present."""
    if "n" not in _EXTRA:
        try:
            _EXTRA["n"] = json.load(open(os.path.join(ROOT, "results", "paper_n", "N_status.json")))["pairs"]
        except Exception:
            _EXTRA["n"] = {}
    return _EXTRA["n"]


def _n_key(src, cls):
    return {"1AVB": "1AVB", "CLBBB": "CLBBB"}.get(cls, cls) + f" ({src})"


def _n_ok(src, cls):
    """Passed drawn pages and simulated photos of set N, and is the model that was kept for its condition."""
    s = _n_status().get(_n_key(src, cls))
    return bool(s and s["pass_pages"] and s["pass_sim"] and "not shown" not in s.get("same_condition_choice", ""))


def _n_not_removed(src, cls):
    s = _n_status().get(_n_key(src, cls))
    return not (s and not s["pass_pages"])


def _op():
    """New operating point (results/find2_op/app_operating_point.json): thresholds at specificity 0.97 chosen on validation data only; NDT dropped (decision of the user, post hoc; analysis_plan_changes.md)."""
    if "op" not in _EXTRA:
        try:
            _EXTRA["op"] = json.load(open(os.path.join(ROOT, "results", "find2_op", "app_operating_point.json")))
        except Exception:
            _EXTRA["op"] = {}
    return _EXTRA["op"]


def _extra_sens_spec(src, cls):
    """Sensitivity and specificity on the 300 clean drawn pages (T2) at the frozen threshold, from the one test of each network (test_metrics.csv)."""
    key = (src, cls)
    if key not in _EXTRA_SS:
        try:
            import pandas as pd
            from . import find2 as F
            t = pd.read_csv((F.OUT_A if src == "A" else F.OUT_B) + "test_metrics.csv")
            r = t[t.set.str.startswith("T2") & (t.cls == cls)].iloc[0]
            _EXTRA_SS[key] = (float(r.sensitivity), float(r.specificity))
        except Exception:
            _EXTRA_SS[key] = (None, None)
    return _EXTRA_SS[key]


_EXTRA_SS = {}


def extra_findings(leads, light, page_found):
    """Research-only extra patterns (networks A and B), only for a GREEN or AMBER straightened photo and only for findings that passed on drawn pages. No percentage."""
    if leads is None or light not in ("GREEN", "AMBER") or not page_found:
        return []
    out = []
    X = D.digitised_to_input(leads)[None]
    for src, names, keep, st, cal, net, M, dev in _load_extra():
        lg = M.logits_from_inputs(net, X, dev)[0]
        for k, c in enumerate(names):
            if c in keep:
                p = 1 / (1 + np.exp(-(lg[k] * cal["platt"][c]["a"] + cal["platt"][c]["b"])))
                op = _op().get("patterns", {}).get(f"{src}:{c}")
                if op:                               # the new operating point: strict threshold, numbers measured at it
                    out.append(dict(cls=c, src=src, name=W.EXTRA_NAMES[f"{src}:{c}"], detected=bool(p >= op["threshold"]), auroc=float(st[c]["T2_auroc"]), positives=int(op["pages_positives"]), sens=op["pages_sens"], spec=op["pages_spec"],
                                    sim_sens=op["sim_sens"], sim_spec=op["sim_spec"], sim_ok=bool(_n_status().get(_n_key(src, c), {}).get("pass_sim", True))))
                    continue
                sn, sp = _extra_sens_spec(src, c)
                ns = _n_status().get(_n_key(src, c))
                if ns:                               # set N has more positives: use its numbers for the drawn pages and add the simulated photos
                    out.append(dict(cls=c, src=src, name=W.EXTRA_NAMES[f"{src}:{c}"], detected=bool(p >= st[c]["threshold"]), auroc=float(ns["pages_auroc"]), positives=int(ns["pages_pos"]), sens=ns["sens_pages"], spec=ns["spec_pages"],
                                    sim_sens=ns["sens_sim"], sim_spec=ns["spec_sim"], sim_ok=bool(ns["pass_sim"])))
                else:
                    out.append(dict(cls=c, src=src, name=W.EXTRA_NAMES[f"{src}:{c}"], detected=bool(p >= st[c]["threshold"]), auroc=float(st[c]["T2_auroc"]), positives=int(st[c]["T2_positives"]), sens=sn, spec=sp))
    return out


_PSTAT = {}


def _p_status():
    """Verdict of set P (results/paper_p/P_status.json, written by section_P_verdict.py); empty until set P has been tested."""
    if "x" not in _PSTAT:
        f = os.path.join(D.ROOT, "results", "paper_p", "P_status.json")
        try:
            _PSTAT["x"] = json.load(open(f))["pairs"] if os.path.exists(f) else {}
        except Exception:
            _PSTAT["x"] = {}
    return _PSTAT["x"]


_QT = {}


def _qt_status():
    if "s" not in _QT:
        f = os.path.join(D.ROOT, "results", "qt_public", "T2_status.json")
        try:
            _QT["s"] = json.load(open(f)) if os.path.exists(f) else {}
        except Exception:
            _QT["s"] = {}
    return _QT["s"]


def qt_measure(leads):
    """QT in ms from the public-data model (results/qt_public/model.pt); only when T2_status.json says it passed on dataset pictures. Returns None otherwise."""
    if not _qt_status().get("qt_available") or leads is None:
        return None
    try:
        import torch
        from . import intervals_ml as I
        if "net" not in _QT:
            dev = "cuda" if torch.cuda.is_available() else "cpu"
            net = I.IntervalNet(n_in=24, n_out=2).to(dev)
            net.load_state_dict(torch.load(os.path.join(D.ROOT, "results", "qt_public", "model.pt"), map_location=dev))
            net.eval()
            _QT["net"] = (net, dev)
        net, dev = _QT["net"]
        x = I.digitised_to_input250(leads)[None]
        with torch.no_grad():
            o = net(torch.from_numpy(np.ascontiguousarray(x)).to(dev)).cpu().numpy()[0]
        return float(o[1] * 45.0 + 420.0)
    except Exception:
        return None


def apply_qt(params, leads):
    """Replace the 'QT not measured' row by a measured value when QT passed the set-P rules."""
    q = qt_measure(leads)
    if q is None or not (250 <= q <= 650):
        return params
    st = _qt_status()["qt_sim"]
    for r in params:
        if r["key"] == "qt":
            r.update(name="QT interval (not corrected for heart rate)", value=q, ref=(350, 450), status="Measured",
                     reason="", confidence="typical error about %d ms on simulated phone photos of dataset ECGs; not validated on real phone photos" % round(st["mae"]))
    return params


def promote_validated(fl, extra):
    """Set P verdict: a research-only pattern that PASSED all set-P rules moves into the main list ('validated on dataset pictures'); one that failed the drawn-page rule is dropped.
    Returns (findings, extra). Nothing changes while P_status.json does not exist."""
    st = _p_status()
    if not st:
        return fl, extra
    keep, fl = [], list(fl)
    for x in extra:
        s = st.get(f"{x['src']}:{x['cls']}")
        if s and s.get("available"):
            row = dict(cls=f"{x['src']}:{x['cls']}", name=x["name"], state="supported", reason="", p=None, detected=bool(x["detected"]), p_internal=0.5, auroc=s["sim_auroc"], sens=s["sim_sens"], spec=s["sim_spec"], validated=True, positives=s["sim_pos"])
            if x["cls"] == "AF" and x["src"] == "B":
                fl = [f for f in fl if f["cls"] != "AF"]
            fl.append(row)
        elif s and str(s.get("verdict", "")).startswith("FAILS"):
            continue
        else:
            keep.append(x)
    return fl, keep


_QS = {}


def _q_status():
    """Final verdict of the fresh sets Q and R (results/paper_r/final_status.json: pooled numbers; availability from the pre-set rule). Empty until tested."""
    if "s" not in _QS:
        f = os.path.join(D.ROOT, "results", "paper_r", "final_status.json")
        try:
            _QS["s"] = json.load(open(f))["pairs"] if os.path.exists(f) else {}
        except Exception:
            _QS["s"] = {}
    return _QS["s"]


def _q_prob(leads, pair):
    """Probability of a retrained-network pair (B2 or A2) for one digitised page; None if the model cannot be loaded."""
    try:
        import torch
        from . import find2 as F
        from . import model as M
        tag, c = pair.split(":")
        key = "net" + tag
        names = F.B_LABELS if tag == "B2" else F.A_CODES
        if key not in _QS:
            folder = os.path.join(D.ROOT, "results", "find2_" + tag) + os.sep
            net = M.EcgNet(n_out=len(names))
            net.load_state_dict(torch.load(folder + "model.pt", map_location="cpu"))
            net.eval()
            _QS[key] = (net, json.load(open(folder + "calibration.json"))["platt"], json.load(open(folder + "thresholds_q.json"))["thresholds"])
        net, platt, thr = _QS[key]
        X = D.digitised_to_input(leads)[None]
        lg = M.logits_from_inputs(net, X, "cpu")[0][names.index(c)]
        return float(1 / (1 + np.exp(-(lg * platt[c]["a"] + platt[c]["b"])))), float(thr[pair]["s97"])
    except Exception:
        return None


def promote_q(fl, extra, leads):
    """Set Q verdict: a pair of the retrained networks that PASSED the rule moves into the main list (only B2:LBBB so far); its older research-only entry is dropped. Nothing changes without Q_status.json."""
    st = _q_status()
    fl, extra = list(fl), list(extra)
    for pair, s in st.items():
        if not (s.get("available") and s.get("decision")):
            continue
        tag, c = pair.split(":")
        src = "B" if tag == "B2" else "A"
        r = _q_prob(leads, pair) if leads is not None else None
        if r is None:
            continue
        p, thr = r
        name = W.EXTRA_NAMES[f"{src}:{c}"]
        fl = [f for f in fl if f["cls"] != f"{src}:{c}"]
        if c == "AF" and src == "B":
            fl = [f for f in fl if f["cls"] != "AF"]
        fl.append(dict(cls=f"{src}:{c}", name=name, state="supported", reason="", p=None, detected=bool(p >= thr), p_internal=p, auroc=s["sim_auroc"], sens=s["sim_sens"], spec=s["sim_spec"], validated=True, positives=s["sim_pos"]))
        extra = [x for x in extra if not (x["src"] == src and x["cls"] == c)]
    return fl, extra


def overall(fl, usable):
    """The colour-coded ECG-PATTERN indicator (never a risk level)."""
    sup = [f for f in fl if f["state"] == "supported" and f["cls"] != "NORM"]
    if not usable:
        return dict(code="retake", colour="#6b7280", label="Photo not clear enough", text=W.RETAKE)
    if not sup:
        return dict(code="unavailable", colour="#6b7280", label="ECG pattern findings: not available",
                    text="No ECG-pattern finding passed our accuracy tests for phone photos, so none is shown. This does not mean the ECG is normal.")
    hit = [f for f in sup if f["detected"]]
    names = ", ".join(f["name"] for f in sup)
    if hit:
        return dict(code="pattern", colour="#c2410c", label="Possible ECG pattern found: medical evaluation advised",
                    text="The research model found: " + "; ".join(f["name"] for f in hit) + ". This is a pattern in the picture, not a diagnosis. Patterns checked: " + names + ".")
    return dict(code="none", colour="#475569", label="No supported pattern found (this does not mean the ECG is normal)",
                text="None of the patterns this tool can check was found: " + names + ". On phone photos these checks miss about 2 to 3 in 10 true patterns. A normal-looking ECG does not exclude heart disease.")


def risk_exploratory(leads, light, page_found, age, usable, age_source="typed"):
    """Exploratory 5-year death estimate (risk pilot 3; research only, did not meet its calibration rule, not validated on photos). Returns dict(state, ...) with state 'shown', 'need_age' or 'blocked'."""
    if not (usable and light == "GREEN" and page_found):
        return dict(state="blocked", reason="shown only for a GREEN light and a straightened photo")
    from . import risk as RK
    no_age = age is None or age == ""
    est = RK.risk3_estimate(leads, None if no_age else age)
    if est is None:
        return dict(state="blocked", reason="the estimate could not be computed for this photo or age (age must be 16 to 90)")
    est.update(state="shown", age_source=("estimated from the ECG, typical error about %d years" % RK.AGE_ERROR_YEARS) if no_age else (age_source or "typed"), text=W.risk_exp_text(est))
    return est


_MI_CAL = {}


def _mi_cal():
    """results/health/MI_photo_calibration_v2.json (second attempt on the fresh set S). Used only if show_percentage is true; {} otherwise or if the file is missing."""
    if "c" not in _MI_CAL:
        try:
            with open(os.path.join(D.ROOT, "results", "health", "MI_photo_calibration_v2.json"), encoding="utf-8") as fh:
                c = json.load(fh)
            _MI_CAL["c"] = c if c.get("show_percentage") else {}
        except Exception:
            _MI_CAL["c"] = {}
    return _MI_CAL["c"]


def mi_photo_calibration(fl):
    """Adds p_cal (fraction) to the heart-attack-pattern row when its score exists and the calibration passed its rules. The row is otherwise unchanged."""
    c = _mi_cal()
    if not c:
        return fl
    for f in fl:
        if f["cls"] == "MI" and f["state"] == "supported" and f.get("p_internal") is not None:
            sc = min(max(float(f["p_internal"]), 1e-6), 1 - 1e-6)
            f["p_cal"] = float(1.0 / (1.0 + np.exp(-(c["a"] * np.log(sc / (1 - sc)) + c["b"]))))
    return fl


def assess(leads, light, reasons, page_found, hr, n_beats, rr_cv, pr_ms, axis_deg, no_output=False, age=None, age_source="typed"):
    usable = (leads is not None) and (not no_output) and light in ("GREEN", "AMBER") and bool(page_found)
    rexp = risk_exploratory(leads, light, page_found, age, usable, age_source)
    params = parameters(light, hr, rr_cv, pr_ms, axis_deg, page_found, reasons, no_output)
    if usable:
        params = apply_qt(params, leads)
    fl, why = findings(leads if usable else None, light, page_found)
    fl = mi_photo_calibration(fl)
    ov = overall(fl, usable)
    extra = extra_findings(leads if usable else None, light, page_found)
    fl, extra = promote_validated(fl, extra)
    fl, extra = promote_q(fl, extra, leads if usable else None)
    nxt = W.NEXT_STEPS["retake"] if ov["code"] == "retake" else W.NEXT_STEPS.get(ov["code"], W.NEXT_STEPS["unavailable"])
    texts = [ov["text"], nxt, W.RISK_UNAVAILABLE, W.DISCLAIMER] + [p["reason"] + " " + p["confidence"] for p in params] + [f["reason"] for f in fl] + [W.EXTRA_NOTE] + [x["name"] for x in extra] + ([rexp["text"]] if rexp.get("state") == "shown" else [])
    bad = [w for t in texts for w in W.check_wording(t)]
    if bad:     # the safety checker caught a bad sentence: fall back to the plain safe text
        ov = dict(code="unavailable", colour="#6b7280", label="ECG pattern findings: not available", text="This tool cannot give a reliable assessment for this photo.")
        nxt = W.NEXT_STEPS["unavailable"]
    return dict(usable=usable, light=light, reasons=reasons or [], page_found=bool(page_found), params=params, findings=fl, overall=ov, extra=extra, extra_note=W.EXTRA_NOTE, next_steps=nxt, risk=W.RISK_UNAVAILABLE,
                disclaimer=W.DISCLAIMER, model_note=why, wording_problems=bad, risk_exp=rexp)
