"""Patient explanation for the MediSense-Cardio demo: FIXED sentences only (no language model).
Rules and reasons: docs/plan/EXPLANATION_WORDING.md.
Two texts:
  patient_explanation(...)  the MAIN output, four short parts: what we read, how sure we are, what we did not check, what to do next.
  general_information(...)  a CLOSED section "What an ECG shows (general information)": a table of the nine ECG parameters (what each tells doctors, what this tool got
                            from the photo or "Not measured by this tool") and a general list of what an ECG can help doctors find (NOT a result for the patient).
Measured by this tool: the heart rate, a rough beat-spacing check, the PR interval and the frontal QRS axis, which passed our pre-set tests (docs/plan/analysis_plan_changes.md,
Sections U and W) on STRAIGHTENED photos. PR is shown only for a GREEN light, a straightened photo and a plausible value, as a number without any verdict.
It never diagnoses, never names a condition for the photo, and says nothing about the heart when the traffic light is RED or the digitiser gave no output.
Research prototype. Not a medical device."""
import re

# Exact safe phrases: removed before the forbidden-pattern scan (they contain words that would otherwise match).
SAFE_PHRASES = [
    "does not mean a normal ecg or a healthy heart",
    "cannot diagnose anything",
    "not a medical device",
]

FORBIDDEN = [
    (r"\byour ecg (is|looks|appears|seems)\b", "judges the ECG"),
    (r"\bthe ecg (is|looks|appears|seems) (normal|fine|healthy)", "judges the ECG"),
    (r"\byou('re| are) (healthy|fine|ok|okay|safe)\b", "says the person is fine"),
    (r"\bnothing to worry\b", "false reassurance"),
    (r"\bno need to (see|visit|consult|worry)", "false reassurance"),
    (r"(?<!if )\byou have\b", "names a condition or state"),
    (r"\b(dangerous|life-threatening)\b", "alarming claim"),
    (r"\b(take|stop|start|increase|reduce) (a |an |your |the |some )?(medicine|medicines|medication|pill|pills|tablet|tablets|drug|drugs)\b", "medicine advice"),
    (r"\b(healthy|normal ecg)\b", "health judgement outside the safe sentence"),
    (r"\bdiagnos", "diagnosis wording outside the safe sentence"),
    (r"\b(prolonged|shortened|abnormal|within normal|normal range|too long|too short)\b", "judges an interval"),
    (r"\b(left|right) axis|axis deviation|normal axis|extreme axis|\baxis is\b", "judges the axis"),
]


def check_wording(text):
    """Returns a list of (pattern_reason, matched_text). Empty list = the text keeps the safety boundary."""
    t = text.lower()
    for s in SAFE_PHRASES:
        t = t.replace(s, " ")
    found = []
    for pat, why in FORBIDDEN:
        for m in re.finditer(pat, t):
            found.append((why, m.group(0)))
    return found


FOOTER = "*Research prototype. Not a medical device. It cannot diagnose anything.*"
TIPS = "A new photo may help: hold the phone straight above the page, keep the whole page in the picture, and make sure the light is even and the photo is in focus."
URGENT = "Get medical help straight away for chest pain, fainting, breathlessness or a racing heartbeat."
SAFE_FALLBACK = ("### Your ECG photo, in plain words\n\nThis tool cannot give a reliable explanation for this photo. Please show your original ECG to a doctor. "
                 + URGENT + "\n\n" + FOOTER)
PR_MIN_MS, PR_MAX_MS = 50, 400
AXIS_NOTE = "This is a rough estimate by our method; in our tests it was typically within about 5 degrees of hospital software, and within 30 degrees for about 95 in 100 photos. Please ask your doctor what it means."
PR_NOTE = "This is a rough estimate by our method; in our tests it differed from hospital software by about 12 ms on a typical photo. Please ask your doctor what it means."

# What each ECG parameter means (general information).
PARAMS = [
    ("Heart rate", "Number of heartbeats per minute"),
    ("Heart rhythm", "Whether the heartbeat is regular or irregular"),
    ("P wave", "Electrical activity of the upper chambers (atria)"),
    ("PR interval", "Time for the signal to travel from the upper chambers to the lower chambers"),
    ("QRS complex", "Electrical activity of the lower chambers (ventricles)"),
    ("QT interval", "Time for the lower chambers to activate and then recover"),
    ("ST segment", "Changes that may point to reduced blood supply or injury of the heart muscle"),
    ("T wave", "Recovery of the lower chambers"),
    ("Axis", "Overall direction of the heart's electrical activity"),
]
NOT_MEASURED = "Not measured by this tool"

