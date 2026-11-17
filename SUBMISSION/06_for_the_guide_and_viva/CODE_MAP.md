# MediSense-Cardio: code map

A research prototype, not a medical device. All paths are relative to `D:\Capstone Project`.
Every number in the report comes from `results/FINAL_NUMBERS.md`. Rules for each analysis were written in `docs/plan/analysis_plan_changes.md` before the run.

## 1. The pipeline, in order

| Step | What it does | Code | How to run |
|---|---|---|---|
| 1. Pick recordings | Random pick of 100 new PTB-XL recordings (seed 42) | `scripts/analysis/select_extension_100.py` | `python -I scripts/analysis/select_extension_100.py` |
| 2. Draw the page | Plots the numbers as a paper-style page (25 mm/s, 10 mm/mV, 2200 x 1700 px) | ECG-Image-Kit in `scripts/tools/ecg-image-kit/` (patched `gen_ecg_image_from_data.py`, called from the sweep notebooks) | Runs inside the notebooks of step 4 |
| 3. Damage the page | 6 damage types x 5 levels | `scripts/quality_proxy/degrade.py` | Imported by the notebooks and scripts |
| 4. Run the sweeps | Draw, damage, digitise, measure heart rate | `colab/MediSense_Cardio_FullSweep_v2_Intervals.ipynb` (first 50), `colab/MediSense_Cardio_Extension_150.ipynb` (new 100), `colab/MediSense_Cardio_Bridge_Run.ipynb` (repeat check) | Colab: upload, Run all |
| 5. Digitise | Picture to 12-lead signal (1,000 Hz, microvolts) | `scripts/tools/Open-ECG-Digitizer/` (unchanged, commit 97a15087). Main files: `src/model/inference_wrapper.py`, `signal_extractor.py` | From inside that folder: `python -m src.digitize --config <settings>.yml` |
| 6. Real captures | Competition photos and scans; your own phone photos | `colab/MediSense_Cardio_ArmC_Kaggle_RealCaptures.ipynb`, `..._ArmCext_*_Kaggle.ipynb`, `..._OwnPhotos_Kaggle.ipynb` | Kaggle (GPU), not Colab |
| 7. Photo scores | 5 scores from the picture alone | `scripts/quality_proxy/image_quality.py` | Imported by the notebooks |
| 8. Analysis | Rates, tests, detectors (table 2) | `scripts/analysis/section_*.py` | See table 2 |
| 9. Traffic light | GREEN / AMBER / RED from the digitised signal | `safeguard/` (table 3) | See table 3 |
| 10. Fix | Find the page and straighten it | `scripts/preprocess/page_straighten.py` | Imported by the demo and the fix notebooks |
| 11. Demo | Photo in, heart rate, light and a plain-words patient explanation out | `demo/` (`app.py`, `pipeline.py`, `explain.py`, `new_samples/`) | Double-click `demo\run_demo.bat`, then open http://127.0.0.1:7860 |
| 12. Patient explanation | Fixed sentences, a wording checker and tests; the PR interval is shown for GREEN straightened photos only | `demo/explain.py`, `demo/pr_interval.py` and `demo/axis_deg.py` (run the frozen Section U and W methods), `demo/tests/test_explanation.py` (19 tests), rules in `docs/plan/EXPLANATION_WORDING.md` | `python -I demo/tests/test_explanation.py` |

## 2. Analysis scripts (`scripts/analysis/`)

