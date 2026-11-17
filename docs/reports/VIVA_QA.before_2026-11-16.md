# Viva question and answer sheet (MediSense-Cardio)

Written 2026-11-14. Simple words on purpose: say it the way it is written here. Every number comes from `results/FINAL_NUMBERS.md`. If a question is not covered here, say "we did not test that" instead of guessing.

## 0. The 60-second summary (learn this first)

"People send photos of ECGs. A program turns the photo back into a signal and measures it. We asked: when the photo is bad, do the numbers go wrong, can we warn the user, and which numbers are safe to show?
We used one open-source digitizer, unchanged. We found only very low resolution and heavy blur made the heart rate wrong a lot (47% and 17% of pages in the test). A warning made from the picture failed. A warning made from the digitized signal worked: a traffic light. Straightening the photographed page cut bad readings from 14 to 2 out of 40 new photos.
We checked each measurement on its own. Heart rate, PR interval and axis passed our rules for straightened photos. QT, QRS duration and the P and T wave amplitudes did not pass, so the demo does not show them.
Every rule was written before we saw the result. We report the failures too. It is a research prototype, not a medical device."

## 1. Numbers cheat card

| What | Number |
|---|---|
| Worst damage, wrong heart rate, held-out 99 pages | low resolution 47/99 (47.5%), blur 17/99 (17.2%) |
| Rotation 16 degrees | no wrong readings, but no output on 19/99 |
| Picture-only warning inside one damage level | AUC 0.52 and 0.48 (guessing is 0.5) |
| Digitized-signal warning | AUC 0.926 |
| Traffic light on competition photos, GREEN | wrong 2 of 917 (0.2%) |
| Straightening on 40 new photos | bad 14 to 2, p = 0.0005 |
| No bad reading got GREEN on the 40 new photos | 0 of 20 (original), 0 of 32 (straightened) |
| Simulated test, 120 photos (a script, not a camera) | bad 64 to 21; 1 of 71 GREEN readings was wrong |
| PR interval on straightened photos | typical error 12.0 ms |
| Axis on straightened photos | typical error 4.4 degrees, 95% within 30 degrees |
| QT interval | not validated (slope 0.68 to 0.69, limit 0.7 or 0.8) |
| QRS duration | not validated (bias +15.4 ms on photos, slope 0.74) |
| P wave amplitude | passed on drawn pages, failed on photos (slope 0.77, limit 0.8) |
| T wave amplitude | stopped early (best slope 0.68) |
| Data | PTB-XL, 21,799 recordings; our sets: 50, 100, 140, 1,100, 100 sealed; own photos 60 + 40 + 40 |

## 2. The basic questions (your guide already asked some of these)

**Q1. Are we converting analog to digital?**
Not really. The ECG already exists as numbers (PTB-XL is digital). We draw it as a paper-style picture (digital to picture), damage or photograph it, and the digitizer turns the picture back into numbers. A real paper ECG is analog ink; our study uses a computer-drawn page to know the right answer. So it is "picture back to signal", and we compare with the original numbers.

**Q2. Is the ECG image really RGB?**
We drew pages as PNG files with red, green, blue and an unused transparent channel (RGBA, all fully opaque). The digitizer opens every image as 3-channel RGB (8 bits each). Phone photos are RGB JPEGs. The pink grid and the black trace differ in their colour values; that helps the model separate grid from trace. A black-and-white scan has no grid colour, and our pages are colour only. This is a stated limit.

**Q3. How is the picture made from the numbers?**
At 25 mm per second and 10 mm per millivolt, 200 dots per inch. One pixel is 5.08 ms across and 0.0127 mV up. A sample (time t, voltage v) goes to pixel x = t / 5.08 ms and y = baseline minus v / 0.0127 mV. The page is 2200 by 1700 pixels.

**Q4. What does the digitizer do?**
Open-ECG-Digitizer (a neural network, U-Net) finds the trace and the grid, a Hough transform finds the tilt, the grid spacing gives the pixel size, and the trace is read as a signal at 1,000 samples per second in microvolts. Unreadable leads are returned as missing. We used it unchanged (commit 97a15087).

**Q5. What is the project's main contribution?**
Three things. (1) A measured account of which damage breaks which measurement. (2) A reliability check from the digitized signal, and a straightening step that was confirmed on new photos. (3) A rule for each measurement, written before the test, that decides whether it may be shown. We also report what failed.

