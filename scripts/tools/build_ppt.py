"""Fill the VIT-AP Capstone final-review template (slides 3-15) from the frozen numbers.
Run: python -I scripts/tools/build_ppt.py   (reads the template, writes SUBMISSION/07_presentation/Capstone_Final_Review.pptx)
All numbers come from results/FINAL_NUMBERS.md. Template titles/sub-headings are kept."""
import copy, os
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from lxml import etree

ROOT = r"D:\Capstone Project"
SRC = os.path.join(ROOT, "SUBMISSION", "07_presentation", "Capstone_Final_Review.pptx")  # slide 1 already filled
TEMPLATE = r"C:\Users\Nihar Sai\Downloads\Capstone_PPT_Template.pptx"
OUT = SRC
FIG = os.path.join(ROOT, "docs", "reports", "figures")
EX = os.path.join(ROOT, "demo", "dataset_examples")

MAROON = RGBColor(0x57, 0x23, 0x14); RED = RGBColor(0x9E, 0x1B, 0x14); TEAL = RGBColor(0x38, 0x91, 0xA7)
INK = RGBColor(0x1E, 0x1E, 0x1E); GREY = RGBColor(0x59, 0x59, 0x59)
TINT = RGBColor(0xF8, 0xF0, 0xEC); LINE = RGBColor(0xE2, 0xCF, 0xC8); WHITE = RGBColor(255, 255, 255)
GREEN = RGBColor(0x2E, 0x8B, 0x57); AMBER = RGBColor(0xE0, 0x9A, 0x1A); REDL = RGBColor(0xC0, 0x39, 0x2B)
FONT = "Gill Sans MT"

prs = Presentation(TEMPLATE)          # always start from the pristine template, then redo slide 1
S = list(prs.slides)


# ---------------------------------------------------------------- helpers
def run(p, text, size=14, bold=False, color=INK, italic=False, font=FONT):
    r = p.add_run(); r.text = text; f = r.font
    f.size = Pt(size); f.bold = bold; f.italic = italic; f.name = font; f.color.rgb = color
    return r


def bullet_xml(p, color="3891A7", marL=0.2):
    pPr = p._p.get_or_add_pPr(); pPr.set("marL", str(int(Inches(marL)))); pPr.set("indent", str(-int(Inches(marL))))
    for tag in ("a:buClr", "a:buFont", "a:buChar", "a:buNone"):
        for e in pPr.findall(qn(tag)): pPr.remove(e)
    c = etree.SubElement(pPr, qn("a:buClr")); etree.SubElement(c, qn("a:srgbClr")).set("val", color)
    f = etree.SubElement(pPr, qn("a:buFont")); f.set("typeface", "Wingdings"); f.set("charset", "2")
    etree.SubElement(pPr, qn("a:buChar")).set("char", "\uf0a7")


def textbox(slide, x, y, w, h, anchor=MSO_ANCHOR.TOP, name=None, margin=0.05):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = True; tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(margin); tf.margin_top = tf.margin_bottom = Inches(0.03)
    if name: tb.name = name
    return tb, tf


def bullets(slide, x, y, w, h, items, size=14, gap=5, color=INK, name=None):
    """items: str or (bold_lead, rest). Teal square bullets."""
    tb, tf = textbox(slide, x, y, w, h, name=name)
    for i, it in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        bullet_xml(p); p.space_after = Pt(gap)
        if isinstance(it, tuple):
            run(p, it[0], size, True, color); run(p, it[1], size, False, color)
        else:
            run(p, it, size, False, color)
    return tb


def card(slide, x, y, w, h, head=None, body=None, hsize=14, bsize=12, fill=TINT, hcolor=MAROON, line=LINE, name=None):
    sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    sh.adjustments[0] = 0.06; sh.fill.solid(); sh.fill.fore_color.rgb = fill
    sh.line.color.rgb = line; sh.line.width = Pt(0.75); sh.shadow.inherit = False
    if name: sh.name = name
    tf = sh.text_frame; tf.word_wrap = True; tf.vertical_anchor = MSO_ANCHOR.TOP
    tf.margin_left = tf.margin_right = Inches(0.12); tf.margin_top = Inches(0.08); tf.margin_bottom = Inches(0.05)
    first = True
    if head:
        p = tf.paragraphs[0]; p.alignment = PP_ALIGN.LEFT; run(p, head, hsize, True, hcolor); p.space_after = Pt(3); first = False
    if body:
        for line_ in (body if isinstance(body, list) else [body]):
            p = tf.paragraphs[0] if first else tf.add_paragraph(); first = False
            p.alignment = PP_ALIGN.LEFT; p.space_after = Pt(2); run(p, line_, bsize, False, INK)
    return sh


