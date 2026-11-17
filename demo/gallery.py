"""Dataset gallery tab of the demo: instant results on dataset pictures. Reads results/paper_n/gallery_cache.json (built by scripts/tools/build_gallery_cache.py): for all 120 simulated phone photos of set N (made from PTB-XL recordings,
NOT real phone photos) the output of the same code the app runs, next to the true answer from the dataset labels. Every photo is listed; nothing is selected by result. Research prototype. Not a medical device."""
import html
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
CACHE = os.path.join(ROOT, "results", "paper_n", "gallery_cache.json")
PHOTOS = os.path.join(ROOT, "results", "paper_n", "N_sim", "photos")
_D = {}
SHORT = {"MI": "Heart-attack pattern", "STTC": "ST/T-wave change", "ASMI": "Anteroseptal heart attack", "LVH": "Left ventricular hypertrophy", "LAFB": "Left anterior fascicular block",
         "IRBBB": "Incomplete right bundle branch block", "AF": "Atrial fibrillation", "LBBB": "Left bundle branch block", "1dAVb": "First-degree AV block"}


def _e(t):
    return html.escape(str(t), quote=True)


def data():
    if "d" not in _D:
        try:
            _D["d"] = json.load(open(CACHE, encoding="utf-8"))
        except Exception:
            _D["d"] = None
    return _D["d"]


def available():
    return data() is not None


def verdict(truth, det):
    """(text, colour) for one pattern of one case."""
    if det is None:
        return "not shown (light RED)", "#6b7280"
    if truth and det:
        return "HIT: found, and it is there", "#15803d"
    if truth and not det:
        return "MISSED: it is there, not found", "#b42318"
    if not truth and det:
        return "FALSE ALARM: found, but not there", "#b45309"
    return "correct: not found, not there", "#374151"


def choices():
    d = data()
    out = []
    for c in d["cases"]:
        t = [SHORT[k] for k, v in c["truth"].items() if v]
        out.append((f"{c['name']}  |  light {c['light']}  |  true: " + (", ".join(t) if t else "none of the 9 patterns"), c["name"]))
    return out


def default_case():
    d = data()
    for c in d["cases"]:                                   # the first case where the tool is right about a pattern: only to start the page with an example; every case can be chosen
        if c["light"] == "GREEN" and any(c["truth"][k] and c["detected"][k] for k in c["truth"]):
            return c["name"]
    return d["cases"][0]["name"]


def scoreboard_html():
    d = data()
    s, sc = d["summary"], d["scoreboard"]
    rows = []
    for k, v in sc.items():
        rows.append(f"<tr><td><b>{_e(SHORT[k])}</b>{' (research only)' if k not in ('MI', 'STTC') else ' (main list)'}</td><td>{v['true_cases']}</td><td style='color:#15803d;font-weight:600'>{v['hits']}</td>"
                    f"<td style='color:#b42318;font-weight:600'>{v['misses']}</td><td style='color:#b45309;font-weight:600'>{v['false_alarms']}</td><td>{v['correct_negatives']}</td></tr>")
    return ("<div class='hh-light' style='font-size:14px;background:#fff;color:#111;padding:14px;border-radius:8px'>"
            f"<p><b>Scoreboard on all {s['cases']} dataset pictures.</b> The tool got a GREEN or AMBER light on {s['green'] + s['amber']} of them ({s['green']} GREEN, {s['amber']} AMBER); on the other {s['red']} the light was RED and the app shows no findings. "
            "The table counts the pictures with a GREEN or AMBER light. The set was built to contain many diseases, so the shares of false alarms are not the shares in the real world.</p>"
            "<table style='width:100%;border-collapse:collapse;font-size:13px;background:#fff;color:#111' border='1' cellpadding='6'><tr style='background:#f3f4f6'><th>Pattern</th><th>True cases</th><th>Found (hits)</th><th>Missed</th><th>False alarms</th><th>Correct: not found, not there</th></tr>"
            + "".join(rows) + "</table><p style='font-size:12.5px;margin-top:6px'>These are simulated phone photos made from PTB-XL recordings, not real phone photos. The tool saw only the picture; the true answer is the dataset label. "
            "Research-only patterns carry no validation on real phone photos.</p></div>")