CAN_FIND = [
    "**Irregular heartbeat** (arrhythmia)",
    "**Signs of a heart attack** (patterns in the ST segment and T wave)",
    "**Reduced blood supply to the heart** (ischemia)",
    "**Heart blocks** (problems with the electrical signal moving through the heart)",
    "**A fast heartbeat** (tachycardia) or **a slow heartbeat** (bradycardia)",
    "**Thickened or enlarged heart chambers** (ventricular hypertrophy)",
    "**Changes linked to potassium or calcium levels** in the blood",
]


def hr_meaning(hr):
    if hr < 40:
        return "far below the usual resting range (60 to 100); please talk to a doctor soon"
    if hr < 60:
        return "slow (below 60); this can be usual in fit people and during sleep"
    if hr <= 100:
        return "inside the usual resting range (60 to 100)"
    if hr <= 150:
        return "fast (above 100); this can come from exercise, fever, stress or caffeine"
    return "far above the usual resting range (60 to 100); please talk to a doctor soon"


def _state(light, hr, reasons, no_output):
    has_hr = (hr == hr) and hr is not None
    if no_output:
        light, has_hr = "RED", False
    if light == "GREEN" and not has_hr:
        light = "RED"          # GREEN without a number cannot occur; fall back to the cautious text
    uneven = any(("irregular" in x) or ("beat gap" in x) for x in (reasons or []))
    return light, has_hr, uneven


RR_CV_MAX = 0.12      # beat-spacing variation (SD/mean of the beat gaps) above which PR is never shown; see pr_shown()


def pr_shown(light, pr_ms, page_found, reasons=None, rr_cv=None):
    """PR is shown only for a GREEN light, a straightened photo (page found), a plausible value (50 to 400 ms), no 'irregular' reason from the traffic light, AND a measured
    beat-spacing variation (rr_cv) of at most RR_CV_MAX. A missing rr_cv hides PR. No other case.
    Why the last two guards (2026-11-14): 12SL finds no PR for 95% of atrial fibrillation / flutter recordings (no P waves), yet our method still produced a PR for all 6 such held-out pages.
    The 'irregular' reason catches only 4 of those 6; rr_cv > 0.12 catches all 6 pages and all 8 phone photos of such recordings in our data, and hides PR on about 15% of normal-rhythm photos.
    It is a precaution calibrated on 14 cases, not a validated filter."""
    irregular = any("irregular" in x for x in (reasons or []))
    calm = rr_cv is not None and rr_cv == rr_cv and rr_cv <= RR_CV_MAX
    return bool(light == "GREEN" and page_found and not irregular and calm and pr_ms is not None and pr_ms == pr_ms and PR_MIN_MS <= pr_ms <= PR_MAX_MS)


def axis_shown(light, axis_deg, page_found):
    """The frontal QRS axis is shown only for a GREEN light, a straightened photo (page found) and a measured value, as degrees without any verdict word. No other case."""
    return bool(light == "GREEN" and page_found and axis_deg is not None and axis_deg == axis_deg)


def _cells(light, hr, has_hr, uneven):
    if light == "GREEN":
        hr_cell = f"**{hr:.0f} beats per minute**: {hr_meaning(hr)}"
        rhythm_cell = ("Some beats were closer together than others. This can be harmless or a rhythm problem, and this tool cannot tell which"
                       if uneven else "No uneven spacing noticed by our rough check")
    elif light == "AMBER":
        hr_cell = f"About {hr:.0f} beats per minute, but **we are not sure it is right**" if has_hr else "Not read reliably"
        rhythm_cell = "Not read reliably"
    else:
        hr_cell = "Not given: the read looks unreliable"
        rhythm_cell = "Not given: the read looks unreliable"
    return hr_cell, rhythm_cell


