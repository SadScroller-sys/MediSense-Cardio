"""Interactive dashboard pieces for the heart health module (Plotly + HTML). Research prototype. Not a medical device.
A. risk box (risk always 'not available') + colour-coded ECG-pattern indicator; B. zoomable waveform; C. parameter charts with reference ranges; D. findings chart; plus the results panel."""
import html

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from . import data as D
from . import wording as W

BLUE, ORANGE, GRAY, INK = "#2a78d6", "#eb6834", "#8a8984", "#0b0b0b"
GREEN_BAND = "rgba(21,128,61,0.16)"
SHORT = {"hr": "Heart rate", "rr": "RR interval", "pr": "PR interval", "axis": "QRS axis"}
SHORT_F = {"NORM": "Normal-looking", "MI": "Heart attack pattern", "STTC": "ST/T-wave change", "CD": "Conduction disturbance", "HYP": "Hypertrophy", "AF": "Atrial fibrillation", "B:LBBB": "Left bundle branch block (dataset pictures)", "A:LAFB": "Left anterior fascicular block (dataset pictures)", "B:AF": "Atrial fibrillation (dataset pictures)"}


def _e(s):
    return html.escape(str(s))


def risk_box(a):
    ov = a["overall"]
    return (
        "<div class='hh-light' style='display:grid;grid-template-columns:1fr 1fr;gap:12px;color:#111'>"
        "<div style='border:2px solid #6b7280;border-radius:10px;padding:12px;background:#f3f4f6;color:#111'>"
        "<div style='font-size:12px;color:#374151'>A. CARDIAC RISK</div>"
        "<div style='font-size:20px;font-weight:700;color:#374151'>&#9888; Not available</div>"
        f"<div style='font-size:13px;margin-top:6px;color:#111'>{_e(a['risk'])}</div>"
        "<div style='font-size:13px;margin-top:6px;color:#111'><b>What is shown instead:</b> graph D, how likely each ECG pattern is on this ECG.</div></div>"
        f"<div style='border:2px solid {ov['colour']};border-radius:10px;padding:12px;background:#fff;color:#111'>"
        "<div style='font-size:12px;color:#374151'>ECG PATTERN FINDING (not a risk level)</div>"
        f"<div style='font-size:20px;font-weight:700;color:{ov['colour']}'>{_e(ov['label'])}</div>"
        f"<div style='font-size:13px;margin-top:6px;color:#111'>{_e(ov['text'])}</div>"
        "<div style='font-size:12px;margin-top:6px;color:#374151'>Model confidence is not the same as the chance of heart disease: a high model score only says the picture resembles the pattern.</div></div></div>"
        + exploratory_risk_box(a) + mi_percent_box(a))


def mi_percent_box(a):
    """A3. HEART-ATTACK PATTERN percentage (research only): the calibrated chance that this ECG shows the pattern. Shown only when the calibration passed its rules (status file) and the pattern could be checked for this photo."""
    mi = next((f for f in a.get("findings", []) if f["cls"] == "MI" and f["state"] == "supported"), None)
    head = "<div style='font-size:12px;color:#374151'>A3. HEART-ATTACK PATTERN: CHANCE THE ECG SHOWS IT (research only, second calibration attempt)</div>"
    if mi is None or mi.get("p_cal") is None:
        return ("<div class='hh-light' style='margin-top:12px;border:2px dashed #9ca3af;border-radius:10px;padding:12px;background:#f9fafb;color:#111'>" + head
                + "<div style='font-size:14px;margin-top:4px;color:#111'>No percentage for this photo (it needs a GREEN or AMBER straightened photo and a finished calibration).</div></div>")
    p = mi["p_cal"] * 100
    bar = ("<div style='position:relative;height:18px;background:#e5e7eb;border-radius:9px;margin:8px 0 4px'>"
           f"<div style='position:absolute;left:0;width:{p:.1f}%;top:0;bottom:0;background:#eb6834;border-radius:9px;opacity:.9'></div></div>"
           "<div style='display:flex;justify-content:space-between;font-size:11px;color:#374151'><span>0 in 100</span><span>50</span><span>100 in 100</span></div>")
    return ("<div class='hh-light' style='margin-top:12px;border:2px solid #c2410c;border-radius:10px;padding:12px;background:#fff7ed;color:#111'>" + head
            + f"<div style='font-size:20px;font-weight:700;color:#c2410c'>about {p:.0f} in 100</div>" + bar
            + f"<div style='font-size:12.5px;margin-top:8px;color:#111'>{_e(W.mi_percent_text(mi['p_cal']))}</div></div>")


