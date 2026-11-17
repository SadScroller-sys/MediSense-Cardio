# Section G: reporting and method standards, and mixed papers (9 files), review of 2026-11-04

This folder is a catch-all. The 9 files are:
43_bmj (Riley sample size), 54_PMC5736701 (WRONG FILE), 57_PMC12891466 (Moody Challenge overview, mislabelled),
59_s41746-025-02277-8 (medical-LLM benchmark; same file as Recovered_Papers/PMC12855988),
60_s41746-025-02327-1 (Open-ECG-Digitizer, published version), 61_s41598-026-40637-w (conformal triage),
62_s44387-026-00097-z (abstention in medical text), 63_s41746-018-0040-6 (diabetic retinopathy pivotal trial),
66_gcsp.2025 (cardiology patient guides by chatbots; same file as Recovered_Papers/PMC13025549).

Depth of reading: Riley BMJ sample-size paper: the sample-size steps and worked examples (targeted full-section read).
Diabetic retinopathy trial: results, image-quality algorithm and operating protocol (targeted). Challenge overview: read in
full earlier. Open-ECG-Digitizer published version: compared with the arXiv version, numbers identical (19.65 / 12.19 /
10.47 dB; Emory 7.34, 7.24, 1.05 to 2.03). Conformal triage and abstention papers: abstract and framing only. The
medical-LLM benchmark and the patient-guide study: abstract and limitations only, tangential. The NHS file: contents list
and quality-assurance sections only.

## The papers that matter

### 1. Riley et al., Calculating the sample size required for developing a clinical prediction model, BMJ 2020
- Three-step approach, not just "10 events per predictor": (1) enough to estimate the overall outcome rate precisely
  (aim for margin of error 0.05); (2) enough for small prediction error across the range; (3) enough that the expected
  overfitting (shrinkage) is at most 10%. Also: avoid splitting the data; use bootstrapping for internal validation.
- Examples from the paper: outcome rate 10% needs at least 139 people for a margin of 0.05; 20 predictors with expected
  Cox-Snell R2 of 0.1 needs 1,698 people; the answer is sensitive to R2, lower anticipated R2 needs more.
- Applying it to us (my calculation with their formula; it reproduces their 139 and 1,698):
  - Outcome rate 6.5%, margin 0.05: about 94 independent subjects; margin 0.02: about 584.
  - Five predictors, shrinkage 0.9: about 875 subjects at R2 0.05, about 425 at R2 0.10, about 199 at R2 0.20, about 123 at
    R2 0.30. Our held-out AUC of 0.607 suggests a low R2, so 0.05 to 0.10 is the cautious range.
  - We have 49 recordings. Our 1,519 tests are 31 versions of each recording, not 1,519 independent people, and 65 of the
    99 bad readings come from five recordings.
- Verdict: the detector is far below the recommended sample size by this standard. This is an approximate application (their
  method assumes independent subjects and a particular model type), but the direction is clear.

### 2. Diabetic retinopathy pivotal trial, Abramoff et al., npj Digit Med 2018 (an autonomous AI system, 900 people)
- The system has a built-in image-quality algorithm that runs before the diagnostic one and returns one of three outputs:
  disease detected, not detected, or "insufficient quality". Operators retake the image up to three times; if still
  insufficient, that result is reported to the user.
- Results: sensitivity 87.2%, specificity 90.7%, imageability 96.1% (33 of 900 participants, 4%, got an insufficient-quality
  output); pre-set targets were sensitivity above 85%, specificity above 82.5%.
- For us: a quality gate with a defined retake protocol and a reported "imageability rate" is exactly the structure of an
  authorised autonomous screening system. We can borrow the framing: report how many photos would be rejected and what the
  user does next. Their gate is built into the product and designed with the image acquisition protocol; ours is a
  prototype on simulated damage.
- Read in detail: sensitivity, specificity, imageability, quality-algorithm description and protocol. Not read in detail:
  the statistics supplement.

