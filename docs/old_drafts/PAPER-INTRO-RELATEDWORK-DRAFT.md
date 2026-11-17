# Introduction and Related Work (draft for the paper)

*Draft — written 2026-09-24, from `docs/PLAN.md` (Part 2, the reframed claim and title
rationale), `docs/REFERENCES.md` (the annotated reading list, its Topic 5–7 "where our
contribution sits" argument, and the Appendix IEEE reference list), and
`docs/review1/MediSense-Cardio_Review1.pptx` framing. Citation numbers `[N]` use the
Appendix numbering in `docs/REFERENCES.md` as of 2026-08-21 — re-verify if that file is
reordered before submission. `[TODO]` marks placeholders that need a decision, not a
fabricated fact.*

---

## I. Introduction

An ECG (electrocardiogram) taken at a clinic is normally read by trained staff on
calibrated equipment. Increasingly, patients instead encounter a printed or
photographed ECG outside that setting — a printout from a home device, a photo of a
clinic report sent over a messaging app, an image uploaded to a symptom-checking
service — and expect a system that can read it back into numbers and explain what
those numbers mean in plain language. Systems of this shape are already technically
feasible: open-source tools can digitize a paper ECG image into a waveform with
reported signal-to-noise around 19.65 dB on real-world scanned pages [5], and
large language models are routinely used to translate structured clinical output
into plain-language text for patients [33], [34], [38]–[43].

What is not established is what happens when the *input image itself* is degraded —
blurred, tilted, poorly lit, low-resolution, or compressed — as a patient's own phone
photo very often will be. Each stage of a digitize-then-explain pipeline is normally
validated on clean, well-scanned images. If the extracted heart rate (or interval) is
wrong because the source image was poor, and the pipeline is confident anyway, the
final sentence shown to the patient can be **false reassurance**: a system stating
that an abnormal reading is normal. This is a safety-relevant failure specific to the
image→numbers→text pipeline as a whole, not to any one stage of it, and — as
Section I-B argues — it has not been directly measured.

### A. Problem statement and research question

We ask: **how much does image degradation of a photographed paper ECG have to
accumulate before an automated digitize-and-explain pipeline gives a patient a
factually wrong, falsely reassuring answer?** We answer this empirically rather than
theoretically, using a pipeline built from existing, previously-validated open-source
components (Section III), a public ECG dataset with known ground truth [45], and a
systematic, controlled degradation study spanning six realistic image-quality axes at
five severities each (Section III-C).

### B. Contribution

[TODO — state final contribution scope honestly against what has actually been run.
As of 2026-09-24 the results in Section IV are Contribution 1 only, heart-rate tier,
50 of a planned ~500 records. Do not claim Contribution 2 (the no-reference quality
proxy) as delivered unless it is built before submission — `docs/PLAN.md` describes it
as designed but not started.]

This paper's contribution, as currently supported by evidence:

1. We build and run an end-to-end, repeatable degradation-measurement harness —
   render (ECG-Image-Kit [1]) → controlled multi-axis degradation → digitize
   (Open-ECG-Digitizer [5]) → compare against ground truth — over a stratified,
   labeled sample of PTB-XL records [45], covering six independent degradation axes
   (blur, rotation, JPEG compression, resolution, brightness/shadow, grid contrast)
   at five severities each.
2. We report, for the first time to our knowledge (Section II), how digitization
   error at this severity range translates into the *patient-facing* outcome that
   matters — not signal-level error alone, but whether the system would tell a
   patient with an abnormal heart rate that they are within normal range — and show
   that this happens only at the two most severe levels of two of the six axes
   tested (blur, resolution), while the other four axes degrade gracefully into
   "no answer" rather than a wrong one.
3. [TODO, only if delivered before submission] A no-reference image-quality signal,
   calibrated against the measured errors above, that predicts these failures without
   needing ground truth at inference time (Contribution 2, `docs/PLAN.md`).

### C. Paper organization

Section II situates this work against ECG digitization, ECG signal-quality
assessment, uncertainty-aware medical AI, and patient-facing medical text generation.
Section III describes the dataset, pipeline, and degradation model. Section IV
reports results. Section V [TODO: Discussion/Limitations] and Section VI [TODO:
Conclusion] follow.

---

## II. Related Work

We organize related work around the three fields this project sits between, following
the structure already worked out in `docs/REFERENCES.md`: (A) digitizing paper ECGs,
which we reuse rather than contribute to; (B) assessing whether a signal or image is
good enough to trust, the closest published work to the first half of our
contribution; (C) knowing when an automated system should decline to answer, the
closest published work to the second half; and (D) generating patient-facing medical
text safely, which bounds how novel our end-to-end framing can honestly be claimed
to be.

### A. ECG digitization

Converting a printed or photographed ECG into a digital waveform is an active but
comparatively mature area. ECG-Image-Kit [1] provides a synthetic-image generation
toolbox that we use to render controlled test images from ground-truth PTB-XL signals
(Section III-B). On the reading side, several open digitizers now report strong
accuracy on real scanned pages: Open-ECG-Digitizer [5], which we use, is validated on
37,191 ECG images with reported SNR near 19.65 dB; ECGtizer [3] and ECG-Digitiser
(the 2024 PhysioNet Challenge winner [2], [4]) represent independently developed
alternatives, and a wider body of digitization work spans classical image-processing
pipelines [6]–[9] through recent deep-learning approaches [10], [11]. The 2024 George
B. Moody PhysioNet Challenge established SNR against ground truth as the field's
standard accuracy measure [2], [4] — we report a comparable measure in our own
pipeline (T1, `docs/PLAN.md`) but the contribution of this paper begins after this
stage, not within it: we treat digitization as a solved, reusable building block, and
study what happens to its output under degraded input.

### B. ECG signal- and image-quality assessment

A separate line of work asks whether a given ECG signal is even worth analyzing.
Deep-learning quality classifiers report strong accuracy distinguishing interpretable
from non-interpretable ECGs — up to 97.1%/96.4% in one generalized model assisted by
conditional GANs [12] — and the same question has been studied specifically for noisy
or intermittent recordings from wearable and portable devices [13], [15], [16],
[19]–[22], including unsupervised approaches that need no quality labels at all [14],
[17], [18]. This body of work establishes that signal-quality gating is both feasible
and already standard practice before automated analysis of a *waveform*.

Distinct from signal quality, ECG-image-database [2], [4] catalogues the actual
degradations a photographed paper ECG accumulates in the real world — perspective
skew, wrinkles, stains, uneven lighting — which is the basis for the six degradation
axes we simulate in Section III-C, and makes a finding we rely on directly: SNR alone
is a poor proxy for clinically important detail, since it captures gross waveform
distortion but misses the subtle onset/offset features that interval measurements
depend on [2]. This is why our own evaluation (Section III-D) measures error at the
level of the extracted clinical value, not only signal fidelity.

**Gap.** This literature asks *"is this signal good enough to analyze?"* — a question
answered once, upstream of any patient-facing statement. It does not ask what we ask:
whether the analysis, once trusted and reported to a patient, was actually correct.

### C. Uncertainty, abstention, and knowing when not to answer

A second relevant field studies when an automated medical system should decline to
give a confident answer rather than risk a wrong one. This includes uncertainty-aware
abstention for medical text classification [23], conformal and cost-aware deferral
for clinical triage under distribution shift [24], [27], deferral frameworks
purpose-built for LLM-based clinical systems [25], and quality/uncertainty
quantification specifically applied to ECG interpretation [28], [31], [47]–[51]
selective-classification approaches more broadly [32], and further applications of
uncertainty estimation to diagnostic support [29], [30]. Notably, [26] — a study we
engage with directly rather than cite only in passing — finds that clinician-facing
abstention does not straightforwardly reduce harm: when an AI system abstains,
clinicians' own error patterns *shift* rather than simply improve, with false
positives falling but false negatives rising. This is a direct challenge to any
system, including the one this project's Contribution 2 would extend, that treats
abstention as an unqualified safety improvement; we treat it as a design constraint
rather than an assumption.

**Gap.** This literature is almost entirely about *whether to answer at all*, given
an uncertainty estimate that already exists. It does not connect that uncertainty
back to a measured, empirical rate of a specific real-world harm (false reassurance)
caused by a specific, controllable input condition (image degradation) — which is
what Section IV of this paper does before any deferral policy is proposed.

### D. Generating patient-facing medical explanations, safely

Using large language models to translate clinical output into patient-readable text
is an established and fast-moving area. Prior work has evaluated LLM-generated
patient information for cardiological procedures generally [33]; personalized
plain-language summaries and their cost/quality trade-offs [34]; radiology report
summarization for patients [38]; safety guardrails specifically for patient-facing
LLM systems [39]; and general benchmarking of LLM chatbots and public LLM responses
on patient-facing medical questions [40]–[43]. A broader clinical-safety benchmark,
CSEDB, defines 30 metrics for evaluating medical LLM safety and effectiveness [35].
Within cardiology specifically, ECG-LM [36] and vision-enabled LLM evaluation for
image-based ECG interpretation [37] are both recent, but — as in [2]'s framing of
the digitization literature — both are aimed at *clinician* users interpreting a
signal or trace, not at a patient reading a plain-language explanation of their own
photographed ECG.

**Gap.** Patient-facing plain-language summarization is established; measuring
medical-AI safety in general is established. Neither existing thread traces a
*specific, controllable, upstream cause* — photo quality — through to the specific
*downstream harm* (false reassurance) in the specific setting (a patient's own
photographed paper ECG) that this paper studies.

### E. Positioning

Table [TODO] and the summary above show that the closest published work stops at one
of two boundaries: it checks whether a signal or image is good enough to trust
(Section II-B), or it studies when a system should abstain given uncertainty it
already has (Section II-C) — but no work we found connects a controllable,
photographable-real-world condition (image degradation) all the way through to a
measured, patient-facing outcome (false reassurance) in an ECG-specific,
patient-facing setting. That is the gap Section IV's results are aimed at, and it is
the claim this paper is prepared to defend: not that digitization, quality
assessment, or patient-facing summarization are individually novel — each is
established and cited above — but that **no prior work quantifies how far into the
pipeline a degraded photograph's error propagates, and at what severity it becomes a
falsely reassuring statement to a patient** [see `docs/PLAN.md`, "The claim to write
in the paper"].

---

## What's still needed before this can go into the paper

1. **Do not overclaim Contribution 2 in the Introduction.** As of this draft it is
   designed (`docs/PLAN.md`) but not built or evaluated; Section I-B is written with
   an explicit `[TODO]` guard for exactly this reason — check it against the actual
   state of the repo at submission time, not against this draft's date.
2. Write the Discussion/Limitations and Conclusion sections (not attempted here) —
   Limitations should state the heart-rate-only scope and the 50-record sample size
   plainly, matching `PAPER-RESULTS-DRAFT.md` and `PAPER-METHOD-DRAFT.md`.
3. A short related-work summary table (method / what it measures / gap vs. this work)
   is common in IEEE related-work sections and referenced above as `Table [TODO]` —
   add one if space allows; it is not essential.
4. Two Topic-1 (ECG fundamentals, AHA/ACCF/HRS [52]) and Topic-2 (PTB-XL dataset
   [45], [46]) citations belong more naturally in Section III (Method) than here, and
   are already used there in `PAPER-METHOD-DRAFT.md` — avoid citing them redundantly
   in the Introduction beyond the single dataset mention above.
5. Reference numbers `[1]`–`[52]` must be re-verified against the live
   `docs/REFERENCES.md` Appendix immediately before submission in case it has been
   edited or renumbered since 2026-08-21.
