# Heart health assessment module: inspection and plan (2026-11-15)

Requested by the guide: an additional module that turns a photo of a paper ECG into extracted parameters (with status and confidence), a supported-findings assessment, a risk view and an interactive dashboard, without breaking the existing app. This page is the "before implementing anything" step: what we already have, what is missing, what is honestly possible, and the rules we would fix first. **Status 2026-11-15: built and tested (results in `results/FINAL_NUMBERS.md` section 11); sections 1 to 7 below are the plan as written before building.**

## 1. The guide's list against what exists

| Guide asks | What we already have | Gap |
|---|---|---|
| Accept JPG, JPEG, PNG; preprocess; extract waveform; digitise | `demo/pipeline.py`: page finder + straightening, Open-ECG-Digitizer (unchanged), 12 leads at 1 kHz; the demo already takes JPG and PNG | none (reuse) |
| Image quality status; ask for a better photo | traffic light GREEN / AMBER / RED with reasons; "no usable heart rate" is always RED | wording for "please retake the photo" |
| Heart rate | validated (clean-page limits of agreement -3.2 to +3.1 bpm) | none |
| RR interval | the beats are already found (heart rate and beat-spacing variation `rr_cv`) | show mean RR derived from the same beats |
| PR interval | validated for straightened GREEN photos with steady beat spacing (typical error 7 to 12 ms) | none (already in the demo) |
| QRS duration | three attempts, **not validated** (bias +15 ms on photos) | cannot be provided; shown as "not measured" with the reason |
| QT / QTc | three attempts, **not validated** (compressed toward the middle) | same |
| Axis (extra) | validated for straightened photos | none |
| Measurement status and confidence | traffic light + the tested error of each method | a per-parameter status table (measured / not measured / hidden and why) |
| ML model for ECG abnormalities | none | **to build** (section 3) |
| Cardiac risk Low / Moderate / High | none | **not possible**, see section 2 |
| Interactive dashboard (risk indicator, zoomable waveform, parameter bars with reference ranges, findings chart) | Gradio page with a static plot and fixed wording | Plotly charts (needs `pip install plotly`; it is not installed) |
| Safety wording | `demo/explain.py` with a forbidden-phrase checker and 19 tests | extend the list and tests to the new texts |

## 2. What is honestly possible (the guide's own safety rules point the same way)

- **Cardiac risk categories (Low / Moderate / High) cannot be built.** A risk model needs outcome data (who later had an event). PTB-XL has ECG labels from cardiologists but no follow-up. The guide says: if a validated risk model is unavailable, show "risk assessment not available". We do that, in a visible box, with the reason.
- **ECG findings can be built, with a clear name: "ECG pattern", not "risk".** PTB-XL (21,799 recordings, public) carries cardiologist labels in five groups: normal, myocardial infarction pattern, ST/T change, conduction disturbance, hypertrophy; plus atrial fibrillation / flutter as a rhythm label. A colour-coded indicator can say "ECG pattern: no supported abnormality found / needs review / abnormal pattern found", labelled as an ECG finding and never as cardiac risk.
- **Probabilities are shown only if the model is calibrated and has passed our rule** (below). Otherwise the finding says "not available for this photo".
- **A normal result never says the heart is healthy.** The fixed sentence: "This research tool found no supported abnormal pattern. A normal-looking ECG does not exclude heart disease."

## 3. Datasets and models required

| Need | Choice | Download? |
|---|---|---|
| Labelled ECGs for training | PTB-XL v1.0.3, already in `data/ptbxl/`, with `scp_statements.csv` and the standard 10 folds | none |
| Model | a small 1-D convolutional network trained by us on the PTB-XL training folds (1 to 8), validated on fold 9, benchmark-tested on fold 10; GPU (RTX 3050, 4 GB) is enough, minutes per run | none (a pre-trained model would need a download and a yes) |
| Same input as the app gives | train on signals cut to the **page layout** (2.5 s per lead plus the 10 s lead II strip), the same cut we used in Sections T and U, so the model sees what the digitiser outputs | none |
| Calibration | Platt or isotonic fit on fold 9 only | none |
| Validation on the digitised domain | the 200 recordings of ours that have PTB-XL labels and digitised pages (first 50, new 100, fresh F, sealed G, phone-photo pages), **removed from training** | none |

**Honest limit found while inspecting:** among those 200 recordings the positives are few (MI 35, ST/T 47, conduction 41, hypertrophy 33, atrial fibrillation 14). Intervals on digitised pages will be wide and AF almost untestable. More digitised labelled pages would fix it (about 45 s per page on the GPU: 150 extra pages = about 2 hours in the background, chosen to add positives).

## 4. Rules to fix before any result (my proposal; the guide has not approved them)

1. Training uses folds 1 to 8 minus our 200 recordings; fold 9 for early stopping and calibration; fold 10 once for the benchmark number. The 200 digitised recordings are touched once, after the model is frozen.
2. A finding is **supported** in the app only if, on the digitised pages, AUROC is at least 0.80 with a bootstrap lower bound above 0.70, and calibration error (ECE) is at most 0.10 on fold 10. A finding that fails is shown as "not available". Fewer than 20 positives = "not testable", also not shown.
3. Findings are shown only when the traffic light is GREEN or AMBER and the page was straightened; RED shows "please send a clearer photo".
4. No percentage is shown unless the finding passed rule 2; model confidence and abnormality are drawn as two separate things.
5. The result is reported as measured, including a failure; labels PRE-SPECIFIED / EXPLORATORY as in `results/FINAL_NUMBERS.md`.

## 5. Design (new files only; nothing existing is rewritten)

- New package `demo/health/`: `data.py` (labels and layout cut), `model.py` (network, training, calibration), `evaluate.py` (the rules above), `assess.py` (parameters + findings + wording), `dashboard.py` (Plotly figures). One hook (a new tab "Heart health assessment") in `demo/app.py`. Existing tabs, tests and numbers stay.
- Reused as they are: `pipeline.run`, `page_straighten`, `pr_interval`, `axis_deg`, the traffic light, `explain.check_wording`.
- Dashboard: (A) risk box: "Cardiac risk assessment: not available" plus the colour-coded ECG-pattern indicator; (B) Plotly waveform, seconds on x and mV on y, zoom, lead selector; (C) parameter bars with reference ranges (heart rate 60 to 100 bpm, PR 120 to 200 ms, RR from the heart rate; QRS and QT rows say "not measured"); (D) findings chart with only supported findings, abnormal ones marked.
- Results panel in the guide's order: image quality, waveform, parameters, abnormalities, assessment, risk, confidence and limitations, next steps.

## 6. Time

Review is Fri 20 Nov; the report, paper and rehearsal are also open. Proposed timebox with a stop rule: Sat 15 plan + data; Sun 16 model, validation (extra pages in the background); Mon 17 evening dashboard, tests, stop; Tue to Thu rehearsal. If a finding does not pass its rule it ships as "not available", which is a result, not a failure of the module.

## 7. Decisions needed

1. Go-ahead with this scope (findings as "ECG pattern", risk shown as not available).
2. Digitise about 150 more labelled pages in the background (about 2 hours of GPU) to make the digitised-page validation meaningful, yes or no.
3. Install `plotly` in `demo/.venv-gpu` (small, needed for zoom).
4. Ask the guide whether the thresholds in section 4 are acceptable (same sheet as the other thresholds).