def exploratory_risk_box(a):
    """A2. EXPLORATORY 5-year death estimate (risk pilot 3), a separate research-only box. Shown only for a GREEN straightened photo with an age entered; otherwise a short grey note."""
    r = a.get("risk_exp") or dict(state="blocked", reason="not available")
    head = "<div style='font-size:12px;color:#374151'>A2. EXPLORATORY 5-YEAR ESTIMATE (research only, not validated)</div>"
    if r.get("state") != "shown":
        return ("<div class='hh-light' style='margin-top:12px;border:2px dashed #9ca3af;border-radius:10px;padding:12px;background:#f9fafb;color:#111'>" + head
                + f"<div style='font-size:14px;margin-top:4px;color:#111'>No estimate yet: {_e(r.get('reason', ''))}.</div></div>")
    lo, hi, p = r["low"] * 100, r["high"] * 100, r["p"] * 100
    bar = ("<div style='position:relative;height:22px;background:#e5e7eb;border-radius:11px;margin:10px 0 4px'>"
           f"<div style='position:absolute;left:{lo:.1f}%;width:{max(hi - lo, 1):.1f}%;top:0;bottom:0;background:#fbbf24;border-radius:11px;opacity:.85'></div>"
           f"<div style='position:absolute;left:calc({p:.1f}% - 2px);width:4px;top:-3px;bottom:-3px;background:#92400e;border-radius:2px'></div></div>"
           "<div style='display:flex;justify-content:space-between;font-size:11px;color:#374151'><span>0 in 100</span><span>25</span><span>50</span><span>75</span><span>100 in 100</span></div>")
    return ("<div class='hh-light' style='margin-top:12px;border:2px solid #d97706;border-radius:10px;padding:12px;background:#fffbeb;color:#111'>" + head
            + f"<div style='font-size:20px;font-weight:700;color:#92400e'>about {int(round(lo / 5) * 5)} to {int(round(hi / 5) * 5)} in 100</div>"
            f"<div style='font-size:13px;margin-top:4px;color:#111'>5-year chance of death for people of age {r['age']:.0f} ({_e(r.get('age_source', 'typed'))}) with an ECG like this (middle of the range: {p:.0f} in 100; group: {_e(r['group'])}). "
            f"Average of {r['n_models']} models.</div>" + bar +
            f"<div style='font-size:12.5px;margin-top:8px;color:#111'>{_e(r['text'])}</div></div>")


def waveform(leads):
    """B. All 12 leads on a lead selector, time in seconds, amplitude in mV, zoom and a range slider."""
    fig = go.Figure()
    if leads is None:
        fig.add_annotation(text="No waveform could be read from this photo", showarrow=False)
        fig.update_layout(height=320, xaxis_visible=False, yaxis_visible=False)
        return fig
    names = [L for L in D.LEADS if L in leads and leads[L] is not None]
    for L in names:
        y = np.asarray(leads[L], float) / 1000.0
        t = np.arange(len(y)) / 1000.0
        fig.add_trace(go.Scattergl(x=t, y=y, mode="lines", name=L, line=dict(width=1.1, color=BLUE), visible=(L == "II"), connectgaps=False,
                                   hovertemplate="%{x:.2f} s<br>%{y:.3f} mV<extra>" + L + "</extra>"))
    buttons = [dict(label=L, method="update", args=[{"visible": [n == L for n in names]}, {"title": f"Lead {L} as read by the digitiser"}]) for L in names]
    fig.update_layout(title="Lead II as read by the digitiser (choose a lead; drag to zoom; double-click to reset)", height=360, margin=dict(l=50, r=20, t=70, b=40),
                      updatemenus=[dict(buttons=buttons, active=names.index("II") if "II" in names else 0, direction="down", x=0.0, y=1.22, xanchor="left", yanchor="top")],
                      xaxis=dict(title="Time (seconds)", rangeslider=dict(visible=True, thickness=0.08), showgrid=True, gridcolor="#e6e5e1"),
                      yaxis=dict(title="Amplitude (mV)", showgrid=True, gridcolor="#e6e5e1", zeroline=True), plot_bgcolor="white", font=dict(color=INK))
    return fig


def parameter_chart(a):
    """C. One small chart per measured parameter: the value against its reference range. Unmeasured parameters are listed in the table, not drawn."""
    meas = [p for p in a["params"] if p["value"] is not None and p["ref"]]
    fig = make_subplots(rows=max(len(meas), 1), cols=1, vertical_spacing=0.16, subplot_titles=[f"{SHORT.get(p['key'], p['name'])} ({p['unit']}), reference {p['ref'][0]} to {p['ref'][1]}" for p in meas] or [""])
    if not meas:
        fig.add_annotation(text="No parameter could be measured reliably from this photo", showarrow=False)
        fig.update_layout(height=200, xaxis_visible=False, yaxis_visible=False)
        return fig
    for i, p in enumerate(meas, start=1):
        lo, hi = p["ref"]
        span = hi - lo
        xmin, xmax = min(lo - span * 0.6, p["value"] - span * 0.2), max(hi + span * 0.6, p["value"] + span * 0.2)
        fig.add_shape(type="rect", x0=lo, x1=hi, y0=0, y1=1, fillcolor=GREEN_BAND, line=dict(width=0), row=i, col=1)
        inside = lo <= p["value"] <= hi
        fig.add_trace(go.Scatter(x=[p["value"]], y=[0.5], mode="markers+text", marker=dict(size=16, color=BLUE if inside else ORANGE, line=dict(width=2, color="white"), symbol="diamond"),
                                 text=[f"{p['value']:.0f}" + (" (outside the reference range)" if not inside else "")], textposition="top center", showlegend=False,
                                 hovertemplate=f"{p['name']}: %{{x:.0f}} {p['unit']}<extra></extra>"), row=i, col=1)
        fig.update_xaxes(range=[xmin, xmax], row=i, col=1, showgrid=False)
        fig.update_yaxes(visible=False, range=[0, 1], row=i, col=1)
    fig.update_annotations(font_size=12)
    fig.update_layout(height=140 * len(meas) + 60, margin=dict(l=20, r=20, t=50, b=20), plot_bgcolor="white", font=dict(color=INK))
    return fig


