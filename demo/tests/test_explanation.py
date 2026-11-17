"""Tests for demo/explain.py (wording rules: docs/plan/EXPLANATION_WORDING.md).
Run:  python -I demo/tests/test_explanation.py      (also works with pytest)"""
import itertools
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import explain as E  # noqa: E402

NAN = float("nan")
HRS = [NAN, 30, 39.9, 40, 57, 59.9, 60, 78, 100, 100.1, 106, 150, 150.1, 200]
REASONS = [[], ["beat spacing is irregular"], ["minor note (did not change the light): one beat gap is much shorter than the others (an extra beat?)"],
           ["leads I, II and III disagree with each other"]]


PRS = [None, NAN, 49.9, 50, 120, 150, 250, 400, 400.1]
CVS = [None, 0.03, 0.2]


def all_cases():
    for light, hr, reasons, found, no_out, pr, cv in itertools.product(("GREEN", "AMBER", "RED"), HRS, REASONS, (True, False), (False, True), PRS, CVS):
        yield (dict(light=light, hr=hr, reasons=reasons, page_found=found, no_output=no_out, pr=pr, cv=cv),
               E.patient_explanation(light, hr, reasons, found, no_out, pr, cv),
               E.general_information(light, hr, reasons, no_out, pr, found, cv))


def row(text, name):
    for line in text.splitlines():
        if line.startswith(f"| **{name}**"):
            return line
    raise AssertionError(f"row {name} missing")


def test_no_forbidden_wording_anywhere():
    n = 0
    for args, main, general in all_cases():
        for t in (main, general):
            bad = E.check_wording(t)
            assert not bad, (args, bad)
        assert "not a medical device" in main.lower(), args
        assert general, args                      # the general section is never empty (it would mean the safety fallback fired)
        n += 1
    assert n == 3 * len(HRS) * len(REASONS) * 2 * 2 * len(PRS) * len(CVS)


def test_checker_catches_bad_sentences():
    for s in ["Your ECG is normal.", "Your ECG looks fine.", "You are healthy.", "You're fine.", "There is nothing to worry about.",
              "There is no need to see a doctor.", "You have atrial fibrillation.", "This is dangerous.", "Stop your medication.",
              "This is a diagnosis of heart block.", "A healthy heart rate."]:
        assert E.check_wording(s), s


def test_checker_allows_the_safe_sentences():
    for s in ["A normal heart rate does not mean a normal ECG or a healthy heart.", "It cannot diagnose anything.", "Not a medical device.",
              "Get help if you have chest pain."]:
        assert not E.check_wording(s), (s, E.check_wording(s))


def test_main_output_has_four_short_parts_and_no_table():
    for light in ("GREEN", "AMBER", "RED"):
        t = E.patient_explanation(light, 78, [], True, False)
        for h in ("What we read", "How sure we are", "What we did not check", "What to do next"):
            assert f"**{h}**" in t, (light, h)
        assert "| Parameter |" not in t and "arrhythmia" not in t          # the table and the general list live in the closed section
        assert "General information" not in t.split("What to do next")[0]
        assert len(t) < 2200, (light, len(t))                              # short
        assert "QT interval" in t and "not available yet" in t           # QT is named as not measured


def test_every_parameter_has_a_row_and_only_hr_and_rhythm_are_measured():
    g = E.general_information("GREEN", 78, [], False)
    for name, _ in E.PARAMS:
        assert row(g, name), name
        if name not in ("Heart rate", "Heart rhythm"):
            assert E.NOT_MEASURED in row(g, name), name      # QT, PR, QRS, ST, T, P, axis are never claimed as measured
    assert "ms" not in row(g, "QT interval")


def test_general_information_is_marked_as_not_a_result():
    for light in ("GREEN", "AMBER", "RED"):
        g = E.general_information(light, 78, [], False)
        assert "general information, not a result for you" in g
        assert "This main result did not look for any of these" in g
        for item in ("arrhythmia", "heart attack", "ischemia", "Heart blocks", "tachycardia", "bradycardia", "hypertrophy", "potassium"):
            assert item in g, (light, item)


def test_red_and_no_output_say_nothing_about_the_heart():
    for hr in HRS:
        for no_out in (False, True):
            t = E.patient_explanation("RED", hr, [], True, no_out)
            assert "beats per minute**" not in t and "usual resting range" not in t, (hr, no_out)
            assert "not giving a heart rate" in t
            g = E.general_information("RED", hr, [], no_out)
            assert "Not given" in row(g, "Heart rate") and "Not given" in row(g, "Heart rhythm")
    t = E.patient_explanation("GREEN", 78, [], True, True)   # a "no output" flag overrides everything
    assert "not giving a heart rate" in t