**Q6. How is this different from existing work?**
Existing digitizer papers report signal-to-noise ratio, mostly on capture types the dataset already has. We damage one thing at a time over five levels, measure the clinical numbers a patient would be told, define false reassurance (looks normal but is not), and test warnings from the picture and from the signal. The closest papers are on robustness to image damage (Qasmi and Ali) and a vision-language quality module (Li et al.).

## 3. Method questions

**Q7. Why did you not change the digitizer?**
To measure what a real tool does. If we changed it, the results would be about our tool, not about the existing one.

**Q8. What is "wrong" and what is "bad"?**
Wrong: a heart rate more than 5 beats per minute from the true one. No usable heart rate: fewer than 3 beats found. Bad: wrong or no usable heart rate.

**Q9. Where do the true values come from?**
Heart rate: measured by the same code on the recording the page was drawn from. Intervals and axis: PTB-XL+ values from a commercial algorithm called 12SL.

**Q10. 12SL is also an algorithm. Is it ground truth?**
No. It is a reference, not truth. We checked it: 12SL and a second commercial algorithm (Glasgow) agree within about 4 to 6 ms for QRS and QT, and within 30 degrees on 99% of recordings for axis. Where they did not agree (P duration, T duration, ST amplitude), we did not attempt the measurement because no reference exists.

**Q11. What does "pre-specified" mean? Why does it matter?**
We wrote the rule and the pass or fail wording in a log before we saw the result. That stops us from choosing a rule that makes the result look good. "Exploratory" means the idea came after we had seen earlier data. "Post hoc" means we did it to understand a result. We used the word "confirmed" only for the straightening test, whose rule was fixed before the photos existed.

**Q12. How many recordings did you use and are they separate?**
Held-out and sealed sets were chosen in advance with a fixed random seed. Development data and test data never overlap. Whole recordings are held out in cross-validation, so one recording is never in both training and test.

## 4. Results questions

**Q13. Which damage matters?**
Only very low resolution (page shrunk to 15%) and heavy blur. JPEG, brightness, faded grid and rotation did not make the heart rate wrong. Rotation made the digitizer give no answer on about 1 page in 5.

**Q14. Why could the picture not warn about failure?**
A score from the picture knows how damaged a page is, but it could not tell which damaged pages fail. Inside one damage level it was at chance (0.52 and 0.48). It also did not work on real captures (0.52). The honest reading is a negative result.

**Q15. Why does the digitized signal warn better?**
Failures show up in the signal: beats are uneven, leads disagree, parts are missing. Fifteen simple checks gave AUC 0.926, and 0.87 to 0.89 inside the worst damage levels.

**Q16. Does GREEN mean the heart rate is right?**
No. GREEN means no warning was raised. In our data GREEN readings on competition photos were wrong 0.2% of the time (2 of 917), and in a simulation of 120 phone photos 1 of 71 straightened GREEN readings was wrong. It is not a guarantee.

**Q17. Does RED mean the person has a heart problem?**
No. RED means the read looks unreliable. It says nothing about the heart. The check also flags irregular rhythms more often, because a truly irregular rhythm looks like a failed read (67% of readings on atrial fibrillation or flutter recordings were flagged).

**Q18. What does straightening do and how sure are you?**
It finds the page in the photo and flattens it to a standard rectangle. On 40 new photos bad readings fell from 14 to 2; 12 photos became good and none became bad (exact paired test p = 0.0005). The rule was fixed before the photos. The limit: one phone, one screen, 20 recordings.

**Q19. Why did QT fail? It looked close.**
The typical error was small, but our safety checks showed it was squeezing values toward the average. A true short QT was read too long by 23 to 27 ms, so a short QT would look normal. That is the false reassurance we are trying to avoid. A third attempt could not find any method that passed the slope check, so we stopped.

**Q20. Why did QRS fail? The error was only 5 to 6 ms.**
The average error hid a bias: on 40 straightened photos the mean error was +15.4 ms (limit 5) and the slope was 0.74 (limit 0.8). One pixel is about 5 ms at our resolution, so a 10 ms rule is close to what a photo can show.

**Q21. Why did you not try the ST segment?**
The two commercial algorithms disagree on it, and its spread (0.047 mV) is under 4 pixels. A reference that experts' tools do not agree on cannot test us.

