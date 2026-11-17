"""A0 poster (841 x 1189 mm, portrait) for the capstone review as an editable PowerPoint file. All numbers are copied from results/FINAL_NUMBERS.md (sections 1 to 10.26). Output: docs/reports/MediSense_Cardio_A0_poster.pptx
Export to PDF and a preview PNG with scripts/tools/export_pptx.ps1. Usage: python -I scripts/tools/make_poster.py"""
import os

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
FIG = ROOT + "/docs/reports/figures/"
OUT = ROOT + "/docs/reports/MediSense_Cardio_A0_poster.pptx"
NAVY, BLUE, INK, GREY, PASS, FAIL, CARD, EDGE = (RGBColor(0x12, 0x35, 0x5B), RGBColor(0x1D, 0x4E, 0x89), RGBColor(0x11, 0x18, 0x27), RGBColor(0x4B, 0x55, 0x63), RGBColor(0x1B, 0x7F, 0x3B),
                                                 RGBColor(0xB4, 0x23, 0x18), RGBColor(0xF5, 0xF7, 0xFA), RGBColor(0xD0, 0xD7, 0xDE))
WHITE = RGBColor(255, 255, 255)
FONT = "Calibri"
W_IN, H_IN = 33.11, 46.81                       # A0 portrait
prs = Presentation()
prs.slide_width, prs.slide_height = Inches(W_IN), Inches(H_IN)
slide = prs.slides.add_slide(prs.slide_layouts[6])


def box(x, y, w, h, fill=None, line=None, shape=MSO_SHAPE.RECTANGLE):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    s.shadow.inherit = False
    if fill is None:
        s.fill.background()
    else:
        s.fill.solid()
        s.fill.fore_color.rgb = fill
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line
        s.line.width = Pt(1.5)
    return s


def text(x, y, w, h, paras, anchor=MSO_ANCHOR.TOP, margin=0.15):
    """paras: list of (text, size_pt, bold, colour, align, space_after_pt) or list of runs [(text, size, bold, colour)]."""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    for m in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
        setattr(tf, m, Inches(margin))
    first = True
    for p in paras:
        para = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        runs = p[0] if isinstance(p[0], list) else [(p[0], p[1], p[2], p[3])]
        align = p[4] if len(p) > 4 else PP_ALIGN.LEFT
        para.alignment = align
        para.space_after = Pt(p[5] if len(p) > 5 else 6)
        for t, size, bold, col in runs:
            r = para.add_run()
            r.text = t
            r.font.name = FONT
            r.font.size = Pt(size)
            r.font.bold = bold
            r.font.color.rgb = col
    return tb


def card(x, y, w, h, title, number):
    box(x, y, w, h, fill=CARD, line=EDGE)
    box(x, y, w, 1.35, fill=BLUE)
    text(x + 0.2, y, w - 0.4, 1.35, [([(f"{number}  ", 44, True, RGBColor(0x9E, 0xC5, 0xFE)), (title, 44, True, WHITE)],)], anchor=MSO_ANCHOR.MIDDLE)


def bullets(items, size=27, col=INK, after=9):
    return [([("•  ", size, True, BLUE), (t, size, False, col)],) + (PP_ALIGN.LEFT, after) for t in items]


def picture(path, x, y, w=None, h=None):
    return slide.shapes.add_picture(path, Inches(x), Inches(y), width=Inches(w) if w else None, height=Inches(h) if h else None)


M = 1.0
CW = W_IN - 2 * M
GAP = 0.7
COL = (CW - 2 * GAP) / 3                         # width of one of three columns

# ------------------------------------------------------------------ header
from PIL import Image  # noqa: E402

demo = Image.open(FIG + "fig4_2_demo_output.png")
demo.crop((1000, 30, 1900, 900)).save(FIG + "fig_demo_crop.png")          # the readable right half of the demo screenshot (light and plain-words text)
box(0, 0, W_IN, 5.8, fill=NAVY)
text(M, 0.4, 22.5, 3.0, [("MediSense-Cardio: can the numbers read from a photo of an ECG be trusted?", 66, True, WHITE, PP_ALIGN.LEFT, 0)])
text(M, 3.5, 22.5, 2.2, [("From Paper to Patient: Quantifying and Mitigating Digitization-Induced False Reassurance in Automated ECG Explanation", 30, False, RGBColor(0xC9, 0xD8, 0xEA), PP_ALIGN.LEFT, 6),
                         ("School of Computer Science and Engineering (SCOPE), VIT-AP University, Amaravati  |  Capstone Project, B.Tech CSE, November 2026", 25, False, RGBColor(0xC9, 0xD8, 0xEA), PP_ALIGN.LEFT, 0)])
