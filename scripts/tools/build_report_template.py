"""Build the capstone report in the VIT-AP template (CAPSTONE_THESIS_Sample_Format.docx).

The template file is the base: its cover, certificate, sections, headers, footers and back pages stay as they are.
The text and figures come from the v4 report (SUBMISSION/01_report/CAPSTONE_REPORT_v4_review.docx); nothing in the
body text is rewritten except the sentence of Section 1.4 that lists the chapters (Chapter 6 and 7 now exist).

Usage:  python -I scripts/tools/build_report_template.py <template.docx> <v4.docx> <out.docx> [pages.json] [fig_results_at_a_glance.png]
pages.json (optional) maps a key to a page number; it is written by scripts/tools/report_pages.py from a PDF render.
"""
import copy
import io
import json
import re
import sys
from xml.sax.saxutils import escape

import docx
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls, qn

TEMPLATE, V4, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
PAGES = json.load(open(sys.argv[4], encoding="utf-8")) if len(sys.argv) > 4 else {}
NS = nsdecls("w", "r", "wp", "a", "pic")
TOC_WIDTHS = (983, 1212, 5180, 1879)
BODY_FONT_SZ = 24

t = docx.Document(TEMPLATE)
s = docx.Document(V4)
tb, sb = t.element.body, s.element.body

# ---------------------------------------------------------------- updates after the v4 text (results of 18 November 2026)
import hashlib

FIG44_OLD = "dd6b5a86"  # md5 prefix of Figure 4.4 as embedded in the v4 file (sections 10.1 to 10.34 only)
FIG44_NEW = open(sys.argv[5], "rb").read() if len(sys.argv) > 5 else None
TEXT_FIXES = [
    ("so the app shows only found or not found for two patterns (infarction and ST/T change) and no percentage.",
     "so, at this stage, the app shows only found or not found for two patterns (infarction and ST/T change) and no percentage (a later calibration of the infarction score is described below)."),
    ("it adds two ECG patterns (infarction and ST/T change) as found or not found, never with a percentage.",
     "it adds two ECG patterns (infarction and ST/T change) as found or not found; for infarction it also shows the calibrated percentage of Section 4.12, labelled as a second attempt on simulated photographs and not tested on real photos. No other pattern is shown with a percentage."),
]
for old, new_text in TEXT_FIXES:
    hit = [r for r in s.element.body.iter(qn("w:t")) if old in (r.text or "")]
    assert len(hit) == 1, old[:50]
    hit[0].text = hit[0].text.replace(old, new_text)

T = list(tb)  # template elements, indices as analysed
S = list(sb)


def text_of(el):
    return "".join(x.text or "" for x in el.iter(qn("w:t")))


def page_of(key):
    return str(PAGES.get(key, "0"))


# ---------------------------------------------------------------- small builders
def run_xml(text, bold=False, italic=False, sz=None, color=None, highlight=False):
    rpr = ""
    if bold:
        rpr += "<w:b/><w:bCs/>"
    if italic:
        rpr += "<w:i/><w:iCs/>"
    if color:
        rpr += f'<w:color w:val="{color}"/>'
    if sz:
        rpr += f'<w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/>'
    if highlight:
        rpr += '<w:highlight w:val="yellow"/>'
    rpr = f"<w:rPr>{rpr}</w:rPr>" if rpr else ""
    return f'<w:r>{rpr}<w:t xml:space="preserve">{escape(text)}</w:t></w:r>'


def para(runs="", ppr=""):
    return parse_xml(f"<w:p {NS}><w:pPr>{ppr}</w:pPr>{runs}</w:p>")


def set_runs(p, segments, base_sz=None):
    """Replace the runs of p by segments [(text, flags)], keeping the paragraph properties.
    flags: b = bold, i = italic, h = highlighted placeholder, r = red."""
    for child in list(p):
        if child.tag != qn("w:pPr"):
            p.remove(child)
    for text, flags in segments:
        p.append(parse_xml(f"<w:p {NS}>" + run_xml(text, "b" in flags, "i" in flags, base_sz, "EE0000" if "r" in flags else None, "h" in flags) + "</w:p>")[0])


def marked(text):
    """'plain {{placeholder}} plain' -> segments, placeholders highlighted."""
    out = []
    for i, part in enumerate(re.split(r"\{\{|\}\}", text)):
        if part:
            out.append((part, "h" if i % 2 else ""))
    return out


