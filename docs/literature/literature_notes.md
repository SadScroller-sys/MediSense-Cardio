# Literature notes: the three closest papers (read 2026-11-04)

Read from the full text (engrXiv PDF; arXiv PDF for VLM-in-the-Loop; arXiv HTML for Open-ECG-Digitizer
because the PDF download was cut off). Equations and figures in the Open-ECG-Digitizer HTML did not
extract, so numbers that were stripped from its tables are not quoted here.

## 1. engrXiv 8013 -- "How Robust Are ECG Image Digitizers to Image Damage? A Per-Type, Per-Method Study"
Qasmi and Ali, 2025/26 preprint, 23 pages. https://engrxiv.org/preprint/view/8013

What they did
- PhysioNet/Moody Challenge 2024 dataset: 977 records x 9 *labelled capture types* (clean, colour scan,
  B&W scan, mobile photo, screen photo, stained, damaged, moldy colour, moldy B&W) = 8,793 images.
- Compared three methods (a "ladder"): classical sweep, sweep + neural grid rectification, full neural
  pipeline (pretrained components from the Challenge winners).
- One metric only: SNR in dB (aligned, linear-domain average). Reported per type.
- Result: classical baseline negative SNR on all 9 types (-4.83 dB overall); full pipeline about 25.6 dB
  overall, within a 0.46 dB band across types.

How we differ (use these points if asked)
- They use the ready-made capture types of an existing dataset. We apply 6 controlled damage types, one at
  a time, each at 5 severities, so we can say how fast error grows with severity.