text(24.0, 0.45, 8.3, 5.0, [("Team", 28, True, RGBColor(0x9E, 0xC5, 0xFE), PP_ALIGN.LEFT, 4),
                            ("Matcha Karthik (23BCE9569)", 28, False, WHITE, PP_ALIGN.LEFT, 2), ("Reddi Navya (23BCE9587)", 28, False, WHITE, PP_ALIGN.LEFT, 2),
                            ("Nihar Sai Adithya (23BCE7567)", 28, False, WHITE, PP_ALIGN.LEFT, 2), ("Thanush Naidu (23BCE20244)", 28, False, WHITE, PP_ALIGN.LEFT, 10),
                            ("Guide", 28, True, RGBColor(0x9E, 0xC5, 0xFE), PP_ALIGN.LEFT, 4), ("Dr. Tarun Narayan Shankar", 28, False, WHITE, PP_ALIGN.LEFT, 0)])

# ------------------------------------------------------------------ row 1: problem, what we did, how we kept it honest
Y1, H1 = 6.4, 8.3
x2, x3 = M + COL + GAP, M + 2 * (COL + GAP)
card(M, Y1, COL, H1, "The problem", "1")
text(M + 0.2, Y1 + 1.5, COL - 0.4, H1 - 1.6, [
    ("Many ECGs exist only as paper or a phone photo. A program turns the photo back into a signal and measures it. A bad photo can give a wrong heart rate that still looks normal, and a wrong number that looks fine is worse than no number.", 31, False, INK, PP_ALIGN.LEFT, 12),
    ([("We asked:", 31, True, BLUE)], PP_ALIGN.LEFT, 4),
] + bullets(["Which photo damage breaks the numbers?", "Can we warn the user, and from what?", "Which numbers are safe to show?"], size=31, after=6))
card(x2, Y1, COL, H1, "What we did", "2")
text(x2 + 0.2, Y1 + 1.5, COL - 0.4, H1 - 1.6, bullets([
    "Drew ECG pages from public PTB-XL recordings with known answers.",
    "Damaged them 6 ways; photographed screen and printed pages.",
    "Straightened each photo; read it with an open-source digitizer.",
    "Measured heart rate, PR and axis; made a traffic light.",
    "Checked every measure against hospital software.",
    "Trained networks on public data for patterns and risk."], size=29, after=8))
card(x3, Y1, COL, H1, "How we kept it honest", "3")
text(x3 + 0.2, Y1 + 1.5, COL - 0.4, H1 - 1.6, bullets([
    "Every pass rule was written before its result.",
    "Each test was run once; failures are reported.",
    "Fresh, sealed recordings for confirmation.",
    "No model was taught from our own photos.",
    "Results are labelled pre-specified, exploratory or post hoc.",
    "Thresholds are our proposal, not yet approved by the guide."], size=30, after=9))

# ------------------------------------------------------------------ strip of three numbers
YC, HC = Y1 + H1 + 0.55, 4.1
calls = [("0.2%", PASS, "of GREEN heart rates were wrong on 917 real captures. On printed paper from another phone: 2 of 19, so GREEN is not a guarantee."),
         ("14 → 2", PASS, "bad readings among 40 new photos after straightening the page (p = 0.0005). Also 31 → 15 on 66 printed-paper photos."),
         ("0", FAIL, "risk numbers shown. Two honest tries at a risk from the ECG failed our rules (AUROC 0.71 and 0.83; age alone 0.80 and 0.82).")]
for i, (big, col, small) in enumerate(calls):
    xx = M + i * (COL + GAP)
    box(xx, YC, COL, HC, fill=CARD, line=EDGE)
    box(xx, YC, 0.35, HC, fill=col)
    text(xx + 0.5, YC + 0.05, COL - 0.65, 1.9, [(big, 96, True, col, PP_ALIGN.LEFT, 0)])
    text(xx + 0.5, YC + 1.85, COL - 0.65, HC - 1.9, [(small, 28, False, INK, PP_ALIGN.LEFT, 0)])

# ------------------------------------------------------------------ results at a glance (left) + demo (right)
Y2 = YC + HC + 0.55
FW = 20.6
FH = FW * 1264 / 1878
H2 = FH + 1.9
box(M, Y2, FW + 0.4, H2, fill=CARD, line=EDGE)
box(M, Y2, FW + 0.4, 1.35, fill=BLUE)
text(M + 0.2, Y2, FW, 1.35, [([("4  ", 44, True, RGBColor(0x9E, 0xC5, 0xFE)), ("Results at a glance: what we found, and what we refuse to show", 44, True, WHITE)],)], anchor=MSO_ANCHOR.MIDDLE)
picture(FIG + "fig_results_at_a_glance_hires.png", M + 0.2, Y2 + 1.55, w=FW)
XR = M + FW + 0.4 + GAP
WR = W_IN - M - XR
card(XR, Y2, WR, H2, "The demo", "5")
picture(FIG + "fig_demo_crop.png", XR + 0.2, Y2 + 1.55, w=WR - 0.4)
dh = (WR - 0.4) * 870 / 900
text(XR + 0.2, Y2 + 1.55 + dh + 0.15, WR - 0.4, H2 - (1.55 + dh + 0.25), bullets([
    "Photo in; traffic light, heart rate and tested measures out, in fixed, checked wording.",
    "Two patterns shown as found or not found, never as a diagnosis or risk.",
    "Upright phone photos are turned automatically."], size=30, after=9))

