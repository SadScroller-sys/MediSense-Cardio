# Literature list for MediSense-Cardio

Built 2026-11-04 from the links collected during the earlier literature search in this project.
arXiv titles were fetched from the arXiv API. Entries marked "title not verified" are links I
collected earlier but have not re-opened; check them before citing.

## A. ECG digitisation (closest to our work)
- 2510.19590 (2025) Digitizing Paper ECGs at Scale: An Open-Source Algorithm for Clinical Research -- https://arxiv.org/abs/2510.19590 (Open-ECG-Digitizer, the tool we stress-test; code https://github.com/Ahus-AIM/Open-ECG-Digitizer)
- 2604.00396 (2026) VLM-in-the-Loop: A Plug-In Quality Assurance Module for ECG Digitization Pipelines -- https://arxiv.org/abs/2604.00396 (overlaps our quality-gate idea; must cite and differentiate)
- engrXiv 8013: How Robust Are ECG Image Digitizers to Image Damage? A Per-Type, Per-Method Study -- https://engrxiv.org/preprint/view/8013 (CLOSEST OVERLAP: same question as ours, damage type by type. Must read in full and state clearly how our study differs.)
- npj Digital Medicine 2026, same Open-ECG-Digitizer paper, published version -- https://www.nature.com/articles/s41746-025-02327-1 and https://pmc.ncbi.nlm.nih.gov/articles/PMC12891466
- 2307.01946 (2023) ECG-Image-Kit: A Synthetic Image Generation Toolbox to Facilitate Deep Learning-Based ECG Digitization -- https://arxiv.org/abs/2307.01946 (generates our drawn pages; https://github.com/alphanumericslab/ecg-image-kit)
- 2412.12139 (2024) ECGtizer: a fully automated digitizing and signal recovery pipeline for electrocardiograms -- https://arxiv.org/abs/2412.12139
- 2410.14185 (2024) Combining Hough Transform and Deep Learning Approaches to Reconstruct ECG Signals From Printouts -- https://arxiv.org/abs/2410.14185
- 2502.14909 (2025) Comparing Deep Neural Network for Multi-Label ECG Diagnosis From Scanned ECG -- https://arxiv.org/abs/2502.14909
- https://github.com/felixkrones/ECG-Digitiser (code; paper title not verified)

## B. Dataset and ECG measurement
- PTB-XL dataset paper (Scientific Data 2020) -- https://www.nature.com/articles/s41597-020-0495-6 ; data https://physionet.org/content/ptb-xl/1.0.3/
- PTB-XL+, a comprehensive electrocardiographic feature dataset (Sci Data 2023) -- https://www.nature.com/articles/s41597-023-02153-8 ; https://physionet.org/content/ptb-xl-plus/1.0.1/
- 2004.13701 (2020) Deep Learning for ECG Analysis: Benchmarks and Insights from PTB-XL -- https://arxiv.org/abs/2004.13701
- 1808.04804 (2018) Finding morphology points of electrocardiographic signal waves using wavelet analysis -- https://arxiv.org/abs/1808.04804
- 1805.05913 (2018) Pre-Hospital Management of Acute Myocardial Infarction Using Tele-Electrocardiography System -- https://arxiv.org/abs/1805.05913
- AHA/ACCF/HRS recommendations for the standardization and interpretation of the ECG, part IV: ST segment, T and U waves, and the QT interval (Circulation 2009) -- https://pubmed.ncbi.nlm.nih.gov/19228821 (source of QT cut-offs)
- Which QT Correction Formulae to Use for QT Monitoring? (J Am Heart Assoc 2016) -- https://pmc.ncbi.nlm.nih.gov/articles/PMC4937268 (Bazett vs Fridericia)
- Sources of QTc variability: implications for effective ECG monitoring in clinical practice (Ann Noninvasive Electrocardiol 2020) -- https://pmc.ncbi.nlm.nih.gov/articles/PMC7358850
- Correlation of QT interval correction methods during atrial fibrillation and sinus rhythm (Am J Cardiol 2013) -- https://pubmed.ncbi.nlm.nih.gov/23972343
- Intra- and interreader variability in QT interval measurement by tangent and threshold methods (J Electrocardiol 2009) -- https://pubmed.ncbi.nlm.nih.gov/19261293 (why ~20 ms interval noise is normal)
- The development and validation of an easy to use automatic QT-interval algorithm (PLoS One 2017) -- https://pmc.ncbi.nlm.nih.gov/articles/PMC5581168
- A wavelet-based ECG delineator: evaluation on standard databases (IEEE Trans Biomed Eng 2004) -- https://pubmed.ncbi.nlm.nih.gov/15072211 (basis of NeuroKit2's interval method)

