# MediSense-Cardio: START HERE

**What this project is:** a stress test of the open-source ECG digitiser Open-ECG-Digitizer, and a research demo built on it. We damage computer-drawn ECG pages and photos, measure whether heart rate and intervals go wrong, test whether the picture alone can warn (traffic light), and test which heart-rate, interval and ECG-pattern results can be shown safely. The final tests use dataset pictures (drawn pages and simulated phone photos of public hospital ECGs) plus our earlier screen and printed-paper photos. One digitiser, two phones. Research prototype, not a medical device.

**For the review (Fri 20 Nov 2026): open `SUBMISSION/00_START_HERE.md`.** It has the report, paper, poster, results, rules, guide and viva sheets in one numbered folder (copies; refresh with `python scripts/tools/make_submission_folder.py`).

**Read these three files first** (all in `docs/plan/`):
1. `MASTER_PLAN.md`: what we do, dates, and the rules for the analysis.
2. `CLAIMS_REGISTER.md`: what we are allowed to claim, and the evidence each claim needs.
3. `PROGRESS-LOG.md`: what has been done, newest at the bottom.

## Where things are
| Folder | What is inside |
|---|---|
| `docs/plan/` | the plan, the claims register, the progress log, older plans |
| `docs/literature/` | the research-paper reviews (sections A to G), the paper list, the comparison table |
| `docs/paper/` and `docs/journal/` | the two papers (LaTeX). Do not move: scripts write figures and tables here |
| `docs/reports/` | project diary (PDF), team report, sweep results note |
| `docs/old_drafts/` | early paper drafts, kept for history |
| `colab/` | the Colab notebooks (see `colab/README.md`) |
| `scripts/analysis/` | the analysis scripts (one per question, named for what it does) |
| `scripts/notebook_builders/` | programs that build the notebooks |
| `results/` | all results (see `results/README.md`) |
| `reproducibility/` | how to reproduce everything: versions, tool commits and patches, rerun guide, one-page check for a second person |
| `demo/` | the Gradio demo (`run_demo.bat`), the heart health module `demo/health/`, dataset example pictures, tests |
| `safeguard/` | the traffic-light safeguard (reliability check) code and model |
| `website/` | the project website |
| `SUBMISSION/` | copies of the final deliverables with an index (made by `scripts/tools/make_submission_folder.py`) |
| `results/paper_p/`, `paper_q/`, `paper_r/` | the fresh dataset-picture sets P, Q and R (selection, pages, simulated photos, one-time test results, verdicts); `find2_A2/`, `find2_B2/`: the retrained pattern networks; `qt_public/`: QT/QRS retry |
| `data/` | PTB-XL recordings and the PTB-XL+ features (large, public, not edited) |

## Rules
- Do not move or rename `data/`, `results/`, `scripts/`, `colab/`: many scripts have these paths written inside them.
- Every number in a paper, slide or diary comes from `results/FINAL_NUMBERS.md` (created at the freeze, about Nov 10).
- Anything not listed above (`scratchpad*`, `venv*`, `backend`, `notebooks`, the notebook copy in this folder) is not part of the current work and was not touched.
