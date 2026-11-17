# Related-work table (for the guide)

Source: papers in C:\ECG research and Downloads, read 2026-11-04. "Read" says how deeply:
FULL = whole paper; KEY = abstract, intro, results/discussion, limitations, conclusion.
Detail and caveats are in docs/literature_notes.md; links are in docs/literature_list.md.

## A. Same problem: digitising paper/photo ECGs and testing it

| Paper | What they did | Main finding | How we differ | Read |
|---|---|---|---|---|
| engrXiv 8013, Qasmi and Ali | PhysioNet 2024 data, 9 ready-made capture types, 3 methods, per-type SNR | Classical tracer negative on all types; neural pipeline about 25.6 dB, flat across types | We damage one thing at a time over 5 severities, measure HR/PR/QRS/QT/QTc, define false reassurance, add a photo-only gate. Their own future work asks for the SNR-to-clinical link | FULL |
| Open-ECG-Digitizer, Stenhede et al. (npj Digit Med 2026) | The digitiser we test; trained on synthetic images; real hospital scans and phone photos | SNR 19.65 dB scanner vs 12.19 and 10.47 dB phones; unreadable leads set to NaN | We stress-test this exact tool under controlled damage and count unreadable as bad. Their phone-vs-scan gap is the real-photo gap we cannot close | FULL |
| VLM-in-the-Loop, Li et al. (2026) | QA module after digitising: signal-quality indices plus a vision-language judge | Consistency 71 to 89% with tool evidence; AUROC for fidelity only 0.64; all 3 published digitisers failed on 428 real archive scans | Ours gates on the photo alone, before digitising, and targets clinically wrong readings. Both studies find prediction is hard (0.64 vs our 0.607) | FULL |
| Moody Challenge 2024 overview, Reyna et al. | 62 teams; real hidden set of 35,595 images | SNR does not reflect clinical measures; negative-SNR teams still classified well | Motivation for measuring intervals instead of SNR | KEY |
| SignalSavants, Krones et al. (winner) | Hough rotation, nnU-Net, mask vectorisation | 17.02 dB CV; 12.15 leaderboard; 0.57 mean over all real variants; no positive score on stained phone photos | Quantifies the real-photo gap that our simulated damage cannot reproduce | KEY |
| ECG-Image-Kit, Shivashankara et al. | Synthetic ECG image generator; case study incl. QRS, RR, QT comparison on 10,000 synthetic images | Reference and digitised intervals "highly correlated" (scatter plots, no summary numbers); authors say not indicative of real clinical accuracy | Intervals compared before, on synthetic images only. Our artifacts differ (no wrinkles, creases, handwriting, perspective) | FULL (method detail skimmed) |
| ECGtizer, Lence et al. | Automated digitiser with lost-signal recovery; JOCOVID 807 real hospital ECGs (device PDFs) | Mean absolute time difference 25 to 28 ms (best methods); QT difference 0.04 to 0.09 s, QRS 0.02 to 0.06 s | Even on clean printouts intervals are off by tens of ms: supports our ~20 ms noise floor. Not tested on creased or low-quality scans (their limitation) | FULL (method detail skimmed) |
| PTB-Image / VinDigitizer, Nguyen et al. (arXiv 2502.14909) | Printed and scanned 549 PTB records; digitised with VinDigitizer | Mean SNR 0.01 dB on scans. The classification comparison in the abstract is "work in progress": no results in the paper | Preliminary dataset note. Do not cite it as showing accuracy falls with scan quality | FULL |

## B. Method background

| Topic | Papers | What they tell us | Read |
|---|---|---|---|
| QT correction | Vandenberk 2016; QTc variability review 2020 | Bazett over-corrects at high HR; Fridericia/Framingham better; Bazett healthy upper limit 472/482 ms exceeds 450/460 cut-offs | KEY |
| Interval measurement | QT algorithm (PMC5581168); wavelet delineation (1808.04804) | Automated QT matches trained readers but errs on low T-wave amplitude | KEY |
| Datasets | PTB-XL (Sci Data 2020), PTB-XL+ (2023), PTB-XL benchmarks | Source of our recordings and reference features | KEY |
| Graded corruption benchmarks | ImageNet-C, MedMNIST-C, pathology corruptions, CheXphoto/CheXphotogenic | Severity-graded damage is a standard design; photo-of-image is a known test | KEY |
| Synthetic vs real damage | 2505.04835; augmentation-corruption 2102.11273 | Mean ranking transfers, specific corruptions (brightness, fog) transfer poorly; robustness may not generalise to unseen types | KEY |

## C. Gate and decision papers

| Topic | Papers | What they tell us | Read |
|---|---|---|---|
| Photo or document quality | DocIQ; text-line DIQA | No-reference scoring exists for documents, trained on human ratings/OCR | KEY |
| ECG signal quality | PMC7517279, PMC8539388 | Judge the signal, not the photo | KEY |
| Risk control / conformal | RCPS, Learn-then-Test, Conformal Risk Control, CP introduction, class-conditional CP | Threshold with a stated guarantee, needs calibration data and exchangeability | KEY |
| Limits of conformal in medicine | 2506.18162 | Unreliable under distribution shift; do not use to select predictions | KEY |
| Deferral to humans | Learning to defer; guided deferral; biosignal UQ review | Pass hard cases to people; study in situ | KEY |
| Human response to abstention | 2508.07617 (259 clinicians) | Abstention helps partly but raises false negatives | KEY |
| Real-world validation | DR pivotal trial; seven-system DR head-to-head | External validation reveals gaps; image-quality handling matters | KEY (trial: abstract only) |

## D. Standards

| Topic | Paper | Use for us | Read |
|---|---|---|---|
| Sample size | Riley (BMJ 2020; Stat Med part II) | 10 events/predictor is only a rule of thumb; our 99 events cluster in few recordings | KEY |
| Reporting | CLAIM 2024 | State level of data splitting (we split by recording) | KEY |
| Calibration | Van Calster 2019 | Check calibration of our risk scores (not done) | KEY |
| Simulation reporting | Morris 2019 | Describe simulated damage design transparently | KEY |

## Three sentences for "how is this different from existing work?"
1. Existing digitiser papers report SNR, mostly on dataset-defined capture types; we apply one controlled damage
   type at a time over five severities and measure the clinical numbers a patient-facing statement would use.
2. We define false reassurance (a normal-looking digitised value when the truth is abnormal) and measure how
   often damage causes it.
3. We test a photo-only warning before digitising. It is a weak prototype (held-out AUC 0.607 on the primary
   target, poor on unseen damage types), reported as such.