## B2. ECG signal quality assessment (related to our quality gate)
- A Deep Learning Approach for Featureless Robust Quality Assessment of Intermittent AF Recordings from Portable and Wearable Devices (Entropy 2020) -- https://pmc.ncbi.nlm.nih.gov/articles/PMC7517279
- ECG Quality Assessment with a Generalized Deep Learning Model Assisted by Conditional GANs (Life 2021) -- https://pmc.ncbi.nlm.nih.gov/articles/PMC8539388
- Clinical validation of a novel smartwatch for automated detection of atrial fibrillation (Heart Rhythm O2 2022) -- https://pmc.ncbi.nlm.nih.gov/articles/PMC9043399

## C. Image damage and robustness (does synthetic damage match real photos?)
- 2505.04835 (2025) Are Synthetic Corruptions A Reliable Proxy For Real-World Corruptions? -- https://arxiv.org/abs/2505.04835
- 1903.12261 (2019) Benchmarking Neural Network Robustness to Common Corruptions and Perturbations -- https://arxiv.org/abs/1903.12261
- 2007.06199 (2020) CheXphoto: 10,000+ Photos and Transformations of Chest X-rays -- https://arxiv.org/abs/2007.06199
- 2011.06129 (2020) CheXphotogenic: Generalization of DL Models for Chest X-ray Interpretation to Photos of Chest X-rays -- https://arxiv.org/abs/2011.06129
- 2406.17536 (2024) MedMNIST-C: benchmark and improved classifier robustness by simulating realistic image corruptions -- https://arxiv.org/abs/2406.17536
- 2206.14973 (2022) Benchmarking the Robustness of DNNs to Common Corruptions in Digital Pathology -- https://arxiv.org/abs/2206.14973
- 2102.11273 (2021) On Interaction Between Augmentations and Corruptions in Natural Corruption Robustness -- https://arxiv.org/abs/2102.11273

## D. No-reference image quality
- 2509.17012 (2025) DocIQ: A Benchmark Dataset and Feature Fusion Network for Document Image Quality Assessment -- https://arxiv.org/abs/2509.17012
- 1906.01907 (2019) Towards Document Image Quality Assessment: A Text Line Based Framework and A Synthetic Text Line Image Dataset -- https://arxiv.org/abs/1906.01907

## E. Selective prediction / deferral / risk control (our "flag the risky photo" gate)
- 2110.01052 (2021) Learn then Test: Calibrating Predictive Algorithms to Achieve Risk Control -- https://arxiv.org/abs/2110.01052
- 2101.02703 (2021) Distribution-Free, Risk-Controlling Prediction Sets -- https://arxiv.org/abs/2101.02703
- 2208.02814 (2022) Conformal Risk Control -- https://arxiv.org/abs/2208.02814
- 2107.07511 (2021) A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification -- https://arxiv.org/abs/2107.07511
- 2306.09335 (2023) Class-Conditional Conformal Prediction with Many Classes -- https://arxiv.org/abs/2306.09335
- 2506.18162 (2025) Pitfalls of Conformal Predictions for Medical Image Classification -- https://arxiv.org/abs/2506.18162
- 1711.06664 (2017) Predict Responsibly: Improving Fairness and Accuracy by Learning to Defer -- https://arxiv.org/abs/1711.06664
- 2406.07212 (2024) Trustworthy and Practical AI for Healthcare: A Guided Deferral System with LLMs -- https://arxiv.org/abs/2406.07212
- 2312.09454 (2023) Uncertainty Quantification in Machine Learning for Biosignal Applications -- A Review -- https://arxiv.org/abs/2312.09454
- 2508.07617 (2025) Selective Prediction Reduces the Negative Effects of Automation Bias Overall but Increases False Negatives -- https://arxiv.org/abs/2508.07617

## F. Over-trust in AI output (supports "false reassurance")
- 2408.15266 (2024) People over trust AI-generated medical responses and view them to be as valid as doctors, despite low accuracy -- https://arxiv.org/abs/2408.15266
- 2605.00468 (2026) ReLay: Personalized LLM-Generated Plain-Language Summaries for Better Understanding, but at What Cost? -- https://arxiv.org/abs/2605.00468 (tangential)