**Q22. P wave passed on pages but failed on photos. Why report it as failed?**
Because the rule was written before and needed the photo test too. The slope on photos was 0.77, limit 0.8. We did not change the limit after seeing it.

**Q23. Why is PR shown but only sometimes?**
PR passed for straightened photos with steady rhythm. It is hidden if the light is not GREEN, the page was not straightened, the value is outside 50 to 400 ms, or the beat spacing varies (rr_cv above 0.12). The last guard exists because in atrial fibrillation there are no P waves, but our method still gave numbers for all 6 such test pages. The guard was calibrated on only 14 cases, so it is a precaution, not a validated filter.

**Q24. Axis passed. Does it detect right axis deviation?**
Not shown to work. The fresh test had no right-axis recording, and on photos a right axis was matched in 0 of 4. One recording was wrong by about 120 degrees in both photos. The demo shows degrees only and never a word like "left axis deviation".

## 5. Honesty and limits questions

**Q25. What are the biggest limits?**
One digitizer, one phone, one laptop screen (photos of a screen, not of paper). Damage is simulated on computer-drawn pages, and the digitizer was trained on a similar generator. Real captures have fewer than 100 wrong readings, so those results are descriptive. References are an algorithm, not expert readings. The thresholds are our proposal and the guide has not approved them yet.

**Q26. You changed the heart-rate measure after seeing a problem. Is that fair?**
We call it post hoc and show both versions. Applying the same cleaning filter to the true and the digitized signal cut wrong readings among real captures from 168 of 1,203 to 46 of 1,201. The clean page was wrong in 11% because of a fragile one-number heart-rate method, not damage.

**Q27. You reused photos and pages for P and T wave. Is that a problem?**
We said so in the plan before the run. They had been used for QRS and QT, but no P or T result had been seen, and the P and T methods were built on other recordings. A new set of photos would be cleaner.

**Q28. Does the tool help patients?**
We do not claim that. A clinician study in the literature found that abstaining can even increase missed problems. We only claim the tool warns before showing numbers.

**Q29. Is it a medical device? Can a patient use it?**
No. It is a research prototype. The demo never diagnoses and always says it is not a medical device and to show the original ECG to a doctor.

**Q30. What could go wrong with the demo text?**
All sentences come from a fixed list. A wording checker blocks verdicts such as "your ECG is normal", "you have", diagnoses, and words like "prolonged" or "left axis deviation". There are 19 automated tests. If any text fails the checker, a safe fallback sentence is shown.

**Q31. Why not use a language model to explain the ECG?**
Free text can say unsafe or wrong things. Studies of language models for patient explanations show quality varies. We chose fixed sentences so the output can be checked and tested.

**Q32. Who checked your numbers?**
A second script by the same author recomputes 36 headline numbers from the raw files and all match, and another script checks that every number in the report is in the results file. A second person's recheck of 3 numbers (47/99, 14 to 2, 2/917) is still to be done; the command is in the appendix.

## 6. Project and practical questions

**Q33. What did it cost?**
Software and data are free and open source. Equipment was already owned (laptop with an RTX 3050, phone). Digitizing takes about 35 to 40 seconds per photo on the GPU. The Chapter 3 table lists the amounts to be filled by the team.

**Q34. Where is the code?**
`D:\Capstone Project`: `scripts/analysis/` (analysis), `safeguard/` (traffic light), `demo/` (the app), `scripts/preprocess/page_straighten.py` (straightening), `docs/reports/CODE_MAP.md` (map of everything). Start the demo with `demo\run_demo.bat` and open http://127.0.0.1:7860.

**Q35. What would you do with more time?**
Photograph printed paper with several phones, use expert-annotated references, look for QT, QRS and P and T methods that pass the slope check, and study with clinicians whether the warning changes decisions. Detecting heart conditions comes only after each measurement behind it is validated.

**Q36. Is the paper ready?**
Two drafts are rebuilt from the frozen numbers (IEEE conference style and journal style). They still need compiling on Overleaf and the title, authors and funding line. Nothing is submitted.

## 7. If you are asked something you do not know

Say: "We did not test that. In our study the answer is limited to one digitizer, one phone and one screen." Do not guess a number. The numbers you may quote are on the cheat card in section 1.
