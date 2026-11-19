"""Build the capstone report exactly in the VIT-AP template (CAPSTONE_THESIS_Sample_Format.docx) from the EDITED report
(the user's working file, e.g. "From Paper to Patient ECG - updated.docx"): its Chapter 1 to Chapter 7 content is moved into a copy of the template;
cover, certificate, acknowledgement, abstract, contents, lists, biodata pages and the closing note keep the template's own layout, sections, margins and footers.
Usage: python -I scripts/tools/build_report_from_edited.py <template.docx> <edited.docx> <out.docx> <pages.json> <photo.jpg>
pages.json maps keys to page numbers; pass an empty {} on the first pass, then run refresh_page_numbers.py on a PDF render and rebuild."""
import copy
import io
import json
import re
import sys
from xml.sax.saxutils import escape

import docx
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Inches
from docx.text.paragraph import Paragraph

TEMPLATE, EDITED, OUT, PAGESJSON, PHOTO = sys.argv[1:6]
PAGES = json.load(open(PAGESJSON, encoding="utf-8"))
NS = nsdecls("w", "r", "wp", "a", "pic")
TOC_WIDTHS = (983, 1212, 5180, 1879)

t = docx.Document(TEMPLATE)
s = docx.Document(EDITED)
tb, sb = t.element.body, s.element.body
T = list(tb)
S = list(sb)


def text_of(el):
    return "".join(x.text or "" for x in el.iter(qn("w:t")))


def page_of(key):
    return str(PAGES.get(key, "0"))


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
    for child in list(p):
        if child.tag != qn("w:pPr"):
            p.remove(child)
    for text, flags in segments:
        p.append(parse_xml(f"<w:p {NS}>" + run_xml(text, "b" in flags, "i" in flags, base_sz, "EE0000" if "r" in flags else None, "h" in flags) + "</w:p>")[0])


def first_bold(p):
    r = p.find(qn("w:r"))
    if r is None:
        return False
    b = r.find(qn("w:rPr") + "/" + qn("w:b"))
    return b is not None and b.get(qn("w:val")) not in ("0", "false")


def find_p(prefix):
    return next(e for e in S if e.tag == qn("w:p") and text_of(e).strip().startswith(prefix))


# ---------------------------------------------------------------- front matter, from the edited file
TITLE = text_of(find_p("FROM PAPER TO PATIENT")).strip()
cert_src = text_of(find_p("This is to certify that the Capstone Project work titled"))
m = re.match(r"This is to certify that the Capstone Project work titled .(.*). that is being submitted by (.*) is in partial fulfillment (.*)$", cert_src, re.S)
cert_title, cert_names, cert_rest = m.group(1), m.group(2), m.group(3)
NAMES = [("MATCHA KARTHIK", "23BCE9569", "7674948903"), ("REDDI NAVYA", "23BCE9587", "9346647959"),
         ("NIHAR SAI ADITHYA", "23BCE7567", "9182657317"), ("THANUSH NAIDU", "23BCE20244", "9121391426")]
GUIDE = "Dr. Tarun Narayan Shankar"

set_runs(T[0], [(TITLE, "b")], 32)
set_runs(T[1], [])
for idx, (nm, reg, _) in zip((18, 19, 20, 21), NAMES):
    set_runs(T[idx], [(f"{nm} ({reg})", "b")], 28)
set_runs(T[26], [(GUIDE.upper(), "b")])
set_runs(T[42], [("This is to certify that the Capstone Project work titled “", ""), (cert_title, "b"), ("” that is being submitted by ", ""), (cert_names, "b"),
                 (" is in partial fulfillment " + cert_rest, "")], 28)
set_runs(T[45], [(GUIDE, "i")])
set_runs(T[58], [("HoD, Department of Computer Science and Engineering", "")])

ack_hod = text_of(find_p("We express our sincere thanks")).strip()
ack_guide = text_of(find_p("We are profoundly grateful")).strip()
ack_res = text_of(find_p("We also thank the authors")).strip()
set_runs(T[67], [(ack_hod, "")])
set_runs(T[69], [(ack_guide, "")])
res_p = copy.deepcopy(T[71])
set_runs(res_p, [(ack_res, "")])
res_blank = copy.deepcopy(T[72])
T[73].addprevious(res_p)
T[73].addprevious(res_blank)
for idx, (nm, reg, _) in zip((76, 77, 78, 79), NAMES):
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


for blank in (T[64], T[66], T[68], T[70], T[72], T[74], res_blank):
    if text_of(blank) == "":
        shrink_blank(blank, 8)