def stat(slide, x, y, w, h, big, small, color=RED):
    sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    sh.adjustments[0] = 0.08; sh.fill.solid(); sh.fill.fore_color.rgb = TINT; sh.line.color.rgb = LINE; sh.line.width = Pt(0.75)
    sh.shadow.inherit = False
    tf = sh.text_frame; tf.word_wrap = True; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = tf.margin_right = Inches(0.08)
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER; run(p, big, 30, True, color)
    p2 = tf.add_paragraph(); p2.alignment = PP_ALIGN.CENTER; run(p2, small, 11.5, False, INK)
    return sh


def table(slide, x, y, w, col_w, rows, hsize=12, bsize=11.5, row_h=0.3, header=True):
    nrows, ncols = len(rows), len(rows[0])
    gs = slide.shapes.add_table(nrows, ncols, Inches(x), Inches(y), Inches(w), Inches(row_h * nrows))
    tbl = gs.table
    tblPr = tbl._tbl.tblPr
    for a in ("firstRow", "bandRow"): tblPr.set(a, "0")
    sid = tblPr.find(qn("a:tableStyleId"))
    if sid is not None: sid.text = "{5940675A-B579-460E-94D1-54222C63F5DA}"  # No Style, Table Grid
    for j, cw in enumerate(col_w): tbl.columns[j].width = Inches(cw)
    for i, row in enumerate(rows):
        tbl.rows[i].height = Inches(row_h)
        for j, val in enumerate(row):
            c = tbl.cell(i, j); c.margin_left = c.margin_right = Inches(0.07); c.margin_top = c.margin_bottom = Inches(0.03)
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf = c.text_frame; tf.word_wrap = True; p = tf.paragraphs[0]
            head = header and i == 0
            run(p, str(val), hsize if head else bsize, head or j == 0, WHITE if head else INK)
            c.fill.solid(); c.fill.fore_color.rgb = MAROON if head else (TINT if i % 2 == 0 else WHITE)
            tcPr = c._tc.get_or_add_tcPr()
            for side in ("a:lnL", "a:lnR", "a:lnT", "a:lnB"):
                ln = etree.SubElement(tcPr, qn(side)); ln.set("w", "6350")
                sf = etree.SubElement(ln, qn("a:solidFill")); etree.SubElement(sf, qn("a:srgbClr")).set("val", "E2CFC8")
            # a:ln* must precede the fill in tcPr: move fills to the end
            for f in tcPr.findall(qn("a:solidFill")): tcPr.remove(f); tcPr.append(f)
    return gs


def pic(slide, path, x, y, w=None, h=None, name=None):
    p = slide.shapes.add_picture(path, Inches(x), Inches(y), Inches(w) if w else None, Inches(h) if h else None)
    if name: p.name = name
    return p


def caption(slide, x, y, w, text, size=10.5, align=PP_ALIGN.LEFT, italic=True):
    tb, tf = textbox(slide, x, y, w, 0.3); p = tf.paragraphs[0]; p.alignment = align
    run(p, text, size, False, GREY, italic); return tb


def clean_body(slide, keep_first=True):
    """Keep the template's sub-heading line; drop the empty/placeholder lines under it; shrink the box to the sub-heading."""
    body = [s for s in slide.shapes if s.name == "TextShape 2"][0]
    ps = body.text_frame.paragraphs
    for p in ps[1:]: p._p.getparent().remove(p._p)
    body.height = Inches(0.5)
    return body


def set_page_no(slide, n):
    for s in slide.shapes:
        if s.has_text_frame and s.top > Inches(4.5) and s.left > Inches(8) and s.text_frame.text.strip().isdigit():
            r = s.text_frame.paragraphs[0].runs
            if r:
                r[0].text = str(n)
                for x in r[1:]: x.text = ""


def duplicate(slide, after_index):
    """Copy a content slide (title, sub-heading, page number, logo) so a heading can continue on a second slide."""
    new = prs.slides.add_slide(slide.slide_layout)
    for ph in list(new.shapes): ph._element.getparent().remove(ph._element)
    for sh in slide.shapes:
        if sh.shape_type == 13:
            blob = sh.image.blob
            import io
            np_ = new.shapes.add_picture(io.BytesIO(blob), sh.left, sh.top, sh.width, sh.height); np_.name = sh.name
        else:
            new.shapes._spTree.append(copy.deepcopy(sh._element))
    lst = prs.slides._sldIdLst; ids = list(lst); el = ids[-1]; lst.remove(el); lst.insert(after_index + 1, el)
    return new


def set_subheading(slide, text):
    body = [s for s in slide.shapes if s.name == "TextShape 2"][0]
    p = body.text_frame.paragraphs[0]
    p.runs[0].text = text
    for r in p.runs[1:]: r.text = ""


