# MediSense-Cardio: sheet for the guide (thresholds, rules, wording, decisions)

Updated 2026-11-16 (final state before the review). Every pass rule below is **the team's proposal and has not been approved**. Each rule was written down before the result it judges (`docs/plan/analysis_plan_changes.md`). Numbers come from `results/FINAL_NUMBERS.md`. Research prototype, not a medical device.

## 1. Measurements: rule, result, what the app does

| Measurement | Pass rule (proposed) | Result | App | Guide: approve? |
|---|---|---|---|---|
| Heart rate | "wrong" = more than 5 bpm from the true rate (monitor tolerance of 5 bpm or 10%) | clean pages: limits of agreement -3.2 to +3.1 bpm; GREEN readings wrong 0.2% (2 of 917 real captures) but **2 of 19 on printed paper from another phone** | shown (GREEN or AMBER light); GREEN does not prove the rate is right | |
| PR interval | typical error at most 20 ms, at least 90% within 40 ms, bias at most 10 ms, at least 90% with a value | 7.3 ms (held-out pages), 12.0 ms (screen photos), 12.6 ms (22 printed-paper photos, 94% within 40 ms); atrial fibrillation guard added | shown for GREEN, straightened, steady beat spacing | |
| Frontal QRS axis | median error at most 10 deg, at least 90% within 30 deg, mean error at most 10 deg, category agreement at least 90% | 4.4 deg (screen photos), 6.3 deg and 91% within 30 deg (printed paper); right-axis detection not shown | shown as degrees for GREEN, straightened | |
| QRS duration | typical error at most 10 ms, at least 90% within 20 ms, bias at most 5 ms, slope at least 0.8, wide-QRS tail | 3 hand-made attempts failed; a network trained on public data passed fresh drawn pages (4.1 ms) but failed photos (slope 0.65; printed paper bias +7.6 ms) | **not measured (final)** | |
| QT / QTc | typical error at most 20 ms (QTc 25), at least 90% within 40 ms (QTc 50), bias at most 10 ms, slope at least 0.8, long and short QT tails | 3 hand-made attempts failed; the network failed even drawn pages (bias +12.4 ms) and photos (slope 0.54; short QT read 38 ms too long) | **not measured (final)** | |
| P wave, T wave, ST segment | no reliable reference (the two commercial algorithms disagree) | not attempted | not measured | |

**Question 1:** are these thresholds acceptable? Is the slope rule (at least 0.8, so that long QT is not read as normal) acceptable?

## 2. ECG-pattern findings

- **Main list (first network, trained on PTB-XL):** infarction pattern and ST/T change are shown on photos (AUROC 0.81 and 0.84 on 222 new photos), as "found" or "not found", never with a percentage. **Conduction disturbance failed on printed paper** (0.42, 5 positive photos) and is no longer shown; hypertrophy fails (0.75 on new drawn pages); atrial fibrillation cannot be tested on real photos. On photos a "not found" misses 2 to 3 in 10 true patterns.
- **Rule (proposed):** a pattern is shown for photos only if it has at least 20 positives, AUROC at least 0.80 (lower interval end above 0.70) on drawn pages, and AUROC at least 0.75 on photos (also on real printed-paper photos when we have at least 20 positive ones).
- **Extra block, research only (two more networks trained on public data only: A on PTB-XL, 16 codes; B on CODE-15%, 6 labels, 132,040 exams):** benchmark AUROC 0.98 to 0.995 (B). On our pages, 7 patterns passed the drawn-page rule; of the 8 network-and-finding pairs tested once on a positive-rich set of 120 pages, 6 passed on drawn pages and 5 on simulated photos; **no real photos with enough positives exist, so none is promoted** (the photo session was cancelled by decision). The patterns appear only in a collapsed "research only" block, as "possible pattern" or "not found", with a note. **Found after testing: with balanced thresholds, 49% of clean drawn pages and 72% of our real phone photos that had none of the patterns still got at least one flagged. We therefore set stricter thresholds from validation data only (specificity 0.97) and dropped one weak pattern (non-specific T wave), a POST HOC exception to our own rule that we ask you to note: clean items flagged fell to 18% (drawn pages) and 26% (phone photos), at the cost of sensitivity (for example 46 to 57 in 100 for hypertrophy and fascicular block).**
- Output wording: "ECG pattern found: medical evaluation advised"; the "none found" indicator is neutral grey and says "this does not mean the ECG is normal".