# ---------------------------------------------------------------- front matter
TITLE = text_of(S[0]).strip()
WORKING = text_of(S[1]).strip()
cert_src = text_of(S[22])
m = re.match(r"This is to certify that the Capstone Project work titled .(.*). that is being submitted by (.*) is in partial fulfillment (.*)$", cert_src, re.S)
cert_title, cert_names, cert_rest = m.group(1), m.group(2), m.group(3)
NAMES = [("MATCHA KARTHIK", "23BCE9569"), ("REDDI NAVYA", "23BCE9587"), ("NIHAR SAI ADITHYA", "23BCE7567"), ("THANUSH NAIDU", "23BCE20244")]
GUIDE = "Dr. Tarun Narayan Shankar"

# cover
set_runs(T[0], [(TITLE, "b")], 32)
set_runs(T[1], [(WORKING, "i")], 24)
for idx, (nm, reg) in zip((18, 19, 20, 21), NAMES):
    set_runs(T[idx], [(f"{nm} ({reg})", "b")], 28)
set_runs(T[26], [(GUIDE.upper(), "b")])

# certificate
set_runs(T[42], [("This is to certify that the Capstone Project work titled “", ""), (cert_title, "b"), ("” that is being submitted by ", ""), (cert_names, "b"),
                 (" is in partial fulfillment " + cert_rest, "")], 28)
set_runs(T[45], [(GUIDE, "i")])
set_runs(T[58], [("HoD, Department of ", ""), ("[DEPARTMENT TO BE CONFIRMED]", "h")])

# acknowledgement (template wording; names filled in; two sentences of the v4 text added)
ack = [text_of(S[i]) for i in (34, 35, 36, 37)]
set_runs(T[67], marked("We express our sincere thanks to Dr. S. Sudhakar Ilango, Dean, SCOPE, Dr. Saroj Kumar Panigrahy, Associate Dean, SCOPE, and {{Name of the HoD}}, HoD, {{Department}} for the continuous encouragement, academic support, and facilities provided throughout the project."))
guide_sentence = ack[0].split("for the guidance, regular review and encouragement that shaped this work. ")[1]
set_runs(T[69], [(f"We are profoundly grateful to {GUIDE}, our Project Supervisor/Guide, for the invaluable guidance, constant support, constructive feedback, and encouragement extended to us at every stage of this project. " + guide_sentence, "")])
res_p = copy.deepcopy(T[71])
set_runs(res_p, [(ack[2], "")])
res_blank = copy.deepcopy(T[72])
T[73].addprevious(res_p)
T[73].addprevious(res_blank)
for idx, (nm, reg) in zip((76, 77, 78, 79), NAMES):
    set_runs(T[idx], [(f"{nm.title()} – {reg}", "")])

def page_break_before(p):
    ppr = p.find(qn("w:pPr"))
    if ppr is None:
        ppr = parse_xml(f"<w:pPr {NS}/>")
        p.insert(0, ppr)
    pos = 0
    for k, c in enumerate(ppr):
        if c.tag in (qn("w:pStyle"), qn("w:keepNext"), qn("w:keepLines")):
            pos = k + 1
    ppr.insert(pos, parse_xml(f"<w:pageBreakBefore {NS}/>"))


def shrink_blank(p, sz):
    ppr = p.find(qn("w:pPr"))
    if ppr is None:
        ppr = parse_xml(f"<w:pPr {NS}/>")
        p.insert(0, ppr)
    for old in ppr.findall(qn("w:rPr")):
        ppr.remove(old)
    ppr.append(parse_xml(f'<w:rPr {NS}><w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/></w:rPr>'))


# the blank lines between the acknowledgement paragraphs are made small so that the page still holds the longer text
for blank in (T[64], T[66], T[68], T[70], T[72], T[74], res_blank):
    if text_of(blank) == "":
        shrink_blank(blank, 8)
# the template pads pages with empty paragraphs; real page breaks are used instead
for idx in [61, 80, 81, 82] + list(range(89, 107)):
    el = T[idx]
    assert el.tag == qn("w:p") and not el.findall(".//" + qn("w:drawing")) and el.find(".//" + qn("w:sectPr")) is None
    assert text_of(el).strip() == ""
    tb.remove(el)
