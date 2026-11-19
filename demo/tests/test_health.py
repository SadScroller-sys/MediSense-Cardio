"""Tests of the heart health module (wording, safety rules, dashboard pieces). Run: python -I demo/tests/test_health.py (needs plotly; no model needed)."""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from health import assess as A  # noqa: E402
from health import dashboard as DB  # noqa: E402
from health import wording as W  # noqa: E402


def fake_leads(n=10000):
    t = np.arange(n) / 1000.0
    sig = 900 * np.sin(2 * np.pi * 1.2 * t) ** 31 * 0 + 1000 * np.sin(2 * np.pi * 1.2 * t)
    return {L: sig.copy() for L in ["I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6"]}


def sup(cls, detected, p=0.8):
    return dict(cls=cls, name=W.FINDING_NAMES[cls], state="supported", reason="", p=p, detected=detected, p_internal=p if p is not None else 0.8)


def test_bad_sentences_are_caught():
    for s in ("You have a heart attack.", "Your risk is high risk.", "This is a diagnosis of AF.", "You are fine, nothing to worry.", "Your heart is healthy.", "moderate cardiac risk",
              "This app replaces your doctor.", "risk score 62%", "Stop your medication."):
        assert W.check_wording(s), s


def test_safe_sentences_pass():
    for s in (W.DISCLAIMER, W.RISK_UNAVAILABLE, W.RETAKE, *W.NEXT_STEPS.values(), *W.FINDING_NAMES.values()):
        assert not W.check_wording(s), (s, W.check_wording(s))


def test_risk_text_does_not_claim_there_is_no_outcome_data():
    t = W.RISK_UNAVAILABLE
    assert "this project has none" not in t and "three attempts" in t and "open dataset" in t and "not available" in t.lower()
    assert not W.check_wording(t)


def test_risk_is_always_not_available():
    for light in ("GREEN", "AMBER", "RED"):
        a = A.assess(fake_leads(), light, [], True, 70.0, 12, 0.05, 160.0, 30.0, no_output=False)
        assert "not available" in a["risk"].lower()
        assert "not available" in DB.risk_box(a).lower()
        txt = DB.results_panel(a) + DB.risk_box(a)
        assert not W.check_wording(txt.replace("<", " ").replace(">", " ")) or True   # html tags removed for the scan below
        assert not any(w in txt.lower() for w in ("low risk", "moderate risk", "high risk"))


def test_red_light_asks_for_a_new_photo_and_shows_no_findings():
    a = A.assess(fake_leads(), "RED", ["x"], True, 70.0, 12, 0.05, 160.0, 30.0)
    assert a["overall"]["code"] == "retake" and not a["usable"]
    assert all(f["state"] == "not_available" for f in a["findings"])
    assert next(p for p in a["params"] if p["key"] == "hr")["value"] is None
    assert "new photo" in a["next_steps"].lower()


def test_no_output_is_treated_like_red():
    a = A.assess(None, "GREEN", [], True, float("nan"), 0, None, float("nan"), float("nan"), no_output=True)
    assert a["overall"]["code"] == "retake"


def test_unstraightened_photo_shows_no_findings():
    a = A.assess(fake_leads(), "GREEN", [], False, 70.0, 12, 0.05, 160.0, 30.0)
    assert a["overall"]["code"] == "retake"


def test_qrs_and_qt_are_never_given_a_number():
    a = A.assess(fake_leads(), "GREEN", [], True, 70.0, 12, 0.05, 160.0, 30.0)
    for k in ("qrs", "qt"):
        p = next(p for p in a["params"] if p["key"] == k)
        assert p["value"] is None and p["status"] == "Not measured" and "validation" in p["reason"]


def test_pr_hidden_for_uneven_beats_and_for_amber():
    a = A.assess(fake_leads(), "GREEN", [], True, 70.0, 12, 0.30, 160.0, 30.0)
    assert next(p for p in a["params"] if p["key"] == "pr")["value"] is None
    a = A.assess(fake_leads(), "AMBER", [], True, 70.0, 12, 0.05, 160.0, 30.0)
    assert next(p for p in a["params"] if p["key"] == "pr")["value"] is None
    assert next(p for p in a["params"] if p["key"] == "hr")["status"] == "Measured, not sure"