def test_amber_never_claims_the_number_is_right():
    g = E.general_information("AMBER", 106, [], False)
    assert "we are not sure it is right" in row(g, "Heart rate")
    assert "Not read reliably" in row(E.general_information("AMBER", NAN, [], False), "Heart rate")
    t = E.patient_explanation("AMBER", 106, [], True, False)
    assert "not sure it is right" in t and "usual resting range" not in t


def test_green_boundaries():
    cases = {39.9: "far below", 40: "slow", 59.9: "slow", 60: "inside the usual", 100: "inside the usual", 100.1: "fast", 150: "fast", 150.1: "far above"}
    for hr, word in cases.items():
        assert word in E.patient_explanation("GREEN", hr, [], True, False).split("**Heart rhythm:**")[0], (hr, word)
        assert word in row(E.general_information("GREEN", hr, [], False), "Heart rate"), (hr, word)
    t = E.patient_explanation("GREEN", NAN, [], True, False)   # GREEN without a number cannot occur; it must fall to the cautious text
    assert "not giving a heart rate" in t


def test_uneven_beats_note_only_when_present():
    a = E.patient_explanation("GREEN", 78, [], True, False)
    b = E.patient_explanation("GREEN", 78, ["minor note: one beat gap is much shorter than the others"], True, False)
    assert "closer together" not in a and "closer together" in b
    assert "No uneven spacing noticed" in a


def test_pr_is_shown_only_for_green_straightened_plausible():
    def g(light="GREEN", found=True, no_out=False, pr=150, cv=0.03):
        return E.patient_explanation(light, 78, [], found, no_out, pr, cv)
    ok = g()
    assert "**PR interval:** about **150 ms**" in ok and "differed from hospital software by about 12 ms" in ok and "ask your doctor" in ok
    for bad in (dict(light="AMBER"), dict(light="RED"), dict(found=False), dict(no_out=True), dict(pr=NAN), dict(pr=None), dict(pr=49.9), dict(pr=400.1), dict(cv=0.121), dict(cv=0.4), dict(cv=None), dict(cv=NAN)):
        assert "PR interval:" not in g(**bad), bad
    assert "about **50 ms**" in g(pr=50) and "about **400 ms**" in g(pr=400)
    assert "PR interval:" in g(cv=0.12) and "PR interval:" in g(cv=0.0)       # the limit itself is allowed
    assert "about **150 ms**" not in E.patient_explanation("GREEN", NAN, [], True, False, 150, 0.03)      # GREEN without a heart rate falls back to the cautious text


def test_pr_is_hidden_when_the_beat_spacing_is_irregular():
    irregular = ["beat spacing is irregular"]
    minor = ["minor note (did not change the light): one beat gap is much shorter than the others (an extra beat?)"]
    assert "PR interval:" not in E.patient_explanation("GREEN", 78, irregular, True, False, 150, 0.03)
    assert E.NOT_MEASURED in row(E.general_information("GREEN", 78, irregular, False, 150, True, 0.03), "PR interval")
    assert "PR interval:" in E.patient_explanation("GREEN", 78, minor, True, False, 150, 0.03)        # the frequent minor note alone does not hide it
    assert "PR interval:" in E.patient_explanation("GREEN", 78, [], True, False, 150, 0.03)


def test_pr_is_hidden_for_the_beat_spacing_seen_in_atrial_fibrillation_pages():
    # rr_cv of the 6 held-out atrial fibrillation pages (0.157 to 0.417) and of 8 phone photos of such recordings (0.14 to 0.205): all above 0.12, so PR must be hidden
    for cv in (0.14, 0.142, 0.143, 0.146, 0.157, 0.172, 0.185, 0.19, 0.191, 0.205, 0.253, 0.352, 0.417):
        assert "PR interval:" not in E.patient_explanation("GREEN", 78, [], True, False, 200, cv), cv


def test_not_checked_list_matches_what_is_shown():
    def part(pr):
        t = E.patient_explanation("GREEN", 78, [], True, False, pr, 0.03)
        return t.split("**What we did not check**")[1].split("**What to do next**")[0]
    shown, hidden = part(150), part(None)
    assert "PR interval" not in shown and all(x in shown for x in ("P wave", "QRS complex", "QT interval", "ST segment", "T wave", "axis"))
    assert "PR interval" in hidden


