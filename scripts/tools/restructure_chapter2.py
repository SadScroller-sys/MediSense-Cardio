"""Restructure Chapter 2 of the report as a workflow: every step gets a shaded box with Objective, Input, Process, Algorithms and Output;
the sections are put in the order of the data flow (page straightening before the digitizer); a workflow table and an algorithms table are added;
the statistics paragraph becomes its own section; Table A.6 (commands) is added to the appendix. The contents and list of tables are updated by text
(their page numbers must be refreshed afterwards).
No result or number is changed; every fact comes from the report text, docs/reports/METHODS_AND_FORMULAE.md and docs/reports/CODE_MAP.md.
Usage: python -I scripts/tools/restructure_chapter2.py <report.docx>   (the file is edited in place; make a backup first)"""
import copy
import re
import sys
from xml.sax.saxutils import escape

from docx import Document
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.table import _Row
from docx.text.paragraph import Paragraph

PATH = sys.argv[1]
d = Document(PATH)
body = d.element.body
els = list(body)
NS = nsdecls("w")
FONT = '<w:rFonts w:ascii="times new roman" w:eastAsia="times new roman" w:hAnsi="times new roman" w:cs="times new roman"/>'


def txt(e):
    return "".join(t.text or "" for t in e.iter(qn("w:t")))


def settext(p, t):
    runs = p.findall(qn("w:r")) if hasattr(p, "findall") else None
    par = Paragraph(p, None)
    par.runs[0].text = t
    for r in par.runs[1:]:
        r.text = ""


# ------------------------------------------------------------------ locate the old Chapter 2
i144 = next(i for i, e in enumerate(els) if e.tag == qn("w:p") and txt(e).startswith("This chapter describes what was built and how it was tested"))
i_end = next(i for i, e in enumerate(els) if i > i144 and e.tag == qn("w:p") and txt(e).strip() == "CHAPTER 3")
old = els[i144 + 1:i_end]
heads = [i for i, e in enumerate(old) if e.tag == qn("w:p") and re.match(r"^2\.\d+ ", txt(e).strip())]
sections = {}
for k, h in enumerate(heads):
    end = heads[k + 1] if k + 1 < len(heads) else len(old)
    num = re.match(r"^(2\.\d+) ", txt(old[h]).strip()).group(1)
    sections[num] = old[h:end]
assert list(sections) == [f"2.{n}" for n in range(1, 14)], list(sections)
trailing = old[heads[-1]:]  # last section may include the blank paragraph before CHAPTER 3


# ------------------------------------------------------------------ builders
def run(text, bold=False, sz=21):
    b = "<w:b/><w:bCs/>" if bold else ""
    return f'<w:r><w:rPr>{FONT}{b}<w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/></w:rPr><w:t xml:space="preserve">{escape(text)}</w:t></w:r>'


def rich(text, sz=21):
    """'**bold** plain' -> runs"""
    out = ""
    for i, part in enumerate(re.split(r"\*\*", text)):
        if part:
            out += run(part, bold=bool(i % 2), sz=sz)
    return out


def box(objective, inp, process, algos, output):
    lines = [("Objective: ", objective), ("Input: ", inp), ("Process: ", process), ("Algorithms: ", algos), ("Output: ", output)]
    paras = ""
    for lab, t in lines:
        paras += f'<w:p><w:pPr><w:spacing w:before="0" w:after="50" w:line="259" w:lineRule="auto"/><w:jc w:val="left"/></w:pPr>{run(lab, True)}{rich(t)}</w:p>'
    b = '<w:top w:val="single" w:sz="6" w:space="0" w:color="7F7F7F"/><w:left w:val="single" w:sz="6" w:space="0" w:color="7F7F7F"/><w:bottom w:val="single" w:sz="6" w:space="0" w:color="7F7F7F"/><w:right w:val="single" w:sz="6" w:space="0" w:color="7F7F7F"/>'
    xml = (f'<w:tbl {NS}><w:tblPr><w:tblW w:w="5000" w:type="pct"/><w:tblBorders>{b}</w:tblBorders><w:tblLayout w:type="fixed"/>'
           f'<w:tblCellMar><w:top w:w="80" w:type="dxa"/><w:left w:w="140" w:type="dxa"/><w:bottom w:w="60" w:type="dxa"/><w:right w:w="140" w:type="dxa"/></w:tblCellMar></w:tblPr>'
           f'<w:tblGrid><w:gridCol w:w="8600"/></w:tblGrid><w:tr><w:trPr><w:cantSplit/></w:trPr><w:tc><w:tcPr><w:tcW w:w="5000" w:type="pct"/>'
           f'<w:shd w:val="clear" w:color="auto" w:fill="EDEDED"/></w:tcPr>{paras}</w:tc></w:tr></w:tbl>')
    return parse_xml(xml)