# ================================================================ SLIDE 1 (re-apply)
s = S[0]; sh = {x.name: x for x in s.shapes}
t = sh["TextShape 1"].text_frame.paragraphs[1]; r = t.runs[0]
r.text = "From Paper to Patient: Quantifying and Mitigating Digitization-Induced False Reassurance in Automated ECG Explanation"
r.font._element.set("sz", "2000"); t._p.find(qn("a:endParaRPr")).set("sz", "2000")
g = sh["TextShape 2"].text_frame.paragraphs[0]; rr = g.runs; rr[2].text = "Dr. Tarun Narayan Shankar"
for x in rr[3:]: g._p.remove(x._r)
tf = sh["CustomShape 3"].text_frame; ps = tf.paragraphs
new = copy.deepcopy(ps[0].runs[3]._r); new.find(qn("a:t")).text = " [to be confirmed]"; ps[0].runs[3]._r.addnext(new)
lab = ps[1]; body_ = lab._p.getparent()
for q in ps[2:]: body_.remove(q._p)
for ln in ["Matcha Karthik (23BCE9569)", "Reddi Navya (23BCE9587)", "Nihar Sai Adithya (23BCE7567)", "Thanush Naidu (23BCE20244)"]:
    n = copy.deepcopy(lab._p); x = n.findall(qn("a:r"))[0]; x.find(qn("a:t")).text = ln; x.find(qn("a:rPr")).set("b", "0"); body_.append(n)

# ================================================================ SLIDE 2 (outline: template list already matches; just tidy the first-line wording)
# left unchanged on purpose

# ================================================================ SLIDE 3 Project overview
s = S[2]; clean_body(s)
bullets(s, 0.35, 1.25, 5.3, 3.5, [
    ("The situation: ", "ECGs are now shared as photos or printouts. Apps turn the picture back into signals and explain it in plain words."),
    ("The risk: ", "a damaged photo can give a wrong number that looks normal, which is false reassurance."),
    ("Our work: ", "keep one open digitiser unchanged, measure when its numbers break, and warn the user with a traffic light."),
    ("Evidence: ", "ECGs with a known true answer, drawn as pages, damaged and photographed on a phone."),
    ("Also tried: ", "ECG-pattern findings and a 5-year risk range, kept as research hints. Not a medical device."),
], size=14, gap=6)
xs = [5.85, 7.9]; ys = [1.3, 2.85]
facts = [("150", "recordings damaged in 6 ways, 5 levels"), ("1,260", "real-capture images (140 recordings x 9 types)"),
         ("100", "own-phone photos of ECG pages on a screen"), ("1", "digitiser, used unchanged")]
