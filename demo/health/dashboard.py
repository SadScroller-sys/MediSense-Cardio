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
    """C. Measured parameters as VERTICAL bars: one small bar chart per measured parameter, the value against its reference range (green band). Unmeasured parameters are listed in the table, not drawn."""
    meas = [p for p in a["params"] if p["value"] is not None and p["ref"]]
    fig = make_subplots(rows=1, cols=max(len(meas), 1), horizontal_spacing=0.10, subplot_titles=[f"{SHORT.get(p['key'], p['name'])} ({p['unit']})<br>reference {p['ref'][0]} to {p['ref'][1]}" for p in meas] or [""])
    if not meas:
        fig.add_annotation(text="No parameter could be measured reliably from this photo", showarrow=False)
        fig.update_layout(height=260, xaxis_visible=False, yaxis_visible=False)
        return fig
    for i, p in enumerate(meas, start=1):
        lo, hi = p["ref"]
        span = hi - lo
        v = float(p["value"])
        ymin, ymax = min(0.0, lo - span * 0.3, v - span * 0.2), max(hi + span * 0.6, v + span * 0.25)
        fig.add_hrect(y0=lo, y1=hi, fillcolor=GREEN_BAND, line_width=0, layer="below", row=1, col=i)
        inside = lo <= v <= hi
        fig.add_trace(go.Bar(x=[SHORT.get(p["key"], p["name"])], y=[v], marker_color=BLUE if inside else ORANGE, text=[f"{v:.0f}" + ("" if inside else "<br>outside range")], textposition="outside",
                             cliponaxis=False, showlegend=False, width=0.5, hovertemplate=f"{p['name']}: %{{y:.0f}} {p['unit']}<extra></extra>"), row=1, col=i)
        fig.update_yaxes(range=[ymin, ymax], row=1, col=i, gridcolor="#e6e5e1")
        fig.update_xaxes(showticklabels=False, row=1, col=i)
    fig.update_annotations(font_size=12)
    fig.update_layout(height=380, margin=dict(l=50, r=20, t=80, b=30), plot_bgcolor="white", font=dict(color=INK))
    return fig


