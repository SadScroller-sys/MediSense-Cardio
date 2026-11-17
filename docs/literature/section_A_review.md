# Section A: ECG digitisation (7 papers), review of 2026-11-04

Depth of reading: Open-ECG-Digitizer (HTML version, no equations or table cells that did not extract),
VLM-in-the-Loop, engrXiv 8013, SignalSavants, the PTB-Image / VinDigitizer paper: FULL text.
ECG-Image-Kit and ECGtizer: full read of introduction, datasets, the interval/clinical-measurement parts,
results tables and conclusions; the mid-paper method detail (network architectures, training) skimmed.

## One-paragraph picture of the field
A digitiser takes an image of a paper ECG and returns a signal. Almost everyone scores it with SNR (signal-to-noise
ratio in dB), usually on scans or on synthetic renders, and trains mostly on synthetic images. All the real-photo
evidence says it gets much worse on phone photos and damaged paper. Clinical measurements (heart rate, QT, QRS) are
rarely checked and, where they are, mostly on clean or synthetic inputs.

## Paper by paper

### 1. Open-ECG-Digitizer: Stenhede et al., arXiv 2510.19590 / npj Digit Med 2026 (the tool we stress-test)
- Question: can one open tool digitise scans and phone photos at scale?
- Method: five modules: U-Net segmentation, perspective correction (Hough based), grid-size extraction,
  layout identification, segmentation-to-trace conversion. Trained only on synthetic images (modified ECG-Image-Kit
  on CODE-15%), deliberately unlike the test data.
- Data: 1,596 real images (266 ECGs, thermal paper) photographed with two phones and scanned; also the Emory hidden
  Challenge set (35,595 images).
- Results (mean SNR): scanner 19.65 dB, OnePlus 12.19, iPhone 10.47. On Emory, positive in every category but low,
  roughly 1 to 7 dB (colour scan clean 7.34, B&W scan clean 7.24, mobile photo clean 1.05, stained 2.03, screenshot 2.11).
- Authors' own caveats: unreadable leads are set to NaN, not rejected; low SNR is often time misalignment rather than
  wrong shape; SNR may not match clinical utility; needs more clinical validation.
- For us: this is the system under test. Its NaN behaviour is why "unreadable counts as bad" is fair. The phone-vs-scan
  gap (about 7 to 9 dB) is the real-photo gap our simulation cannot reproduce.

### 2. VLM-in-the-Loop: Li et al., arXiv 2604.00396 (preprint, under review)
- Question: can a vision-language model check and correct any digitiser's output?
- Method: three-tier QA (signal-quality indices, morphology checks, VLM judge with tool evidence) plus a 12-action
  correction loop.
- Results: tool evidence raises verdict consistency 71% to 89% (200 PTB-XL records); AUROC for predicting fidelity
  0.64 (0.56 to 0.71); logistic regression on tool features 0.59. On 428 real clinical images three published digitisers
  failed (ECG-Digitiser 84.2% poor, Open-ECG-Digitizer 2.5 valid leads per image, ECGMiner empty output on all).
  Standard signal-quality indices resolved only 2 of 5,080 leads.
- Uses plausibility ranges HR 30 to 220, PR 120 to 200 ms, QTc 340 to 500 ms (Bazett).
- For us: the closest "gate" paper, but after digitising and on fidelity, not clinical error. Its modest AUROC sits
  beside our 0.607. Its real-image failures say our synthetic damage may understate real trouble.

### 3. engrXiv 8013: Qasmi and Ali, "How Robust Are ECG Image Digitizers to Image Damage?"
- Question: does accuracy hold for every damage type, not just on average?
- Data: PhysioNet 2024 set, 977 records x 9 labelled capture types = 8,793 images.
- Method: three-rung ladder (classical sweep, plus grid rectification, plus neural reader); SNR only.
- Results: -4.83 / -3.37 / 25.56 dB overall; neural pipeline within a 0.46 dB band across the types they report.
- Limits they state: local split (not the official hidden set), pretrained components, synthetic-to-real gap, SNR only,
  four of nine types not tabulated for the full pipeline.
- For us: closest overlap; differences are graded severity, clinical intervals, false reassurance and the gate.

### 4. SignalSavants (Challenge winner): Krones et al., arXiv 2410.14185 (4 pages)
- Method: Hough rotation, nnU-Net segmentation, vectorise the mask (mean y of non-zero pixels per column).
- Data: 21,799 PTB-XL recordings, at least four ECG-Image-Kit augmentations each.
- Results: CV SNR 17.02 dB; official leaderboard (PTB-XL scans) 12.15, rank 1 of 16. On other hidden image types:
  positive 0.51 to 4.93 on scans of any paper quality, but NEGATIVE -1.76 to -0.72 on mobile phone photos and
  screenshots. No team scored positive on phone photos of stained paper.
- Larger models (M2, M3) overfit and did worse on the hidden set (9.42, 4.20).
- Assumptions that hurt generalisation: fixed lead order and position, one full signal per image, constant resolution
  and grid scale.
