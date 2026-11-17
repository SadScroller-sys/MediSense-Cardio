# IEEE paper rebuild, 2026-11-14

**New file: `main_v2.tex`** (rebuilt from `results/FINAL_NUMBERS.md` sections 1 to 10.10). `main.tex` (the September draft: 50 records, first sweep only) is kept unchanged and is out of date.

## What the new paper says
Same story as the capstone report: held-out damage sweep (resolution and blur only), picture-only warning fails, traffic light from the digitized signal, straightening fix confirmed (14 to 2 of 40, p = 0.0005), per-measurement validation (HR, PR, axis pass for straightened photos; QT, QRS duration, P and T amplitude do not), demo with fixed wording. Labels PRE-SPECIFIED / EXPLORATORY / POST HOC are kept. Numbers in FINAL_NUMBERS section 8 are not quoted.

## How to upload (Overleaf)
1. Zip the `docs/paper/` folder (needs `main_v2.tex`, `references.bib`, `figures/fig_pipeline.png`, `figures/fig_wrong_by_damage.png`).
2. Overleaf: New Project, Upload Project; Menu: Main document = `main_v2.tex`, compiler pdfLaTeX; Recompile.
3. Do not overwrite the project that holds the older corrected paper; upload as a new project.

## Checked and not checked
- Checked by script (`scratchpad/check_tex.py`, same checks as before): environments balance, braces balance, all 19 `\cite` keys exist in `references.bib`, both figure files exist, no unescaped percent signs.
- Spot-checked against FINAL_NUMBERS.md by reading (abstract, Tables 2 to 5, validation paragraph).
- **NOT compiled** (no LaTeX here): layout, page count (IEEE conference limit is usually 6 pages; this will probably run longer, so it may need trimming) and the `\footnote` are unverified.

## Still needs the team
- Title (working), author block, affiliations, funding line (placeholders marked TODO).
- The thresholds are the assistant's proposal, not approved by the guide; the paper says so.
- Second-person recheck of 3 numbers (47/99, 14 to 2 of 40, 2/917).
- The journal paper (`docs/journal/`) is still the older version and has NOT been rebuilt.


# Update 2026-11-16: new results added to `main_v2.tex` (IEEEtran, generic conference class; venue and title still open)
- Added (from FINAL_NUMBERS 10.11 to 10.20 and 11): method paragraph "Further tests and models"; results subsections "Printed paper, another phone", "A network for QRS duration and QT", "ECG-pattern findings" (+ Table 6), "A mortality-risk pilot (negative result)"; abstract, contribution 6, demonstration, discussion, limitations, conclusion updated.
- **Risk pilot 2 (5-year, ECG + age, sealed new test) is NOT in the paper yet**: there is a `% TODO` comment in the risk subsection; add its result (pass or fail) when `results/risk_pilot2/SECTION_RISK2_h5.md` exists.
- Upload: `docs/paper/medisense-cardio-paper-v2.zip` (new Overleaf project, main document `main_v2.tex`, pdfLaTeX).
- Checked by script `scripts/tools/check_tex.py`: environments and braces balance, 19 of 19 cite keys exist, all refs have labels, figure files exist, no bare percent signs. NOT compiled: page count (IEEE conference limit is usually 6 pages; the paper has about 4,000 words plus 6 tables and 2 figures, so it will probably need trimming) and layout are unverified.
- Numbers were typed from FINAL_NUMBERS.md by hand: the second-person check should include the new ones (3 of 22 to 2 of 22; 31 to 15 of 66, p = 0.0004; risk AUROC 0.713 against age 0.799).
