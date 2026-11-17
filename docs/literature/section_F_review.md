# Section F: over-trust in AI output (2 papers), review of 2026-11-04

Depth of reading: "People over trust AI-generated medical responses" (arXiv 2408.15266): methods, experiments 1 and 2,
statistics, discussion and limitations (targeted full-section read). ReLay (arXiv 2605.00468): abstract, study design,
results summary, limitations; the 50-page appendix and the model comparisons were not read.
Both papers are about language-model text, not ECG or images. They are loose, motivational support only.

## Paper by paper

### 1. People over trust AI-generated medical responses (arXiv 2408.15266)
- Data: medical questions and doctor answers from HealthTap; GPT-3 answers to the same questions. Four practising physicians
  rated 150 AI answers: 56% High Accuracy, 44% Low Accuracy.
- Experiment 1 (98 participants kept after screening): could non-experts tell whether an answer was written by a doctor or
  by AI? Accuracy was about 50% for doctor answers (50%), High-Accuracy AI (53%) and Low-Accuracy AI (50%); not different
  across types (p = 0.65). Confidence in the guess was high anyway, and not different when guesses were right or wrong.
- Experiment 2 (96 participants): participants rated understanding, validity, trustworthiness and completeness, and
  how likely they would be to follow the advice.
  - High-Accuracy AI answers were rated more valid (0.95 vs 0.81), trustworthy (4.26 vs 3.85) and complete (4.03 vs 3.55)
    than the doctors' answers.
  - Low-Accuracy AI answers were rated about the same as the doctors' answers on those scales.
  - Willingness to follow the advice did not differ significantly between the three types.
- Authors' conclusion: wrong AI answers can look as convincing as right ones, a danger if used without expert oversight.
- Limits they state: GPT-3 (older model), online participants may not represent the public, answers were text only.
  Also: only 100 participants per experiment, four physician raters, no real decisions or outcomes.

### 2. ReLay, COLM 2026 (arXiv 2605.00468)
- A dataset of 300 participant and plain-language-summary pairs from 50 lay readers (recruited through Prolific; 397
  recruited, 128 met eligibility, 50 completed all stages), comparing expert-written plain-language summaries of research
  with LLM-personalised ones.
- Findings: the interactive, personalised summaries gave higher comprehension and perceived quality, but also more risk of
  hallucination and bias reinforcement than the non-personalised ones.
- Relevance to us: very little. It is about summarising research for lay readers.

## What Section F means for the project
1. The one idea worth using: confident, wrong output is often accepted by lay people (paper 1). That supports why a
   digitiser that returns a clean-looking but wrong number is a safety issue, and why we measure "false reassurance".
2. It is indirect. These studies are about text answers from a language model, not a patient looking at a digitised ECG
   result. They do not show how people react to a wrong heart rate or QTc. Do not present them as evidence about our system.
3. Cite paper 1 in one sentence of motivation at most. ReLay is better left out.

## Questions a guide could ask
- "Do you have evidence people over-trust a wrong digitised ECG?" No direct evidence. The nearest is the text-answer study
  and, for gates, the clinician study in Section E. A user study with our outputs would be needed.
- "Why is this literature in your review?" To motivate the false-reassurance definition, nothing more.

## Cautions
- GPT-3 era, small samples, online crowd workers.
- ReLay appendix and model results were not read.
