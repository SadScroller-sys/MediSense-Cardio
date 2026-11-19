"""Set S pipeline (resumable; run with the system python):  python results/paper_s/run_S.py
Steps (each skipped if already done): keep-awake helper, draw 300 pages, make 300 simulated photos, digitise the photos. The one-time tests are separate scripts (section_MI_photocal2.py, section_S_risk_range.py).
Writes progress lines to results/paper_s/run.log. Stops (never writes a false 'done') if an output is missing."""
import os
import subprocess
import sys
import time

ROOT = "D:/Capstone Project/"
PY = ROOT + "demo/.venv-gpu/Scripts/python.exe"
PS = ROOT + "results/paper_s/"
LOG = open(PS + "run.log", "a", buffering=1)
N = 300


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
if count(PS + "pages", ".png") < N:
    say("drawing pages")
    run("python", ["scripts/analysis/make_pages_generic.py", "results/paper_s/selected_S.csv", "results/paper_s", "inpS"], PS + "make_pages.log")
n = count(PS + "pages", ".png")
say(f"pages drawn: {n} of {N}")
if n < N:
    say("not all pages drawn: stopping")
    sys.exit(1)
if count(PS + "P_sim/photos", ".jpg") < N:
    say("making simulated photos")
    run("python", ["scripts/analysis/make_sim_photos_S.py"], PS + "sim_make.log")
m = count(PS + "P_sim/photos", ".jpg")
say(f"simulated photos made: {m} of {N}")
if m < N:
    say("not all photos made: stopping")
    sys.exit(1)
if count(PS + "P_sim/dig_v2") < N:
    say("digitising simulated photos")
    run(PY, ["scripts/analysis/digitise_sim_photos_S.py"], PS + "sim_digitise.log")
m = count(PS + "P_sim/dig_v2")
say(f"simulated photos digitised: {m} of {N}")
if m < N:
    say("not all photos digitised: stopping")
    sys.exit(1)
open(PS + "S_pictures_done.flag", "w").write("done")
say("S PICTURES FINISHED")
