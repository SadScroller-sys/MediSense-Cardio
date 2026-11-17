# Patient explanation: wording rules (option 2, rule-based, no language model)

Status: DRAFT written 2026-11-13. It was not checked against the original project guide's allowed and forbidden list (section 8 of that guide is not in this repository). Please compare and correct it before the review.

## Purpose
After the demo recognises a photo, it explains in plain words what the tool read and what that could mean. It is the "bounded plain-language explanation with a non-diagnostic safety boundary" of `docs/plan/PLAN.md`. Every sentence comes from a fixed list in `demo/explain.py`. No sentence is generated.

## Layout (final form, 2026-11-13)
**Main output, four short parts:** (1) what we read, (2) how sure we are, (3) what we did not check, (4) what to do next.

**Closed section "What an ECG shows (general information)":**
- a table of the nine ECG parameters (heart rate, heart rhythm, P wave, PR interval, QRS complex, QT interval, ST segment, T wave, axis). Each row says what the parameter tells doctors (general information) and what this tool got from the photo;
- a general list of what an ECG can help doctors find (irregular heartbeat, signs of a heart attack, reduced blood supply, heart blocks, fast or slow heartbeat, thickened chambers, potassium or calcium changes), marked "general information, not a result for you", saying the tool did not look for any of these.

(History: an earlier version put the table in the main output. It was moved into the closed section after a review against standard practice: measurements stay hidden until they are validated, and general teaching must not look like a result.)