page_break_before(T[62])
page_break_before(T[83])
page_break_before(T[107])

# abstract
abstract_txt = text_of(S[44]).strip()
set_runs(T[87], [(abstract_txt, "")])
for sp in T[87].find(qn("w:pPr")).findall(qn("w:spacing")):
    sp.set(qn("w:line"), "300")
kw = text_of(S[45]).strip()
kw_p = copy.deepcopy(T[87])
set_runs(kw_p, [("Keywords:", "b"), (kw[len("Keywords:"):], "")])
blank = copy.deepcopy(T[88])
T[87].addnext(blank)
blank.addnext(kw_p)

# ---------------------------------------------------------------- headings of the report body
body_items = []  # (kind, text) for the contents and lists
chapter_no = {"CHAPTER 1": 1}
APPX_CH, REF_CH = 6, 7


def heading1(text):
    m = re.match(r"CHAPTER (\d+): (.*)", text)
    if m:
        num, title = int(m.group(1)), m.group(2)
    elif text == "APPENDIX":
        num, title = APPX_CH, "APPENDIX"
    else:
        num, title = REF_CH, "REFERENCES"
    p = parse_xml(
        f'<w:p {NS}><w:pPr><w:keepNext/><w:pageBreakBefore/><w:spacing w:after="240" w:line="360" w:lineRule="auto"/><w:jc w:val="center"/><w:outlineLvl w:val="0"/></w:pPr>'
        f'<w:r><w:rPr><w:b/><w:sz w:val="28"/><w:szCs w:val="28"/></w:rPr><w:t>CHAPTER {num}</w:t><w:br/><w:t>{escape(title)}</w:t></w:r></w:p>')
    body_items.append(("H1", num, title))
    return p


def heading2(text):
    three = re.match(r"^\d+\.\d+\.\d+ ", text)
    sz = 26 if three else 28
    p = parse_xml(
        f'<w:p {NS}><w:pPr><w:keepNext/><w:spacing w:before="200" w:after="80" w:line="360" w:lineRule="auto"/><w:outlineLvl w:val="{2 if three else 1}"/></w:pPr>'
        f'<w:r><w:rPr><w:b/><w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/></w:rPr><w:t xml:space="preserve">{escape(text)}</w:t></w:r></w:p>')
    body_items.append(("H3" if three else "H2", text))
    return p


# ---------------------------------------------------------------- copying the v4 body
width_scale = 9254 / 8600


def fix_table(tbl):
    for tag, attr in (("w:tblW", "w:w"), ("w:gridCol", "w:w"), ("w:tcW", "w:w")):
        for e in tbl.iter(qn(tag)):
            if e.get(qn(attr)) and e.get(qn("w:type"), "dxa") == "dxa":
                e.set(qn(attr), str(round(int(e.get(qn(attr))) * width_scale)))
    jc = parse_xml(f'<w:jc {NS} w:val="center"/>')
    tblpr = tbl.find(qn("w:tblPr"))
    tblpr.insert(1, jc)
    return tbl


img_id = [9000]


def fix_images(el):
    for blip in el.iter(qn("a:blip")):
        rid = blip.get(qn("r:embed"))
        blob = s.part.related_parts[rid].blob
        if FIG44_NEW and hashlib.md5(blob).hexdigest()[:8] == FIG44_OLD:
            blob = FIG44_NEW
        new_rid, _ = t.part.get_or_add_image(io.BytesIO(blob))
        blip.set(qn("r:embed"), new_rid)
    for dp in el.iter("{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}docPr"):
        img_id[0] += 1
        dp.set("id", str(img_id[0]))