| Script | Question it answers | Status |
|---|---|---|
| `section_C.py` | Which damage makes heart rate wrong, and how often? (claims C1, C2) | Pre-specified |
| `section_D.py` | Can the 5 photo scores warn? (claim C3) | Pre-specified, inconclusive |
| `section_A.py` | Aligned SNR, and paired error against the clean page | Pre-specified |
| `section_B.py` | Reference checks, intervals, second detector, flagged recordings | Exploratory |
| `section_E.py` | Coverage curve: how many wrong readings a flag catches | Exploratory |
| `section_G.py` | Calibration, sample size (Riley), CLAIM checklist | Exploratory |
| `section_D2_features.py` and `section_D2.py` | Can 15 features of the digitised signal catch failures? | Exploratory |
| `section_H.py` | Real captures: rates by capture type (Arm C and C+) | Exploratory |
| `section_I_clean_page.py`, `section_I2_truth.py`, `section_I3_sensitivity.py` | Why do clean pages give wrong readings? | Post hoc |
| `section_J_remeasure.py`, `section_K_remeasure_sim.py` | Cleaned heart-rate measure (real and simulated) | Post hoc |
| `section_L.py` | Output check and photo detector repeated with the cleaned labels | Post hoc |
| `section_M.py`, `section_M_features.py` | Do 5 beat detectors add value? (rule not met) | Exploratory |
| `section_N_real_photo.py` | Can photo scores predict failure on real captures? | Exploratory |
| `section_O_ownphotos.py` | Frozen models on your 60 phone photos | Exploratory confirmation |
| `section_Q_fixexp.py <kaggle_output_dir>` | Fix experiment on the first 60 photos | Exploratory |
| `section_Q2_confirm.py <kaggle_output_dir>` | Fix confirmation on 40 new photos | Confirmed (p = 0.0005) |
| `final_numbers_recompute.py` | Recomputes 36 headline numbers from raw files | Check script |
| `dataset_inventory.py` | One sheet listing every recording, its images, true signal, 12SL values and flags (`results/DATASET_INVENTORY.csv`) | Inventory (no new result) |
| `section_R_waveform_errors.py` | Waveform errors of the digitised lead II: MAE, RMSE, correlation, gain, R-peak amplitude and timing (`results/analysis/SECTION_R.md`) | Exploratory, added after the freeze |
| `section_T_better_qt.py` (`--dev`, `--test`, `--confirm`) | A better QT method (median beat, tangent T end): development on the first 50, one held-out test, one confirmation on new phone photos (`SECTION_T*.md`) | Exploratory, added after the freeze; close but not validated |
| `section_V_qrs_qt_v2.py` (`--dev`, `--test`, `--confirm`) | QRS duration and QT, second attempt on fresh data: 1,000 development recordings, one test on 100 fresh pages, one confirmation on phone photos (`SECTION_V*.md`) | Exploratory; neither validated |
| `section_W_axis.py` (`--dev`, `--test`, `--confirm`) | Frontal QRS axis from six limb leads; same discipline (`SECTION_W*.md`) | Exploratory; validated for straightened photos |
| `select_fresh_sets.py`, `make_fresh_pages.py`, `digitise_fresh_pages.py` | Choose the 100 fresh recordings and 1,000 development recordings, draw the fresh pages with a patched copy of ECG-Image-Kit, digitise them on the GPU (`results/fresh/`) | Data preparation |
| `section_U_pr_qrs.py` (`--dev`, `--test`, `--confirm`) | PR and QRS with my own median-beat method: development on the first 50, one held-out test, one confirmation on new phone photos (`SECTION_U*.md`) | Exploratory, added after the freeze; PR validated under the pre-set rule, QRS not |
| `section_S_intervals_digitised.py` | PR, QRS, QT on the digitised lead II against 12SL, with a pre-set acceptance rule (`results/analysis/SECTION_S.md`) | Exploratory, added after the freeze; no interval validated |
| `section_X_global_qrs_qt.py` (`--dev`, `--test`, `--confirm`) | Third attempt at QRS duration and QT (combined leads): QT stopped in development, QRS not validated (`SECTION_X*.md`) | Exploratory; not validated |
| `section_Y_p_t_amplitude.py` | P-wave and T-wave amplitude of lead II against 12SL (`SECTION_Y*.md`) | Exploratory; not validated |
| `section_Z_sim_photos.py`, `make_sim_photos.py` | 120 SIMULATED phone photos: straightening and traffic light (`SECTION_Z.md`) | Exploratory; confirmed in simulation |
| `section_H_paper.py`, `make_paper_pages.py`, `select_paper_20.py`, `digitise_paper_photos.py` | Printed-paper photo test (pages H01-H20); waiting for the 40 photos | Prepared, not run |
| `section_RC_risk_coverage.py` | Risk-coverage curves of the traffic light and the photo detector from saved scores (`SECTION_RC.md`, `sectionRC_risk_coverage.png`) | Exploratory, descriptive |
| `section_CI_bland_altman.py` | Bland-Altman pictures (heart rate, PR, axis) and cluster-bootstrap intervals (`SECTION_CI.md`, `sectionCI_bland_altman.png`) | Exploratory, descriptive |
| `section_FG_failure_gallery.py` | Eight failures chosen by a rule, as pictures (`SECTION_FG.md`, `sectionFG_failure_gallery.png`) | Descriptive |
| `repeat_variation_demo.py`, `repeat_variation_summary.py` | Repeat variation of the demo pipeline on the same photo (`results/reproducibility/`) | Descriptive; GPU environment |
| `second_person_green_count.py` | Third number of the second-person check (GREEN wrong, 2 of 917) | Check script |
| `demo/health/` (`data.py`, `model.py`, `train.py`, `evaluate.py`, `assess.py`, `dashboard.py`, `wording.py`) | Heart health module: ECG-pattern model trained on PTB-XL, one test, assessment logic, Plotly dashboard, own wording rules (`results/health/SECTION_HEALTH.md`) | Exploratory; MI, STTC, CD shown on photos |
| `scripts/analysis/health_demo_samples_check.py` | The module end to end on the six demo photos (`results/health/demo_samples_check.md`) | Descriptive |

Each script writes its tables to `results/analysis/` (`SECTION_X.md` plus CSV files).
Run with `python -I scripts/analysis/<script>.py` (Sections O, Q and Q2 take a folder argument, shown in the file header).

