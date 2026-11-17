"""Resume set Q after the restart (resumable; run with the system python):  python results/paper_q/run_Q_resume.py
Steps (each skipped if already done): keep-awake process, train A2, train B2, digitise the 160 drawn pages, digitise the 160 simulated photos, then the one-time tests and the verdict.
Writes progress lines to results/paper_q/resume.log. Never writes a 'done' flag unless the outputs exist."""
import os
import subprocess
import sys
import time

ROOT = "D:/Capstone Project/"
PY = ROOT + "demo/.venv-gpu/Scripts/python.exe"
PQ = ROOT + "results/paper_q/"
LOG = open(PQ + "resume.log", "a", buffering=1)


def say(m):
    LOG.write(time.strftime("%H:%M:%S ") + m + "\n")


def run(args, out):
    with open(out, "a") as f:
        return subprocess.call([PY, "-I"] + args, cwd=ROOT, stdout=f, stderr=subprocess.STDOUT)


def count(d, pat=".npz"):
    return len([x for x in os.listdir(d) if x.endswith(pat)]) if os.path.isdir(d) else 0


say("resume started")
subprocess.Popen(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", PQ + "keep_awake.ps1"], creationflags=0x08000000)
time.sleep(60)
for _ in range(30):                                   # wait until torch loads (GPU ready after the restart)
    r = subprocess.run([PY, "-I", "-c", "import torch;print(torch.cuda.is_available())"], capture_output=True, text=True)
    if r.returncode == 0:
        say("torch ok, cuda=" + r.stdout.strip())
        break
    time.sleep(30)
else:
    say("TORCH STILL FAILS: stopping")
    sys.exit(1)
for w, folder in (("A", "find2_A2"), ("B", "find2_B2")):
    if not os.path.exists(ROOT + f"results/{folder}/thresholds_q.json"):
        say(f"training {w}2")
        os.makedirs(ROOT + f"results/{folder}", exist_ok=True)
        rc = run(["scripts/analysis/section_Q_train.py", w], ROOT + f"results/{folder}/train.log")
        say(f"train {w}2 exit {rc}")
        if not os.path.exists(ROOT + f"results/{folder}/thresholds_q.json"):
            say("training failed: stopping")
            sys.exit(1)
if count(PQ + "q_digitized_12lead") < 160:
    say("digitising pages")
    run(["scripts/analysis/digitise_pages_generic.py", "results/paper_q/pages", "results/paper_q/q_digitized_12lead", "results/paper_q/digitise_log.csv"], PQ + "digitise_pages.log")
n = count(PQ + "q_digitized_12lead")
say(f"pages digitised: {n} of 160")
if n < 160:
    say("not all pages digitised: stopping")
    sys.exit(1)
if count(PQ + "P_sim/dig_v2") < 160:
    say("digitising simulated photos")
    run(["scripts/analysis/digitise_sim_photos_Q.py"], PQ + "sim_digitise.log")
m = count(PQ + "P_sim/dig_v2")
say(f"simulated photos digitised: {m} of 160")
if m < 160:
    say("not all photos digitised: stopping")
    sys.exit(1)
open(PQ + "pictures_done.flag", "w").write("done")
for part in ("pages", "sim"):
    say(f"test {part}: exit {run(['scripts/analysis/section_Q_test.py', part], PQ + f'test_{part}.log')}")
say(f"verdict: exit {run(['scripts/analysis/section_Q_verdict.py'], PQ + 'verdict.log')}")
say("Q TESTS FINISHED")