def findings_chart(a):
    """D. Supported findings as VERTICAL bars: how likely is each supported ECG PATTERN (not cardiac risk). Bands: unlikely, possible, likely. Percentages only when the finding's calibration passed our
    fresh-photo test; otherwise the bar is a model score without a number. Abnormal patterns that are found are orange."""
    sup = [f for f in a["findings"] if f["state"] == "supported"]
    fig = go.Figure()
    if not sup:
        fig.add_annotation(text="No ECG-pattern finding is available for this photo", showarrow=False)
        fig.update_layout(height=260, xaxis_visible=False, yaxis_visible=False)
        return fig
    pct = all(f["p"] is not None for f in sup)
    names = [f"{SHORT_F.get(f['cls'], f['name'][:40])}<br>" + ("FOUND" if f["detected"] else "not found") for f in sup]
    vals = [f["p_internal"] for f in sup]
    cols = [(ORANGE if (f["detected"] and f["cls"] != "NORM") else (BLUE if f["cls"] != "NORM" else GRAY)) for f in sup]
    for y0, y1, c, lab in ((0, 0.3, "rgba(120,120,120,0.10)", "unlikely"), (0.3, 0.7, "rgba(240,160,0,0.14)", "possible"), (0.7, 1.0, "rgba(235,104,52,0.16)", "likely")):
        fig.add_hrect(y0=y0, y1=y1, fillcolor=c, line_width=0, annotation_text=lab, annotation_position="top right", annotation_font_size=10)
    fig.add_trace(go.Bar(x=names, y=vals, marker_color=cols, text=[f"{v * 100:.0f}%" if pct else "" for v in vals], textposition="outside", cliponaxis=False,
                         hovertemplate="%{x}<extra></extra>"))
    ttl = "How likely is each ECG pattern (model estimate, not cardiac risk)" if pct else "ECG-pattern model score (no percentage: not validated for photos; not cardiac risk)"
    fig.update_layout(title=dict(text=ttl, font=dict(size=13)), height=420, margin=dict(l=60, r=30, t=70, b=90), yaxis=dict(range=[0, 1.12], title="Estimated probability that the ECG shows the pattern" if pct else "Model score (not a probability)",
                                                                                                                           gridcolor="#e6e5e1"), xaxis=dict(tickfont=dict(size=11)), plot_bgcolor="white", font=dict(color=INK), bargap=0.35)
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
                           text=f"On {f.get('rates_note') or 'photos'} it found {f['sens'] * 100:.0f} in 100 true patterns and<br>wrongly flagged {(1 - f['spec']) * 100:.0f} in 100 photos without the pattern")
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
    """G. Is the waveform reliable? VERTICAL bars, one per check the traffic light makes, as a share of the limit it uses: inside the green zone (up to 100%) is fine, beyond it the light is warned.
    Display of numbers already computed in the safeguard; nothing is trained or tuned here."""
    feat = (r or {}).get("features")
    m = _p90()
    lim = m.get("reason_p90", {})
    if not feat or not lim:
        return _blank("No reliability checks could be computed for this photo")
    rows = []
    for key, label in (("rr_cv", "Beat spacing<br>is regular"), ("einthoven", "Leads I, II, III<br>agree"), ("goldberger", "aVR, aVL, aVF<br>agree"), ("xlead_count_absdiff", "All leads count<br>the same beats")):
        v = feat.get(key)
        if v is not None and np.isfinite(v) and lim.get(key):
            rows.append((label, float(v) / lim[key]))
    nu = feat.get("n_unreadable_leads")
    if nu is not None and np.isfinite(nu):
        rows.append((f"Leads readable<br>({12 - int(nu)} of 12)", 0.0 if int(nu) == 0 else 1.5))
    sp = (r or {}).get("detector_spread")
    if sp is not None and np.isfinite(sp):
        rows.append(("Beat detectors<br>agree", float(sp) / float(m.get("detector_spread_note_bpm", 15.0))))
    if not rows:
        return _blank("No reliability checks could be computed for this photo")
    labels = [x[0] for x in rows]
    vals = [min(x[1], 2.0) for x in rows]
    cols = [BLUE if v <= 1.0 else ORANGE for v in vals]
    fig = go.Figure(go.Bar(x=labels, y=vals, marker_color=cols, text=[("OK" if v <= 1.0 else "over the limit") for v in vals], textposition="outside", cliponaxis=False,
                           hovertemplate="%{x}: %{y:.0%} of the limit<extra></extra>"))
    fig.add_hrect(y0=0, y1=1.0, fillcolor=GREEN_BAND, line_width=0, layer="below")
    fig.add_hline(y=1.0, line_dash="dash", line_color=GRAY, annotation_text="limit", annotation_position="top right")
    light = a.get("light", "")
    fig.update_layout(title=dict(text=f"Is the waveform reliable? Traffic light: {light} (green is not a guarantee)", font=dict(size=13)), height=420, margin=dict(l=60, r=30, t=70, b=90),
                      yaxis=dict(range=[0, 2.3], tickvals=[0, 0.5, 1.0, 1.5, 2.0], tickformat=".0%", title="Share of the limit used by the traffic light (lower is better)", gridcolor="#e6e5e1"),
                      plot_bgcolor="white", font=dict(color=INK), bargap=0.35)
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