def spacer():
    return parse_xml(f'<w:p {NS}><w:pPr><w:spacing w:before="0" w:after="60"/></w:pPr></w:p>')


def make_table(headers, rows, widths, sz=19):
    b = '<w:top w:val="single" w:sz="4" w:space="0" w:color="000000"/><w:left w:val="single" w:sz="4" w:space="0" w:color="000000"/><w:bottom w:val="single" w:sz="4" w:space="0" w:color="000000"/><w:right w:val="single" w:sz="4" w:space="0" w:color="000000"/><w:insideH w:val="single" w:sz="4" w:space="0" w:color="000000"/><w:insideV w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
    grid = "".join(f'<w:gridCol w:w="{w}"/>' for w in widths)

    def cell(w, t, bold, fill=None):
        sh = f'<w:shd w:val="clear" w:color="auto" w:fill="{fill}"/>' if fill else ""
        return (f'<w:tc><w:tcPr><w:tcW w:w="{w}" w:type="dxa"/>{sh}</w:tcPr><w:p><w:pPr><w:spacing w:before="0" w:after="0"/><w:jc w:val="left"/></w:pPr>'
                f'{rich(t, sz) if not bold else run(t, True, sz)}</w:p></w:tc>')

    xml = (f'<w:tbl {NS}><w:tblPr><w:tblW w:w="{sum(widths)}" w:type="dxa"/><w:jc w:val="center"/><w:tblBorders>{b}</w:tblBorders><w:tblLayout w:type="fixed"/>'
           f'<w:tblCellMar><w:top w:w="40" w:type="dxa"/><w:left w:w="80" w:type="dxa"/><w:bottom w:w="40" w:type="dxa"/><w:right w:w="80" w:type="dxa"/></w:tblCellMar></w:tblPr><w:tblGrid>{grid}</w:tblGrid>')
    xml += '<w:tr><w:trPr><w:cantSplit/><w:tblHeader/></w:trPr>' + "".join(cell(w, h, True, "D9D9D9") for w, h in zip(widths, headers)) + "</w:tr>"
    for r in rows:
        xml += "<w:tr><w:trPr><w:cantSplit/></w:trPr>" + "".join(cell(w, c, False) for w, c in zip(widths, r)) + "</w:tr>"
    return parse_xml(xml + "</w:tbl>")


