# Report plan (written 2026-11-12)

**What the college asks (circular VIT-AP/2026/DoA/FALL26-27/CAP/1, read again 2026-11-12)**
- Report + supporting material (A0 poster, plagiarism report) by **20 Nov 2026**; worth 20 marks. Final review 17-21 Nov (fixed for us: Fri 20 Nov, 10:00-18:00, in person), 40 marks.
- One digital PDF uploaded on VTOP (also to the guide and the School office). The grade is generated only after this.
- The report must contain **a record of all codes, standards and software tools** used (item 16).
- Item 5: projects are expected to have hardware plus software; if not, "significant design aspects with an application to real-world problems". Ours has no new hardware: we say so and show the design aspects (pipeline, safeguard, demo, realistic constraints).
- Item 4: bought / borrowed / submitted elsewhere = malpractice (F grade). Plagiarism report needed. All text original; every borrowed idea cited.
- Panel: Programme Chair, External Examiner, three internal experts, the guide; oral exam. Absence at the viva = re-registration.
- The Programme Chair / HoD shares the final report format separately: **confirm the CSE format** (the sample we have, `Downloads/CAPSTONE_THESIS_Format.docx`, is from the Electronics school).
- Proposal form (blank, `Downloads/Capstone Project Proposal.docx`) lists the outcomes the report should show: (a) maths/science/engineering, (c) design within realistic constraints, (d) multidisciplinary teams, (e) identify and solve problems, (g) communicate, (k) modern tools; plus "Realistic constraints" and "Engineering standards".

**Template structure (sample, TNR 12 pt, 1.5 spacing)**
Title page; Certificate; Acknowledgements; Abstract; Table of contents; List of figures and tables; 1 Introduction (1.1 Objectives, 1.2 Background and literature survey, 1.3 Organisation of the report); 2 System (2.1 Proposed system, 2.2 Working methodology, 2.3 Standards, 2.4 System details: 2.4.1 Software, 2.4.2 Hardware); 3 Cost analysis; 4 Results and discussion; 5 Conclusion and future works; 6 Appendix (all code); 7 References; biodata.

**Where our material goes**

| Report part | What goes in | Source files |
|---|---|---|
| Abstract | problem, what we did, 4 headline results, limits (about 250 words) | FINAL_NUMBERS.md |
| 1 Introduction | why a photographed ECG can give a silently wrong heart rate; objectives = C1, C2, C3, traffic light, straightening fix, demo; literature (digitisers, Challenge, quality assessment, VLM gate) | docs/literature/, section_*_review.md, related_work_table.md |
| 2.1 Proposed system | block diagram: photo -> straighten -> Open-ECG-Digitizer -> heart rate -> traffic light | demo/pipeline.py, safeguard/ |
| 2.2 Working methodology | condensed METHODS_AND_FORMULAE (full version in an appendix) | docs/reports/METHODS_AND_FORMULAE.md |
| 2.3 Standards | ECG paper conventions (25 mm/s, 10 mm/mV), PTB-XL / SCP-ECG labels, CLAIM 2024 checklist, Riley and Collins sample-size rules, AHA QT recommendations; what a medical device would need and we did NOT apply | CLAIMS_REGISTER, Section G |
| 2.4.1 Software | table of tools and versions | demo/.venv-gpu, notebooks |
| 2.4.2 Hardware | phone, laptop (RTX 3050 4 GB), Kaggle GPU; no hardware built | |
| 2.5 Realistic constraints, outcomes a/c/d/e/g/k | health and safety (not a medical device), ethical (public data, no patient data), economic, sustainability; team roles | |
| 3 Cost analysis | all tools free or open source; list resources actually used; printing/poster cost from the team | ask the team |
| 4 Results and discussion | simulated sweeps, real captures, own phone, traffic light, straightening confirmation, negative results, limits, what may and may not be claimed | results/FINAL_NUMBERS.md |
| 5 Conclusion and future work | | |
| Appendix | file list with purpose; code of the core modules; formula list; glossary | |
| References | IEEE numbered | docs/paper/*.bib |

**Order of writing (each section: I write, the user reads and says go-ahead):** 1 Introduction -> 2 System and method -> 4 Results -> 5 Conclusion -> abstract -> 3 Cost -> appendix and references -> front matter. Build as .docx (Word is installed, so the single PDF can be made by Word itself).

**Needed from the team:** guide name; project title; confirm the CSE format; role of each of the four team members; real costs (printing, poster).

---
## Added 2026-11-12: what the files that came with the circular say
- The circular (`Downloads/Circular Capstone FALL 2026-27 Semester.pdf`), the proposal form, the rubrics (`Capstone Project Rubrics.xlsx`) and the thesis format (`CAPSTONE_THESIS_Format.docx`) were all downloaded together on 21 Aug 2026. So **the report format that came with the circular is `CAPSTONE_THESIS_Format.docx`**. No separate CSE format has arrived (user, 2026-11-12). Decision: follow this file exactly; if a CSE format arrives later, only the layout changes.
- Rubric rows that belong to the report and supporting material: **Report in prescribed format** ("has to conform exactly to the format supplied with all relevant information, proof read and ratified by the guide; verified by the Programme Chair and signed by the Dean of the School"), **Poster** (A0), **Plagiarism report**, **Quality of report** (contents neatly placed, graphs/tables, list of contents, legible, good grammar, organisation of data).
- Rubric rows judged in the final review (40): Results (do the outcomes justify a solution), Novelty (how much is new), Objectives met (set in review 1, modified in review 2), Application (real-world use), Presentation (systematic, strong analytical arguments), Standards/Tools (requisite standards followed, skill in the tools). The report and the talk must make each of these visible.
- Consequences: (1) start from the template file itself so the layout is exact; (2) the guide must read and ratify the report before the PDF is made, then the certificate page needs signatures: plan a guide meeting by 17-18 Nov; (3) objectives in Chapter 1 must match the objectives told in reviews 1 and 2 (check the diary PDF and review slides); (4) add a short "Novelty" paragraph and a "Standards and tools" table so those marks can be seen.
