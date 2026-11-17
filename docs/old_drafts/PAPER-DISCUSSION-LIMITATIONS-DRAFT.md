# Discussion and Limitations (draft for the paper)

*Draft — written 2026-09-24, from `docs/SWEEP-RESULTS.md` ("Limitations that must appear
in the paper"), `docs/PLAN.md` (Part 2 and the abstention/deferral discussion under
Topic 6), and `PAPER-RESULTS-DRAFT.md` / `PAPER-METHOD-DRAFT.md` (so numbers and scope
statements agree across the paper). Section numbering follows
`PAPER-INTRO-RELATEDWORK-DRAFT.md`: V = Discussion (interpretation), VI = Limitations.
Some papers fold Limitations into Discussion as one subsection — `[TODO]` marks that
formatting choice for whoever assembles the final document.*

---

## V. Discussion

### A. Two axes matter; four do not — and the failure mode differs

The central pattern in Section IV is not that degradation is uniformly harmful, but
that it is sharply bimodal. Blur and low resolution are the only two of six tested
axes that produce a rising error trend (Section IV-C) and the only two that produce a
real false-reassurance event (Section IV-D) — and in both cases only at the single
most severe level tested, with no detectable warning at intermediate severities. This
matters practically: a monitoring or quality-gating system cannot rely on a smooth
early-warning signal from these two axes. Error is effectively flat through level 4
and then jumps at level 5, so any usable quality threshold for blur or resolution
must sit clearly below that jump, not be tuned against a gradual curve.

The other four axes — rotation, JPEG compression, grid-contrast fade, and
brightness/shadow — behave differently in a way that is, if anything, reassuring for
system design. Rotation's worst failure mode is a **silent drop**: at its most severe
level, 4 of 44 reliable records (9%) produced no reading at all rather than a wrong
one (Section IV-C, IV-D). A system that returns nothing is trivially safer than one
that returns a confident wrong answer — a silent drop is recoverable (the user is
asked to retake the photo) in a way a false reassurance is not. JPEG compression,
grid-contrast fade, and brightness/shadow produced neither a rising error trend nor a
meaningful rate of any bad outcome at any level tested, suggesting the digitizer's
extraction step is genuinely robust to these three particular failure modes within
the ranges we tested.

**Why blur and resolution might differ from the other four** is worth stating as a
hypothesis rather than a settled finding, since we did not instrument the digitizer's
internals to confirm it directly [TODO: state explicitly if this remains a hypothesis
or if Contribution 2 / a follow-up look at the failing images (`docs/PLAN.md`,
"optional: look at the 6 failing pictures") produced direct evidence before
submission]: both axes destroy the same underlying signal — the sharp edges of the
printed trace against the grid — that grid detection and R-peak localization likely
depend on, whereas rotation is a global geometric transform the digitizer's layout
step may already correct for, and JPEG/contrast/brightness degrade appearance without
removing the trace's edges at the severities tested.

### B. Practical implication: where an upload-time quality gate should sit

`docs/PLAN.md` proposes deriving a minimum acceptable image-quality threshold from
exactly this kind of curve, to be enforced as an upload-time gate (Contribution 2,
not yet built — Section VI-C). The results here suggest that gate does not need to be
symmetric across all six axes: a system could safely tolerate a moderately rotated,
compressed, faded, or unevenly lit photo, but should specifically flag or reject
images that are heavily blurred or captured at very low resolution — the two
conditions under which this study observed real, clinically meaningful
misclassification. This is a narrower and more targeted claim than "reject all poor
quality images," and one this dataset, unusually, supports directly.

### C. Engaging the abstention critique

Jabbour et al. [26] find that when a clinical AI system abstains, clinicians' own
error patterns shift rather than uniformly improve — false positives fall, false
negatives rise. This is relevant to any future version of this system that acts on
the findings in Section V-B by refusing to process a low-quality image: a refusal is
not automatically a safe outcome if it pushes a patient toward not seeking care at
all, rather than toward retaking the photo or consulting a clinician. Our current
results do not test this — they measure whether the *system's own output* is wrong,
not what a patient or clinician does downstream in response to a wrong or withheld
answer, which [26]'s finding suggests is not a safe assumption to skip. We treat this
as an open question for Contribution 2 and any deployed version of the quality gate
proposed above, not as evidence against building one, but as a reason its evaluation
must eventually include what happens after the system declines to answer, not only
whether it declined correctly.

### D. Relation to the closest published work