## 3. Traffic light (`safeguard/`)

| File | Role |
|---|---|
| `ecg_traffic_light.py` | The tool: 15 features, then a logistic score, then the light |
| `model.json` | Frozen model and thresholds (AMBER 0.2585, RED 0.7823) |
| `train_safeguard.py` | Builds `model.json` from the simulated new 100 only (run once) |
| `evaluate_safeguard.py` | Evaluates the frozen tool once: `python -I safeguard/evaluate_safeguard.py` |
| `summarize_safeguard.py` | Makes the result tables (Section P) |
| `tests/test_traffic_light.py` | Unit tests |

## 4. Notebooks and builders
- Notebook list and purpose: `colab/README.md`.
- Never edit notebook cells by hand. Change the builder in `scripts/notebook_builders/` and upload the rebuilt notebook.

## 5. Reproducing the numbers
Full guide (versions, tool commits, patches, what is not exact, a one-page check for a second person): `reproducibility/REPRODUCE.md`.

```
python -I scripts/analysis/final_numbers_recompute.py
```
It prints `recomputed | reported | MATCH or DIFFERENT` for each of 36 numbers. All match. It is a second script by the same author, not a second person, and it does not re-run the digitizer.

## 6. Where to read next
1. `README.md` (start here)
2. `docs/plan/MASTER_PLAN.md`, `CLAIMS_REGISTER.md`, `PROGRESS-LOG.md`
3. `docs/reports/METHODS_AND_FORMULAE.md` (all methods and formulae)
4. `results/FINAL_NUMBERS.md` (all numbers, what may and may not be claimed)

## 9. Late additions (16 to 17 Nov 2026): fresh dataset-picture sets, retrained pattern networks, QT retry

All paths relative to `D:\Capstone Project`. Run with `demo\.venv-gpu\Scripts\python.exe -I <script>` (the GPU environment). Each test script refuses to run twice (rule: test once).

| Step | Code | Output |
|---|---|---|
| Choose fresh recordings, set P / Q / R | `scripts/analysis/select_P_fresh.py`, `select_Q_fresh.py`, `select_R_fresh.py` | `results/paper_p|q|r/selected_*.csv` |
| Draw pages, make simulated phone photos, digitise | `scripts/analysis/make_pages_generic.py`, `make_sim_photos_P|Q|R.py`, `digitise_pages_generic.py`, `digitise_sim_photos_P|Q|R.py`; pipeline runners `results/paper_p/run_P_chain.bat`, `results/paper_q/run_Q_resume.py`, `results/paper_r/run_R.py` | digitised pages and photos in `results/paper_*/` |
| Pattern networks A and B (first versions) | `scripts/analysis/section_FIND2_train.py A|B`; network code `demo/health/model.py`, `find2.py` | `results/find2_A`, `find2_B` |
| Strict operating point (specificity 0.97) | `scripts/analysis/section_OP_thresholds.py`, `section_OP_apply.py` | `results/find2_op/` |
| Retrained networks A2 and B2 (strong photo damage) | `scripts/analysis/section_Q_train.py A|B` (`model.strong_damage` in `demo/health/model.py`) | `results/find2_A2`, `find2_B2` (with `thresholds_q.json`) |
| One-time tests and verdicts | `scripts/analysis/section_P_test.py`, `section_P_verdict.py`, `section_Q_test.py`, `section_Q_verdict.py`, `section_R_test.py`, `section_R_verdict.py`; pooled numbers `section_QR_pooled.py` | `SECTION_P|Q|R.md`, `*_status.json`, `results/paper_r/final_status.json` (read by the app) |
| QT and QRS retry on doctor-marked data (LUDB, QT Database) | `scripts/analysis/qt_public_parse.py`, `qt_public_train.py`, `qt_public_test_T1.py`, `qt_public_test_T2.py` | `results/qt_public/` |
| In the app | `demo/health/assess.py` (`promote_validated`, `promote_q`, `apply_qt`, all gated by the status files), `demo/health/dashboard.py`, `demo/health/wording.py` | `demo/tests/` (run `python -I demo/tests/test_health.py`) |
| Gallery tab | `scripts/tools/build_gallery_cache.py`, `make_dataset_examples.py`, `demo/gallery.py` | `results/paper_n/gallery_cache.json`, `demo/dataset_examples/` |
| Report, paper, poster, figure | `scripts/tools/build_report_v4.py`, `finalize_report.ps1`, `check_report_pdf.py`, `make_paper_zip.py`, `check_tex.py`, `make_poster.py`, `export_pptx.ps1`, `make_results_at_a_glance.py`, `plagiarism_self_check.py` | `docs/reports/`, `docs/paper/` |
| Submission folder | `scripts/tools/make_submission_folder.py` | `SUBMISSION/` |