def findings_chart(a):
    """D. How likely is each supported ECG PATTERN (not cardiac risk). Bands: unlikely, possible, likely. Percentages only when the finding's calibration passed our fresh-photo test;
    otherwise the bar is a model score without a number. Abnormal patterns that are found are orange."""
    sup = [f for f in a["findings"] if f["state"] == "supported"]
    fig = go.Figure()
    if not sup:
        fig.add_annotation(text="No ECG-pattern finding is available for this photo", showarrow=False)
        fig.update_layout(height=200, xaxis_visible=False, yaxis_visible=False)
        return fig
    pct = all(f["p"] is not None for f in sup)
    names = [f"{SHORT_F.get(f['cls'], f['name'][:40])}: " + ("FOUND" if f["detected"] else "not found") for f in sup]
    vals = [f["p_internal"] for f in sup]
    cols = [(ORANGE if (f["detected"] and f["cls"] != "NORM") else (BLUE if f["cls"] != "NORM" else GRAY)) for f in sup]
    for x0, x1, c, lab in ((0, 0.3, "rgba(120,120,120,0.10)", "unlikely"), (0.3, 0.7, "rgba(240,160,0,0.14)", "possible"), (0.7, 1.0, "rgba(235,104,52,0.16)", "likely")):
        fig.add_vrect(x0=x0, x1=x1, fillcolor=c, line_width=0, annotation_text=lab, annotation_position="top", annotation_font_size=10)
    fig.add_trace(go.Bar(x=vals, y=names, orientation="h", marker_color=cols, text=[f"{v * 100:.0f}%" if pct else "" for v in vals], textposition="outside", cliponaxis=False,
                         hovertemplate="%{y}<extra></extra>"))
    ttl = "How likely is each ECG pattern (model estimate, not cardiac risk)" if pct else "ECG-pattern model score (no percentage: not validated for photos; not cardiac risk)"
    fig.update_layout(title=dict(text=ttl, font=dict(size=13)), height=62 * len(sup) + 130, margin=dict(l=20, r=40, t=70, b=40), xaxis=dict(range=[0, 1.08], title="Estimated probability that the ECG shows the pattern" if pct else "Model score (not a probability)"),
                      plot_bgcolor="white", font=dict(color=INK))
    return fig


def _blank(text, h=260):
    fig = go.Figure()
    fig.add_annotation(text=text, showarrow=False, font=dict(size=13, color=INK))
    fig.update_layout(height=h, xaxis_visible=False, yaxis_visible=False, plot_bgcolor="white", margin=dict(l=10, r=10, t=40, b=10))
    return fig


def hr_gauge(a):
    """E. Heart rate gauge (display only). The number is the same one as in Panel C and is shown only when the traffic light lets it through."""
    p = next((q for q in a["params"] if q["key"] == "hr"), None)
    if p is None or p["value"] is None:
        return _blank("No usable heart rate: the read looks unreliable, so no number is shown")
    v = float(p["value"])
    lo, hi = p["ref"]
    inside = lo <= v <= hi
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=v, number=dict(suffix=" bpm", font=dict(size=34, color=INK)),
        title=dict(text="Heart rate<br><span style='font-size:11px'>shaded: resting adult range 60 to 100 bpm</span>", font=dict(size=13)),
        gauge=dict(axis=dict(range=[30, 200], tickwidth=1), bar=dict(color=BLUE if inside else ORANGE, thickness=0.3),
                   steps=[dict(range=[30, lo], color="rgba(120,120,120,0.12)"), dict(range=[lo, hi], color=GREEN_BAND), dict(range=[hi, 200], color="rgba(120,120,120,0.12)")])))
    fig.update_layout(height=260, margin=dict(l=20, r=20, t=60, b=10), font=dict(color=INK), paper_bgcolor="white")
    return fig


