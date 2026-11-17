# How to compile this paper (Overleaf)

No LaTeX distribution is installed on this machine, so the file has been checked
structurally (all `\begin`/`\end` pairs balance, all `\cite{}` keys resolve against
`references.bib`) but **not yet compiled to a PDF**. Do that first, before trusting
layout, figure placement, or page count.

## Steps

1. Go to [overleaf.com](https://www.overleaf.com) and sign in (or create a free account).
2. **New Project → Upload Project**, and upload this whole `docs/paper/` folder as a
   zip — or **New Project → Blank Project**, then upload the three files individually
   (`main.tex`, `references.bib`, and the `figures/` folder with its three PNGs).
3. Overleaf ships `IEEEtran.cls` by default — no template upload needed.
4. Set the compiler to **pdfLaTeX** (Menu → Compiler), and set the main document to
   `main.tex` if it isn't picked automatically.
5. Click **Recompile**. It should build the paper with the abstract, all 7 sections,
   3 figures, and the bibliography (52 references, ~50 actually cited).

## What still needs a human decision before this is submittable

These are marked `[TODO]` directly in `main.tex` — search for that string:

1. **Title** — a working title is filled in from `docs/PLAN.md`'s recommendation;
   confirm it (or pick one of the alternatives PLAN.md lists) before submitting.
2. **Author block** — names, department, institution, city/country, emails are all
   placeholders. Fill in `\author{...}` near the top of `main.tex`.
3. Everything else (Abstract through Conclusion, all citations, both tables, all
   three figures) is filled in from the finished draft sections in `docs/PAPER-*-DRAFT.md`
   — nothing else is a placeholder.

## Where the content came from

- Text: assembled from `docs/PAPER-INTRO-RELATEDWORK-DRAFT.md`,
  `docs/PAPER-METHOD-DRAFT.md`, `docs/PAPER-RESULTS-DRAFT.md`,
  `docs/PAPER-DISCUSSION-LIMITATIONS-DRAFT.md`, `docs/PAPER-ABSTRACT-CONCLUSION-DRAFT.md`.
- Figures: the three real result figures, downloaded from
  `MyDrive/MediSense-Cardio-Study/figures/` (the notebook-generated 300dpi PNGs), not
  the earlier mock/dry-run versions.
- Bibliography: all 52 numbered references transcribed from `docs/REFERENCES.md`'s
  Appendix into BibTeX (`references.bib`); only the ~50 actually cited in the text
  will appear in the compiled bibliography.

## Known open issues carried over from the drafts

- Section III-D states plainly that only the heart-rate tier of the T3 outcome
  measure was computed (no PR/QRS/QT), because digitized signals from the sweep run
  were not retained. This is the paper's largest limitation (Section VI) and is named
  as the top future-work item (Section VII) — it is not hidden or minimized anywhere
  in the text.
- The no-reference quality proxy (originally "Contribution 2") is described as
  proposed future work only, not as a delivered result — do not let editing pull it
  back into the Abstract or Introduction as something already done unless it is
  actually built and evaluated before submission.
- NeuroKit2 is cited by footnote URL, not as a numbered reference (no verified formal
  citation for it existed in `docs/REFERENCES.md`) — add a proper `@misc`/`@article`
  entry to `references.bib` if the venue requires all tools to be numbered citations.