### 3. Moody Challenge 2024 overview (Reyna et al.), the file named 57_PMC12891466
- Read in full earlier: 62 teams, the real hidden set of 35,595 images, winner 12.15 SNR on the scans-only leaderboard and
  0.57 mean on the extended hidden data; the organisers say SNR does not reflect clinical measurements.
- For us: this is the Challenge's own statement of the problem and metric. The file is mislabelled; the Open-ECG-Digitizer
  paper is 60_s41746-025-02327-1 and 01 in Section A.

### 4. Open-ECG-Digitizer, published version (npj Digit Med 2026): same numbers as the arXiv version reviewed in Section A.

## Related papers, lower importance
- Conformal selective prediction with cost-aware deferral (Kwon and Kim, Sci Rep 2026): early-sepsis prediction on
  temporally separated test sets. Deferring low-confidence cases reduced error on the retained cases by 49.6% at 80% coverage
  in-distribution and 46.7% out-of-distribution; coverage stayed close to the 90% target. For comparison, our gate at 20%
  flagged lowers the bad-reading rate among accepted photos from about 6.5% to about 4.4%, a reduction of about 32%
  (my approximate calculation). Different task, a far stronger model and far more data, so this is context only.
- Uncertainty-aware abstention in medical text (Vazhentsev et al., npj AI 2026): evaluates uncertainty methods for
  abstention on clinical texts and proposes HUQ-2. No imaging or ECG content; only the abstract was read.
- NHS Diabetic Eye Screening, "The management of grading quality" (this is the WRONG file for 54_PMC5736701): a screening
  programme's quality-assurance manual for graders (test sets with known truth, sensitivity and specificity thresholds, kappa,
  sample-size tables). Loosely useful as an example of ongoing performance monitoring; not the paper we meant to get.

## Tangential, can be dropped
- A novel evaluation benchmark for medical LLMs (npj Digit Med 2025): safety scores lower than effectiveness scores
  across models; language models, not ECG.
- Chatbot patient information guides for ECG, echo and stress tests (Glob Cardiol Sci Pract 2025): compared readability and
  reliability of two chatbots; tiny study; not about digitisation.

## Method standards read from the Recovered_Papers and Downloads folders (key sections only)
- CLAIM 2024 update: a checklist for AI imaging studies; the item we meet most clearly is stating the level of data
  splitting (we split by recording). TRIPOD+AI itself is not among the downloaded files.
- Calibration (Van Calster 2019): poorly calibrated risk scores mislead; we have not checked the calibration of our detector.
- Simulation studies (Morris 2019): describe the simulated design transparently (what varied, how many repetitions).
- Riley part II (Stat Med 2019): the longer statistical derivation behind the BMJ summary.

## What Section G means for the project
1. Sample size is the honest weak point of the detector. Riley's criteria say hundreds of independent recordings are
   needed for even five predictors at a modest signal; we have 49.
2. The gate framing has a real-world model: an authorised screening system with a built-in quality check, a retake protocol
   and a reported imageability rate. Report ours in those terms (share of photos rejected, what happens next).
3. Add a calibration check of the detector's probabilities and cite CLAIM and TRIPOD+AI items we meet or do not meet.
4. Cite the Challenge overview for "SNR is not a clinical metric", Riley for sample size, and the DR trial for the gate
   structure. Leave out the LLM and patient-guide papers.

## Questions a guide could ask
- "Is 49 recordings enough?" By Riley's own criteria, no for model development; fine for a stress test of a digitiser,
  as long as we say so.
- "Does a real system do this?" Yes, an authorised DR screening system returns "insufficient quality" with a retake rule.
- "Did you check calibration?" Not yet.

## Housekeeping found in this folder
- 54_PMC5736701.pdf is the wrong document; the intended paper (Leveraging uncertainty information from deep neural
  networks for disease detection) still has to be downloaded if we want it.
- 57_PMC12891466.pdf is the Challenge overview, not the Open-ECG-Digitizer paper.
- Two duplicates (59 = PMC12855988; 66 = PMC13025549).