def pattern_donut(a):
    """F. Donut for the strongest supported ECG PATTERN. It is not heart risk (risk stays 'not available'). A percentage is drawn only when that pattern's calibration passed our
    photo test (f['p'] is not None); otherwise the donut is grey and shows the band (unlikely, possible, likely) without a number."""
    sup = [f for f in a["findings"] if f["state"] == "supported" and f["cls"] != "NORM" and f.get("p_internal") is not None]
    if not sup:
        return _blank("No ECG-pattern finding is available for this photo")
    f = max(sup, key=lambda q: q["p_internal"])
    name = SHORT_F.get(f["cls"], f["name"][:40])
    pi = float(f["p_internal"])
    band = "unlikely" if pi < 0.3 else ("possible" if pi < 0.7 else "likely")
    if f.get("p") is not None or f.get("p_cal") is not None:
        pc = float(f["p"]) if f.get("p") is not None else float(f["p_cal"])
        fig = go.Figure(go.Pie(values=[pc, 1 - pc], hole=0.72, sort=False, direction="clockwise", marker=dict(colors=[ORANGE if f["detected"] else BLUE, "#e6e5e1"]), textinfo="none",
                               hovertemplate="%{label}: %{value:.0%}<extra></extra>", labels=["chance the picture shows this pattern", "rest"]))
        centre, sub = f"{pc * 100:.0f}%", "estimated chance this ECG shows the pattern"
    else:                                              # B: the model SCORE on a ring (amber part), clearly not a chance
        fig = go.Figure(go.Pie(values=[max(pi, 0.001), max(1 - pi, 0.001)], hole=0.72, sort=False, direction="clockwise", marker=dict(colors=["#f59e0b", "#e6e5e1"]), textinfo="none", hoverinfo="skip"))
        centre, sub = band, f"model score {pi * 100:.0f} in 100: a score, not a chance"
    if f.get("sens") is not None and f.get("spec") is not None:       # A: the measured detection rates on photos
        fig.add_annotation(x=0.5, y=-0.02, showarrow=False, font=dict(size=11, color="#374151"),
                           text=f"On photos it found {f['sens'] * 100:.0f} in 100 true patterns and<br>wrongly flagged {(1 - f['spec']) * 100:.0f} in 100 photos without the pattern")
    fig.add_annotation(text=f"<b>{_e(centre)}</b>", x=0.5, y=0.54, showarrow=False, font=dict(size=30, color=INK))
    fig.add_annotation(text=_e(sub), x=0.5, y=0.40, showarrow=False, font=dict(size=11, color="#374151"))
    fig.update_layout(title=dict(text=f"{_e(name)}<br><span style='font-size:11px'>strongest ECG pattern; not heart risk</span>", font=dict(size=13)), height=300, showlegend=False, margin=dict(l=20, r=20, t=60, b=50), paper_bgcolor="white", font=dict(color=INK))
    return fig


def _p90():
    """The limits the traffic light itself uses (safeguard/model.json). Returned as {} if the file is not found."""
    import json
    import os
    try:
        here = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(here, "..", "..", "safeguard", "model.json"), encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {}


def reliability_bars(r, a):
    """G. Is the waveform reliable? One bar per check the traffic light makes, as a share of the limit it uses: inside the green zone (up to 100%) is fine, beyond it the light is warned.
    Display of numbers already computed in the safeguard; nothing is trained or tuned here."""
    feat = (r or {}).get("features")
    m = _p90()
    lim = m.get("reason_p90", {})
    if not feat or not lim:
        return _blank("No reliability checks could be computed for this photo")
    rows = []
    for key, label in (("rr_cv", "Beat spacing is regular"), ("einthoven", "Leads I, II, III agree"), ("goldberger", "aVR, aVL, aVF agree"), ("xlead_count_absdiff", "All leads count the same beats")):
        v = feat.get(key)
        if v is not None and np.isfinite(v) and lim.get(key):
            rows.append((label, float(v) / lim[key]))
    nu = feat.get("n_unreadable_leads")
    if nu is not None and np.isfinite(nu):
        rows.append((f"Leads readable ({12 - int(nu)} of 12)", 0.0 if int(nu) == 0 else 1.5))
    sp = (r or {}).get("detector_spread")
    if sp is not None and np.isfinite(sp):
        rows.append(("Beat detectors agree", float(sp) / float(m.get("detector_spread_note_bpm", 15.0))))
    if not rows:
        return _blank("No reliability checks could be computed for this photo")
    labels = [x[0] for x in rows][::-1]
    vals = [min(x[1], 2.0) for x in rows][::-1]
    cols = [BLUE if v <= 1.0 else ORANGE for v in vals]
    fig = go.Figure(go.Bar(x=vals, y=labels, orientation="h", marker_color=cols, text=[("OK" if v <= 1.0 else "over the limit") for v in vals], textposition="outside", cliponaxis=False,
                           hovertemplate="%{y}: %{x:.0%} of the limit<extra></extra>"))
    fig.add_vrect(x0=0, x1=1.0, fillcolor=GREEN_BAND, line_width=0)
    fig.add_vline(x=1.0, line_dash="dash", line_color=GRAY, annotation_text="limit", annotation_position="top")
    light = a.get("light", "")
    fig.update_layout(title=dict(text=f"Is the waveform reliable? Traffic light: {light} (green is not a guarantee)", font=dict(size=13)), height=60 * len(rows) + 120, margin=dict(l=20, r=80, t=70, b=40),
                      xaxis=dict(range=[0, 2.3], tickvals=[0, 0.5, 1.0, 1.5, 2.0], tickformat=".0%", title="Share of the limit used by the traffic light (lower is better)"), plot_bgcolor="white", font=dict(color=INK))
    return fig