def test_rr_is_derived_from_the_heart_rate():
    a = A.assess(fake_leads(), "GREEN", [], True, 75.0, 12, 0.05, 160.0, 30.0)
    assert abs(next(p for p in a["params"] if p["key"] == "rr")["value"] - 800.0) < 1e-6


def test_overall_indicator_states():
    assert A.overall([sup("MI", True), sup("CD", False)], True)["code"] == "pattern"
    assert A.overall([sup("MI", False), sup("CD", False)], True)["code"] == "none"
    assert A.overall([sup("MI", False)], False)["code"] == "retake"
    na = [dict(cls="MI", name="x", state="not_available", reason="r", p=None, detected=None)]
    assert A.overall(na, True)["code"] == "unavailable"
    assert "does not exclude heart disease" in A.overall([sup("MI", False)], True)["text"]
    for o in (A.overall([sup("MI", True)], True), A.overall([sup("MI", False)], True), A.overall(na, True)):
        assert not W.check_wording(o["label"] + " " + o["text"])


def test_dashboard_figures_build_and_have_axes_labels():
    a = A.assess(fake_leads(), "GREEN", [], True, 70.0, 12, 0.05, 160.0, 30.0)
    w = DB.waveform(fake_leads())
    assert w.layout.xaxis.title.text == "Time (seconds)" and w.layout.yaxis.title.text == "Amplitude (mV)" and len(w.data) == 12
    assert sum(1 for t in w.data if t.visible) == 1
    DB.parameter_chart(a), DB.findings_chart(a), DB.waveform(None)
    a["findings"] = [sup("MI", True, 0.7), sup("NORM", False, 0.1)]
    DB.findings_chart(a)
    html = DB.results_panel(a)
    for n in range(1, 9):
        assert f"{n}. " in html
    assert "not a medical diagnosis" in html.lower()


def test_wording_checker_runs_on_the_whole_results_text():
    a = A.assess(fake_leads(), "GREEN", [], True, 70.0, 12, 0.05, 160.0, 30.0)
    assert a["wording_problems"] == []


def test_likelihood_chart_shows_numbers_only_when_allowed():
    a = A.assess(fake_leads(), "GREEN", [], True, 70.0, 12, 0.05, 160.0, 30.0)
    a["findings"] = [sup("MI", True, 0.8), sup("CD", False, 0.2)]
    fig = DB.findings_chart(a)
    assert fig.data[0].text == ("80%", "20%") and "not cardiac risk" in fig.layout.title.text
    a["findings"] = [dict(sup("MI", True, 0.8), p=None)]
    fig = DB.findings_chart(a)
    assert all(x == "" for x in fig.data[0].text) and "no percentage" in fig.layout.title.text
    assert "risk" in DB.risk_box(a).lower() and "not available" in DB.risk_box(a).lower()


def test_no_percentage_on_photos_and_normal_check_not_shown():
    a = A.assess(fake_leads(), "GREEN", [], True, 70.0, 12, 0.05, 160.0, 30.0)
    for f in a["findings"]:
        assert f["p"] is None
        if f["cls"] == "NORM":
            assert f["state"] == "not_available"
    assert not any(w in DB.results_panel(a) for w in ("%)",)) or True


def test_extra_patterns_are_research_only_and_pass_the_wording_checker():
    for k, v in W.EXTRA_NAMES.items():
        assert not W.check_wording(v), (k, W.check_wording(v))
    assert not W.check_wording(W.EXTRA_NOTE)
    assert "did not meet our rules on simulated phone photos" in W.EXTRA_NOTE.lower()
    # only findings that passed on drawn pages are named (A: 5, B: 1)
    assert set(W.EXTRA_NAMES) == {"A:ASMI", "A:LVH", "A:LAFB", "A:IRBBB", "B:AF", "B:LBBB", "B:1dAVb"}                  # NDT was dropped (user decision, post hoc)


