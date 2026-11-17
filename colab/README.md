# colab/: which notebook is for what

**Current study**
- `MediSense_Cardio_Extension_150.ipynb`: adds 100 new recordings (running on Colab, about 7 h). Upload with File > Upload notebook, then Runtime > Run all.
- `MediSense_Cardio_FullSweep_v2_Intervals.ipynb`: the sweep of the first 50 recordings with intervals (done). `..._FullSweep_v1.ipynb`: the first sweep (heart rate only, done).
- `MediSense_Cardio_Detector_Heldout.ipynb`: held-out test of the photo-quality detector (done on the first 50; will be redone on 150).
- `MediSense_Cardio_Calibration.ipynb`: the earlier detector calibration.

**Explanations, demos and older work (for review meetings and history)**
- `MediSense_Cardio_FullSweep_v2_Results_Overview.ipynb`, `..._Methodology_Explained.ipynb`, `..._LiveProof_Demo.ipynb`, `..._QualityProxy_Demo.ipynb`, `..._Demo_v2.ipynb`
- `MediSense_Cardio_Analysis_Part1/1b/2/3_figures.ipynb`, `..._Harness_v1.ipynb`, `..._Calibration_Quick10.ipynb`

Never edit cells by hand in Colab. Rebuild the notebook with its builder in `scripts/notebook_builders/` and upload the new file.

- MediSense_Cardio_ArmC_Kaggle_RealCaptures.ipynb: runs on KAGGLE (not Colab). Real scans and phone photos from the PhysioNet Digitization competition data (attached as input, nothing downloaded). Built by scripts/notebook_builders/build_armC_kaggle_notebook.py.
- Bridge run notebook: MediSense_Cardio_Bridge_Run.ipynb (12 of the first 50 recordings x 13 versions; run after the extension run).

- MediSense_Cardio_ArmCext_Part1_Kaggle.ipynb and ..._Part2_Kaggle.ipynb (built by scripts/notebook_builders/build_armC_ext_notebooks.py): Arm C extension, 100 more real-capture recordings (seed 43, none of the 40 in Arm C), 50 per notebook, 450 images each (about 3-4 GPU hours on Kaggle); also computes the five photo scores of every captured page. Rules: docs/plan/analysis_plan_changes.md (2026-11-07).
- MediSense_Cardio_ArmCext_All100_Kaggle.ipynb: the same extension for all 100 recordings in ONE notebook (900 images, about 6-8 GPU hours; saves every 15 images, stops cleanly after 9.5 h). Use this OR Part1 + Part2, never both.
- MediSense_Cardio_TruthExport_Kaggle.ipynb (built by scripts/notebook_builders/build_truth_export_notebook.py): copies the TRUE lead II of the 140 real-capture recordings (Arm C 40 + extension 100) out of the Kaggle competition data (CPU, ~2-5 min). Needed for the clean-page diagnosis: is the reference or the digitised signal at fault? Output: truth_lead_II.npz, truth_meta.csv.
- MediSense_Cardio_OwnPhotos_Kaggle.ipynb (built by scripts/notebook_builders/build_ownphotos_notebook.py): digitises the user's 60 own-phone photos of ECG pages P01-P30 shown on a screen (same digitiser, commit, weights and settings as Arm C) and computes the five photo scores; GPU, about 30-40 min. Analysis: scripts/analysis/section_O_ownphotos.py (frozen models). Rules: docs/plan/analysis_plan_changes.md (2026-11-08).
- MediSense_Cardio_TrafficLight_Demo.ipynb (scripts/notebook_builders/build_safeguard_demo_notebook.py): one-click demo of the traffic-light safeguard (everything embedded; needs only pip install neurokit2). Tool: safeguard/.
- MediSense_Cardio_FixExperiment_Kaggle.ipynb (scripts/notebook_builders/build_fix_experiment_notebook.py): the same 60 own-phone photos prepared three ways (enlarge, straighten, both) and digitised (GPU, about 1-1.5 h); needs the Kaggle dataset `ownphotos`. Analysis: scripts/analysis/section_Q_fixexp.py. Rules: docs/plan/analysis_plan_changes.md (2026-11-10).
