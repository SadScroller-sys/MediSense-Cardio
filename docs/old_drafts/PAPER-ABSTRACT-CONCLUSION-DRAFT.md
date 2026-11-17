# Abstract and Conclusion (draft for the paper)

*Draft — written 2026-09-24, summarizing `PAPER-INTRO-RELATEDWORK-DRAFT.md`,
`PAPER-METHOD-DRAFT.md`, `PAPER-RESULTS-DRAFT.md`, and
`PAPER-DISCUSSION-LIMITATIONS-DRAFT.md`. No new claims or numbers are introduced here —
both sections only restate what those four documents already establish. Write the
Abstract last when assembling the final paper (after any last-minute number changes),
since it is the piece most likely to go stale first. Section numbering: VII =
Conclusion, following VI = Limitations.*

---

## Abstract

Patients increasingly encounter automated systems that read a photographed paper ECG
and explain it in plain language, but such pipelines are typically validated on
clean, well-scanned images — not on the blurred, tilted, or low-resolution photos
patients actually take. We study how much image degradation an automated
digitize-and-explain pipeline can tolerate before it gives a patient a falsely
reassuring answer. We build an end-to-end measurement harness — render, degrade,
digitize, and compare against ground truth — over a stratified sample of 50 PTB-XL
records, spanning six independent degradation axes (blur, rotation, JPEG compression,
resolution, brightness/shadow, grid contrast) at five severities each plus a clean
baseline (1,550 tests total). On clean images, all reliably-digitized records were
read correctly. Under degradation, heart-rate error rose only along two of the six
axes — blur and low resolution — and only at their most severe level, where the
system misclassified 2 of 9 and 4 of 9 at-risk records respectively as within normal
range when they were not: a real, clinically meaningful false reassurance. The
remaining four axes (rotation, JPEG compression, grid-contrast fade, brightness)
degraded gracefully, at worst producing no reading rather than a wrong one. A further
6 of 50 records were unreliable to digitize regardless of degradation, independent of
image quality. These results indicate that quality-based safeguards for this kind of
system need not treat all degradation uniformly: two specific, identifiable failure
conditions account for the safety-relevant risk observed, and could form the basis of
a targeted upload-time quality check. [TODO: adjust the closing sentence if
Contribution 2 (the calibrated no-reference quality proxy) is built and evaluated
before submission, and state it as delivered rather than proposed.]

*(~230 words as drafted; trim toward the target venue's abstract word limit —
`docs/REFERENCES.md`, "Candidate publication venues" — before submission.)*

---

## VII. Conclusion

This paper measured, rather than assumed, how far degradation in a photographed paper
ECG propagates into what an automated system tells a patient. Using a controlled,
repeatable harness over a labeled sample of PTB-XL records, we found the failure is
not uniform across degradation types: heavy blur and very low resolution are
qualitatively different from rotation, JPEG compression, faded print, and uneven
lighting, both in whether they produce a rising error trend at all (Section IV-C) and
in the kind of failure they cause when they do — a wrong, falsely reassuring answer
for blur and resolution, versus a safer "no answer" for the others (Section IV-D,
Section V-A). This distinction is, to our knowledge, not previously reported for a
patient-facing ECG pipeline (Section II), and it has a direct practical consequence:
an upload-time image-quality gate for a system like this does not need to reject
broadly degraded photos uniformly — it needs to specifically catch heavy blur and low
resolution, the two conditions under which this study observed real harm.

The study also surfaced a finding independent of degradation itself: 6 of 50 sampled
records (12%) were unreliable to digitize in most of their versions, including 4 that
failed on the undamaged clean image. We report this as a real property of the
digitizer's reliability on this sample, not folded into the degradation curves, and
note it as a caution for anyone deploying a similar pipeline: image quality is not
the only source of failure worth measuring.

**Future work.** The most direct next steps, in order of value: (1) re-run the study
retaining digitized signals to extend the outcome measure beyond heart rate to PR,
QRS, and QT/QTc, which would allow diagnosis-relevant false reassurance (e.g., a
missed prolonged QT) to be measured directly rather than only rate-based
misclassification (Section VI, Limitation 1); (2) build and calibrate the
no-reference image-quality proxy proposed as Contribution 2 in `docs/PLAN.md`,
targeted specifically at the two axes shown here to matter, and evaluate whether it
predicts false-reassurance risk well enough to gate uploads before digitization runs
at all; (3) extend the sample back toward the originally planned ~500 records to
narrow the wide confidence intervals around the 9-record at-risk population
(Section VI, Limitation 2); (4) test combined-axis degradation, since real
photographs plausibly combine several of these conditions at once (Section VI,
Limitation 6); and (5) evaluate the abstention question raised in Section V-C
directly — what a patient or clinician does when the system declines to answer,
not only whether the decision to decline was correct.

More broadly, this work argues that "does the digitizer work" and "is the final
patient-facing statement correct" are different questions, and that safety claims for
systems of this kind should be evaluated against the second, not only the first.

---

## What's still needed before this can go into the paper

1. Resolve the Abstract's `[TODO]` against whichever contributions are actually
   delivered by submission — do not let the Abstract claim more than
   `PAPER-INTRO-RELATEDWORK-DRAFT.md`'s Section I-B claims.
2. Trim the Abstract to the target venue's word limit once a venue is finalized
   (`docs/REFERENCES.md`, "Candidate publication venues").
3. The Conclusion's future-work list is ordered by the same priority already used in
   `project_fullsweep_state.md` / prior status updates — re-check that ordering still
   matches whatever the team actually plans to attempt before the deadline.
4. Once all sections are final, do one pass across all six paper-section drafts
   (`PAPER-METHOD-DRAFT.md`, `PAPER-RESULTS-DRAFT.md`,
   `PAPER-INTRO-RELATEDWORK-DRAFT.md`, `PAPER-DISCUSSION-LIMITATIONS-DRAFT.md`, this
   file) checking that every number, record ID, and citation number agrees — they
   were written separately and cross-referenced by hand, not generated from one
   shared source of truth.
