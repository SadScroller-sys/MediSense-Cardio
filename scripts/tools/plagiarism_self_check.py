"""Overlap self-check (NOT an official plagiarism report). Finds runs of N or more identical consecutive words between our texts (report, paper) and the source papers we used
(PDFs in C:/ECG research/ECG_Papers and the README / licence files of the open-source tools). Reference lists are excluded from our texts. Output: docs/reports/PLAGIARISM_SELF_CHECK.md and a CSV of every flagged run.
The official check (Turnitin or the college's tool) must still be run by the guide or the library; this script only helps to find and fix close passages first.
Usage: python -I scripts/tools/plagiarism_self_check.py [N=8]"""
import csv
import glob
import os
import re
import sys
import time
from collections import defaultdict

import docx
import pymupdf as fitz

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
N = int(sys.argv[1]) if len(sys.argv) > 1 else 8
SRC_DIR = "C:/ECG research/ECG_Papers"
BS = chr(92)


def words(text):
    return re.findall(r"[a-z0-9]+(?:[-'][a-z0-9]+)*", text.lower())


# ---------------------------------------------------------------- our texts
def report_text():
    d = docx.Document(os.path.join(ROOT, "docs", "reports", "CAPSTONE_REPORT_DRAFT_v4.docx"))
    paras = [p.text for p in d.paragraphs]
    a = next(i for i, t in enumerate(paras) if t.startswith("CHAPTER 1"))
    # the abstract sits before the table of contents; the references are excluded
    ab = next(i for i, t in enumerate(paras) if t.strip() == "ABSTRACT")
    b = next(i for i, t in enumerate(paras) if t.strip() == "REFERENCES")
    keep = paras[ab + 1:ab + 2] + paras[a:b]
    for t in d.tables:
        for r in t.rows:
            keep.append(" ".join(c.text for c in r.cells))
    txt = "\n".join(keep)
    return re.sub(r"\[\d+(?:[,-]\s*\d+)*\]", " ", txt)


def paper_text():
    s = open(os.path.join(ROOT, "docs", "paper", "main_v2.tex"), encoding="utf-8").read()
    s = s[s.index(BS + "begin{abstract}"):s.index(BS + "bibliographystyle")]
    s = re.sub(r"(?m)(?<!" + re.escape(BS) + r")%.*$", "", s)
    s = re.sub(r"\$[^$]*\$", " ", s)
    s = re.sub(re.escape(BS) + r"(?:cite|ref|label|footnote|url)\{[^}]*\}", " ", s)
    s = re.sub(re.escape(BS) + r"[a-zA-Z]+\*?(\[[^\]]*\])?", " ", s)
    s = re.sub(r"[{}~&]|``|''|--", " ", s)
    return s


# ---------------------------------------------------------------- sources
def source_texts():
    out = {}
    pdfs = glob.glob(SRC_DIR + "/**/*.pdf", recursive=True)
    t0 = time.time()
    for k, f in enumerate(pdfs):
        try:
            doc = fitz.open(f)
            txt = " ".join(p.get_text() for p in doc)
            doc.close()
            if len(txt) > 2000:
                out[os.path.relpath(f, SRC_DIR).replace(os.sep, "/")] = txt
        except Exception:
            pass
        if k % 20 == 0:
            print("read", k, "of", len(pdfs), "PDFs", round(time.time() - t0), "s", flush=True)
    for f in ("scripts/tools/Open-ECG-Digitizer/README.md", "scripts/tools/Open-ECG-Digitizer/CHANGELOG.md", "scripts/tools/Open-ECG-Digitizer/LICENSE"):
        p = os.path.join(ROOT, f)
        if os.path.exists(p):
            out["tool: " + f] = open(p, encoding="utf-8", errors="ignore").read()
    for f in glob.glob(os.path.join(ROOT, "scripts/tools/ecg-image-kit/**/*.md"), recursive=True):
        out["tool: " + os.path.relpath(f, ROOT).replace(os.sep, "/")] = open(f, encoding="utf-8", errors="ignore").read()
    return out


print("reading sources ...", flush=True)
SRC = source_texts()
print(len(SRC), "source texts", flush=True)
index = defaultdict(set)                      # hash of N consecutive words -> source ids
names = list(SRC)
for sid, name in enumerate(names):
    w = words(SRC[name])
    for i in range(len(w) - N + 1):
        index[hash(" ".join(w[i:i + N]))].add(sid)
print("index of", len(index), "word runs", flush=True)

rows = []
summary = []
for label, txt in (("Report (v4, body, tables and abstract; references excluded)", report_text()), ("IEEE paper (main_v2.tex, body)", paper_text())):
    w = words(txt)
    covered = [False] * len(w)
    who = [None] * len(w)
    for i in range(len(w) - N + 1):
        h = hash(" ".join(w[i:i + N]))
        if h in index:
            for j in range(i, i + N):
                covered[j] = True
                who[j] = who[j] | index[h] if who[j] else set(index[h])
    runs, i = [], 0
    while i < len(w):
        if covered[i]:
            j = i
            s = set(who[i])
            while j + 1 < len(w) and covered[j + 1]:
                j += 1
                s |= who[j]
            runs.append((i, j, s))
            i = j + 1
        else:
            i += 1
    cov = sum(covered)
    summary.append((label, len(w), cov, 100.0 * cov / max(len(w), 1), len(runs)))
    for i, j, s in runs:
        rows.append(dict(text=label.split(" (")[0], words=j - i + 1, start=i, passage=" ".join(w[i:j + 1]), sources="; ".join(sorted(names[x] for x in s))[:300]))
    print(label, ":", len(w), "words,", cov, "words in runs of", N, "or more =", round(100.0 * cov / max(len(w), 1), 2), "%,", len(runs), "runs", flush=True)

rows.sort(key=lambda r: (r["text"], -r["words"]))
csvp = os.path.join(ROOT, "docs", "reports", f"plagiarism_self_check_runs_N{N}.csv")
with open(csvp, "w", newline="", encoding="utf-8") as f:
    wr = csv.DictWriter(f, fieldnames=["text", "words", "start", "passage", "sources"])
    wr.writeheader()
    wr.writerows(rows)
print("wrote", csvp, len(rows), "runs", flush=True)
import json  # noqa: E402

json.dump(dict(N=N, sources=len(SRC), summary=summary), open(os.path.join(ROOT, "docs", "reports", f"plagiarism_self_check_summary_N{N}.json"), "w"), indent=1)