def test_pr_row_in_the_table():
    g = E.general_information("GREEN", 78, [], False, 150, True, 0.03)
    assert "About **150 ms**" in row(g, "PR interval") and E.NOT_MEASURED not in row(g, "PR interval")
    for light in ("AMBER", "RED"):
        assert E.NOT_MEASURED in row(E.general_information(light, 78, [], False, 150, True, 0.03), "PR interval"), light
    assert E.NOT_MEASURED in row(E.general_information("GREEN", 78, [], False, 150, False, 0.03), "PR interval")
    assert E.NOT_MEASURED in row(E.general_information("GREEN", 78, [], False, None, True, 0.03), "PR interval")
    assert E.NOT_MEASURED in row(E.general_information("GREEN", 78, [], False, 150, True, 0.2), "PR interval")        # too much beat-spacing variation
    assert E.NOT_MEASURED in row(E.general_information("GREEN", 78, [], False, 150, True, None), "PR interval")       # unknown spacing hides PR
    for name in ("QRS complex", "QT interval", "P wave", "ST segment", "T wave", "Axis"):      # still never claimed
        assert E.NOT_MEASURED in row(g, name), name


def test_no_interval_verdict_words():
    for s in ["The PR interval is prolonged.", "A shortened PR.", "an abnormal PR interval", "within normal limits", "the normal range", "too long"]:
        assert E.check_wording(s), s


def test_axis_is_shown_only_for_green_straightened_with_a_value():
    def g(light="GREEN", found=True, no_out=False, ax=45.0, cv=0.03):
        return E.patient_explanation(light, 78, [], found, no_out, None, cv, ax)
    ok = g()
    assert "**QRS axis:** about **45 degrees**" in ok and "within 30 degrees for about 95 in 100 photos" in ok and "ask your doctor" in ok
    for bad in (dict(light="AMBER"), dict(light="RED"), dict(found=False), dict(no_out=True), dict(ax=NAN), dict(ax=None)):
        assert "QRS axis:" not in g(**bad), bad
    assert "about **-60 degrees**" in g(ax=-60.4) and "about **180 degrees**" in g(ax=180.0)
    assert "QRS axis:" in g(cv=0.4) and "QRS axis:" in g(cv=None)          # the beat-spacing guard applies to PR only; the axis does not depend on rhythm


def test_axis_row_and_not_checked_list():
    g = E.general_information("GREEN", 78, [], False, None, True, 0.03, 45.0)
    assert "About **45 degrees**" in row(g, "Axis") and E.NOT_MEASURED not in row(g, "Axis")
    for light in ("AMBER", "RED"):
        assert E.NOT_MEASURED in row(E.general_information(light, 78, [], False, None, True, 0.03, 45.0), "Axis"), light
    assert E.NOT_MEASURED in row(E.general_information("GREEN", 78, [], False, None, False, 0.03, 45.0), "Axis")
    assert E.NOT_MEASURED in row(E.general_information("GREEN", 78, [], False, None, True, 0.03, None), "Axis")
    for name in ("QRS complex", "QT interval", "P wave", "ST segment", "T wave"):     # QRS duration and QT are still never claimed
        assert E.NOT_MEASURED in row(g, name), name

    def part(ax):
        t = E.patient_explanation("GREEN", 78, [], True, False, None, 0.03, ax)
        return t.split("**What we did not check**")[1].split("**What to do next**")[0]
    assert " axis" not in part(45.0) and " axis" in part(None)
    assert "QRS complex" in part(45.0) and "QT interval" in part(45.0)                # QRS duration and QT stay in the not-checked list


def test_no_axis_verdict_words_and_the_grid_stays_clean():
    for s in ["Left axis deviation.", "a normal axis", "right axis", "extreme axis", "the axis is abnormal", "axis deviation"]:
        assert E.check_wording(s), s
    for light, ax, pr, found, cv in itertools.product(("GREEN", "AMBER", "RED"), (None, NAN, -90.0, -30.0, 0.0, 60.0, 90.0, 148.0, 180.0), (None, 150), (True, False), (None, 0.03, 0.2)):
        for t in (E.patient_explanation(light, 78, [], found, False, pr, cv, ax), E.general_information(light, 78, [], False, pr, found, cv, ax)):
            assert not E.check_wording(t), (light, ax, pr, found, cv, E.check_wording(t))


if __name__ == "__main__":
    fns =[v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for f in fns:
        f()
        print("ok  ", f.__name__)
    print(f"{len(fns)} tests passed")
