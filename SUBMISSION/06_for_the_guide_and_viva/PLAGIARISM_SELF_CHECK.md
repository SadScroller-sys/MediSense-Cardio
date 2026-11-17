# Plagiarism self-check (2026-11-16)

**What this is, and what it is not.** This is the team's own overlap check, made with a script we wrote. It is **not** the official plagiarism report. The college asks for an official report from its own tool (Turnitin or the tool the library or the guide uses). The official report must be requested from the guide or the library. This self-check finds and fixes close passages first, so the official result is cleaner.

## 1. What was checked

| Item | Detail |
|---|---|
| Our texts | The capstone report (draft v4: abstract and chapters 1 to 5, appendix and all tables; the reference list is left out) and the IEEE paper (`main_v2.tex`, abstract and body). Citation marks like [57] are removed before comparing. |
| Sources compared against | 53 PDFs of the papers we read (`C:\ECG research\ECG_Papers`, all topic folders), plus the README, changelog and licence of Open-ECG-Digitizer and the text files of ECG-Image-Kit: 66 source texts, 474,000 distinct 8-word runs. |
| Method | Every run of 8 (strict) or 5 (loose) identical words in a row between our text and any source is found. Words are lower-cased; punctuation, numbers formatting and line breaks are ignored. |
| Script | `scripts/tools/plagiarism_self_check.py` (run: `python -I scripts/tools/plagiarism_self_check.py 8`, then `5`). Output: `docs/reports/plagiarism_self_check_runs_N8.csv` and `_N5.csv`. |
| Control | The loose setting (5 words) finds matches, so the checker is working; the strict setting finding none means no long copied passage was present. |

## 2. Results

| Text | Words | Runs of 8 or more identical words | Runs of 5 or more |
|---|---|---|---|
| Report | 12,792 | **0** | 22 runs, 120 words (0.9%) |
| IEEE paper | 5,061 | **0** | 11 runs, 56 words (1.1%) |

**No passage of 8 or more consecutive identical words was found in any source.** The 33 short runs (5 to 7 words) are all of these harmless kinds:
- titles of works we cite ("the George B. Moody PhysioNet Challenge 2024", "algorithm for digitizing paper ECGs at scale");
- standard technical terms ("25 mm/s and 10 mm/mV", "area under the ROC curve", "incomplete right bundle branch block", "bias and limits of agreement", "to the end of the T wave");
- table numbers and values ("0.05 0.10", "value of at least 0");
- two phrases from one cited clinician study that we paraphrase with a citation ("a study of 259 clinicians", "of automation bias overall but").

One sentence was close to its source (12 words in a row, from the sample-size paper cited as [57]: "depends on the number of events, not only on the number of ...") and was **reworded** in the report. The idea is cited; the wording is now ours.

## 3. Citation check
All 61 references in the report are cited in the text, and every cited number has a reference (no missing and no unused references). The paper's 19 citation keys all exist in `references.bib`. The report has one quotation in quote marks: our own working title. Every other text is in the team's own words.

## 4. What this check cannot do (limits)
- It compares only against the 53 papers we have as PDFs. The report cites 61 references, and some of them (and the web pages of the datasets) are not among those PDFs, so they could not be compared. It cannot see other sources or the internet.
- It finds copied wording, not copied ideas or close paraphrase, and it cannot tell whether a short run is properly cited.
- **We did not search the internet with sentences of the report**, to keep the unpublished report private. The official tool is the right place for that.
- It does not check the program code (our code is our own, apart from the open-source tools named in the report with their licences: Open-ECG-Digitizer (commit 97a15087, unchanged), ECG-Image-Kit (patched copy) and the libraries listed in Table 3.1).
- Figures: the figures in the report are made by our own scripts (the pipeline figure, the damage chart and the demonstration screenshot); to our knowledge no figure is copied from a paper or a website. The team should confirm this.

## 5. Expect these in the official report (so they are not a surprise)
- **The reference list and the titles in it** will be matched; ask the tool to exclude references and quotes if it allows.
- **Standard terms and method names** (PTB-XL, PTB-XL+, CLAIM checklist, 12SL, "25 mm/s", Open-ECG-Digitizer).
- **The paper.** About 35% of the paper's words also appear in the report (checked: 35.3% in runs of 8 or more words), because both describe the same project by the same authors. If the official check also contains the paper, or if the paper is later published, a similarity report will show this overlap. **Submit the report PDF alone** to the college check, and tell the guide that the paper is the same work in short form. When the paper is submitted to a venue, say that the report is the long version.
- **The team's other documents** in the project (plans, notes) are not part of the report and are not submitted.

## 6. What the team must do
1. Ask the guide or the library how to get the official report (Turnitin or the college's tool) and what the maximum similarity is. The circular we have does not give a number; confirm it.
2. Give the tool the final **PDF** of the report (not the draft files), with the title page, but ask to exclude the reference list and quoted text if the tool has the option.
3. Save the official report PDF next to the final report and name it clearly (for example `CAPSTONE_REPORT_plagiarism_report.pdf`). Show this self-check to the guide if asked.
4. If the official report flags a passage, send it to us; we reword it and rerun this script, then submit again.
5. A signed declaration of originality, if the college asks for one, must come from the team members themselves.

*Made by `scripts/tools/plagiarism_self_check.py`; counts and files are reproducible. Not a substitute for the official tool.*
