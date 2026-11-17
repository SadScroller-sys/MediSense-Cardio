# MediSense-Cardio — Plan Review & Corrected Roadmap (Technical Version)

*Formal wording, with sources. For your teacher, your slides, and your paper. See [PLAN-simple.md](PLAN-simple.md) for the plain-English version.*

## Context

**MediSense-Cardio** (paper title) / **MediSense AI** (product brand): an ECG digitization → feature extraction →
bounded plain-language explanation pipeline, with an enforced non-diagnostic safety boundary.

This document is both a critique of the original project guide and a corrected roadmap.

**Scope decision (2026-07-26):** the 15–20 participant comprehension study is **deferred**. Priority is a working
end-to-end system; the study is revisited later. See [Deferred](#the-deferred-study) for what that costs and the
cheap hedge that keeps the door open.

**Research contribution (2026-07-26):** the novelty claim moves from "we combined existing components" — which a
literature check shows is partly occupied — to **measuring how digitization error propagates into what a patient
is told**. See [Part 2 — The Research Contribution](#part-2--the-research-contribution). This is provable with
PTB-XL alone, needs no human participants, and reuses the pipeline you were already building.

**Three facts that set the urgency:**
- Project start: **2026-07-26**. Week 1 is `Jul 24–31`.
- Review 1 is **2026-08-18**.

The guide is well above average: the V1/V2+ split is disciplined, the safety boundary is specified as concrete
allowed/forbidden *utterances* rather than vibes, and "measure the violation rate, don't assume it's zero" is the
right instinct. The problems below are problems of a plan good enough to be worth stress-testing.

---

## Status update (2026-09-20)

Contribution 1's degradation sweep has been **run** (50 stratified PTB-XL records × 6 damage types × 5 levels +
clean = 1,550 tests; scope reduced from the planned ~500 records because of time and free-GPU limits). First
results: heart-rate error and patient-facing false reassurance appear only at the most severe blur and resolution
loss; rotation causes silent drops; JPEG, grid contrast and brightness show no effect; 6 of 50 records fail in most
of their versions (4 even on the clean picture). Only the heart-rate version of measure T3 exists; PR/QRS/QT and diagnosis-level
false reassurance, and all of Contribution 2, are not yet done. Details: [SWEEP-RESULTS.md](SWEEP-RESULTS.md) and
[PROGRESS-LOG.md](PROGRESS-LOG.md) (Days 7–9). Where this deviates from the plan below: the sample is ~50, not
~500 records, so the Verification claim "reported explicitly" applies to a much smaller abnormal count (25).

## Part 1 — Evaluation

### 🔴 Blocker 1 — The guardrail evaluation is circular

The guide says an output filter blocks diagnostic phrasing, and you report the violation rate.

You cannot measure a filter's violation rate **using that same filter**. By construction it reports ~0% — every
violation it detects is one it already blocked. That's a tautology, and it's the first thing an examiner will find.

This matters more than it looks: the judge harness you build here is the **same harness** that measures T3
explanation error in [Part 2](#part-2--the-research-contribution). Build it correctly once and it carries two
results.

**Fix — separate the enforcer from the evaluator:**

| Role | Mechanism |
|---|---|
| **Enforce** (in the product) | Constrained prompt + keyword/rule output filter |
| **Evaluate** (in the paper) | *Independent* judge over a held-out sample of **post-filter** outputs — LLM-as-judge with a rubric written from §8's allowed/forbidden lists, **plus** manual review of ~100 outputs |

Report **leakage past the filter**, not what the filter caught. The interesting number is what your filter missed.
Have a second person (advisor, peer) blind-rate a subset so you can report inter-rater agreement.

### 🔴 Blocker 2 — The §2 novelty claim is partly already occupied

§2 claims: *"No existing system combines real-world-robust digitization, structured explainable feature extraction,
an explicit non-diagnostic safety boundary, and empirical evaluation of patient comprehension."*

A literature check puts that under pressure from three directions:

| §2 assumes | Actually found |
|---|---|
| Nothing ECG-specific exists for patients | [Patient information guides for cardiological procedures incl. ECG](https://pmc.ncbi.nlm.nih.gov/articles/PMC13025549/), generated with ChatGPT/Gemini — *Global Cardiology Science & Practice* (2025) |
| Comprehension evaluation is unexplored | [Ophthalmology-notes comprehension trial](https://clinicaltrials.gov/study/NCT06859216) (completing Jun 2026); [ReLay](https://arxiv.org/pdf/2605.00468) on personalized plain-language summaries |
| Measuring safety adherence is novel | Mature subfield — [CSEDB](https://www.nature.com/articles/s41746-025-02277-8) defines 30 clinical safety metrics; refusal rate / groundedness are standard |

ECG+LLM is also moving fast: [ECG-LM](https://spj.science.org/doi/10.34133/hds.0221) and
[vision-LLM ECG image interpretation](https://www.jmir.org/2026/1/e86692) are both recent. Both clinician-facing,
so the patient-facing distinction survives — but it's eroding, and "we combined three existing things" is a weak
claim even when true.

**Fix:** replace the combination claim with the error-propagation claim in
[Part 2](#part-2--the-research-contribution). Then run a dated systematic search (PubMed + arXiv + Scholar) —
record **exact queries, dates, result counts**, versioned, re-run before submission. Find out in Week 2 whether
someone has published it, not at the defense.

### 🟠 Issue 3 — "Node.js/Express *or* FastAPI (pick one)" is unresolved

The guide justifies a microservice split because digitization and NeuroKit2 are Python-native. That holds for a
team; for a solo capstone it buys an integration boundary you must build, debug, deploy, and document — and your
own risk table already lists "backend/AI-service integration overhead" as a risk.

**Recommendation: single FastAPI backend.** Python end-to-end, no cross-language boundary, no second runtime in
deployment. This *deletes* a risk row rather than mitigating it. React frontend unaffected; you keep the logical
separation in the architecture diagram (modules, not services). V2+ modules are also Python, so the split buys no
future flexibility either.

✅ **Confirmed (2026-08-10):** no specific language/stack is required by the program. Single FastAPI backend it is.

### 🟠 Issue 4 — MIMIC-IV-ECG has a multi-week access gate

Verified against PhysioNet:
- **PTB-XL** — fully **open access**, CC-BY 4.0, no credentialing. 21,799 records / 18,869 patients, ~3 GB.
  Downloadable today. ✅
- **MIMIC-IV-ECG** — **credentialed only**: CITI "Data or Specimens Only Research" + completion report + signed
  DUA + supervisor verification. Realistically **2–6 weeks**.

The guide lists it as optional. **Cut it** — or start credentialing this week. Don't let an optional held-out set
become the critical path.

### 🟡 Issue 5 — Digitization metrics: your instinct is right, with literature backing

PhysioNet Challenge 2024 scored digitization with **SNR**. Adopt it for comparability with published baselines.

Keep your feature-level error metric too — the Challenge organizers note SNR captures gross distortion (QRS,
T-wave) while **missing clinically significant subtle detail** like Q-wave onset, T-offset, and ST segment. Since
your whole downstream pipeline is interval measurement, feature-level error is arguably your *more* relevant
metric. Report both, cite that limitation as justification — it turns a metrics choice into a methodological
argument.

### 🟡 Issue 6 — Free-tier LLM rate limits will bite

Guardrail evaluation over "a large test set" = thousands of calls against Groq/Gemini free tiers. Build **response
caching keyed on the feature vector** from day one, and log every prompt/response pair to disk — you need those
transcripts for the paper anyway, and re-running a batch to recover lost output is pure waste.

### ⚪ Issue 7 — The plugins section is orthogonal; defer it

Two honest notes on §11: **I cannot verify** those plugin names, marketplace IDs, or command sets are current — the
guide states them as fact, so verify before relying on them. And `git clone ... && ./setup` runs a third-party
script; normal developer risk, but worth a deliberate decision.

Mainly: none of it affects your grade or paper. Defer past Review 1. `/diagram` and `/make-pdf` are genuinely
useful for figures — revisit then.

### ✅ Keep unchanged

- **The V1/V2+ split** and naming scope creep as risk #1 — correct diagnosis of how these projects fail.
- **§8's safety boundary** as concrete allowed/forbidden utterances. Directly implementable *and* gradeable.
- **No model training in V1** — removes GPU dependency and weeks of risk.
- **Structured output between every stage, never raw signal → LLM** — what makes the system auditable.

---

## The Deferred Study

**What deferral costs — and why it's now covered.** Per §2, the comprehension study *was* the stated academic
novelty, so dropping it would normally hollow out the research claim. [Part 2](#part-2--the-research-contribution)
replaces it: error propagation and uncertainty propagation carry the novelty instead, and neither needs a single
participant. The deferral is no longer a hole in the paper.

**What deferral buys.** It removes the two longest-lead risks (ethics approval, study design/power) from the
critical path, and returns ~3 weeks — which happens to be exactly the overrun that pushed the original Phase 6 past
the November review. The schedule below now fits.

**The cheap hedge — do this.** From Phase 3, have the pipeline generate and log **all three explanation variants**
per ECG (raw report / naive unconstrained LLM / bounded explanation). Near-zero cost now; if you later decide to
run the study, the materials already exist. Retrofitting this after the fact is expensive.

**Decision deadline — around mid-September (start of Phase 3).** Not because the study runs then, but because
ethics approval takes 3–8 weeks and would need to start by then to land in time. If you're past mid-September with
no decision, the study is off the table by default. Better to choose that deliberately.

---

## Part 2 — The Research Contribution

### The gap, in plain terms

A patient photographs their ECG printout. The photo is slightly blurry or tilted. The digitizer misreads the trace
a little. A QT interval that was truly **480 ms** comes out as **420 ms**. The app then tells the patient, with
complete confidence:

> *"Your QT interval is 420 ms, which is within the normal range."*

It wasn't normal. The patient is reassured and doesn't see a doctor. **A bad photo just became bad medical advice.**

The literature evaluates digitization against clinical biomarkers (RR, QRS width, QT) and stops there. Nobody
follows the error one hop further — into the sentence the patient actually reads. That hop is where the harm is,
and it's unoccupied.

**The research question:**
> **How much image degradation does it take before the system tells a patient something factually wrong — and can
> the system detect that it's happening?**

### Why this fits your project exactly

| Property | Why it matters now |
|---|---|
| **No human participants** | No ethics approval, no recruiting. Removes the blocker that deferred the original study. |
| **PTB-XL is sufficient** | Open access, ground truth known. You already planned to download it. |
| **Reuses the pipeline** | The experiment *is* your Phase 2 + Phase 3 system, run in a loop. Little added build work. |
| **Rewards your architecture** | §4's "structured output between every stage" makes explanation error **automatically computable** — see below. This turns a design decision you already made into a methodological asset. |
| **Feeds the product** | The result is a minimum image-quality threshold the app then *enforces at upload*. Research output becomes a shipped feature. |

### Contribution 1 — Error propagation study

**Setup.** Sample ~500 PTB-XL records, stratified so a meaningful fraction have genuinely out-of-range values
(without abnormal cases you cannot observe false reassurance at all). Render to images with ECG-Image-Kit at
controlled degradation levels.

**Degradation axes** — vary one at a time, then in combination, ~5 levels each plus a clean baseline:
blur · rotation/skew · JPEG compression · resolution · brightness/shadow gradient · grid contrast.

**Three measurement tiers** (the third is the novel one):

| Tier | Measures | Metric |
|---|---|---|
| T1 signal | Waveform fidelity | SNR vs ground truth *(comparable to PhysioNet 2024)* |
| T2 feature | Clinical measurements | Absolute error in ms/bpm — HR, PR, QRS, QT/QTc, axis |
| **T3 explanation** | **What the patient is told** | **Error taxonomy below** |

**T3 error taxonomy:**

| Class | Definition | Severity |
|---|---|---|
| **False reassurance** | Ground truth out of range → explanation says in-range | 🔴 **Safety-critical — the headline metric** |
| **False alarm** | Ground truth in range → explanation says out-of-range | 🟠 Causes anxiety, unnecessary visits |
| **Value error** | Stated number off by more than clinical tolerance | 🟡 |
| **Silent drop** | Feature failed to extract; explanation omits it without saying so | 🔴 Invisible failure |

**How T3 is computed cheaply.** Because §4 passes a *structured feature dict* to the LLM rather than raw signal,
you can classify most of T3 **deterministically** — compare the degraded-image feature dict against the
ground-truth dict using a reference-range table. The LLM-judge is then only needed for the narrow question "does
the generated text faithfully state this dict?", which is also what Blocker 1's independent judge already does.
One evaluation harness, two results.

**Output.** Curves of degradation level → false-reassurance rate, and a derived **minimum acceptable image quality
threshold**. That threshold ships as an upload-time quality gate.

### Contribution 2 — Uncertainty propagation

Contribution 1 shows the failure exists. Contribution 2 addresses it — and it's what turns a measurement paper into
a system paper.

Every stage of your pipeline currently discards its own uncertainty and hands the next stage a bare number. Instead:

1. **Compute a no-reference quality proxy at inference** — obtainable *without* ground truth: grid-detection
   confidence, lead-segmentation confidence, signal continuity/gap count, estimated trace SNR.
2. **Calibrate it** against the true errors measured in Contribution 1.
3. **Surface it** in the explanation:
   > *"Your QT interval is about 460 ms. This image was low quality, so this measurement may not be exact — please
   > confirm with your doctor."*
4. **Evaluate it:** does the proxy actually predict error? Report correlation with T2 error, and AUC for predicting
   a false-reassurance event. If the proxy predicts failure, the system can refuse rather than mislead.

Nothing in the surveyed literature propagates digitization uncertainty into patient-facing output. Confident
statement of a possibly-wrong number is the default everywhere.

⚠️ **Risk — digitizer opacity.** Two of the four proposed signals (grid-detection and lead-segmentation confidence)
require the digitizer to *expose its internals*. If you adopt a black-box tool, they may not exist, and
Contribution 2 loses half its inputs.

**Mitigation — split the proxy into two tiers, and build the second tier first:**

| Tier | Signals | Availability |
|---|---|---|
| **Image-level** *(build first)* | Laplacian-variance blur, skew estimate, resolution, grid contrast, JPEG artifacts | Computed from the image alone — **always available, any digitizer** |
| Digitizer-internal *(bonus)* | Grid/lead-segmentation confidence, gap count, trace SNR | Only if the tool exposes them |

Image-level signals are also the ones a real upload gate would use — they're computable *before* digitization runs,
so a low-quality photo can be rejected without wasting the pipeline. Build those first; treat internal signals as
upside. This makes Contribution 2 robust to your Week 2 digitizer choice, which is otherwise a hidden dependency
between two decisions made weeks apart.

### Proposed title

**Recommended:**
> **From Paper to Patient: Quantifying and Mitigating Digitization-Induced False Reassurance in Automated ECG
> Explanation**

Why this one: *"From Paper to Patient"* literally names the pipeline and is memorable; *"Quantifying and
Mitigating"* maps one-to-one onto Contributions 1 and 2, signalling this is a system paper rather than a
measurement note; *"False Reassurance"* names the safety-critical metric in the title, where it does the most work.

**Alternatives:**

| Title | Best when |
|---|---|
| *False Reassurance in Automated ECG Explanation: Measuring Error Propagation from Paper Image to Patient-Facing Text* | You want the metric leading and no rhetorical hook |
| *MediSense-Cardio: An Uncertainty-Aware Pipeline for Safe Patient-Facing ECG Explanation* | Your department expects the system name in the title |
| *When Image Quality Becomes Misinformation: Error Propagation in Patient-Facing ECG Interpretation* | You want the broadest framing — generalizes past ECG |

**Naming the metric is worth doing deliberately.** *"False reassurance rate"* is short, self-explanatory to a
non-specialist, and clinically resonant. A named metric is what makes work citable — pick it now and use it
consistently in code, figures, and prose. Define it once, formally, in the methods section.

⚠️ Check whether your institution requires the project name (*MediSense-Cardio*) in the formal title. If so, use
`MediSense-Cardio: From Paper to Patient — …` and keep the rest.

### The claim to write in the paper

❌ **Not:** *"We combined digitization, explanation, and a safety boundary."* — weak, and partly already occupied.

✅ **Instead:**
> *"Digitization is solved and patient-facing LLM summarization is established, but no work measures how
> digitization error propagates into what a patient is told. We quantify that propagation, show that image
> degradation induces false reassurance at measurable rates, and demonstrate that a no-reference quality proxy
> predicts these failures well enough to withhold or qualify the explanation."*

Narrower, survives a literature check, provable with PTB-XL alone — and the safety framing makes it genuinely
publishable rather than merely gradeable.

---

## Part 3 — Corrected Roadmap

### Changes vs. the original guide

| # | Change | Reason |
|---|---|---|
| 1 | Comprehension study **deferred**; log 3 variants anyway | Your call; hedge keeps it recoverable |
| 2 | **Novelty → error propagation + uncertainty** (Part 2) | Combination claim partly occupied; this one needs no participants |
| 3 | Guardrail eval → independent judge + human review | Original was circular; shares a harness with the T3 evaluation |
| 4 | Backend → single FastAPI | Deletes the integration risk *(pending stack mandate)* |
| 5 | MIMIC-IV-ECG → cut, or credential in Week 1 | 2–6 week access gate |
| 6 | Paper writing → continuous from Phase 2 | Methods written 4 months later are slow and wrong |
| 7 | Novelty search → documented, dated, versioned | Defensibility at viva |
| 8 | LLM caching + transcript logging → day one | Rate limits; **and the study re-runs the pipeline hundreds of times** |
| 9 | Plugins (§11) → deferred past Review 1 | Zero effect on deliverables |

### Day 0 — Before any real code

Three gates. Nothing downstream is safe until these clear, and none of them is a coding task.

**Gate 1 — Two conversations (today/tomorrow).** Zero code, highest leverage in the whole plan.
- **Advisor: does the reframed contribution (Part 2) count as novelty?** If they say no, months of work point the
  wrong way. One email now.
- **Is a stack mandated (MERN/Node)?** Decides Phase 4 architecture.
- Confirm both review dates while you're asking.

**Gate 2 — The walking skeleton (one day, throwaway code).** Before committing 20 weeks to this toolchain, prove
it runs *on your machine* — **one** PTB-XL record, all the way through, ugly and hardcoded:

```
PTB-XL record → ECG-Image-Kit renders an image → digitizer reads it back
              → NeuroKit2 extracts HR + intervals → compare against ground truth
```

This is a **spike, not the pipeline** — throw it away afterward. Its only job is to surface a broken link in Week 1
rather than Week 6. Expected failure points, in order:
1. **The digitizer.** ECG-Digitiser is deep-learning-based (torch + model weights). Heaviest dependency, most
   likely to fight you.
2. **Windows.** Many research repos assume Linux. If you hit path/build failures, move to **WSL2** early — that
   decision is cheap now and expensive in Week 10.
3. **ECG-Image-Kit** rendering setup.

If the skeleton runs, the plan is sound. If it doesn't, you've lost a day instead of a month.

**Gate 3 — Repo hygiene (30 minutes).** `.gitignore` (`venv/`, `node_modules/`, `data/`, `.env`) committed
**before** PTB-XL lands. A 3 GB dataset in git history is genuinely painful to remove later.

> **Do NOT start with:** auth, React, database schema, or the dashboard. They're the comfortable, familiar part —
> which is exactly why they're the trap. They carry no project risk, and starting there means meeting the hard
> research problem in month three with no slack left.

### Immediate — Week 1 remainder

*Assumes the three Day-0 gates above are clear. Gates 1 and 3 are not repeated here.*

1. **Decide MIMIC-IV-ECG** — cut, or begin CITI training now.
2. **Python env** — venv + §10 dependencies. Confirm `neurokit2` and `wfdb` import cleanly.
3. **Download PTB-XL** (~3 GB, open access) into gitignored `data/`.
4. **Shortlist digitizers** — ECG-Digitiser (Krones et al.), ECGtizer, npj "Digitizing paper ECGs at scale". Note
   license + dependencies for each *before* investing in one — **and whether each exposes internal confidence
   signals**, which Contribution 2 depends on (see the risk note in Part 2).
5. **Run the Gate 2 walking skeleton** end to end on one record.

### Week 2

- Bench shortlisted digitizers on identical sample images; pick on **evidence**, record the comparison — that table
  goes straight into the paper.
- **Get ECG-Image-Kit rendering** a PTB-XL record to an image. The degradation study depends on it, so failure here
  is worth discovering in Week 2, not Week 4.
- Run and **document** the systematic novelty search (queries, dates, counts) — now targeting the *error
  propagation* claim, not the combination claim.

### Week 3

- Turn the Gate 2 spike into a **real, re-runnable script** (arguments not hardcoded, ~10 records not one). Still
  rough, but it must be the thing the degradation harness grows out of — not the throwaway.
- Lock the research question in writing — the Part 2 formulation, with the degradation study named.
- Draft Review 1 slides (problem, gap, scope, stack rationale).

### Buffer — no new technical work

Rehearse, fix demo breakage. Protect this; it is not spare capacity.

**→ Review 1** — locked scope · documented literature gap · working digitization + extraction demo ·
stack chosen with rationale · **the reframed research claim stated and advisor-endorsed**.

### Phases 2–5

- **Phase 2** — Digitization pipeline; validate against PTB-XL ground truth; real-photo stress test.
  Report **SNR + feature-level error**.
  **+ Build the degradation harness** (render → degrade → digitize → extract, scripted and repeatable) and collect
  **T1 + T2**. Stratify the sample for abnormal cases now — retrofitting that later invalidates the run.
  *Paper: methodology starts here.*
- **Phase 3** — Prompt template, LLM integration (caching + transcript logging), guardrail filter,
  iterate. **Log all 3 explanation variants.** Independent leakage evaluation.
  **+ Collect T3** (reuse the same judge harness) → false-reassurance curves → **derive the quality threshold**.
  **+ Build and calibrate the no-reference quality proxy** (Contribution 2). *Study go/no-go decision.*
- **Phase 4** — Platform shell: auth, profile, endpoints, DB, frontend, deploy end-to-end.
  **+ Ship the threshold as an upload-time quality gate**, and surface the confidence qualifier in the UI — the
  research result becomes a visible product feature, which also demos well.
- **Phase 5** — Paper, polish, defense deck, final deployment. *(~3 weeks of recovered slack lands
  here — comfortably inside the November review.)*

---

## Verification

**Week 1 is done when:**
```bash
python -c "import neurokit2, wfdb, cv2; print('deps ok')"
```
- `git log` shows real commits; `git status` shows no `data/` or `venv/` tracked
- PTB-XL loads — a record reads via `wfdb` and plots
- Stack mandate confirmed; MIMIC decision made
- Digitizer shortlist documented with licenses

**Review 1 is met when** a single command takes an ECG image and prints HR + intervals, and you can state the
literature gap with dated citations.

**Guardrail (Phase 3) is validly measured when** leakage is reported by a judge *independent* of the filter, over
post-filter outputs, with a human-reviewed subsample and inter-rater agreement.

**The research contribution holds when:**
- The degradation harness is **scripted and re-runnable end to end** — a result you cannot regenerate is a result
  you cannot defend.
- The sample contains enough out-of-range cases that false reassurance is *observable*; report the abnormal-case
  count explicitly.
- False-reassurance rate is reported **as a curve against degradation**, not a single number — the curve is the
  finding, and it's what yields the threshold.
- The quality proxy is validated on records **held out** from those used to calibrate it.
- A named negative result is acceptable and still publishable: if the proxy fails to predict error, report it. That
  is a real finding about the limits of no-reference quality estimation, not a failed project.

---

## Open Questions

1. **Does your advisor accept the reframed contribution?** Take Part 2 to them before Review 1 — a novelty claim
   the supervisor hasn't endorsed is a bad thing to discover at the defense. This is the highest-value question here.
2. ~~Is a specific stack mandated?~~ **Resolved 2026-08-10 — no. FastAPI confirmed.**
3. **Exact date of the November review?** Confirms the Phase 5 landing zone.
4. **MIMIC-IV-ECG — cut or credential?** Decide this week or it decides itself.

## Sources

*Citations verified 2026-08-19. Where a journal version exists, it is cited in preference to the preprint —
see [REFERENCES.md](REFERENCES.md) for the full annotated reading list.*

**Tools and data this project builds on:**
- Stenhede, Bjørnstad & Ranjbar, "Digitizing paper ECGs at scale: an open-source algorithm for clinical
  research", *npj Digital Medicine* (2026). doi: 10.1038/s41746-025-02327-1 —
  [journal](https://www.nature.com/articles/s41746-025-02327-1) · [preprint](https://arxiv.org/pdf/2510.19590)
- Shivashankara, Deepanshi, Mehri Shervedani, Clifford, Reyna & Sameni, "ECG-Image-Kit: a synthetic image
  generation toolbox to facilitate deep learning-based electrocardiogram digitization",
  ***Physiological Measurement*** **45**(5) 055019 (2024). doi: 10.1088/1361-6579/ad4954 · open access —
  [journal](https://iopscience.iop.org/article/10.1088/1361-6579/ad4954) ·
  [preprint](https://arxiv.org/pdf/2307.01946)
- [PTB-XL v1.0.3 — open access, CC-BY 4.0](https://physionet.org/content/ptb-xl/1.0.3/)
- [MIMIC-IV-ECG access requirements](https://mimic.mit.edu/docs/faq/how-to-get-access.html)

**Metrics and degradation evidence:**
- Reyna, Deepanshi, Weigle, Koscova, … Clifford & Sameni, "ECG-image-database: large-scale paired ECG images and
  time-series with real-world artifacts; a foundation for computerized ECG digitization and analysis",
  ***Physiological Measurement*** **47**(7) 075015 (2026). doi: 10.1088/1361-6579/ae85b2 · open access —
  [journal](https://iopscience.iop.org/article/10.1088/1361-6579/ae85b2) ·
  [preprint](https://arxiv.org/html/2409.16612v1)
  *Source of the "SNR misses clinically significant subtle detail" argument used in Issue 5 above.*
- [PhysioNet Challenge 2024 — results & scoring](https://moody-challenge.physionet.org/2024/results/)
- [Digitization and Classification of ECG Images: Challenge 2024 (CinC)](https://moody-challenge.physionet.org/2024/papers/cinc_paper.pdf)

**Prior work bounding the novelty claim (Blocker 2):**
- Soundarrajan, Vartanian, Bhakle, Katakam, Dhanwada, Randhawa & Puvvala, "Assessment of patient information
  guides generated by LLMs for common cardiological procedures", *Global Cardiology Science & Practice*
  **2025**(2) e202526. doi: 10.21542/gcsp.2025.26 —
  [article](https://pmc.ncbi.nlm.nih.gov/articles/PMC13025549/)
- [AI plain-language summaries & patient comprehension trial (ophthalmology)](https://clinicaltrials.gov/study/NCT06859216)
- [ReLay — personalized LLM plain-language summaries](https://arxiv.org/pdf/2605.00468)
- [CSEDB — clinical safety/effectiveness benchmark for medical LLMs](https://www.nature.com/articles/s41746-025-02277-8) — *npj Digital Medicine*
- [ECG-LM — multimodal LLM for ECG](https://spj.science.org/doi/10.34133/hds.0221) — *Health Data Science*
- [Vision-enabled LLMs for ECG image interpretation](https://www.jmir.org/2026/1/e86692) — *JMIR* (2026)

**Publication venues** — scope fit and evidence assessed 2026-08-19; see
[REFERENCES.md § Candidate publication venues](REFERENCES.md#candidate-publication-venues).
Short version: ***Physiological Measurement*** is the strongest target (it published both imaging tools above,
and its scope explicitly covers signal-quality assessment and validation); *npj Digital Medicine* is the
high-prestige option; *Journal of Electrocardiology* the well-matched fallback.
⚠️ CinC 2026 closed on 15 Apr 2026 — **CinC 2027** is the realistic conference target.
