# Results (draft for the paper)

*Draft — written 2026-09-24 from `docs/SWEEP-RESULTS.md` and the three figures in
`MyDrive/MediSense-Cardio-Study/figures/`. Plain markdown so it can be pasted into
whatever paper template (Word or LaTeX/IEEEtran) is used; not yet copy-edited to a
strict word count. Numbers are load-bearing — do not round differently across
sections. Cross-check every number here against `SWEEP-RESULTS.md` before submitting.*

---

## IV. Results

### A. Dataset and test volume

We evaluated 50 records drawn from PTB-XL (a fixed, seed-42 stratified sample of a
500-record pool; 25 labeled normal and 25 abnormal under the PTB-XL diagnostic
superclasses, covering NORM, HYP, STTC, CD and MI). Each record was rendered as a
clean printed-ECG image and degraded along six axes — Gaussian blur, rotation, JPEG
compression, resolution downsampling, brightness/shadow, and grid-contrast fade — at
five severity levels each, plus the clean baseline, for 31 images per record and
1,550 digitize-and-compare tests in total. Every test was digitized with
Open-ECG-Digitizer and the resulting lead-II heart rate was compared against the
ground-truth rate computed from the original signal with NeuroKit2.

*(Note for whoever finishes this: state here whether 50/500 was a scope reduction
made for time, and reference Limitations — already true in SWEEP-RESULTS.md,
carry the same wording into the paper so the two documents do not disagree.)*

### B. Digitizer reliability across the sample

Before analyzing the effect of degradation, we characterized how reliably the
digitizer reads the sample at all. Of 1,550 tests, 163 (10.5%) produced no
extractable heart rate; 154 of these had no digitized signal returned by the tool.
These failures were not spread evenly across the sample: 6 of the 50 records
accounted for the great majority of them, and 4 of those 6 (records 00102, 08150,
13316, 19059) failed to produce a usable signal even on the **undamaged** clean
image (record 00102 also has an unmeasurable ground-truth rate, so it is excluded
throughout). The remaining 37 records never failed and 7 failed once or twice out of
31 attempts. We treat this as a property of specific source images — likely layout or
rendering characteristics the digitizer's layout-matching step does not handle — and
not a property of the degradation being studied. We report these 6 records separately
(Fig. 3) and restrict the degradation analysis below to the 44 **reliable** records
(≤20% failure rate across their 31 versions).

### C. Heart-rate error grows with two of six degradation types

