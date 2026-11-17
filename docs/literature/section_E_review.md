# Section E: selective prediction, deferral and risk control (10 papers), review of 2026-11-04

Depth of reading: clinician selective-prediction study (2508.07617), conformal pitfalls in medicine (2506.18162),
biosignal uncertainty review (2312.09454, rejection section): targeted full-section reads with numbers.
Learn-then-Test, risk-controlling prediction sets, conformal risk control, the conformal introduction, class-conditional
conformal, learning to defer, guided deferral (LLM): abstract, introduction, discussion and conclusion plus targeted
searches; the mathematical proofs were not read. Two related papers filed in Section G (conformal triage, abstention in
medical text) were read at abstract/conclusion level only and are not covered here.

## What this section is about
A "gate" says: for this input, do not trust the output (or hand the case to a person). Our photo-quality detector is a
gate. These papers say what a gate can promise and how to judge it.

## Paper by paper

### 1. Selective prediction and human decisions, arXiv 2508.07617 (259 clinicians)
- Setup: vignette study; clinicians decided treatment for hospitalised patients (a) alone, (b) with inaccurate AI,
  (c) with inaccurate AI that abstains on risky parts ("selective prediction").
- Results: treatment accuracy alone 62%; with inaccurate AI 50% (drop significant); with selective prediction 55%
  (partly recovered). False-positive rate rose from 40% to 55% with AI, and returned to baseline (41%) with abstention, but
  the false-negative rate stayed high: 42% versus 31% alone (p < 0.05). Clinicians undertreated more when the AI abstained,
  especially those with no prior AI experience (13 points higher false negatives).
- The effect comes from how people react to abstention, not from the abstention rule's accuracy.
- Limits: online vignettes, not real practice; short training.
- For us: when our gate says "this photo is risky", a user may react in a way we have not tested. The result is a warning
  that the human response to a flag must be studied, not assumed.

### 2. Pitfalls of conformal predictions for medical image classification, arXiv 2506.18162
- Conformal prediction (CP) gives a coverage guarantee (the true label is in the predicted set at least 1 minus alpha of the
  time) from a calibration set, but only under exchangeability of calibration and test data.
- Pitfalls shown on skin-lesion (7 classes) and histopathology (2 classes) data: guarantees are marginal, not per class or
  per subgroup (rare melanoma under-covered while common nevus over-covered); they fail under domain shift and label shift
  (they recover only after recalibrating on shifted data); CP should not be used to pick the confident predictions to boost
  accuracy; with few classes it adds little over simple confidence.
- For us: the exchangeability assumption fails exactly where we would want the gate to work (new damage types, new
  cameras). A guarantee claim would be unsafe.

### 3. Uncertainty quantification for biosignals, a review, arXiv 2312.09454
- Systematic review of uncertainty in machine learning for EEG, ECG, EOG, EMG.
- Evaluating rejection: recommends a coverage-accuracy curve over a range of thresholds, not a single threshold, and a
  separate task-ROC and rejection-ROC. Warns that scoring rejection as "will this be wrong?" classification can
  underestimate it, because noisy ECGs are sometimes still classified correctly.
- What happens to rejected cases matters: re-record the signal (noise-type problems) or hand to a clinician; the review
  cautions that the two kinds of uncertainty cannot yet be separated reliably. Also that uncertainty methods should be
  studied "in situ" with clinicians.
- For us: this is the right way to present our gate (a threshold-range curve, not one number), and it names the open
  question "what does the user do after a flag?"

### 4. Learn then Test (2110.01052), Risk-Controlling Prediction Sets (2101.02703), Conformal Risk Control (2208.02814)
- Three related methods to choose a threshold on any trained model so that a stated error (for example a miss rate) stays
  below a target with high probability, using a held-out calibration set. LTT treats the choice as multiple hypothesis
  testing; RCPS uses a concentration bound; CRC controls the expected value of a monotone loss.
- All need calibration data from the same distribution as deployment.
- For us: this is how a gate could eventually be certified ("misses at most X% of bad readings"). It needs far more
  independent recordings than 49, calibration data that resemble real use, and cannot cover unseen damage types.

### 5. A gentle introduction to conformal prediction (2107.07511) and class-conditional conformal prediction (2306.09335)
- The first is a tutorial: guarantees, how to evaluate (adaptivity, correctness checks). The second shows that per-class
  coverage needs enough calibration examples per class; below about 10 per class only the standard method is usable,
  roughly 20 to 75 per class a clustering method works best.
- For us: our "bad reading" class is rare (6.5% of tests, 99 of 1,519, with 65 of them from five recordings), so
  class-specific guarantees are out of reach with current data.

### 6. Predict Responsibly: learning to defer (1711.06664) and a guided-deferral system with LLMs (2406.07212)
- Learning to defer: train the model knowing a downstream human decision-maker exists; deferral can improve accuracy and
  fairness, even with biased humans. Guided deferral: parse medical reports, defer uncertain cases to humans with guidance;
  pilot study suggests complementarity; the authors warn that standard calibration error metrics mislead on imbalanced
  healthcare data and propose an "imbalanced ECE".
- For us: the gate's value depends on what the human step does. Imbalanced bad readings make accuracy-style or calibration
  scores misleading, so report catch rate and false-alarm rate (as we do).

## What our gate can honestly claim, in numbers
Our held-out gate table for the primary target (heart rate off by more than 5 bpm or unreadable; 99 bad of 1,519 tests,
6.5%). Accepted-tests bad rate is my approximate calculation from the rounded percentages in that table:

| Flag the most suspicious | Bad readings caught | Good readings wrongly flagged | Bad rate among accepted photos |
|---|---|---|---|
| none (accept all) | 0% | 0% | 6.5% |
| 10% | 37% | 8% | about 4.6% |
| 20% | 46% | 18% | about 4.4% |
| 30% | 58% | 28% | about 3.9% |

Reading: rejecting a third of all photos lowers the bad-reading rate among the ones you keep from 6.5% to about 4%.
That is a modest gain for a large inconvenience, and it came from five hand-made scores on 49 recordings tested only on
the same damage types.

## What this section means for the project
1. Present the gate as a threshold-range curve (this table, extended), with the honest line "rejecting 30% of photos cuts
   bad readings among accepted ones from about 6.5% to about 4%".
2. Do not claim a statistical guarantee. The papers say the guarantees need exchangeable calibration data and a
   calibration set large enough for a rare class; neither holds.
3. State plainly that the user's reaction to a flag is untested; the clinician study shows it can shift errors the wrong way
   (more missed problems).
4. Specify what happens after a flag: retake the photo (a quality problem) or have a person check (a recording problem).
   Section B showed many failures come from the recording itself, which retaking a photo cannot fix.
5. If this goes further: collect many more recordings and real photos, calibrate at recording level, and test on damage
   types not used to build the gate.

## Questions a guide could ask
- "Is this a formal safety guarantee?" No. Show the curve, not a guarantee.
- "What happens when it flags a photo?" Not tested. Two options (retake, or human check) and the clinician study's warning.
- "Why not conformal prediction?" Its guarantee needs exchangeable calibration data and enough examples of a rare class;
  our damage types shift and bad readings are rare and clustered.

## Cautions
- I did not read the proofs or the long experiments of the three risk-control papers.
- The clinician study uses vignettes and a different clinical task; use its direction, not its numbers, for us.
- The "bad rate among accepted" column is derived from rounded percentages and is approximate.
