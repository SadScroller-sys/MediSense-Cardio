# Method (draft for the paper)

*Draft — written 2026-09-24 from `docs/PLAN.md` (Part 2 — The Research Contribution) and
`docs/SWEEP-RESULTS.md` ("What was run"). Citation numbers below use the numbering in
`docs/REFERENCES.md` as of 2026-08-19 — re-check them if that file has been reordered
since. Placeholders are marked `[TODO]`. This section describes what was actually run,
including the scope cut from ~500 to 50 records — stated here plainly, matching the
wording already in SWEEP-RESULTS.md and PAPER-RESULTS-DRAFT.md so the three documents
agree.*

---

## III. Method

We study how image degradation of a photographed paper ECG propagates through an
automated digitization pipeline into the value ultimately reported to a patient. This
section describes the data, the degradation model, the pipeline under test, and the
measurement used in the Results that follow.

### A. Dataset and sampling

We use PTB-XL [45], a public, clinically-validated 12-lead ECG dataset (CC-BY 4.0)
containing diagnostic superclass labels (NORM, MI, STTC, CD, HYP) for each record. A
diagnostic-outcome study requires a mix of normal and abnormal ground truth — without
abnormal cases, false reassurance cannot be observed at all — so we drew a stratified
sample rather than a random one.

We sampled 50 records from a fixed 500-record stratified pool (seed 42), balanced
25 normal / 25 abnormal by PTB-XL superclass (NORM 24, HYP 9, STTC 7, CD 5, MI 4 in the
final 50). **The sample size was reduced from a planned ~500 records to 50** because of
free-tier GPU compute limits and the project deadline; the reduction was decided before
any result was observed, and its effect on statistical power is discussed in
Section [TODO — Limitations]. The 500-record pool and the seed-42 selection are fixed
and version-controlled (`data/ptbxl/sample_500.csv`) so the sample is reproducible.

### B. Pipeline under test

For each sampled record, we reproduce the path a patient's photo would take through the
system end to end:

1. **Rendering.** The record's ground-truth 12-lead signal is rendered to a printed-ECG
   page image using ECG-Image-Kit [1], which produces a realistic clinical-ECG layout at
   a fixed clean baseline.
2. **Controlled degradation.** The clean image is degraded along one of six axes,
   independently, at five increasing severity levels each (Section III-C), plus the
   undamaged image itself, for 31 image variants per record.
3. **Digitization.** Each variant is passed to Open-ECG-Digitizer [5] (Stenhede,
   Bjørnstad & Ranjbar, arXiv:2510.19590; `python -m src.digitize`), a deep-learning
   digitizer, which returns an extracted digital waveform and layout match metadata
   (`digitization_metadata.csv`), or fails to return a signal at all.
4. **Feature extraction and comparison.** Heart rate is computed from the digitized
   lead-II waveform using NeuroKit2's R-peak detector [TODO: add NeuroKit2 citation to
   REFERENCES.md — Makowski et al., *Behavior Research Methods*, 2021] and compared
   against the heart rate computed the same way from the original, undegraded ground-
   truth signal.

All digitization was run on a T4 GPU (Google Colab); reproduction instructions and the
exact resumable notebook are in `colab/MediSense_Cardio_FullSweep_v1.ipynb`.

### C. Degradation model

We degrade the rendered clean image along six axes chosen to span distinct real-world
photography failure modes — focus, hand angle, transmission/storage, camera distance,
ambient light, and print condition — rather than only one:

| Axis | Simulates | Levels (1→5) |
|---|---|---|
| Blur | Camera out of focus | Gaussian kernel 3, 7, 11, 15, 21 px |
| Rotation | Photo taken at an angle | 2°, 5°, 8°, 12°, 16° |
| JPEG compression | Lossy transmission/storage | Quality 50, 30, 15, 8, 3 |
| Resolution | Camera distance / low-end camera | ×0.75, 0.5, 0.35, 0.25, 0.15, then upscaled back |
| Brightness/shadow | Uneven ambient lighting | Linear shadow gradient, 15–75% |
| Grid contrast | Faded or low-contrast printout | Fade toward mean, 15–75% |

Each axis is varied independently (one axis at a time against an otherwise-clean image),
not in combination — a single-axis sweep, consistent with the scope set in
`docs/PLAN.md`. Levels increase monotonically in severity within each axis; level 5 is
the most severe tested, not a hard ceiling on real-world degradation.
[TODO: state explicitly if/why combinations were out of scope, or mark as future work.]

### D. Outcome measure

Phase 2 of this study measures the raw error a reader would need (T1 signal fidelity,
T2 feature-level error); the analysis in this paper's Results section reports a
heart-rate-only realization of the third, patient-facing tier (T3) defined in
`docs/PLAN.md`: each digitized heart rate is classified against clinical banding
(<60 bpm slow, 60–100 bpm normal, >100 bpm fast) [52] and compared against the same
banding applied to the ground-truth rate, yielding one of five outcomes — correct,
false alarm, **false reassurance** (reported normal when the truth is slow or fast),
wrong-abnormal, or silent drop (no signal extracted). False reassurance is the
safety-critical outcome: it is the case in which a degraded image causes the system to
tell a patient with an abnormal heart rate that they are within normal range.

[TODO — Limitations, to state explicitly in that section, not fabricate here: this
paper's current Results use the heart-rate realization of T3 only. PR, QRS and QT/QTc
intervals — and therefore diagnosis-level false reassurance beyond heart rate banding —
were defined in the method but not yet computed, because digitized signals from this
run were not retained; a re-run saving signals is planned before the camera-ready
version if time allows.]

### E. Records excluded from the degradation analysis

Six of the 50 sampled records were unreadable by the digitizer in most of their 31
variants, including — for four of the six — the undamaged clean image itself. We
treat this as a per-record digitizer failure independent of the degradation under
study (Results, Section IV-B) and report it separately rather than folding it into
the degradation curves, which are computed over the remaining 44 records.

---

## What's still needed before this can go into the paper

1. ~~Confirm the exact digitizer citation.~~ **Resolved 2026-09-24** — the tool's own
   README cites arXiv:2510.19590, which matches reference [5] (Stenhede, Bjørnstad &
   Ranjbar). Method text above now cites it directly.
2. Add a NeuroKit2 citation (Makowski et al. 2021) to `docs/REFERENCES.md` if it is not
   already there under a different number.
3. Decide and write the one line stating why single-axis (not combined-axis)
   degradation was in scope — likely "time and scope," matching the honesty already used
   elsewhere in these docs.
4. This Method section and `PAPER-RESULTS-DRAFT.md`'s dataset description (Section IV-A)
   currently repeat the same numbers — when assembling the final paper, keep the full
   description here in Method and have Results refer back to it rather than restating it.
5. A Method subsection for Contribution 2 (the no-reference quality proxy) is not
   included here because that work has not started; add it only once real.