def risk_rate_bars(a):
    """J. Heart risk rate as VERTICAL bars (research only): low end of the range, middle value, high end of the range, and for comparison the average 5-year death rate in our research data (15.6 in 100).
    Same numbers as box A2 and dial I; shown only when box A2 has an estimate."""
    r = a.get("risk_exp") or {}
    if r.get("state") != "shown":
        return _blank("No heart risk rate yet: " + str(r.get("reason", "not available")), h=340)
    lo, p, hi = r["low"] * 100, r["p"] * 100, r["high"] * 100
    names = ["Low end of range", "Middle value", "High end of range", "Average in our research data"]
    vals = [lo, p, hi, 15.6]
    cols = ["#fbbf24", "#92400e", "#fbbf24", "#9ca3af"]
    fig = go.Figure(go.Bar(x=names, y=vals, marker_color=cols, text=[f"{v:.0f} in 100" for v in vals], textposition="outside", cliponaxis=False,
                           hovertemplate="%{x}: %{y:.0f} in 100<extra></extra>"))
    fig.update_layout(title=dict(text="Heart risk rate, 5 years (research only, not validated)<br><span style='font-size:11px'>chance of death in our research data for people like this; rough group: " + _e(r["group"]) + "</span>", font=dict(size=13)),
                      height=380, margin=dict(l=50, r=20, t=90, b=60), yaxis=dict(title="in 100 people", range=[0, 105], gridcolor="#e6e5e1"), xaxis=dict(tickfont=dict(size=11)),
                      plot_bgcolor="white", font=dict(color=INK), bargap=0.35)
    return fig


def disease_bars(a):
    """K. Heart disease PATTERNS as VERTICAL bars (not diagnoses). One bar per pattern the tool could check for this photo. Height = the calibrated chance that the ECG shows the pattern where that passed our rules
    (heart-attack pattern), otherwise the model SCORE (not a chance, drawn with a pale hatch). Orange = pattern found, blue = not found."""
    rows = []
    for f in a.get("findings", []):
        if f["state"] != "supported" or f["cls"] == "NORM":
            continue
        if f.get("p_cal") is not None:
            v, kind = float(f["p_cal"]), "chance"
        elif f.get("p") is not None:
            v, kind = float(f["p"]), "chance"
        elif f.get("p_internal") is not None:
            v, kind = float(f["p_internal"]), "score"
        else:
            continue
        rows.append((SHORT_F.get(f["cls"], f["name"][:30]), v * 100, kind, bool(f["detected"])))
    if not rows:
        return _blank("No heart disease pattern could be checked for this photo", h=340)
    names = [r[0] for r in rows]
    vals = [r[1] for r in rows]
    cols = [(ORANGE if r[3] else BLUE) for r in rows]
    shapes = ["" if r[2] == "chance" else "/" for r in rows]
    texts = [(f"{r[1]:.0f} in 100" if r[2] == "chance" else f"score {r[1]:.0f}") + ("<br>FOUND" if r[3] else "<br>not found") for r in rows]
    fig = go.Figure(go.Bar(x=names, y=vals, marker=dict(color=cols, pattern=dict(shape=shapes, fgcolor="white", size=6)), text=texts, textposition="outside", cliponaxis=False,
                           hovertemplate="%{x}: %{y:.0f}<extra></extra>"))
    fig.update_layout(title=dict(text="Heart disease patterns (not diagnoses)<br><span style='font-size:11px'>solid bar = calibrated chance the ECG shows the pattern; hatched bar = model score, not a chance</span>", font=dict(size=13)),
                      height=420, margin=dict(l=50, r=20, t=90, b=110), yaxis=dict(title="in 100 (chance) or score (0 to 100)", range=[0, 112], gridcolor="#e6e5e1"), xaxis=dict(tickangle=-25, tickfont=dict(size=11)),
                      plot_bgcolor="white", font=dict(color=INK), bargap=0.3)
    return fig


