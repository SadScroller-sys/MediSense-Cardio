# Journal paper rebuild, 2026-11-14

**New file: `main_v2.tex`** (one file, rebuilt from `results/FINAL_NUMBERS.md` sections 1 to 10.10). The 2026-09-25 scaffold (`main.tex` plus `sections/*.tex`, 50 records, first sweep) is kept unchanged and is out of date.

Same findings and labels (PRE-SPECIFIED / EXPLORATORY / POST HOC) as the IEEE paper (`docs/paper/main_v2.tex`) and the capstone report, with fuller methods, a waveform-quality subsection, a per-measurement validation section and a reproducibility statement. Numbers in FINAL_NUMBERS section 8 are not quoted.

## Upload (Overleaf)
Zip `docs/journal/` (needs `main_v2.tex`, `references.bib`, `figures/fig_pipeline.png`, `figures/fig_wrong_by_damage.png`); New Project, Upload; main document `main_v2.tex`; pdfLaTeX + BibTeX. Upload as a NEW project; do not overwrite the earlier compiled one.

## Checked / not checked
Checked by script: environments and braces balance, all `\citep` keys exist in `references.bib`, both figures exist, no unescaped percent signs. Key numbers read against FINAL_NUMBERS.md. NOT compiled (no LaTeX here): layout, page count, the footnote and the table widths are unverified.

## Still needs the team
Title, authors, funding, ethics and contribution statements (marked TODO); repository link; guide approval of the thresholds; second-person recheck of three numbers; port to IOP `iopart` before submission (optional per IOP).