# ------------------------------------------------------------------ heading texts and boxes
NEW = [  # (new number, old number or None, new heading, box)
    ("2.1", "2.1", "Overall Workflow of the Method", None),
    ("2.2", "2.2", "Step 1: Data and Reference Values", dict(
        objective="get real ECGs whose true answer is known.",
        inp="PTB-XL (21,799 ten-second 12-lead ECGs, 100 Hz and 500 Hz versions) and PTB-XL+ (interval values from the commercial algorithms 12SL and Glasgow).",
        process="1) draw a random pool of 500 recordings with a fixed seed; 2) the first 50 form the development set; 3) 100 more from the unused recordings form the held-out set; 4) choose every later test set with another seed, so that no recording is in two test sets; 5) set the reference heart rate and mark recordings that are reference-uncertain (100 Hz and 500 Hz differ by more than 5 bpm) or unreliable (more than 20% of versions without output).",
        algos="**seeded random selection** (seed 42 for the held-out 100).",
        output="lists of recordings: 150 in the damage sweeps, 148 of them reliable.")),
    ("2.3", "2.3", "Step 2: Drawing the Page", dict(
        objective="turn a recording into a paper-style ECG page, so that damage can be added to it.",
        inp="one 10-second, 12-lead recording (100 Hz version).",
        process="1) set the paper scale: 25 mm/s, 10 mm/mV, 200 dpi; 2) convert each sample (t, v) to the pixel position x = t / dt, y = y0 - v / dv; 3) use the standard layout of three rows by four leads plus a long lead II strip; 4) write the page on a 2200 x 1700 px canvas with its label.",
        algos="**ECG-Image-Kit** (one patched copy used for every set).",
        output="a clean page image.")),
    ("2.4", "2.4", "Step 3: Damage and Real Captures", dict(
        objective="measure which kind and amount of damage makes the reading wrong, and check the result on real pictures.",
        inp="the clean page; real captures from the public competition dataset; the team's own phone photographs of pages shown on a laptop screen; printed pages photographed by another person.",
        process="1) apply one damage type at a time at five levels; 2) the first 50 recordings get 31 versions and the new 100 get 13; 3) make 120 simulated phone photographs of 60 sealed pages (tilt, screen edge, vignette, noise, blur, shadow); 4) photograph real pages straight on and from the side at about 30 degrees.",
        algos="**Gaussian blur**, **rotation**, **JPEG compression**, **shrink-and-enlarge (low resolution)**, **left-to-right shadow ramp** and **contrast fade of the grid**.",
        output="damaged or photographed pictures.")),
    ("2.5", "2.8", "Step 4: Page Straightening", dict(
        objective="remove tilt and perspective from a photograph before it is digitized.",
        inp="a phone photograph of a page.",
        process="1) reduce the photo to 800 pixels and smooth it; 2) threshold it; 3) clean it with a morphological close and then an open; 4) take the largest contour that covers at least 12% of the image and reduce it to a four-sided polygon; 5) order the corners; 6) map the four corners to a 2200 x 1700 rectangle; 7) accept the result only if the width-to-height ratio is between 0.9 and 1.8.",
        algos="**Otsu threshold**, **morphological opening and closing**, **contour and polygon approximation**, **perspective transform** (getPerspectiveTransform with cubic interpolation).",
        output="the straightened page, or the original photograph if no page is found.")),
    ("2.6", "2.5", "Step 5: The Digitizer", dict(
        objective="turn the page picture back into a 12-lead signal.",
        inp="the page image (the straightened one when Step 4 accepted it).",
        process="1) a network marks the trace and the grid; 2) the page tilt is estimated; 3) the grid spacing gives the size of a pixel; 4) the trace is read out as a signal; leads that cannot be read are returned as missing values.",
        algos="**Open-ECG-Digitizer**, unchanged (commit 97a15087, published weights): a **U-Net** for trace and grid, a **Hough transform** for the tilt.",
        output="a 1,000 Hz signal in microvolts for 12 leads.")),
    ("2.7", "2.6", "Step 6: Measurements", dict(
        objective="compare the digitized signal with the true signal, using the same code on both.",
        inp="the true and the digitized signal.",
        process="1) clean lead II; 2) find the R-peaks; 3) take the gap RR between neighbouring peaks, the rate is 60 / RR and the heart rate is its mean; 4) call a reading wrong if it is more than 5 bpm from the reference, and unusable if fewer than 3 beats are found; 5) measure PR on a median beat, QT and QTc by the Bazett and Fridericia formulas, and the axis from the six limb leads.",
        algos="**NeuroKit2** (cleaning, R-peak detection, wavelet delineation), **median-beat method** for PR, **least-squares axis**, **Bazett** and **Fridericia** correction.",
        output="heart rate, PR interval and axis for the true and the digitized signal, with the labels wrong or no usable reading.")),
    ("2.8", "2.7", "Step 7: Reliability Check (Traffic Light)", dict(
        objective="warn the user when the digitized signal should not be trusted.",
        inp="the digitized signal only (never the true one).",
        process="1) compute 15 features from the output; 2) fill gaps with the median and standardise; 3) compute the risk score; 4) turn it into a light with two thresholds (AMBER at 0.2585, RED at 0.7823); 5) apply two extra rules: fewer than 3 beats is RED, and a feature outside the range seen in training turns GREEN into AMBER; 6) the model was trained once on simulated damage and then frozen.",
        algos="**logistic regression** on standardised features, **percentile thresholds** from training scores.",
        output="GREEN, AMBER or RED with reasons. GREEN means no warning was raised, not that the heart rate is correct.")),
    ("2.9", "2.9", "Step 8: Validation of Each Measurement", dict(
        objective="decide which measurements may be shown to a user.",
        inp="the value measured on the digitized photograph and the PTB-XL+ reference value.",
        process="1) write the pass rule before the test; 2) develop the method on the development set and freeze it; 3) test once on a sealed set; 4) confirm once on a second set of phone photographs; 5) allow calibration to shift a value (an offset) but never to rescale it.",
        algos="**median-beat PR**, **least-squares axis**, error, bias, slope and tail checks against the reference.",
        output="heart rate, PR interval (straightened photo, steady rhythm) and axis pass; QT, QRS duration and P- and T-wave amplitude do not.")),
    ("2.10", "2.10", "Step 9: Demonstration and Explanation Safeguards", dict(
        objective="show only validated information, in fixed wording.",
        inp="an ECG photograph.",
        process="1) straighten the page (Step 4); 2) digitize (Step 5); 3) compute the traffic light (Step 7); 4) show the heart rate with the light, and PR interval and axis only under their conditions; 5) list the measurements that did not pass as not measured; 6) take every sentence from a fixed list, block forbidden words with a checker, and test all combinations with 19 automated tests.",
        algos="steps 4 to 7 above and a **rule-based wording checker** (no language model).",
        output="the light, the validated values and a plain-words explanation.")),
    ("2.11", "2.12", "Step 10: Further Tests and Models", None),
    ("2.12", None, "Statistical Analysis", dict(
        objective="judge whether differences and warnings are real and not chance.",
        inp="counts of wrong readings, scores and measured errors, grouped by recording.",
        process="1) give each rate a confidence interval; 2) resample whole recordings, not images, for intervals; 3) compare paired yes/no results with an exact test and correct a family of tests; 4) show agreement with bias and limits; 5) judge warning scores by the area under the ROC curve; 6) keep all images of one recording in one fold in cross-validation.",
        algos="**Wilson interval**, **recording-level bootstrap**, **exact McNemar test**, **Holm correction**, **Bland-Altman**, **AUC**, **grouped cross-validation**, **Riley sample-size criterion**.",
        output="the intervals, p-values and verdicts reported in Chapter 4.")),
    ("2.13", "2.11", "Fixed Settings", None),
    ("2.14", "2.13", "Limitations of the Method", None),
]
BOX_PRINTED = dict(
    objective="test whether the results hold for another phone and for real paper.",
    inp="20 printed pages photographed by another person with an unknown phone (set H2: 80 photos, then 40 more).",
    process="1) match each photo to its page by image content; 2) turn a photo that is taller than wide by 90 degrees; 3) straighten, digitize and run the traffic light; 4) the primary set is the 22 straight full-resolution photos, the 52 full-resolution photos and the 66 recompressed copies are reported as separate secondary sets.",
    algos="Steps 4 to 7 unchanged, **matching by image content**, **exact McNemar test**.",
    output="the number of bad readings per set, with and without straightening.")
