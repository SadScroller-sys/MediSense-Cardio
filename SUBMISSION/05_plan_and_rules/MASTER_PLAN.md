# MASTER PLAN: MediSense-Cardio, from now to the review (Nov 17 to 21, 2026)

Written 2026-11-04 evening, before any result from the extension run exists. This replaces `docs/analysis_plan_150.md` (kept as history).
Anything changed after data arrive goes into `docs/analysis_plan_changes.md` with a date and a reason, and is labelled exploratory.

## 1. The project in three sentences
We damage computer-drawn ECG pages (6 damage types) and measure whether Open-ECG-Digitizer then gives wrong heart rates and intervals.
We count "false reassurance" (a normal-looking value when the truth is abnormal). We test whether the picture alone can warn before the digitiser runs.
It is a small, simulated, one-digitiser stress test, and every document must say so.

## 2. Where we are
- Done: first sweep of 50 recordings (31 versions each); held-out detector test (AUC 0.607); literature review sections A to G; reference checks
  (heart rate fine; PR and QRS unreliable; QT and QTc moderate at best); PTB-XL+ downloaded; extension designed (+100 recordings, 150 total).
- Running: extension notebook on Colab (1,300 images, about 7 h, started the evening of Nov 4).
- Found: the digitiser is not repeatable between runs (the same images gave 163 unreadable in sweep 1 and 30 in sweep 2; where both gave a heart rate, 98% identical).

## 3. Phases and dates
| Phase | What | Who | When |
|---|---|---|---|
| 1 | Main extension run finishes; verify Drive saves; download results | you, then me | Nov 5-6 |
| 2 | **Bridge run**: re-digitise 12 of the first 50 recordings (the 6 that flipped between sweeps + 6 others) in the new environment, 13 versions each (156 images, about 1 h) | me builds, you run | Nov 6 |
| 3 | Optional: 5-10 real phone photos of printed pages (I prepare the pack; you print and photograph) | you | by Nov 8 |
| 4 | Analysis by section A, B, C, D, E, G (rules in section 4) | me; you say "go ahead" after each | Nov 7-9 |
| 5 | **Freeze**: all numbers into `results/FINAL_NUMBERS.md`. No new analyses after this | both | Nov 10 |
| 6 | Papers (IEEE + journal), deck + pptx + online deck, diary, team report, all from FINAL_NUMBERS.md | me | Nov 11-14 |
| 7 | Title confirmed with your guide; rehearse the hard questions | you + me | Nov 12-16 |
| 8 | Website (plan Phase 4): only if phases 1-5 are done by Nov 10 | me | optional |

## 4. Analysis rules (fixed now)
**Data roles.** First 50 recordings = development set (already seen). New 100 = held-out replication **in the same pool** (not external).
Comparisons across both use levels 3 and 5 only. Unit of analysis = the recording; intervals by Wilson (simple rates) or recording-level bootstrap (pooled).

**Outcomes.** (a) *No output*: the digitiser gave no heart rate. (b) *Wrong heart rate*: output exists and |digitised - reference| > 5 bpm (secondary: > 10 bpm). The confirmatory
outcome is (b). (a) is reported separately because it changed between sweeps. Reference = detector on the 100 Hz record the page was drawn from. A recording is
*reference-uncertain* if its 100 Hz and 500 Hz references differ by more than 5 bpm. A recording is *flagged* if PTB-XL has any of baseline drift, static noise, burst noise,
electrode problems, extra beats, pacemaker. A recording is *unreliable* (excluded and listed) if more than 20% of its versions give no output.

**Questions and verdict rules.** All verdicts are worded "in the simulation, within these six damage types". A verdict must hold both with and without reference-uncertain recordings.
- **C1, which damage causes wrong heart rates?** On the new 100 at level 5: resolution highest and at least 20%; blur second and at least 10%; JPEG, brightness, grid fading below 10%;
  rotation at most 15%. Level 3 is reported alongside. The breaking point (smallest level at least 10%) comes from the first 50 only.
- **C2, is the background failure the recording?** Descriptive, no pass/fail. Among unflagged recordings: rates with intervals for rotation, JPEG, brightness, grid fading at level 5 and for clean images.
  "Consistent with the recording hypothesis" if each point estimate is at most 5% (rotation at most 10%).
- **C3, does the photo-quality detector discriminate?** Train on the first 50, score once on the new 100; same five scores, same model, target = wrong heart rate (>5 bpm). "Discriminates within these six
  damage types" only if AUC is at least 0.70 and the lower end of its 95% interval is above 0.60. **Inconclusive** if the new 100 hold fewer than 100 wrong readings. **Ceiling-limited** (not "fails") if the oracle
  (told the exact damage type and level) is itself below 0.70. Always reported with: the oracle, the best single score, leave-one-damage-type-out, the swapped direction (train on new 100, test on first 50),
  cross-validation on all 150 grouped by recording, and the coverage curve (flag 10, 20, 30% of photos: share of wrong readings caught, wrong-reading rate among kept photos). The word "usable" is not used.
- **Bridge rule:** if more than 5% of images change their bad/no-output label between sweep 2 and the bridge run, all comparisons that pool the first 50 with the new 100 (including C3) are demoted to exploratory.