# ------------------------------------------------------------------ row 4: networks, not shown and limits
Y3 = Y2 + H2 + 0.55
H3 = H_IN - 3.0 - 0.5 - Y3
HW = (CW - GAP) / 2
card(M, Y3, HW, H3, "Networks A and B (public data)", "6")
tbl_rows = [("Label (network B)", "AUROC"), ("Left bundle branch block", "0.995"), ("Fast heart rate", "0.992"), ("Slow heart rate", "0.990"), ("Right bundle branch block", "0.989"), ("Atrial fibrillation", "0.980"), ("First-degree AV block", "0.978")]
TW = 8.3
text(M + 0.2, Y3 + 1.4, HW - 0.4, 0.95, [("Tested once on 26,346 held-out exams. Network A: 16 PTB-XL codes, AUROC 0.74 to 0.998.", 27, False, INK, PP_ALIGN.LEFT, 0)], margin=0.1)
RH = 0.62
gt = slide.shapes.add_table(len(tbl_rows), 2, Inches(M + 0.3), Inches(Y3 + 2.55), Inches(TW), Inches(RH * len(tbl_rows))).table
gt.columns[0].width, gt.columns[1].width = Inches(TW - 1.9), Inches(1.9)
for r, (a, b) in enumerate(tbl_rows):
    gt.rows[r].height = Inches(RH)
    for c, v in enumerate((a, b)):
        cell = gt.cell(r, c)
        cell.text = v
        cell.fill.solid()
        cell.fill.fore_color.rgb = BLUE if r == 0 else (WHITE if r % 2 else CARD)
        cell.margin_top = cell.margin_bottom = Inches(0.04)
        for p in cell.text_frame.paragraphs:
            p.alignment = PP_ALIGN.RIGHT if c == 1 else PP_ALIGN.LEFT
            for run in p.runs:
                run.font.size = Pt(24)
                run.font.name = FONT
                run.font.bold = (r == 0)
                run.font.color.rgb = WHITE if r == 0 else INK
text(M + 0.3 + TW + 0.3, Y3 + 2.55, HW - TW - 1.1, H3 - 2.5, bullets([
    "Too few positive phone photos to prove them: shown only as a collapsed “research only” hint.",
    "Seven patterns together, at strict thresholds, flag 2 in 10 clean pages and 3 in 10 clean phone photos, and miss about half of some true patterns."], size=27, after=10), margin=0.05)
x4 = M + HW + GAP
card(x4, Y3, HW, H3, "Not shown, and limits", "7")
text(x4 + 0.2, Y3 + 1.5, HW / 2 - 0.3, H3 - 1.6, [([("Not shown (failed our rules):", 29, True, FAIL)], PP_ALIGN.LEFT, 6)] + bullets([
    "QT, QRS duration, P and T amplitude: bias and slope checks.", "Conduction pattern on printed paper (AUROC 0.42).", "Any risk number or graph."], size=27, after=8), margin=0.1)
text(x4 + HW / 2 + 0.1, Y3 + 1.5, HW / 2 - 0.3, H3 - 1.6, [([("Limits:", 29, True, BLUE)], PP_ALIGN.LEFT, 6)] + bullets([
    "One digitizer, two phones, mostly screen photos.", "Few positive photos per pattern.", "Reference values are hospital software, not experts.", "Rules not yet approved by the guide."], size=27, after=8), margin=0.1)

# ------------------------------------------------------------------ footer
YF = H_IN - 3.0
box(0, YF, W_IN, 3.0, fill=NAVY)
text(M, YF + 0.2, 21.6, 3.2, [
    ("Conclusion: the numbers read from a photo can be trusted only after the digitized signal is checked. Straighten the page, warn with a traffic light, and show only what passed its test.", 28, True, WHITE, PP_ALIGN.LEFT, 6),
    ("Research prototype for a university project. Not a medical device. Do not use it to make decisions about anyone's health.", 24, False, RGBColor(0xC9, 0xD8, 0xEA), PP_ALIGN.LEFT, 0)])
text(23.0, YF + 0.2, W_IN - 23.0 - M, 3.2, [
    ("Data: PTB-XL, PTB-XL+, CODE-15% (open). Tools: Open-ECG-Digitizer, ECG-Image-Kit, NeuroKit2, PyTorch, Gradio.", 22, False, RGBColor(0xC9, 0xD8, 0xEA), PP_ALIGN.LEFT, 6),
    ("Details: capstone report, results/FINAL_NUMBERS.md, demo in demo/.", 22, False, RGBColor(0xC9, 0xD8, 0xEA), PP_ALIGN.LEFT, 0)])
prs.save(OUT)
print("saved", OUT, "| row 4 height", round(H3, 1), "| band 2 ends at", round(Y2 + H2, 1), "of", H_IN)
