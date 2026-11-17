Subject: Capstone: QT interval from ECG photos, one question about our pass rule

Dear Sir/Madam,

A short update on one part of our project, with one question where we need your advice.

**What we did.** We tried to measure the QT interval from the digitised ECG and compare it with the hospital software's value (12SL, from PTB-XL+). Before running anything we wrote down a pass rule, so that we could not adjust it after seeing the result:
- the typical (median) error must be 20 ms or less,
- at least 90% of readings must be within 40 ms of 12SL,
- the average bias must be within 10 ms,
- at least 90% of recordings must give a value.

**Results.** Our first method (NeuroKit2) failed: typical error 36 ms, and only 70% of recordings gave a value. We then built a better method, developed on 50 recordings only, and tested it once on 100 other recordings:

| Test | Typical error | Within 40 ms | Result |
|---|---|---|---|
| 100 held-out recordings, original signal | 7.8 ms | 92% | meets the rule |
| 100 held-out recordings, digitised page | 13.5 ms | 92% | misses: bias +10.5 ms (limit 10) |
| 100 new phone photos, straightened | 19.5 ms | 84% | misses: needs 90% |

So it is close, but it does not meet our rule. We did not change the method or the thresholds after seeing the held-out result. In the demo, QT is shown as "not measured", and we say so.

**The same process for PR and QRS.** We applied the same procedure (rule written first, method developed on 50 recordings, one test on 100 held-out recordings, one confirmation on 100 new phone photos). The pass rule for PR is 20 ms typical error, 90% within 40 ms, bias within 10 ms; for QRS it is 10 ms, 90% within 20 ms, bias within 5 ms (one pixel of our images is about 5 ms, so QRS is close to the limit of what a photo can show).

| Parameter | Held-out digitised pages | New phone photos (straightened) | Result |
|---|---|---|---|
| PR interval | 7.3 ms typical error, 97% within 40 ms | 12.0 ms, 95% within 40 ms | meets the rule (only after the photo is straightened) |
| QRS duration | 13.2 ms, 72% within 20 ms | 18.2 ms, 59% within 20 ms | does not meet |

**Update after a second attempt on fresh data.** We drew 100 new pages from recordings never used before, digitised them, and ran each test once. Results against the same rules:

| Parameter | 100 fresh pages | 100 phone photos (straightened) | Result |
|---|---|---|---|
| Frontal QRS axis (new) | 3.8 degrees typical error, 99% within 30 degrees | 4.4 degrees, 95% within 30 degrees | meets the rule |
| QT interval | 8.8 ms, 93% within 40 ms | bias -16.5 ms, 86% within 40 ms | meets on drawn pages, not on phone photos |
| QRS duration | 9.2 ms but only 74% within 20 ms | 12.9 ms, 69% | does not meet |

We also checked that the numbers are not just pulled toward the average: QT has a slope of 0.68 against the hospital value (we set 0.7 as the limit in advance), and QRS duration reads wide QRS about 45 ms too short, so we do not show either. The axis is shown as degrees only, with no words such as "left axis deviation".

**Our questions.**
1. Are these thresholds reasonable for a research prototype, or is there a standard tolerance for QT measurement that you would like us to use instead?
2. Is 12SL acceptable as the reference, or do you want us to compare with expert-marked intervals?
3. Is it acceptable to report QT as "close but not validated" and QRS duration as not validated, show only the parameters that passed (heart rate, PR interval, QRS axis), and keep the rest hidden in the demo?

The final review is on Friday 20 November, so we would be grateful for your advice before then.

Thank you,
[Your name]
[Team / register number]

Notes for the writer (delete before sending): the full numbers are in `results/FINAL_NUMBERS.md` section 10.5 and `results/analysis/SECTION_T.md`. The thresholds are our own proposal; this note does not claim the guide approved them.
