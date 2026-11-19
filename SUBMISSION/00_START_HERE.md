# MediSense-Cardio: submission folder

Built 18 Nov 2026 22:55 by `scripts/tools/make_submission_folder.py` (copies; the originals stay where the scripts expect them).
Research prototype for a university project. Not a medical device.

## What is where

| Folder | What is inside |
|---|---|
| `01_report/` | The project report (final review copy): `CAPSTONE_REPORT_v4_review.pdf`, `CAPSTONE_REPORT_v4_review.docx` |
| `02_paper/` | The conference paper (IEEE format). Upload the zip to Overleaf as a new project and compile: `medisense-cardio-paper-v2.zip`, `main_v2.tex`, `references.bib` |
| `03_poster/` | A0 poster: `MediSense_Cardio_A0_poster.pdf`, `MediSense_Cardio_A0_poster.pptx` |
| `04_results/` | All numbers and the test records (every number in the report, paper and poster comes from FINAL_NUMBERS.md): `FINAL_NUMBERS.md`, `README.md`, `SECTION_P.md`, `SECTION_Q.md`, `SECTION_OP.md`, `SECTION_R.md`, `POOLED_QR.md`, `R_status.json`, `final_status.json`, `T1_metrics.csv`, `T2_pages.csv`, `T2_sim.csv`, `P_status.json`, `Q_status.json`, `fig_results_at_a_glance.png` |
| `05_plan_and_rules/` | The rules written BEFORE each result, and the plan: `analysis_plan_changes.md`, `MASTER_PLAN.md`, `CLAIMS_REGISTER.md`, `PROGRESS-LOG.md` |
| `06_for_the_guide_and_viva/` | Guide approval sheet, viva questions and answers, methods, code map, plagiarism self-check: `GUIDE_APPROVAL_SHEET.md`, `VIVA_QA.md`, `METHODS_AND_FORMULAE.md`, `CODE_MAP.md`, `PLAGIARISM_SELF_CHECK.md` |
| `07_diary/` | Project diary: `Capstone_Project_Diary_filled_9weeks.pdf` |
| `08_reproducibility/` | How to rerun and check everything: `REPRODUCE.md`, `ENVIRONMENT.md`, `SECOND_PERSON_CHECK.md`, `CHECK_REPORT.md`, `run_all_checks.py`, `requirements_demo_gpu.txt`, `requirements_analysis_minimal.txt` |

## The code: `09_code/`

A readable copy of our own code (demo, heart health module, analysis scripts, builders, safeguard, Colab notebooks). The map of what each script does is `06_for_the_guide_and_viva/CODE_MAP.md`. Run the code from the original folders, not from this copy. The third-party tools (Open-ECG-Digitizer, ECG-Image-Kit), the Python environments, the data and the results are not copied: see `08_reproducibility/`.

## The demo (code stays in `demo/`, it needs the GPU environment and is too large to copy)

```
cd demo
run_demo.bat                      (opens http://localhost:7860)
```
Tabs: the picture check, the heart health assessment, **Our results (at a glance)**, **Dataset gallery (instant results)** (dataset pictures with the true answer next to the tool's answer), how it works.
Example pictures are in `demo/dataset_examples/` (12 dataset pictures with a key).

## The main findings in five lines

1. A GREEN heart rate from the traffic light is wrong 0.2% of the time (2 of 917 captures); on printed paper from another phone 2 of 19 were wrong, so it is not a guarantee.
2. Straightening the photo reduced bad readings (screen photos 14 to 2 of 40, p = 0.0005; printed paper 31 to 15 of 66).
3. Heart rate, PR interval and QRS axis are shown; QT and QRS duration are not (they failed their pre-set rules, twice).
4. Heart-attack and ST/T patterns are shown on photos; left bundle branch block and atrial fibrillation passed our rules on fresh dataset pictures only (not on real phone photos; AF passed on its second test); other patterns are research-only hints.
5. Mortality risk from the ECG was tried three times and failed its rules (the third missed only the calibration rule), so no validated risk is shown; the app has a separate, labelled research-only range.

Every pass rule was written before its result was seen and has not been approved by the guide.

## Original project folders (do not move: scripts have these paths inside)

`data/` (public datasets), `results/` (all runs), `scripts/` (analysis code), `demo/`, `colab/`, `docs/`, `reproducibility/`, `website/`, `safeguard/`. See the main `README.md`.


## The website: `10_website/`

The project website (static). Open `index.html`, or run `python -m http.server 8099` inside the folder and open http://127.0.0.1:8099. Updated 18 Nov 2026 with the latest results.