**Exploratory (labelled as such).** Aligned SNR by damage and level; SNR vs heart-rate error; flagged vs unflagged effect; QT and QTc by the multi-lead continuous-wavelet method on the saved 12-lead signals
(PR and QRS are not analysed); QTc false reassurance by Fridericia (Bazett as sensitivity), described as "by this method"; heart-rate false reassurance (descriptive only, rare); detector calibration and
continuous-target correlation; standard no-reference quality baseline; real-photo check if photos exist.

**Disclosure of what was tuned after seeing the first 50:** the rotation allowances (15% and 10%), reporting level 3, the "no output" split, the bridge run.

## 4b. Complete analysis inventory (final; nothing is added after the freeze except into the changes log, as exploratory)
C = confirmatory (has a verdict rule in section 4); E = exploratory (reported, not judged).

| # | Analysis | Section | Type |
|---|---|---|---|
| 1 | Wrong heart rate (>5 bpm, output exists) by damage type and level, Wilson intervals, new 100 and all 150 | C | C (C1) |
| 2 | Same, level 3 beside level 5; breaking point from first 50 only | C | E |
| 3 | Unflagged recordings only: rates at level 5 and clean | C | E (C2, descriptive) |
| 4 | Verdicts repeated with and without reference-uncertain recordings | B | C (condition) |
| 5 | Five-outcome table by damage type and level (correct normal, correct abnormal, false alarm, false reassurance, no answer); normal HR range 60 to 100 bpm, described as a convention | C | E (descriptive) |
| 6 | No-output rate by damage type and level | C | E |
| 7 | Paired Wilcoxon signed-rank of heart-rate error against each image's own clean version, Holm-corrected; Bland-Altman bias and limits of agreement per level | A, C | E |
| 8 | Dose-response: monotonic trend of error with level for each damage type | C | E |
| 9 | Subgroups: wrong-reading rate by sex, age band, diagnosis group, true heart-rate range | B, C | E |
| 10 | Heart-rate detector sensitivity: second peak detector on the saved signals (new 100 and bridge) | B | E |
| 11 | Reference checks on the new 100: heart rate at 100 vs 500 Hz; QT and QTc by the multi-lead continuous-wavelet method vs 12SL on the original signal | B | E |
| 12 | QT and QTc preservation (digitised vs original, same method); QTc false reassurance by Fridericia, Bazett as sensitivity, "by this method" | B, C | E |
| 13 | Aligned SNR by damage type and level; SNR vs heart-rate error; cases with acceptable SNR but wrong heart rate | A | E |
| 14 | Sweep 1 vs sweep 2: output availability and label flips (done 2026-11-04: 163 vs 30 unreadable) and the bridge run | A | E (feeds the bridge rule) |
| 15 | Five image scores: correlation with error, refreshed on 150 recordings | D | E |
| 16 | Detector on first 50, scored once on new 100 (AUC, interval), with oracle, best single score | D | C (C3) |
| 17 | Detector extras: leave-one-damage-type-out, swapped direction, grouped cross-validation on all 150, continuous-target correlation | D | E |
| 18 | Gate variant using the digitiser's own output (count of unreadable leads) vs photo-only; standard no-reference quality baseline | D | E |
| 19 | Coverage curve: flag the top 10, 20, 30% of photos: wrong readings caught, wrong-reading rate among kept photos | E | E |
| 20 | Detector calibration; sample-size statement against Riley's criteria | G | E |
| 21 | Reporting checklist: CLAIM items met and not met | G | E |
| 22 | Real-photo check (only if photos exist): digitise them, compare with our simulated damage ranking | A | E |

Cannot be done and stated as limits: combined damage (several types at once), PR and QRS as clinical measures, human response to a flag, anything about real photos beyond item 22.

## 5. What we will and will not claim
- Will claim: low resolution and blur cause wrong heart rates in this simulation; most other failures follow the recording, not the damage; the detector's performance and ceiling as measured; the digitiser's run-to-run
  variation as measured; our reference intervals are method-dependent.
- Will not claim: clinical accuracy of PR, QRS or QTc; any statistical guarantee for the gate; that the gate helps patients (the human response to a flag is untested); that results hold for real phone photos.
- Limits in every document: simulated damage on computer-drawn pages from the generator family the digitiser was trained on; one digitiser (versions recorded for the new run only); 150 recordings;
  six damage types without stains, creases, glare or perspective; heart-rate reference depends on sampling rate for 16% of recordings.

## 6. Decisions only you can make
1. Project title (confirm with your guide by Nov 12).
2. Real phone photos: yes or no.
3. Undo the paper edits made earlier on Nov 4, or leave them (papers are not touched until phase 6).
4. Website: only if the freeze is on time.
5. Anything in section 4 you disagree with, before data arrive.

## 7. Main risks
Colab run fails or disconnects (resume; a bad day costs a day). The bridge run shows large run-to-run differences (then pooled comparisons are exploratory; the first-50 findings still stand).
Intervals do not improve (they stay a side result). Time: if phase 4 slips past Nov 10, the website is dropped first, then the real-photo check.
