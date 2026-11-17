"""Set R pipeline (resumable; run with the system python):  python results/paper_r/run_R.py
Steps (each skipped if already done): keep-awake helper, draw 120 pages, make 120 simulated photos, digitise pages, digitise photos, then the one-time tests and the verdict.
Writes progress lines to results/paper_r/run.log. Stops (never writes a false 'done') if an output is missing."""
import os
import subprocess
import sys
import time

ROOT = "D:/Capstone Project/"
PY = ROOT + "demo/.venv-gpu/Scripts/python.exe"
PR = ROOT + "results/paper_r/"
LOG = open(PR + "run.log", "a", buffering=1)


def say(m):
    LOG.write(time.strftime("%H:%M:%S ") + m + "\n")


def run(exe, args, out):
    with open(out, "a") as f:
        return subprocess.call([exe, "-I"] + args, cwd=ROOT, stdout=f, stderr=subprocess.STDOUT)


def count(d, pat=".npz"):
    return len([x for x in os.listdir(d) if x.endswith(pat)]) if os.path.isdir(d) else 0


say("run started")
subprocess.Popen(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ROOT + "results/paper_q/keep_awake.ps1"], creationflags=0x08000000)
r = subprocess.run([PY, "-I", "-c", "import torch;print(torch.cuda.is_available())"], capture_output=True, text=True)
if r.returncode != 0:
    say("TORCH FAILS (GPU library): stopping")
    sys.exit(1)
say("torch ok, cuda=" + r.stdout.strip())
if count(PR + "pages", ".png") < 120:
    say("drawing pages")
    run("python", ["scripts/analysis/make_pages_generic.py", "results/paper_r/selected_R.csv", "results/paper_r", "inpR"], PR + "make_pages.log")
n = count(PR + "pages", ".png")
say(f"pages drawn: {n} of 120")
if n < 120:
    say("not all pages drawn: stopping")
    sys.exit(1)
if count(PR + "P_sim/photos", ".jpg") < 120:
    say("making simulated photos")
    run("python", ["scripts/analysis/make_sim_photos_R.py"], PR + "sim_make.log")
m = count(PR + "P_sim/photos", ".jpg")
say(f"simulated photos made: {m} of 120")
if m < 120:
    say("not all photos made: stopping")
    sys.exit(1)
if count(PR + "r_digitized_12lead") < 120:
    say("digitising pages")
    run(PY, ["scripts/analysis/digitise_pages_generic.py", "results/paper_r/pages", "results/paper_r/r_digitized_12lead", "results/paper_r/digitise_log.csv"], PR + "digitise_pages.log")
n = count(PR + "r_digitized_12lead")
say(f"pages digitised: {n} of 120")
if n < 120:
    say("not all pages digitised: stopping")
    sys.exit(1)
if count(PR + "P_sim/dig_v2") < 120:
    say("digitising simulated photos")
    run(PY, ["scripts/analysis/digitise_sim_photos_R.py"], PR + "sim_digitise.log")
m = count(PR + "P_sim/dig_v2")
say(f"simulated photos digitised: {m} of 120")
if m < 120:
    say("not all photos digitised: stopping")
    sys.exit(1)
for part in ("pages", "sim"):
    say(f"test {part}: exit {run(PY, ['scripts/analysis/section_R_test.py', part], PR + f'test_{part}.log')}")
say(f"verdict: exit {run(PY, ['scripts/analysis/section_R_verdict.py'], PR + 'verdict.log')}")
say("R TESTS FINISHED")