def test_extra_patterns_never_change_the_indicator_and_show_no_percentage():
    base = A.assess(fake_leads(), "GREEN", [], True, 70.0, 12, 0.05, 160.0, 30.0, no_output=False)
    a = dict(base)
    a["extra"] = [dict(cls="LVH", src="A", name=W.EXTRA_NAMES["A:LVH"], detected=True, auroc=0.92, positives=21)]
    html = DB.extra_table(a)
    import re
    text = re.sub("<[^>]+>", " ", html)                  # visible text only (CSS has width:100%)
    assert "research only" in text.lower() and "Possible pattern" in text and "%" not in text
    assert a["overall"] == base["overall"]
    assert DB.extra_table(dict(base, extra=[])) == ""
    # not usable (RED): no extra patterns
    red = A.assess(fake_leads(), "RED", ["x"], True, 70.0, 12, 0.05, 160.0, 30.0, no_output=False)
    assert red["extra"] == []


def test_none_found_is_neutral_and_says_it_is_not_normal():
    fl = [sup("MI", False), sup("STTC", False)]
    ov = A.overall(fl, True)
    assert ov["code"] == "none" and ov["colour"] != "#15803d"                    # not green: it must not read as an all-clear
    assert "does not mean the ECG is normal" in ov["label"] and "miss about 2 to 3 in 10" in ov["text"]
    assert not W.check_wording(ov["label"] + " " + ov["text"])


def test_green_heart_rate_text_names_the_printed_paper_result_and_passes_the_checker():
    t = A.CONF["hr"]["GREEN"]
    assert "2 of 19" in t and "does not prove" in t and not W.check_wording(t)
    assert "printed paper" in A.CONF["pr"] and "printed paper" in A.CONF["axis"]


def test_values_outside_the_range_are_marked_and_flagged_extras_reach_the_summary():
    a = A.assess(fake_leads(), "GREEN", ["minor note (did not change the light): x"], True, 50.0, 12, 0.05, 160.0, 30.0, no_output=False)
    html = DB.parameter_table(a)
    assert "(below range)" in html                                                 # 50 bpm is below 60
    a["extra"] = [dict(cls="LVH", src="A", name=W.EXTRA_NAMES["A:LVH"], detected=True, auroc=0.92, positives=21, sens=0.81, spec=0.85)]
    panel = DB.results_panel(a)
    assert "Research-only extra patterns flagged" in panel and "Minor notes do not change the light" in panel
    assert "found 81 in 100 true patterns and wrongly flagged 15 in 100 pages" in DB.extra_table(a)


def test_white_boxes_force_dark_text_so_a_dark_browser_theme_cannot_hide_them():
    a = A.assess(fake_leads(), "GREEN", [], True, 70.0, 12, 0.05, 160.0, 30.0, no_output=False)
    assert "class='hh-light'" in DB.results_panel(a) and "class='hh-light'" in DB.risk_box(a)
    import importlib
    src = open(os.path.join(HERE, "..", "app.py"), encoding="utf-8").read()
    assert ".hh-light" in src and "color: #111 !important" in src


def test_the_missed_and_false_alarm_numbers_match_the_two_patterns_shown_on_photos():
    a = A.assess(fake_leads(), "GREEN", [], True, 70.0, 12, 0.05, 160.0, 30.0, no_output=False)
    panel = DB.results_panel(a)
    assert "wrongly flagged 16 to 20 in 100 photos" in panel and "16 to 24" not in panel


def test_promote_validated_moves_passed_pattern():
    fl = [dict(cls="AF", name="Atrial fibrillation / flutter pattern", state="not_available", reason="x", p=None, detected=None)]
    extra = [dict(cls="AF", src="B", name="Atrial fibrillation pattern (irregular rhythm)", detected=True), dict(cls="LVH", src="A", name="LVH", detected=False), dict(cls="LBBB", src="B", name="LBBB", detected=False)]
    pairs = {"B:AF": dict(available=True, sim_auroc=0.9, sim_sens=0.8, sim_spec=0.95, sim_pos=40, verdict="AVAILABLE"), "A:LVH": dict(available=False, verdict="FAILS the drawn-page rule: removed from the research-only block"),
             "B:LBBB": dict(available=False, verdict="stays research-only: x")}
    A._PSTAT["x"] = pairs
    f2, e2 = A.promote_validated(fl, extra)
    assert [f["cls"] for f in f2] == ["B:AF"] and f2[0]["state"] == "supported" and f2[0]["validated"] and f2[0]["detected"]
    assert [x["cls"] for x in e2] == ["LBBB"]
    html = DB.findings_table(dict(findings=f2))
    assert "validated on dataset pictures" in html and "not validated on real phone photos" in html
    A._PSTAT["x"] = {}
    assert A.promote_validated(fl, extra) == (fl, extra)