- **Fresh test on 266 new dataset pictures (set P), added 2026-11-17:** the six extra patterns were found on drawn pages with AUROC 0.90 to 0.98 but only 0.67 to 0.85 on simulated phone photos; **none met our rule, so none is promoted** (about 3 to 5 in 10 clean simulated photos still get a flag). QT retried on doctor-marked public data: accurate on held-out signals (12 ms) but not on digitised pictures (66 ms); QT and QRS stay not measured. Real photos are not part of the verdict.

- **Retrained networks, fresh sets Q and R, added 2026-11-17:** after retraining with stronger photo damage, **left bundle branch block and atrial fibrillation passed our rules on fresh dataset pictures** and are shown in the demo as validated findings, labelled "validated on dataset pictures, not on real phone photos". Set Q (160 pictures, tested once): LBBB passed (photos AUROC 0.84, 72 in 100 found, 8 in 100 false alarms), AF missed specificity by 0.7 points (89 instead of 90), LAFB failed sensitivity. Set R (120 new pictures, same frozen network, tested once): LBBB passed again (photos AUROC 0.81, 66 found, 6 false alarms per 100), AF passed (0.84, 71 found, 7 false alarms per 100). **AF passed only on its second test**, so it is less certain. LAFB and the other patterns stay research-only.

**Question 2:** are these rules acceptable, and may left bundle branch block and atrial fibrillation be shown as validated on dataset pictures only (AF passed on its second test)? Is the wording acceptable? **Question 3:** may the research-only block stay in the demo with its remaining false alarms (about 2 in 10 clean drawn pages and 3 to 5 in 10 clean simulated photos flagged), and do you accept the post hoc change of thresholds and the dropped pattern, or should it be hidden for the review?

## 3. Risk (final: not shown)

- A true cardiac-risk estimate needs a dataset linking ECGs to outcomes; PTB-XL has none. We used **CODE-15%** (open, CC-BY 4.0; all-cause mortality), named "ECG-estimated all-cause mortality risk (research)", never "heart disease risk".
- **Pilot 1 (1-year, ECG only): failed** (AUROC 0.713 against 0.799 for age alone; calibration slope 0.62; risk of a real printed photo not stable, 0.43).
- **Pilot 2 (5-year, ECG plus age, new sealed test): failed** (AUROC 0.833 but age alone 0.819; the ECG added +0.013, not significant; risk not stable on simulated photos). Proposed categories (Low under 5%, Moderate 5% to under 15%, High 15% or more) were never used.
- The app shows "cardiac risk: not available" and says why. Reported as a negative result in the report and the paper.

**Question 4:** do you agree to present the risk work as a negative result and show no risk graph?

## 4. Wording rules
Never a diagnosis; never "healthy" or "nothing to worry"; never a risk level unless a validated model passed; always "a normal-looking ECG does not exclude heart disease", "not a medical device" and a doctor visit for symptoms. Automatic checker plus 42 automated tests (rotation 3, health 20, explanation 19).

## 5. Other decisions
- **Printed paper from another phone** (friend's photos): straightening confirmed on 66 recompressed photos (31 to 15 bad, p = 0.0004), not on 22 straight full-size photos (3 to 2); the page finder needs a quarter turn for an upright phone (now automatic in the app).
- Paper: venue and title (conference vs patent; the final review needs one outcome). IEEE conference version ready (`docs/paper/`), not yet compiled by the team.
- Report format (the Electronics sample is the only one we have), ratification before the PDF. The official plagiarism report (Turnitin or the college tool) must be requested from you or the library; our own check found no run of 8 identical words in any source.
- Is a website expected? (A local demo exists and is used for the review.)
- Who rechecks the key numbers (`reproducibility/SECOND_PERSON_CHECK.md`; now also the new numbers 10.17 to 10.26)?

| Sign-off | Name | Date | Signature |
|---|---|---|---|
| Guide | | | |