def _align(clean12, leads):
    """Aligns the true recording to the digitised one. The digitised lead II (1 kHz, microvolts) and the true lead II (100 Hz, millivolts, upsampled) are compared at 250 Hz; the lag with the best correlation
    (within plus or minus 1 s) is used for every lead. Returns (lag in samples at 1 kHz, {lead: (true_up_aligned, digitised_mV)}) or None."""
    from scipy.signal import resample_poly
    out = {}
    if clean12 is None or leads is None or leads.get("II") is None:
        return None
    t1k = np.arange(10000) / 1000.0
    t100 = np.arange(clean12.shape[1]) / 100.0

    def prep(k, L):
        d = np.asarray(leads.get(L), float)[:10000] / 1000.0 if leads.get(L) is not None else np.full(10000, np.nan)
        if len(d) < 10000:
            d = np.concatenate([d, np.full(10000 - len(d), np.nan)])
        o = np.interp(t1k, t100, clean12[k])
        return o, d

    o2, d2 = prep(D.LEADS.index("II"), "II")
    m = np.isfinite(d2)
    if m.sum() < 3000:
        return None
    a = np.where(m, d2 - np.nanmedian(d2), 0.0)[::4]
    b = (o2 - np.median(o2))[::4]
    best, lag = -2.0, 0
    for L in range(-250, 251):
        x, y = (a[L:], b[:len(b) - L]) if L >= 0 else (a[:L], b[-L:])
        mm = (np.abs(x) > 0) | (np.abs(y) > 0)
        if mm.sum() < 500:
            continue
        c = np.corrcoef(x[mm], y[mm])[0, 1]
        if np.isfinite(c) and c > best:
            best, lag = c, L
    lag1k = lag * 4
    for k, Ln in enumerate(D.LEADS):
        o, d = prep(k, Ln)
        o = o - np.median(o)
        d = d - np.nanmedian(d) if np.isfinite(d).any() else d
        if lag1k >= 0:                                  # digitised signal starts later than the true one by lag1k samples: shift the true one
            o_al = np.concatenate([np.full(lag1k, np.nan), o[:10000 - lag1k]])
        else:
            o_al = np.concatenate([o[-lag1k:], np.full(-lag1k, np.nan)])
        out[Ln] = (o_al, d)
    return lag1k, out


def original_vs_reconstructed(leads, clean12):
    """L. LINE GRAPH: the true recording (dataset record) against the signal the tool read from the picture, lead II with a lead selector. Only for dataset pictures: a photo from a person has no
    original recording. The correlation after aligning the two is shown for every lead."""
    al = _align(clean12, leads)
    if al is None:
        return _blank("No original recording for this picture: the original exists only for dataset pictures", h=380)
    lag, sig = al
    t = np.arange(10000) / 1000.0
    names, cors = [], {}
    fig = go.Figure()
    for Ln in D.LEADS:
        o, d = sig[Ln]
        m = np.isfinite(o) & np.isfinite(d)
        cors[Ln] = float(np.corrcoef(o[m], d[m])[0, 1]) if m.sum() > 500 and np.std(d[m]) > 0 else float("nan")
        vis = Ln == "II"
        fig.add_trace(go.Scattergl(x=t, y=o, mode="lines", name="original (true recording)", line=dict(width=1.4, color="#6b7280"), visible=vis, legendgroup="o", showlegend=vis,
                                   hovertemplate="%{x:.2f} s<br>%{y:.3f} mV<extra>original " + Ln + "</extra>"))
        fig.add_trace(go.Scattergl(x=t, y=d, mode="lines", name="read from the picture", line=dict(width=1.2, color=ORANGE), visible=vis, legendgroup="d", showlegend=vis,
                                   hovertemplate="%{x:.2f} s<br>%{y:.3f} mV<extra>picture " + Ln + "</extra>"))
        names.append(Ln)
    buttons = []
    for i, Ln in enumerate(names):
        vis = [False] * (2 * len(names))
        vis[2 * i] = vis[2 * i + 1] = True
        c = cors[Ln]
        buttons.append(dict(label=f"{Ln} (r = {c:.2f})" if np.isfinite(c) else Ln, method="update", args=[{"visible": vis, "showlegend": vis}, {"title": f"Lead {Ln}: original against read from the picture, correlation r = {c:.2f}" if np.isfinite(c) else f"Lead {Ln}"}]))
    c2 = cors.get("II", float("nan"))
    fig.update_layout(title=dict(text=f"Original against read from the picture, correlation r = {c2:.2f} (choose a lead; drag to zoom)", font=dict(size=13), x=0.22, xanchor="left"), height=420, margin=dict(l=50, r=20, t=80, b=50),
                      updatemenus=[dict(buttons=buttons, active=0 if "II" not in names else names.index("II"), direction="down", x=0.0, y=1.22, xanchor="left", yanchor="top")],
                      xaxis=dict(title="Time (seconds)", gridcolor="#e6e5e1"), yaxis=dict(title="Amplitude (mV)", gridcolor="#e6e5e1"), plot_bgcolor="white", font=dict(color=INK),
                      legend=dict(orientation="h", y=-0.2), annotations=[dict(x=1, y=-0.3, xref="paper", yref="paper", showarrow=False, xanchor="right", font=dict(size=11, color="#374151"),
                                                                           text=f"time shift removed: {lag} ms; amplitudes are not rescaled")])
    return fig


