# Reproducibility package (MediSense-Cardio), written 2026-11-14

Research prototype, not a medical device. Every number in the report comes from `results/FINAL_NUMBERS.md`.
This page says what you need, in which order to run it, what is exact and what is not, and how long each part takes.

## 1. What is in this folder

| File | What it is |
|---|---|
| `REPRODUCE.md` | This guide |
| `SECOND_PERSON_CHECK.md` | One page for a second person who reruns three headline numbers (claims register, mark 4) |
| `ENVIRONMENT.md` | Exact versions: Python, GPU, packages, tool commits, weight checksums |
| `requirements_analysis_minimal.txt` | **Use this one** for levels 1 and 2: the 9 packages the analysis scripts import, pinned (tested in a clean environment, see section 2) |
| `run_all_checks.py` | One command that runs every level-1 check and writes `CHECK_REPORT.md` (PASS or FAIL per check) |
| `requirements_analysis_system_python.txt` | `pip freeze` of the whole system Python that ran the analysis (148 lines; a record, not for installing) |
| `requirements_demo_gpu.txt` | `pip freeze` of `demo\.venv-gpu`, the environment that runs the digitiser and the demo (84 lines) |
| `patches/open_ecg_digitizer_local_changes.patch` | Our only change to Open-ECG-Digitizer (see section 4) |
| `patches/ecg_image_kit_local_changes.patch` | Our change to ECG-Image-Kit |
| `../results/reproducibility/recompute_run_2026-11-14.log` | Output of the 36-number recheck on 2026-11-14: all 36 MATCH |
| `../results/reproducibility/repeat_variation_*.csv/.md` | How much the digitiser changes when the same photo is run again (section 6) |

## 2. Three levels of "reproduce"

| Level | What you rerun | Needs | Time | Result |
|---|---|---|---|---|
| 1. Check the numbers | The 36 headline numbers, from the saved result files | Python + the packages in `requirements_analysis_system_python.txt` | about 2 minutes | Prints `MATCH` or `DIFFERENT` for each number |
| 2. Redo the analyses | Every `scripts/analysis/section_*.py` on the saved digitised signals | Same as level 1 | minutes per section | Same tables and `SECTION_*.md` files |
| 3. Redo the digitising | Draw, damage and digitise the pages again | A GPU, the digitiser, the notebooks in `colab/` (Colab or Kaggle) | the first 50 recordings took about 10.5 hours; the new 100 about 7 hours | Same numbers up to the small variation in section 6 |

**Tested in a clean environment (2026-11-14):** a new empty virtual environment, only `requirements_analysis_minimal.txt` installed, then `run_all_checks.py` (all 4 checks PASS) and the interval and risk-coverage scripts. The two result tables they write came out byte-identical to the ones made in the main Python (SHA-256 equal). So the minimal list is enough and the results do not depend on my machine's extra packages.

Level 1 is what a second person should do. Level 3 is not bit-exact: the digitiser has a random tie-break in its line tracer (section 6).

## 3. Level 1 and 2: step by step

1. Open a terminal in the project folder (`D:\Capstone Project`).
2. Install the packages in a new empty virtual environment: `python -m venv .venv-check`, then `.venv-check\Scripts\python.exe -m pip install -r reproducibility/requirements_analysis_minimal.txt` (Python 3.13 on Windows; exact versions in `ENVIRONMENT.md`)
3. Run all the checks with one command (about 3 minutes): `.venv-check\Scripts\python.exe -I reproducibility/run_all_checks.py`; it writes `reproducibility/CHECK_REPORT.md`. Or run the main check alone:
   ```
   python -I scripts/analysis/final_numbers_recompute.py
   ```
   Expected last line: `ALL MATCH: True`. This script is written fresh and does not import the section scripts; it reads only the raw result files.
4. Run the test suites (both must say all tests passed):
   ```
   python -I safeguard/tests/test_traffic_light.py
   python -I demo/tests/test_explanation.py
   ```
5. To redo one analysis, run its script, for example `python -I scripts/analysis/section_C.py`; it rewrites `results/analysis/SECTION_C.md` and the CSV files. The list of scripts and what each answers is in `docs/reports/CODE_MAP.md` (section 2). Sections O, Q and Q2 take a folder argument (shown at the top of each file).
6. The held-out tests (`section_T`, `section_U`, `section_V`, `section_W`, `section_X`, `section_Y`) have `--dev`, `--test` and `--confirm`. The frozen choices are saved next to them (`sectionT_frozen.json`, `sectionU_frozen.json`, `sectionW_frozen.json`, ...). **Do not re-tune a method and re-run `--test` or `--confirm`: each was run once on purpose.** Re-running them only checks that the saved result is the same.