def risk_rate_chart(a):
    """I. Heart risk rate (research only): a dial for the exploratory 5-year range of box A2. The needle is the middle value; the amber band is the range shown; the grey bands are the rough groups
    (lower under 5 in 100, middle 5 to 15, higher 15 or more). It exists only when box A2 has an estimate (GREEN straightened photo); it is not a validated risk and not a prediction for the person."""
    r = a.get("risk_exp") or {}
    if r.get("state") != "shown":
        return _blank("No heart risk rate yet: " + str(r.get("reason", "not available")), h=300)
    p, lo, hi = r["p"] * 100, r["low"] * 100, r["high"] * 100
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=p, number=dict(suffix=" in 100", valueformat=".0f", font=dict(size=30, color=INK)),
        title=dict(text="Heart risk rate (research only)<br><span style='font-size:11px'>5-year, our research data; amber = range; not validated</span>", font=dict(size=13)),
        gauge=dict(axis=dict(range=[0, 100], tickvals=[0, 5, 15, 25, 50, 75, 100], tickwidth=1), bar=dict(color="#92400e", thickness=0.18),
                   steps=[dict(range=[0, 5], color="rgba(21,128,61,0.18)"), dict(range=[5, 15], color="rgba(240,160,0,0.18)"), dict(range=[15, 100], color="rgba(235,104,52,0.16)"),
                          dict(range=[lo, hi], color="rgba(245,158,11,0.75)")])))
    fig.add_annotation(x=0.5, y=-0.12, showarrow=False, text=f"about {int(round(lo / 5) * 5)} to {int(round(hi / 5) * 5)} in 100 (rough group: {_e(r['group'])})", font=dict(size=12, color="#374151"))
    fig.update_layout(height=300, margin=dict(l=20, r=20, t=90, b=40), font=dict(color=INK), paper_bgcolor="white")
    return fig


# ------------------------------------------------------------------ H. which part of the heart (chamber view): display only; groups the patterns already found by where they sit in the heart
CHAMBER = {"AF": ["RA", "LA"], "MI": ["LV"], "ASMI": ["LV"], "STTC": ["LV", "RV"], "HYP": ["LV"], "LVH": ["LV"], "LBBB": ["LV"], "LAFB": ["LV"], "IRBBB": ["RV"], "1dAVb": ["AV"], "CD": ["LV", "RV"]}
REGION_NAME = {"RA": "Right atrium", "LA": "Left atrium", "RV": "Right ventricle", "LV": "Left ventricle", "AV": "AV junction"}
LINKED = {  # what a pattern is linked to, in plain words (never a diagnosis)
    "AF": "an irregular rhythm of the upper chambers (atrial fibrillation or flutter)",
    "MI": "a pattern linked to a heart attack, in the muscle of the left ventricle",
    "ASMI": "a pattern linked to a heart attack at the front wall and septum of the left ventricle",
    "STTC": "a change in how the ventricles recover after each beat (ST/T-wave change)",
    "HYP": "a thickened ventricle wall (hypertrophy pattern)", "LVH": "a thickened wall of the left ventricle",
    "LBBB": "a delay in the electrical path to the left ventricle (left bundle branch block pattern)",
    "LAFB": "a delay in one branch of the left ventricle's electrical path (fascicular block pattern)",
    "IRBBB": "a mild delay in the electrical path to the right ventricle (incomplete right bundle branch block pattern)",
    "1dAVb": "a slow signal between the upper and lower chambers (first-degree AV block pattern)",
    "CD": "a delay in the electrical path of the ventricles (conduction pattern)"}


def chamber_states(a):
    """{region: dict(state 'found'|'clear'|'unchecked', patterns [(key, name)])}. A pattern counts as checked only if the app could supply a result for it; the normal-looking pattern is not used."""
    items = []
    for f in a.get("findings", []):
        if f["state"] == "supported" and f["cls"] != "NORM":
            items.append((f["cls"].split(":")[-1], f["name"], bool(f["detected"])))
    for x in a.get("extra") or []:
        items.append((x["cls"], x["name"], bool(x["detected"])))
    out = {r: dict(state="unchecked", patterns=[]) for r in REGION_NAME}
    for key, name, det in items:
        for r in CHAMBER.get(key, []):
            if det:
                out[r]["state"] = "found"
                if (key, name) not in out[r]["patterns"]:
                    out[r]["patterns"].append((key, name))
            elif out[r]["state"] == "unchecked":
                out[r]["state"] = "clear"
    return out


