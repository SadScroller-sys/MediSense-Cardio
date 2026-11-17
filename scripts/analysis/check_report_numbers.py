"""Check that the numbers written in the Word report (and optionally the LaTeX papers) appear in results/FINAL_NUMBERS.md or in the method files.
  python -I scripts/analysis/check_report_numbers.py <file.docx|file.tex> [...]
Prints every number-like token of the document that is NOT found in the allowed sources, with a bit of context, so a person can check it. This is a typo and stale-number check, not a proof of correctness."""
import re
import sys
import zipfile

ROOT = "D:/Capstone Project/"
SOURCES = [ROOT + "results/FINAL_NUMBERS.md", ROOT + "docs/reports/METHODS_AND_FORMULAE.md", ROOT + "docs/plan/analysis_plan_changes.md", ROOT + "docs/reports/CODE_MAP.md"]
NUM = re.compile(r"(?<![\w.])[-+]?\d[\d,]*\.?\d*(?![\w])")


def text_of(path):
    if path.endswith(".docx"):
        x = zipfile.ZipFile(path).read("word/document.xml").decode("utf8")
        x = re.sub(r"</w:p>", "\n", x)
        return re.sub(r"<[^>]+>", "", x)
    return open(path, encoding="utf-8").read()


def norm(tok):
    t = tok.replace(",", "").lstrip("+-")
    return t.rstrip(".")


allowed = set()
for s in SOURCES:
    for m in NUM.finditer(open(s, encoding="utf-8").read().replace("{,}", ",")):
        allowed.add(norm(m.group(0)))
for path in sys.argv[1:]:
    t = text_of(path)
    # drop the reference list and the table of contents lines, which contain years and page numbers
    cut = t.find("REFERENCES")
    body = t[:cut] if cut > 0 else t
    seen = {}
    for m in NUM.finditer(body):
        tok = norm(m.group(0))
        if tok in allowed or len(tok) == 0:
            continue
        if re.fullmatch(r"[0-9]{1,2}", tok):      # small integers: citation numbers, counts, section numbers
            continue
        if re.fullmatch(r"(19|20)\d\d", tok):     # years
            continue
        seen.setdefault(tok, body[max(0, m.start() - 50):m.end() + 30].replace("\n", " "))
    print(f"== {path}: {len(seen)} numbers not found in the sources")
    for k, v in seen.items():
        print(f"  {k:>10}  ...{v}...")
