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
RISK_UNAVAILABLE = ("Cardiac risk assessment: not available. We tested whether the ECG can estimate the chance of death within a few years, using an open dataset that follows patients over time (two attempts, rules written beforehand). "
                    "Neither attempt met our rules, and the estimate followed age more than the ECG, so no risk level or percentage is shown. An ECG alone cannot predict a person's overall heart risk.")
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