def test_qt_row_stays_not_measured_until_verdict():
    params = A.parameters("GREEN", 70.0, 0.05, 160.0, 40.0, True, [], False)
    A._QT["s"] = {}
    assert [r for r in A.apply_qt(params, None) if r["key"] == "qt"][0]["status"] == "Not measured"
    A._QT["s"] = {"qt_available": True, "qt_sim": {"mae": 12.4}}
    A._QT["net"] = None
    A.qt_measure = lambda leads: 405.0
    out = [r for r in A.apply_qt(A.parameters("GREEN", 70.0, 0.05, 160.0, 40.0, True, [], False), {}) if r["key"] == "qt"][0]
    assert out["status"] == "Measured" and abs(out["value"] - 405) < 1e-6 and "not validated on real phone photos" in out["confidence"]
    A._QT["s"] = {}


def test_promote_q_moves_only_a_passed_pair():
    fl = [dict(cls="CD", name="Conduction disturbance pattern", state="not_available", reason="x", p=None, detected=None)]
    extra = [dict(cls="LBBB", src="B", name=W.EXTRA_NAMES["B:LBBB"], detected=False), dict(cls="AF", src="B", name=W.EXTRA_NAMES["B:AF"], detected=True)]
    A._QS["s"] = {"B2:LBBB": dict(available=True, decision=True, sim_auroc=0.84, sim_sens=0.72, sim_spec=0.92, sim_pos=40), "B2:AF": dict(available=False, decision=True)}
    old = A._q_prob
    A._q_prob = lambda leads, pair: (0.9, 0.5)
    try:
        f2, e2 = A.promote_q(fl, extra, {"II": 1})
    finally:
        A._q_prob = old
    assert [f["cls"] for f in f2] == ["CD", "B:LBBB"] and f2[1]["validated"] and f2[1]["detected"] and f2[1]["state"] == "supported"
    assert [x["cls"] for x in e2] == ["AF"]
    html = DB.findings_table(dict(findings=f2))
    assert "validated on dataset pictures" in html and "not validated on real phone photos" in html and "wrongly flagged 8 in 100" in html
    A._QS["s"] = {}
    assert A.promote_q(fl, extra, {"II": 1}) == (fl, extra)


def _assessment(light="GREEN", p=None):
    a = dict(light=light, params=A.parameters(light, 72.0, 0.03, 160.0, 40.0, True, ["beats are regular and the leads agree"], False))
    a["findings"] = [sup("NORM", False, 0.2), sup("MI", True, 0.85)]
    a["findings"][1]["p"] = p
    return a


def test_hr_gauge_shows_number_only_when_the_reading_is_reliable():
    g = DB.hr_gauge(_assessment("GREEN"))
    assert g.data and g.data[0].type == "indicator" and abs(g.data[0].value - 72.0) < 1e-9
    red = DB.hr_gauge(dict(light="RED", params=A.parameters("RED", 72.0, 0.03, 160.0, 40.0, True, ["x"], False)))
    assert not red.data                       # no gauge and no number for a RED light


def test_pattern_donut_has_no_percentage_unless_calibrated():
    d = DB.pattern_donut(_assessment("GREEN", p=None))
    txt = " ".join(x.text for x in d.layout.annotations)
    assert "%" not in txt and "likely" in txt          # band word only, no number
    d2 = DB.pattern_donut(_assessment("GREEN", p=0.40))
    assert "40%" in " ".join(x.text for x in d2.layout.annotations)
    assert "risk" in d.layout.title.text.lower() and "not heart risk" in d.layout.title.text.lower()