for idx in [61, 80, 81, 82] + list(range(89, 107)):
    el = T[idx]
    assert el.tag == qn("w:p") and not el.findall(".//" + qn("w:drawing")) and el.find(".//" + qn("w:sectPr")) is None
    assert text_of(el).strip() == ""
    tb.remove(el)
for ackp in (T[63], T[65], T[67], T[69], T[71], res_p, T[73]):  # a little tighter, so that the longer text still fits on one page
    for sp in ackp.find(qn("w:pPr")).findall(qn("w:spacing")):
        sp.set(qn("w:line"), "330")
page_break_before(T[62])
page_break_before(T[83])
page_break_before(T[107])

abstract_txt = text_of(find_p("Many electrocardiograms (ECGs) exist only as printouts")).strip()
set_runs(T[87], [(abstract_txt, "")])
for sp in T[87].find(qn("w:pPr")).findall(qn("w:spacing")):
    sp.set(qn("w:line"), "300")
kw = text_of(find_p("Keywords:")).strip()
kw_p = copy.deepcopy(T[87])
set_runs(kw_p, [("Keywords:", "b"), (kw[len("Keywords:"):], "")])
blank = copy.deepcopy(T[88])
T[87].addnext(blank)
blank.addnext(kw_p)

# ---------------------------------------------------------------- the body, from the edited file
body_items = []
img_id = [9000]


def heading1(num, title):
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


def fix_table(tbl):
    tblpr = tbl.find(qn("w:tblPr"))
    if tblpr.find(qn("w:jc")) is None:
        tblpr.insert(1, parse_xml(f'<w:jc {NS} w:val="center"/>'))
    return tbl


def fix_images(el):
    for blip in el.iter(qn("a:blip")):
        rid = blip.get(qn("r:embed"))
        new_rid, _ = t.part.get_or_add_image(io.BytesIO(s.part.related_parts[rid].blob))
        blip.set(qn("r:embed"), new_rid)
    for dp in el.iter("{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}docPr"):
        img_id[0] += 1
        dp.set("id", str(img_id[0]))


CAP = re.compile(r"^(Table|Figure) ([0-9A-Z]+\.\d+):? (.*)$", re.S)
SECT = re.compile(r"^(\d+\.\d+(?:\.\d+)?|[A-G]\.) \S")
new = []


def is_blank(e):
    return e.tag == qn("w:p") and text_of(e).strip() == "" and e.find(".//" + qn("w:drawing")) is None


def blank_el():
    return para("", "")


i0 = next(i for i, e in enumerate(S) if e.tag == qn("w:p") and text_of(e).strip() == "CHAPTER 1")
iend = next(i for i, e in enumerate(S) if i > i0 and e.tag == qn("w:p") and text_of(e).strip() == "BIODATA")
region = S[i0:iend]
k = 0
while k < len(region):
    el = region[k]
    k += 1
    if el.tag == qn("w:sectPr"):
        continue
    if el.tag == qn("w:tbl"):
        new.append(fix_table(copy.deepcopy(el)))
        continue
    txt = text_of(el).strip()
    ppr_sect = el.find(qn("w:pPr") + "/" + qn("w:sectPr"))
    if is_blank(el):
        if ppr_sect is not None:
            continue
        if new and not is_blank(new[-1]):
            new.append(blank_el())
        continue
    m1 = re.fullmatch(r"CHAPTER (\d)", txt)
    if m1:
        while is_blank(region[k]):
            k += 1
        title = text_of(region[k]).strip()
        k += 1
        while new and is_blank(new[-1]):
            new.pop()
        new.append(heading1(int(m1.group(1)), title))
        continue
    style = el.find(qn("w:pPr") + "/" + qn("w:pStyle"))
    style = style.get(qn("w:val")) if style is not None else ""
    cm = CAP.match(txt)
    if cm and (first_bold(el) or style == "Caption") and len(txt) < 400:
        kind, num, title = cm.groups()
        body_items.append((kind, num, title))
        label = f"{kind} {num} {title}"
        if new and is_blank(new[-1]) and kind == "Table":
            new.pop()
        if kind == "Figure":
            p = para(run_xml(label), '<w:pStyle w:val="Caption"/><w:spacing w:before="60" w:after="200"/><w:jc w:val="center"/>')
        else:
            p = para(run_xml(label, bold=True), '<w:keepNext/><w:spacing w:before="200" w:after="100" w:line="360" w:lineRule="auto"/><w:jc w:val="center"/>')
        new.append(p)
        continue
    if SECT.match(txt) and first_bold(el) and len(txt) < 110:
        while new and is_blank(new[-1]):
            new.pop()
        new.append(heading2(txt))
        continue
    p = copy.deepcopy(el)
    for tag in ("w:bookmarkStart", "w:bookmarkEnd", "w:lastRenderedPageBreak"):
        for e in list(p.iter(qn(tag))):
            e.getparent().remove(e)
    for sp in p.findall(qn("w:pPr") + "/" + qn("w:sectPr")):
        sp.getparent().remove(sp)
    if p.find(".//" + qn("w:drawing")) is not None:
        fix_images(p)
        new.append(p)
        continue
    num = p.find(".//" + qn("w:numId"))
    if num is not None:
        num.set(qn("w:val"), "3")
    new.append(p)