- For us: this is the clearest statement that simulated augmentation scores (17.02) overstate real-photo performance.

### 5. ECG-Image-Kit: Shivashankara et al., arXiv 2307.01946 (Physiol Meas 2024)
- What it is: open synthetic generator (handwriting, wrinkles, creases, shadows, perspective, rotation).
- Case study: 21,801 images from the PhysioNet QT database; a classical plus deep pipeline; SNR.
- Clinical measurements: on 10,000 synthetic images at 200 dpi, QRS width, RR and QT from the reference and from the
  digitised signal were reported as "highly correlated" in a scatter figure (no summary numbers in the text). Outliers
  came from R-peak and fiducial detection failures, low-amplitude ECGs (quantisation noise) and grid or text residue.
- Authors' caveat: results "are not indicative of the actual clinical parameter measurements" because the same detectors
  are used on both sides; they suggest comparing to human annotation in future.
- For us: it generates the kind of pages we use; its artifact list is wider than ours (we have no creases, perspective,
  handwriting or glare). Intervals were checked before, but only on synthetic images and without numbers.

### 6. ECGtizer: Lence et al., arXiv 2412.12139
- Method: automated lead detection, three pixel-based extraction variants, a lost-signal recovery step.
- Data: JOCOVID (807 real hospital ECGs, available as XML and PDF; the PDFs are device printouts, not photos), PTB-XL.
- Interval results (JOCOVID, lead II, NeuroKit2 beats): mean absolute time-domain difference 25.47 ms (PaperECG),
  28.02 ms (ECGtizerFull), larger for the others. QT difference 0.04 to 0.09 s (SD 0.08 to 0.16 s); QRS difference
  0.02 to 0.06 s. Amplitude differences 75 to 895 microvolts depending on method.
- Limits they state: clean, digitally generated pages only; creases, annotations and variable scan quality are future work.
- For us: even on clean device PDFs, interval differences are around 25 to 30 ms on average, with large spread. That
  supports treating about 20 ms as a normal noise floor (ours: median 20 ms on clean images), and it uses the same
  NeuroKit2 style of measurement.

### 7. PTB-Image / VinDigitizer: Nguyen et al., arXiv 2502.14909 (7 pages)
- Data: 549 PTB records printed with ECG-Image-Kit and scanned (the "PTB-Image" dataset; this confirms it exists).
- Method: VinDigitizer (YOLOv8 row detection, Otsu binarisation, iterative grid removal, least-cost path tracing).
- Result: mean SNR 0.01 dB on the scans, i.e. barely better than outputting zeros, although waveform shape was
  "recognisable".
- IMPORTANT: the abstract and conclusion describe a comparison of AlexNet, VGG, ResNet and Vision Transformer on
  scanned ECGs, but the section "Direct Diagnosis via Scanned Images" says only "Work in progress". The paper contains no
  classification results. Treat it as a preliminary dataset-and-baseline note, not as evidence that accuracy falls
  with scan quality.

## What Section A tells us (themes)
1. SNR is the common metric and the field itself doubts it (Challenge organisers, Open-ECG-Digitizer, ECG-Image-Kit,
   engrXiv all say it is not clinical). Our clinical-measurement approach answers a stated need.
2. Simulated or cross-validation scores overstate real-photo performance: SignalSavants 17.02 dB CV vs negative on
   phone photos; Open-ECG-Digitizer 19.65 dB scans vs about 10 to 12 dB phones; VLM-in-the-Loop: three digitisers fail
   on real archives. Our simulated damage should be presented as a stress test, not a prediction of field performance.
3. Intervals have been measured in two places (ECG-Image-Kit on synthetic images, ECGtizer on clean PDFs) and show tens
   of milliseconds of error even without damage. Nobody in this section measures them under graded damage.
4. Nobody here defines false reassurance or tests a photo-only gate. VLM-in-the-Loop is the only gate, after digitising.
5. Common weak points: single digitiser per study, mostly synthetic training, hospital-specific data, preprints.

## Questions a guide could ask, and the honest answer
- "Isn't this what engrXiv already did?" They did per-type SNR on dataset-defined capture types with a pretrained
  pipeline; we did graded damage and clinical intervals on Open-ECG-Digitizer. Related, not identical.
- "Why not report SNR?" The Challenge organisers say it does not reflect clinical measures; we report it only
  alongside clinical errors if needed.
- "Do your results hold on real photos?" Not shown. Every paper here that tests real photos finds worse performance.
- "Why is your interval error already 20 ms on clean images?" ECGtizer reports 25 to 28 ms mean time differences on
  clean device printouts; reader-to-reader QT variability is also tens of milliseconds (Section B papers).

## Corrections to earlier notes (made 2026-11-04)
- The PTB-Image paper does not contain classification results (see paper 7).
- SignalSavants scored negative on ALL mobile phone photos and screenshots, not only on stained ones.
- ECG-Image-Kit gives no numeric interval accuracy in the text, only a correlation figure.
