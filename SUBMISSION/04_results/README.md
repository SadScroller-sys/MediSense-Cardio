# results/: map

**Current study**
- `v2_intervals/`: the first 50 recordings (second sweep): results_v2.csv is the main table (1,550 rows).
- `extension/`: the 100 new recordings: selected_100.csv (who), selection_summary.md, reference_check_150.csv (heart-rate reference check, all 150). The Colab run writes to Drive; its results will be copied here.
- `detector_heldout_results.md`: held-out test of the photo-quality detector (first 50).
- `flagged_recordings_effect.md`, `hr_reference_check.md`, `reference_vs_ptbxl_plus.md`, `interval_method_comparison.md` (+ .csv, .log): checks of the data and of our reference measurements.
- `qtc_fridericia_rerun.md`: QTc false reassurance with Bazett vs Fridericia.
- `FINAL_NUMBERS.md`: the frozen numbers (sections 10.1 to 10.30). Papers, slides, diary, poster and the demo use only this file.
- `paper_n/`, `paper_p/`, `paper_q/`, `paper_r/`: the positive-rich dataset-picture sets N, P, Q and R (R = replication of LBBB and AF; `paper_r/final_status.json` is what the app reads) (selection, drawn pages, simulated photos, digitised outputs, one-time test results, `SECTION_*.md`, `*_status.json`).
- `find2_A/`, `find2_B/`: pattern networks A (PTB-XL) and B (CODE-15%); `find2_A2/`, `find2_B2/`: the retrained versions used for set Q; `find2_op/`: the strict operating point (specificity 0.97).
- `qt_public/`: QT and QRS retry on doctor-marked public data (LUDB, QT Database): model, `T1_metrics.csv`, `T2_*.csv`.
- `risk_pilot/`, `risk_pilot2/`: the two mortality-risk pilots (both failed their rules).
- `health/`, `fresh*/`, `intervals_ml/`, `ownphotos*/`, `extension/`: the earlier runs behind the heart-health module and the photo tests.

**Older pilot material (not part of the final numbers):** `gate2_spike/`, `live_proof/`, `multi_sample_test/` (6 clean digitised outputs), `real_ecg_image_kit_test/`, `side_by_side_test.png`, `quality_proxy_*`.