Fig. 1 shows the median and 90th-percentile absolute heart-rate error, per damage
type and severity level, over the 44 reliable records (clean-image error: median
0.13 bpm, mean 0.52 bpm — the digitizer's baseline noise floor). Two of the six axes
show a clear, monotonic rise in error with severity:

- **Blur.** Median error rises from 0.12 bpm at level 1 to 1.64 bpm at level 5; the
  90th-percentile error rises from 0.41 to 2.90 bpm over the same range.
- **Resolution.** Error stays near the clean baseline through level 4 (0.11–0.20 bpm
  median) and then jumps sharply at level 5 to 2.36 bpm median / 7.72 bpm mean, with
  41% of readings at that level off by more than 5 bpm.

The other four axes show no comparable trend: rotation error stays under 1 bpm at
every level; JPEG compression, grid-contrast fade, and brightness/shadow all stay
within the noise band of the clean baseline (medians 0.2–1.2 bpm with no consistent
direction as severity increases). Rotation's effect instead shows up as a different
failure mode, described next.

### D. Patient-facing outcome: false reassurance and silent drops

We classified each reading into the same slow/normal/fast bands used clinically
(<60, 60–100, >100 bpm) and compared the digitized band against the ground-truth
band, giving one of: correct, false alarm, **false reassurance** (system reports
normal when the truth is slow or fast), wrong-abnormal, or silent drop (no reading
produced). This is a heart-rate-only stand-in for the T3 "what the patient is told"
measure defined in our method; only 9 of the 44 reliable records have a truly
abnormal ground-truth rate (6 slow, 3 fast), so this is the size of the population
that can produce a false reassurance at all — the counts below should be read as a
pattern, not a stable rate.

On the clean images, all 44 reliable records were read correctly (0/44 errors).
Across the degraded images, 9 heart-rate readings were misclassified as normal when
the truth was abnormal; of these, 6 were **real** misreadings (digitized rate more
than 10 bpm from the true rate) and 3 were threshold artefacts, where a reading a
fraction of a beat from the 60 or 100 bpm boundary crossed the line without being a
clinically meaningful error (e.g., a true rate of 59.7 bpm read as 60.0 bpm). All 6
real false-reassurance events occurred at the **worst** severity level (level 5) of
the same two axes identified in Section IV-C:

- **Low resolution, level 5:** 4 of the 9 at-risk records (44%) were told "normal"
  when they were not, with readings off by 14–33 bpm.
- **Blur, level 5:** 2 of the 9 at-risk records (22%) were misread the same way, off
  by roughly 15 bpm.
- No false-reassurance events occurred at any other axis or at severity levels 1–4 of
  blur or resolution.

Rotation produced a different failure: at its worst level, 4 of 44 reliable records
(9%) yielded no reading at all (a silent drop) rather than a wrong one — the picture
became unreadable before it became misleading. JPEG compression, grid-contrast fade
and brightness produced negligible false alarms and no false reassurance at any
tested level. Fig. 2 summarizes both outcome types as heatmaps across all six axes
and five levels.

### E. Summary of findings

Within this sample and this pipeline: (1) the system is reliable on clean images and
under mild-to-moderate degradation on every axis tested; (2) it degrades gracefully
along four of six axes (rotation, JPEG, grid contrast, brightness), producing at
worst a "no answer" outcome rather than a wrong one; (3) two axes — heavy blur and
low resolution — are qualitatively different: both produce a real, clinically
meaningful false-reassurance event, and both do so specifically at the most severe
level tested, with no warning at intermediate levels; (4) roughly one record in eight
in this sample is unreliable for reasons independent of image quality, which is
itself an operational finding about the digitizer rather than about degradation.

*(Next: state this section's numbers are heart-rate-only per the Limitations already
in SWEEP-RESULTS.md — diagnosis-level false reassurance, and PR/QRS/QT-based error,
were not measured because digitized signals were not retained from this run.)*

---

## Figure captions (for direct reuse)

**Fig. 1.** Absolute heart-rate error (bpm, symlog scale) vs. degradation severity
(0 = clean) for each of the six damage types, over the 44 reliable records. Solid
line: median; dashed line: 90th percentile. Grey line: median error on the clean
image. Only blur and resolution show a rising trend, and only at the highest
severities.

**Fig. 2.** Left: of the 9 records whose true heart rate is slow or fast, how many
were misclassified as "normal" (reading off by >10 bpm) at each damage type ×
severity level. Right: of the 44 reliable records, how many produced no reading at
all, by damage type × severity level.

**Fig. 3.** The 12 records (of 50) with the most unreadable versions out of 31
attempted; 6 fail in most versions, and 4 of those fail even on the clean image.

---

## What's still needed before this can go in the paper

1. Fit into the actual venue's IEEE template (columns, `\cite{}` keys from
   REFERENCES.md, table/figure numbering matching the rest of the paper).
2. A short **Discussion** paragraph interpreting *why* blur/resolution behave
   differently from rotation/JPEG/brightness (worth checking against the digitizer's
   documented failure modes, if any exist, rather than speculating).
3. Decide whether to report Wilson 95% CIs inline for the 9-record false-reassurance
   counts (they exist in `t3_hr_pooled.csv`) — with n=9 the intervals are wide and may
   be more honest to show than a bare percentage.
4. The exact scope-reduction sentence (500→50) needs to match whatever the Method
   section says, and should be stated plainly, not buried.