for k, (b, t_) in enumerate(facts):
    stat(s, xs[k % 2], ys[k // 2], 1.95, 1.4, b, t_, color=MAROON)
caption(s, 5.85, 4.3, 4.0, "Numbers: results/FINAL_NUMBERS.md, sections 1 and 10.1.")

# ================================================================ SLIDE 4 Problem statement & motivations
s = S[3]; clean_body(s)
card(s, 0.35, 1.3, 4.5, 1.75, "Problem", [
    "Digitisers are tested on clean scans. For a damaged photo nobody tells the user which numbers can still be trusted.",
    "A wrong heart rate that looks normal is worse than no number."], bsize=13)
card(s, 5.05, 1.3, 4.6, 1.75, "Motivation", [
    "ECG photos are sent by phone and uploaded to explanation services, often outside a clinic.",
    "Plain-language tools need a built-in way to say: do not trust this reading."], bsize=13)
stats = [("47.5%", "wrong heart rate at very low resolution (simulated)"), ("38%", "no output on phone photos of a screen (140 recordings)"),
         ("20 of 60", "own-phone photos with a wrong or missing heart rate"), ("11%", "wrong even on the clean kit page (real captures)")]
for k, (b, t_) in enumerate(stats):
    stat(s, 0.35 + k * 2.4, 3.2, 2.25, 1.4, b, t_)
caption(s, 0.35, 4.62, 7.5, "Sources: FINAL_NUMBERS.md sections 2.1, 3.2 and 3.4.")

# ================================================================ SLIDE 5 Objectives & expected impact
s = S[4]; clean_body(s)
qs = [("Q1", "Which kinds of photo damage make a measurement wrong?"),
      ("Q2", "Can a reliability check warn the user, and from what: the photo or the digitised signal?"),
      ("Q3", "Which measurements, ECG patterns and risk estimates can be shown at all, under rules written before the test?"),
      ("Q4", "Can a demo show only validated information, with risk and findings clearly labelled?")]
for k, (q, t_) in enumerate(qs):
    y = 1.3 + k * 0.82
    c = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(0.35), Inches(y + 0.07), Inches(0.5), Inches(0.5)); c.fill.solid(); c.fill.fore_color.rgb = RED
    c.line.fill.background(); c.shadow.inherit = False
    tf = c.text_frame; tf.margin_left = tf.margin_right = 0; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER; run(p, q, 13, True, WHITE)
    tb, tf2 = textbox(s, 0.95, y, 4.3, 0.65, anchor=MSO_ANCHOR.MIDDLE); run(tf2.paragraphs[0], t_, 13, False, INK)
card(s, 5.5, 1.3, 4.15, 3.3, "Expected impact", None)
bullets(s, 5.6, 1.75, 3.95, 2.8, [
    "Users learn which photo problems break which numbers.",
    "A GREEN, AMBER, RED light flags readings that need a person.",
    "A method where every pass rule is fixed before the result.",
    "A clear list of what an app should refuse to show, such as QT and a mortality risk number.",
    "Honest negative results, so no false claims reach patients."], size=12.5, gap=5)

# ================================================================ SLIDE 6 Related work & limitations
s = S[5]; clean_body(s)
rows = [["Related work", "What it does", "Limitation we address"],
        ["ECG-Image-Kit and the Moody Challenge 2024 [1,2]", "Draws realistic ECG pages; challenge to digitise and classify them", "Scored overall; not which damage breaks which measurement"],
        ["Open-ECG-Digitizer, ECGtizer, Challenge winner [3,4,5]", "Open pipelines that turn an ECG image into signals", "Validated mostly on clean scans; no warning to the user"],
        ["Robustness of digitisers to damage [6]; VLM quality module [7]", "Per-damage robustness study; a vision-language quality check added to the pipeline", "Digitiser changed or no user-facing rule for what to show"],
        ["Signal-quality scoring [8]", "Scores the quality of ECG signals", "Works on signals, not on the digitised output of a photo"],
        ["Abstention and deferral [9,10]", "Lets a system decline to answer; one clinician study found it can raise missed problems", "No claim here that a warning helps patients"]]
table(s, 0.35, 1.3, 9.3, [2.9, 3.3, 3.1], rows, hsize=12, bsize=11, row_h=0.6)

# ================================================================ SLIDE 7 Improvements over existing solutions
s = S[6]; clean_body(s)
rows = [["", "Existing practice", "This project"],
        ["Digitiser", "Modified or newly trained", "One open digitiser, unchanged"],
        ["Evaluation", "Overall accuracy on clean or lightly damaged images", "Each measurement checked against references, rules written first"],
        ["Warning", "Photo-quality score, or none", "Traffic light from the digitised signal (AUC 0.93 vs 0.52 inside the worst damage)"],
        ["Bad photos", "Fed to the digitiser as they are", "Page is found and straightened first: bad readings 14 to 2 of 40 (p = 0.0005)"],
        ["Health claims", "Diagnosis or risk score from the image", "ECG patterns only, never a diagnosis; risk only as a labelled research range"],
        ["Output", "Numbers or free text", "Only validated numbers, fixed wording, a list of what was not checked"]]
table(s, 0.35, 1.25, 9.3, [1.3, 3.2, 4.8], rows, hsize=12, bsize=11.5, row_h=0.5)
caption(s, 0.35, 4.85, 8.0, "AUC values from FINAL_NUMBERS.md sections 2.3 and 3.1. Pass rules are the team's proposal, not guide-approved.")

# ================================================================ SLIDE 8 System architecture
s = S[7]; clean_body(s)
pic(s, os.path.join(FIG, "fig2_1_pipeline.png"), 0.35, 1.2, h=3.45, name="Pipeline diagram")
bullets(s, 5.95, 1.35, 3.7, 3.3, [
    ("Test side: ", "a recording with a known answer is drawn as a page, then damaged or photographed."),
    ("Fix: ", "the page is found and straightened."),
    ("Digitiser: ", "picture to 12 signals."),
    ("Three outputs: ", "measurements, a traffic light, and a comparison with the true signal."),
], size=13, gap=7)

# ================================================================ SLIDE 9 Key components
s = S[8]; clean_body(s)
comp = [("1  Page maker", "ECG-Image-Kit draws a paper-style page from a recording"),
        ("2  Damage and photos", "6 damage types x 5 levels; real captures; own phone photos"),
        ("3  Straightener", "finds the page, flattens it to 2200 x 1700 pixels"),
        ("4  Digitiser", "Open-ECG-Digitizer, unchanged: 12 leads at 1,000 Hz"),
        ("5  Measurements", "heart rate, PR interval, QRS axis (QT and QRS duration not shown)"),
        ("6  Reliability check", "15 features of the digitised signal give GREEN, AMBER or RED"),
        ("7  Findings and risk", "pattern network (heart attack, ST/T, LBBB, AF) and a research-only 5-year risk range"),
        ("8  Demo app", "Gradio: fixed wording, health view, results, dataset gallery")]
for k, (h_, b_) in enumerate(comp):
    card(s, 0.35 + (k % 4) * 2.36, 1.3 + (k // 4) * 1.7, 2.2, 1.55, h_, b_, hsize=14, bsize=12.5)

# ================================================================ SLIDE 10 Algorithms / technologies
s = S[9]; clean_body(s)
card(s, 0.35, 1.3, 5.45, 3.35, "Algorithms and methods", None)
bullets(s, 0.45, 1.72, 5.25, 2.9, [
    ("Digitiser: ", "Open-ECG-Digitizer, unchanged."),
    ("Straightening: ", "Otsu threshold, largest four-corner shape, perspective warp."),
    ("Heart rate: ", "R-peaks on cleaned lead II."),
    ("PR and axis: ", "median beat; axis by least squares on six limb leads."),
    ("Reliability: ", "15 signal features, logistic regression, frozen thresholds 0.2585 and 0.7823."),
    ("Findings: ", "small 1-D CNN (0.5 M parameters), six PTB-XL labels."),
    ("Risk: ", "five-fold CNN plus an age network, averaged; range of plus or minus 10 points."),
    ("Statistics: ", "Wilson 95% intervals, exact McNemar with Holm, Bland-Altman, AUC."),
], size=11.5, gap=3)
card(s, 5.95, 1.3, 3.7, 3.35, "Technologies and tools", None)
bullets(s, 6.05, 1.72, 3.5, 2.9, [
    "Python, PyTorch, scikit-learn, OpenCV",
    "NeuroKit2 for beat detection",
    "ECG-Image-Kit (page drawing)",
    "Gradio demo app",
    "Google Colab GPU for runs",
    "PTB-XL, PTB-XL+ and CODE-15% data",
], size=13, gap=6)

# ================================================================ SLIDE 11 Dataset / Input-Output
s = S[10]; clean_body(s)
rows = [["Data", "What it is", "Size"],
        ["PTB-XL [11]", "10-second 12-lead ECGs; also trains the findings network", "21,799 recordings"],
        ["PTB-XL+ [12]", "Reference values from 12SL and Glasgow", "same recordings"],
        ["Drawn pages", "ECG-Image-Kit pages, 6 damage types", "150 recordings"],
        ["Competition captures [14]", "Real scans and photos, 9 capture types", "1,260 images"],
        ["Own phone photos", "Pages shown on a laptop screen, straight and angled", "100 photos"],
        ["CODE-15%", "Public patients with follow-up, for the risk pilots", "19,048 patients, 2,965 deaths"]]
table(s, 0.35, 1.25, 6.0, [1.6, 2.8, 1.6], rows, hsize=12, bsize=10.5, row_h=0.42)
card(s, 0.35, 4.3, 6.0, 0.55, None, None)
tb, tf = textbox(s, 0.4, 4.32, 5.9, 0.5, anchor=MSO_ANCHOR.MIDDLE)
p = tf.paragraphs[0]; run(p, "Input: ", 12, True, MAROON); run(p, "a photo or scan of a 12-lead ECG page.  ", 12)
run(p, "Output: ", 12, True, MAROON); run(p, "measurements, traffic light, findings, risk range.", 12)
pic(s, os.path.join(EX, "N002_angled.jpg"), 6.6, 1.3, w=3.05, name="Example angled photo")
caption(s, 6.6, 3.7, 3.05, "Example: angled phone photo of a page")

# ================================================================ SLIDE 12 Parameters
s = S[11]; clean_body(s); set_subheading(s, "Parameters Descriptions")
rows = [["Group", "Parameter", "Value"],
        ["Page", "Speed, gain, size", "25 mm/s, 10 mm/mV, 200 dpi, 2200 x 1700 px"],
        ["Damage", "6 types x 5 levels", "worst: blur 21 x 21, rotation 16 deg, JPEG q 3, shrink to 15%, ramp 0.75, fade 0.75"],
        ["Labels", "Wrong / no usable heart rate", "more than 5 bpm off / fewer than 3 beats in lead II"],
        ["Traffic light", "AMBER / RED start", "score 0.2585 / 0.7823 (from simulated training only)"],
        ["Statistics", "Intervals and tests", "Wilson 95%, exact McNemar, Holm, alpha 0.05"],
        ["Measurements", "PR / axis pass rule", "PR: 20 ms typical error; axis: 10 deg, 90% within 30 deg"],
        ["Findings", "Pass rule on photos", "AUROC 0.75 or more, 20 or more positive photos"],
        ["", "Operating point", "specificity 0.97 (set on damaged validation data)"],
        ["Risk", "Range / pass rule", "plus or minus 10 points; calibration slope 0.8 to 1.25"],
        ["All rules", "Fixed before each test", "team proposal, not guide-approved"]]
table(s, 0.35, 1.25, 9.3, [1.5, 2.5, 5.3], rows, hsize=12, bsize=11, row_h=0.34)

# ================================================================ SLIDE 13 Experimental outcomes (3 slides, same heading)
s13 = S[12]; clean_body(s13); set_subheading(s13, "Experimental Outcomes (1/6): which damage breaks heart rate")
pic(s13, os.path.join(FIG, "fig4_1_wrong_by_damage.png"), 0.35, 1.3, w=5.6, name="Wrong HR by damage")
bullets(s13, 6.15, 1.3, 3.5, 3.3, [
    ("Held-out 99 recordings, worst level. ", ""),
    "Low resolution: 47.5% wrong. Blur: 17.2%.",
    "JPEG, brightness, faded grid: 3% or less, same as a clean page (3.0%).",
    "Strong rotation: 0% wrong, but no output for 19% of pages.",
    "Holds with and without reference-uncertain recordings.",
], size=12.5, gap=5)
caption(s13, 0.35, 4.35, 5.6, "Pre-specified claim C1 (supported). FINAL_NUMBERS.md 2.1.")

s13b = duplicate(s13, 12); set_subheading(s13b, "Experimental Outcomes (2/6): traffic light and straightening")
for sh in list(s13b.shapes):
    if sh.name in ("Wrong HR by damage",): sh._element.getparent().remove(sh._element)
# remove copied content boxes (everything except title, subheading, page no, logo)
for sh in list(s13b.shapes):
    if sh.name not in ("TextShape 1", "TextShape 2", "TextShape 3", "Picture 2", "Picture 3", "Picture 4"):
        sh._element.getparent().remove(sh._element)
rows = [["Traffic light, real captures", "Readings", "Wrong"],
        ["GREEN", "917", "2  (0.2%)"], ["AMBER", "204", "14  (6.9%)"], ["RED", "82", "30  (36.6%)"]]
g = table(s13b, 0.35, 1.3, 4.6, [2.2, 1.0, 1.4], rows, hsize=12, bsize=12, row_h=0.4)
for i, col in ((1, GREEN), (2, AMBER), (3, REDL)):
    c = g.table.cell(i, 0); c.fill.solid(); c.fill.fore_color.rgb = col
    for r in c.text_frame.paragraphs[0].runs: r.font.color.rgb = WHITE
bullets(s13b, 0.35, 3.05, 4.7, 1.6, [
    "In 40 new photos no bad reading was GREEN.",
    "Not a guarantee: on printed paper from another phone 2 of 19 GREEN photos were wrong.",
], size=12, gap=4)
rows = [["New photos (40)", "Original", "Straightened"],
        ["Bad readings", "14 / 40", "2 / 40"], ["No usable HR", "4", "0"], ["Wrong HR", "10", "2"],
        ["Angled shots bad", "10 / 20", "1 / 20"]]
table(s13b, 5.3, 1.3, 4.35, [1.9, 1.2, 1.25], rows, hsize=12, bsize=12, row_h=0.4)
card(s13b, 5.3, 3.45, 4.35, 1.15, None, None)
tb, tf = textbox(s13b, 5.35, 3.48, 4.25, 1.1, anchor=MSO_ANCHOR.MIDDLE)
p = tf.paragraphs[0]; run(p, "CONFIRMED: ", 13, True, GREEN); run(p, "exact McNemar p = 0.0005, rule written before the photos existed. One phone, one screen, 20 recordings.", 12)
caption(s13b, 0.35, 4.68, 8.5, "Sources: FINAL_NUMBERS.md sections 3.3 and 4 (confirmation), and the printed-paper note in 00_START_HERE.md.")

KEEP = ("TextShape 1", "TextShape 2", "TextShape 3", "Picture 2", "Picture 3", "Picture 4")


def fresh(after, sub):
    sl = duplicate(s13b, after); set_subheading(sl, sub)
    for sh in list(sl.shapes):
        if sh.name not in KEEP: sh._element.getparent().remove(sh._element)
    return sl


def status_colour(g, col_idx, rows):
    for i, r in enumerate(rows):
        if i == 0: continue
        v = r[col_idx].lower(); c = g.table.cell(i, col_idx)
        col = GREEN if v.startswith(("shown", "meets", "found")) else (REDL if v.startswith(("not shown", "fails", "not met")) else GREY)
        for rr in c.text_frame.paragraphs[0].runs: rr.font.color.rgb = col; rr.font.bold = True


# ---- 3/6 measurements
s13m = fresh(13, "Experimental Outcomes (3/6): which measurements can be shown")
rows = [["Measurement (straightened photos)", "Typical error vs 12SL", "Pre-set rule", "In the app"],
        ["Heart rate", "GREEN wrong 0.2% (2 of 917)", "within 5 bpm", "Shown"],
        ["PR interval", "12.0 ms; 95% within 40 ms", "Meets", "Shown"],
        ["QRS axis", "4.4 degrees; 95% within 30", "Meets", "Shown"],
        ["QT interval", "14.9 ms, bias -16.5 ms; 86% within 40", "Fails", "Not shown"],
        ["QRS duration", "12.9 ms; only 69% within 20 ms", "Fails", "Not shown"]]
g = table(s13m, 0.35, 1.3, 9.3, [2.9, 3.3, 1.5, 1.6], rows, hsize=12, bsize=12, row_h=0.42)
status_colour(g, 3, rows); status_colour(g, 2, rows)
bullets(s13m, 0.35, 3.95, 9.3, 1.0, [
    "PR and axis meet their rules only after straightening. PR is hidden when the beats are irregular (atrial fibrillation).",
    "QT and QRS duration were tried three times on new data and still failed, so the app says \"not measured\".",
], size=12, gap=4)
caption(s13m, 0.35, 4.85, 9.0, "Sources: FINAL_NUMBERS.md 10.6 to 10.9. Rules are the team's proposal, not guide-approved.")

# ---- 4/6 findings
s13f = fresh(14, "Experimental Outcomes (4/6): heart-health findings")
rows = [["ECG pattern (AUROC)", "Drawn pages", "Phone photos", "In the app"],
        ["Heart-attack pattern", "0.91", "0.86", "Shown"],
        ["ST/T change", "0.89", "0.87", "Shown"],
        ["Conduction disturbance", "0.90", "0.88 (screen); 0.42 (printed paper)", "Not shown"],
        ["Hypertrophy", "0.78", "0.64", "Not shown"],
        ["Atrial fibrillation", "0.87", "0.84 on dataset photos", "Dataset only"],
        ["Left bundle branch block", "0.97", "0.83 on dataset photos", "Dataset only"]]
g = table(s13f, 0.35, 1.3, 6.35, [1.95, 1.0, 2.2, 1.2], rows, hsize=11.5, bsize=10.5, row_h=0.42)
status_colour(g, 3, rows)
bullets(s13f, 6.9, 1.3, 2.75, 3.4, [
    "Shown as found or not found, not as a risk.",
    "On photos a miss is 14 to 28 in 100 true patterns; a false alarm 16 to 24 in 100.",
    "Heart-attack percentage: passed on a second try (error 0.040), simulated photos only.",
    "Never a diagnosis.",
], size=11.5, gap=4)
caption(s13f, 0.35, 4.35, 6.3, "Sources: FINAL_NUMBERS.md 11.2, 10.31, 10.38; 'at a glance' figure for printed paper (0.42, 22 photos).")

# ---- 5/6 risk
s13r = fresh(15, "Experimental Outcomes (5/6): risk estimate (research only)")
rows = [["Risk test", "Result", "Verdict"],
        ["1-year death, ECG alone", "AUROC 0.71; age alone 0.80", "Not shown"],
        ["5-year death, ECG + age (sealed test)", "AUROC 0.83; ECG adds +0.013, not significant", "Not shown"],
        ["5-year, five-fold (19,048 patients)", "AUROC 0.811 vs 0.798 for age; calibration slope 0.76", "Research only"],
        ["Age read from the ECG", "error 9.3 years; risk AUROC 0.795", "Research only"],
        ["Range on photos", "holds for 67 to 72% of real photos (target 80%)", "Not met"]]
g = table(s13r, 0.35, 1.3, 6.2, [2.0, 2.9, 1.3], rows, hsize=11.5, bsize=10.5, row_h=0.5)
status_colour(g, 2, rows)
bullets(s13r, 6.75, 1.3, 2.9, 3.4, [
    "No validated risk number is shown.",
    "The ECG adds little beyond age.",
    "A separate research box shows a range of plus or minus 10 points, only for a GREEN straightened photo.",
    "Estimates run high: only people with full follow-up were used.",
], size=11.5, gap=4)
caption(s13r, 0.35, 4.45, 6.2, "Sources: FINAL_NUMBERS.md 10.19, 10.21, 10.32 to 10.36. Same cohort, cross-validated, not an external test.")

# ---- 6/6 user interface
s13c = fresh(16, "Experimental Outcomes (6/6): user interface and what is shown")
pic(s13c, os.path.join(FIG, "fig4_2_demo_output.png"), 0.35, 1.3, w=5.8, name="Demo output")
caption(s13c, 0.35, 3.95, 5.8, "Demo: a straightened photo, GREEN light, plain wording, and what was not checked.")
bullets(s13c, 6.35, 1.3, 3.3, 3.3, [
    ("Shown: ", "heart rate, PR interval, QRS axis, traffic light."),
    ("Found or not found: ", "heart-attack and ST/T patterns."),
    ("Research only: ", "5-year risk range, other patterns."),
    ("Not shown: ", "QT, QRS duration, validated risk."),
    ("Always printed: ", "this is not a guarantee."),
], size=12.5, gap=5)

# ================================================================ SLIDE 14 Summary
s14 = S[13]
body = [x for x in s14.shapes if x.name == "TextShape 2"][0]
body._element.getparent().remove(body._element)
cols = [("Key Findings", [
            "Low resolution and heavy blur break heart rate (47.5%, 17.2%).",
            "Rotation causes missing output, not wrong numbers.",
            "A picture-only warning fails (AUC 0.52 inside a damage level); the digitised signal works (0.93).",
            "GREEN heart rate wrong 0.2% (2 of 917).",
            "Straightening: 14 to 2 of 40 bad (p = 0.0005).",
            "Heart-attack and ST/T patterns found (AUROC 0.86 on photos); no validated risk (ECG adds +0.013 to age)."]),
        ("Limitations", [
            "One phone, one screen, one digitiser.",
            "GREEN is not a guarantee (2 of 19 wrong on printed paper).",
            "Flags 67% of right readings on atrial fibrillation.",
            "QT and QRS duration failed their rules.",
            "Findings tested on dataset pictures and one phone; risk range holds for 67 to 72% of photos.",
            "Pass rules not guide-approved. Not a medical device."]),
        ("Future Directions", [
            "More phones, screens and printed paper.",
            "A better QT and QRS delineation method.",
            "Real-photo tests for LBBB and atrial fibrillation.",
            "A second person rechecks the key numbers.",
            "A clinical study of whether a warning changes what people do.",
            "Pre-set rules for every new claim."])]
for k, (h_, items) in enumerate(cols):
    x = 0.35 + k * 3.15
    card(s14, x, 0.95, 3.0, 3.75, None, None)
    tb, tf = textbox(s14, x + 0.05, 1.0, 2.9, 0.45)
    p = tf.paragraphs[0]; bullet_xml(p); run(p, h_, 18, True, INK)
    bullets(s14, x + 0.05, 1.5, 2.9, 3.15, items, size=11.5, gap=4)

# ================================================================ SLIDE 15 Bibliography
s15 = S[14]
refs = [
    "Shivashankara KK et al. ECG-Image-Kit. Physiol Meas 2024;45:055019.",
    "Reyna MA et al. Digitization and Classification of ECG Images: Moody PhysioNet Challenge 2024. Comput Cardiol 2024;51.",
    "Stenhede N et al. Digitizing paper ECGs at scale (Open-ECG-Digitizer). npj Digit Med 2026;9:145.",
    "Lence A et al. ECGtizer. arXiv:2412.12139.",
    "Krones F et al. Hough transform and deep learning to reconstruct ECG from printouts. Comput Cardiol 2024.",
    "Qasmi MI, Ali Z. How robust are ECG image digitizers to image damage? engrXiv 2026 (preprint).",
    "Li J et al. VLM-in-the-Loop: QA module for ECG digitization. arXiv:2604.00396 (preprint).",
    "Zhou X et al. ECG quality assessment with a generalized deep learning model. Life 2021;11:1013.",
    "Vazhentsev A et al. Uncertainty-aware abstention in medical diagnosis. npj Artif Intell 2026;2:86.",
    "Jabbour S et al. Selective prediction and automation bias. arXiv:2508.07617 (preprint).",
    "Wagner P et al. PTB-XL, a large public ECG dataset. Sci Data 2020;7:154.",
    "Strodthoff N et al. PTB-XL+, an ECG feature dataset. Sci Data 2023;10:279.",
    "Makowski D et al. NeuroKit2. Behav Res Methods 2021;53:1689.",
    "Reyna MA et al. ECG-image-database: paired ECG images and time series. Physiol Meas.",
]
sub = [x for x in s15.shapes if x.name == "Subtitle 2"][0]
tf = sub.text_frame; tf.word_wrap = True
bodyPr = tf._txBody.find(qn("a:bodyPr")); bodyPr.set("numCol", "2"); bodyPr.set("spcCol", str(int(Inches(0.25))))
for i, t_ in enumerate(refs):
    p = tf.paragraphs[0] if i == 0 else tf.add_paragraph(); p.alignment = PP_ALIGN.LEFT; p.space_after = Pt(4)
    pPr = p._p.get_or_add_pPr(); pPr.set("marL", "0"); pPr.set("indent", "0"); etree.SubElement(pPr, qn("a:buNone"))
    run(p, f"[{i + 1}] ", 11, True, MAROON, font=FONT); run(p, t_, 11, False, INK, font=FONT)
sub.left, sub.top, sub.width, sub.height = Inches(0.4), Inches(0.95), Inches(9.2), Inches(3.9)

# ---------------------------------------------------------------- page numbers
for i, sl in enumerate(prs.slides, 1):
    set_page_no(sl, i)
prs.save(OUT)
print("saved", OUT, len(prs.slides), "slides")