def heart_diagram(a):
    """H. A simple heart drawing: atria on top, ventricles below, the AV junction in the middle. Orange = a pattern was found there; blue = checked, none found; grey = not checked. Not a diagnosis."""
    st = chamber_states(a)
    col = {"found": ORANGE, "clear": "#9cc3f0", "unchecked": "#dcdcd8"}
    boxes = {"RA": (0.03, 0.55, 0.45, 0.97), "LA": (0.52, 0.55, 0.97, 0.97), "RV": (0.03, 0.03, 0.40, 0.45), "LV": (0.44, 0.03, 0.97, 0.45)}
    fig = go.Figure()
    for r, (x0, y0, x1, y1) in boxes.items():
        fig.add_shape(type="rect", x0=x0, y0=y0, x1=x1, y1=y1, fillcolor=col[st[r]["state"]], line=dict(color="white", width=3), layer="below")
        n = len(st[r]["patterns"])
        sub = {"found": f"{n} pattern{'s' if n != 1 else ''} found", "clear": "checked, none found", "unchecked": "not checked"}[st[r]["state"]]
        fig.add_annotation(x=(x0 + x1) / 2, y=(y0 + y1) / 2, text=f"<b>{REGION_NAME[r]}</b><br><span style='font-size:11px'>{sub}</span>", showarrow=False, font=dict(size=13, color=INK))
    fig.add_shape(type="circle", x0=0.43, y0=0.455, x1=0.57, y1=0.545, fillcolor=col[st["AV"]["state"]], line=dict(color="white", width=2))
    fig.add_annotation(x=0.5, y=0.5, text="AV", showarrow=False, font=dict(size=11, color=INK))
    fig.add_annotation(x=0.5, y=1.07, text="Atria (upper chambers)", showarrow=False, font=dict(size=11, color="#374151"))
    fig.add_annotation(x=0.5, y=-0.07, text="Ventricles (lower chambers)", showarrow=False, font=dict(size=11, color="#374151"))
    fig.update_layout(title=dict(text="Where the patterns found sit in the heart (not a diagnosis)", font=dict(size=13)), height=340, margin=dict(l=10, r=10, t=60, b=40), plot_bgcolor="white", paper_bgcolor="white",
                      xaxis=dict(visible=False, range=[0, 1]), yaxis=dict(visible=False, range=[-0.1, 1.12]))
    return fig


def chamber_html(a):
    """The simplified risk wording (same research-only range as box A2) and the conditions each pattern found is linked to, grouped by chamber."""
    r = a.get("risk_exp") or {}
    if r.get("state") == "shown":
        lo, hi = int(round(r["low"] * 100 / 5.0) * 5), int(round(r["high"] * 100 / 5.0) * 5)
        risk = (f"<b>Simple view:</b> people of age {r['age']:.0f} with an ECG like this fall in our rough <b>{_e(r['group'])}</b> group. In our research data about <b>{lo} to {hi} in 100</b> of them died within 5 years. "
                "This is one research-only range for the whole ECG, not a separate number for the atria or the ventricles, and not a prediction for you.")
    else:
        risk = f"<b>Simple view:</b> no estimate yet ({_e(r.get('reason', 'not available'))})."
    st = chamber_states(a)
    rows = []
    for grp, regs in (("Atria", ["RA", "LA"]), ("Between atria and ventricles", ["AV"]), ("Ventricles", ["RV", "LV"])):
        found = {}
        for rg in regs:
            for key, name in st[rg]["patterns"]:
                found[key] = name
        if found:
            for key, name in found.items():
                rows.append(f"<tr><td><b>{_e(grp)}</b></td><td>{_e(name)}</td><td>linked to {_e(LINKED.get(key, 'a conduction or rhythm change'))}</td></tr>")
        else:
            any_checked = any(st[rg]["state"] == "clear" for rg in regs)
            rows.append(f"<tr><td><b>{_e(grp)}</b></td><td colspan='2' style='color:#374151'>{'checked: no pattern found' if any_checked else 'not checked for this photo'}</td></tr>")
    table = ("<table style='width:100%;border-collapse:collapse;font-size:13px;background:#fff;color:#111;margin-top:8px' border='1' cellpadding='6'><tr style='background:#f3f4f6'><th>Part of the heart</th><th>Pattern found</th><th>What it is linked to</th></tr>"
             + "".join(rows) + "</table>")
    return ("<div class='hh-light' style='font-size:14px;background:#fff;color:#111;padding:12px;border-radius:8px'>" + f"<div style='margin-bottom:6px'>{risk}</div>" + table
            + "<div style='font-size:12px;color:#374151;margin-top:8px'>These are patterns in the picture, not diagnoses. Only patterns the tool could check for this photo are listed; a pattern that is not listed was not found or not checked. Show the ECG to a doctor.</div></div>")


