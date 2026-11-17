"""One command that runs every check of reproduction level 1 and writes reproducibility/CHECK_REPORT.md (PASS or FAIL per check).
Usage (from any folder):  python -I reproducibility/run_all_checks.py
Needs only the packages in requirements_analysis_minimal.txt. It does not re-run the digitiser. About 3 minutes."""
import datetime
import os
import platform
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
CHECKS = [
    ("36 headline numbers recomputed from the raw files", "scripts/analysis/final_numbers_recompute.py", "ALL MATCH: True"),
    ("Second-person number 3: GREEN wrong on the competition captures (2/917)", "scripts/analysis/second_person_green_count.py", "MATCH"),
    ("Traffic-light unit tests", "safeguard/tests/test_traffic_light.py", "ALL TESTS PASSED"),
    ("Demo wording tests", "demo/tests/test_explanation.py", "tests passed"),
]
rows = []
for name, script, needle in CHECKS:
    r = subprocess.run([sys.executable, "-I", os.path.join(ROOT, script)], cwd=ROOT, capture_output=True, text=True)
    out = (r.stdout or "") + (r.stderr or "")
    ok = r.returncode == 0 and needle in out and "DIFFERENT" not in out
    last = [ln for ln in out.strip().splitlines() if ln.strip()][-1] if out.strip() else "(no output)"
    rows.append((name, "PASS" if ok else "FAIL", last[:160].replace("|", "/")))
    print(("PASS" if ok else "FAIL"), "-", name, "|", last[:120], flush=True)
md = ["# Check report", "", f"Run: {datetime.datetime.now():%Y-%m-%d %H:%M}, Python {platform.python_version()} on {platform.system()} {platform.release()}.", "",
      "| Check | Result | Last line of its output |", "|---|---|---|"] + [f"| {a} | **{b}** | {c} |" for a, b, c in rows]
md += ["", "What this proves: the saved result files give the reported numbers when recounted by a second script, and the tests pass, in this environment. "
       "What it does not prove: it does not re-run the digitiser, and a second PERSON has not been involved unless you wrote your name in `SECOND_PERSON_CHECK.md`."]
open(os.path.join(ROOT, "reproducibility", "CHECK_REPORT.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
sys.exit(0 if all(r[1] == "PASS" for r in rows) else 1)