Section II-B's cited quality-assessment literature asks whether a *signal* is good
enough to analyze, typically reporting classification accuracy against a
human-labeled interpretable/non-interpretable ground truth [12]–[22]. Our results are
not directly comparable to those accuracy figures, because we ask a different
question — not "is this readable" in the abstract, but "does the number this system
would report to a patient, given this specific image, match the truth" — and report
outcome rates at graded severities rather than a single accuracy figure. We see this
as the intended extension described in `docs/REFERENCES.md`'s framing of the gap:
carrying the quality question through to the sentence a patient reads, rather than
stopping at the signal.

---

## VI. Limitations

We state these plainly, as scope decisions and known weaknesses, matching the wording
already used in `docs/SWEEP-RESULTS.md` so the two documents do not disagree.

1. **Heart rate only.** The Results in Section IV realize only the heart-rate band of
   the T3 patient-facing outcome measure defined in Section III-D. PR interval, QRS
   duration, and QT/QTc — and therefore diagnosis-relevant false reassurance beyond
   simple rate banding (e.g., a missed prolonged QT) — were defined in the method but
   not computed, because digitized signals from this run were not retained.
   [TODO: state whether a re-run saving signals was completed before submission; if
   not, this remains the paper's single largest limitation and should be named as
   future work in the Conclusion, not softened here.]
2. **Sample size and its effect on the headline finding's precision.** The study
   sample was reduced from a planned ~500 stratified records to 50, for compute-quota
   and deadline reasons decided before any result was observed (Section III-A). Of
   those 50, only 9 records have a truly abnormal ground-truth heart rate, since a
   false-reassurance event can only be observed on an abnormal-truth record. The
   false-reassurance counts in Section IV-D (2/9, 4/9) should be read as a pattern
   demonstrating *that* the failure exists and roughly *where* it concentrates, not
   as a precise population rate — Wilson 95% confidence intervals computed over this
   sample (`t3_hr_pooled.csv`) are wide, consistent with n=9.
3. **A data-quality confound, reported and excluded rather than hidden.** Six of the
   50 sampled records (12%) were unreadable by the digitizer in most of their 31
   versions regardless of degradation, and 4 of those 6 failed even on the undamaged
   clean image. We attribute this to per-record digitizer behavior unrelated to the
   degradation under study and exclude these records from the degradation analysis
   (Section IV-B), reporting them separately. This is itself a finding about
   real-world digitizer reliability, not only a methodological caveat, and we report
   it as such rather than silently dropping the records.
4. **Simulated, not photographed, degradation.** All six degradation axes are applied
   by post-processing a cleanly rendered image (OpenCV transforms), not captured from
   an actual camera photographing a printed page. This isolates each axis cleanly for
   controlled measurement, which real photographs rarely allow, but real photos
   combine several of these conditions simultaneously (e.g., blur and uneven lighting
   together) and may include failure modes this simulation does not reproduce, such
   as physical creasing, glare, or partial occlusion — several of which are
   catalogued directly from real photographed ECGs in [2], [4] and would be a natural
   extension of this degradation model.
5. **Single digitizer, single rendering tool, single lead.** All results use one
   digitization tool (Open-ECG-Digitizer [5]) and one rendering tool (ECG-Image-Kit
   [1]); the false-reassurance pattern reported here is a property of this specific
   pipeline and may not generalize to other digitizers listed in Section II-A
   ([2]–[4], [6]–[11]) without re-running the study against them. Measurements are
   also computed from lead II only, matching the pipeline's current scope, not the
   full 12-lead signal.
6. **Single-axis degradation.** Each of the six axes was varied independently against
   an otherwise-clean image (Section III-C), not in combination. Real photographs
   plausibly combine multiple degradations at once (e.g., a tilted, dim photo taken
   at a distance), and combined-axis effects may compound differently than the
   single-axis curves in Section IV-C would predict; this was out of scope for the
   time available and is named here as future work, not silently assumed away.

---

## What's still needed before this can go into the paper

1. Resolve the two `[TODO]`s above against the actual state of the project at
   submission time — specifically, whether a signal-retaining re-run happened
   (affects Limitation 1's framing and whether Section V-A's hypothesis about
   *why* blur/resolution differ can be stated as evidence rather than speculation).
2. Decide the Discussion/Limitations split: some IEEE venues want a single combined
   "Discussion" section, others a separate "Limitations" subsection or paragraph —
   check the target venue's template (`docs/REFERENCES.md`, "Candidate publication
   venues") before final formatting.
3. Cross-check that every claim above still matches whatever numbers are in
   `SWEEP-RESULTS.md` and `PAPER-RESULTS-DRAFT.md` at submission time — this section
   was written to agree with them as of 2026-09-24 but was not regenerated from a
   shared source of truth, so a later change to one must be propagated to the others
   by hand.
4. Conclusion and Abstract remain to be written after this.