CAP = re.compile(r"^(Table|Figure) ([0-9A-Z]+\.\d+): (.*)$", re.S)
new = []
in_refs = False
i0 = next(i for i, e in enumerate(S) if e.tag == qn("w:p") and text_of(e) == "CHAPTER 1: INTRODUCTION")
for el in S[i0:]:
    if el.tag == qn("w:sectPr"):
        continue
    if el.tag == qn("w:tbl"):
        c = copy.deepcopy(el)
        new.append(fix_table(c))
        continue
    style = el.find(qn("w:pPr") + "/" + qn("w:pStyle"))
    style = style.get(qn("w:val")) if style is not None else "Normal"
    txt = text_of(el).strip()
    if style == "Heading1":
        in_refs = txt == "REFERENCES"
        new.append(heading1(txt))
        continue
    if style == "Heading2":
        new.append(heading2(txt))
        continue
    p = copy.deepcopy(el)
    for tag in ("w:bookmarkStart", "w:bookmarkEnd", "w:lastRenderedPageBreak"):
        for e in list(p.iter(qn(tag))):
            e.getparent().remove(e)
    assert p.find(".//" + qn("w:fldChar")) is None and p.find(".//" + qn("w:hyperlink")) is None
    if p.find(".//" + qn("w:drawing")) is not None:
        fix_images(p)
        new.append(p)
        continue
    cm = CAP.match(txt)
    if cm:
        kind, num, title = cm.groups()
        body_items.append((kind, num, title))
        label = f"{kind} {num} {title}"
        if kind == "Figure":
            p = para(run_xml(label), '<w:pStyle w:val="Caption"/><w:spacing w:before="60" w:after="200"/><w:jc w:val="center"/>')
        else:
            p = para(run_xml(label, bold=True), '<w:keepNext/><w:spacing w:before="200" w:after="100" w:line="360" w:lineRule="auto"/><w:jc w:val="center"/>')
        new.append(p)
        continue
    # list items: bullets of the template (numId 3)
    num = p.find(".//" + qn("w:numId"))
    if num is not None:
        num.set(qn("w:val"), "3")
    if txt.startswith("Chapter 2 describes the system and the methods."):
        old = "The appendix and references follow."
        assert old in txt
        for r in p.iter(qn("w:t")):
            if old in (r.text or ""):
                r.text = r.text.replace(old, "Chapter 6 is the appendix and Chapter 7 gives the references.")
    if in_refs and re.match(r"^\[\d+\]", txt):
        for ppr in p.findall(qn("w:pPr")):
            p.remove(ppr)
        p.insert(0, parse_xml(f'<w:pPr {NS}><w:spacing w:after="160"/><w:jc w:val="both"/></w:pPr>'))
        for r in p.iter(qn("w:r")):
            rpr = r.find(qn("w:rPr"))
            if rpr is None:
                rpr = parse_xml(f"<w:rPr {NS}/>")
                r.insert(0, rpr)
            for tag in ("w:sz", "w:szCs"):
                rpr.append(parse_xml(f'<w:{tag[2:]} {NS} w:val="23"/>'))
    new.append(p)

# ---------------------------------------------------------------- contents, list of tables, list of figures
def borderless_table(widths, rows, header, aligns, title_col, hdr_sz=28, sz=22):
    """rows: list of (cells, bold, indent); aligns: jc per column (None = left); indent applies to title_col."""
    grid = "".join(f'<w:gridCol w:w="{w}"/>' for w in widths)

    def cell(w, text, bold, sz_, jc, ind=0):
        ppr = '<w:spacing w:before="10" w:after="20"/>' + (f'<w:ind w:left="{ind}"/>' if ind else "") + (f'<w:jc w:val="{jc}"/>' if jc else "")
        return f'<w:tc><w:tcPr><w:tcW w:w="{w}" w:type="dxa"/></w:tcPr><w:p><w:pPr>{ppr}</w:pPr>{run_xml(text, bold, sz=sz_) if text else ""}</w:p></w:tc>'

    xml = (f'<w:tbl {NS}><w:tblPr><w:tblW w:w="{sum(widths)}" w:type="dxa"/><w:tblLayout w:type="fixed"/>'
           f'<w:tblLook w:val="04A0" w:firstRow="1" w:lastRow="0" w:firstColumn="1" w:lastColumn="0" w:noHBand="0" w:noVBand="1"/></w:tblPr><w:tblGrid>{grid}</w:tblGrid>')
    xml += '<w:tr><w:trPr><w:cantSplit/><w:tblHeader/></w:trPr>' + "".join(
        cell(w, h, True, hdr_sz, "center" if k != title_col else None) for k, (w, h) in enumerate(zip(widths, header))) + "</w:tr>"
    for cells, bold, ind in rows:
        xml += "<w:tr><w:trPr><w:cantSplit/></w:trPr>"
        for k, (w, c) in enumerate(zip(widths, cells)):
            xml += cell(w, c, bold, sz, aligns[k], ind if k == title_col else 0)
        xml += "</w:tr>"
    return parse_xml(xml + "</w:tbl>")