BOX_NETS = dict(
    objective="test whether ECG patterns and a mortality-risk estimate can be read from photographs and shown safely.",
    inp="PTB-XL (patterns) and CODE-15% (patterns and mortality) for training; the team's digitized pages and photographs only as tests.",
    process="1) train each network once on public data (patterns: PTB-XL folds 1 to 8, fold 9 for calibration, fold 10 as benchmark); 2) remove from training every recording that appears in a digitized or photo set; 3) test once on the benchmark, on digitized drawn pages and on straightened photographs; 4) choose fresh sets only after the rule is logged; 5) apply the pass rules below; 6) risk: a patient-level split, pilot 1 (one year, ECG only), pilot 2 (five years, ECG plus age, sealed test), pilot 3 (five-fold cross-validation), then calibration and a check of the displayed range on pictures.",
    algos="**one-dimensional convolutional networks**, **Platt scaling** (calibration), **five-fold cross-validation**.",
    output="pattern findings shown only where the pass rules were met; no validated risk estimate.")

# ------------------------------------------------------------------ build the new sequence
new = []


def heading_el(old_num, newnum, title):
    if old_num:
        h = sections[old_num][0]
    else:
        h = copy.deepcopy(sections["2.2"][0])
    settext(h, f"{newnum} {title}")
    return h