def beat_rate_chart(leads, a):
    """M. LINE GRAPH: the heart rate at each beat (60 / the gap to the previous beat) across the 10 seconds, with the average as a dashed line. Drawn only for a GREEN or AMBER straightened photo, the same
    rule as the heart-rate number: a read that looks unreliable shows no rate. A jumping line means uneven beats (or a bad read); it is not a diagnosis."""
    if leads is None or leads.get("II") is None or not a.get("usable"):
        return _blank("No beat-to-beat heart rate: shown only for a GREEN or AMBER straightened photo", h=380)
    try:
        import neurokit2 as nk
        ii = np.asarray(leads["II"], float)[:10000]
        idx = np.flatnonzero(np.isfinite(ii))
        if len(idx) < 3000:
            return _blank("Too little signal in lead II to find the beats", h=380)
        a0, a1 = idx[0], idx[-1] + 1
        seg = ii[a0:a1]
        seg = np.interp(np.arange(len(seg)), np.flatnonzero(np.isfinite(seg)), seg[np.isfinite(seg)])
        cl = nk.ecg_clean(seg, sampling_rate=1000, method="neurokit")
        pk = np.asarray(nk.ecg_peaks(cl, sampling_rate=1000)[1]["ECG_R_Peaks"])
    except Exception:
        return _blank("The beats could not be found in lead II", h=380)
    if len(pk) < 3:
        return _blank("Fewer than 3 beats found: no beat-to-beat heart rate", h=380)
    rr = np.diff(pk) / 1000.0
    hr = 60.0 / rr
    tt = (a0 + pk[1:]) / 1000.0
    mean = float(np.mean(hr))
    fig = go.Figure()
    fig.add_hrect(y0=60, y1=100, fillcolor=GREEN_BAND, line_width=0, layer="below")
    fig.add_trace(go.Scatter(x=tt, y=hr, mode="lines+markers", line=dict(width=2, color=BLUE), marker=dict(size=8), name="heart rate at each beat",
                             hovertemplate="beat at %{x:.2f} s: %{y:.0f} bpm<extra></extra>"))
    fig.add_hline(y=mean, line_dash="dash", line_color=GRAY, annotation_text=f"average {mean:.0f} bpm", annotation_position="top left")
    fig.add_trace(go.Scatter(x=tt, y=rr * 1000.0, mode="lines+markers", line=dict(width=2, color="#7c3aed", dash="dot"), marker=dict(size=6, symbol="diamond"), name="RR interval (gap between beats)", yaxis="y2",
                             hovertemplate="beat at %{x:.2f} s: RR %{y:.0f} ms<extra></extra>"))
    spread = float(np.max(hr) - np.min(hr))
    fig.update_layout(title=dict(text=f"Beat-to-beat heart rate and RR interval ({len(hr)} beats; heart rate lowest to highest {spread:.0f} bpm; green band = resting adult range 60 to 100)", font=dict(size=13)), height=380,
                      margin=dict(l=60, r=70, t=70, b=50), xaxis=dict(title="Time (seconds)", range=[0, 10], gridcolor="#e6e5e1"),
                      yaxis=dict(title="Heart rate (beats per minute), blue", range=[max(0, min(hr.min(), 60) - 15), max(hr.max(), 100) + 15], gridcolor="#e6e5e1"),
                      yaxis2=dict(title="RR interval (milliseconds), purple dotted", overlaying="y", side="right", showgrid=False, range=[max(0, rr.min() * 1000 - 150), rr.max() * 1000 + 150]),
                      plot_bgcolor="white", font=dict(color=INK), showlegend=False)
    return fig