CH_TITLE = {1: "Introduction", 2: "System and Method", 3: "Cost Analysis", 4: "Results and Discussion", 5: "Conclusion and Future Work", 6: "Appendix", 7: "References"}
toc_rows = []
sno = 0
for title, key in (("Acknowledgement", "ACKNOWLEDGEMENT"), ("Abstract", "ABSTRACT"), ("List of Tables and Figures", "LISTS")):
    sno += 1
    toc_rows.append(((f"{sno}.", "", title, page_of(key)), False, 0))
cur_chapter = None
for it in body_items:
    if it[0] == "H1":
        sno += 1
        cur_chapter = it[1]
        toc_rows.append(((f"{sno}.", str(it[1]), CH_TITLE[it[1]], page_of(f"H1:{it[1]}")), True, 0))
    elif it[0] in ("H2", "H3"):
        mm = re.match(r"^(\d+(?:\.\d+)+|[A-Z])\.? (.*)$", it[1])
        toc_rows.append((("", mm.group(1), mm.group(2), page_of("H:" + it[1])), False, 0 if it[0] == "H2" else 300))
toc = borderless_table(TOC_WIDTHS, toc_rows, ("S.No.", "Chapter", "Title", "Page Number"), ["center", "center", None, "center"], 2)

LW = (1500, 6159, 1400)
lot_rows = [((it[1], it[2], page_of(f"C:{it[0]} {it[1]}")), False, 0) for it in body_items if it[0] == "Table"]
lof_rows = [((it[1], it[2], page_of(f"C:{it[0]} {it[1]}")), False, 0) for it in body_items if it[0] == "Figure"]
lot = borderless_table(LW, lot_rows, ("Table No.", "Title", "Page No."), ["center", None, "center"], 1)
lof = borderless_table(LW, lof_rows, ("Figure No.", "Title", "Page No."), ["center", None, "center"], 1)
# the title column of the lists is left-aligned


T[110].addprevious(toc)
tb.remove(T[110])
for idx in range(116, 124):
    tb.remove(T[idx])
T[115].addnext(lot)
tb.remove(T[126])
T[125].addnext(lof)

# ---------------------------------------------------------------- put the body in, copy the biodata page
for idx in range(127, 1053):
    if T[idx].getparent() is not None:
        tb.remove(T[idx])
anchor = T[125] if False else lof
for el in new:
    anchor.addnext(el)
    anchor = el

bio_blocks = T[1054:1064]
bio_pb = T[1053]


def fill_bio(block, name, reg):
    for p in block:
        if p.tag != qn("w:p"):
            continue
        for r in p.iter(qn("w:t")):
            if r.text == "xxxxx":
                r.text = f"{name.title()} ({reg})"
            elif r.text and "123456789" in r.text:
                r.text = r.text.replace("123456789", "[to be filled]")
            elif r.text and "xx.xxxx@vitap.ac.in" in r.text:
                r.text = r.text.replace("xx.xxxx@vitap.ac.in", "[to be filled]")


pristine = [copy.deepcopy(e) for e in bio_blocks]
fill_bio(bio_blocks, *NAMES[0])
last = bio_blocks[-1]
for nm, reg in NAMES[1:]:
    pb = copy.deepcopy(bio_pb)
    last.addnext(pb)
    last = pb
    block = [copy.deepcopy(e) for e in pristine]
    for c in block:
        for dp in c.iter("{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}docPr"):
            img_id[0] += 1
            dp.set("id", str(img_id[0]))
        last.addnext(c)
        last = c
    fill_bio(block, nm, reg)

# ---------------------------------------------------------------- drop template pictures and charts nobody refers to any more
from lxml import etree
doc_xml = etree.tostring(t.element).decode()
for rid, rel in list(t.part.rels.items()):
    if rel.reltype.endswith("/image") or rel.reltype.endswith("/chart"):
        if f'"{rid}"' not in doc_xml:
            t.part.rels.pop(rid)

cp = t.core_properties
cp.title = TITLE.title()
cp.author = ""
t.save(OUT)
print("saved", OUT, "| body items:", len(body_items), "| tables:", sum(1 for x in body_items if x[0] == "Table"), "| figures:", sum(1 for x in body_items if x[0] == "Figure"))