def parameter_table(a):
    rows = []
    for p in a["params"]:
        v = f"{p['value']:.0f} {p['unit']}" if p["value"] is not None else "-"
        if p["value"] is not None and p["ref"]:
            if p["value"] < p["ref"][0]:
                v += " (below range)"
            elif p["value"] > p["ref"][1]:
                v += " (above range)"
        ref = f"{p['ref'][0]} to {p['ref'][1]} {p['unit']}" if p["ref"] else "-"
        why = p["reason"] if p["status"] != "Measured" and p["status"] != "Measured, not sure" else p["confidence"]
        col = {"Measured": "#15803d", "Measured, not sure": "#b45309"}.get(p["status"], "#6b7280")
        rows.append(f"<tr><td><b>{_e(p['name'])}</b></td><td>{_e(v)}</td><td>{_e(ref)}</td><td style='color:{col};font-weight:600'>{_e(p['status'])}</td><td>{_e(why)}</td></tr>")
    return ("<table style='width:100%;border-collapse:collapse;font-size:13px;background:#fff;color:#111' border='1' cellpadding='6'><tr style='background:#f3f4f6'><th>Parameter</th><th>Value</th>"
            "<th>Reference range</th><th>Status</th><th>Confidence or reason</th></tr>" + "".join(rows) + "</table>"
            "<div style='font-size:12px;color:#374151;margin-top:4px'>Reference ranges are general adult resting ranges for orientation, not a judgement of this person.</div>")


def findings_table(a):
    rows = []
    for f in a["findings"]:
        if f["state"] == "supported":
            st = "Pattern found" if f["detected"] else "Not found"
            col = "#c2410c" if (f["detected"] and f["cls"] != "NORM") else "#374151"
            parts = []
            if f.get("p") is not None:
                parts.append(f"estimated probability {f['p'] * 100:.0f}% (calibrated on photos)")
            if f.get("validated"):
                parts.append(f"validated on dataset pictures (simulated phone photos; {f['positives']} pictures with the pattern): found {f['sens'] * 100:.0f} in 100 true patterns and wrongly flagged {(1 - f['spec']) * 100:.0f} in 100 pictures without it; not validated on real phone photos; no percentage is shown")
            elif "sens" in f:
                parts.append(f"in our phone-photo tests this check found {f['sens'] * 100:.0f} in 100 true patterns and wrongly flagged {(1 - f['spec']) * 100:.0f} in 100 photos without the pattern")
            if f.get("p_cal") is not None:
                parts.append(f"about {f['p_cal'] * 100:.0f} in 100 (the chance this ECG shows the pattern, not of a heart attack; calibrated on simulated photos, second attempt; not validated on real phone photos)")
            if f.get("p") is None and not f.get("validated") and f.get("p_cal") is None:
                parts.append("no percentage is shown (not validated for photos)")
            extra = "; ".join(parts)
        else:
            st, col, extra = "Not available", "#6b7280", f["reason"]
        rows.append(f"<tr><td>{_e(f['name'])}</td><td style='color:{col};font-weight:600'>{_e(st)}</td><td>{_e(extra)}</td></tr>")
    return ("<table style='width:100%;border-collapse:collapse;font-size:13px;background:#fff;color:#111' border='1' cellpadding='6'><tr style='background:#f3f4f6'><th>ECG pattern</th><th>Result</th><th>Note</th></tr>"
            + "".join(rows) + "</table>")


def _extra_note(x):
    if x.get("sens") is not None and x.get("spec") is not None:
        return ("on clean drawn pages (%d pages with this pattern) it found %d in 100 true patterns and wrongly flagged %d in 100 pages without it; not tested on phone photos"
                % (x["positives"], round(100 * x["sens"]), round(100 * (1 - x["spec"]))))
    return "passed on clean drawn pages (AUROC %.2f, %d positive pages); not tested on phone photos" % (x["auroc"], x["positives"])


def _extra_note_full(x):
    t = _extra_note(x)
    if x.get("sim_sens") is not None:
        t = t.replace("; not tested on phone photos", "")
        t += ("; on 120 simulated photos it found %d in 100 and wrongly flagged %d in 100%s; not tested on real phone photos"
              % (round(100 * x["sim_sens"]), round(100 * (1 - x["sim_spec"])), "" if x.get("sim_ok") else " (it did not meet our rule there)"))
    return t