def patient_explanation(light, hr, reasons=None, page_found=True, no_output=False, pr_ms=None, rr_cv=None, axis_deg=None):
    """MAIN output. light: GREEN / AMBER / RED. hr: heart rate in bpm or NaN. reasons: the traffic light's reason strings. pr_ms: PR interval in ms or None/NaN. Returns markdown."""
    light, has_hr, uneven = _state(light, hr, reasons, no_output)
    show_pr = pr_shown(light, pr_ms, page_found, reasons, rr_cv)
    show_axis = axis_shown(light, axis_deg, page_found)
    hr_cell, rhythm_cell = _cells(light, hr, has_hr, uneven)
    out = ["### Your ECG photo, in plain words"]
    if light == "GREEN":
        bullets = [f"- **Heart rate:** {hr_cell}.", f"- **Heart rhythm:** {rhythm_cell}."]
        if show_pr:
            bullets.append(f"- **PR interval:** about **{pr_ms:.0f} ms**. {PR_NOTE}")
        if show_axis:
            bullets.append(f"- **QRS axis:** about **{axis_deg:.0f} degrees**. {AXIS_NOTE}")
        out.append("**What we read**\n\n" + "\n".join(bullets))
        out.append("**How sure we are**\n\nThe photo was clear enough for the tool to read the page, and its checks found no sign of a failed read. So the heart rate is probably right. This is not a guarantee.")
    elif light == "AMBER":
        out.append(f"**What we read**\n\n- **Heart rate:** {hr_cell}.")
        out.append("**How sure we are**\n\nSome of the tool's checks looked unusual, so please do not rely on this result.")
    else:
        why = "The tool found no ECG in the picture." if no_output else "The tool's checks found signs of a failed or unreliable read."
        if not page_found:
            why += " The edges of the page were not found, so the photo was used as it is."
        out.append("**What we read**\n\n**We could not read this photo reliably, so we are not giving a heart rate or any comment on your heart.**")
        out.append(f"**How sure we are**\n\n{why}")
    unmeasured = ["P wave"] + ([] if show_pr else ["PR interval"]) + ["QRS complex", "QT interval", "ST segment", "T wave"] + ([] if show_axis else ["axis"])
    out.append("**What we did not check**\n\nThis tool did not measure the " + ", ".join(unmeasured[:-1]) + " or " + unmeasured[-1] + ", and this main result does not look for any heart condition (the separate research tab \"Heart health assessment\" checks a few ECG patterns, with its own tests). "
               "Those measurements are not available yet, because they have not passed our own accuracy checks. "
               "**A normal heart rate does not mean a normal ECG or a healthy heart.**")
    nxt = "Please show your original ECG to a doctor." if light == "GREEN" else (
        f"Please have a person look at the original ECG. {TIPS}" if light == "AMBER" else f"Please take a new photo, or show the original paper ECG to a doctor. {TIPS}")
    out.append(f"**What to do next**\n\n{nxt} {URGENT}")
    out.append("*Open \"What an ECG shows (general information)\" below to learn what each ECG measurement means.*")
    out.append(FOOTER)
    text = "\n\n".join(out)
    return SAFE_FALLBACK if check_wording(text) else text


def general_information(light, hr, reasons=None, no_output=False, pr_ms=None, page_found=True, rr_cv=None, axis_deg=None):
    """CLOSED section text: parameter table (meaning + what this tool got from the photo) and a general list of what an ECG can help doctors find."""
    light, has_hr, uneven = _state(light, hr, reasons, no_output)
    hr_cell, rhythm_cell = _cells(light, hr, has_hr, uneven)
    pr_cell = f"About **{pr_ms:.0f} ms** (rough estimate; typical difference from hospital software about 12 ms in our tests)" if pr_shown(light, pr_ms, page_found, reasons, rr_cv) else NOT_MEASURED
    axis_cell = f"About **{axis_deg:.0f} degrees** (rough estimate; within 30 degrees for about 95 in 100 photos in our tests)" if axis_shown(light, axis_deg, page_found) else NOT_MEASURED
    rows = ["| Parameter | What it tells doctors | From your photo |", "|---|---|---|"]
    for name, meaning in PARAMS:
        val = hr_cell if name == "Heart rate" else rhythm_cell if name == "Heart rhythm" else pr_cell if name == "PR interval" else axis_cell if name == "Axis" else NOT_MEASURED
        rows.append(f"| **{name}** | {meaning} | {val} |")
    text = ("#### The nine ECG parameters\n\n" + "\n".join(rows)
            + "\n\n#### What an ECG can help doctors find (general information, not a result for you)\n\n"
            + "\n".join(f"- {x}" for x in CAN_FIND)
            + "\n\nThis main result did not look for any of these; the separate research tab checks only a few ECG patterns. An ECG alone cannot confirm a condition: doctors also use your history, an examination, blood tests and sometimes scans. "
              "**A normal heart rate does not mean a normal ECG or a healthy heart.**")
    return "" if check_wording(text) else text