for newnum, oldnum, title, spec in NEW:
    h = heading_el(oldnum, newnum, title)
    new.append(h)
    rest = list(sections[oldnum][1:]) if oldnum else []
    if oldnum == "2.6":  # the statistics paragraph moves to its own section
        stat = next(e for e in rest if txt(e).startswith("Statistics."))
        rest.remove(stat)
        STAT = stat
    if spec:
        new.append(box(**spec))
        new.append(spacer())
    if newnum == "2.12":
        STAT.getparent().remove(STAT) if STAT.getparent() is not None else None
        rest = [STAT]
    if newnum == "2.11":
        printed, nets, passr = rest[0], rest[1], rest[2]
        new += [box(**BOX_PRINTED), spacer(), printed, box(**BOX_NETS), spacer(), nets, passr]
        continue
    if newnum == "2.1":
        # objective sentence, the overview paragraph, figure, caption, the new workflow table and the algorithms table
        overview, fig, figcap, tabcap, oldtbl, blank = rest
        objective_p = copy.deepcopy(overview)
        settext(objective_p, "Objective of the method. The method has one purpose: to find out how photo damage changes the numbers read from an ECG image, to warn a user when these numbers should not be trusted, and to show only what has passed rules written beforehand. It also tests whether ECG patterns and a mortality-risk estimate can be read from the same photographs and shown safely. The steps below follow the path of the data; each step lists its objective, input, process, algorithms and output.")
        new += [objective_p, overview, fig, figcap]
        settext(tabcap, "Table 2.1 The workflow: input, method, output and objective of each step")
        wf = make_table(["Step", "Input", "Method", "Output", "Objective"], [
            ["1 Data", "PTB-XL recordings (10 s, 12 leads) and PTB-XL+ values", "Seeded random selection; reference heart rate from the same code", "Development, held-out and later test sets", "Real ECGs with a known answer"],
            ["2 Drawing", "One recording", "ECG-Image-Kit, 25 mm/s, 10 mm/mV, 200 dpi", "Clean 2200 x 1700 px page", "Make a paper-style page"],
            ["3 Damage and captures", "Clean page, competition captures, own and printed photos", "Six damage types at five levels", "Damaged or photographed picture", "Measure what damage does"],
            ["4 Straightening", "Phone photograph", "Otsu threshold, largest contour, four corners, perspective transform", "Straightened page", "Remove tilt and perspective"],
            ["5 Digitizer", "Page image", "Open-ECG-Digitizer (U-Net, Hough transform), unchanged", "12-lead signal, 1,000 Hz", "Turn the picture back into a signal"],
            ["6 Measurements", "True and digitized signal", "NeuroKit2 R-peaks; median-beat PR; least-squares axis", "Heart rate, PR, axis; wrong or no reading", "Compare digitized with true"],
            ["7 Reliability check", "Digitized signal only", "15 features, logistic regression, two thresholds", "GREEN, AMBER or RED with reasons", "Warn when not to trust"],
            ["8 Validation", "Photo measurements and PTB-XL+ reference", "Pass rules written first; sealed test, then confirmation", "Which measurements may be shown", "Show only validated numbers"],
            ["9 Demonstration", "An ECG photograph", "Steps 4 to 7, fixed sentences, wording checker", "Light, validated values, plain words", "Safe explanation"],
            ["10 Further tests", "Printed pages; public data (PTB-XL, CODE-15%)", "One-dimensional convolutional networks, each tested once", "Pattern findings; risk estimates (none validated)", "Test patterns and risk"],
        ], [1500, 1650, 2250, 1800, 1400])
        new.append(tabcap)
        new.append(wf)
        new.append(spacer())
        cap2 = copy.deepcopy(tabcap)
        settext(cap2, "Table 2.2 Algorithms used in each step")
        al = make_table(["Step", "Algorithm", "What it does here"], [
            ["2 Drawing", "ECG-Image-Kit plotting", "places each sample on a 25 mm/s, 10 mm/mV grid"],
            ["3 Damage", "Gaussian blur, rotation, JPEG compression, shrink-and-enlarge, shadow ramp, contrast fade", "simulate six kinds of damage at five levels"],
            ["4 Straightening", "Otsu threshold, morphological opening and closing, contour and polygon approximation, perspective transform", "finds the page in a photograph and flattens it"],
            ["5 Digitizer", "U-Net; Hough transform", "finds the trace and the grid; estimates the page tilt"],
            ["6 Measurements", "NeuroKit2 cleaning and R-peak detection; median-beat PR; least-squares axis", "heart rate, PR interval and axis"],
            ["7 Reliability check", "Logistic regression on 15 features; percentile thresholds", "turns the output signal into a light"],
            ["10 Further tests", "One-dimensional convolutional network; Platt scaling", "ECG patterns and risk with a calibrated output"],
            ["Statistics (2.12)", "Wilson interval, bootstrap, exact McNemar test, Holm correction, AUC, Bland-Altman", "judge results"],
        ], [1500, 4300, 2800])
        new.append(cap2)
        new.append(al)
        new.append(spacer())
        continue
    for e in rest:
        t = txt(e).strip()
        if t.startswith("Table 2.2 Pass rules"):
            settext(e, "Table 2.3 Pass rules proposed for each measurement")
        elif t.startswith("Table 2.3 Fixed settings"):
            settext(e, "Table 2.4 Fixed settings")
        new.append(e)

