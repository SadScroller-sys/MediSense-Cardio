"""Parallel, resumable downloader for the CODE-15% pilot (Zenodo 10.5281/zenodo.4916206, CC-BY 4.0). Approved by the user on 2026-11-15: exams.csv + exams_part0..3.zip (about 11 GB).
Uses many HTTP range requests at once (one connection is throttled to about 70 KB/s) and writes data/code15/PROGRESS.txt every 15 seconds (percent, speed, time left).
Resumes after any interruption (finished chunks are recorded in <file>.chunks.json). Usage: python -I scripts/tools/download_code15.py [parts] [connections]   e.g.  4 32"""
import json
import os
import sys
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
OUT = os.path.join(ROOT, "data", "code15")
BASE = "https://zenodo.org/records/4916206/files/"
N_PARTS = int(sys.argv[1]) if len(sys.argv) > 1 else 4
CONN = int(sys.argv[2]) if len(sys.argv) > 2 else 32
CHUNK = 4 * 1024 * 1024
os.makedirs(OUT, exist_ok=True)
FILES = ["exams.csv"] + [f"exams_part{i}.zip" for i in range(N_PARTS)]
lock = threading.Lock()
done_bytes = {"n": 0}
t_start = time.time()


def size_of(name):
    req = urllib.request.Request(BASE + name + "?download=1", method="HEAD")
    with urllib.request.urlopen(req, timeout=60) as r:
        return int(r.headers["Content-Length"])


sizes = {n: size_of(n) for n in FILES}
total = sum(sizes.values())
state = {}
for n in FILES:
    f = os.path.join(OUT, n + ".chunks.json")
    state[n] = set(json.load(open(f))) if os.path.exists(f) else set()
    if not os.path.exists(os.path.join(OUT, n + ".part")) and not os.path.exists(os.path.join(OUT, n)):
        with open(os.path.join(OUT, n + ".part"), "wb") as fh:
            fh.truncate(sizes[n])
already = sum(min(CHUNK, sizes[n] - c * CHUNK) for n in FILES for c in state[n])
done_bytes["n"] = already
jobs = [(n, c) for n in FILES for c in range((sizes[n] + CHUNK - 1) // CHUNK) if c not in state[n] and not os.path.exists(os.path.join(OUT, n))]


def fetch(job):
    n, c = job
    a, b = c * CHUNK, min(sizes[n], (c + 1) * CHUNK) - 1
    attempt = -1
    while True:                      # no giving up: a network drop only makes it wait (back-off up to 30 s) and retry, so it survives disconnects
        try:
            req = urllib.request.Request(BASE + n + "?download=1", headers={"Range": f"bytes={a}-{b}"})
            with urllib.request.urlopen(req, timeout=90) as r:
                data = r.read()
            if len(data) != b - a + 1:
                raise IOError("short read")
            with lock:
                with open(os.path.join(OUT, n + ".part"), "r+b") as fh:
                    fh.seek(a)
                    fh.write(data)
                state[n].add(c)
                json.dump(sorted(state[n]), open(os.path.join(OUT, n + ".chunks.json"), "w"))
                done_bytes["n"] += len(data)
            return
        except Exception:
            attempt += 1
            time.sleep(min(30, 2 + attempt * 2))


def reporter():
    last, last_t = done_bytes["n"], time.time()
    while True:
        time.sleep(15)
        now, cur = time.time(), done_bytes["n"]
        rate = (cur - last) / max(now - last_t, 1e-9)
        last, last_t = cur, now
        left = (total - cur) / rate if rate > 1 else float("inf")
        txt = (f"CODE-15% pilot download   updated {time.strftime('%H:%M:%S')}\n"
               f"done {cur / 1e9:.2f} GB of {total / 1e9:.2f} GB  =  {100 * cur / total:.1f} %\n"
               f"speed {rate / 1024:.0f} KB/s ({CONN} connections)\n"
               f"time left about {left / 3600:.1f} hours" if left != float("inf") else
               f"CODE-15% pilot download   updated {time.strftime('%H:%M:%S')}\ndone {cur / 1e9:.2f} GB of {total / 1e9:.2f} GB  =  {100 * cur / total:.1f} %\nspeed {rate / 1024:.0f} KB/s\ntime left: not known yet\n")
        open(os.path.join(OUT, "PROGRESS.txt"), "w").write(txt + "\n")
        if cur >= total:
            return


threading.Thread(target=reporter, daemon=True).start()
with ThreadPoolExecutor(CONN) as ex:
    list(ex.map(fetch, jobs))
for n in FILES:
    p = os.path.join(OUT, n + ".part")
    if os.path.exists(p) and len(state[n]) * 1 >= (sizes[n] + CHUNK - 1) // CHUNK:
        os.replace(p, os.path.join(OUT, n))
open(os.path.join(OUT, "PROGRESS.txt"), "w").write(f"FINISHED {time.strftime('%H:%M:%S')}: {total / 1e9:.2f} GB downloaded in {(time.time() - t_start) / 60:.0f} minutes\n")
open(os.path.join(OUT, "download_done.flag"), "w").write("finished\n")