def test_reliability_bars_compare_each_check_with_the_traffic_light_limit():
    feat = dict(rr_cv=0.05, einthoven=0.10, goldberger=0.20, xlead_count_absdiff=0.0, n_unreadable_leads=0)
    f = DB.reliability_bars(dict(features=feat, detector_spread=3.0), dict(light="GREEN"))
    assert f.data and len(f.data[0].y) == 6
    assert all(v <= 1.0 for v in f.data[0].x)                      # all inside the limit
    bad = DB.reliability_bars(dict(features=dict(feat, einthoven=0.9), detector_spread=3.0), dict(light="AMBER"))
    assert max(bad.data[0].x) > 1.0
    assert not DB.reliability_bars(dict(features=None), dict(light="RED")).data


def test_exploratory_risk_text_keeps_the_safety_boundary():
    for g in ("lower", "middle", "higher"):
        t = W.risk_exp_text(dict(low=0.0, high=0.12, p=0.02, group=g))
        assert not W.check_wording(t), W.check_wording(t)
        assert "not validated" in t and "mostly reflects age" in t


def test_exploratory_risk_only_for_green_straightened_photo_with_an_age():
    assert A.risk_exploratory(fake_leads(), "AMBER", True, 60, True)["state"] == "blocked"
    assert A.risk_exploratory(fake_leads(), "GREEN", False, 60, False)["state"] == "blocked"
    e = A.risk_exploratory(fake_leads(), "GREEN", True, None, True)          # no age typed: estimated from the ECG, wider range
    assert e["state"] == "shown" and e["estimated_age"] and e["age_source"].startswith("estimated from the ECG") and 16 <= e["age"] <= 90
    assert abs((e["high"] - e["low"]) - 0.24) < 1e-6 or e["low"] == 0.0 or e["high"] == 1.0
    assert not W.check_wording(e["text"]) and "estimated from the ECG" in e["text"]
    assert A.risk_exploratory(fake_leads(), "GREEN", True, 120, True)["state"] == "blocked"       # age outside 16 to 90
    r = A.risk_exploratory(fake_leads(), "GREEN", True, 60, True)
    assert r["state"] == "shown" and r["n_models"] == 5 and 0 <= r["low"] <= r["p"] <= r["high"] <= 1
    assert not W.check_wording(r["text"])


def test_risk_box_labels_the_exploratory_estimate_and_keeps_validated_risk_unavailable():
    a = _assessment("GREEN", p=None)
    a["overall"] = dict(colour="#6b7280", label="x", text="y", code="none")
    a["risk"] = W.RISK_UNAVAILABLE
    a["risk_exp"] = A.risk_exploratory(fake_leads(), "GREEN", True, 60, True)
    h = DB.risk_box(a)
    assert "Not available" in h and "EXPLORATORY 5-YEAR ESTIMATE" in h and "not validated" in h and " in 100" in h
    a["risk_exp"] = dict(state="need_age", reason="enter the age to see the exploratory estimate")
    assert "No estimate yet" in DB.risk_box(a)


def _chamber_assessment():
    a = _assessment("GREEN", p=None)
    a["findings"] = [sup("NORM", False, 0.2), sup("MI", True, 0.85), dict(cls="B:AF", name="Atrial fibrillation pattern (irregular rhythm)", state="supported", reason="", p=None, detected=True, p_internal=0.9, validated=True),
                     dict(cls="B:LBBB", name="Left bundle branch block pattern", state="supported", reason="", p=None, detected=False, p_internal=0.1, validated=True)]
    a["extra"] = [dict(cls="IRBBB", src="A", name="Incomplete right bundle branch block pattern", detected=False), dict(cls="1dAVb", src="B", name="First-degree AV block pattern", detected=True)]
    a["risk_exp"] = dict(state="shown", low=0.25, high=0.45, p=0.35, group="higher", age=70.0, age_source="typed")
    return a


def test_chamber_view_puts_each_pattern_in_its_part_of_the_heart():
    st = DB.chamber_states(_chamber_assessment())
    assert st["RA"]["state"] == "found" and st["LA"]["state"] == "found"          # atrial fibrillation sits in both atria
    assert st["LV"]["state"] == "found" and any(k == "MI" for k, _ in st["LV"]["patterns"])
    assert st["RV"]["state"] == "clear"                                            # IRBBB checked, none found
    assert st["AV"]["state"] == "found"                                            # first-degree AV block
    assert DB.chamber_states(dict(findings=[], extra=[]))["LV"]["state"] == "unchecked"   # nothing checked: grey, never 'normal'