# the very last old element before CHAPTER 3 (a blank paragraph) was part of section 2.13 and stays with it
# remove the old elements and insert the new ones after the chapter intro
anchor = els[i144]
for e in old:
    if e.getparent() is not None:
        e.getparent().remove(e)
for e in new:
    if e.getparent() is not None:
        e.getparent().remove(e)
    anchor.addnext(e)
    anchor = e

# ------------------------------------------------------------------ contents and list of tables
CH2_TOC = {n: (num, f"{title}") for n, (num, _, title, _) in zip(range(14), NEW)}
toc = d.tables[0]
rows2 = [r for r in toc.rows if re.fullmatch(r"2\.\d+", r.cells[1].text.strip())]
assert len(rows2) == 13, len(rows2)
last = rows2[-1]
extra = copy.deepcopy(last._tr)
last._tr.addnext(extra)
rows2 = rows2 + [_Row(extra, toc)]
for r, (num, title) in zip(rows2, CH2_TOC.values()):
    for c, v in ((r.cells[1], num), (r.cells[2], title)):
        par = c.paragraphs[0]
        par.runs[0].text = v
        for x in par.runs[1:]:
            x.text = ""

lot = d.tables[1]
trs = [r for r in lot.rows]
find = lambda no: next(r for r in lot.rows if r.cells[0].text.strip() == no)  # noqa: E731
r23, r22, r21 = find("2.3"), find("2.2"), find("2.1")


def setcell(r, i, v):
    par = r.cells[i].paragraphs[0]
    par.runs[0].text = v
    for x in par.runs[1:]:
        x.text = ""


