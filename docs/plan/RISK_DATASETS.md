# Datasets for an ECG-based risk estimate (searched 2026-11-15)

Question: which public datasets link ECGs to what happened to patients later, so that a risk estimate could be trained and checked? PTB-XL has cardiologist labels but no follow-up, so it cannot give a risk.

| Dataset | Outcome | Access | Size | Fit for us |
|---|---|---|---|---|
| **CODE-15%** (Telehealth Network of Minas Gerais, Brazil; Zenodo 10.5281/zenodo.4916206) | `death` (true if the patient dies during follow-up) and `timey` (time to death, or follow-up time if alive), **only on each patient's first exam**; all-cause death | **Open, CC-BY 4.0**, no sign-up | 345,779 exams, 233,770 patients; 46.3 GB (exams.csv 35.5 MB + 18 zip parts of about 2.7 GB); HDF5, 400 Hz, 12 leads | **Best fit.** The page does not state the unit of `timey`, how follow-up or death was ascertained, or the follow-up length: check in the data and the papers before use |
| **MIMIC-IV-ECG** (Beth Israel Deaconess, PhysioNet) | Linkable to MIMIC-IV hospital records (deaths from state and hospital records) | **Credentialed**: PhysioNet data use agreement and training, approval takes days to weeks | about 800,000 ECGs, about 160,000 patients, 500 Hz | Sicker hospital population (mortality 27.8% in the benchmark), so not representative of people photographing a home ECG. Start the application now in parallel |
| CODE-II-open | not confirmed | open subset of 15,000 patients | small | Check whether it carries outcomes |
| Danish nationwide ECG cohort, UK Biobank, Framingham, ARIC, MESA | long follow-up | restricted (collaboration, application, months) | large | Not possible before 20 Nov |

## What the literature says an ECG-only mortality model can do (Lukyanenko et al. 2024, arXiv 2406.17002, benchmark on CODE-15% and MIMIC-IV-ECG)
- All-cause mortality, ECG only: 1-year AUROC about 0.80 to 0.82 on CODE-15% (train and test on the same source), concordance about 0.80.
- **Moving to another source loses 0.1 to 0.15 AUROC** (about 0.64 to 0.73). Classifier-based models needed site-specific calibration. The authors do not claim clinical validity.
- Event rates in CODE-15%: cumulative mortality 1.23% by year 1, 3.36% by year 5, 3.6% overall (low, so absolute probabilities are small and thresholds for "Low / Moderate / High" would be a matter of choice).

## What this means for MediSense-Cardio (honest limits)
1. The outcome is **all-cause mortality**, not "heart attack risk". Any score must be named "ECG-estimated all-cause mortality risk (research)", never "heart disease risk".
2. A model can be trained and checked on the original signals of CODE-15%. **Outcome validation on photos is impossible**: none of our digitised photos or pages has follow-up data. Only a transfer check is possible: how much does the predicted risk of the same ECG change between the original signal and its digitised version (we have about 700 digitised PTB-XL items).
3. Low / Moderate / High cut-offs on absolute probability are a choice, not a finding: they need the guide's approval and a clear statement of how they were set.
4. The population is Brazilian primary-care patients (2010 to 2016 per the Zenodo page), 400 Hz, one source: expect the cross-source drop above.

## Proposed pilot (needs a yes to download)
`exams.csv` (35.5 MB) plus HDF5 parts 0 to 3 (about 11 GB, about 77,000 exams): train a 5-year all-cause mortality classifier on the original signals with a patient-level split, calibrate it, report AUROC, calibration and the transfer check on our digitised items. Every rule is logged before any result.

Sources: https://zenodo.org/records/4916206, https://physionet.org/content/mimic-iv-ecg/1.0/, https://arxiv.org/html/2406.17002v1