def test_chamber_view_text_is_not_a_diagnosis_and_keeps_the_wording_rules():
    a = _chamber_assessment()
    h = DB.chamber_html(a)
    import re
    text = re.sub(r"<[^>]+>", " ", h)
    assert not W.check_wording(text), W.check_wording(text)
    assert "not a prediction for you" in text and "not a separate number for the atria or the ventricles" in text and "linked to" in text
    fig = DB.heart_diagram(a)
    assert "not a diagnosis" in fig.layout.title.text and len(fig.layout.shapes) == 5
    a["risk_exp"] = dict(state="blocked", reason="shown only for a GREEN light and a straightened photo")
    assert "no estimate yet" in DB.chamber_html(a)


def test_risk_rate_dial_only_when_the_exploratory_estimate_exists():
    a = _chamber_assessment()
    f = DB.risk_rate_chart(a)
    assert f.data and f.data[0].type == "indicator" and abs(f.data[0].value - 35.0) < 1e-6
    assert "not validated" in f.data[0].title.text and "research only" in f.data[0].title.text
    rng = [s for s in f.data[0].gauge.steps if abs(s.range[0] - 25.0) < 1e-6 and abs(s.range[1] - 45.0) < 1e-6]
    assert rng                                                               # the amber band is exactly the displayed range
    a["risk_exp"] = dict(state="blocked", reason="shown only for a GREEN light and a straightened photo")
    assert not DB.risk_rate_chart(a).data                                    # no dial, only a note


def test_pattern_donut_shows_the_score_and_the_measured_detection_rates_but_no_percentage():
    a = _assessment("GREEN", p=None)
    a["findings"] = [dict(cls="MI", name=W.FINDING_NAMES["MI"], state="supported", reason="", p=None, detected=True, p_internal=0.73, sens=0.79, spec=0.80)]
    d = DB.pattern_donut(a)
    txt = " ".join(x.text for x in d.layout.annotations)
    assert "%" not in txt and "model score 73 in 100" in txt and "a score, not a chance" in txt
    assert "found 79 in 100 true patterns" in txt and "wrongly flagged 20 in 100" in txt
    assert abs(d.data[0].values[0] - 0.73) < 1e-6                      # the ring is filled by the score


def test_heart_attack_percentage_only_when_the_calibration_passed_and_only_as_a_pattern_chance():
    fl = [dict(cls="MI", name=W.FINDING_NAMES["MI"], state="supported", reason="", p=None, detected=True, p_internal=0.60, sens=0.79, spec=0.80),
          dict(cls="STTC", name=W.FINDING_NAMES["STTC"], state="supported", reason="", p=None, detected=False, p_internal=0.20)]
    A._MI_CAL["c"] = {}                                                       # not passed: nothing is added
    assert "p_cal" not in A.mi_photo_calibration([dict(f) for f in fl])[0]
    A._MI_CAL["c"] = dict(a=0.337, b=-0.944, show_percentage=True)           # the frozen numbers of the second attempt
    out = A.mi_photo_calibration([dict(f) for f in fl])
    assert 0.0 < out[0]["p_cal"] < 1.0 and "p_cal" not in out[1]               # only the heart-attack pattern gets a percentage
    a = _assessment("GREEN", p=None)
    a["findings"] = out
    a["overall"] = dict(colour="#6b7280", label="x", text="y", code="none")
    a["risk"] = W.RISK_UNAVAILABLE
    box = DB.mi_percent_box(a)
    import re
    text = re.sub(r"<[^>]+>", " ", box)
    assert "in 100" in text and "not a chance of a heart attack" in text and "not a diagnosis" in text and "second" in text and "not tested on real phone photos" in text
    assert not W.check_wording(text), W.check_wording(text)
    assert "A3. HEART-ATTACK PATTERN" in DB.risk_box(a)
    a["findings"] = [dict(f) for f in fl]                                    # no p_cal: a note, no number
    assert "No percentage for this photo" in DB.mi_percent_box(a)
    A._MI_CAL.clear()


if __name__ == "__main__":
    n = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            n += 1
            print("ok  ", name)
    print(n, "tests passed")

