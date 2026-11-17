"""Builds (or refreshes) D:/Capstone Project/SUBMISSION/: COPIES of the final deliverables in one numbered, readable structure, plus an index (00_START_HERE.md).
Nothing is moved or deleted outside SUBMISSION/ (many scripts have the original paths written inside them). Run again after any last edit:  python scripts/tools/make_submission_folder.py
Missing source files are reported, not hidden."""
import os
import shutil
import time

ROOT = "D:/Capstone Project/"
OUT = ROOT + "SUBMISSION/"
PLAN = [
    ("01_report", "The project report (final review copy)", [
        "docs/reports/CAPSTONE_REPORT_v4_review.pdf", "docs/reports/CAPSTONE_REPORT_v4_review.docx"]),
    ("02_paper", "The conference paper (IEEE format). Upload the zip to Overleaf as a new project and compile", [
        "docs/paper/medisense-cardio-paper-v2.zip", "docs/paper/main_v2.tex", "docs/paper/references.bib"]),
    ("03_poster", "A0 poster", [
        "docs/reports/MediSense_Cardio_A0_poster.pdf", "docs/reports/MediSense_Cardio_A0_poster.pptx"]),
    ("04_results", "All numbers and the test records (every number in the report, paper and poster comes from FINAL_NUMBERS.md)", [
        "results/FINAL_NUMBERS.md", "results/README.md", "results/paper_p/SECTION_P.md", "results/paper_q/SECTION_Q.md", "results/find2_op/SECTION_OP.md",
        "results/paper_r/SECTION_R.md", "results/paper_r/POOLED_QR.md", "results/paper_r/R_status.json", "results/paper_r/final_status.json", "results/qt_public/T1_metrics.csv", "results/qt_public/T2_pages.csv", "results/qt_public/T2_sim.csv", "results/paper_p/P_status.json", "results/paper_q/Q_status.json",
        "docs/reports/figures/fig_results_at_a_glance.png"]),
    ("05_plan_and_rules", "The rules written BEFORE each result, and the plan", [
        "docs/plan/analysis_plan_changes.md", "docs/plan/MASTER_PLAN.md", "docs/plan/CLAIMS_REGISTER.md", "docs/plan/PROGRESS-LOG.md"]),
    ("06_for_the_guide_and_viva", "Guide approval sheet, viva questions and answers, methods, code map, plagiarism self-check", [
        "docs/reports/GUIDE_APPROVAL_SHEET.md", "docs/reports/VIVA_QA.md", "docs/reports/METHODS_AND_FORMULAE.md", "docs/reports/CODE_MAP.md", "docs/reports/PLAGIARISM_SELF_CHECK.md"]),
    ("07_diary", "Project diary", ["docs/reports/Capstone_Project_Diary_filled_9weeks.pdf"]),
    ("08_reproducibility", "How to rerun and check everything", [
        "reproducibility/REPRODUCE.md", "reproducibility/ENVIRONMENT.md", "reproducibility/SECOND_PERSON_CHECK.md", "reproducibility/CHECK_REPORT.md", "reproducibility/run_all_checks.py",
        "reproducibility/requirements_demo_gpu.txt", "reproducibility/requirements_analysis_minimal.txt"]),
]
os.makedirs(OUT, exist_ok=True)
missing, copied = [], 0
lines = ["# MediSense-Cardio: submission folder", "",
         f"Built {time.strftime('%d %b %Y %H:%M')} by `scripts/tools/make_submission_folder.py` (copies; the originals stay where the scripts expect them).",
         "Research prototype for a university project. Not a medical device.", "",
         "## What is where", "", "| Folder | What is inside |", "|---|---|"]
for sub, what, files in PLAN:
    os.makedirs(OUT + sub, exist_ok=True)
    got = []
    for f in files:
        src = ROOT + f
        if os.path.exists(src):
            shutil.copy2(src, OUT + sub + "/" + os.path.basename(f))
            got.append(os.path.basename(f)); copied += 1
        else:
            missing.append(f)
    lines.append(f"| `{sub}/` | {what}: " + ", ".join(f"`{g}`" for g in got) + " |")