def extra_table(a):
    """Research-only extra patterns (networks A and B): clearly separated, no percentage, never part of the indicator."""
    ex = a.get("extra") or []
    if not ex:
        return ""
    rows = []
    for x in ex:
        st, col = ("Possible pattern", "#c2410c") if x["detected"] else ("Not found", "#374151")
        rows.append(f"<tr><td>{_e(x['name'])}</td><td style='color:{col};font-weight:600'>{_e(st)}</td><td>{_e(_extra_note_full(x))}</td></tr>")
    return ("<details style='margin-top:10px;padding:8px;border:1px dashed #9ca3af;border-radius:6px'><summary style='cursor:pointer'><b>Extra patterns (research only): " + str(len(ex)) + " checked, false alarms still happen. Click to open.</b></summary>"
            "<table style='width:100%;border-collapse:collapse;font-size:13px;background:#fff;color:#111;margin-top:6px' border='1' cellpadding='6'><tr style='background:#f3f4f6'><th>Pattern</th><th>Result</th><th>Note</th></tr>"
            + "".join(rows) + f"</table><div style='font-size:12.5px;color:#374151;margin-top:4px'>{_e(a.get('extra_note', ''))}</div></details>")


def results_panel(a):
    """The guide's results list, in order, as one HTML block (items 1 to 8)."""
    lightc = {"GREEN": "#15803d", "AMBER": "#b45309", "RED": "#b91c1c"}.get(a["light"], "#6b7280")
    reasons = "; ".join(a["reasons"]) if a["reasons"] else "no reason to warn"
    ov = a["overall"]
    det = [f["name"] for f in a["findings"] if f["state"] == "supported" and f["detected"] and f["cls"] != "NORM"]
    minor = " Minor notes do not change the light; they are worth a look at the waveform chart." if "minor note" in reasons else ""
    exd = [x["name"] for x in (a.get("extra") or []) if x["detected"]]
    extra_line = (" Research-only extra patterns flagged: " + "; ".join(exd) + ". About 3 to 5 in 10 of our simulated phone photos without any of these patterns also got a flag, so this is a weak hint to show a doctor, not a validated finding.") if exd else ""
    parts = [
        f"<h4>1. ECG image quality</h4><p><b style='color:{lightc}'>{_e(a['light'])}</b>; page found and straightened: {'yes' if a['page_found'] else 'no'}. Reasons: {_e(reasons)}.{_e(minor)}</p>",
        "<h4>2. Extracted ECG waveform</h4><p>See the waveform chart (time in seconds, amplitude in mV; choose a lead, drag to zoom).</p>",
        "<h4>3. Measured ECG parameters</h4>" + parameter_table(a),
        "<h4>4. Detected abnormalities, if any</h4><p>" + (_e("; ".join(det)) if det else "None among the supported patterns (or none available for this photo).") + (_e(" Research-only hints are listed below the table.") if a.get("extra") else "") + "</p>" + findings_table(a) + extra_table(a),
        f"<h4>5. Heart health assessment</h4><p><b style='color:{ov['colour']}'>{_e(ov['label'])}</b>: {_e(ov['text'] + extra_line)}</p>",
        f"<h4>6. Risk category and supporting evidence</h4><p>{_e(a['risk'])}</p>"
        + (f"<p><b>Exploratory estimate (research only):</b> {_e(a['risk_exp']['text'])}</p>" if (a.get('risk_exp') or {}).get('state') == 'shown' else ""),
        "<h4>7. Confidence and limitations</h4><ul><li>Each measurement above carries the error we measured for its method; the traffic light is the per-photo check.</li>"
        "<li>The findings model was trained on public hospital ECGs and tested on our drawn pages and phone photos; findings that did not pass the pre-set tests are not shown.</li>"
        "<li>A 'not found' result misses some patterns: in our phone-photo tests the checks found about 79 in 100 infarction patterns and 72 in 100 ST/T patterns, and wrongly flagged 16 to 20 in 100 photos without the pattern.</li><li>Conduction patterns in general are not shown for real photos: they were found on photos of a screen but not on our printed-paper photos. Two exceptions passed our rules on fresh dataset pictures (drawn pages and simulated phone photos): left bundle branch block (found about 69 in 100 true patterns on simulated photos, 8 in 100 wrongly flagged) and atrial fibrillation (found about 75 in 100, 9 in 100 wrongly flagged; it passed on its second test). Neither is validated on real phone photos. The other conduction-type patterns (fascicular block, AV block) stay in the research-only block.</li><li>Model confidence is not heart risk.</li><li>Printed paper from one other phone was tested on very few positive photos (5 to 7 per pattern); other phones are not yet shown to work.</li></ul>",
        f"<h4>8. Recommended next steps</h4><p>{_e(a['next_steps'])}</p>",
        f"<div style='margin-top:10px;padding:8px;border:1px solid #d1d5db;border-radius:6px;font-size:12.5px'>{_e(a['disclaimer'])}</div>"]
    return "<div class='hh-light' style='font-size:14px;background:#fff;color:#111;padding:14px;border-radius:8px'>" + "".join(parts) + "</div>"
