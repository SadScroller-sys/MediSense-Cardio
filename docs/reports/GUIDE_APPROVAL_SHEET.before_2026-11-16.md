# MediSense-Cardio: sheet for the guide (thresholds, rules, wording, decisions)

Prepared 2026-11-15. Every pass rule below is **the team's proposal and has not been approved**. Each rule was written down before the result it judges (`docs/plan/analysis_plan_changes.md`). Numbers come from `results/FINAL_NUMBERS.md`. Research prototype, not a medical device.

## 1. Measurements: rule, result, what the app does

| Measurement | Pass rule (proposed) | Result | App | Guide: approve? |
|---|---|---|---|---|
| Heart rate | "wrong" = more than 5 bpm from the true rate (monitor tolerance of 5 bpm or 10%) | clean pages: limits of agreement -3.2 to +3.1 bpm; resolution 5 and blur 5: wrong 47% and 17% | shown (GREEN or AMBER light) | |
| PR interval | typical error at most 20 ms, at least 90% within 40 ms, bias at most 10 ms, at least 90% with a value | 7.3 ms (held-out pages), 12.0 ms (new phone photos), met on straightened photos only; atrial fibrillation guard added | shown for GREEN, straightened, steady beat spacing | |
| Frontal QRS axis | median error at most 10 deg, at least 90% within 30 deg, mean error at most 10 deg, category agreement at least 90% | 4.4 deg, 95% within 30 deg on straightened photos; right-axis detection not shown | shown as degrees for GREEN, straightened | |
| QRS duration | typical error at most 10 ms, at least 90% within 20 ms, bias at most 5 ms, slope at least 0.8, wide-QRS tail | 3 rule-based attempts failed; learned model passed drawn pages (6.4 ms) but failed photos (slope 0.65) | **not measured** (second attempt pending) | |
| QT / QTc | typical error at most 20 ms (QTc 25), at least 90% within 40 ms (QTc 50), bias at most 10 ms, slope at least 0.8, long and short QT tails | 3 rule-based attempts failed; learned model: drawn pages close, photos failed (slope 0.50) | **not measured** (second attempt pending) | |
| P wave, T wave, ST segment | no reliable reference (the two commercial algorithms disagree) | not attempted | not measured | |

**Question 1:** are these thresholds acceptable? Is the slope rule (at least 0.8, so that long QT is not read as normal) acceptable?

## 2. ECG-pattern findings (heart health model)

- Trained on public PTB-XL labels (normal, infarction, ST/T change, conduction disturbance, hypertrophy, atrial fibrillation). **These are ECG patterns, not diagnoses and not cardiac risk.**
- **Rule (proposed):** a pattern is shown for drawn pages if on at least 20 positives its AUROC is at least 0.80 (lower interval end above 0.70); for phone photos also at least 20 positive photos and AUROC at least 0.75 (and at least 0.70 on real printed-paper photos for the second model). A percentage is shown only if calibration error on photos is at most 0.10. Otherwise "not available".
- **Result (model 1, one test):** shown on photos: infarction pattern 0.857, ST/T change 0.865, conduction disturbance 0.875. Hypertrophy failed (0.636). Atrial fibrillation could not be tested on photos. On photos a "not found" misses 14 to 28 in 100 true patterns and a "found" is wrong for 16 to 24 in 100 photos without the pattern. No percentage is shown (calibration on photos was poor).

**Question 2:** are these rules acceptable? Is it acceptable to name the output "ECG pattern found: medical evaluation advised"?

## 3. Risk

- A true cardiac-risk estimate needs a dataset linking ECGs to later outcomes. PTB-XL has none; the app shows "cardiac risk: not available" and says why.
- Candidate: **CODE-15%** (open, CC-BY 4.0; 345,779 ECGs; death and time to death on each patient's first exam; all-cause mortality). A 2024 benchmark reports about 0.80 to 0.82 AUROC for 1-year mortality from the ECG alone, and a loss of 0.1 to 0.15 when moving between sources.
- A pilot would estimate **ECG-estimated all-cause mortality risk (research)**, not "heart disease risk". Outcome validation on photos is impossible (no follow-up for our photos); only a check of how much the predicted risk changes between an original and a digitised ECG.

**Question 3:** may a pilot risk graph appear in the app with that name, with Low / Moderate / High cut-offs on absolute probability chosen by you (for example under 1%, 1 to 5%, over 5% in 5 years)? If the pilot does not pass, the box stays "not available".

## 4. Wording rules
Never a diagnosis; never "healthy" or "nothing to worry"; never a risk level unless a validated model passed; always "a normal-looking ECG does not exclude heart disease", "not a medical device" and a doctor visit for symptoms. Automatic checker plus 33 tests.

## 5. Other decisions
- Paper: venue and title (conference vs patent; the final review needs one outcome).
- Report format (the Electronics sample is the only one we have), ratification before the PDF.
- Is a website expected? (A local demo exists and is used for the review.)
- Who rechecks three numbers (`reproducibility/SECOND_PERSON_CHECK.md`)?

| Sign-off | Name | Date | Signature |
|---|---|---|---|
| Guide | | | |
