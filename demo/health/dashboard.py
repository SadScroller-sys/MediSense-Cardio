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
        "<div style='font-size:12px;margin-top:6px;color:#374151'>Model confidence is not the same as the chance of heart disease: a high model score only says the picture resembles the pattern.</div></div></div>")


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
            if f.get("p") is None and not f.get("validated"):
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
        f"<h4>6. Risk category and supporting evidence</h4><p>{_e(a['risk'])}</p>",
        "<h4>7. Confidence and limitations</h4><ul><li>Each measurement above carries the error we measured for its method; the traffic light is the per-photo check.</li>"
        "<li>The findings model was trained on public hospital ECGs and tested on our drawn pages and phone photos; findings that did not pass the pre-set tests are not shown.</li>"
        "<li>A 'not found' result misses some patterns: in our phone-photo tests the checks found about 79 in 100 infarction patterns and 72 in 100 ST/T patterns, and wrongly flagged 16 to 20 in 100 photos without the pattern.</li><li>Conduction patterns in general are not shown for real photos: they were found on photos of a screen but not on our printed-paper photos. Two exceptions passed our rules on fresh dataset pictures (drawn pages and simulated phone photos): left bundle branch block (found about 69 in 100 true patterns on simulated photos, 8 in 100 wrongly flagged) and atrial fibrillation (found about 75 in 100, 9 in 100 wrongly flagged; it passed on its second test). Neither is validated on real phone photos. The other conduction-type patterns (fascicular block, AV block) stay in the research-only block.</li><li>Model confidence is not heart risk.</li><li>Printed paper from one other phone was tested on very few positive photos (5 to 7 per pattern); other phones are not yet shown to work.</li></ul>",
        f"<h4>8. Recommended next steps</h4><p>{_e(a['next_steps'])}</p>",
        f"<div style='margin-top:10px;padding:8px;border:1px solid #d1d5db;border-radius:6px;font-size:12.5px'>{_e(a['disclaimer'])}</div>"]
    return "<div class='hh-light' style='font-size:14px;background:#fff;color:#111;padding:14px;border-radius:8px'>" + "".join(parts) + "</div>"