lines += ["", "## The code: `09_code/`", "",
          "A readable copy of our own code (demo, heart health module, analysis scripts, builders, safeguard, Colab notebooks). The map of what each script does is `06_for_the_guide_and_viva/CODE_MAP.md`. "
          "Run the code from the original folders, not from this copy. The third-party tools (Open-ECG-Digitizer, ECG-Image-Kit), the Python environments, the data and the results are not copied: see `08_reproducibility/`.",
          "", "## The demo (code stays in `demo/`, it needs the GPU environment and is too large to copy)", "",
          "```", "cd demo", "run_demo.bat                      (opens http://localhost:7860)", "```",
          "Tabs: the picture check, the heart health assessment, **Our results (at a glance)**, **Dataset gallery (instant results)** (dataset pictures with the true answer next to the tool's answer), how it works.",
          "Example pictures are in `demo/dataset_examples/` (12 dataset pictures with a key).", "",
          "## The main findings in five lines", "",
          "1. A GREEN heart rate from the traffic light is wrong 0.2% of the time (2 of 917 captures); on printed paper from another phone 2 of 19 were wrong, so it is not a guarantee.",
          "2. Straightening the photo reduced bad readings (screen photos 14 to 2 of 40, p = 0.0005; printed paper 31 to 15 of 66).",
          "3. Heart rate, PR interval and QRS axis are shown; QT and QRS duration are not (they failed their pre-set rules, twice).",
          "4. Heart-attack and ST/T patterns are shown on photos; left bundle branch block and atrial fibrillation passed our rules on fresh dataset pictures only (not on real phone photos; AF passed on its second test); other patterns are research-only hints.",
          "5. Mortality risk from the ECG was tried twice and failed its rules, so no risk is shown.", "",
          "Every pass rule was written before its result was seen and has not been approved by the guide.", "",
          "## Original project folders (do not move: scripts have these paths inside)", "",
          "`data/` (public datasets), `results/` (all runs), `scripts/` (analysis code), `demo/`, `colab/`, `docs/`, `reproducibility/`, `website/`, `safeguard/`. See the main `README.md`.", ""]

# ---- 09_code: a readable COPY of our own code (not the third-party tools, not the Python environments, not data or results)
CODE = OUT + "09_code/"
if os.path.isdir(CODE):
    shutil.rmtree(CODE)
os.makedirs(CODE)
_skip = shutil.ignore_patterns(".venv*", "venv*", "__pycache__", "*.pyc", "_server*", "*.before_*", "_kit", "*.log", "*.err")
_n = 0
for src, dst in (("demo", "demo"), ("safeguard", "safeguard"), ("colab", "colab"), ("scripts/analysis", "scripts/analysis"), ("scripts/preprocess", "scripts/preprocess"), ("scripts/quality_proxy", "scripts/quality_proxy"),
                 ("scripts/harness", "scripts/harness"), ("scripts/notebook_builders", "scripts/notebook_builders")):
    if os.path.isdir(ROOT + src):
        shutil.copytree(ROOT + src, CODE + dst, ignore=_skip)
os.makedirs(CODE + "scripts/tools", exist_ok=True)
for f in os.listdir(ROOT + "scripts/tools"):
    if os.path.isfile(ROOT + "scripts/tools/" + f):
        shutil.copy2(ROOT + "scripts/tools/" + f, CODE + "scripts/tools/" + f)
for f in ("results/paper_q/run_Q_resume.py", "results/paper_r/run_R.py", "results/paper_p/run_P_chain.bat"):
    if os.path.exists(ROOT + f):
        shutil.copy2(ROOT + f, CODE + "scripts/" + os.path.basename(f))
open(CODE + "README_CODE.md", "w", encoding="utf-8").write("""# Code copy

A readable COPY of our own code, for reading and for the examiners. Run the code from the ORIGINAL folders (`D:\\Capstone Project\\demo`, `scripts`, ...): the scripts have those paths and the data and results folders written inside them.

- `demo/`: the Gradio demo and the heart health module (`demo/health/`), with tests in `demo/tests/` (the GPU environment is not copied).
- `scripts/analysis/`: one script per question (tests refuse to run twice); `scripts/tools/`: builders for the report, paper, poster, figures and this folder; `scripts/preprocess/`, `scripts/quality_proxy/`, `scripts/harness/`, `scripts/notebook_builders/`.
- `safeguard/`: the traffic light. `colab/`: the Colab notebooks.
- Not copied: the third-party tools Open-ECG-Digitizer (commit 97a15087, unchanged) and ECG-Image-Kit (patched copy; the patches are in `08_reproducibility/`), the Python environments, the datasets and the results.
- The map of what each script does: `06_for_the_guide_and_viva/CODE_MAP.md` (section 9 lists the last two days).
""")
print("code copy:", sum(len(fs) for _, _, fs in os.walk(CODE)), "files")

open(OUT + "00_START_HERE.md", "w", encoding="utf-8").write("\n".join(lines))
print(f"copied {copied} files into {OUT}")
for m in missing:
    print("MISSING:", m)