## G. Reporting and method standards
- Checklist for Artificial Intelligence in Medical Imaging (CLAIM): 2024 Update (Radiol Artif Intell 2024) -- https://pmc.ncbi.nlm.nih.gov/articles/PMC11304031
- Calculating the sample size required for developing a clinical prediction model (BMJ 2020, Riley et al.) -- https://doi.org/10.1136/bmj.m441 (NOT TRIPOD+AI; this is the sample-size paper)
- Minimum sample size for developing a multivariable prediction model: PART II, binary and time-to-event outcomes (Stat Med 2019) -- https://pmc.ncbi.nlm.nih.gov/articles/PMC6519266
- Calibration: the Achilles heel of predictive analytics (BMC Med 2019) -- https://pmc.ncbi.nlm.nih.gov/articles/PMC6912996
- Using simulation studies to evaluate statistical methods (Stat Med 2019) -- https://pmc.ncbi.nlm.nih.gov/articles/PMC6492164
- TRIPOD+AI itself is still not in this list; add it (BMJ 2024) when you download papers.

## H. Real-world validation of AI screening, and abstention in medicine
- Pivotal trial of an autonomous AI-based diagnostic system for detection of diabetic retinopathy in primary care offices (npj Digit Med 2018) -- https://www.nature.com/articles/s41746-018-0040-6
- Multicenter, Head-to-Head, Real-World Validation Study of Seven Automated AI Diabetic Retinopathy Screening Systems (Diabetes Care 2021) -- https://pmc.ncbi.nlm.nih.gov/articles/PMC8132324 (a real-world image-quality gate example)
- Leveraging uncertainty information from deep neural networks for disease detection (Sci Rep 2017) -- https://pmc.ncbi.nlm.nih.gov/articles/PMC5736701
- Conformal selective prediction with cost aware deferral for safe clinical triage under distribution shift (Sci Rep 2026) -- https://www.nature.com/articles/s41598-026-40637-w
- Uncertainty-aware abstention in medical diagnosis based on medical texts (npj Artif Intell 2026) -- https://www.nature.com/articles/s44387-026-00097-z

## I. Patient-facing AI safety (context for "false reassurance"; tangential to the engineering)
- A novel evaluation benchmark for medical LLMs illuminating safety and effectiveness in clinical domains (npj Digit Med 2025) -- https://pmc.ncbi.nlm.nih.gov/articles/PMC12855988
- Assessment of patient information guides generated by LLMs for common cardiological procedures (Glob Cardiol Sci Pract 2025) -- https://pmc.ncbi.nlm.nih.gov/articles/PMC13025549
- Safety guardrails in patient-facing LLM systems for chronic disease self-management: a realist review (Int J Med Inform 2026) -- https://pubmed.ncbi.nlm.nih.gov/42224752

## Status
- All titles above are verified against the arXiv, PubMed/PMC and Crossref records (2026-11-04). Verified means the title and venue match the link; I have not yet read each paper in full again.
- Not found as separate papers: the GitHub repos (Open-ECG-Digitizer, ecg-image-kit, ECG-Digitiser by felixkrones, ecgtizer) are code, not papers.
- To study them properly, download the PDFs into D:\Capstone Project\papers\ and I will read them and fill in a
  per-paper table (what they did, what they found, how we differ).

## J. Papers we did NOT have (found 2026-11-04; not downloaded, not read; verified only from search results)
- ECG-Image-Database: A Dataset of ECG Images with Real-World Imaging and Scanning Artifacts (Reyna, Clifford, Sameni et al., 2024) -- https://arxiv.org/abs/2409.16612 ; the hidden real test set of the Moody Challenge (35,595 images, soaked/stained/moldy/photographed).
- Automatic digitization of paper electrocardiograms: a systematic review (Lence et al., J Electrocardiol 2023;80:125-132) -- PMID 37352634, DOI 10.1016/j.jelectrocard.2023.05.009. Says shared benchmarks and metrics are lacking.
- TRIPOD+AI statement (Collins et al., BMJ 2024;385:e078378) -- DOI 10.1136/bmj-2023-078378. Open access.
- Development and Validation of an Algorithm for the Digitization of ECG Paper Images (Sensors 2022) -- https://pmc.ncbi.nlm.nih.gov/articles/PMC9572306 ; validates HR and QT on scanned paper (101 cases); small test set; figures differ between summaries, so check the full text.
- A fully-automated paper ECG digitisation algorithm using deep learning (Sci Rep 2022) -- https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9722713/ (title only checked).
- Demolder et al. 2025 (printed-and-photographed 6,000-image benchmark; cited by Open-ECG-Digitizer and engrXiv 8013): original not found by search; an arXiv paper 2602.07446 attributes a 6,000-image set to a different team, so authorship is unconfirmed.
- Fortune et al. 2022, Digitizing ECG Image: a new method and open-source software code -- https://pmc.ncbi.nlm.nih.gov/articles/PMC9286778/ (link taken from the engrXiv reference list).
- PTB-Image (Nguyen et al., 2025) and PTB-XL-Image-17K: named in engrXiv 8013; PTB-Image could not be confirmed by search.
