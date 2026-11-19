"""Read a PDF render of the template-based report and write pages.json (page numbers for the contents, list of tables and list of figures).
The printed page number of a PDF page is its index, because the cover page (index 0) has no number and the certificate is page 1.
Usage: python -I scripts/tools/report_pages.py <report.pdf> <v4.docx> <pages.json>"""
import json
import re
import sys

import docx
import pymupdf
from docx.oxml.ns import qn

pdf, v4, out = sys.argv[1:4]
doc = pymupdf.open(pdf)
norm = lambda x: re.sub(r"\s+", " ", x).strip()  # noqa: E731
pages = [norm(p.get_text()) for p in doc]
s = docx.Document(v4)
text = lambda e: norm("".join(x.text or "" for x in e.iter(qn("w:t"))))  # noqa: E731

first_ch1 = next(i for i, t in enumerate(pages) if re.search(r"CHAPTER 1 INTRODUCTION", t) and "Table No." not in t and "S.No." not in t)
res = {}


def find_from(start, needle, label):
    for i in range(start, len(pages)):
        if needle in pages[i]:
            return i
    print("NOT FOUND:", label, "|", needle[:60])
    return None


res["ACKNOWLEDGEMENT"] = find_from(0, "ACKNOWLEDGEMENT", "ack")
res["ABSTRACT"] = find_from(0, "ABSTRACT", "abstract")
res["LISTS"] = next((i for i, t in enumerate(pages) if "List of Tables" in t and "Table No." in t), None)
chapter_titles = {1: "INTRODUCTION", 2: "SYSTEM AND METHOD", 3: "COST ANALYSIS", 4: "RESULTS AND DISCUSSION", 5: "CONCLUSION AND FUTURE WORK", 6: "APPENDIX", 7: "REFERENCES"}
for n, tt in chapter_titles.items():
    res[f"H1:{n}"] = find_from(first_ch1, f"CHAPTER {n} {tt}", f"chapter {n}")
for e in s.element.body:
    if e.tag != qn("w:p"):
        continue
    st = e.find(qn("w:pPr") + "/" + qn("w:pStyle"))
    st = st.get(qn("w:val")) if st is not None else ""
    tx = text(e)
    if st == "Heading2":
        res["H:" + tx] = find_from(first_ch1, tx, tx)
    m = re.match(r"^(Table|Figure) ([0-9A-Z]+\.\d+): (.*)$", tx)
    if m:
        res[f"C:{m.group(1)} {m.group(2)}"] = find_from(first_ch1, f"{m.group(1)} {m.group(2)} {m.group(3)}"[:70], tx[:40])
res = {k: v for k, v in res.items() if v is not None}
json.dump(res, open(out, "w", encoding="utf-8"), indent=1)
print(len(res), "entries; first chapter page", first_ch1, "of", len(pages), "pdf pages")
