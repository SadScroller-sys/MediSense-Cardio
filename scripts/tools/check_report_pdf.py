"""Check the report PDF: the table of contents, the list of tables and figures (page numbers match where the captions really are), leftover placeholders.
Usage: python -I scripts/tools/check_report_pdf.py docs/reports/CAPSTONE_REPORT_v4_review.pdf"""
import re
import sys

import pymupdf as fitz

d = fitz.open(sys.argv[1])
n = len(d)
txt = [p.get_text() for p in d]
print("pages:", n)
# the PDF page number printed in the footer is the page index + 1 only if numbering starts at 1: find the printed number of the Chapter 1 page
ch1 = next(i for i, t in enumerate(txt) if "CHAPTER 1: INTRODUCTION" in t and "......" not in t)
print("Chapter 1 heading is on PDF page", ch1 + 1)
toc_i = next(i for i, t in enumerate(txt) if "TABLE OF CONTENTS" in t)
print("table of contents on PDF page", toc_i + 1, "| first lines:", " / ".join(txt[toc_i].split("\n")[1:8]))
# list of tables: (caption, printed page)
lot_i = next(i for i, t in enumerate(txt) if "LIST OF TABLES" in t)
entries = []
for i in range(lot_i, ch1):
    for line in txt[i].split("\n"):
        m = re.match(r"^((Table|Figure) [0-9A-Z]+\.[0-9]+):.*?\.{2,}\s*(\d+)\s*$", line)
        if m:
            entries.append((m.group(1), int(m.group(3))))
print("list entries with a page number:", len(entries))
bad = 0
for key, page in entries:
    real = [i + 1 for i in range(ch1, n) if re.search(r"(?m)^" + re.escape(key) + ":", txt[i])]
    # printed page number = footer number; find how PDF index maps to the printed number by reading the footer of that page
    if not real:
        print("caption not found in body:", key)
        bad += 1
        continue
    foot = re.match(r"\s*(\d+)\s", txt[real[0] - 1])
    printed = int(foot.group(1)) if foot else None
    if printed != page:
        print("MISMATCH", key, "list says", page, "page footer says", printed, "(PDF page", real[0], ")")
        bad += 1
print("mismatches:", bad)
ph = [(i + 1, m) for i, t in enumerate(txt) for m in re.findall(r"\[[^\]]*(?:to be filled|to confirm|TODO)[^\]]*\]", t)]
print("placeholders left:", len(ph))
for pg, m in ph:
    print("  page", pg, m)
