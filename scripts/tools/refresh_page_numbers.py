"""Write the real page numbers into the contents table, the list of tables and the list of figures of a report docx.
The page numbers are read from a PDF render of the same file made by Word (printed number = first line of the page text).
Usage: python -I scripts/tools/refresh_page_numbers.py <report.docx> <render.pdf>   (the docx is edited in place; make a backup first)
Run it twice with a new render in between to check that the numbers are stable."""
import re
import sys

import docx
import pymupdf

PATH, PDF = sys.argv[1], sys.argv[2]
norm = lambda x: re.sub(r"\s+", " ", x).strip()  # noqa: E731
doc = pymupdf.open(PDF)
pages = []  # (printed number or None, normalised text)
for p in doc:
    raw = p.get_text().strip().split("\n")
    first = raw[0].strip() if raw else ""
    last = raw[-1].strip() if raw else ""
    printed = int(first) if first.isdigit() else (int(last) if last.isdigit() else None)
    pages.append((printed, norm(p.get_text())))

d = docx.Document(PATH)
toc, lot, lof = d.tables[0], d.tables[1], d.tables[2]

first_ch = next(i for i, (n, t) in enumerate(pages) if "INTRODUCTION" in t and "1.1 Objectives" in t and "S.No." not in t and "Table No." not in t)


def find(needle, start=0):
    needle = norm(needle)
    for i in range(start, len(pages)):
        if needle in pages[i][1]:
            return pages[i][0]
    print("NOT FOUND:", needle[:70])
    return None


def setcell(cell, v):
    par = cell.paragraphs[0]
    if par.runs:
        par.runs[0].text = str(v)
        for r in par.runs[1:]:
            r.text = ""
    else:
        par.add_run(str(v))


CHAPTER_TITLE = {"1": "INTRODUCTION", "2": "SYSTEM AND METHOD", "3": "COST ANALYSIS", "4": "RESULTS AND DISCUSSION", "5": "CONCLUSION AND FUTURE WORK", "6": "APPENDIX", "7": "REFERENCES"}
changed = 0
for r in toc.rows[1:]:
    c = [x.text.strip() for x in r.cells]
    s_no, num, title = c[0], c[1], c[2]
    pg = None
    if not num:  # front rows
        key = {"Acknowledgement": "ACKNOWLEDGEMENT", "Abstract": "ABSTRACT", "List of Tables and Figures": "List of Tables"}.get(title)
        if key:
            pg = next((pages[i][0] for i in range(0, first_ch) if key in pages[i][1] and "S.No." not in pages[i][1]), None)
    elif num in CHAPTER_TITLE:
        pg = find(CHAPTER_TITLE[num], first_ch)  # the label "CHAPTER n" may sit at the foot of the page before
    elif re.fullmatch(r"[A-Z]", num):
        pg = find(f"{num}. {title}", first_ch)
    else:
        pg = find(f"{num} {title}", first_ch)
    if pg is not None and r.cells[3].text.strip() != str(pg):
        setcell(r.cells[3], pg)
        changed += 1
for tbl in (lot, lof):
    for r in tbl.rows[1:]:
        c = [x.text.strip() for x in r.cells]
        kind = "Table" if tbl is lot else "Figure"
        pg = find(f"{kind} {c[0]} {c[1]}"[:75], first_ch)
        if pg is not None and r.cells[2].text.strip() != str(pg):
            setcell(r.cells[2], pg)
            changed += 1
d.save(PATH)
print("cells changed:", changed, "| first chapter pdf page:", first_ch)