## What the tool may claim to have measured
- **Heart rate** (from lead II), a **rough beat-spacing check** (from the traffic light's reasons), and, since 2026-11-14, the **PR interval**.
- **PR interval: shown as a number only, no verdict.** Conditions (all must hold, enforced in `demo/explain.py` and tested): the light is GREEN; the photo was straightened (the page was found); the value is between 50 and 400 ms; the traffic light's check did NOT report irregular beat spacing, AND the beat-spacing variation (rr_cv) is known and at most 0.12 (safeguards added 2026-11-14: 12SL finds no PR for 95% of atrial fibrillation recordings because there are no P waves, yet our method still gave a number for all 6 such held-out pages; the first guard catches 4 of 6, the second all 6 pages and all 8 such phone photos in our data, at the cost of hiding PR on about 15% of normal-rhythm photos; a precaution calibrated on 14 cases, not a validated filter; the frequent minor note 'one beat gap is shorter' alone does not hide PR). It is never shown for AMBER, RED, "no output", an unstraightened photo or an implausible value. The sentence is: "PR interval: about X ms. This is a rough estimate by our method; in our tests it differed from hospital software by about 12 ms on a typical photo. Please ask your doctor what it means." The words "normal", "prolonged", "shortened", "abnormal" and "within normal limits" are blocked for intervals.
- **Why PR may be shown (evidence):** it met the rule written in advance (typical error <= 20 ms, 90% within 40 ms, |bias| <= 10 ms, 90% with a value) on the held-out 100 recordings (7.3 ms on digitised pages) and on 100 new phone photos once straightened (12.0 ms, 95% within 40 ms); see `results/FINAL_NUMBERS.md` section 10.6. The rule is the assistant's proposal and has NOT been approved by the guide. It does not hold for photos that were not straightened (only 67% gave a PR) or for heavy blur and very low resolution.
- **Frontal QRS axis: shown as a number of degrees only, no verdict word** (never "left axis deviation", "normal axis" and similar; blocked automatically). Conditions (enforced in `demo/explain.py`, tested): the light is GREEN, the photo was straightened (the page was found) and a value was measured. The sentence is: "QRS axis: about X degrees. This is a rough estimate by our method; in our tests it was typically within about 5 degrees of hospital software, and within 30 degrees for about 95 in 100 photos. Please ask your doctor what it means." Evidence: it met the rule written in advance on 100 fresh pages (3.8 degrees typical error, 99% within 30 degrees) and on 100 phone photos once straightened (4.4 degrees, 95% within 30 degrees, 92% category agreement); `results/FINAL_NUMBERS.md` section 10.8. Known limit: one recording (P13, true 148 degrees) was read as -95 degrees, and right-axis detection is not shown to work (no right-axis recording in the fresh test); the rule is the assistant's proposal and is not approved by the guide. It does not hold for photos that were not straightened.
- **Every other parameter says "Not measured by this tool".** QRS duration and QT were tried again on fresh data (Section V) and are NOT validated: QT meets the rule on fresh drawn pages (8.8 ms) but not on phone photos (bias -16.5 ms) and its slope against 12SL is 0.68 (limit 0.7: it shrinks long and short values toward the middle); QRS duration reads recordings with a true QRS of 120 ms or more about 45 ms too short, which would show a wide QRS as normal, so it must never be shown. NeuroKit2 intervals were unusable (section 10.3). If a later method passes a rule written in advance (including the slope check), that row can be shown in the same way; no other row changes.
- The conditions in the general list are never attached to the photo.

## By light

| Light | Heart rate row | Rhythm row | PR interval row (and Axis row) | Meaning given |
|---|---|---|---|---|
| GREEN | Number and its resting range | Uneven spacing noted, or "none noticed by our rough check" | A number (straightened photo, 50 to 400 ms) or "Not measured by this tool" | Probably reliable, not a guarantee |
| AMBER | Number with "we are not sure it is right" | Not read reliably | Not measured by this tool | Do not rely on it |
| RED | "Not given" | "Not given" | Not measured by this tool | Nothing is said about the heart |
| No output | "Not given" | "Not given" | Not measured by this tool | Nothing is said about the heart |

The closed general-information section is available for every light.

## Allowed wording
- "your heart rate is about X beats per minute"
- "inside the usual resting range (60 to 100)", "slow (below 60)", "fast (above 100)"
- "the photo was / was not clear enough to read"
- "this tool cannot tell which", "please show your original ECG to a doctor"
- general information about what an ECG can help doctors find, ONLY when marked "general information, not a result for you"
- "Not measured by this tool"
- "PR interval: about X ms" with the rough-estimate sentence above, only under the PR conditions
- "QRS axis: about X degrees" with the rough-estimate sentence above, only under the axis conditions
- "a normal heart rate does not mean a normal ECG or a healthy heart" (the only allowed use of "normal ECG" and "healthy")
- "this tool cannot diagnose anything", "not a medical device"

## Forbidden wording (blocked automatically)
- "your ECG is / looks / appears normal (fine, healthy)"
- "you are healthy / fine / OK / safe"
- "nothing to worry about", "no need to see / visit / consult a doctor"
- "you have ..." (except "if you have ...", used for symptoms)
- "dangerous", "life-threatening"
- advice to take, stop or start medicine
- any diagnosis, or a named condition, for an uploaded photo (the general list is information, never a finding)
- a value for any parameter that this tool did not measure (everything except heart rate, the beat-spacing check and PR under its conditions)
- any verdict on the axis: "left axis", "right axis", "axis deviation", "normal axis", "extreme axis"
- any verdict on an interval: "normal", "prolonged", "shortened", "abnormal", "within normal limits", "too long", "too short"

## How it is enforced
1. Fixed sentences only (`demo/explain.py`).
2. `check_wording()` scans every patient text for the forbidden patterns after removing the exact safe phrases above. If it ever finds one, the demo shows a generic safe message instead.
3. `demo/tests/test_explanation.py` (19 tests) runs every light, boundary heart rates (39.9, 40, 59.9, 60, 100, 100.1, 150, 150.1), PR values (missing, 49.9, 50, 120, 150, 250, 400, 400.1) and missing values through the checker, and checks that PR appears only under its conditions.
4. `demo/axis_deg.py` runs the exact method of Section W (`results/analysis/sectionW_frozen.json`); it reproduces the tested values exactly (checked on 10 fresh pages).
5. `demo/pr_interval.py` runs the exact method and frozen offset of Section U (`results/analysis/sectionU_frozen.json`); it reproduces the tested values exactly (checked on 8 held-out pages).

## Limits
- This is a keyword check on fixed sentences. It protects the fixed list from edits that add forbidden words. It is not a test of a language model.
- It has not been tested with real patients or with a second reader. No claim is made that the explanation helps patients (the one clinician study found shows abstention can even raise missed problems).
- The presenter view for the six test samples also shows the PTB-XL label of the source recording. That is for explaining the demo and is never shown for an uploaded photo.


## Update 2026-11-15
The guide asked for a separate heart health assessment module (`demo/health/`). The MAIN result still never names a condition; its sentences now say that the main result did not look for conditions and that the separate research tab checks a few ECG patterns. The module has its own, stricter wording rules and tests (`demo/health/wording.py`, `demo/tests/test_health.py`): it may say a research model found an ECG PATTERN, never a diagnosis, never a risk level, never reassurance.