while new and is_blank(new[-1]):
    new.pop()

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
WPNS = "{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}"
ANS = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
EXTRA = {"NIHAR SAI ADITHYA": dict(email="adithya.23bce7567@vitap.ac.in",
                                   address="19-14-287/A, Beside Sai Baba Temple, Raghavendra Nagar, Tirupati, Andhra Pradesh - 517501", photo=PHOTO)}


def fill_bio(block, name, reg, mobile, email=None, address=None, photo=None):
    for p in block:
        if p.tag != qn("w:p"):
            continue
        for r in p.iter(qn("w:t")):
            if r.text == "xxxxx":
                r.text = f"{name.title()} ({reg})"
            elif r.text and "123456789" in r.text:
                r.text = r.text.replace("123456789", mobile)
            elif r.text == "xx.xxxx" and email:  # the template splits the address into runs: xx.xxxx | @vit | ap | .ac.in
                r.text = email.split("@")[0]
        full = text_of(p)
        if "Permanaent Address" in full:
            for r in p.iter(qn("w:t")):
                if r.text and "Permanaent" in r.text:
                    r.text = r.text.replace("Permanaent", "Permanent")
            if address:
                ppr = p.find(qn("w:pPr"))
                ind = parse_xml(f'<w:ind {NS} w:left="3050" w:hanging="3050"/>')
                jc = ppr.find(qn("w:jc"))
                (jc.addprevious(ind) if jc is not None else ppr.append(ind))
                if jc is not None:
                    jc.set(qn("w:val"), "left")
                runs = p.findall(qn("w:r"))
                extra = copy.deepcopy(runs[-1])
                for x in list(extra):
                    if x.tag != qn("w:rPr"):
                        extra.remove(x)
                tt = parse_xml(f'<w:t {NS} xml:space="preserve">{escape(address)}</w:t>')
                extra.append(tt)
                runs[-1].addnext(extra)
    if photo:
        # put the picture into the photo box of the template (the first text box = the modern branch of the alternate content)
        box = next(c for e in block for c in e.iter(qn("w:txbxContent")))
        bp = box.find(qn("w:p"))
        for x in list(bp):
            if x.tag != qn("w:pPr"):
                bp.remove(x)
        par = Paragraph(bp, t._body)
        par.add_run().add_picture(photo, width=Inches(1.0))
        anchor_el = next(a for e in block for a in e.iter(WPNS + "anchor"))
        anchor_el.find(WPNS + "extent").set("cy", "1450000")
        for e in anchor_el.iter(ANS + "ext"):
            e.set("cy", "1450000")


def renumber(block):
    for c in block:
        for dp in c.iter(WPNS + "docPr"):
            img_id[0] += 1
            dp.set("id", str(img_id[0]))


pristine = [copy.deepcopy(e) for e in bio_blocks]
fill_bio(bio_blocks, NAMES[0][0], NAMES[0][1], NAMES[0][2], **EXTRA.get(NAMES[0][0], {}))
last = bio_blocks[-1]
for nm, reg, mob in NAMES[1:]:
    pb = copy.deepcopy(bio_pb)
    last.addnext(pb)
    last = pb
    block = [copy.deepcopy(e) for e in pristine]
    renumber(block)
    for c in block:
        last.addnext(c)
        last = c
    fill_bio(block, nm, reg, mob, **EXTRA.get(nm, {}))

# ---------------------------------------------------------------- drop template pictures and charts nobody refers to any more
from lxml import etree
doc_xml = etree.tostring(t.element).decode()
for rid, rel in list(t.part.rels.items()):
    if rel.reltype.endswith("/image") or rel.reltype.endswith("/chart"):
        if f'"{rid}"' not in doc_xml:
            t.part.rels.pop(rid)

cp = t.core_properties
cp.title = TITLE.title().replace("Ecg", "ECG")
cp.author = ""
t.save(OUT)
print("saved", OUT, "| body items:", len(body_items), "| tables:", sum(1 for x in body_items if x[0] == "Table"), "| figures:", sum(1 for x in body_items if x[0] == "Figure"))