def case_html(name):
    d = data()
    c = next(x for x in d["cases"] if x["name"] == name)
    rows = []
    for k, _ in d["patterns"]:
        v, col = verdict(c["truth"][k], c["detected"][k])
        rows.append(f"<tr><td>{_e(SHORT[k])}</td><td>{'yes' if c['truth'][k] else 'no'}</td><td>{'not shown' if c['detected'][k] is None else ('found' if c['detected'][k] else 'not found')}</td>"
                    f"<td style='color:{col};font-weight:600'>{_e(v)}</td></tr>")
    hr = "no usable heart rate" if c["hr_read"] is None else f"{c['hr_read']:.0f} bpm"
    tru = "-" if c["hr_true"] is None else f"{c['hr_true']:.0f} bpm"
    top = ("<div class='hh-light' style='font-size:14px;background:#fff;color:#111;padding:14px;border-radius:8px'>"
           f"<p><b>Case {_e(c['name'])}</b> (a simulated phone photo of PTB-XL recording {c['ecg_id']}). Traffic light: <b>{_e(c['light'])}</b>. Heart rate read from the photo: <b>{_e(hr)}</b>; "
           f"true heart rate from the original signal: <b>{_e(tru)}</b>.</p>"
           "<table style='width:100%;border-collapse:collapse;font-size:13px;background:#fff;color:#111' border='1' cellpadding='6'><tr style='background:#f3f4f6'><th>Pattern</th><th>True answer (dataset label)</th><th>What the tool said</th><th>Verdict</th></tr>"
           + "".join(rows) + "</table></div>")
    return top


def show(name):
    """(photo path, truth-versus-tool html, the heart-health panel html) of one case."""
    d = data()
    c = next(x for x in d["cases"] if x["name"] == name)
    return os.path.join(PHOTOS, name + ".jpg"), case_html(name), c["panel_html"]


def truth_box(name, a):
    """For a dataset picture (file name starting with a set-N page id, e.g. N037_angled.jpg) the true answer next to what the tool said on THIS check; empty for any other picture."""
    d = data()
    if d is None or not name:
        return ""
    base = os.path.splitext(os.path.basename(str(name)))[0]
    case = next((c for c in d["cases"] if c["page"] == base[:4]), None)
    if case is None or not base[:4].startswith("N"):
        return ""
    tool = {k: None for k, _ in d["patterns"]}
    for f in a.get("findings", []):
        if f["cls"] in ("MI", "STTC") and f["state"] == "supported":
            tool[f["cls"]] = bool(f["detected"])
    for x in a.get("extra") or []:
        tool[x["cls"]] = bool(x["detected"])
    rows = []
    for k, _ in d["patterns"]:
        v, col = verdict(case["truth"][k], tool[k])
        rows.append(f"<tr><td>{_e(SHORT[k])}</td><td>{'yes' if case['truth'][k] else 'no'}</td><td>{'not shown' if tool[k] is None else ('found' if tool[k] else 'not found')}</td><td style='color:{col};font-weight:600'>{_e(v)}</td></tr>")
    return ("<div class='hh-light' style='font-size:14px;background:#fff;color:#111;padding:14px;border-radius:8px;margin-bottom:10px;border:2px solid #1d4ed8'>"
            f"<p><b>True answer next to what the tool said ({_e(base)})</b></p>"
            "<table style='width:100%;border-collapse:collapse;font-size:13px;background:#fff;color:#111' border='1' cellpadding='6'><tr style='background:#f3f4f6'><th>Pattern</th><th>True answer</th><th>What the tool said</th><th>Verdict</th></tr>"
            + "".join(rows) + "</table></div>")