def risk_vs_age_line(leads, a):
    """N. LINE GRAPH: the research 5-year chance of death of THIS ECG at every age from 20 to 90 (x = age, y = chance in 100 people), with the range of box A2 as a band around the line and a marker at the age used.
    It shows plainly that the number mostly follows age. Drawn only when box A2 has an estimate (GREEN straightened photo). Research only, not validated, not a prediction for the person."""
    r = a.get("risk_exp") or {}
    if r.get("state") != "shown":
        return _blank("No risk-against-age line: " + str(r.get("reason", "not available")), h=380)
    from . import risk as RK
    ages = np.arange(20, 91, 2)
    p = RK.risk3_curve(leads, ages)
    if p is None:
        return _blank("The risk-against-age line could not be computed for this photo", h=380)
    hw = RK.RANGE_HALF_WIDTH_EST if r.get("estimated_age") else RK.RANGE_HALF_WIDTH
    y, lo, hi = p * 100, np.clip(p - hw, 0, 1) * 100, np.clip(p + hw, 0, 1) * 100
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=np.r_[ages, ages[::-1]], y=np.r_[hi, lo[::-1]], fill="toself", fillcolor="rgba(245,158,11,0.25)", line=dict(width=0), name="range shown", hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=ages, y=y, mode="lines", line=dict(width=3, color="#92400e"), name="this ECG at each age", hovertemplate="age %{x}: %{y:.0f} in 100<extra></extra>"))
    fig.add_hline(y=15.6, line_dash="dash", line_color=GRAY, annotation_text="average in our research data (16 in 100)", annotation_position="bottom right")
    fig.add_trace(go.Scatter(x=[r["age"]], y=[r["p"] * 100], mode="markers+text", marker=dict(size=13, color=ORANGE, line=dict(width=2, color="white")), text=[f"age {r['age']:.0f}: {r['p'] * 100:.0f} in 100"],
                             textposition="top left", name="age used", hovertemplate="age %{x:.0f}: %{y:.0f} in 100<extra></extra>"))
    fig.update_layout(title=dict(text="Heart risk rate against age for this ECG (research only, not validated)<br><span style='font-size:11px'>the number mostly follows age; band = range shown</span>", font=dict(size=13)),
                      height=400, margin=dict(l=60, r=20, t=80, b=50), xaxis=dict(title="Age (years)", range=[20, 90], gridcolor="#e6e5e1"),
                      yaxis=dict(title="5-year chance of death (in 100 people)", range=[0, 100], gridcolor="#e6e5e1"), plot_bgcolor="white", font=dict(color=INK), showlegend=False)
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
                parts.append(f"on {f.get('rates_note') or 'our phone-photo tests'} this check found {f['sens'] * 100:.0f} in 100 true patterns and wrongly flagged {(1 - f['spec']) * 100:.0f} in 100 photos without the pattern")
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
        "<li>A 'not found' result misses some patterns: on 300 fresh random simulated phone photos the checks found about 76 in 100 infarction patterns and 70 in 100 ST/T patterns, and wrongly flagged about 34 and 29 in 100 photos without the pattern.</li><li>Conduction patterns in general are not shown for real photos: they were found on photos of a screen but not on our printed-paper photos. Two exceptions passed our rules on fresh dataset pictures (drawn pages and simulated phone photos): left bundle branch block (found about 69 in 100 true patterns on simulated photos, 8 in 100 wrongly flagged) and atrial fibrillation (found about 75 in 100, 9 in 100 wrongly flagged; it passed on its second test). Neither is validated on real phone photos. The other conduction-type patterns (fascicular block, AV block) stay in the research-only block.</li><li>Model confidence is not heart risk.</li><li>Printed paper from one other phone was tested on very few positive photos (5 to 7 per pattern); other phones are not yet shown to work.</li></ul>",
        f"<h4>8. Recommended next steps</h4><p>{_e(a['next_steps'])}</p>",
        f"<div style='margin-top:10px;padding:8px;border:1px solid #d1d5db;border-radius:6px;font-size:12.5px'>{_e(a['disclaimer'])}</div>"]
    return "<div class='hh-light' style='font-size:14px;background:#fff;color:#111;padding:14px;border-radius:8px'>" + "".join(parts) + "</div>"
