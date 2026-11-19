"""Wording rules of the heart health module. The older demo wording (demo/explain.py) never names a condition; the guide's new request asks for supported ECG findings,
so this module has its OWN list: it may say that a research model found an ECG PATTERN, but it must never diagnose, never give a risk level, never reassure.
Research prototype. Not a medical device."""
import re

SAFE_PHRASES = [
    "a normal-looking ecg does not exclude heart disease",
    "it is not a diagnosis",
    "not a medical diagnosis",
    "does not replace a doctor or a cardiologist",
    "this is a pattern in the picture, not a diagnosis",
    "no risk level or percentage is shown",
    "no validated risk level or percentage is shown",
    "not a diagnosis",
    "not diagnoses",
    "not a medical device",
    "cannot diagnose anything",
    "an ecg alone cannot predict a person's overall heart risk",
]

FORBIDDEN = [
    (r"\byou have\b", "names a condition for the person"),
    (r"\byou('re| are) (healthy|fine|ok|okay|safe|at risk|in danger)\b", "judges the person"),
    (r"\b(low|moderate|medium|high) (cardiac |heart |cardiovascular )?risk\b", "gives a risk level (no validated risk model exists)"),
    (r"\brisk (score|level|category|of (a )?(heart attack|stroke|death))\b", "gives a risk result"),
    (r"\bnothing to worry\b|\bno need to (see|visit|consult|worry)\b|\bguarantee", "false reassurance"),
    (r"\b(healthy heart|heart is healthy|heart is fine|you are fine)\b", "false reassurance"),
    (r"\bdiagnos", "diagnosis wording outside the safe phrases"),
    (r"\b(dangerous|life-threatening|emergency)\b", "alarming claim"),
    (r"\b(take|stop|start|increase|reduce) (a |an |your |the |some )?(medicine|medicines|medication|pill|pills|tablet|tablets|drug|drugs)\b", "medicine advice"),
    (r"\breplace[s]? (a |your )?(doctor|cardiologist)\b", "claims to replace a doctor"),
]


def check_wording(text):
    """List of (reason, matched text); empty = the text keeps the safety boundary."""
    t = text.lower()
    for s in SAFE_PHRASES:
        t = t.replace(s, " ")
    return [(why, m.group(0)) for pat, why in FORBIDDEN for m in re.finditer(pat, t)]


DISCLAIMER = ("This is an AI-assisted research assessment, not a medical diagnosis. It is not a medical device and does not replace a doctor or a cardiologist. "
              "A normal-looking ECG does not exclude heart disease, and an ECG alone cannot predict a person's overall heart risk.")
RISK_UNAVAILABLE = ("Cardiac risk assessment: not available. We tested whether the ECG can estimate the chance of death within a few years, using an open dataset that follows patients over time (three attempts, rules written beforehand). "
                    "None of the attempts met all of our rules (the third missed only the calibration rule), and the estimate follows age more than the ECG, so no validated risk level or percentage is shown; the research-only box below shows an exploratory range. An ECG alone cannot predict a person's overall heart risk.")
RETAKE = ("The photo is not clear enough for a reliable read. Please take a new photo: hold the phone straight above the page, keep the whole page in the picture, "
          "use even light and make sure the picture is in focus.")
NEXT_STEPS = {
    "retake": RETAKE + " Please also show the original ECG to a doctor.",
    "pattern": "Please show this ECG and this result to a doctor for medical evaluation. Get medical help straight away for chest pain, fainting, breathlessness or a racing heartbeat.",
    "none": "Please still show the original ECG to a doctor: a normal-looking ECG does not exclude heart disease. Get medical help straight away for chest pain, fainting, breathlessness or a racing heartbeat.",
    "unavailable": "Please show the original ECG to a doctor. Get medical help straight away for chest pain, fainting, breathlessness or a racing heartbeat.",
}
FINDING_NAMES = {
    "NORM": "Normal-looking pattern",
    "MI": "Pattern linked to a heart attack (myocardial infarction)",
    "STTC": "ST/T-wave change pattern",
    "CD": "Conduction disturbance pattern (e.g. bundle branch block)",
    "HYP": "Hypertrophy pattern (thickened heart chambers)",
    "AF": "Atrial fibrillation / flutter pattern",
}

# Extra patterns from the two public-data networks A (PTB-XL, 16 codes) and B (CODE-15%, 6 labels): research-only, shown ONLY for findings that passed on clean computer-drawn pages
# (results/find2_A/status.json, results/find2_B/status.json). None could be tested on phone photos (too few positive photos), so they never change the main indicator and carry no percentage.
EXTRA_NAMES = {
    "A:ASMI": "Pattern linked to an anteroseptal heart attack",
    "A:LVH": "Left ventricular hypertrophy pattern (thickened heart muscle)",
    "A:LAFB": "Left anterior fascicular block pattern (a conduction change)",
    "A:IRBBB": "Incomplete right bundle branch block pattern (a mild conduction change)",
    "B:AF": "Atrial fibrillation pattern (irregular rhythm)",
    "B:LBBB": "Left bundle branch block pattern (a conduction change)",
    "B:1dAVb": "First-degree AV block pattern (a slow electrical signal between the heart's chambers)",
}
EXTRA_NOTE = ("Research-only extra patterns: these passed our tests on clean computer-drawn pages but did not meet our rules on simulated phone photos in a fresh test, so a result is a hint to show a doctor and not a validated finding. "
              "The decision thresholds are strict (set on validation data to give about 3 false alarms in 100 clean recordings per pattern), but because several patterns are checked at once, about 2 in 10 clean drawn pages and 3 to 5 in 10 of our simulated phone photos that had none of these patterns still had at least one flagged, so a single flag is still weak evidence. "
              "No percentage is shown, and these patterns do not change the indicator above.")


def risk_exp_text(est):
    """Text of the exploratory 5-year estimate (risk pilot 3). It must pass check_wording: no risk level, no risk category, no reassurance, no diagnosis."""
    lo, hi = int(round(est["low"] * 100 / 5.0) * 5), int(round(est["high"] * 100 / 5.0) * 5)
    return (f"Exploratory research estimate, not validated: in our research data, about {lo} to {hi} in 100 people of this age with an ECG like this died within 5 years (our rough group: {est['group']}). "
            + ("The age was estimated from the ECG (typical error about 9 years), so the range is wider. " if est.get("estimated_age") else "")
            + "These numbers come from a research group chosen for having died or been followed for a full 5 years, so they run higher than for people in general. "
            "On our test pictures this range contained the value of the clean ECG for about 9 in 10 drawn pages but only about 2 in 3 photos, so with a photo the real uncertainty is larger than shown. The model did not meet our own calibration rule, "
            "was not tested on real phone photos, and mostly reflects age. It is not a prediction for you, not a medical diagnosis and not medical advice.")


def mi_percent_text(p_cal):
    """Text of the heart-attack-pattern percentage (second calibration attempt on the fresh set S). It is the chance the ECG shows the PATTERN, never the chance of a heart attack."""
    n = int(round(p_cal * 100))
    return (f"About {n} in 100 pictures like this one show the heart-attack pattern in our test data (typical error about 4 points). This is the chance that this ECG shows the pattern, not a chance of a heart attack, and not a diagnosis. "
            "It was estimated from simulated phone photos of dataset recordings, calibrated to the PTB-XL population (about 25 in 100 records there have the pattern), on a second attempt after the first one missed our rule; "
            "it was not tested on real phone photos. Please show the ECG to a doctor.")
