# Section D: no-reference image quality (2 papers), review of 2026-11-04

Depth of reading: DocIQ read in full (4 pages of content). Text-line DIQA paper (arXiv 1906.01907): introduction,
dataset and label construction, benchmarks, results tables and conclusion by targeted search; the network detail not read.
Neither paper is about ECG.

## Paper by paper

### 1. DocIQ, arXiv 2509.17012 (2025): document image quality assessment (DIQA)
- Dataset DIQA-5000: 500 real phone captures of printed documents (100 each of five distortions: shadow, occlusion,
  blur, creases, moire), each processed through random combinations of enhancement steps into 10 versions = 5,000 images.
  23 experienced raters, 15 ratings per image on three dimensions (overall quality, sharpness, colour fidelity), cleaned
  with ITU-R BT.500.
- Model: ResNet50 backbone with layout masks, multi-scale feature fusion, one regression head per quality dimension.
- Targets: human mean opinion scores (DIQA-5000) or OCR accuracy (SmartDoc-QA, 2,130 phone-captured documents).
- Results: SRCC 0.8832 (overall), 0.9086 for character accuracy, 0.8989 for word accuracy; beats six general-purpose
  no-reference methods. 80/20 train/test split.
- Stated gap: older "handcrafted" document-quality methods (gradient magnitude, directional sharpness) "often fail to
  generalize to complex, real-world distortions".
- Things to note: the paper does not say whether its 80/20 split keeps the 10 versions of one capture together; if not,
  the numbers could be inflated by the same leakage we avoided by holding out whole recordings.

### 2. Towards Document Image Quality Assessment: a text line based framework, arXiv 1906.01907
- Framework: detect text lines, score each line with a CNN, combine into a page score; trained on 52,094 synthesised
  text-line images whose quality label is computed from the synthetic distortion with a piecewise function.
- Evaluated on two benchmarks (SmartDoc-QA and DocImg-QA) where ground truth is OCR recognition accuracy, averaged over
  several OCR engines so that the quality label does not depend on one engine.
- Results: LCC / SROCC of about 74 / 76% on SmartDoc-QA and 91 / 87% on DocImg-QA for the best variant, above the earlier
  method it compares with (about 63 / 63% on SmartDoc-QA).
- Motivation stated: assess documents uploaded online and reject those of low quality before they reach OCR.

## What Section D shows
1. A gate that rejects bad uploads before the downstream tool runs is an established idea in document processing
   (reject low-quality images before OCR). Our "photo gate" has precedent there, even though nobody has done it for ECG.
2. The benchmarks use the downstream tool's accuracy as the quality label (OCR accuracy), the same idea as ours (the
   digitiser's error is the label). The text-line paper averages over several OCR engines to avoid learning one
   engine's quirks.
3. Both approaches use layout or text-region awareness: quality is judged where the content is, not over the whole page.
4. Both train on thousands of images and report correlations of 0.75 to 0.9 against a clean quality label.

## Compared with our detector
| | Section D papers | Our detector |
|---|---|---|
| Features | learned from pixels (CNN), layout-aware | five hand-made scores: blur (Laplacian variance), skew (line angle), resolution (high-frequency ratio), contrast, JPEG blockiness |
| Training data | 2,130 to 52,094 images | 1,519 tests from 49 recordings (31 versions of each recording) |
| Label | human opinion or OCR accuracy | HR or interval wrong by a fixed tolerance, or unreadable |
| Downstream tools in the label | several OCR engines (1906) | one digitiser |
| Split | 80/20, grouping not stated (DocIQ) | whole recordings held out |
| Result | correlation 0.75 to 0.91 | held-out AUC 0.607 (primary target); Spearman 0.26 to 0.31 for the best single scores vs QRS error |

Honest reading:
- Our hand-made scores are the kind the DocIQ authors say generalise poorly, and our own unseen-damage result agrees.
- The comparison in correlation numbers is not like for like: their label is a quality score for the whole image; ours
  is the error of a clinical measurement, which also depends on the recording (premature beats, noise bursts, a
  pacemaker), as Section B showed.
- A fairer, achievable improvement for us: use the digitiser's own output as part of the gate (number of unreadable
  leads, layout-match confidence) in addition to photo scores. That is what VLM-in-the-Loop does after digitising.

## Questions a guide could ask
- "Why hand-made scores instead of a trained quality model?" Small data (49 recordings) and a wish for interpretable
  scores; the cost is poor generalisation, which our unseen-damage test shows.
- "Does your gate depend on one digitiser?" Yes. The text-line paper averages over several OCR engines for that reason;
  we test one digitiser.
- "Is there a fair comparison with a standard no-reference quality score?" Not done. Computing BRISQUE or NIQE-style
  scores on our 1,550 images and testing them against the same target would be a quick, honest baseline. (These are
  standard methods that I know of, but they are not in the papers we read.)

## Cautions
- DocIQ is a 2025 preprint; treat its numbers as reported, not verified.
- I did not read the text-line paper's network design or ablations.