- They report SNR only and say so in their limitations ("we do not yet link recovered-signal SNR to
  downstream diagnostic accuracy"). We measure HR, PR, QRS, QT and QTc against the truth.
- They have no false-reassurance concept and no photo-quality predictor.
- Their finding (neural pipeline is uniformly robust) disagrees with ours (resolution, blur and rotation
  break readings at high severity, and a few recordings cause most bad readings). Likely reasons: their
  damage is the dataset's own, not graded; their metric averages in the linear domain, which they admit
  lets easy images dominate; and SNR can look fine while clinical intervals are off. We should state this
  as a difference in what is measured, not claim they are wrong.
- Both studies share the same limits: one family of digitisers, mostly synthetic or rendered inputs.
- Their own "future work" (link damage-specific SNR to downstream clinical accuracy) is what we do.
  Say that plainly.

## 2. Open-ECG-Digitizer -- Stenhede et al., "Digitizing Paper ECGs at Scale" (arXiv 2510.19590; npj Digit Med 2026)
https://arxiv.org/abs/2510.19590 ; published version https://www.nature.com/articles/s41746-025-02327-1

What they did
- The digitiser we stress-test: neural segmentation, perspective correction (Hough-based), grid scale
  extraction, layout identification, segmentation-to-trace conversion.
- Trained only on synthetic images (ECG-Image-Kit variant on CODE-15%) to test domain shift.
- Real data: 1,596 images (266 ECGs) at Akershus, scanner vs two phones. Mean SNR: scanner 19.65 dB,
  OnePlus 12.19 dB, iPhone 10.47 dB. Also evaluated on the Emory hidden Challenge set (positive SNR in
  every category, but low: roughly 1 to 7 dB).

Things that matter for us
- Real phone photos score about 7 to 9 dB lower than scans. That is the real-photo gap, and it is a
  limit on what our synthetic damage can claim.
- Unreadable parts are set to NaN, not rejected. This supports how we count "unreadable" as a bad
  reading.
- They say SNR "might not always be completely aligned with the clinical utility". This supports our
  clinical-interval approach.
- They say low SNR is often caused by time misalignment, not wrong shape. Relevant to our alignment and
  interval choices.
- Limitations they list: needs more clinical validation, domain shift, overlapping signals.

## 3. VLM-in-the-Loop -- Li et al., arXiv 2604.00396 (preprint, April 2026)
https://arxiv.org/abs/2604.00396

What they did
- A quality-assurance module placed after any digitiser: it looks at the extracted signal and the
  original image, scores quality with signal-quality indices, morphology checks and a vision-language
  model, and can trigger re-processing.
- Tested on 200 PTB-XL records with paired truth, and on 428 real HCM clinical archive images.
- Numbers: verdict consistency 71% -> 89% with tool evidence; the AUROC for predicting above/below-median
  signal fidelity is only 0.64 (95% interval 0.56 to 0.71); logistic regression on tool features alone
  0.59. Standard signal-quality indices resolved only 2 of 5,080 leads.
- On real archive images, three published digitisers failed badly (e.g. ECG-Digitiser 84.2% Poor; Open-
  ECG-Digitizer 2.5 valid leads per image).
- Plausibility checks they use: HR 30 to 220 bpm, PR 120 to 200 ms, QTc 340 to 500 ms (Bazett).

How we differ
- Their gate runs after digitising and uses the recovered signal plus the image. Ours uses only the
  photo, before digitising, so it can stop a bad upload before any compute.
- They predict a reconstruction-fidelity score (PCC). We predict clinically wrong readings (HR, QTc, QRS)
  and define false reassurance.
- Their predictive power is modest too (AUROC 0.64). Our held-out 0.607 for the primary target is in the
  same range. Both studies show quality prediction is hard. Do not present ours as better.
- Their real-image result (all three digitisers fail on real archive scans) says our synthetic damage may
  understate real-world failure.

## What this means for our claims
1. Novelty is narrower than "we stress-test digitisers": the per-damage-type idea exists (engrXiv 8013).
   What is ours: graded severities, clinical interval errors, false-reassurance, and a photo-only gate.
2. Cite both engrXiv 8013 and VLM-in-the-Loop in related work and state the differences above.
3. Keep the claim modest: the gate is a prototype, and the three papers all point to the synthetic-to-
   real gap as the main open risk.

## 4. Findings from the second round (papers downloaded to C:\ECG research, read 2026-11-04)
Depth of reading: abstract plus conclusion/limitations section only, unless marked "more". Not full text.

QT correction (matters for our QTc results)
- Vandenberk et al., JAHA 2016 (PMC4937268, 6,609 patients; read abstract, methods table, conclusion): Bazett
  corrects worst; Fridericia and Framingham correct best and predict 30-day mortality better (HR 5.95 and
  7.31 vs 4.49 for Bazett). In healthy people the Bazett 99% upper limit was 472 ms (men), 482 ms (women),
  ABOVE the usual 450/460 ms cut-offs, so Bazett over-calls prolonged QTc.
- Sources of QTc variability (Ann Noninvasive Electrocardiol 2020, ANEC-25-e12730): much QTc variability is
  measurement method, not biology; avoid Bazett for clinical decisions.
- Consequence: our QTc false-reassurance numbers use Bazett. The Fridericia rerun you postponed is worth
  doing before the review, because a guide who knows this literature can ask.

Checking the gate idea (selective prediction)
- Selective prediction clinician study (arXiv 2508.07617, 259 clinicians): hiding unsafe AI output helps
  only partly and shifts the kind of error clinicians make, with more false negatives. Our gate says "do
  not trust this reading"; we have not tested what a person does then. State it as a limit.
- Conformal prediction pitfalls (arXiv 2506.18162): guarantees are unreliable under distribution shift
  and should not be used to pick which predictions to trust. Fits our result: the detector fails on
  unseen damage types (AUC 0.32 to 0.37). Do not claim formal guarantees.
- Learn-then-Test (2110.01052) and Conformal Risk Control (2208.02814) give the formal way to set a
  threshold for a chosen risk. Only a future step for us: we need more recordings first.

Damage design and the synthetic-to-real question
- ECG-Image-Kit (2307.01946; also described in the Challenge paper): its artifacts are wrinkles, creases,
  shadows, rotation, handwriting. Ours are blur, rotation, JPEG, low resolution, brightness gradient, grid
  fade. We have no creases, perspective, glare or handwriting. That is the honest gap to state.
- Challenge paper (Reyna et al. 2024, PMC12891466 file, 4 pages): 62 teams; hidden set is 35,595 REAL
  printed, photographed or scanned images (clean, stained, deteriorated, screen photos). The winner scored
  12.15 on the hidden set (Krones/SignalSavants, 2410.14185: 17.02 dB in cross-validation, 12.15 hidden).
- Are Synthetic Corruptions A Reliable Proxy For Real-World Corruptions? (2505.04835): for segmentation,
  mean performance under synthetic corruptions correlates with real (r about 0.69 to 0.86), but this is
  driving scenes, not ECG. Supports "synthetic damage ranks methods reasonably", not "numbers transfer".
- CheXphoto (2007.06199, 2011.06129): photos of chest X-rays plus synthetic photo-like transforms, a direct
  precedent for what we do. They also took real photos.
- MedMNIST-C (2406.17536): severity-graded corruptions across medical imaging, a precedent for graded damage.
- ECGtizer (2412.12139): tested mostly on clean, digitally generated pages; says creases and scan quality
  are future work. VLM-in-the-Loop shows real data is much harder.
  CORRECTION (full read, see docs/section_A_review.md): 2502.14909 (PTB-Image / VinDigitizer) reports only a
  0.01 dB SNR baseline; its classification section is "work in progress", so it shows nothing about accuracy
  versus scan quality. ECG-Image-Kit gives no numeric interval accuracy. ECGtizer reports 25 to 28 ms mean
  interval differences on clean device printouts.

Quality gates
- ECG SIGNAL-quality papers (PMC7517279, PMC8539388) work on the recorded signal, not the photo.
  Only VLM-in-the-Loop gates on the image, and after digitising. A photo-only gate before digitising looks
  open, but that also means little prior work to benchmark against.
- Document image quality (1906.01907, DocIQ 2509.17012): no-reference quality models for scanned documents
  exist and are trained on human ratings or OCR accuracy. Our five hand-made signals are simpler and are
  not trained against a human quality rating.

Method standards
- Riley et al., BMJ 2020 (sample size): rule of thumb 10 events per predictor; prefer bootstrapping over
  splitting data. We have 99 bad readings and 5 predictors, but 65 of the 99 come from 5 recordings, so
  the effective sample is far smaller than 99.
- CLAIM 2024 update (ryai.240300): checklist for AI imaging studies; includes stating the level of data
  splitting (patient vs image). We split by recording, which is the right level.

## 5. Third round: key-section read of every remaining paper (2026-11-04)
Depth: abstract, introduction, results or discussion, limitations and conclusion. Not every page.

Strongest new evidence for our framing
- Moody Challenge 2024 overview (Reyna et al.): they say SNR "does not directly capture or reflect clinical
  measurements", and that some teams with negative SNR still classified ECGs almost as well as the best
  teams. That is our motivation for measuring clinical intervals instead of SNR, stated by the organisers.
- SignalSavants / Krones et al. (winner): 17.02 dB in cross-validation, 12.15 on the scans-only leaderboard,
  but a mean extended-hidden score of only 0.57 across ALL real variants (photos, stains, deterioration).
  Their own discussion: no team got a positive score on phone photos of stained paper, and cross-validation
  was much higher than hidden data. This is the real-photo gap in numbers.
- ECG-Image-Kit paper did compare QRS width, RR and QT with ground truth, so "we measure intervals" alone
  is not new. But that was a case study on its own synthetic images and its authors say it is not indicative
  of real clinical measurement. Our graded damage and false-reassurance framing are still ours.
- ECGtizer: evaluated on clean, digitally generated pages only; its QT/QRS preservation is claimed but
  untested on creased or low-quality scans (its own limitation).
- Real-world head-to-head of seven diabetic-retinopathy AI systems (Lee 2021): only 3 of 7 matched human
  sensitivity and 1 of 7 matched specificity, with low PPV. External, real-world validation exposes gaps that
  company numbers hide. Supports caution about a prototype validated only on simulated damage.
- CheXphotogenic (photos of chest X-rays, 8 models): most models dropped on photos but stayed about as good
  as radiologists in most comparisons. The drop from digital to photo is normal and should be reported, not hidden.

Synthetic damage as a proxy
- Synthetic-vs-real corruption study (2505.04835): mean performance correlates (r about 0.69 to 0.86) but
  individual corruption types differ: snow aligned well, while brightness and fog correlated weakly. Our
  brightness-gradient damage may be the least realistic of ours; its unseen-type AUC (0.32) is the worst.
  This is from driving segmentation, so it is only a caution.
- ImageNet-C (1903.12261) is the origin of graded corruption benchmarks; the pathology benchmark
  (2206.14973) found error roughly doubled on corrupted images and confidence estimates became unreliable.
  Augmentation-corruption paper (2102.11273): robustness may not generalise beyond the corruptions seen,
  which matches our finding that the detector fails on damage types left out of training.

Selective prediction and risk control (all method papers; none ECG-specific)
- Risk-controlling prediction sets (2101.02703), Learn-then-Test (2110.01052), Conformal Risk Control
  (2208.02814), the conformal introduction (2107.07511) and class-conditional conformal (2306.09335):
  ways to set a threshold with a stated error guarantee. They need calibration data and exchangeability.
  We have 49 recordings and see distribution shift between damage types, so the guarantees would not hold.
- Learning to defer (1711.06664) and the guided-deferral LLM paper (2406.07212): a system should pass hard
  cases to a human; the second warns that calibration metrics mislead on imbalanced healthcare data, as ours is.
- Biosignal uncertainty review (2312.09454): uncertainty methods for ECG/EEG exist, but they need study
  "in situ", i.e. with clinicians acting on the flag. Same gap as the clinician selective-prediction study.
- Calibration paper (PMC6912996): poorly calibrated risk scores are misleading. We have not checked the
  calibration of our detector's probabilities. A to-do.

Method and statistics
- Riley part II (PMC6519266) and BMJ 2020: sample-size criteria beyond "10 events per predictor". Not applied yet.
- Simulation-studies tutorial (PMC6492164): report the design of simulated experiments transparently
  (what was varied, how many repetitions). Relevant because all our damage is simulated.
- QT algorithm paper (PMC5581168): automated QT is as accurate as trained manual readers, using the tangent
  method, but low T-wave amplitude raises error. Supports expecting extra QT error on faint or blurred traces.
- Wavelet delineation (1808.04804) and PTB-XL benchmarks (2004.13701): background for interval measurement
  and for the dataset. PTB-XL+ (2023) supplies reference interval features.

Tangential (read for relevance only; they do not change our claims)
- Medical-LLM safety benchmark (PMC12855988), over-trust in AI medical answers (2408.15266), ReLay (2605.00468),
  and the cardiology patient-guide LLM study (PMC13025549): about language models, not ECG images. The
  over-trust study is a loose support for "people may believe a confident wrong output".
- Tele-ECG for heart attack care (1805.05913): background only.
- Document image quality (DocIQ, text-line framework): no-reference quality scoring for scanned documents;
  trained on human ratings or OCR accuracy, unlike our untrained signals.
- ECG signal-quality papers (PMC7517279, PMC8539388), smartwatch AF validation (PMC9043399): all judge the
  recorded signal, not the photo. Smartwatch: algorithm alone was of limited clinical value without physician review.
- Conformal triage (Sci Rep 2026), abstention in medical text (npj AI 2026), autonomous DR pivotal trial
  (2018): read for abstract and conclusion only; method details not reviewed.

## Download problems found (C:\ECG research)
- Still missing: PMID 19261293, 19228821, 15072211, 23972343 (the four PubMed papers). 19228821 is the
  AHA/ACCF/HRS QT statement we cite for 450/460 ms, so it is the one to get. I could not fetch it.
- WRONG FILE: G._Reporting_and_Method_Standards\54_PMC5736701.pdf is an 83-page diabetic-eye grading
  quality guide, not "Leveraging uncertainty information from deep neural networks for disease detection".
  That paper is still missing.
- 57_PMC12891466.pdf is the Moody Challenge 2024 overview, not the Open-ECG-Digitizer paper (that one is
  01_2510.pdf / 60_s41746-025-02327-1.pdf). Useful, just mislabelled.
- Duplicates: 59 and PMC12855988 are the same file; 66_gcsp and PMC13025549 are the same file.
- Not downloaded at all: Lence 2023 digitisation review, TRIPOD+AI.
