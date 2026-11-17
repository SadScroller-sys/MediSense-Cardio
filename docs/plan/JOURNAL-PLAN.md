# Journal paper plan — Physiological Measurement (IOP)

*Created 2026-09-25. Decision (user): an **extended version of the same work**, targeting **Physiological
Measurement**. The IEEE conference paper (due 2026-09-28) stays as is; this is a separate, longer manuscript.*

**Scope update (2026-09-25, user-confirmed):** the journal paper presents **everything we actually built, from
scratch, step by step, with real outputs** — a fully reproducible account, not a short results paper. It does
**not** claim the unbuilt parts (LLM explanation, safety-boundary filter, web app); those go in Future work.
The user recalled this requirement without being sure of its source ("I guess") — **confirm with the guide**.

## Step-by-step structure, each tied to a real artefact

| # | Step | Real output to show | Where it lives |
|---|---|---|---|
| 0 | Data and sampling | class / sex / age table of the 50 records | `scripts/analysis/analyze_v2_intervals.py` (reconstructs sample) |
| 1 | Feasibility spike: render → digitize → compare, one synthetic record | rendered page, digitizer output image, HR comparison | `results/gate2_spike/` |
| 2 | Real rendering tool on a real record | real ECG-Image-Kit page and its digitization | `results/real_ecg_image_kit_test/` |
| 3 | 6-record validation | per-record true vs measured HR table, ground truth vs digitized waveform overlay | `results/multi_sample_test/`, PROGRESS-LOG Day 3 |
| 4 | Degradation model (6 axes × 5 levels) | one record shown at every axis and level (**new figure**) | degrade functions in the sweep notebook |
| 5 | Harness + pilot (10 records, blur) | throughput (~20.3 s/image on a T4) | PROGRESS-LOG Day 7 |
| 6 | Full sweep v1 (1,550 tests): checkpointing, cleaning | cleaning table | `docs/SWEEP-RESULTS.md` |
| 7 | Reliability | failing-records figure | conference Fig. 3 |
| 8 | Heart-rate error and patient-facing outcomes | error-vs-level, outcome heatmaps | conference Figs 1–2 |
| 9 | Sweep v2 (PR/QRS/QT/QTc) | completion log, data dictionary | `results/v2_intervals/` |
| 10 | Interval analysis, noise floor, 100 Hz vs 500 Hz ground truth, Bland–Altman, stats | tables + new figures | `results/v2_intervals/journal/` |
| 11 | Reproducibility: v1 vs v2 digitizer drift | per-test agreement (needs v1 file from Drive) | pending |
| S | Supplement | notebooks, scripts, data dictionary, exact parameters, environment | repo |

Steps 1–3 and 5 are documented but the raw runs predate the harness; where an output was not saved (e.g. the
pilot's per-image table) the paper says so rather than reconstructing it.

## Hard constraints from the journal (checked 2026-09-25 against IOP's author guidance)

| Item | Requirement | Confidence |
|---|---|---|
| Abstract | Structured: **Objective / Approach / Main results / Significance**. ≤250 words per one IOP page, "not normally more than 300" per another | **Two sources disagree — design for 250, verify on the submission page** |
| References | **Harvard alphabetical (author–year)**, not IEEE numbered | Stated explicitly for this journal |
| Keywords | Required at submission | Stated |
| Prior publication | A conference paper may be submitted only if the journal version does **not** appear "in substantially the same form" | Stated — the main design constraint |
| Ethics statement | Required for human/animal research. PTB-XL is public, de-identified data — state that plainly | Stated |
| Template | LaTeX template optional (IOP `iopart`) | Stated |
| Length | No hard word limit for a full paper; long is fine if justified | Stated |

## What makes it "substantially different" (must be real content, not padding)

New analysis that can be done **with data already collected** (no new GPU runs):
1. **T1 signal-fidelity tier** — the sweep saved `snr_db` for every test but neither paper reports it. Add
   SNR vs degradation per axis.
2. **Formal statistics** — paired tests of each degraded level vs the same record's clean image
   (Wilcoxon signed-rank), effect sizes, Holm correction across the 6×5 comparisons. A journal reviewer will ask.
3. **Agreement analysis** — Bland–Altman of digitized vs ground-truth HR and QTc on clean images (bias and
   limits of agreement). This also quantifies the ~20 ms delineation floor properly.
4. **Per-diagnostic-class breakdown** (NORM / MI / STTC / CD / HYP) — does degradation hurt some classes more?
5. **v1 vs v2 reproducibility comparison** — the same records/images digitized by two versions of the tool five
   days apart. Direct per-test agreement of heart rate is a genuine, publishable digitizer-drift finding.
   *(Needs v1 `results_clean.csv` from Drive.)*
6. Fuller Methods (formal definitions of every metric, exact degradation parameters, delineation details),
   deeper Related Work, and a proper sample-size / uncertainty section.

New experiments that would strengthen it further but are **out of scope for now**: 500 records, a second
digitizer, real phone photos, the no-reference quality proxy (Contribution 2).

## Honest weaknesses a reviewer will hit (write to these, do not hide them)

- n = 50 records; only 9 (HR) / 19 (QTc) at-risk. → report CIs and frame as a controlled simulation study.
- One digitizer, one renderer, simulated (not photographed) damage. → limitations + future work.
- The digitizer version was not pinned; v1 and v2 disagree on which records fail. → report as a finding.
- QTc outcome result is weak/exploratory. → keep the cautious framing from the conference paper.

## Structure (IOP-style)

Abstract (structured) → Introduction → Related work (fold into Introduction if IOP prefers) → Methods
(data, pipeline, degradation model, metrics T1/T2/T3, statistics) → Results (reliability; T1 SNR; T2 HR and
intervals; T3 outcomes; agreement; per-class; reproducibility) → Discussion → Limitations → Conclusions →
Data availability, Ethics, Acknowledgements → References (Harvard).

## Work order

1. [ ] Extra analysis script `scripts/analysis/journal_extra_analysis.py` (items 1–4, from v2 data)
2. [ ] Download v1 `results_clean.csv` from Drive → item 5
3. [ ] Figures for the journal (new SNR, agreement, per-class panels)
4. [ ] Convert `references.bib` to Harvard formatting (iopart + natbib)
5. [ ] Draft the manuscript in `docs/journal/`
6. [ ] Compile in Overleaf with the IOP template; human read-through; guide sign-off
