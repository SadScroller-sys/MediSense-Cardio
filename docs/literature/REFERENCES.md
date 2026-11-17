# MediSense-Cardio — Reading List & References

*Real papers, in the order they should be read. Each entry says what to take from it in one plain sentence.*

*Companion documents: [PLAN-simple.md](PLAN-simple.md) (plain English plan) · [PLAN.md](PLAN.md) (technical plan) ·
[PROGRESS-LOG.md](PROGRESS-LOG.md) (what's been built so far).*

---

## How to use this list

Read in numbered order — each topic depends on the one before it. You cannot judge whether a measurement is
"out of range" until you know what the ranges are (Topic 1), and you cannot study image quality until you know
what the image is meant to produce (Topics 2–4).

**If you only have two days**, read Topics 1, 3, 5 and 6. Topics 5 and 6 are the closest published work to this
project's actual contribution.

⭐ = directly underpins our research contribution. 🎥 = video resources available for that topic.

### Where videos help, and where they run out

| Topic | Best way to learn it |
|---|---|
| 1 — ECG fundamentals | 🎥 **YouTube is excellent.** Well-taught, plenty of good material. |
| 2–3 — Dataset, digitization | Mixed — documentation and the papers themselves. |
| 4 — Image degradation | Papers. General OpenCV tutorials (perspective correction, document scanning) transfer well. |
| 5–6 — Quality assessment, uncertainty ⭐ | **Papers only. There are effectively no videos on this.** |

That last row matters: searching for *"ECG image quality → false reassurance → uncertainty"* returns almost
nothing on video. **That is not a gap in your searching — it is the point.** If there were a tutorial series on
this exact question, it would not be a research contribution. Expect to learn the novel part from journal papers,
and use video only for the foundations.

> ⚠️ **Caveat on all video links below:** these have been confirmed to exist and come from well-established
> channels, but nobody on this project has watched them end to end — treat them as starting points, not vetted
> curriculum. Prefer established channels over one-off videos, and never take a clinical threshold from a video.

---

## Topic 1 — ECG fundamentals and normal ranges

**Read this first. Nothing else makes sense without it.**

- **AHA/ACCF/HRS Recommendations for the Standardization and Interpretation of the Electrocardiogram**,
  *Circulation* (2009), 6-part scientific statement.
  https://www.ahajournals.org/doi/10.1161/circulationaha.108.191096
  Part IV specifically covers the ST segment, T and U waves, and the QT interval.

**What to take from it:** the definitions and normal ranges for the measurements this project reports — heart
rate, PR interval, QRS duration, QT/QTc. This is the clinical authority behind every "in range / out of range"
decision the system makes.

> ⚠️ **This is the single most important source in this list, and the most dangerous to get wrong.** These
> thresholds *define* what counts as false reassurance. If a cut-off is wrong by 10 ms, the headline metric is
> silently wrong and no test will catch it.
>
> Two specifics worth noting now: the guideline defines prolonged QT as **≥460 ms in women and >450 ms in men** —
> i.e. thresholds are **sex-specific**, so the system needs patient sex to judge QT correctly. Note also that
> reported normal values differ slightly by sex across other intervals too (PR, QRS).
>
> **Verify every number directly in the published guideline before it goes into code.** Do not take thresholds
> from summaries, including this one.

**Do not try to learn to diagnose diseases.** This project reports measurements only — see
[What we are deliberately not doing](#what-we-are-deliberately-not-doing).

---

### 🎥 Video resources for this topic

YouTube is genuinely good for ECG fundamentals — this is well-taught territory.

**Channels (well-established, large back catalogues):**
- **[The EKG Guy](https://www.youtube.com/c/theekgguy)** — run by a Mayo Clinic cardiology fellow; 500+ videos.
- **Ninja Nerd** — strong on the underlying physiology (*why* the heart produces each wave).
- **[LITFL ECG lecture series](https://litfl.com/ecg-interpretation-video-lectures/)** — 5-part series taught with
  a cardiologist.

**Single videos to start with:**
- [ECG Interpretation Made Easy (13 min)](https://www.youtube.com/watch?v=u1m3HKW1VqU) — fastest useful overview.
- [ECG/EKG Interpretation Tutorial — Episode 1](https://www.youtube.com/watch?v=FFUnBTe6c-Y) — start of a series.
- [Full ECG interpretation playlist](https://www.youtube.com/playlist?list=PL2oVjKTYocdPMaNwn4xbg6xAIaAnyraMj)

**Stop when you can confidently say what P, QRS, T, PR, QRS-duration and QT/QTc mean, and roughly what's normal.**
Do not continue into disease diagnosis — this project does not diagnose, so that time is better spent on Topics 5
and 6.

> ⚠️ Videos are for *intuition only*. Any number that goes into code must come from the AHA/ACCF/HRS guideline
> above, not from a video.

---

## Topic 2 — The dataset

- **Wagner et al., "PTB-XL, a large publicly available electrocardiography dataset"**, *Scientific Data* (2020).
  https://www.nature.com/articles/s41597-020-0495-6
  Dataset: https://physionet.org/content/ptb-xl/1.0.3/ — 21,799 records from 18,869 patients, ~3 GB,
  **open access, CC-BY 4.0, no application needed.**

- **Strodthoff, Mehari, Nagel, Aston, Sundar, Graff, Kanters, Haverkamp, Dössel, Loewe, Bär & Schaeffter,
  "PTB-XL+, a comprehensive electrocardiographic feature dataset"**, *Scientific Data* (2023).
  https://www.nature.com/articles/s41597-023-02153-8 ·
  https://physionet.org/content/ptb-xl-plus/1.0.1/

**What to take from these:** PTB-XL is the ground truth for the whole project — the "right answers" our degraded
images get compared against. PTB-XL+ adds measurements extracted by other tools, which is how we sanity-check
that our own measurement step is behaving.

*(For contrast: MIMIC-IV-ECG requires credentialing, training certification and a signed agreement — a 2–6 week
process. See [PLAN.md](PLAN.md) for why it's optional and possibly not worth the wait.)*

---

## Topic 3 — Turning paper ECGs into digital signals

- ⭐ **Stenhede, Bjørnstad & Ranjbar, "Digitizing paper ECGs at scale: an open-source algorithm for clinical
  research"**, *npj Digital Medicine* (2026). doi: 10.1038/s41746-025-02327-1
  https://www.nature.com/articles/s41746-025-02327-1 · preprint: https://arxiv.org/pdf/2510.19590
  Code: https://github.com/Ahus-AIM/Open-ECG-Digitizer
  **This is the tool already installed and running in this project.** Validated on 37,191 ECG images; reports
  ~19.65 dB signal-to-noise on scanned pages with real-world artifacts.

- **Shivashankara, Deepanshi, Mehri Shervedani, Clifford, Reyna & Sameni, "ECG-Image-Kit: a synthetic image
  generation toolbox to facilitate deep learning-based electrocardiogram digitization"**,
  *Physiological Measurement* **45**(5) 055019 (2024). doi: 10.1088/1361-6579/ad4954 · open access
  https://iopscience.iop.org/article/10.1088/1361-6579/ad4954 ·
  preprint: https://arxiv.org/abs/2307.01946 · code: https://github.com/alphanumericslab/ecg-image-kit
  Used to generate realistic ECG page images from digital signals.
  *(Cite the journal version, not the preprint.)*

- **Reyna, Deepanshi, Weigle, Koscova, Campbell, Seyedi, Elola, Bahrami Rad, Shah, Bhatia, Clifford & Sameni,
  "Digitization and Classification of ECG Images: The George B. Moody PhysioNet Challenge 2024"**,
  *Computing in Cardiology* **51**:1–4 (2024). https://www.cinc.org/archives/2024/pdf/CinC2024-011.pdf
  https://moody-challenge.physionet.org/2024/ · results: https://moody-challenge.physionet.org/2024/results/
  Challenge paper: https://moody-challenge.physionet.org/2024/papers/cinc_paper.pdf

- **Krones et al., ECG-Digitiser** (Challenge 2024 winner) — https://github.com/felixkrones/ECG-Digitiser
- **Lence, Fall, Cohen, Granese, Zucker, Salem & Prifti, "ECGtizer: a fully automated digitizing and signal
  recovery pipeline for electrocardiograms"** — https://arxiv.org/abs/2412.12139 ·
  https://github.com/UMMISCO/ecgtizer

**What to take from these:** how a photo of ECG paper becomes numbers — grid detection, perspective correction,
trace extraction, pixel→millivolt conversion. Also note the standard accuracy measure (SNR) used by the Challenge,
so our results are comparable to published work.

> **Important framing:** digitization is a **solved problem** we are *reusing*, not our contribution. Several
> working open-source tools already exist. Our contribution starts *after* this step.

---

### 🎥 Learning the measurement step (signal → numbers)

Searching for NeuroKit2 video tutorials mostly returns documentation — there is little good video coverage, and
the written material is better anyway.

- **[NeuroKit2 ECG documentation](https://neuropsychology.github.io/NeuroKit/functions/ecg.html)** — the library
  this project already uses for measurements.
- **[Worked HRV example with runnable code](https://neuropsychology.github.io/NeuroKit/examples/ecg_hrv/ecg_hrv.html)**
- **[Comparison of Python R-peak detection libraries](https://www.samproell.io/posts/signal/ecg-library-comparison/)**
  — useful because it shows different algorithms disagreeing on the same signal, which is a small preview of why
  measurement error matters in this project.

**For video:** search **"Pan-Tompkins algorithm explained"**. It's the classic heartbeat-detection method and
understanding it explains most of what NeuroKit2 does internally. Also useful: band-pass filtering, baseline
wander removal, powerline noise.

---

## Topic 4 — Real-world image degradation

- ⭐ **Reyna, Deepanshi, Weigle, Koscova, … Clifford & Sameni, "ECG-image-database: large-scale paired ECG images
  and time-series with real-world artifacts; a foundation for computerized ECG digitization and analysis"**,
  *Physiological Measurement* **47**(7) 075015 (2026, published 27 Jul 2026). doi: 10.1088/1361-6579/ae85b2 ·
  open access
  https://iopscience.iop.org/article/10.1088/1361-6579/ae85b2 · preprint: https://arxiv.org/html/2409.16612v1
  *(Cite the journal version, not the preprint.)*

**What to take from it:** the catalogue of distortions real photographed ECGs actually contain — perspective
skew, wrinkles, stains, uneven lighting. These are exactly the degradations our experiment will apply
deliberately.

It also makes a point we rely on directly: **SNR is a poor measure of clinically important detail.** It captures
gross waveform distortion but misses subtle features like Q-wave onset, T-offset and the ST segment — which are
precisely what interval measurements depend on. This is the published justification for why we report
measurement-level error alongside SNR, rather than SNR alone.

---

## Topic 5 ⭐ — ECG signal quality assessment

**This is the closest existing work to the first half of our contribution.**

- **Zhou, Zhu, Nakamura & Noro, "Electrocardiogram Quality Assessment with a Generalized Deep Learning Model
  Assisted by Conditional Generative Adversarial Networks"**, *Life* **11**:1013 (2021). doi: 10.3390/life11101013
  https://doi.org/10.3390/life11101013 · https://pmc.ncbi.nlm.nih.gov/articles/PMC8539388/
  Reports 97.1% / 96.4% accuracy identifying ECGs suitable for interpretation.

- **Huerta Herraiz, Martínez-Rodrigo, Bertomeu-González, Quesada, Rieta & Alcaraz, "A Deep Learning Approach for
  Featureless Robust Quality Assessment of Intermittent Atrial Fibrillation Recordings from Portable and Wearable
  Devices"**, *Entropy (Basel)* **22**(7) 733 (2020). doi: 10.3390/e22070733
  https://pmc.ncbi.nlm.nih.gov/articles/PMC7517279/

- **Strodthoff, Wagner, Schaeffter & Samek, "Deep Learning for ECG Analysis: Benchmarks and Insights from
  PTB-XL"**, *IEEE Journal of Biomedical and Health Informatics* **25**(5) 1519–1528 (2021).
  doi: 10.1109/JBHI.2020.3022989 — https://arxiv.org/pdf/2004.13701 (preprint)
  Published in IEEE JBHI, not just an arXiv preprint — includes signal quality assessment among its benchmark
  tasks. *(This entry was previously cited as arXiv-only; corrected 2026-08-21.)*

**What to take from these:** the established idea that you should check whether an ECG is good enough *before*
trusting any analysis of it.

**How our project extends this:** existing work asks *"is the ECG signal good enough to analyse?"* We ask the
harder, more consequential question — ***"is the ECG image good enough that we can safely say something to a
patient about it?"*** The published work stops at the signal. We follow the error all the way to the sentence the
patient reads.

---

## Topic 6 ⭐⭐ — Uncertainty, abstention and knowing when not to answer

**This is the closest existing work to the second half of our contribution — the part that makes it a system
paper rather than just a measurement.**

- **Vazhentsev, Sviridov, Barseghyan, Kuzmin, Panchenko, Nesterov, Shelmanov & Panov, "Uncertainty-aware
  abstention in medical diagnosis based on medical texts"**, *npj Artificial Intelligence* (2026).
  https://www.nature.com/articles/s44387-026-00097-z

- **Kwon & Kim, "Conformal selective prediction with cost-aware deferral for safe clinical triage under
  distribution shift"**, *Scientific Reports* **16**:10016 (2026). https://www.nature.com/articles/s41598-026-40637-w

- **Strong, Men & Noble, "Trustworthy and Practical AI for Healthcare: A Guided Deferral System with Large
  Language Models"**
  https://arxiv.org/pdf/2406.07212 — deferral specifically in an LLM setting, which is our setting.

- 🔴 **Jabbour, Fouhey, Banovic, Shepard, Kazerooni, Sjoding & Wiens, "Selective Prediction Reduces the Negative
  Effects of Automation Bias Overall but Increases False Negatives"** — https://arxiv.org/abs/2508.07617
  *(Previously circulated as "On the Limits of Selective AI Prediction: A Case Study in Clinical Decision
  Making" — retitled on arXiv; cite the current title.)*

**What to take from these:** how a system can recognise its own uncertainty and decline to answer — saying
*"this image isn't clear enough to give you a reliable number, please retake it or see a doctor"* instead of
stating a confident wrong value.

> **Read the last one carefully — it argues against us.** It finds that when AI abstains, clinicians' error
> patterns *shift* rather than simply improve: false positives fell but false negatives rose. In other words,
> abstention is not automatically safer; it moves risk around.
>
> This is a direct challenge to our Contribution 2, and it is far better to meet it now than to have an examiner
> raise it at the review. Engaging with it honestly — acknowledging that "the system says I'm unsure" has its own
> failure modes — makes the project stronger, not weaker.

---

## Topic 7 — Explaining medical results to patients, safely

*These bound our novelty claim — they show what has already been done, so we claim only what is genuinely new.*

- **Soundarrajan, Vartanian, Bhakle, Katakam, Dhanwada, Randhawa & Puvvala, "Assessment of patient information
  guides generated by LLMs for common cardiological procedures"**, *Global Cardiology Science & Practice*
  **2025**(2) e202526. doi: 10.21542/gcsp.2025.26
  https://pmc.ncbi.nlm.nih.gov/articles/PMC13025549/

- **Chan, Han, Chen, Fang, Gryboski, Lee, Tanna, Zhu, Lu, Wang & Guo, "ReLay: Personalized LLM-Generated
  Plain-Language Summaries for Better Understanding, but at What Cost?"** — https://arxiv.org/abs/2605.00468

- **AI-generated plain-language summaries & patient comprehension trial (ophthalmology)**
  https://clinicaltrials.gov/study/NCT06859216

- **Wang, Tang, Yang, Gong, … Liang & Wu, "A novel evaluation benchmark for medical LLMs illuminating safety
  and effectiveness in clinical domains"** (the CSEDB benchmark), *npj Digital Medicine* **9**:91 (2025).
  https://www.nature.com/articles/s41746-025-02277-8 — defines 30 clinical safety metrics.

- **Yang, Hong, Zhang, Luo, Zhao, Zhang, Yu, Zhou, Yang, Zhang, Qiao & Nie, "ECG-LM: Understanding
  Electrocardiogram with a Large Language Model"**, *Health Data Science* (2025).
  https://spj.science.org/doi/10.34133/hds.0221

- **Soubh, Rasenack, Haarmann, Wiedmann, Zabel, Schmidt, Suliman & Bergau, "Performance of Vision-Enabled Large
  Language Models in Image-Based Electrocardiogram Interpretation: Exploratory Evaluation"**,
  *J Med Internet Res* **28**:e86692 (2026). doi: 10.2196/86692 · https://www.jmir.org/2026/1/e86692

**What to take from these:** plain-language medical summaries and medical-AI safety measurement are both
**established fields** — we are not the first to do either. The existing ECG+LLM work is aimed at *clinicians*,
not patients, which is the distinction our project sits in. Knowing this list protects you from claiming novelty
you don't have.

---

## The architecture

```
                    PAPER ECG
                        │
                        ▼
                📷 Patient photo
                        │
                        ▼
        ┌───────────────────────────────┐
        │   Image quality analysis      │
        │   blur · tilt · resolution    │
        │   contrast · lighting         │
        └───────────────┬───────────────┘
                        │
                  Quality score
                        │
              ┌─────────┴─────────┐
              │                   │
           GOOD                  BAD
              │                   │
              ▼                   ▼
      ECG digitization        ABSTAIN
              │                   │
              ▼                   ▼
      Signal extraction    "Image too unclear
              │             to read reliably —
              ▼             please retake"
      Measurements
      HR · PR · QRS · QT/QTc
              │
              ▼
   Reference-range comparison
   (per AHA/ACCF/HRS, sex-specific)
              │
              ▼
   Bounded plain-language explanation
   + uncertainty qualifier where needed
              │
              ▼
   "Your QT interval is about 460 ms,
    which is above the usual range.
    Please discuss this with a doctor."
```

**Every stage hands the next a structured, inspectable result** — never a raw signal straight to the language
model. This is what keeps the system auditable, and it's also what makes our experiment cheap to run: because the
measurements are structured, we can compare "what the system would say" against "what the truth was"
automatically.

---

## What we are deliberately not doing

Stating these as **decisions** rather than gaps — each one was considered and rejected for a reason.

| Not doing | Why |
|---|---|
| **Diagnosing diseases** | The system reports measurements and whether they fall inside published reference ranges. It never names a condition, never estimates risk, never advises treatment. This is a safety boundary, not a limitation — and it is measured and reported, not assumed. |
| **Training our own classifier** | Working open-source digitizers already exist and are published. Rebuilding one adds months and contributes nothing new. |
| **Grad-CAM / SHAP / saliency maps** | These explain what a *trained classifier* paid attention to. We train no classifier — measurements come from a deterministic algorithm, and wording from a language model. There is no model attention to visualise, so these techniques do not apply to this architecture. |
| **Risk scores or "confidence in a diagnosis"** | Follows from the safety boundary. Our uncertainty is about **measurement reliability** ("this photo may be too unclear to read accurately"), never about **clinical risk** ("you probably have X"). These are different things and conflating them would breach the safety design. |
| **A patient comprehension study (for now)** | Deferred — it needs ethics approval with a long lead time. The current contribution is provable with PTB-XL alone. See [PLAN.md](PLAN.md). |

---

## Candidate publication venues

*Scopes and recent-paper evidence checked 2026-08-19. Re-check before submitting — scopes and deadlines move.*

| Venue | Scope fit | Evidence it publishes our kind of work |
|---|---|---|
| ⭐ **Physiological Measurement** (IOP) | **Strongest.** Scope explicitly covers signal quality assessment, calibration and validation — i.e. Contribution 2 — alongside ECG digitization | Published **both** ECG-Image-Kit (2024) and ECG-Image-Database (2026). The digitization-imaging community's home journal |
| **npj Digital Medicine** (Nature) | Clinical application of validated AI/ML models; digital-health safety and governance | Published our digitizer (*Digitizing paper ECGs at scale*) and CSEDB. Highest prestige, most competitive |
| **Journal of Electrocardiology** (Elsevier) | The most ECG-specific journal that exists | Published *High Precision ECG Digitization Using AI* (Feb 2025) |
| **JMIR** | Patient-facing digital health, AI health communication, plain-language comprehension | Active 2025–26 stream on patient-centred AI health communication and LLM patient-question accuracy; also ECG-Chat report generation |
| **Computers in Biology and Medicine** (Elsevier) | Pipeline/methods papers in medical signal analysis | Steady ECG deep-learning output through 2025 |
| **Artificial Intelligence in Medicine** (Elsevier) | Requires *both* clinical impact **and** methodological novelty — our abstention/deferral framing fits | Core scope is decision-support under uncertainty |
| **IEEE JBHI** | Engineering-leaning biomedical informatics | ECG + uncertainty-quantification work appears here, though scope statement is less explicit than the above |

**Conference — Computing in Cardiology (CinC).** Hosts the PhysioNet Challenge, so the digitization audience is
already assembled; 4-page papers, fast turnaround.
⚠️ **CinC 2026 (Madrid, 20–23 Sep) is closed** — abstracts were due 15 Apr 2026. **CinC 2027 is the realistic
target**, which fits a Phase-2/3 results timeline better anyway.

**Suggested strategy:** Contribution 1 (error propagation) → Physiological Measurement or CinC 2027.
Contributions 1+2 together as a system paper → npj Digital Medicine, with Journal of Electrocardiology as the
well-matched fallback.

---

## Where this project's contribution sits

Reading the list above in order, the gap becomes visible:

- Topic 3 shows **digitization is solved.**
- Topic 5 shows people check **whether a signal is good enough to analyse.**
- Topic 7 shows people **write plain-language medical summaries**, and **measure AI safety.**

**Nobody joins the last link in the chain.** No published work measures how a degraded input image propagates all
the way through to a *factually wrong statement made to a patient* — or builds a system that detects that risk and
declines to answer instead.

That is what this project measures, and then mitigates.

---

## Appendix — Full IEEE-numbered reference list (Review 1 requirement)

*Compiled 2026-08-21 for the guide's requested format: numbered `[N]`, grouped by topic, ≥10 papers per topic.
Metadata verified against Crossref, Nature, IOP Publishing, or the publisher directly — not guessed. This list is
the citation appendix; the annotated topic-by-topic reading list above remains the one to actually read.*

**How the five topics map to this project:** I — the digitizer and image tools we use. II — the closest
published work to Contribution 1 (measuring signal reliability). III — the closest published work to
Contribution 2 (deciding when *not* to answer). IV — bounds the novelty claim: patient-facing LLM text is an
active field, but not for ECGs specifically. V — general ECG deep-learning context our work sits inside.

### I. ECG digitization — paper/photo to digital signal (11)

[1] K. K. Shivashankara, Deepanshi, A. Mehri Shervedani, G. D. Clifford, M. A. Reyna, and R. Sameni,
"ECG-Image-Kit: a synthetic image generation toolbox to facilitate deep learning-based electrocardiogram
digitization," *Physiological Measurement*, vol. 45, no. 5, p. 055019, 2024.

[2] M. A. Reyna, Deepanshi, J. Weigle, Z. Koscova, K. Campbell, S. Seyedi, A. Elola, A. Bahrami Rad, A. J. Shah,
N. K. Bhatia, G. D. Clifford, and R. Sameni, "Digitization and Classification of ECG Images: The George B. Moody
PhysioNet Challenge 2024," *Computing in Cardiology*, vol. 51, pp. 1–4, 2024.

[3] A. Lence, A. Fall, S. D. Cohen, F. Granese, J.-D. Zucker, J.-E. Salem, and E. Prifti, "ECGtizer: a fully
automated digitizing and signal recovery pipeline for electrocardiograms," *arXiv:2412.12139*, 2024.

[4] M. A. Reyna, Deepanshi, J. Weigle, Z. Koscova, K. Campbell, S. Seyedi, A. Elola, A. Bahrami Rad, A. J. Shah,
N. K. Bhatia, G. D. Clifford, and R. Sameni, "ECG-image-database: large-scale paired ECG images and time-series
with real-world artifacts; a foundation for computerized ECG digitization and analysis," *Physiological
Measurement*, vol. 47, no. 7, p. 075015, 2026.

[5] N. Stenhede, H. Bjørnstad, and S. Ranjbar, "Digitizing paper ECGs at scale: an open-source algorithm for
clinical research," *npj Digital Medicine*, 2026.

[6] D. KumarGarg, D. Thakur, and S. Sharma, "ECG Paper Records Digitization through Image Processing
Techniques," *International Journal of Computer Applications*, vol. 48, no. 13, pp. 35–38, 2012.

[7] R. Patil and R. Karandikar, "Image digitization of discontinuous and degraded electrocardiogram paper
records using an entropy-based bit plane slicing algorithm," *Journal of Electrocardiology*, vol. 51, no. 4,
pp. 707–713, 2018.

[8] M. C. Lewis, M. Maiya, and N. Sampathila, "A Novel Method for the Conversion of Scanned Electrocardiogram
(ECG) Image to Digital Signal," *Advances in Intelligent Systems and Computing*, pp. 363–373, 2017.

[9] V. Randazzo, E. Puleo, A. Paviglianiti, et al., "Development and Validation of an Algorithm for the
Digitization of ECG Paper Images," *Sensors*, vol. 22, no. 19, p. 7138, 2022.

[10] S. Mukherjee and N. Mehendale, "ECG Paper Record Digitization and Diagnosis Using Deep Learning," in *2025
IEEE 4th International Conference for Advancement in Technology (ICONAT)*, 2025, pp. 1–4.

[11] J. V. Vadakkan, M. S. Manikandan, and L. R. Cenkeramaddi, "A Unified ECG Paper Digitization Framework with
R-peak Detection for RR Interval Analysis and Deep ECG Learning Applications," in *2024 16th International
Conference on Electronics, Computers and Artificial Intelligence (ECAI)*, 2024, pp. 1–6.

### II. ECG signal quality assessment (11) ⭐

[12] X. Zhou, X. Zhu, K. Nakamura, and M. Noro, "Electrocardiogram Quality Assessment with a Generalized Deep
Learning Model Assisted by Conditional Generative Adversarial Networks," *Life*, vol. 11, p. 1013, 2021.

[13] Á. Huerta Herraiz, A. Martínez-Rodrigo, V. Bertomeu-González, A. Quesada, J. J. Rieta, and R. Alcaraz, "A
Deep Learning Approach for Featureless Robust Quality Assessment of Intermittent Atrial Fibrillation Recordings
from Portable and Wearable Devices," *Entropy*, vol. 22, no. 7, p. 733, 2020.

[14] N. Seeuws, M. De Vos, and A. Bertrand, "Electrocardiogram Quality Assessment Using Unsupervised Deep
Learning," *IEEE Transactions on Biomedical Engineering*, vol. 69, no. 2, pp. 882–893, 2022.

[15] X. Zhang, J. Li, Z. Cai, L. Zhao, and C. Liu, "Deep Learning-Based Signal Quality Assessment for Wearable
ECGs," *IEEE Instrumentation & Measurement Magazine*, vol. 25, no. 5, pp. 41–52, 2022.

[16] M. Chen, Y. Li, L. Zhang, X. Zhang, J. Gao, Y. Sun, W. Shi, and S. Wei, "Multitask Learning-Based Quality
Assessment and Denoising of Electrocardiogram Signals," *IEEE Transactions on Instrumentation and Measurement*,
vol. 73, pp. 1–13, 2024.

[17] A. Mondal, M. S. Manikandan, and R. B. Pachori, "Deep Spectrogram Feature Based ECG Signal Quality
Assessment for False Alarm Reduction," in *2023 9th International Conference on Signal Processing and
Communication (ICSC)*, 2023, pp. 532–537.

[18] A. Mondal, M. S. Manikandan, and R. B. Pachori, "Automatic ECG signal quality assessment using
convolutional neural networks and derivative ECG signal for false alarm reduction," *Biomedical Signal
Processing and Control*, vol. 108, p. 107876, 2025.

[19] C. Ma, Z. Wang, and L. Zhao, "Deep Learning-based Signal Quality Assessment in Wearable ECG Monitoring," in
*2023 Computing in Cardiology Conference (CinC)*, 2023.

[20] A. Huerta, A. Martinez-Rodrigo, and J. J. Rieta, "ECG Quality Assessment via Deep Learning and Data
Augmentation," in *2021 Computing in Cardiology (CinC)*, 2021, pp. 1–4.

[21] X. Shi, K. Yamamoto, and T. Ohtsuki, "Unsupervised Learning-Based Non-Invasive Fetal ECG Multi-Level
Signal Quality Assessment," *Bioengineering*, vol. 10, no. 1, p. 66, 2023.

[22] Y. Jin, Z. Li, C. Qin, et al., "A novel attentional deep neural network-based assessment method for ECG
quality," *Biomedical Signal Processing and Control*, vol. 79, p. 104064, 2023.

### III. Uncertainty, abstention & selective prediction in clinical ML (10) ⭐⭐

[23] A. Vazhentsev, I. Sviridov, A. Barseghyan, G. Kuzmin, A. Panchenko, A. Nesterov, A. Shelmanov, and M.
Panov, "Uncertainty-aware abstention in medical diagnosis based on medical texts," *npj Artificial
Intelligence*, 2026.

[24] H. Kwon and D.-J. Kim, "Conformal selective prediction with cost-aware deferral for safe clinical triage
under distribution shift," *Scientific Reports*, vol. 16, p. 10016, 2026.

[25] E. Strong, K. Men, and D. Noble, "Trustworthy and Practical AI for Healthcare: A Guided Deferral System
with Large Language Models," *arXiv:2406.07212*, 2024.

[26] S. Jabbour, D. Fouhey, N. Banovic, J. Shepard, E. Kazerooni, M. W. Sjoding, and J. Wiens, "Selective
Prediction Reduces the Negative Effects of Automation Bias Overall but Increases False Negatives,"
*arXiv:2508.07617*, 2025. *(Argues against our Contribution 2 framing — engaged with directly.)*

[27] P. Horton, A. Florea, B. Stringfield, et al., "Conformal validation: A deferral policy using uncertainty
quantification with a human-in-the-loop for model validation," *Machine Learning with Applications*, vol. 22,
p. 100733, 2025.

[28] M. D. Fall, E. C. Faye, et al., "Which Uncertainty Quantification Method in Deep Learning Models for Knee
Osteoarthritis Diagnosis?" in *2025 IEEE Statistical Signal Processing Workshop (SSP)*, 2025, pp. 56–60.

[29] I. Khandokar, O. Farghaly, A. N. Kothari, et al., "Towards Precision Diagnosis: Integrating Lexical
Analysis and Deep Learning for Uncertainty Detection and Quantification in Clinical Reports," in *2024 IEEE
37th International Symposium on Computer-Based Medical Systems (CBMS)*, 2024, pp. 267–272.

[30] X. Li, Q. Zheng, and S. Zhang, "A Reliable Deep Learning Model for ECG Interpretation: Mitigating
Overconfidence and Direct Uncertainty Quantification," *Symmetry*, vol. 17, no. 5, p. 794, 2025.

[31] R. Simão, M. Barandas, D. Belo, and H. Gamboa, "Study of Uncertainty Quantification Using Multi-Label ECG
in Deep Learning Models," in *Proc. 16th Int. Joint Conf. on Biomedical Engineering Systems and Technologies*,
2023, pp. 252–259.

[32] J. J. Garcia, R. Kitzmiller, and A. Krishnamurthy, "Selective classification with machine learning
uncertainty estimates improves ACS prediction: A retrospective study in the prehospital setting," preprint,
2024.

### IV. Patient-facing LLM explanation & medical AI safety (11)

[33] S. Soundarrajan, K. Vartanian, R. Bhakle, T. Katakam, K. Dhanwada, K. S. Randhawa, and N. Puvvala,
"Assessment of patient information guides generated by LLMs for common cardiological procedures," *Global
Cardiology Science & Practice*, vol. 2025, no. 2, p. e202526, 2025.

[34] J. Chan, Y. Han, J. Chen, S. Fang, L. D. Gryboski, A. Lee, S. Tanna, Q. Zhu, Z. Lu, L. L. Wang, and Y. Guo,
"ReLay: Personalized LLM-Generated Plain-Language Summaries for Better Understanding, but at What Cost?"
*arXiv:2605.00468*, 2026.

[35] S. Wang, Z. Tang, H. Yang, Q. Gong, et al., "A novel evaluation benchmark for medical LLMs illuminating
safety and effectiveness in clinical domains," *npj Digital Medicine*, vol. 9, p. 91, 2025.

[36] K. Yang, M. Hong, J. Zhang, Y. Luo, et al., "ECG-LM: Understanding Electrocardiogram with a Large Language
Model," *Health Data Science*, 2025.

[37] A. Soubh, N. Rasenack, N. Haarmann, F. Wiedmann, M. Zabel, K. Schmidt, N. Suliman, and L. Bergau,
"Performance of Vision-Enabled Large Language Models in Image-Based Electrocardiogram Interpretation:
Exploratory Evaluation," *Journal of Medical Internet Research*, vol. 28, p. e86692, 2026.

[38] N. W. Sterling, F. Brann, S. O. Frisch, et al., "Patient-Readable Radiology Report Summaries Generated via
Large Language Model: Safety and Quality," *Journal of Patient Experience*, vol. 11, 2024.

[39] Y. Zhao, Y. Miao, and Y. Luo, "Safety guardrails in patient-facing large language model systems for
chronic disease self-management: a realist review," *International Journal of Medical Informatics*, vol. 218,
p. 106513, 2026.

[40] H. Mondal, G. Gupta, and P. K. Sarangi, "Assessing the Capability of Large Language Model Chatbots in
Generating Plain Language Summaries," *Cureus*, 2025.

[41] V. Ravikumar, "A Comparative Evaluation of Large Language Models for Patient-Facing Medical Question
Answering: Accuracy, Bias, and Clinical Safety Assessment," *International Journal of Artificial Intelligence
in Medicine*, vol. 4, no. 1, pp. 56–83, 2026.

[42] W. Zhong, G. Zheng, Q. Li, et al., "Benchmarking public large language model responses to patient-facing
varicose veins questions: informational quality, verifiability indicators, and readability," *Frontiers in
Public Health*, vol. 14, 2026.

[43] B. Jiang, H. Sun, L. Chen, et al., "Benchmarking publicly accessible large language models for
English-language patient-facing acute pancreatitis information: a cross-sectional study of quality,
transparency, and readability," *Frontiers in Public Health*, vol. 14, 2026.

### V. ECG datasets, fundamentals & deep-learning classification (9)

[44] N. Strodthoff, P. Wagner, T. Schaeffter, and W. Samek, "Deep Learning for ECG Analysis: Benchmarks and
Insights from PTB-XL," *IEEE Journal of Biomedical and Health Informatics*, vol. 25, no. 5, pp. 1519–1528, 2021.

[45] P. Wagner, N. Strodthoff, R.-D. Bousseljot, D. Kreiseler, F. I. Lunze, W. Samek, and T. Schaeffter,
"PTB-XL, a large publicly available electrocardiography dataset," *Scientific Data*, vol. 7, p. 154, 2020.

[46] N. Strodthoff, T. Mehari, C. Nagel, et al., "PTB-XL+, a comprehensive electrocardiographic feature
dataset," *Scientific Data*, 2023.

[47] S. Mihandoost, "A deep neural network model with spectral correlation function for electrocardiogram
classification and diagnosis of atrial fibrillation," *Healthcare Analytics*, vol. 6, p. 100370, 2024.

[48] D. Zhang, S. Yang, X. Yuan, et al., "Interpretable deep learning for automatic diagnosis of 12-lead
electrocardiogram," *iScience*, vol. 24, no. 4, p. 102373, 2021.

[49] C. Lai, S. Zhou, and N. Trayanova, "Heart Rhythm Classification From an Optimal Lead Subset of the 12-lead
Electrocardiogram by Deep Learning," *Circulation*, vol. 142, no. Suppl_3, 2020.

[50] A. Eleyan and E. Alboghbaish, "Electrocardiogram Signals Classification Using Deep-Learning-Based
Incorporated Convolutional Neural Network and Long Short-Term Memory Framework," *Computers*, vol. 13, no. 2,
p. 55, 2024.

[51] Z. Li, D. Zhou, L. Wan, et al., "Heartbeat classification using deep residual convolutional neural network
from 2-lead electrocardiogram," *Journal of Electrocardiology*, vol. 58, pp. 105–112, 2020.

[52] AHA/ACCF/HRS, "Recommendations for the Standardization and Interpretation of the Electrocardiogram
(6-part scientific statement)," *Circulation*, 2009.

---

⚠️ **Honesty notes on this appendix, so it's used correctly:**
- Several entries use "et al." after the third author because the underlying bibliographic record (Crossref)
  did not return the full author list. Before this goes into a formal paper bibliography, pull the complete
  author list from the publisher page for any "et al." entry.
- [26] and [32] are **not peer-reviewed** at time of writing (arXiv preprint and a preprint respectively) —
  disclose that if citing them as evidence rather than as a discussion point.
- This list was compiled for breadth against the guide's "≥10 per topic" requirement. Not every entry is
  equally central to the project's actual argument — Topics II and III contain the papers closest to
  Contributions 1 and 2; Topics I, IV and V are broader context. Weight citations accordingly in the paper
  itself, rather than treating all 52 as equally load-bearing.