## 4. Data and tools (what must be on the disk)

| Item | Where | Check |
|---|---|---|
| PTB-XL v1.0.3 (21,799 recordings) | `data/ptbxl/` (public, PhysioNet, CC BY 4.0) | `data/ptbxl/SHA256SUMS.txt` lists the checksum of every file (87,203 lines) |
| PTB-XL+ features (12SL, Glasgow, ...) | `data/ptbxl_plus/` (public, PhysioNet); downloader `scripts/tools/download_ptbxl_plus.py` | complete as of 2026-11-04 |
| ECG-Image-Kit | `scripts/tools/ecg-image-kit/`, upstream https://github.com/alphanumericslab/ecg-image-kit, commit `27b90f56896c9fc78b05a83ca14844ea2637aa0b` | one file patched: `patches/ecg_image_kit_local_changes.patch` (plus a new `requirements-core.txt`) |
| Open-ECG-Digitizer | `scripts/tools/Open-ECG-Digitizer/`, upstream https://github.com/Ahus-AIM/Open-ECG-Digitizer, commit `97a15087d4abcda843da8c58ee74b1d8f47e6f9a`, **unchanged except one local patch** | `patches/open_ecg_digitizer_local_changes.patch`: the `ray` import is wrapped in a try, because `ray` has no build for this Python. It is used only for training (`EarlyStopper`), not for reading images. It does not change any number. |
| Digitiser weights | `scripts/tools/Open-ECG-Digitizer/weights/` | SHA-256 in `ENVIRONMENT.md` |
| Settings for every run | One settings text, written at run time by `_config_text()` in `demo/pipeline.py` and by `write_digitizer_config()` in the Kaggle notebooks (identical text: the two published weight files, George Moody 2024 lead layouts, `resample_size` 3000, `apply_dewarping: false`, `possibly_flipped: false`) | `demo/pipeline.py` lines 39 to 100 |

The saved results (`results/`) are what levels 1 and 2 read. They came from Colab and Kaggle runs and are in the project folder; the Drive copies are the originals (`MyDrive/MediSense-Cardio-Study/`).

## 5. Fixed seeds and rules

- Seeds: 42 (first 50 and the new 100), 45 (confirmation pages Q), 46 (fresh pages F), 47 (sealed pages G), 49 (simulated photos), 51 (printed-paper pages H), 52 (risk-coverage ties and bootstrap), 53 (interval bootstrap). Each is written in the script that uses it.
- Every analysis rule was written in `docs/plan/analysis_plan_changes.md` (or `MASTER_PLAN.md`) before the run. The master plan, the first plan and the claims register are fingerprinted (SHA-256 in `docs/plan/PROGRESS-LOG.md`) and are not edited.
- Labels in `FINAL_NUMBERS.md`: PRE-SPECIFIED, EXPLORATORY, POST HOC.

## 6. What is NOT exact (said plainly)

1. **The digitiser is not fully deterministic.** Its line tracer breaks ties at random, so running the same photo twice can give slightly different numbers. We measured how much on 10 demo photos, 3 runs each, nothing changed between runs: see `results/reproducibility/repeat_variation_summary.md`.
2. **Output availability changed between the first two sweeps** (163 vs 30 unreadable images on the same pages). Where both gave a heart rate, 98.1% were identical. Cause unknown (different machine or unpinned code). This is why the second sweep is called a repeat, not a replication. The bridge run (12 recordings x 13 versions, another day) changed the "bad" label on 0 of 156 images.
3. **Colab and Kaggle have no fixed package versions.** The notebooks print the digitiser commit, but the Colab package versions were not saved. Level 3 on a new Colab day can differ in the last decimals.
4. **Same author.** The 36-number recheck is a second script by the same person. A second person has not rerun anything yet (see `SECOND_PERSON_CHECK.md`).
5. **No git history.** Nothing has been committed yet. Until it is, the zip made from this folder is the only snapshot.

## 7. What a reviewer can run in the room (laptop with the GPU environment)

```
demo\run_demo.bat
```
then open http://127.0.0.1:7860. About 35 seconds per photo. Six sample photos in `demo/new_samples/` and four in `demo/examples/`.

## 8. Not part of the package
`venv/`, `venv-ecg-image-kit/` (broken copies from another machine), `demo/.venv-gpu/` (5 GB; rebuild it with `python -m venv demo\.venv-gpu`, then `demo\.venv-gpu\Scripts\python.exe -m pip install -r reproducibility/requirements_demo_gpu.txt --extra-index-url https://download.pytorch.org/whl/cu126`; the `+cu126` PyTorch builds come from that address, not from PyPI), `data/` (public; download again from PhysioNet), `scratchpad*`.