setcell(r23, 0, "2.4"); setcell(r23, 1, "Fixed settings")
setcell(r22, 0, "2.3"); setcell(r22, 1, "Pass rules proposed for each measurement")
setcell(r21, 1, "The workflow: input, method, output and objective of each step")
newrow = copy.deepcopy(r21._tr)
r21._tr.addnext(newrow)
nr = _Row(newrow, lot)
setcell(nr, 0, "2.2"); setcell(nr, 1, "Algorithms used in each step")

# ------------------------------------------------------------------ appendix: Table A.6, commands
els = list(body)
iF = next(i for i, e in enumerate(els) if e.tag == qn("w:p") and txt(e).strip().startswith("F. Reproducing the Headline Numbers"))
j = iF + 1
while j < len(els) and not (els[j].tag == qn("w:p") and txt(els[j]).strip() in ("CHAPTER 7", "REFERENCES")) and els[j].tag != qn("w:sectPr"):
    j += 1
last_el = els[j - 1]
headF = els[iF]
paraF = els[iF + 1]
hG = copy.deepcopy(headF)
settext(hG, "G. Commands to Run Each Step")
pG = copy.deepcopy(paraF)
settext(pG, "Table A.6 lists the command or the place where each step of Chapter 2 is run. All paths are relative to the project folder. Each one-time test script refuses to run a second time, by design.")
capA6 = copy.deepcopy(next(e for e in els if e.tag == qn("w:p") and txt(e).strip().startswith("Table A.5")))
settext(capA6, "Table A.6 Commands to run each step")
cmds = make_table(["Step", "Command or place", "Code"], [
    ["1 Data", "python -I scripts/analysis/select_extension_100.py", "scripts/analysis/"],
    ["2, 3 Drawing and damage", "runs inside the sweep notebooks (Colab)", "colab/*.ipynb; scripts/quality_proxy/degrade.py"],
    ["4 Straightening", "imported by the demo and the fix notebooks; fix tests: python -I scripts/analysis/section_Q_fixexp.py <folder> and section_Q2_confirm.py <folder>", "scripts/preprocess/page_straighten.py"],
    ["5 Digitizer", "from inside the digitizer folder: python -m src.digitize --config <settings>.yml", "scripts/tools/Open-ECG-Digitizer/"],
    ["6 Measurements and analysis", "python -I scripts/analysis/section_C.py (the other section_*.py scripts run the same way)", "scripts/analysis/"],
    ["7 Traffic light", "python -I safeguard/evaluate_safeguard.py", "safeguard/"],
    ["10 Patterns and risk", "demo\\.venv-gpu\\Scripts\\python.exe -I scripts/analysis/section_FIND2_train.py A (or B); section_RISK3_cv.py for the risk pilot", "scripts/analysis/, demo/health/"],
    ["9 Demonstration", "double-click demo\\run_demo.bat, then open http://127.0.0.1:7860; tests: python -I demo/tests/test_health.py", "demo/"],
    ["Check", "python -I scripts/analysis/final_numbers_recompute.py", "scripts/analysis/"],
], [1700, 4600, 2300])
anchor = last_el
for e in (hG, pG, capA6, cmds, spacer()):
    anchor.addnext(e)
    anchor = e

# list of tables: A.6 and contents row G
rowA5 = find("A.5")
rA6 = copy.deepcopy(rowA5._tr)
rowA5._tr.addnext(rA6)
setcell(_Row(rA6, lot), 0, "A.6"); setcell(_Row(rA6, lot), 1, "Commands to run each step")
rowF = next(r for r in toc.rows if r.cells[1].text.strip() == "F")
rG = copy.deepcopy(rowF._tr)
rowF._tr.addnext(rG)
rr = _Row(rG, toc)
for c, v in ((rr.cells[1], "G"), (rr.cells[2], "Commands to Run Each Step")):
    par = c.paragraphs[0]
    par.runs[0].text = v
    for x in par.runs[1:]:
        x.text = ""

d.save(PATH)
print("saved", PATH)
