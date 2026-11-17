# MediSense-Cardio review demo

Upload a photo of an ECG page -> the page is straightened -> Open-ECG-Digitizer reads it -> heart rate + traffic light (GREEN / AMBER / RED).
Research prototype for the capstone review. **Not a medical device.** Runs only on this computer; no internet needed; photos are processed in a temporary folder and deleted.

## How to start (3 steps)
1. Double-click `demo\run_demo.bat` (or run `python demo\app.py` in a terminal from `D:\Capstone Project`).
2. Wait until the window says `Running on local URL: http://127.0.0.1:7860`.
3. Open http://127.0.0.1:7860 in a browser. Click an example photo (or upload your own) and press **Check this photo**.
Close the black window to stop it.

## What the screen shows (added 2026-11-13)
- **Traffic light box:** GREEN / AMBER / RED. For RED the heart rate is not shown.
- **"Your ECG photo, in plain words":** the main output, made only from fixed sentences (`explain.py`, rules in `docs/plan/EXPLANATION_WORDING.md`), in four short parts: what we read, how sure we are, what we did not check, what to do next. GREEN shows the heart rate and its resting range, AMBER shows it with "we are not sure it is right", and RED or "no output" say nothing about the heart. It never diagnoses. The **PR interval** is shown as a number (no verdict) only for a GREEN light, a straightened photo and steady beat spacing (a precaution: atrial fibrillation has no P waves; PR is hidden when the beat spacing varies, about 15% of normal-rhythm photos), because it passed our pre-set tests on straightened photos (typical error 7 to 12 ms against 12SL; `results/FINAL_NUMBERS.md` section 10.6; `pr_interval.py` runs the exact tested method). The **frontal QRS axis** is shown as degrees (no verdict word) for GREEN straightened photos, because it passed our pre-set tests on fresh pages and phone photos (`FINAL_NUMBERS.md` section 10.8; `axis_deg.py` runs the exact tested method). QRS duration and QT were tried again on fresh data and are not validated, so they are named as not available.
- **"What an ECG shows (general information)" (closed by default):** a table of the nine ECG parameters (heart rate, rhythm, P wave, PR, QRS, QT, ST, T wave, axis) with what each tells doctors and what this tool got from the photo (only heart rate and a rough beat-spacing check; every other row says "Not measured by this tool"), and a general list of what an ECG can help doctors find, marked as not a result for the patient.
- **"Technical details for the presenter" (closed by default):** the traffic light reasons, timing, what the digitizer recognised in the photo (layout, leads read, beats), and, for the six test samples in `new_samples/`, the PTB-XL label of the source recording.
- Wording tests: `python -I demo/tests/test_explanation.py` (19 tests; forbidden phrases are blocked and a safe message is shown if a sentence is ever edited badly).
- Not built: an LLM explanation. The explanation is rule-based on purpose.

## Same photo, same numbers (added 2026-11-15)
The digitiser breaks ties in its line tracer with a tiny random number (`src/model/signal_extractor.py`, `torch.randn(...) * 1e-6`) and never seeds it, so before this change the same photo could give a PR 22 ms apart or an axis 11 degrees apart on a rerun (`results/reproducibility/repeat_variation_summary.md`). The digitiser code is **not** edited: `pipeline.py` starts it through a small bootstrap that seeds torch first (seed 42, fixed in advance). Result of the repeat test: see `results/reproducibility/repeat_variation_seeded_summary.md`. To get the unseeded behaviour of the study runs, set `DEMO_DIGITISER_SEED=none` before starting the demo. The study's own results were produced unseeded and are unchanged; the demo shows one fixed draw of the tie-break, not a better one.

## What it uses (all unchanged from the study)
- `scripts/preprocess/page_straighten.py` - page finder + perspective correction (the fix confirmed in Section Q2).
- `scripts/tools/Open-ECG-Digitizer` - commit 97a15087, weights `unet_weights_07072025.pt` and `lead_name_unet_weights_07072025.pt`, same settings file as every run.
- `safeguard/ecg_traffic_light.py` - 15 output features -> logistic score -> light (AMBER 0.2585, RED 0.7823).

## Speed and limits
- GPU (RTX 3050, environment `demo\.venv-gpu`, PyTorch 2.14.1 + CUDA 12.6): about 33-35 s per photo (first photo after start about 50 s). `run_demo.bat` uses this environment automatically.
- CPU (normal Python, PyTorch CPU build): about 50-60 s per photo. The page falls back to the CPU on its own if a GPU run fails (4 GB card: out of memory is possible on very large inputs).
- With the box "also run without straightening" ticked it takes twice as long. Odd pictures (noise) can take much longer.
- Most of the time is the digitiser itself (it loads the models at every call and does part of its work on the CPU), so the GPU saves about a third, not more.
- Works for standard 12-lead pages like the test pages. A random picture gives RED / "no usable heart rate" (checked with noise and a blank page).
- A GREEN light is not a guarantee. See `results/FINAL_NUMBERS.md` section 6 for what may and may not be claimed.

## Checked on 2026-11-11
- Example 1 (angled photo): with straightening 63 bpm GREEN (true 63.8); without 108 bpm RED. Same as the Kaggle run (62.6 / 107.9).
- Example 2: 55.0 bpm GREEN, identical to the Kaggle value (55.03).
- Noise picture and blank page: RED, no usable heart rate. A text file renamed .jpg is refused by the page.

## GPU check 2026-11-11 (same four example photos, GPU run vs the Kaggle run of the study)
| Photo | GPU here | Kaggle (study) |
|---|---|---|
| Example 2, straight | 55.03 bpm GREEN | 55.03 GREEN |
| Example 1, angled, with fix / without | 62.56 GREEN / 107.89 RED | 62.56 GREEN / 107.89 RED |
| Example 3, angled, with fix / without | 106.28 AMBER / no reading RED | 106.28 AMBER / no reading RED |
| Example 4, hard page, with fix / without | 65.90 RED / 65.93 RED | 65.90 RED / 65.93 RED |
The GPU environment reproduces the study's numbers to the second decimal (the CPU run gave the same values to the precision shown).
