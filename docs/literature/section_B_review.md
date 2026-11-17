# Section B: datasets and ECG measurement (5 papers), review of 2026-11-04

Depth of reading: PTB-XL dataset paper and PTB-XL+ paper: targeted read of the data description, signal metadata,
validation and fold sections (not every page). PTB-XL benchmarks: abstract, task list, results summary.
Wavelet delineation (1808.04804): abstract, method headings, conclusion. Tele-ECG (1805.05913): abstract and
introduction only; it is background, not relevant to our claims.

## Paper by paper

### 1. PTB-XL, Wagner et al., Scientific Data 2020 (the source of our recordings)
- 21,799 ten-second 12-lead ECGs from 18,869 patients, recorded 1989 to 1996. Original sampling 400 Hz,
  released upsampled to 500 Hz, plus a 100 Hz downsampled copy.
- Labels: SCP statements. 67.13% from manual interpretation by a cardiologist; only about 73.7% of records are marked as
  validated by a human, and the authors say one can reasonably claim a single human validation.
- Signal quality metadata (flags): baseline drift, static noise, burst noise, electrode problems, extra beats, pacemaker.
  77.01% of records have no quality annotation ("highest quality"); pacemaker flagged in 1.34%.
- Ages 90 and over are coded as 300 (privacy rule).
- Ten patient-wise stratified folds; folds 9 and 10 contain only human-validated records.
- For us: matches what we saw (50 records, ages up to 300, 41 to 42 of 50 human-validated, one pacemaker).

### 2. PTB-XL+, Strodthoff et al., Scientific Data 2023
- Adds ECG features for every PTB-XL record from three algorithms: Marquette 12SL and Glasgow (commercial, from a median
  beat) and ECGDeli (open). Includes intervals, amplitudes, fiducial points and median beats.
- Consistency check: the two commercial algorithms agree well (correlation above 0.9 for most amplitude and interval
  features); weakest on small waves (S, P, Q amplitudes).
- For us: this is an independent source of reference intervals. Our "truth" PR, QRS, QT and QTc come from NeuroKit2
  applied to the original signal, not from a cardiologist or a commercial algorithm. We have not checked how far those
  truth values sit from 12SL, Glasgow or ECGDeli on our 50 records.

### 3. Deep Learning for ECG Analysis: Benchmarks and Insights from PTB-XL, Strodthoff et al. (arXiv 2004.13701)
- Benchmarks classifiers on PTB-XL across statement, age, sex and signal-quality tasks; ResNet and Inception-style CNNs
  best; reports 95% confidence intervals; discusses uncertainty.
- For us: confirms PTB-XL is a standard benchmark and that a signal-quality task exists on it. Not about images.

### 4. Finding morphology points of ECG waves using wavelet analysis (arXiv 1808.04804)
- A multi-lead wavelet delineation algorithm: sensitivity above 97% for peaks and 96% for onsets/offsets on the QT
  database, and mean errors within the CSE (Committee of General Standards for Electrocardiography) tolerances, except
  P-wave onsets.
- For us: a related wavelet method, not the one NeuroKit2 uses. To my knowledge NeuroKit2's "dwt" delineator follows
  Martinez et al. 2004 (PubMed 15072211, paywalled; not re-verified here). The relevant point is that wavelet
  delineators have known tolerance limits.

### 5. Pre-hospital management of heart attack using tele-ECG (arXiv 1805.05913)
- A prototype tele-ECG system in Tehran with an automatic measurement algorithm. Background only.

## New check, relative to our project: do the hard recordings carry PTB-XL's own flags?
Script: scripts/analysis/hard_recordings_vs_ptbxl_flags.py. Target: heart rate unreadable or off by more than 5 bpm
(the primary target). 49 reliable recordings, 1,519 tests, 99 bad readings.

| Recording | Bad / 31 | PTB-XL flag |
|---|---|---|
| 14808_lr | 27 | extra beats ("4ES") |
| 13323_lr | 13 | burst noise and baseline drift |
| 11236_lr | 11 | pacemaker |
| 13316_lr | 8 | none |
| 01126_lr | 6 | none |

- Recordings with any PTB-XL quality flag: 14 records, 61 bad readings of 434 tests (14.1%).
  Unflagged: 35 records, 38 of 1,085 (3.5%). About four times higher.
- By flag: extra beats 21.3% (5 records), pacemaker 35.5% (1 record), burst noise 16.1% (3), baseline drift 17.2% (3),
  static noise 0.8% (4 records).
- Honest limits: only 14 flagged records, and three recordings (14808, 13323, 11236) carry most of the effect; two of
  the five hardest recordings (13316, 01126) have no flag. This is a pattern in 49 recordings, not a tested predictor.
- Meaning: much of the heart-rate failure follows the recording's own content (premature beats, bursts of noise, a
  pacemaker), whatever the damage. That agrees with the earlier finding that 65 of 99 bad readings come from 5 recordings,
  and it explains why a photo-only detector has a low ceiling.

## What Section B means for the project
1. Our dataset is standard and well documented, and its own flags explain a large part of the failures. The write-up
   should say this plainly, and the stress-test result should be shown with and without flagged recordings.
2. Our reference intervals come from one open algorithm. Compare them with PTB-XL+ values (12SL, Glasgow, ECGDeli) for
   the 50 recordings; that would put a number on how much of the 20 ms clean-image noise floor is truth error rather than
   digitiser error. Not done yet.
3. The original data are 400 Hz. Our first sweep used the 100 Hz copy for ground truth, where one sample is 10 ms; the
   500 Hz files are upsampled, so they add no real information beyond 400 Hz.
4. Labels are not all human-validated (about 74% overall). Fine for our use, but state it.

## Related papers from other folders that belong with measurement (read earlier, key sections only)
Vandenberk 2016 (Bazett worst, Fridericia/Framingham best), the QTc-variability review (2020), the automatic QT-interval
algorithm paper (PMC5581168: automatic QT matches trained readers but errs when T-wave amplitude is low).
