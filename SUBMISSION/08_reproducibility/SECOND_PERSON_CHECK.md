# Second-person check: rerun three numbers (about 15 minutes)

Why: the project's 36-number recheck was written by the same author as the analysis. The claims register asks for a different person (a team member or the guide) to rerun three numbers before a claim can reach grade A. You do not need to understand the ECG part. You only run commands and compare numbers.

You need: this project folder on a Windows computer with Python 3.13, and the packages in `requirements_analysis_minimal.txt` (best in a new virtual environment: `python -m venv .venv-check`, then `.venv-check\Scripts\python.exe -m pip install -r reproducibility/requirements_analysis_minimal.txt`).

## Step 1. Run the check

Easiest: `.venv-check\Scripts\python.exe -I reproducibility/run_all_checks.py` runs this step, the third number and the tests, and writes `reproducibility/CHECK_REPORT.md` (send that file back too). Or by hand:

Open a terminal in the project folder and run:

```
python -I scripts/analysis/final_numbers_recompute.py
```

The last line must say `ALL MATCH: True`. If a line says `DIFFERENT`, write it down and stop.

## Step 2. Compare these three numbers by hand

Numbers 1 and 2 are lines in the output of Step 1 (it prints `recomputed | reported | MATCH`). Number 3 is not in that output: run this small script too, and write what its last line says:

```
python -I scripts/analysis/second_person_green_count.py
```

| # | What the number means | Line to find | Expected |
|---|---|---|---|
| 1 | Pages with a wrong heart rate at the worst low-resolution level, new 100 recordings | `new 100, resolution level 5: wrong >5 bpm` | 47/99 |
| 2 | Bad readings on 40 new phone photos: original vs straightened | `CONFIRMATION` lines (bad, original and straightened) | 14 and 2 (exact test p = 0.0005) |
| 3 | Wrong heart rates among GREEN traffic-light readings, competition real captures | last line of `second_person_green_count.py` | `GREEN wrong: 2/917 ... MATCH` |

## Step 3. Write down

- Your name, the date, the computer, the Python version (`python --version`).
- For each of the three numbers: what the script printed.
- Whether anything said `DIFFERENT`.

Send this page back filled in. The project will add one line to `docs/plan/PROGRESS-LOG.md` and to `results/FINAL_NUMBERS.md` section 7 ("checked by a second person: name, date").

## What this check does and does not prove
- It proves the saved result files give these numbers when recounted by a second script, on a second person's computer.
- It does not rerun the digitiser and it does not check the ECG science. It uses the same digitised signals and the same definition of "wrong" (more than 5 bpm from the true heart rate).
