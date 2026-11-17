# Progress Log — MediSense-Cardio

*A step-by-step record of what has been done on this project, in the order it happened. Written in plain language
so it's useful both as a "what did we do" reference and as raw material for the paper's methodology section later.*

*See [PLAN-simple.md](PLAN-simple.md) for the plan and [PLAN.md](PLAN.md) for the technical version with sources.*

---

## Day 0 — Planning (2026-07-26)

1. **Reviewed the original project guide** the user had already written (scope, architecture, tech stack, dataset
   list, dated roadmap). Found two serious problems: the plan to test the safety filter using the filter itself
   (circular — it would always report success), and the claimed research novelty was partly already done by other
   published work.

2. **Searched the published research** to check what was actually new versus already done. Confirmed: ECG
   digitization itself is a solved problem; AI-written plain-language medical summaries already exist for other
   conditions; measuring AI safety filters is a mature field. But nobody has measured **what happens to the
   patient-facing explanation when the input photo is bad** — that gap became the new research focus.

3. **Reframed the research question** to: *how much does a blurry/tilted/dark photo have to degrade before the
   app tells a patient something factually wrong, and can the app detect that it's happening?* Proposed title:
   *"From Paper to Patient: Quantifying and Mitigating Digitization-Induced False Reassurance in Automated ECG
   Explanation."*

4. **User decided to defer the planned 15–20 person comprehension study** (originally the project's main research
   claim) to focus on building first. The reframed research question above replaced it as the paper's contribution,
   since it needs no human participants — provable using free public data alone.

5. **Wrote the corrected plan**, split into two files for different audiences:
   - `docs/PLAN-simple.md` — plain English, for day-to-day use
   - `docs/PLAN.md` — technical version with citations, for the advisor and the paper

6. **Saved project memory** so future sessions have this context without re-explaining it from scratch.

---

## Day 1 — Environment setup (2026-07-26 evening – 2026-07-27)

### Step 1: Checked what tools were already installed

Found: Python 3.14.6 (very new — released recently, so some other tools might not support it yet), Git 2.54.0,
Git LFS 3.7.1 (a Git add-on for handling large files). No Node.js checked yet — not needed for the Python side.

### Step 2: Built the project folder structure

Created these folders inside `D:\Capstone Project`:
```
backend/    — will hold the API code (Phase 4+)
notebooks/  — for quick experiments
data/       — for the downloaded ECG data (kept out of Git — see below)
docs/       — project documents (this file, the plan)
scripts/    — one-off and utility scripts
results/    — experiment outputs
```

### Step 3: Set up Git safely, before any data arrived

Wrote a `.gitignore` file that tells Git to **never track**: the `data/` folder (large downloads), the `venv/`
folder (the Python toolkit — regenerable), `node_modules/` (future frontend), and `.env` files (secrets/API keys).

This had to happen **before** downloading any data — once a large file is inside Git's history, removing it later
is a real headache. Ran `git init` to start version control. *The user chose to handle staging, committing, and
pushing to GitHub themselves — I did not run `git add`/`git commit`/`git push`.*

### Step 4: Created a Python virtual environment ("venv")

A venv is an isolated Python toolbox just for this project, so its packages don't clash with anything else on the
computer. Created at `D:\Capstone Project\venv`.

### Step 5: Installed and tested the core Python toolkit

Installed: `numpy`, `scipy`, `pandas`, `matplotlib` (general number-crunching and plotting), `opencv-python` (image
processing), `wfdb` (reads the standard heart-signal data format), `neurokit2` (extracts heart-rate and interval
measurements from a signal), `python-dotenv` (for secrets management later).

**Result: all installed and imported correctly on the first try.** No issues, despite the very new Python version.

### Step 6: Installed and tested PyTorch (the AI library)

PyTorch is needed because the tool that reads an ECG photo back into numbers uses a trained AI model. This was
flagged in the plan as the single most likely thing to break, since PyTorch support for brand-new Python versions
is usually slow to arrive.

**Result: it worked.** PyTorch 2.13.0 installed with a version built specifically for this Python release, ran a
test calculation correctly. No GPU on this machine, so it runs on the regular processor — slower, but the plan
never called for GPU use anyway. This crossed off the top predicted risk before it caused any delay.

### Step 7: Downloaded one real ECG to test with

Rather than downloading the entire ~3 GB public dataset upfront, fetched a **single** real heart recording
(`00001_lr` — 12 leads, 10 seconds) directly from the free PhysioNet archive, and saved it to `data/sample/`. This
confirmed that downloading from the data source works, without committing to the full download yet.

### Step 8: Looked into optional add-on tools ("plugins")

Checked what extra tools were already available with no installation (a chart-maker, a PDF reader, a slide-deck
maker, a project-notes writer) versus the three specific ones named in the original guide. Verified one of the
three ("Superpowers" — a strict test-first coding routine) is real and installable; one ("gstack") isn't in the
official list and would need a manual download from a stranger's script; the third ("Ruflo") was correctly skipped
in the original guide as overkill for a solo project. Decided: install nothing extra yet — revisit after the first
project review, once real pipeline code is being written.

---

## Day 1 (continued) — Setting up the two ECG tools

The remaining piece needed for today's test: two outside tools, written and published by other researchers, that
this project uses rather than rebuilds from scratch.

- **ECG-Image-Kit** — turns a heart signal into a picture that looks like a real printed ECG page.
- **Open-ECG-Digitizer** — reads that picture back into numbers. (Chosen over two alternative tools because it
  supports the Python version already installed here; the alternatives wanted an older, specific version, which
  would have meant a second, separate install.)

### What went wrong, and how it was fixed

**Problem 1 — an interrupted download corrupted itself.** The first attempt to download Open-ECG-Digitizer got
cut off partway through (it includes two large AI model files, ~90 MB each, and the connection here is slow).
Cutting a download off partway doesn't just leave it incomplete — it can leave the tool's internal bookkeeping
confused about what it actually has, so it reports "done" without the files really being there.

**How this was caught:** re-running the download command kept reporting success while the actual files never
appeared. Rather than keep retrying blindly, checked what the tool itself believed was on disk versus what was
really there — and found a clear mismatch across nearly the whole download, confirming it was corrupted, not just
slow.

**Fix:** deleted the broken copy and started over from scratch, this time letting it run uninterrupted with a much
longer time allowance.

**Problem 2 — a locked file blocked cleanup.** The delete-and-restart didn't fully work either: something on the
computer (most likely antivirus software actively scanning the large files it had just seen appear) was still
holding onto one of the files, so it couldn't be fully removed, and the next download attempt failed too.

**Fix:** rather than fight the lock, started the fresh download under a new folder name instead, sidestepping the
locked one entirely.

Both downloads did eventually finish correctly (confirmed with a hash check, not just "the file exists" — after the
earlier corruption, a size/hash check was worth the extra minute).

---

## Day 1 (continued) — Running the actual test

### Problem 3 — the official picture-generator needs a library that doesn't exist for this Python

The official ECG-Image-Kit tool (the one meant to draw the test picture) turned out to depend on an old, exact
version of a large add-on library (TensorFlow, used only for one cosmetic feature — fake handwritten annotations on
the image). Checked directly: that exact version has **no build at all** for this computer's Python version. Not
slow — genuinely unavailable.

**Decision:** rather than install an entire second, older Python setup just to draw one test picture, wrote a
small, simple stand-in script that draws the ECG signal onto a printed-paper-style grid directly (`scripts/gate2_
walking_skeleton.py`). This skips the cosmetic extras (handwriting, paper wrinkles, stains) that the official tool
adds, but produces the same basic thing the digitizer needs to read: a grid and a trace. Good enough to prove the
pipeline connects. **Note for Week 2:** getting the real, official image generator working (likely needs its own,
separate, older Python environment) is still on the list for when digitizer tools get properly compared and picked.

### Problem 4 — the digitizer also demanded an unrelated, unavailable library

Same story, different tool: the digitizer's code was written so that just *loading* it always tries to load a large
library called Ray (used only for a training feature this project doesn't need — Ray also doesn't support this
Python version). Checked the digitizer's own source code directly and confirmed: the specific piece that needs Ray
is a training-only helper that the actual "read this picture" code path never touches.

**Fix:** made a small, clearly-labeled edit to the local copy of that tool — if Ray isn't available, quietly skip
it instead of refusing to start. This is a change to the downloaded copy of someone else's tool, not to this
project's own code, and it's commented in place explaining exactly why.

### Running the real test

With both stand-ins and fixes in place, ran the digitizer on the hand-drawn test picture. **It worked — produced
real output in 19 seconds**, no crash, no silent failure this time.

**What the numbers showed:**
- All 12 leads (the 12 different views of the heart an ECG records) came back with real data, not empty.
- One expected snag: the digitizer tries to recognize which standard "page layout" a picture uses, and the simple
  stand-in picture didn't exactly match any of its known layouts. It fell back to a reasonable default, which meant
  it only recovered the correct time segment for each lead, not the full recording.
- For the one lead checked directly against the real answer (Lead II, the most commonly used one): the recovered
  chunk covered about 2.4 seconds, and it found 2 heartbeats in that stretch — which works out to a heart rate in
  the right neighborhood, but 2 beats is too few to call it a solid measurement. The real answer for comparison:
  63.9 beats per minute, from the full 10-second recording.
- The recovered heights of the heartbeat signal were noticeably smaller than the real ones (roughly a third the
  size at the peak) — a sign that the digitizer's scale reading was somewhat off, which is expected in a way, since
  it was working from a simplified test picture, not one drawn the way it was actually trained to expect.

**Bottom line for today's test:** the goal was never "get an accurate reading today" — the plan's own goal for this
step was just proving a picture can go in and numbers can come out, on this computer, without anything crashing.
**That's now proven.** The actual accuracy work — using the real image-generation tool and testing on many records,
not just one hand-drawn example — is Week 2 and Phase 2 work, already scheduled in the plan.

---

## What's proven so far

- ✅ Every core Python tool this project needs installs and runs correctly, including the one considered highest-risk
  (the AI library needed by the digitizer).
- ✅ Downloading real ECG data from the public archive works.
- ✅ The project folder and version control are set up safely.
- ✅ **The full pipeline runs end to end**: a real heart recording → a picture of it → numbers read back out of that
  picture → compared against the real answer. Two real snags were hit and fixed along the way (see above), both
  documented and both understood, not papered over.
- ⚠️ Today's specific numbers aren't an accuracy result — they're a connectivity proof. The test picture was a
  simplified stand-in, not the real tool the project will ultimately use, so the numbers being a bit off was
  expected and doesn't say anything yet about how good the real pipeline will be.

---

## Day 1 (continued) — Tidying up before moving on

Before starting the next real step, checked the project folder itself for mess — worth doing periodically, not
just at the end.

**Found and fixed:**
- The first, broken attempt at downloading the digitizer tool (from the corruption problem above) was still
  sitting on disk, empty and useless. Deleted it, and renamed the working copy back to a clean name (it had picked
  up an awkward "-v2" suffix purely from the debugging process, not because it means anything).
- **A real gap in `.gitignore`**: it was written on Day 0, before the two outside tools existed, so it never
  learned to exclude them. Left as-is, this would have let ~900 MB of someone else's code and large AI model
  files get pulled into this project's own saved history the next time everything gets uploaded — plus a messier
  problem where a downloaded tool's own internal history would end up nested inside this project's. Fixed by
  adding `scripts/tools/` to the ignore list, the same way `data/` was already protected on Day 0.
- Also excluded a folder that's just this AI assistant's own local settings (`.claude/`) — machine-specific,
  not something that belongs in the project's saved history either.

Confirmed clean afterward: nothing outside `docs/`, `scripts/` (just the two real code files), and `.gitignore`
itself shows up as unprotected. Plenty of disk space left (159 GB free).

---

## Day 2 — Getting the real picture-drawing tool working (2026-07-28)

Following up on the note from Day 1: the official picture-drawing tool needed old software that doesn't exist for
this computer's main Python. Today's job was fixing that properly, since the earlier test used a simplified
stand-in.

**Step 1 — added a second, separate copy of Python, just for this one tool.** Rather than touch the main Python
already set up (which everything else depends on), installed **Python 3.11** side by side. Nothing else on this
computer changed — this is purely an extra toolbox that only this one tool uses, kept in its own separate
project folder (`venv-ecg-image-kit`) so it can never mix with the main setup.

**Step 2 — a false "it worked."** The first attempt to set up this tool's add-ons looked like it succeeded (the
summary said so), but checking directly afterward showed the main missing piece hadn't actually installed. The
real problem only showed up by reading the actual installation log line by line: the setup had silently stopped
partway through, and the way I'd checked it the first time — piping the output through a "just show me the last
bit" command — hid that failure. **Lesson applied:** don't trust a shortened summary of a long-running setup step;
check the real, complete result.

**Step 3 — found the actual blocker, and fixed it the same way as before.** The real problem: this tool has one
extra, optional feature — adding fake handwritten notes onto the picture, to make it look more like a real messy
scan — and *that* feature needs the same broken old software as before, plus another program (a code compiler)
that isn't installed on this computer either.

Checked directly in the tool's own code: that optional feature is the *only* thing needing this broken software,
and it's not something this project uses or needs. So, same fix as Day 1's digitizer problem — told the tool to
only load that feature if someone actually asks for handwriting, which nothing here does. Then installed
everything else the tool needs, skipping just that one optional piece.

**Step 4 — it worked, genuinely this time.** Ran the real tool on the sample heart recording. It produced a
proper-looking picture: red grid lines exactly like a real hospital printout, all 12 signal traces correctly
labelled, a calibration mark at the start of each row (a standard feature real ECG machines print), and a longer
strip at the bottom — this is a correctly formatted page, not the simplified stand-in from Day 1.

**Why this matters:** the digitizer (the tool that reads a picture back into numbers) is trained to recognise
standard page formats like this one. Day 1's stand-in didn't quite match any of its known formats, so it guessed
and only partly succeeded. This real picture should let it recognise the format properly instead of guessing —
worth re-testing.

**What's now set up, for future reference:**
- `venv-ecg-image-kit/` — the second, separate Python toolbox, just for this tool.
- `scripts/tools/ecg-image-kit/codes/ecg-image-generator/requirements-core.txt` — the trimmed list of add-ons
  actually installed (everything except the handwriting-only pieces).
- A small, clearly-labelled edit inside the tool's own downloaded copy of its code, so it doesn't demand the
  broken software unless the handwriting feature is actually turned on.
- Real output saved at `results/real_ecg_image_kit_test/`.

### Re-testing the digitizer on the real picture

With the real, correctly formatted picture in hand, re-ran yesterday's test — same reading tool, same setup, only
the picture changed.

**The layout-guessing problem from yesterday is gone.** Yesterday the tool couldn't recognise the hand-drawn
stand-in and had to guess a default format. This time it **correctly recognised the real page format**, with a
low "how well did this match" score (0.094 — a genuine confident match, not a fallback).

**The numbers are dramatically better:**

| | Yesterday (stand-in picture) | Today (real picture) |
|---|---|---|
| How much of the recording it read | ~2.4 seconds out of 10 | **Full 10 seconds** |
| Heartbeats found | 2 (too few to trust) | **10 — matches the real count exactly** |
| Heart rate | couldn't calculate | **63.8 bpm vs. the true 63.9 bpm — 0.1 bpm off** |
| Signal height (a scale check) | about 1/3 the real size | **about 90% of the real size — close** |

**Caveats, stated honestly:** this is still just **one recording, one lead** — not yet a real accuracy test. The
0.1 bpm result is a genuinely strong sign, not proof the whole pipeline is accurate. The proper test — many
recordings, all 12 leads, deliberately damaged photos — is still Week 2 / Phase 2 work per the plan. But this
result confirms the earlier problem really was the stand-in picture, not the reading tool itself, which is exactly
what needed confirming before trusting the real accuracy work to come.

---

## Day 3 — Testing on more than one recording (2026-08-10)

Yesterday's excellent result was one recording. Before trusting the tools further, tested on **6 real recordings**
instead of one — still small, but enough to check whether yesterday's result was typical or a lucky exception.

**Setup:** downloaded 5 more real heart recordings from the free archive (6 total now), drew all 6 as proper ECG
pictures using the real picture-drawing tool, then read all 6 back with the real digitizer.

**Result: 5 out of 6 were excellent — genuinely close to the true numbers, not just roughly right:**

| Recording | True heart rate | What the tool read | How far off |
|---|---|---|---|
| 00001 | 63.9 bpm | 63.8 bpm | 0.1 bpm |
| 00003 | 63.7 bpm | 63.7 bpm | 0.0 bpm |
| 00004 | 74.7 bpm | 74.9 bpm | 0.2 bpm |
| 00005 | 66.4 bpm | 66.5 bpm | 0.1 bpm |
| 00006 | 83.1 bpm | 83.0 bpm | 0.1 bpm |
| **00002** | **47.6 bpm** | **couldn't get a reliable reading** | — |

Average difference on the 5 good ones: about **0.1 beats per minute** — genuinely accurate, not a fluke.

**The one honest failure, looked into rather than brushed aside:** recording 00002 only got a tiny sliver of data
read back (2.5 seconds instead of the full 10), so no reliable heart rate could be calculated. Checked the actual
picture the tool drew for this one — **it looks completely normal**, same clean grid, same correct layout as the
other five. So the problem isn't a bad picture; something inside the reading tool's own logic went wrong on this
particular recording, for a reason not yet understood.

**One detail worth flagging for later, not chasing down right now:** the digitizer reports its own "how well did
this match a known page layout" score for every image. Recording 00002 had the **worst score of all six** (0.31,
versus 0.09–0.23 for the five that worked). That's only one data point, far too little to draw a conclusion from —
but if that score genuinely predicts failure, it's exactly the kind of early-warning signal this project's second
contribution is about. Worth watching for during the real Week 2/Phase 2 testing, not something to chase down now.

**What this means:** the tools are genuinely working well, not just on one lucky example — and the one failure is
real, honestly reported, and not hidden. A 5/6 success rate on 6 hand-picked, undamaged, real recordings is a
reasonable starting point; Week 2's real test (many more recordings, deliberately damaged photos) will show the
true picture.

---

## Day 3 (continued) — A demo notebook for the guide

Built `colab/MediSense_Cardio_Demo.ipynb` — a self-contained notebook that reproduces today's real-tool pipeline
test (6 recordings, photo-drawing, digitizing, comparison against the true answer) for opening directly in Google
Colab. No local setup needed to view it — open the link, run all cells, everything downloads and runs on Google's
own fast servers.

Same two patches as the local setup (deferred handwriting import, optional ray import) are baked in, since Colab
may or may not hit the same old-library problems this computer did. Ends with a plain-language summary, including
the one honest failure case (`00002_lr`), not just the good results.

**To use it:** upload to Google Drive or open directly in Colab, then share the Colab link with the guide.

**Update:** the first version hit two real problems when actually run in Colab (not something visible from
building it locally):
1. **Step 2 install was very slow** — the old pinned package versions (needed locally) fought against Colab's
   already-installed newer versions during pip's dependency resolution. Fixed by dropping the version pins so
   pip reuses what Colab already has.
2. **Step 1 failed outright** — `ValueError: The binary mode of fromstring is removed, use frombuffer instead`,
   from inside the `wfdb` library's own code, triggered by Colab's newer numpy. Reproduced this exact error
   locally to confirm the cause before fixing it, then added a small, targeted patch redirecting the old call to
   numpy's current replacement (`frombuffer`) — without downgrading numpy, which would have reintroduced problem 1.

Rather than keep layering patches on the same file, rebuilt clean as `colab/MediSense_Cardio_Demo_v2.ipynb` with
both fixes designed in from the start. Old file deleted so there's no ambiguity about which version is current.

**A third problem, same family:** the picture-drawing step failed too — another old library (`imgaug`, unmaintained
since around 2020) crashing on the same kind of removed-numpy-feature issue. Checked directly whether this library
was actually needed at all: it wasn't — it was imported but never once used in that file. Removed the dead import
outright and dropped it from the install list, rather than trying to patch a library we don't even need.

**That third fix was itself incomplete** — a genuine mistake worth recording. `imgaug` was removed from the
install list after checking only *one* file. In fact **three** files import it. Two (`helper_functions.py`,
`CreasesWrinkles/creases.py`) never actually use it — dead imports, safe to delete. But the third
(`ImageAugmentation/augment.py`) genuinely does use it, so removing the library outright broke image generation
with a new error. The correct fix: delete the two dead imports, and *defer* the real one inside the function that
uses it (`get_augment()`), which only runs when `--augment` is explicitly passed — never during clean image
generation.

**How this was finally verified properly, rather than shipped on hope.** After three failed attempts, the approach
changed from "apply fix, send, see what happens" to actually reproducing Colab's conditions locally first:
- The main local environment happens to have the *same* new numpy that breaks things in Colab — so it reproduces
  the failure faithfully.
- Wrote a checker that pulls the patch code **out of the notebook itself**, restores a **pristine** copy of the
  tool from git history (the local copy had earlier edits, which would have made the test lie), runs the patch
  code verbatim, then actually generates images with `imgaug` absent.
- That checker immediately caught a further real bug: running the patch **twice** corrupted the file. Fixed by
  making every patch guarded/idempotent — re-running the cell is now harmless, which matters because re-running
  cells is a completely normal thing to do in a notebook.
- Final state: pristine copy → patch runs → patch runs again (all steps correctly skip) → all four files still
  parse as valid Python → all 6 images generate → exit code 0.

**My own mistake while applying an earlier fix, caught before it reached the user:** the automated edit I used to apply
this patch introduced a genuine bug of its own — a stray line break landed inside a piece of code text, which
would have caused a new error the moment that cell ran. Caught this by directly inspecting the raw file content
rather than trusting that the edit had worked, fixed it properly, and then went further: wrote a small checker
that actually tests every code cell in the notebook for valid Python syntax before considering it done, instead of
just checking the file opens as valid JSON. All 12 code cells pass that check now.

---

## Day 4 — Downloading the full dataset (2026-08-15 – 2026-08-17)

Up to now everything ran on 6 hand-picked recordings. The real experiments need the whole PTB-XL collection
(21,799 recordings), so this was the job: get all of it, intact.

### The earlier attempt turned out to be broken

A partial download from Day 3 (~804 MB) was still sitting on disk. Checked whether it was usable before building
on it — it wasn't: the file couldn't be opened as an archive at all ("End of Central Directory record could not
be found"), which is what a half-finished download looks like. Same lesson as the Day 1 corruption: **an
interrupted download leaves a file that exists but is useless, and only an actual integrity check reveals that.**

### Browser vs. command line

First tried downloading through the web browser. It worked, but crawled — **55.9 KB/s, with 9 hours remaining**.
Switched to a command-line download tool (`curl`) instead, which had already been running noticeably faster on
this same connection. The deciding advantage wasn't only speed: `curl` can **resume** a broken download from
exactly where it stopped, and it writes straight into the project's data folder, so there's no separate step of
moving a finished file into place.

### Five connection drops, no lost work

The download failed and had to be resumed **five times** — the connection here resets rather than staying up for
a 1.8 GB transfer. It broke at roughly 17 MB, 518 MB, 545 MB, 1600 MB and 1730 MB. Each restart picked up from
the exact byte it had reached, so nothing already downloaded was re-fetched.

Progress was tracked automatically with a watcher that reported every 150 MB with a timestamp, so the download
could be left running unattended and checked later, rather than being watched.

**One drop behaved differently and is worth recording:** near the end the transfer *stalled* — the process was
still alive and reported no error, but the file stopped growing for about seven minutes. A stall looks exactly
like slow progress if you only check "is it still running", and it's only visible if you compare the file size
against the last time you looked. It eventually failed on its own with the same connection-reset error.

### Verified, not assumed

The finished file is **1,839,504,686 bytes**. Rather than trusting that the download "finished", checked it
properly: the archive opens cleanly, its own internal integrity check passes with no corrupt entries, and it
contains **87,204 files** — including the recordings at both sampling rates (`records100/`, `records500/`) and
the two label files the project needs (`ptbxl_database.csv`, `scp_statements.csv`).

Stored at `data/ptbxl/ptbxl.zip`, inside the folder Git was told to ignore on Day 0 — so a 1.8 GB file never
entered the project's saved history.

---

## Day 5 — Review 1 slides, and fixing the reference list (2026-08-19)

### Building the review deck

Built a 17-slide presentation for Review 1, structured directly around the three things being marked:
**Objectives (3) · Problem Survey (3) · Subject Knowledge (4)**. Each slide carries a badge showing which
component it serves, so the marker can see the mapping without being told.

Two deliberate content decisions:
- **The Problem Survey section shows our own original novelty claim being disproven** (the Day 0 finding that
  parts of it were already published). A literature survey that finds nothing looks like a survey that wasn't
  done; showing the claim was tested and then narrowed is the actual evidence of having surveyed.
- **The results slide includes the failed recording** (`00002_lr`), not just the five that worked — and uses it
  to introduce Contribution 2, since that recording had the worst layout-match confidence score of the six.

### Checking the slides — two different methods, two different bug types

The normal way to check slides is to convert them to images and look at them. The tool that usually does that
(LibreOffice) isn't installed here, so the first pass was a **written checker** instead: a script that measures
every element's position and reports anything off the edge of the slide, overlapping something else, or holding
more text than it has room for.

That checker found a **genuinely serious bug**: six slide titles were being drawn in *white text on a white
background* — completely invisible — because two arguments had been passed in the wrong order. It also caught
titles running underneath the corner badges.

Then found that **Microsoft PowerPoint itself was installed**, which meant the slides could be exported as
images after all — and inspected in the exact program they'll be presented from. Looking at them caught **four
more problems the measuring script could not detect**: badge text wrapping onto a second line and spilling out
of its shape, a caption colliding with the page footer, a text block floating in the middle of its box instead
of sitting at the top, and a decorative graphic that was simply ugly.

**Worth recording as a lesson:** the two checks are not substitutes. The written checker found an error that
looking at a picture would arguably have missed (invisible text looks like *no* text — easy to read past),
while looking at the slides found four things no measurement would ever flag. Both were needed.

### Correcting the reference list

Checked each candidate journal's current scope and recent ECG/LLM papers. This turned up a **real error in our
own reference list**: two of the most important sources were being cited as preprints when both had since been
published in a peer-reviewed journal — and, as it happens, *the same* journal:

| Source | Was cited as | Actually published in |
|---|---|---|
| ECG-Image-Kit (our image generator) | arXiv preprint | *Physiological Measurement* **45**(5) 055019 (2024) |
| ECG-Image-Database (degradation evidence) | arXiv preprint | *Physiological Measurement* **47**(7) 075015 (2026) |

Two further entries were listed only by a link to PubMed Central — which is a **repository, not a journal**, so
those citations had no venue at all. Both resolved: *Global Cardiology Science & Practice* (2025) and
*Entropy* (2020).

All four are now corrected in [REFERENCES.md](REFERENCES.md) and [PLAN.md](PLAN.md), and the corrected versions
are what appear on the deck's reference slides.

**This also changed where the paper should be sent.** *Physiological Measurement* had been ranked sixth of seven
candidate journals; it should be first — it published both of the imaging tools this project is built on, and
its stated scope explicitly covers signal quality assessment and validation, which is precisely Contribution 2.
One deadline finding too: the relevant conference (Computing in Cardiology) closed submissions for 2026 in
April, so **CinC 2027** is the realistic target — which suits the Phase 2/3 timeline better anyway.

---

## Day 6 — Expanding and hardening the Review 1 deck (2026-08-20 – 2026-08-22)

The 17-slide deck from Day 5 covered the required rubric, but the guide asked for more depth: every literature
topic covered individually (not just the two closest ones), the research-gap claim actually justified rather
than asserted, worked examples of the real techniques used, and a training/testing section. Also asked, twice,
for larger text — the first font pass didn't fully take.

**Grew to 38 slides.** Added a dedicated closest-work slide for each of the three literature topics that hadn't
had one; a four-card slide arguing *why* the research gap is real and falsifiable (not just naming it); a
coverage-matrix table showing the gap claim checked against all 52 papers, not assumed; four "technique in
detail" slides with actual algorithms and worked numeric examples (perspective-correction homography, a
Pan–Tompkins-style R-peak detector traced through a real recording, an LLM-as-judge worked example, and the
quality-proxy calibration math); and an explicit training/testing slide stating plainly that no model is trained
in this project, with the one real train/test split (70/30) that does exist.

**The font pass exposed a real gap in the tooling, not just the text.** The first attempt bumped one font
parameter but missed a second, more heavily-used one entirely — 24 separate text blocks across the deck were
silently untouched. Caught only by re-deriving the count directly from the source rather than trusting that
"a font pass" had been done.

**Bigger text broke layout in ways the automatic checker didn't catch.** Larger text needs more room, and several
boxes that fit before didn't anymore — most seriously, three separate code-example boxes had their last line
spilling silently past the box's bottom edge in the actual rendered slide, invisible to the geometry checker's
estimate but plainly visible once the slides were actually looked at. Same lesson as Day 5, learned again: an
automated check and an actual look at the rendered output catch different classes of bug, and neither substitutes
for the other.

**Found and fixed a broken cross-reference the hard way.** Asked directly "are the slides related" — checking
that prompted tracing every internal callback in the deck, which surfaced a real bug: two slides pointed back to
"the Objectives slide" and its worked example (a true 480 ms QT interval misread as 420 ms), but that slide had
been quietly dropped during the Day 5 restructuring around the rubric sections, while the two references to it
were never updated. Restored the missing slide (now "The Problem, Concretely," slide 3) rather than just deleting
the dangling references, since the worked example is what makes the whole research-gap argument concrete.

Final state: 38 slides, rebuilt and re-verified by rendering every slide through PowerPoint itself, not just
the position-checking script.

---

## Review 1 — completed (2026-09-17)

Confirmed by the user that Review 1 has taken place. The guide's instruction: continue the project, after first
reviewing what has been done so far. No outcome, grade, or specific feedback has been recorded here yet — worth
adding once known, since it may change what Week 2 actually needs to prioritize.

---

## Day 7 — Building the degradation harness and running the pilot (2026-09-17 – 2026-09-18)

The guide's instruction after Review 1 was to continue the project and then write the research paper. The
agreed order: **run the real experiment first, write Results from real numbers second.**

**Moved everything to Google Colab.** The local `venv` turned out to be broken (its `pyvenv.cfg` pointed at
another machine's user profile), so the harness was built as Colab notebooks instead of local scripts. The
same tool patches proven on Day 2–3 (ecg-image-kit, Open-ECG-Digitizer, wfdb) were reused unchanged.

**Pilot (`colab/MediSense_Cardio_Harness_v1.ipynb`):** 10 recordings × 1 damage type (blur) × 6 levels = 60
tests. It proved the whole chain — stratified sample → fetch → render → degrade → digitize → compare — works
end to end, and it produced the number the plan asked for: **~20 s/image on a T4 GPU** (CPU: ~120–150 s/image).
Heart-rate error rose with blur exactly as hypothesised (0.09 bpm clean → 8.8 bpm at the heaviest blur).

**A real bug found and fixed:** the first digitizer crash ("weights only load failed") looked like a PyTorch
version problem. The true cause was that `git-lfs` was not installed on Colab, so the model weight files were
tiny pointer stubs. Fix: `apt-get install git-lfs` before `git lfs pull`.

## Day 8 — The full sweep, and what went wrong on the way (2026-09-18 – 2026-09-20)

**Design (`colab/MediSense_Cardio_FullSweep_v1.ipynb`):** a resumable notebook. Six damage types (blur,
rotation, JPEG compression, resolution, brightness/shadow, grid contrast) × 5 levels + 1 clean = **31 tests
per record**. Everything that must survive a Colab disconnect lives on Google Drive
(`MyDrive/MediSense-Cardio-Study/`): the fixed record sample, the rendered clean images and `results.csv`,
saved after every small batch.

**Scope had to shrink twice, because time and free GPU are limited.** 500 records × 31 = 15,500 tests ≈ 87 h
of GPU time — impossible inside Colab's session limits and the 2026-09-28 deadline. Cut to 150 records, then
to **50 records (25 normal / 25 abnormal) = 1,550 tests ≈ 10.5 h on GPU**. The 50 are a fixed, reproducible
subset (seed 42) of a 500-record pool stored on Drive, so scope can be widened later without re-drawing.
This trim was decided up front, not after seeing results, and must be stated in the paper.

**Problems hit, and what they taught:**
- **Wrong scope silently ran.** Step 3 copied *all* cached images from Drive, so the variant list briefly
  covered 500 records instead of 150. Caught from the printed count ("15500 total variants"), fixed by building
  the list only from the current sample's record ids, before any wasted GPU time.
- **Runtime on CPU by mistake (three times).** Every newly uploaded notebook defaults to CPU; the notebook
  prints `Using device:` and that line must be checked before trusting a run.
- **Free-tier GPU quota is unreliable.** Colab cut off GPU access after a few hours ("You cannot currently
  connect to a GPU due to usage limits"). Decisions made with the user: never pay or silently fall back to CPU
  without asking; retry later; when still blocked, use a **second Google account** (the study folder was shared
  to it as Editor and added as a Drive shortcut).
- **Apparent data loss (false alarm, but instructive).** A results file that looked stale suggested ~500 tests
  had vanished. It was a lagging view; the file was complete. But the scare led to **verified saving**: every
  batch is written to a temp file, swapped in atomically, backed up with a timestamp, and **read back from
  Drive** with an assertion that the row counts match.
- **Two runs writing the same file.** The CPU run (account 1) and GPU run (account 2) worked on the same
  remaining tests and the same `results.csv`, which would have let one overwrite the other. The CPU run was
  shut down the moment the GPU run started.
- **Editing Colab cells by hand in the browser corrupted them repeatedly** (autocomplete popups, misplaced
  clicks). Rule adopted: build the notebook locally, syntax-check it (and dry-run on mock data), upload the file.

**The sweep finished: 1,550 of 1,550 tests done and saved** (the GPU session ran ≈ 5 h on a T4 at ~22–24 s/image, after ~35 min of CPU-only progress earlier). The
results file also held 138 stray rows from earlier scope changes; they are removed in the clean file.

## Day 9 — First analysis of the sweep (2026-09-20)

Three analysis notebooks, all reading from Drive and printing plain text (`colab/MediSense_Cardio_Analysis_*`).
Full numbers and caveats are in [SWEEP-RESULTS.md](SWEEP-RESULTS.md); the short version:

- **Part 1 — cleaning.** 1,688 rows → 1,550 (138 stray removed, 0 duplicates, all expected tests present).
  Saved `results_clean.csv`.
- **Part 1b — failing records.** **6 of the 50 records give no readable signal in most of their versions**
  (00102, 08150, 13316, 00053, 18151, 19059: 18–31 of 31 versions unreadable); **4 of them (00102, 08150, 13316,
  19059) fail even on the clean picture**, while 00053 and 18151 read fine when clean. 163 of 1,550 tests
  (10.5 %) are unreadable overall, almost all "no digitized signal at all". It is a per-record problem, not
  caused by the damage. (An earlier summary in the session wrongly said all 6 fail on the clean picture; corrected.) Record 00102 also has no measurable
  ground-truth heart rate. Plan: report these separately; use the **44 reliable records** for damage curves.
- **Part 2 — patient-facing outcome (heart-rate version).** Each test becomes correct / false alarm / **false
  reassurance** / wrong-abnormal / silent drop, using AHA/ACC rate ranges (slow <60, normal 60–100, fast >100).
  Clean baseline: 0 wrong of 44. **Real false reassurance (reading off by >10 bpm) happened only at level 5 of
  blur and resolution** (6 events); 3 more "events" were threshold artefacts (e.g. 59.7 read as 60.0).
  **Rotation causes silent drops** (4 of 44 unreadable at the worst level) and no wrong answers. JPEG, grid
  contrast and brightness showed no meaningful effect.

- **Part 3 — paper figures.** Three IEEE-sized figures (error vs level, wrongly-reassured / silent-drop
  heatmaps, failing records) saved to `MyDrive/MediSense-Cardio-Study/figures/` (PNG + PDF). Checked visually on
  mock data first, then on the real data; the numbers in the heatmaps match the Part 2 tables. While making Figure 3
  I also caught and corrected my own earlier misstatement about the failing records (see Part 1b).

**Honest limits.** Only 9 reliable records have an abnormal rate in the truth, so percentages carry wide
intervals. This is heart rate only: PR/QRS/QT and diagnosis-level false reassurance (e.g. a missed heart attack)
are **not** measured, because the digitized signals were not saved. Contribution 2 (the no-reference quality
proxy) has **not been started**.

---

## Day 10 — Writing the full paper, then a second sweep for PR/QRS/QT/QTc (2026-09-24 – 2026-09-25)

**Writing the paper (Sep 24).** Wrote every remaining section — Abstract, Introduction, Related Work, Method,
Results, Discussion, Limitations, Conclusion — as a standard IEEE `IEEEtran` conference paper, using the real
numbers from `SWEEP-RESULTS.md`, the three figures, and the 52 already-verified references. Assembled into
`docs/paper/main.tex` + `references.bib`, uploaded to Overleaf, and compiled clean on the first try. Title and
author fields left as placeholders — the user said to fill those in later.

**Deciding to close the biggest gap (Sep 24 evening).** The single largest limitation — heart rate only, no
PR/QRS/QT/QTc — was fixable: v1 never saved the digitized signal, only the heart rate computed from it. Built
`colab/MediSense_Cardio_FullSweep_v2_Intervals.ipynb`, which re-runs digitization from scratch on the **same**
50-record sample (same pool, same seed) but keeps the signal long enough to extract PR, QRS, QT and QTc via
NeuroKit2 delineation, plus patient sex (for the AHA/ACCF/HRS sex-specific QTc threshold). Unit-tested the
interval-extraction logic locally on a synthetic ECG and dry-ran the real `compute_metrics` function against mock
data before spending any GPU time — both passed. Writes to a separate `results_v2.csv` so v1's completed,
verified 1,550-row `results.csv` could never be touched no matter what went wrong.

**Running it (Sep 24 night – Sep 25 morning) — and it was a rough night.**
- First account hit the same free-GPU quota wall as v1, at 900/1,550 rows. Confirmed via a checkpoint verify
  read-back, not just the printed log.
- Switched to the second Google account (same one that ran v1's GPU job), which turned out to have **Colab
  Pro** — better GPU availability.
- The Drive mount was flaky under that account: almost every checkpoint save landed as a stray duplicate
  `results_v2.csv` at the account's Drive **root** instead of the correct shared study folder — happened
  repeatedly, not a one-off. Each time, verified which file was actually the most-advanced (by row count, not
  by trusting the folder icon alone), downloaded and diffed row counts to confirm the strays were harmless
  earlier snapshots, then deleted them. This happened **twice** — once mid-run (480→980 rows) and again
  overnight (980→1,550 rows, ~20 stray copies).
- The browser's connection to the Colab kernel also got stuck once ("Resuming execution" hung indefinitely on
  every reconnect attempt, even in fresh tabs) — turned out to be the notebook's own accumulated output being
  too large to replay, not the kernel being dead (confirmed the kernel was still executing via Colab's own
  "Manage sessions" panel). Fixed by disconnecting and deleting the runtime, clearing all cell outputs, and
  restarting clean.
- **Woke up to `results_v2.csv` at 1,550/1,550 rows — the full re-run completed overnight.** Verified 50 unique
  records, 1,550 unique variant IDs, no gaps or duplicates. Saved a local copy to
  `results/v2_intervals/results_v2.csv`.

**Local interval analysis (Sep 25) — and catching a real measurement problem before it went in the paper.**
Wrote `scripts/analysis/analyze_v2_intervals.py` (no GPU needed) reconstructing the same 50-record sample
locally to join in record labels, then computing the same style of cleaning/outcome analysis as Part 1/1b/2 but
for PR/QRS/QT/QTc. First pass found the QTc-based "false reassurance" count implausibly high (39 events) — and
one record was flagged as a false reassurance on its own **undamaged clean image**, which is impossible if the
measurement were only capturing degradation. Root cause: delineating P/T-wave boundaries from a reconstructed
signal is much noisier than counting R-peaks for heart rate — ground truth and digitized delineation disagree
by a median of ~20 ms even on the clean image (vs ~0.1 bpm for heart rate). Fixed by requiring a QTc
false-reassurance event to count as real only if the same record's own clean image was classified correctly —
that dropped the count from 39 to **6 real events**, spread thin with no clear severity pattern (unlike heart
rate's sharply concentrated 2/9 and 4/9 at the worst level of exactly two axes). The **error-magnitude** trend
(not the threshold-crossing outcome) held up fine without correction and confirms the same blur/resolution
pattern heart rate showed.

**A second honest finding, not swept under the rug:** none of the four records that failed to digitize on their
clean image in the original v1 run failed in this v2 run — a different single record (`15192_lr`) failed instead.
Cause: the sweep notebook clones the digitizer tool fresh each session without pinning a commit, so the v1 run
(Sep 18–20) and v2 run (Sep 24–25) likely used different versions of the upstream tool. Documented as a new,
explicit limitation rather than quietly reconciled.

**Paper updated and republished.** Added a new Method subsection (interval extraction methodology), a new
Results subsection (both the robust error-magnitude finding and the corrected, appropriately-cautious QTc
finding), a new Discussion subsection on measurement precision, two new Limitations items (the baseline noise
floor / exploratory QTc result, and the unpinned-digitizer reproducibility gap), and a revised Future Work list.
Re-verified brace balance and all citation keys, re-uploaded `main.tex` to Overleaf (via the user's own Chrome,
since the browser pane's Overleaf session had gotten mixed up between the two Google accounts), and recompiled
clean — 10 pages, no errors.

**Where the fresh problems came from, for next time:** every headache tonight was Google Colab's free-tier
environment (GPU quota, Drive mount flakiness, stuck reconnects) or an unpinned dependency — never the actual
analysis code, which passed its dry-run tests and ran correctly the first time once given a working GPU
session.

---

## What's next

**Status as of 2026-09-25: the paper is fully written and compiling cleanly (10 pages), covering both the
heart-rate and the new PR/QRS/QT/QTc results. Nothing experimental is blocking submission anymore.**

1. **Fill in the title and author names** in `docs/paper/main.tex` — still literal `[TODO]` placeholders, on
   the user's own "later."
2. **A full human read-through**, by the user and/or teammates, of the compiled PDF — nobody has read the whole
   paper end to end yet, and this matters more now than before given how much changed in Day 10.
3. **Confirm with the guide** that the reframed research question (image degradation → false reassurance) is
   actually approved, not just proposed in `PLAN.md` back in July — open risk, not verified anywhere in the repo.
4. Optional, likely out of scope for the deadline: pin the digitizer to a fixed commit and re-run once more so
   heart-rate and interval results share the exact same reliable-record set (see Day 10's reproducibility
   finding); improve interval delineation precision to shrink the ~20 ms baseline noise floor; build Contribution
   2 (the no-reference quality proxy — still not started); look at why `15192_lr` and the original v1 failing
   records behave differently.
5. Get the guide's Review 1 feedback recorded here, and decide on MIMIC (skip, or start the paperwork).
6. Housekeeping: the repo has no commits yet (everything is untracked); consider committing `docs/`, `colab/`,
   `scripts/` and `results/v2_intervals/` once the user agrees.

## Day 10 addendum (2026-09-25) — per-test comparison of the two sweeps

Downloaded the Sweep-1 results file and compared it with Sweep 2 test by test (`scripts/analysis/v1_v2_per_test_comparison.py`).
- Ground truth identical in all 1,397 tests where both had one. Of 1,367 tests readable in both sweeps, 1,357 (99.3%) agree within 0.15 bpm; max difference 5.9 bpm.
- The six real heart-rate false-reassurance events are **the same six tests** in both sweeps.
- Only seven records changed readability: six that failed in Sweep 1 (00102, 08150, 13316, 19059, 00053, 18151) became readable; 15192 became unreadable. That explains all 173 status changes.
- **Correction:** Sweep 2 is a computational repeat, not an independent replication. Earlier wording ("independent confirmation", "replicates") was removed from the conference paper (`docs/paper/main.tex`) and the journal draft (`docs/journal/`). The evidence for the effect is still one 50-record sample.
- Journal manuscript now has all sections 00–08 and no `\pending` items; not yet compiled (needs Overleaf). Zips rebuilt: `docs/paper/medisense-cardio-paper.zip`, `docs/journal/medisense-cardio-journal.zip`.

## Day 10 close (2026-09-25) — journal manuscript on Overleaf

- Journal manuscript (`docs/journal/`, target Physiological Measurement) is complete in draft: sections 00-08, 27 pages, compiles on Overleaf with 0 errors / 0 warnings. Project: https://www.overleaf.com/project/6ab63c41eb75d6a7a76d5e32
- Methods numbering fixed: Steps 0-9 are now continuous (added Step 7 Sweep 1 analysis and Step 9 Sweep 2 analysis and cross-checks).
- Corrected conference paper is on Overleaf as "medisense-cardio-paper (1)" (https://www.overleaf.com/project/6ab63bb3bd797db75b69d089); it compiles. The older project (6ab4c0a1...) still holds the uncorrected text: delete or ignore it.
- Still open, all needing the user: title and authors; public data-archive DOI; ethics statement; AI-assistance disclosure; funding / conflicts / author contributions; confirmation from the guide; full read-through; port to IOP `iopart` + Harvard references. No git commits yet.

## Deadline day (2026-09-28) — team report refreshed

`docs/TEAM-REPORT.docx` regenerated in simple language for the whole team (built with docx-js since no LibreOffice/pandoc is on this machine; generator saved at the session scratchpad, not in the repo). Now covers, in plain words: both experiments, both papers (conference + journal), the honest "repeat not independent" correction from the per-test comparison, the version-drift problem, and today's remaining steps (title/authors, read-through, submit conference paper; confirm journal scope with guide afterwards).

## Phase 2b started (2026-09-28) — image-quality signal spike

Started Contribution 2 (the automatic bad-photo detector) per the Nov 17-21 review schedule. First step per `docs/PLAN.md`: build the Tier-1 image-level signals (computable from the photo alone, no digitizer internals, works with any digitizer).

New code: `scripts/quality_proxy/degrade.py` (exact copy of the sweep notebooks' degradation functions, kept importable so images can be regenerated locally without GPU time), `scripts/quality_proxy/image_quality.py` (five no-reference signals: `blur_score`, `skew_deg`, `resolution_score`, `contrast_score`, `blockiness_score`), `scripts/quality_proxy/spike_validate_signals.py` (the spike test itself).

**Spike result, run on the 6 local demo images (00001-00006) at all 6 axes x 5 levels:** all five signals are monotonic and strong against their target axis (Spearman |rho| 0.88-0.98). Two needed a real fix first, not a cosmetic one:
- `skew_deg` originally locked onto the ECG trace's own edges instead of the page's structural lines; restricting Hough line detection to lines at least 30% of the image width fixed it — it now recovers the injected rotation angle almost exactly (2/5/8/12/16 degrees measured as 2.0/5.0/8.0/12.0/16.0).
- `blockiness_score`'s first version (spatial boundary-vs-inner pixel differencing) was noise; a spectral version (period-8 peak in the column-gradient spectrum) is strong (rho=-0.94) but moves the opposite direction from the naive guess (less blockiness signal as JPEG damage increases, not more) — noted as an open, unconfirmed hypothesis in the code, not asserted as fact.

**What's NOT done yet, and needs Drive access:** this spike used only the 6 local demo images, not the real 50-record study sample. The actual calibration step (Contribution 2's real deliverable: fit these signals against the true errors already in `results/v2_intervals/results_v2.csv`, report correlation with T2 error and AUC for predicting a false-reassurance event) needs the 50 clean rendered pages, which exist only on Drive (`MediSense-Cardio-Study/`) — they were never saved locally, and the degraded versions were never saved anywhere (generated on Colab's ephemeral disk, one test at a time). Next real step: fetch the 50 clean pages from Drive, regenerate the 1,550 degraded versions locally with `degrade.py` (pure CPU, no GPU needed), compute all five signals for each, and calibrate against `results_v2.csv`.

Local environment note: `venv-ecg-image-kit` is also broken (points at a path that doesn't exist on this machine), on top of the already-known broken main `venv`. Installed `opencv-python-headless` and `scipy` into the system Python to do this work; ECG-Image-Kit itself was not needed for this step.

## 2026-09-29 — Phase 2b spike added to both papers

Added the Phase 2b image-quality-signal spike (started 2026-09-28) to both papers, clearly marked as preliminary work in progress, not a reported result:
- Conference paper (`docs/paper/main.tex`): Future Work item 3 now describes the five signals, the spike test, and the two bugs fixed (skew locking onto the trace instead of the page; blockiness needing a spectral rewrite).
- Journal paper (`docs/journal/sections/06_limitations_conclusions.tex`): new "Work started after this manuscript" note at the end of Conclusions, same content, explicit that it contributes no result to this paper.

Both edited directly on Overleaf (user signed in via their own Chrome; the app's browser pane was signed out) and recompiled: conference paper 0 errors, journal paper 0 errors, both confirmed to contain the new text. Local files and both zips (`docs/paper/medisense-cardio-paper.zip`, `docs/journal/medisense-cardio-journal.zip`) match the Overleaf copies exactly (character-length checked).

**Open question, not yet answered:** whether the conference paper was actually submitted by the 2026-09-28 deadline (title/author fields were still placeholders as of the last check before the deadline). Flagged to the user 2026-09-29; no confirmation yet either way.

## 2026-09-29 (continued) — Phase 2b real next step: calibration notebook

After the tilt-detection methodology was demonstrated (and confirmed working by the user, full run completed), built the actual Phase 2b deliverable per docs/PLAN.md's Contribution 2: does the no-reference quality proxy predict the real measured errors from the 1,550-test experiment?

New notebook `colab/MediSense_Cardio_Calibration.ipynb`: loads the real `results_v2.csv` and the 50 real clean pages from Drive, rebuilds all 1,550 degraded images locally (pure CPU, the damaged versions were never saved anywhere), computes all five Tier-1 signals per image, joins to the real measured errors by `variant_id`, reports Spearman correlation per signal against real QRS error, and fits a logistic regression to report AUC for predicting a real false-reassurance event among at-risk tests -- with an explicit honest fallback if there are too few real events to fit anything meaningful.

Dry-run tested (not just syntax-checked) against fabricated data shaped exactly like the real schema, both branches of the AUC cell exercised (too-few-events fallback, and the actual model-fitting path) — all cells run error-free. Not yet run against the real Drive data; that happens live. No mention of "guide" anywhere (checked programmatically, per user's explicit request this session).

Link: https://colab.research.google.com/drive/1SrSTJ6SUmpQi-6V77NyPnE8vHtVIiJfe

## 2026-11-04: project work from the literature review, Section A (ECG digitisation)
- Found: the saved `snr_db` column is invalid (100 Hz ground truth vs 1,000 Hz digitised signal compared sample by sample,
  no alignment; about -3 dB on every image, flat across damage). Both papers already say it is not reported; no change needed.
  Aligned SNR cannot be recomputed from saved data because the digitised signals were not kept (see journal discussion).
- Papers: related-work text corrected in `docs/paper/main.tex` and `docs/journal/sections/02_related_work.tex`:
  digitisation no longer described as "solved/mature" for phone photos; photo-vs-scan gap added (Open-ECG-Digitizer 19.65 vs
  12.2/10.5 dB; Challenge winner negative on phone photos); closest studies added (engrXiv 8013, VLM-in-the-Loop).
- Bibliography: added ref53 (Challenge winner, Krones et al.), ref54 (engrXiv 8013, posted Aug 2026), ref55 (VLM-in-the-Loop) to both .bib files.
- Fixed two citations: the winner was cited as the Challenge overview (ref2) and is now ref53; the "SNR is a poor clinical
  proxy" statement was credited to ECG-image-database (ref4, not read) and is now credited to the Challenge overview (ref2, read).
- Not compiled (no local LaTeX). Overleaf copies not updated.

## 2026-11-04: extension from 50 to 150 recordings (decided with the user)
- Decision: 150 recordings in total (the first 50 + 100 new), 75 male + 75 female. User asked not to change paper text until the
  project work is done; paper edits made earlier today are listed above and can be undone on request.
- Selection (scripts/analysis/select_extension_100.py, seed 42, rules fixed before any result): from the 450 unused records of the
  original 500-record pool (their clean pages are already on Drive); human-validated labels only; 51 male + 49 female; 50 normal +
  50 abnormal; 31 flagged (about 30%). Output: results/extension/selected_100.csv and selection_summary.md.
- Design for the new 100: the same 6 damage types, levels 3 and 5 only, plus clean = 13 versions each = 1,300 images, about 7 h of Colab.
- Notebook: colab/MediSense_Cardio_Extension_150.ipynb, built by scripts/notebook_builders/build_extension_notebook.py from the proven
  v2 cells (changes asserted). New: digitised lead II saved to Drive for every image; correctly aligned SNR (unit-tested on synthetic
  signals); 500 Hz reference intervals (gt500_*); provenance file with tool commits and weights. Plumbing-tested with stand-in libraries;
  NOT yet run on real data. Results go to results_extension.csv (results_v2.csv untouched).
- Checks done: rebuilt first-50 sample equals results_v2.csv records; no overlap with the new 100 (also asserted inside the notebook).

## 2026-11-04 (evening): PTB-XL+ check of our reference intervals, and a change to the extension notebook
- Downloaded PTB-XL+ features (12SL, Glasgow, ECGDeli) to data/ptbxl_plus/ (all complete, sizes match PhysioNet). Chunked downloader: scripts/tools/download_ptbxl_plus.py.
- Result (results/reference_vs_ptbxl_plus.md): heart-rate reference is fine; NeuroKit2 PR/QRS/QT/QTc on lead II do not track the commercial
  algorithms (rho 0.03 to 0.53 vs 0.91 to 0.93 between 12SL and Glasgow); same at 500 Hz. NeuroKit2 Bazett calls 21/50 prolonged, 12SL 11, Glasgow 9.
- Also found: reference HR differs between 100 and 500 Hz on 8/50 recordings, and for 14808_lr the 100 Hz reference looks wrong (results/hr_reference_check.md).
- Extension notebook now saves all 12 digitised leads per image (extension_digitized_12lead/, about 180 MB), real-data tested on 3 clean images.
- Nothing in the papers was changed in this step.

## 2026-11-04 (evening): analysis plan written BEFORE the extension data exist
- docs/analysis_plan_150.md (sha256 starts 6dc8541d3f5037c0). First 50 = development set; new 100 = confirmation set. Confirmatory questions C1 to C3 with verdict rules; everything else exploratory.
- Colab extension run started by the user the same evening; no results seen at the time of writing.

## 2026-11-04 (late evening): MASTER PLAN written (supersedes analysis_plan_150.md)
- docs/MASTER_PLAN.md (sha256 starts d58f351251d06685): phases and dates, analysis rules C1 to C3 with verdict rules, bridge run, what will and will not be claimed, user decisions.
- Merges three rounds of critique: C2 descriptive; verdicts must hold with and without reference-uncertain recordings; ceiling-limited and inconclusive rules for C3; no-output vs wrong-heart-rate split
  (sweep 1 vs sweep 2 showed the digitiser's output availability is not repeatable: 163 vs 30 unreadable images); bridge run; false reassurance descriptive only.
- Written before the extension results exist; the user had not yet approved the individual changes, only asked for one master plan.

## 2026-11-04 (night): master plan updated with the complete analysis inventory (section 4b, 22 items)
- Added items missing from the first version: paired Wilcoxon + Bland-Altman vs clean, five-outcome table, no-output rate, dose-response, subgroups (sex, age, diagnosis, HR range), second peak detector, gate using digitiser output, refreshed score correlations, sweep 1 vs 2 comparison, CLAIM checklist.
- docs/MASTER_PLAN.md sha256 now starts ce827e2ca11f7cd4. Still before any extension result.

## 2026-11-04 (night): reference-uncertain flags for all 150 recordings (no outcomes used)
- results/extension/reference_check_150.csv: heart rate from the 100 Hz and 500 Hz original record per recording. Reference-uncertain (>5 bpm apart): first 50 = 8 (16%), new 100 = 12 (12%), total 20 of 150. Largest: 09950_lr (55.5 vs 90.8 bpm).
- Computed from the original signals only, before the extension results exist, as required by docs/MASTER_PLAN.md (section 4, condition for every verdict).

## 2026-11-04 (night): claims register written (docs/CLAIMS_REGISTER.md, sha256 starts ea2a14672d1efbcd)
- Nine claims with grades A to D and the four marks each must earn before it enters a paper, deck or diary. Today none is grade A. Before extension results exist.
- 2026-11-04 night: docs/plan/analysis_plan_changes.md created: added the 'colour pages only' limit and corrected the page-size statement (2200x1700 input, not 4000x2800).

- 2026-11-04 (late): Arm B notebook (colab/MediSense_Cardio_ArmB_GeneratorArtifacts.ipynb) render path tested locally on 4 recordings: B1 wrinkles, B2 augment, B3 both all produced pages (4/4 each). Two tool problems found and fixed in the notebook: (1) imgaug/NumPy 2 (sitecustomize shim), (2) wrinkle code crashed on newer OpenCV (cv2.subtract with a NumPy scalar) -> patched to float(); rendering is now one record per call with 3 tries. NOT yet tested: the digitising step of this notebook (reuses the proven sweep cells). Examples: results/extension/armB_example_*.png.

- 2026-11-04 (late): Dean SCOPE email of 1 Nov 2026 confirms the Capstone Final Review: **Friday 20 Nov 2026, 10:00-18:00, physical, attendance in person mandatory**. Guidelines to follow "by end of this week". Earlier rules in the same email chain: outcome should be a national/international conference paper submission or a patent; source code, complete schema and documentation must be presented; attendance counted 4 Aug-14 Nov, minimum 75% to be eligible. This replaces the earlier "Nov 17-21" window: Nov 21 is no longer a spare day. Plan dates unchanged (freeze ~10 Nov; papers/deck 11-14 Nov); rehearsal now 15-19 Nov.

- 2026-11-04 (night): Read Downloads/Circular Capstone FALL 2026-27 (VIT-AP/2026/DoA/FALL26-27/CAP/1, 14-07-2026), CAPSTONE_THESIS_Format.docx (the report template; the "(1)" copy is identical) and Capstone Project Rubrics.xlsx (old-year dates). Facts: (a) **Project report + supporting material (poster, CD) due by 20 Nov 2026** = 20 marks; final review 40 marks; digital copy as ONE PDF uploaded on VTOP, final grade only after; (b) report must contain a record of all codes, standards and software tools (item 16); (c) template chapters: cover, certificate, acknowledgements, abstract, contents, list of figures/tables, Ch1 Introduction (objectives, background and literature survey, organisation), Ch2 system (proposed system, working methodology, standards, system details software/hardware), Ch3 cost analysis, Ch4 results and discussion, Ch5 conclusion and future work, Ch6 appendix (codes), Ch7 references, biodata; Times New Roman 12 pt, 1.5 spacing, justified, Letter page, 1.25 in side margins; (d) rubric items for the 20 report marks: report in prescribed format 5, A0 poster 5, plagiarism report 5, quality of report 5; (e) circular item 5 expects hardware or at least significant design with a real-world application; (f) the template is the Electronics-school sample (vehicle system): the circular says programme chairs/HoDs share the final format separately, so the SCOPE format must be confirmed.

- 2026-11-04 (night): USER REQUIREMENT (said three times): do the project "the same way the researchers did". Two researcher-style arms are therefore part of the project, not optional extras: Arm B = pages damaged with the ECG-Image-Kit generator own artifact options (wrinkles/creases, augmentation), 30 recordings, notebook ready and render-tested (colab/MediSense_Cardio_ArmB_GeneratorArtifacts.ipynb); Arm C = real captures from the public Challenge image set, needs the user Kaggle login and download (not started). Run order after the main extension run: bridge run, Arm B, then Arm C if the data are in hand by 7 Nov. If Arm C is dropped, the report must say so as a stated limit, not leave it out silently.

- 2026-11-04 (night): Arm C Kaggle notebook built (colab/MediSense_Cardio_ArmC_Kaggle_RealCaptures.ipynb, builder scripts/notebook_builders/build_armC_kaggle_notebook.py): data = Kaggle competition "PhysioNet - Digitization of ECG Images" (CC BY 4.0, rules accepted by the user on their account), 40 recordings chosen by seed 42 among those with true signal + all 9 versions (original, print+scan colour/bw, phone photo of print, photo of screen, stained/soaked, extensive damage, mold scan colour/bw). Tested locally end to end on a FAKE competition folder (10 PTB-XL recordings, CPU, 5 images): selection, digitiser setup, smoke test, metrics, checkpoint, overview all ran. The test caught one bug (ray patch applied twice; now applied once) and the notebook now stops if the 2-image smoke test fails. NOT tested: the real Kaggle folder layout (train.csv columns id/fs/sig_len and train/ID/ID.csv, ID-0001..0012.png are taken from the Data page; the notebook prints and stops with a clear message if they differ), GPU, Kaggle Internet/apt-get for git-lfs. Also written: docs/reports/METHODS_AND_FORMULAE.md for the guide.

## 2026-11-05 - Arm C (Kaggle real captures) finished and saved
- 40 recordings x 9 capture types = 360 rows; files in results/armC/: results_armC.csv (360 rows), armC_provenance.json, armC_selected.csv, armC_digitized.zip (360 npz, 12 leads x 10000 samples, float32; zip test OK, 48 MB).
- First look (not yet analysed): SNR median 18 dB (clean kit page) -> 0.6-8.6 dB on real captures; wrong HR (>5 bpm) 5/40 clean vs 4-9/40 on captures; phone photo of screen: 14/40 no output. Differences between capture types NOT significant at n=40.
- Next: which 5 clean pages fail; scale/warp check of the SNR drop; summary table. Needs the user's go-ahead.

## 2026-11-05 - Schedule note
- User is unavailable on 5 Nov only (travelling). Back to full work 6 Nov.
- Colab main extension: 860/1300 at 00:45 IST, ETA ~03:50 IST 5 Nov. Claude verifies the Drive files via the connector on 5 Nov (user not needed).
- Plan: 6 Nov bridge run + Arm B run (user runs Colab); 7-9 Nov analysis A-G + Arm C; 10 Nov freeze (results/FINAL_NUMBERS.md); 11-14 report, poster, plagiarism report; 15-19 rehearsal; 20 Nov review.

## 2026-11-05 - Arm C checks (scripts/analysis_armC_summary.py, scratchpad/armC_check2.py)
- Table: results/armC/armC_summary.csv (Wilson CI, exact paired test vs clean page, Holm). Bad = no output or HR error >5 bpm.
  clean 5/40 (12.5%); print+scan 7/40; phone photo of print 6/40; stained 7/40; extensive damage 8/40; mold 6-9/40 -> none differs from clean (Holm p = 0.875-1.0).
  Phone photo of SCREEN: 14/40 no output, 18/40 bad (45%, CI 31-60%), Holm p = 0.008. This is the only capture type that differs.
- Check 1 (the 5 clean failures): all five have HIGH SNR (11-23 dB) and the digitised heart rate is the SAME in 8-9 of 9 versions (e.g. 54 vs reference 61). So the error comes from the page/recording or the reference side, not from damage. Digitised RR ~1.1 s vs reference 0.98 s. Not caused by sampling rate. Cause NOT settled: needs the Kaggle reference signals (not on this PC; download needs a yes).
- Check 2 (why SNR drops): measured against the clean-page digitisation as proxy reference (shift-only SNR matches the truth-based SNR). Gain fit: +0.4 dB. Global stretch 0.94-1.06: +0.1 to +0.2 dB except phone photo of print (+3.8 dB). Local timing wobble (own shift per 2 s window, +-100 ms): +5 to +7 dB on every capture. Control (pure white noise at 4 and 8 dB SNR) gains 0.0 dB from the same local shifting, so the gain is real local warping, not curve fitting. Conclusion: the low SNR is mostly local time wobble, not noise or gain; beat spacing survives, so HR mostly holds.

## 2026-11-05 - Bridge notebook built
- colab/MediSense_Cardio_Bridge_Run.ipynb (30 cells, all code cells compile) built by scripts/notebook_builders/build_bridge_notebook.py from the Extension notebook (only the record list, file names and a final comparison cell differ).
- 12 records, rule fixed before the run: the 6 that fail in most sweep-2 versions (00102, 08150, 13316, 00053, 18151, 19059) + 6 random reliable (seed 42): 01126, 09990, 13618, 15049, 17820, 20053. List: results/bridge/bridge_selected_12.csv. 156 images, ~1 h.
- Outputs on Drive: results_bridge.csv, bridge_digitized_12lead/, bridge_provenance.json. Last cell (Step 9) compares with sweep 2 (rule: >5% label changes -> pooled comparisons exploratory).
- NOT run yet. Not tested on Colab (only compiled and checked that axis/level/record names match results_v2.csv). Run only after the main extension run prints ALL VARIANTS COMPLETE.
- User plans to run Colab notebooks at 8 am on 5 Nov.

## 2026-11-05 - Arm B test: digitising step works, and a real bug was found and fixed
- BUG: the tool's `--augment` crashes (TypeError: 'NoneType' object is not subscriptable, ImageAugmentation/augment.py line 41) unless `--store_config 1` is given (it needs the lead positions from a .json file). The crash happens AFTER the plain page is saved, and the notebook only checked that the png exists, so B2 would have been the CLEAN page and B3 would have been B1 (wrinkles only) without any warning. The earlier examples in results/extension (B2, B3) were such half-made pages (B1 vs B3 pixel difference 0.1).
- FIX in scripts/notebook_builders/build_armB_notebook.py (notebook rebuilt, 29 cells, compiles): `--store_config 1` added to B2 and B3; a render counts as success only if the tool exit code is 0 AND the page exists; a half-made page is deleted after 3 failed tries. Example images in results/extension replaced with real ones (record 00004).
- TEST (CPU, local, record 00004_lr, reference HR 75.1): digitised HR clean 75.1, wrinkles 75.1, augment 74.6, both 75.1. All four pages gave 12 leads (augment: 9,782 samples after crop). Digitising loop of the notebook is identical to the proven extension loop except file names (diffed).
- NOT tested: the full notebook on Colab (Drive, imgaug install, PhysioNet fetch).

## 2026-11-06 - Extension run (new 100 x 13 versions) checked
- results_extension.csv (copied to results/extension/): 1,300 rows, 100 records, 13 versions each, no duplicates, no overlap with the first 50. Sex 51 male / 49 female.
- No output 26 (2.0%); bad (no output or wrong >5 bpm) 118 (9.1%). Clean pages: 1 no output, 3 wrong >5 bpm (4 of 100).
- Same 13 versions in the first 50: bad 10.0% vs 9.1% in the new 100. Pattern the same: resolution level 5 (44% vs 47%), blur level 5 (20% vs 19%), rotate level 5 (14% vs 20%; 19 of the new-100 rows have no output).
- Still to do: the 12-bit/npz folder (extension_digitized_12lead) and provenance json not yet checked locally.
- 2026-11-06: Bridge notebook failed at Step 1 check (assert human-validated labels): 13618 and 19059 of the 12 are not human-validated (8 of the first 50 are not). Rule applied only to the new 100. Fixed in build_bridge_notebook.py (prints the count instead of asserting); notebook rebuilt.

## 2026-11-07 - Bridge run checked (results/bridge/results_bridge.csv)
- 156 rows (12 records x 13 versions), no duplicates, all match results_v2.csv rows.
- Label (no output or wrong >5 bpm) changed between sweep 2 and the bridge run: 0 of 156 = 0.0% (rule: >5% -> pooled comparisons exploratory). Not triggered.
- No reading: 1 in each run (same image). Both read: 155; heart rates equal within 1 bpm in 153, max difference 1.9 bpm, median 0.0.
- Bad labels: 13 in each run (same images). Clean pages identical (heart rates agree to <=0.1 bpm).

## 2026-11-07 - Section C run (scripts/analysis/section_C.py -> results/analysis/SECTION_C.md and sectionC_*.csv)
- Covers inventory items 1-6 and 8 (rates with Wilson CIs, level 3 beside 5, unflagged-only C2 table, with/without reference-uncertain, five-outcome table, no-output rates, dose-response). Items 7 (paired Wilcoxon/Bland-Altman), 9 (subgroups) and 12 (QT/QTc) not yet run.
- Excluded as unreliable (>20% of versions with no output): 15192_lr (first 50, 20 of 31) and 21205_lr (new 100, 4 of 13). Flagged by PTB-XL: 14 of first 50, 31 of new 100. Reference-uncertain: 8 and 12.
- C1 SUPPORTED on the new 100 at level 5, with and without reference-uncertain recordings, and on all 150: wrong HR >5 bpm resolution 47.5%, blur 17.2%, rotation 0.0%, JPEG 0.0%, brightness 1.0%, grid 3.0% (clean 3.0%).
- C2 (descriptive): every point estimate is within the allowance (rotation <=10%, others <=5%) on new 100 unflagged, new 100 unflagged + ref-certain, and all 150 unflagged.
- Correction to my message of 2026-11-07: I said C2 might fail because rotation level 5 was ~20% 'bad'. 19 of those are NO OUTPUT, not wrong heart rates; the confirmatory outcome (wrong HR with output) is 0.0% for rotation. C2 is descriptive in MASTER_PLAN (not the older analysis_plan_150 wording).
- Rotation at level 5 fails loudly (no output, 19.2% of the new 100); resolution and blur fail silently (output with wrong HR). False reassurance (all 150, HR 60-100 convention): resolution level 5 = 19 of 148, clean = 1 of 148.

## 2026-11-07 - Section A run; extension 12-lead signals downloaded
- scripts/analysis/section_A.py -> results/analysis/SECTION_A.md and sectionA_*.csv (SNR by damage and level, SNR vs error, acceptable-SNR-but-wrong, paired Wilcoxon vs own clean page with Holm, Bland-Altman). First-50 snr_db is invalid and not used; SNR exists for the new 100 and the 12 bridge records only.
- extension_digitized_12lead zip (175 MB) unzipped to results/extension/extension_digitized_12lead/extension_digitized_12lead/: 1,300 npz, all match results_extension.csv variant_ids, 12 leads x 10,000 samples each, zip test OK.

## 2026-11-07 - Arm B (generator artifacts) checked (results/armB/results_armB.csv, armB_summary.csv)
- 120 rows = 30 recordings (all from the new 100) x 4 versions (clean, B1_wrinkles, B2_augment, B3_both); no duplicates; ran on the T4 GPU in the second account.
- Wrong HR >5 bpm: clean 0/30, B1 1/30 (5.24 bpm on a 138.6 bpm recording), B2 0/30, B3 0/30. No output: B2 1/30 (10923). Exact paired test vs clean: no difference (all p = 1.0 after Holm). Median SNR 12.1 / 13.5 / 12.6 / 11.9 dB. Wilson upper bound for 0/30 = 11%.
- The 30 clean pages were digitised again in this run: 29 of 30 heart rates identical to the extension run, 26 of 30 SNR values identical (small repeatability check).
- Limit: n = 30; the digitiser was trained on images from this same generator family (artifacts included), so no harm here is the expected result, not a surprise.

## 2026-11-07 - Detector scores for the new 100 and Section D (C3) (scripts/analysis/section_D.py -> results/analysis/SECTION_D.md, sectionD_*.csv)
- Colab notebook colab/MediSense_Cardio_Detector_Signals_New100.ipynb (CPU) produced quality_signals_ext.csv (1,300 rows); with quality_signals_v2.csv saved in results/detector/. In the smoke test new and old scores matched exactly (60 of 60).
- Rules fixed before looking at results: target = wrong HR >5 bpm on images with output (no-output images left out); train first 50, score new 100 once; verdict words per MASTER_PLAN.
- C3 verdict: INCONCLUSIVE (86 wrong readings in the new 100, rule needs 100). Descriptive: AUC 0.858 (0.81-0.91); oracle 0.827 (0.77-0.90); best single score chosen on first 50 = blur (new-100 AUC 0.814); secondary target (wrong or no output) 0.831; swapped direction 0.750 (0.64-0.91, 50 wrong); grouped CV on all 150 0.795 (0.73-0.87), oracle 0.785.
- Honest reading: detector ~ oracle, so it recognises damage severity. Inside resolution level 5 (47 of 99 wrong) AUC = 0.521; blur level 5 = 0.476 (chance). Leave-one-damage-out: resolution 0.78, blur 0.56, brightness 0.37, grid contrast 0.48 (rotation and JPEG too few wrong readings). Coverage: flag top 10/20/30% catches 60/76/80% of wrong readings, wrong rate among kept photos 3.0/2.1/1.9% (overall 6.8%).
- Earlier first-50 grouped test gave 0.607 (different target); first-50 failures are partly recording-driven (e.g., 14808 wrong in 10 of 13 shared versions).
- Not done (stated): unreadable-leads feature, standard no-reference quality baseline.

## 2026-11-07 - Section B run (scripts/analysis/section_B.py, section_B_detector_check.py -> results/analysis/SECTION_B.md and sectionB_*.csv)
- First attempt hung: 14 worker processes ran the PC out of memory ("paging file too small"), a worker died, the pool waited forever. Fixed: 6 workers, 1 math thread each, a pool that raises on a dead worker. Cached signal measurements: results/analysis/sectionB_cache_*.csv.
- Data fact found: a digitised page shows leads I-III, aVR-aVF, V1-V6 only inside ~2.5 s windows (only lead II, the rhythm strip, spans 10 s) and the saved signals have small gaps (interpolated). NeuroKit2 cwt delineation cannot process 2.5 s windows, so QT on digitised pages = lead II only; truth = same method on original lead II (500 Hz). Original 12-lead median is used only for the check against 12SL.
- B1: HR 100 vs 500 Hz on the new 100: median difference 0.10 bpm, 12 reference-uncertain (4 differ >10 bpm). QT original 12-lead median vs 12SL: rho 0.67, median abs diff 31.5 ms, bias +37.6 (first 50: 0.66, 28.9); lead II only: rho 0.52, 37.0 ms, bias +50.5 (n = 81).
- B2: QT on digitised lead II is available for only 80/99 clean pages and 40/99 blur level 5 pages. Median abs QT error: clean 10.4 ms; resolution 5 30.3; blur 5 30.6; others 9-14. But 25% of clean pages already differ from the original by >60 ms in QTc, so the method's own floor is poor. QTc false reassurance (Fridericia main, tolerance 10 ms): 9 events in 258 tests = 3.5% (2-6), mostly under JPEG/rotation/brightness (which do not hurt HR) -> mainly measurement noise, not a damage effect; Bazett 16/399 = 4.0%. Earlier first-50 result (Bazett, DWT lead II) was 1.2%: different method.
- B3: second detector (Pan-Tompkins) gives 13% wrong on clean pages vs 3% (main). On ORIGINAL signals it disagrees with the main reference on 31 of 100 recordings; no tested alternative is better (best kalidas2017: 19). Ranking of damage unchanged (resolution 5 > blur 5 > rotation 5 > rest), rotation 5 looks bad under this detector (43% wrong, 21 no output). Weak robustness check; C1 verdict (fixed in advance, main detector) unchanged.
- B4 subgroups (exploratory, small): sex no difference; 80+ and HR >100 (n = 13) and STTC/MI worse at resolution/blur level 5; flagged recordings have more failures in the other versions (5.2% vs 1.4%) but the same rate under hard damage (31.8% vs 31.2%).

## 2026-11-07 - Section E run (scripts/analysis/section_E.py -> results/analysis/SECTION_E.md and sectionE_*.csv)
- Rules fixed first: flag top 10/20/30% by predicted risk; (A) held-out first 50 -> new 100, (B) grouped CV on all 150; primary target wrong HR >5 bpm (images with output), secondary wrong or no output; recording-level bootstrap 2,000; comparisons: random, oracle, best single score. No guarantee claimed; effect of a flag on people untested.
- Held-out new 100 (wrong overall 6.8%): flag 10% -> catches 60% (51-73), 6% of right readings wrongly flagged, wrong among kept 3.0%; 20% -> 76% (66-86), 16%, 2.1% (1.0-3.5); 30% -> 80% (72-89), 26%, 1.9%.
- Grouped CV all 150 (wrong overall 7.2%): 20% -> 68% (57-81), 16% wrongly flagged, kept 2.8%.
- Oracle gate (told damage type and level) gives the same numbers (20%: 77%); best single score (blur) 20%: 78% -> the gate is effectively "reject heavily degraded photos". At 10% it flags all 99 resolution-level-5 pages (47 wrong, 52 fine) and 28 of 98 blur-level-5 pages; at 20% all 99 + 98 of those two plus 56 blur-level-3.
- HR false reassurance in the new 100: 27 events; gate flags 16 / 20 / 22 at 10 / 20 / 30%.

## 2026-11-07 - Section G run (scripts/analysis/section_G.py -> results/analysis/SECTION_G.md, sectionG_*.csv, sectionG_calibration.png)
- CLAIM 2024 item list read from the paper (PMC11304031 body text via a web-fetch agent): items 1-36 from the body text, items 37-44 from a summary of the page -> verify wording against the official table/appendix before quoting. Statuses for this study: Met 22, Partly 12, Not applicable 6, To do 3 (title, abstract, funding), Not met 1 (item 21, intended test-set sample size).
- Calibration (train first 50, test new 100, wrong HR >5 bpm): the model as specified (class_weight balanced) is badly miscalibrated: mean predicted risk 0.462 vs observed 0.068, calibration-in-the-large -2.88. Exploratory unweighted refit: mean predicted 0.077 vs observed 0.068, CITL -0.16 (-0.47 to 0.17), slope 1.34 (1.15-1.60), Brier 0.049 vs 0.063 for always predicting the prevalence.
- Riley sample size (5 predictors, S=0.9): about 800-880 independent subjects at R2 0.05 (apparent R2 0.050; max 0.361); n for overall risk 86. First 50: 49 recordings, 1,509 images, 89 events (17.8 per predictor) but 70% of the events come from 5 recordings. New 100: 86 events (<100 recommended for testing); about 1,471 images would be needed for 100 events at 6.8%.

## 2026-11-07 - D2: an output-based gate (EXPLORATORY; rules in docs/plan/analysis_plan_changes.md before running)
Scripts: section_D2_features.py (15 features from the saved 12-lead signal), section_D2.py, section_D2b.py, section_D2b_armC_features.py -> results/analysis/SECTION_D2.md, SECTION_D2b.md, sectionD2*.csv.
- New 100, images with a reading (1,265; 86 wrong; 99 recordings), whole recordings held out (5-fold x10). Overall AUC: photo scores 0.828 (0.77-0.89); output features 0.914 (0.88-0.95); both 0.950 (0.93-0.97); oracle 0.821.
- Pre-fixed criterion MET: within-damage AUC inside resolution level 5 / blur level 5: photo 0.50 / 0.37; output 0.82 (0.73-0.89) / 0.83 (0.69-0.94); both 0.86 / 0.86.
- Gate, flag 10/20/30%: output features catch 64/78/90% of wrong readings (kept wrong 2.7/1.9/1.0%); both 73/88/97% (kept wrong 2.0/1.0/0.3%); photo scores alone 59/76/78%; oracle 55/74/81%.
- Which checks do the work: beat-interval regularity alone (rr_cv, longest/shortest RR) AUC 0.892 overall, 0.88 / 0.87 within resolution5 / blur5. Cross-lead consistency (Einthoven, Goldberger, beat-count agreement) 0.84 / 0.64 / 0.75. Completeness only 0.72 / 0.45 / 0.54.
- Cost: right readings flagged at 20% = 67% in the 6 atrial fibrillation/flutter recordings vs 13% in the other 93; median RR variability on clean pages 0.219 vs 0.026. The check measures plausibility, not truth.
- EXTERNAL check on the real captures (Arm C; model trained on the new 100, applied once): AUC 0.575 (0.38-0.82), 59 wrong readings in 346 images; gate at 30% catches 36% (wrong among kept 15.7% vs 17.1%). Does NOT transfer: real-capture errors are mostly recording-driven (the 5 clean-page failures have good signals; same digitised HR in 8-9 of 9 versions), which no signal check can see. Arm C damage is also mild.
- Follow-up rules (a)-(c) were fixed after seeing the main D2 result. Limits: 86 events, one recording set, first 50 cannot be used (signals not saved).

## 2026-11-07 - Arm C extension notebooks built (not yet run)
- colab/MediSense_Cardio_ArmCext_Part1_Kaggle.ipynb and Part2 (21 cells each, all code cells compile). Derived from the proven Arm C notebook by asserted substitution; seed 43; the 40 Arm C recordings are excluded (embedded list); 100 recordings split into 50 + 50 (sorted); output names carry the part number; new Step 8 computes the five photo scores of every capture (code copied verbatim from the detector notebook).
- Local tests with a fake competition folder (210 ids incl. the 40 used): 100 chosen, 0 overlap with Arm C, parts disjoint, photo-score step ran and verified its saved file. Not tested locally: digitiser and measurement cells (identical to Arm C, which ran on Kaggle on 2026-11-05).
- Rules were written first (analysis_plan_changes.md). Analysis plan after the run: Arm C summary with Wilson + exact paired tests, the D2 output gate applied once, the photo detector applied to real captures, pooled with the first 40 as a secondary view.
- 2026-11-07: single-notebook variant built (MediSense_Cardio_ArmCext_All100_Kaggle.ipynb, PART = 0, outputs *_all*). Use it OR Part1+Part2.

## 2026-11-08 - Arm C extension RUN + analysed (Section H; exploratory/replication)
- Kaggle single notebook (All100, GPU T4 x2, ~7 h, 900 images) finished; zip downloaded and validated: 904 files (900 npz + 4 results), 100 recordings x 9 capture types, no overlap with the first 40, no duplicates. Saved to results/armCext/. Output features for the 900 signals: results/analysis/sectionH_armCext_features.csv.
- Script scripts/analysis/section_H.py -> results/analysis/SECTION_H.md + sectionH_*.csv.
- Wrong HR (>5 bpm) is 8-16% in EVERY capture type, including the clean kit page C0 (11/100). No capture type differs from C0 on wrong HR (paired exact + Holm: all p_holm >= 0.5; smallest raw p 0.0625 for C3). Only effect: C4 phone photo of screen gives NO output in 39/100 (pooled 53/140 = 38%; vs C0 1%; Holm p < 0.0001). When C4 gives an output it is not more often wrong.
- Events: 109 wrong readings in the new 100, 168 pooled (>=100 rule reached). Wrong readings are small: 122/168 are 5-10 bpm, median 7.5 bpm, 10 > 20 bpm, none near double/half.
- Recording-driven: the 11 recordings wrong on the clean page are wrong in 4-9 of 9 versions (85% of their real-capture versions) vs 3.2% for recordings right on the clean page. Cause not established (reference vs digitiser; same generator family).
- Output gate (D2, trained on simulated, applied once): AUC 0.665 (0.51-0.82) new 100; 0.635 (0.51-0.76) pooled 140. Gate 20% flag catches 47% of wrong, flags 16% of right; wrong among kept 8.5% vs 12.7%. Weak; much weaker than in simulation.
- Photo detector (trained on simulated, applied once to new 100): AUC 0.516 (0.46-0.57) for wrong HR; 0.64 for bad (driven by C4 no-output); inside C4 it cannot tell which fail (0.49). Does NOT transfer to real captures. skew_deg saturates at 45 for C2/C4/C8 (score unreliable there).
- Not done: no real-photo validation of QT; digitiser trained on the same generator family; pooled photo scores for the first 40 not available.

## 2026-11-08 - Clean-page diagnosis (Section I; exploratory, digitised signals only)
- Script scripts/analysis/section_I_clean_page.py -> results/analysis/sectionI_clean_page_diagnosis.csv. Question: why 16/140 clean kit pages (C0) give a wrong HR (>5 bpm) in the real-capture arm. Reference (true) signals are NOT on this computer, so only the digitised side can be examined.
- Findings: (1) digitised lead II is complete in the wrong group (median 9,997 of 10,000 samples) - not missing data. (2) 13/16 wrong readings are LOWER than the reference (fewer beats found). (3) Five peak detectors disagree much more on the wrong group (median spread 24 bpm vs 6 bpm): the digitised signal is hard to count beats on. (4) Beat-interval variability (rr_cv) is higher: median 0.163 vs 0.034; AUC for wrong 0.744; wrong in 22% of irregular (rr_cv>0.06, 11/50) vs 5.6% regular (5/89). (5) Other detectors do not rescue it: within 5 bpm of reference for 12-44% of the wrong group.
- Reading: the wrong clean pages are mostly irregular or hard-to-count rhythms where a single 10-second HR number is fragile. NOT shown: whether the reference or the digitised signal is at fault (needs the true lead II of these recordings; a small CPU Kaggle export would settle it).
- 2026-11-08: truth-export notebook built (colab/MediSense_Cardio_TruthExport_Kaggle.ipynb) and executed end-to-end locally on a fake competition folder (170 recordings, 6 sampling rates; 140 signals + meta saved and verified). Not yet run on Kaggle. Plan after the run: (1) compare true vs digitised lead II on the clean page for the 16 wrong readings (beats found, same detector on both); (2) decide if the error is in the reference, the digitiser, or the single-number heart-rate method; (3) if it is the method, add a robust-HR SENSITIVITY analysis (original outcome stays primary; change logged in analysis_plan_changes.md).

## 2026-11-08 - Truth export run + clean-page diagnosis with the TRUE signal (Sections I2, I3; exploratory, post hoc)
- Kaggle truth-export notebook run; results (1).zip validated (140 true lead II signals, all 10 s, native fs 250-1025 Hz, ids match Arm C + extension). Saved in results/truth/.
- Scripts: scripts/analysis/section_I2_truth.py (true vs digitised, clean page) -> results/analysis/sectionI2_truth_vs_digitised.csv; section_I3_sensitivity.py -> sectionI3_*.csv.
- Reference HR reproduced exactly from the true signal (140/140), digitised HR reproduced (139/140).
- 16 wrong clean pages: digitised lead II follows the true signal closely (median correlation 0.98; 14/16 >= 0.94); beats match 1:1 (154 matched, 15 only in truth, 7 only in digitised). Two recordings are real digitiser shape failures (correlation 0.42-0.45: 756565655, 4049828212).
- The five peak detectors disagree about the heart rate on the TRUE signal itself: median spread 32 bpm in the wrong group vs 6 bpm in the right group. So the one-number heart rate is ill-defined for those recordings; the reference method differs from the consensus of detectors on the true signal by > 5 bpm in 7/16 wrong pages (and 6/124 right pages).
- Replacing the reference by the consensus does NOT remove the problem (still 16/140 wrong): ambiguity is on both sides.
- Sensitivity (post hoc; flag from the TRUE signal only: detector spread > 10 bpm; 15 bpm also shown): 57/140 recordings flagged; 14/16 wrong clean pages are inside the flag; wrong clean page 25% in flagged vs 2% in not flagged. Among NOT flagged recordings wrong HR on real captures is 2-6% per type, still no capture type different from C0 (all p_holm = 1.0); screen photos still 36% no output. Primary (original) definition unchanged.

## 2026-11-08 - Fix of the heart-rate MEASUREMENT (Sections J, K; post hoc correction, original kept)
- Cause of most wrong clean pages: the notebooks found beats with neurokit2 on the RAW signal (no nk.ecg_clean) for both the true and the digitised lead II. Same method on both signals, but fragile on hard recordings. Applying nk.ecg_clean (method neurokit) to BOTH before the beats are found (scripts/analysis/section_J_remeasure.py, section_J_summary.py; results/analysis/sectionJ_*.csv).
- Choice made by reasoning (standard library pipeline, same as the interval code in the notebooks already uses), NOT by minimising errors; it did turn out to be the lowest of the five detectors tried (raw 16/140, cleaned 6/140, Pan-Tompkins 13, Elgendi 25, Hamilton 48 wrong clean pages).
- Arm C (real captures, 140 recordings, 1,260 images): wrong HR (>5 bpm) pooled 168 -> 46 (real C1-C8 152 -> 40); new 100: 109 -> 30. Clean page 16/140 -> 6/140. Per capture type 1-3% wrong (was 8-16%); no capture type differs from C0 (all p_holm = 1.0); C4 screen photos still no output in 53/140. Errors still above 5 bpm: 23 of 46 are 5-10 bpm, 10 > 20 bpm. 100-event rule is NOT reached any more for real captures (46 pooled).
- Simulated new 100 (re-measured on the 1,300 saved signals, reference = PTB-XL 100 Hz lead II, reference reproduced exactly): ranking unchanged. Clean 3 -> 4/99; resolution 5: 47 -> 49/99; blur 5: 17 -> 18/99; rotate 5 no output 19/99. All wrong readings with an output: 86 -> 113 (>= 100). First 50 recordings cannot be re-measured (no saved signals).
- Consequences to handle before the freeze: (1) report both measures, original as pre-specified primary, cleaned as the corrected measure for real captures; (2) detector (Section D) and output gate (D2) results on real captures used the ORIGINAL wrong labels and should be repeated with the cleaned labels (exploratory) because the real-capture labels changed a lot; (3) real-capture events < 100, so claims there stay descriptive.

## 2026-11-08 - Output check and photo detector repeated with the corrected labels (Section L; exploratory, post hoc)
- scripts/analysis/section_L.py -> results/analysis/SECTION_L.md, sectionL_*.csv. Labels: cleaned heart-rate measure (Sections J, K).
- Simulated new 100 (1,262 images, 113 wrong): output check cross-validated AUC 0.926 (0.89-0.95); within resolution 5 / blur 5 0.873 / 0.892 (was 0.82 / 0.83); photo scores 0.724 overall, 0.48 / 0.43 within resolution 5 / blur 5 (no use inside the hard damage types). Simulated conclusions survive the correction.
- Real captures, models trained on simulated damage and applied once, scored with cleaned labels: output check AUC 0.923 (0.86-0.97) pooled 140 (46 wrong readings; 0.915 on real C1-C8, 40 wrong), 0.895 (0.81-0.96) new 100 (30 wrong), 0.982 on the first 40 (16 wrong). With original-trained model 0.953. Before the correction the same check scored 0.635 against the original labels, so the earlier "does not transfer" result was largely caused by the noisy original labels.
- Gate (pooled real C1-C8, cleaned labels): flag top 20% catches 90% of wrong readings, flags 17% of right ones; wrong among the kept 0.5% vs 3.8% overall. Flag 10%: 65% caught.
- Photo detector (new 100, photo scores): AUC 0.52 (0.39-0.65): still no use on real captures.
- CAUTIONS: (1) only 46 wrong readings on real captures (<100): descriptive; (2) the output features use the same neurokit cleaned beat detector as the corrected label, so part of the agreement is by design (the check measures internal consistency of beats, not truth) - as before, not shared with the reference; (3) irregular rhythms cost: atrial fibrillation recordings are flagged more often (Section D2b: 67% of right readings flagged at 20% in AF vs 13% others); (4) labels were changed after seeing results, so this stays exploratory.

## 2026-11-08 - Multi-detector agreement features (Section M; exploratory, rules fixed before the run)
- scripts/analysis/section_M_features.py (5 detectors on the digitised lead II; 2,560 signals) and section_M.py -> results/analysis/SECTION_M.md, sectionM_*.csv.
- Pre-fixed rule (a) pooled-140 real-capture AUC rises by >= 0.02: NO (0.923 -> 0.928, +0.005; paired 95% -0.030 to +0.056). (b) simulated within-damage AUC does not fall: YES (resolution 5: 0.873 -> 0.890; blur 5: 0.892 -> 0.898). Added value: NOT MET.
- Detector agreement ALONE is a useful simple check: five features give AUC 0.817 (0.74-0.90) cross-validated on the simulated set (0.76 / 0.83 within resolution 5 / blur 5); the single feature `det_spread` gives 0.859 on the real captures (pooled 140). `det_n_agree` is the best single one inside blur 5 (0.84) and resolution 5 (0.76). Gate at 20%: OUT catches 90% of wrong readings, OUT+DET 78% (noise; 40 events).
- Reading: the 15 output features already contain this information (beat regularity and cross-lead agreement); detector agreement is a simpler, explainable version that needs no training (flag when detectors disagree > X bpm). Not an improvement to the combined model.

## 2026-11-08 - Can the PHOTO predict failure on real captures when trained on real captures? (Section N; exploratory, rules fixed before the run)
- scripts/analysis/section_N_real_photo.py -> results/analysis/sectionN_*.csv. New 100 recordings, 900 images, photo scores from the Kaggle run, grouped 5-fold x10 by recording, logistic regression on five photo scores; comparator = told the capture type.
- T1 NO OUTPUT (43 events): photo scores AUC 0.937 (0.88-0.99); capture type alone 0.887 (0.81-0.94). INSIDE screen photos (39 of 100 no output): 0.862 (0.79-0.93), i.e. the photo scores also tell WHICH screen photos fail (earlier 0.49 was the simulated-damage-trained detector).
- T2 WRONG HR among images with output (30 events): 0.542 (0.46-0.66); capture type alone 0.395. T3 no output or wrong: 0.774 (0.70-0.86); without screen photos 0.555 (0.50-0.62).
- The five photo scores identify the capture type (AUC 0.82-1.00).
- Reading: from a real photo we can predict "the digitiser will give no output" (mainly screen photos) but not "the heart rate will be wrong" (recording-driven, not picture-driven). The simulated-trained detector does not transfer (0.52); a detector trained on real captures does for no output.
- Cautions: one competition dataset / capture setups (other phones and papers unknown); 43 events; exploratory; needs a new dataset to confirm.

## 2026-11-08 - Own-phone confirmation set: pages prepared (no photos yet)
- Rules fixed first (docs/plan/analysis_plan_changes.md, "Own-phone confirmation set"). 30 PTB-XL recordings (seed 44; 21,649 candidates after removing the 150 used) rendered with the patched ECG-Image-Kit run locally (same code as the Colab sweeps; 2200x1700; header shows P01-P30). Files: results/ownphotos/pages/P01.png ... P30.png, ECG_pages_P01_P30.pdf (30 MB, 200 dpi), pages_mapping.csv (page -> ecg_id), source_records/ (the exact .hea/.dat used for the reference).
- Next: user shows the pages full screen on the laptop and takes 2 phone photos per page (straight on, angled ~30 degrees) = 60 photos; I build the Kaggle digitiser + photo-score notebook (frozen models, scored locally).
- 2026-11-08 (night): own-photo Kaggle notebook built (colab/MediSense_Cardio_OwnPhotos_Kaggle.ipynb; copied to Downloads) and its logic executed locally with 6 fake phone photos and a stubbed digitiser (the real digitiser cannot run locally). Analysis script scripts/analysis/section_O_ownphotos.py executed end-to-end on 60 fake photos (random scores; fake outputs deleted so they cannot be mistaken for results). Waiting for the user's 60 photos (planned for the morning of 2026-11-09).

## 2026-11-10 - Own-phone photos received and checked (before any analysis)
- C:\Users\Nihar Sai\Downloads\ownphotos: 60 JPG files, all readable, taken 13:26-13:34 on 2026-11-10 (EXIF orientation 1). Time gaps are consistent with 30 pairs (straight, angled; A-B 3-5 s apart, 8-15 s between pages; first pair 25 s). Matching by file-name order checked by eye on 9 photos: P01 A/B, P02 A/B, P13 A, P21 A, P30 A/B all correct.
- DEVIATIONS (to report): (1) resolution is mixed: 31 photos 1440x1080, 29 photos 4096x3072 (the camera mode changed during the session; the first 13 are small, the last 23 are large); photo scores such as the blur score depend on image size, so results will also be shown by resolution group. (2) One file is a burst-mode photo (IMG_20261110_133015_Burst01.jpg). (3) Some photos show the whole laptop and a washed-out white screen; the red grid appears grey (as in competition screen photos).
- Frozen models and rules are unchanged (analysis_plan_changes.md 2026-11-08).

## 2026-11-10 - Own-phone confirmation RESULT (Section O; frozen models, rules fixed 2026-11-08)
- Kaggle run (GPU, same digitiser commit 97a15087 and weights) of the 60 photos; results (2).zip validated (60 npz + 3 files), saved in results/ownphotos/kaggle_out/. Script scripts/analysis/section_O_ownphotos.py -> results/analysis/SECTION_O.md, sectionO_*.csv.
- No output (no usable heart rate): 6/60 photos (10%), vs 39% in the competition screen photos. With an output: 14/54 wrong (>5 bpm, cleaned) = 26%, median error of the wrong ones 14 bpm; the clean pages of the competition set had ~4% wrong.
- PRE-FIXED CRITERION (photo model predicts no output, AUC >= 0.70 and lower bound > 0.50): NOT MET. All-types model AUC 0.552 (0.32-0.80); screen-only model 0.519 (0.24-0.77). Only 6 events, so low power, but the result does NOT confirm the earlier "promising" finding. Post hoc (not in the plan): the competition-trained photo model for "no output or wrong" 0.506 (0.36-0.66); for wrong only 0.388 (0.24-0.54).
- OUTPUT CHECK (frozen, trained on simulated damage with cleaned labels): AUC 0.855 (0.71-0.96) for wrong HR among the 54 photos with an output (14 wrong): holds on a new phone, descriptive.
- Post hoc breakdown: angled photos B 13 of 30 bad vs straight A 5 of 30; paired by page: A ok & B bad 11, A bad & B ok 1 (exact p = 0.006). Angle and size are confounded (the camera size changed during the session): angled + small (1440x1080) 13/15 bad, angled + large 2/15, straight small 3/16, straight large 2/14. So failures concentrate in angled low-resolution photos.
- Reading for the report: (1) the photo-score predictor of failure does NOT generalise to a new device (and its failure type changes: here wrong readings, not missing output); (2) the reference-free output check does carry over; (3) a simple capture-condition finding: low resolution plus an angled view breaks the heart rate. Limits: one phone, one screen, 30 recordings, 14 wrong readings, size/angle confounded, deviation (mixed size) reported.

## 2026-11-10 - Traffic-light safeguard built, frozen and evaluated once (Section P; steps 2 of the plan)
- Tool: safeguard/ecg_traffic_light.py (numpy + neurokit2), model.json built by safeguard/train_safeguard.py from the simulated new 100 only (1,262 images, 113 wrong). Rules fixed first (analysis_plan_changes.md 2026-11-10); ONE rule added before any real-data evaluation after a unit test showed pure noise got GREEN: an out-of-range guard (GREEN -> AMBER if a feature is outside the training range). Tests: safeguard/tests/test_traffic_light.py (packaged features reproduce the analysis features to 1e-14 on 20 signals; noise -> AMBER; missing/NaN/short signals -> RED; thresholds). Thresholds: AMBER 0.2585, RED 0.7823 (out-of-fold rules).
- Training (out-of-fold): GREEN 903 readings 1.3% wrong; AMBER 219 14.2%; RED 140 50.0%.
- EVALUATION (frozen tool, once; safeguard/evaluate_safeguard.py, summarize_safeguard.py -> results/analysis/SECTION_P.md): competition real captures, images with an output: GREEN 917 readings, 2 wrong (0.2%); AMBER 204, 14 wrong (6.9%); RED 82, 30 wrong (36.6%); AMBER+RED hold 96% of all wrong readings and 21% of right ones. Including no-output images (RED by rule): RED 139 readings, 62.6% bad, holding 84% of all bad. Own phone (54 with output): GREEN 22, 0 wrong; AMBER 15, 1 wrong; RED 17, 13 wrong (76.5%); including 6 no-usable-HR photos RED 23, 19 bad (82.6%). Own phone straight vs angled: angled RED 17 of 30 photos (15 wrong), straight RED 6 of 30.
- Caveats: Wilson intervals treat images as independent (optimistic); real captures < 100 wrong readings; own phone: one phone, 30 recordings, mixed photo size; not a medical device.
- 2026-11-10: step 3 done: one-click demo notebook colab/MediSense_Cardio_TrafficLight_Demo.ipynb (built by scripts/notebook_builders/build_safeguard_demo_notebook.py; everything embedded; executed end-to-end locally; copied to Downloads). Six examples chosen by a fixed rule from the own-phone photos. A GREEN light with minor notes now says "minor note (did not change the light)" so a GREEN never lists warnings as reasons; lights unchanged.
- 2026-11-10: step 4 prepared (not yet run): scripts/preprocess/page_straighten.py (page found in 60/60 own photos, checked by eye), colab/MediSense_Cardio_FixExperiment_Kaggle.ipynb (executed locally end to end with a stubbed digitiser: 180 prepared images, 180 outputs; copied to Downloads), scripts/analysis/section_Q_fixexp.py (tested on fake identical-to-original outputs: no change, p = 1; fake outputs deleted). Rules fixed first (analysis_plan_changes.md). Waiting for the user's Kaggle run.
- 2026-11-11: step 4 RUN DONE (Kaggle commit, 180 images digitised, all 180 outputs; unpacked to results/ownphotos/fixexp_out/; analysis: scripts/analysis/section_Q_fixexp.py -> results/analysis/SECTION_Q.md, sectionQ_*.csv). EXPLORATORY, rules fixed beforehand. 60 own-phone photos, bad = no usable HR or wrong (>5 bpm, cleaned). Original 20 bad (6 no HR, 14 wrong). V1 enlarge 12 bad (exact p 0.0215, Holm 0.0215, improves); V2 straighten 2 bad (newly bad 1, newly good 19, Holm 0.0001, improves); V3 straighten+enlarge 6 bad (Holm 0.0087, improves). Angled+small (15): original 13 bad -> V1 8, V2 1, V3 2. Page found 60/60 (checked by eye earlier). Traffic lights on V2: GREEN 48 (1 wrong), AMBER 10 (1 wrong), RED 2 (0 wrong); original GREEN 22 (0 wrong). Caveats: one phone, one screen, 30 recordings, photos of a laptop screen (page edge easy to find), one post-hoc choice of fixed output size (2200x1700), 60 photos are not independent (30 pages x 2 shots), the fix was designed after seeing the failures on the same photos (exploratory, needs new photos to confirm); safeguard was frozen earlier and was not retrained.
- 2026-11-11: confirmation set for the straightening fix prepared (no photos yet). 20 new PTB-XL recordings (seed 45), pages Q01-Q20 rendered with the same tool (2200x1700, checked Q05 by eye), files in results/ownphotos2/ (pages/, ECG_pages_Q01_Q20.pdf 20.6 MB, pages_mapping.csv, source_records/). Rules logged in analysis_plan_changes.md before any photo. Next: user shows pages on the laptop and takes 2 photos per page (straight, angled).
- 2026-11-11 (evening): 40 new photos received (Downloads\ownphotos2; taken 19:19-19:22; 40 jpg, all open; 10 at 1440x1080 and 30 at 4096x3072; two files named Burst01). Matching by name order checked by eye on the header of ALL 40 photos: #1/#2 = Q01 (straight/angled) ... #39/#40 = Q20, order correct. Page found 40/40, page fully inside the frame (smallest margin 7% of the short side). Angled photos: left/right page-edge height ratio median 0.77 (first set 0.84): same side as the first set, a little stronger angle. Own mistake corrected: I first told the user the first set was taken from the left; the measurement shows the right-hand edge is the larger one in both sets (phone on the same side in both). Notebook colab/MediSense_Cardio_FixConfirm_Kaggle.ipynb built (scripts/notebook_builders/build_fix_confirm_notebook.py; dataset ownphotos2; V0-V3 = 160 images; variant-making cells run locally on the real 40 photos: 160 images, page found 40/40). Next: user uploads dataset ownphotos2 to Kaggle and runs the notebook; I write and run the analysis (rules in analysis_plan_changes.md 2026-11-11).
- 2026-11-11 (evening): analysis script for the confirmation set written and tested on fake outputs (scripts/analysis/section_Q2_confirm.py; fake outputs deleted so they cannot be mistaken for results). Primary = V2 vs V0 on 40 photos, exact paired test, alpha 0.05; words 'confirmed' / 'not confirmed' only. Waiting for the user's Kaggle run (dataset ownphotos2 + notebook MediSense_Cardio_FixConfirm_Kaggle.ipynb, ~1 hour).
- 2026-11-11 (night): docs/reports/METHODS_AND_FORMULAE.md rewritten as the complete methods and formulae from the first sweep to the confirmation set (17 sections: data and reference, page geometry, six damage formulas, arms B/C/C+/own phone, digitiser, heart-rate measures (original and cleaned), statistics, five photo scores, 15 output features, detector agreement, clean-page diagnosis, traffic light thresholds and guard, straightening, fixed-settings table, chronological table with PRE-SPECIFIED / EXPLORATORY / POST HOC status, limits). Checked against the code (degrade.py, image_quality.py, ecg_traffic_light.py, page_straighten.py, section_D.py/D2.py) and the rule log. Notes on how the closest papers write methods: docs/literature/methods_style_notes.md. Still to add after the Kaggle confirmation run: nothing in the methods (frozen); only results go in FINAL_NUMBERS.md.

## 2026-11-11 (night) - Confirmation of the straightening fix on 40 NEW photos: RESULT
- Kaggle run finished (160 images, 160 npz). Output unpacked to results/ownphotos2/confirm_out (from Downloads "results (7).zip", 23 MB). Analysis: `python -I scripts/analysis/section_Q2_confirm.py results/ownphotos2/confirm_out` -> results/analysis/SECTION_Q2.md and sectionQ2_*.csv.
- PRIMARY (rule fixed before the photos existed): V2 straighten vs V0 original, 40 photos. Bad 14 -> 2. Newly bad 0, newly good 12, exact McNemar p = 0.0005. Verdict by the pre-set rule: CONFIRMED.
- V0 bad 14/40 = 4 no usable HR + 10 wrong. V2 bad 2/40 = 0 no usable HR + 2 wrong. By shot (V0): straight 4/20, angled 10/20. (V2): straight 1/20, angled 1/20.
- Secondary (descriptive): V1 enlarge only 13/40 (p = 1.0, no help). V3 straighten big 3/40 (newly bad 1, newly good 12, p = 0.0034), no better than V2.
- Traffic light (not retrained), V2: GREEN 32 (0 bad), AMBER 7 (1 bad), RED 1 (1 bad). V0: GREEN 20 (0 bad), AMBER 7 (1 bad), RED 13 (13 bad). No bad page was GREEN in either.
- Pooled with first 60 (descriptive only): V0 34/100, V2 4/100.
- Limits: one phone, one screen, 20 recordings, two photos per page not independent; fix designed on the first 60 photos.

## 2026-11-11 (night) - Numbers frozen: results/FINAL_NUMBERS.md written
- results/FINAL_NUMBERS.md: every headline number with source section, label (PRE-SPECIFIED / EXPLORATORY / POST HOC), allowed and not-allowed claims, never-quote list.
- scripts/analysis/final_numbers_recompute.py -> results/analysis/FINAL_RECHECK.md: 36 numbers recomputed from raw files (simulated sweeps, bridge, Arm B, cleaned and original real-capture counts, confirmation set from the digitised signals, own-phone set 1, first fix experiment). All 36 match.
- First run showed 3 mismatches of 1 (blur 5: 16 vs 17; all-150 blur 5: 24 vs 25; real captures: 167 vs 168). Cause: saved heart-rate columns are rounded to 0.1 bpm; two readings differ by 5.02 and 5.04 bpm. Reports use the unrounded difference (correct under "more than 5 bpm"); the check script was changed to use diff_bpm. No reported number changed.
- This is a second script by the same author, not a second person: claims-register mark 4 stays open (suggested three numbers: new-100 resolution 5 = 47/99; confirmation bad 14 -> 2; competition GREEN wrong 2/917).
- CLAIMS_REGISTER.md (fingerprinted) not edited; proposed grades are written in FINAL_NUMBERS.md section 6.

## 2026-11-11 (night) - Review demo page built and tested (demo/)
- demo/pipeline.py (straighten -> Open-ECG-Digitizer commit 97a15087 with the two published weights, same settings file -> cleaned HR -> safeguard light), demo/app.py (Gradio 6.31, localhost:7860, queue of 1, no storage), demo/run_demo.bat, demo/README.md, 4 example photos from the confirmation set.
- Local digitiser: repo and weights already on the laptop (scripts/tools/Open-ECG-Digitizer, commit matches the study); PyTorch is the CPU build (no CUDA), about 50-60 s per photo. Gradio installed with pip (the only install).
- Checked: example photo Q01 straight -> 55.03 bpm GREEN (Kaggle 55.03, identical); Q06 angled with fix -> 63 bpm GREEN, without -> 108 bpm RED (Kaggle 62.6 / 107.9); noise and blank pictures -> RED no usable HR; non-image file refused by the page; full click-through in the browser pane worked.
- Not done / needs the user: CUDA PyTorch for speed (about 2.5 GB download, needs a yes); temporary public link (DEMO_SHARE=1, needs a yes); rehearsal on the day's laptop.

## 2026-11-11 (night) - GPU environment for the demo
- User approved the download. demo/.venv-gpu (about 5 GB) = PyTorch 2.14.1+cu126 and torchvision 0.29.1+cu126 from download.pytorch.org, plus scipy, opencv-python, neurokit2, scikit-image, scikit-learn, yacs, torch-tps, matplotlib, pandas, pyyaml, tqdm, gradio from PyPI. The main Python was not changed.
- RTX 3050 (4 GB) detected; all four example photos digitised on the GPU without out-of-memory; results equal to the Kaggle values (e.g. 62.56 / 107.89 / 106.28 / 65.90 bpm). Speed: about 33-35 s per photo (first one about 50 s) vs about 55 s on CPU - not the 15 s I first estimated (digitiser start-up and CPU-side steps dominate). demo/run_demo.bat uses the GPU environment; the pipeline falls back to CPU if a GPU run fails.

## 2026-11-13 - Gaps found in a review against standard digitisation practice; three of four filled (exploratory, after the freeze)
- A ChatGPT-style review of the project listed four gaps. Checked against the files: (1) no waveform errors in mV and ms, (2) no single dataset inventory sheet, (3) PR / QRS / QT not validated on digitised signals, (4) the "What an ECG shows" section not built. Most other recommendations were already done (paired data, 12SL references, straightening, reliability warning).
- Gap 2 done: `scripts/analysis/dataset_inventory.py` -> `results/DATASET_INVENTORY.csv` (340 recordings) and `.md`.
- Rules for gaps 1 and 3 written in `docs/plan/analysis_plan_changes.md` BEFORE the runs. Gap 3 needed one amendment, also before any result: NeuroKit2's wavelet delineation cannot run on the 2.5 s segment each lead (except II) covers on a page, so the measurement is on lead II only.
- Gap 1 done: `scripts/analysis/section_R_waveform_errors.py` -> `results/analysis/SECTION_R.md` (2,660 images, 99 s). Clean simulated pages: MAE 0.0107 mV, RMSE 0.0282 mV, r 0.974, R timing error 2.5 ms, R-peak height 0.08 mV too low. Blur 5: r 0.54; resolution 5: r 0.65; phone photo of print (real): r 0.47.
- Gap 3 done: `scripts/analysis/section_S_intervals_digitised.py` -> `results/analysis/SECTION_S.md`. Result: **no interval is validated.** QT median abs diff 36 ms on the original lead II and 26 ms on the digitised one (rule: 20 ms; only 54 to 55% within 40 ms; only 71% of recordings give a value); PR 78 ms; QRS 84 to 98 ms. The method fails on the original signal already; the photo adds 4 to 12 ms.
- Gap 4 done: the demo's main output is four short parts; the parameter table and the general list moved to a closed section "What an ECG shows (general information)". `demo/explain.py`, 10 tests pass.
- Recorded in `results/FINAL_NUMBERS.md` section 10 (no earlier number changed). Main numbers recounted from the CSVs by a separate command: all match.
- Open: the acceptance rule for intervals is the assistant's proposal and needs the guide; a better QT method (tangent / T-end on a median beat) would be a new development step on the first 50, then a test on the new 100 with a rule fixed in advance; not started.

## 2026-11-14 - A better QT method (exploratory): close, not validated
- User asked to try a better QT method. Rules written before any code ran (analysis_plan_changes.md, 2026-11-14). New code `scripts/analysis/section_T_better_qt.py` (median beat, slope-based QRS onset, tangent T end; 3 aggregators x 2 T-end methods).
- Development on the first 50 original signals (page-layout windows): chosen B_tangent (median over leads), offset -40.5 ms; development median error 10.9 ms; frozen in `results/analysis/sectionT_frozen.json`.
- Held-out test, once, on the new 100: original signal 7.8 ms typical error and it meets the pre-set rule; digitised clean page 13.5 ms, 92% within 40 ms, 100% with a value, but bias +10.5 ms against a limit of 10 ms, so NOT validated (0.5 ms over).
- "Try again": changing anything and re-running on the same 100 would have broken the held-out test, so the method, offset and thresholds were left untouched. Instead a confirmation on NEW data was fixed in writing first and run once: 100 own-phone photos (50 recordings). Straightened photos: 19.5 ms typical error, bias -6.0 ms, 100% with a value, but only 84% within 40 ms (needs 90%), so NOT confirmed. Set Q alone meets; set P does not.
- Compared with NeuroKit2 (36 ms, 69% with a value) this is a large improvement; the demo still says "Not measured" for QT. Recorded in FINAL_NUMBERS 10.5. Numbers recounted from the CSVs.
- Open: the acceptance thresholds still need the guide; a real fix for the remaining error would be a new development step with a new held-out set.

## 2026-11-14 - PR and QRS with my own method (exploratory): PR validated under the pre-set rule, QRS not
- User asked to also make PR and QRS measurable. Rules written first, including a stated physical limit (about 5 ms per pixel). Code: `scripts/analysis/section_U_pr_qrs.py` (--dev, --test, --confirm). Development on the first 50 original signals froze QRS = global measure, 5% slope, offset -7.6 ms and PR = median over leads, tangent P onset, offset +5.8 ms.
- Held-out test once on the new 100: PR meets the rule on the original signal and on digitised clean pages (typical error 8.2 and 7.3 ms, 97 to 99% within 40 ms, 98 to 99% with a value). QRS does not (13.2 ms on photos against 10 ms; 72% within 20 ms).
- Confirmation once on 100 new phone photos: PR meets on STRAIGHTENED photos (12.0 ms, bias +5.2, 95% within 40 ms, 95% with a value) but not on original photos (only 67% give a PR). QRS does not (18.2 ms, bias +15.8, 59% within 20 ms).
- PR error with NeuroKit2 was 78 ms; the new method is about 10 times better. The demo still shows PR and QRS as "Not measured"; adding PR (GREEN photos only, number only, no verdict) is an open decision for the user, and the guide has not approved the thresholds. Recorded in FINAL_NUMBERS 10.6; numbers recounted from the CSVs.

## 2026-11-14 - PR interval added to the demo (user: "Yes, add PR")
- `demo/pr_interval.py` runs the exact Section U method with the frozen candidate and offset (checked: reproduces 8 of 8 held-out values exactly). `demo/explain.py` shows PR as a number only (no verdict), only for a GREEN light, a straightened photo, a value of 50 to 400 ms and no "irregular beat spacing" report; the "not checked" list drops PR only when it is shown. 15 tests pass (PR hidden for AMBER, RED, no output, unstraightened, implausible and irregular cases; interval verdict words blocked).
- Found while doing it: recordings with no 12SL PR (6 of 99 held-out, 12 of 100 photos) had been left out of the PR statistics, and our method still gives a value for them (all 6 held-out); PR was never tested on rhythms without P waves. Recorded as a limit in FINAL_NUMBERS 10.6 and covered by the irregular-spacing guard (a precaution, not a validated filter).
- Six samples through the real pipeline: PR within 5 ms of 12SL on 4 of 5 comparable ones; sample 3 shows none (no P wave found); sample 4 has no 12SL value; sample 6 is RED. Live page checked on sample 2 (213 ms vs 212 ms).

## 2026-11-14 - Safety finding on PR: atrial fibrillation recordings get a made-up PR; guard tightened
- While answering "why does 12SL have no PR for some recordings" it turned out that all 6 held-out recordings without a 12SL PR are atrial fibrillation / flutter (PTB-XL rhythm labels carry likelihood 0.0 when present, which I had misread as "not AF earlier). Across PTB-XL 95% of 1,570 AF/flutter recordings have no 12SL PR. Our PR method gave a number for 6 of 6 held-out pages (170 to 244 ms) and 7 of 12 phone photos: meaningless numbers.
- The "irregular beat spacing" guard caught only 4 of the 6 pages. Added a second guard in the demo: PR hidden when rr_cv is above 0.12 or unknown (all 6 pages and all 8 AF phone photos hidden; about 15% of normal-rhythm photos also lose PR). Precaution calibrated on 14 cases, not validated. 16 tests pass (13 rr_cv values from the AF pages must hide PR).
- FINAL_NUMBERS 10.6 corrected: the PR result holds only where 12SL finds a P wave. Not yet re-run in the browser after this change.

## 2026-11-14 (night) - QRS, QT second attempt and AXIS on fresh data: set up, methods frozen, test pending
- User approved the full plan (stop rule: evening of Mon 16 Nov) and asked for axis after QRS/QT. Rules for both written first in analysis_plan_changes.md (three entries, including one AMENDMENT made before any fresh page was digitised, see below).
- Fresh test set: 100 PTB-XL recordings (seed 46; 7 with atrial fibrillation or flutter) and a development set of 1,000 more, none used before (`scripts/analysis/select_fresh_sets.py`, `results/fresh/`). Pages F001-F100 drawn locally with a patched COPY of ECG-Image-Kit (`scripts/analysis/make_fresh_pages.py`); a re-render of the old page Q01 differs only in the header text (0.07% of pixels). Digitising on the GPU: `scripts/analysis/digitise_fresh_pages.py` (about 45 s per page, resumable; prints no accuracy number).
- AMENDMENT (before any fresh page was seen): the first development run fitted `a x raw + b x RR + c` and got a slope of 0.19 for QT, i.e. a number that is mostly the population mean (a patient with a true QT of 480 ms would be shown about 410 ms: false reassurance, invisible to the error-based rule). The calibration may now only add an offset (QT: + b x RR + c; QRS: + c). The first run is kept in results/analysis/SECTION_V_dev_first_run.md.
- Frozen (development, 1,000 original recordings): QT = median over leads with the tangent T end (cross-validated typical error 8.8 ms, 90% within 40 ms); QRS = global 3% slope (7.0 ms, only 85% within 20 ms on the ORIGINAL signal, so a pass on photos is unlikely); AXIS = 6 limb leads, dominant deflection (3.6 degrees typical error, 97% within 30 degrees, 98% category agreement). Photo offsets for QT and QRS fitted once on the digitised clean pages of the earlier held-out 99.
- Next: when all 100 pages are digitised run `section_V_qrs_qt_v2.py --test` and `section_W_axis.py --test` ONCE, then `--confirm` for each ONCE on the phone photos, record in FINAL_NUMBERS, add validated parameters to the demo (number only).

## 2026-11-14 (night) - Fresh-data tests done: AXIS validated, QT and QRS not
- 100 fresh pages digitised (54 minutes, none failed); each test run ONCE, in the pre-set order (job log: results/analysis/section*_run.log).
- **Axis (Section W): validated for straightened photos.** Fresh pages 3.8 degrees typical error, 99% within 30 degrees (original signal 4.5 degrees, 99%); phone photos straightened 4.4 degrees, 95% within 30, 92% category agreement; not straightened photos fail (82% with a value). One real failure: recording P13 (12SL 148 degrees) read as -95 degrees, error 117 to 121 degrees; right-axis detection is not shown to work (no right-axis recording in the fresh test).
- **QT (Section V): meets the rule on fresh drawn pages (8.8 ms, 93% within 40 ms) but NOT on phone photos (bias -16.5 ms, 86% within 40 ms), and its slope against 12SL is 0.68 (limit 0.7 fixed in advance): not validated.** On the 7 atrial fibrillation pages QT is poor (bias -45.7 ms, one value 180 ms).
- **QRS duration (Section V): not validated** (fresh pages 9.2 ms but only 74% within 20 ms; phone photos 12.9 ms, 69%); slope 0.21 to 0.39 and recordings with a true QRS of 120 ms or more are read about 45 ms too short (a wide QRS would look normal), so it must never be shown.
- The slope and tail checks promised in the amendment were not printed by the test script; I computed them afterwards from the saved per-page CSV (before any decision) and say so in FINAL_NUMBERS 10.7.
- Demo: axis added as degrees only (GREEN + straightened + value; no verdict word; 19 tests pass; `demo/axis_deg.py` reproduces 10 of 10 tested values exactly). QT and QRS stay "Not measured". Recorded in FINAL_NUMBERS 10.7 and 10.8; main numbers recounted from the CSVs.

- Live page check (2026-11-14 night): sample 2 shows PR 213 ms and QRS axis -19 degrees (12SL: 212 ms, -19 degrees); six samples through the real pipeline: axis within 9 degrees of 12SL on all five GREEN ones, none shown for the RED one. Found: the digitiser is not fully deterministic (random tie-break in the line tracer), so PR of the same photo varied by 8 and 5 ms between runs (sample 1: 171.9 vs 163.7 ms); recorded in demo/new_samples/README.md, repeat variation not yet measured on its own.

## 2026-11-14 (night) - Third attempt at QT and QRS duration: development result
- User asked to complete the validation of QT and QRS duration before P, T and ST. Rules for a third attempt written first (analysis_plan_changes.md, 'third'): a combined-lead (global activity) method, a NEW sealed test set G001-G100 (seed 47, 9 with atrial fibrillation/flutter), 40 NEW phone photos of G001-G020 from the user, stricter rule (slope >= 0.8, tail checks).
- Development (1,100 recordings, 5-fold CV, `scripts/analysis/section_X_global_qrs_qt.py --dev`): **QT: no candidate is eligible** (best slopes 0.61 to 0.63 against the 0.8 filter; qt_tan 6.6 ms typical error, 98% with a value), so by the pre-set rule nothing is frozen and the QT attempt STOPS; the combined-lead curve does not remove the compression toward the middle. **QRS duration: qrs_abs_5 frozen** (CV 6.1 ms, 89% within 20 ms, slope 0.81); photo offset -10.3 ms fitted on 199 digitised pages (in-sample slope 0.99, not a test).
- Running: drawing and digitising the 100 G pages (background). Next: make the 20-page PDF for the user's photos (scripts/analysis/make_photo_pdf.py), then QRS test once on G pages (`section_X --test`), confirmation once on the 40 photos (`digitise_new_photos.py`, `section_X --confirm`). Stop rule: Sun 15 Nov evening.

- 2026-11-14 (night) note on the page HEADER: the drawing tool cuts the "ID:" header text at forward slashes, so pages drawn from a Windows backslash path print the whole folder path (overlapping the "Name:" label). This affected F001-F100 and the sealed G001-G100 pages (their signal, kit and settings are identical to the earlier pages; only header text differs; the earlier pages P, Q and the first 100 had the short header). The F-page test results were not affected visibly, but it is a deviation to state as a limit. For the 20 pages the user PHOTOGRAPHS (G001-G020) the pages were redrawn with the short header ("ID: inpG\G001", like Q01) so the photos match the earlier photo sets: `scripts/analysis/make_photo_pages.py` (differs from the sealed G001 page in 0.19% of pixels, rows 22 to 53 = header only). The PDF `results/fresh_g/ECG_pages_G001_G020.pdf` was rebuilt from these pages.

## 2026-11-14 (afternoon) - Third attempt QRS/QT run
40 phone photos of G001-G020 digitised (all pages found, all with output). QT not tested (no candidate passed slope filter). QRS: page test once (a) fails slope 0.79, (b) meets; photo confirmation once fails (bias +15.4 ms, slope 0.74). QRS duration NOT validated; recorded as FINAL_NUMBERS 10.9. Stop rule (Sun 15 Nov) reached for QT/QRS: closed.

## 2026-11-14 (late afternoon) - P and T wave amplitude (Section Y)
Rules logged first. ST, P duration, T duration not attempted (commercial tools disagree). T amplitude stopped in development (slope 0.68). P amplitude: page test meets (a)+(b); photo confirmation fails on slope 0.77. NOT validated; FINAL_NUMBERS 10.10. Demo unchanged: all still 'Not measured by this tool'.

## 2026-11-14 (evening) - Simulated phone-photo test (Section Z)
120 simulated photos of pages G021-G080, digitised as V0 and V2; primary test run once: bad 64 to 21 of 120, newly bad 5, newly good 48, confirmed in simulation. Traffic light on V2: GREEN 1 bad of 71. Recorded as FINAL_NUMBERS 10.11. Printed-paper test (Section H) prepared: pages H01-H20, PDF, instructions, scripts; waiting for the user's 40 photos.

## 2026-11-14 (late night) - Reproducibility package, risk-coverage, intervals + Bland-Altman, failure gallery (exploratory, after the freeze)
- User listed seven improvements (printed-paper validation, independent check, intervals and Bland-Altman, failure gallery, risk-coverage, reproducibility package, guide approval of thresholds). Items 6, 5, 3, 4 done here; 1, 2, 7 need the user, a second person and the guide.
- Item 6: new folder `reproducibility/` (REPRODUCE.md, ENVIRONMENT.md, SECOND_PERSON_CHECK.md, two pip freezes, two tool patches, weight checksums, tool commits). The 36-number recheck was rerun: ALL MATCH (`results/reproducibility/recompute_run_2026-11-14.log`); traffic-light tests and the 19 wording tests pass. New script `second_person_green_count.py` gives the third check number (2/917). Repeat variation of the demo pipeline measured on 10 photos x 3 runs (`repeat_variation_demo.py`, results in `results/reproducibility/`).
- Item 5: Section RC (rules logged first). On the competition captures answering the lowest-risk 80% leaves 0.89% bad (random 8.2%); photo detector about 4%; own-phone set 18.8% (wide interval).
- Item 3: Section CI (rules logged first). A first version used the absolute difference and failed its own check against the frozen Bland-Altman numbers; fixed before recording. Cluster intervals widen but keep the story; PR and axis photo results met the 90% rule by point estimate with the lower interval end at about 89%.
- Item 4: Section FG (rules logged first). GREEN-but-wrong cards show a trace that does not match the truth (r 0.06, 0.20); other cards show a good trace with a wrong number (heart-rate step) or an upside-down aVF (axis failure).
- Found on the way: the damage called "faded grid" lowers the contrast of the whole page (wording note in FINAL_NUMBERS 10.15). Recorded in FINAL_NUMBERS 10.12 to 10.15. Not done: git commit and zip (waiting for the user's yes); printed-paper photos (user); second-person recheck; guide sheet for the thresholds.

## 2026-11-14 (late night, second pass) - the four items redone after the user said "try again"
- I told the user what was weak in my first versions and fixed it: (6) the package was never tested in a clean environment, its package list was a dump of the whole Python, there was no one-command check; (5) risk-coverage lacked the 40 new photos and the 120 simulated photos; (3) bell-curve limits for the axis were inflated by one failure, the heart-rate measure differed between panels, bootstrap numbers depended on call order; (4) two cards had no picture, one was empty, failure types were missing.
- Done: `requirements_analysis_minimal.txt` (9 packages) and `run_all_checks.py`; clean-environment test passed (4 checks PASS, result tables byte-identical to the main Python). Risk-coverage with sets D and E (recomputed lights equal saved lights on 320 of 320 images): the "about 1% bad among the answered" holds on the competition captures and on the straightened real photos but NOT on the harder simulated photos (10.4% at 80% coverage, 11.3% for GREEN + AMBER). CI: percentile limits, cleaned measure, rule table, own seed per interval. Gallery: 10 cards (amplitude shrink, false alarm on an AF page added; card 8 shows its trace). Amendments logged in `analysis_plan_changes.md`; FINAL_NUMBERS 10.12 to 10.15 rewritten.
- Still not possible here: pictures for the two competition cards (image files not on this computer; the Kaggle set would need a download and a yes).

## 2026-11-15 - Seeded demo (improvement 3 of the list): cause found, fixed in the wrapper, test passed
- Cause: unseeded `torch.randn(...) * 1e-6` tie-break in the digitiser. `demo/pipeline.py` now seeds torch (42) through a bootstrap; digitiser code untouched. Seeded repeat test 10 photos x 2 runs: identical on 10 of 10 (criterion fixed before the run: MET). Example photos match the study heart rate and lights. Earlier unseeded test under-counted the variation (sample 1: 163.7 vs 171.9 ms PR). Recorded in FINAL_NUMBERS 10.15. The running demo must be restarted to use it.

## 2026-11-15 - Heart health assessment module (the guide's request): built, tested once, in the demo
- Plan first (`docs/plan/HEART_HEALTH_MODULE_PLAN.md`), rules logged before training. Risk categories are impossible (no outcome data): the app shows "risk assessment not available". Findings = ECG patterns only.
- Data layer, small 1-D CNN, one training run (best epoch 7, fold-9 AUROC 0.926), one test: benchmark 0.88 to 0.97; drawn pages 0.78 to 0.91; phone photos MI 0.857, STTC 0.865, CD 0.875 pass; hypertrophy fails on drawn pages and photos; atrial fibrillation passes on drawn pages but has only 12 positive photos (not testable). Two post-hoc cautious display decisions logged (no percentages on photos; normal check hidden).
- Plotly dashboard (risk box, zoomable waveform, parameter charts with reference ranges, findings chart, eight-part results panel), new wording rules and 13 tests, new tab in `demo/app.py` (old tabs and 19 tests unchanged apart from one sentence). Checked in the browser on a real run (dark-theme text and chart label problems found and fixed). Six demo photos checked end to end. FINAL_NUMBERS section 11.
- Open: guide approval of the pass rules and of the wording; more labelled phone photos would be needed for hypertrophy and atrial fibrillation on photos; printed-paper test of the module.

## 2026-11-15 (evening) - Section AA: learned QRS duration and QT/QTc, tested once: not shown
- Rules logged first; 100 new sealed pages K drawn and digitised (interrupted at 75 by a session end, resumed); network trained once (best epoch 13), one digitised offset fitted on 200 development pages; single test. QRS passes the drawn pages (K 6.4 ms, 92% within 20, slope 0.92; G also) but fails photos (slope 0.65). QT misses K by 3 points (87% within 40 ms) and fails photos (bias +11, slope 0.50). QTc fails (slope). Nothing is shown; no second run (stop rule). FINAL_NUMBERS 10.16.

## 2026-11-15 (night) - Section AA second attempt: rules logged, fresh sets started, model fine-tuned and frozen (no test yet)
- Rules logged first (analysis_plan_changes.md, "second attempt"): attempt-1 test sets (K, G, 140 photos) became development data; new fresh sets: L pages (100 new recordings), L simulated photos (100), and the user's REAL printed-paper photos H (40) as the condition for showing anything in the app.
- Fine-tuned the attempt-1 network on 658 real digitised development items (400 pages, 140 real photos, 118 simulated photos; 450 recordings), 3 outputs (QRS, QT, QTc direct), grouped 5-fold CV chose 26 epochs, one final model frozen. Development CV (not a test): real-photo slopes QRS 0.76, QT 0.60, QTc 0.43 (attempt 1: 0.65, 0.50, 0.23): better, QT still compressed. Scripts: section_AA2_finetune.py, section_AA2_test.py (refuses to run twice), select_L_fresh.py, make_sim_photos_L.py, digitise_sim_photos_L.py.
- Background chain running: draw L pages, digitise, make and digitise L simulated photos (about 3.5 hours). Test NOT run: waiting for L data and for the user's H photos (printed paper).

## 2026-11-15 (night) - Heart health SECOND MODEL: rules + amendment logged, M set added, fine-tuned and frozen (no test yet)
- Rules logged first. Found that L has only 10 hypertrophy / 13 AF positives, so added fresh set M (100 recordings, 37 hypertrophy, 27 AF; amendment logged before any code), queued behind the L chain (pages, then simulated photos).
- Fine-tuned model 1 on 658 real digitised development items (5-fold CV by recording, epoch 3, Platt and thresholds from out-of-fold predictions), frozen. Development (not a test) out-of-fold AUROC: AF 0.988, hypertrophy 0.855, MI 0.902, STTC 0.918, CD 0.925, normal 0.959 (real photos alone: hypertrophy 0.855, AF 0.998). Test script section_HEALTH2_test.py refuses to run twice; waits for L, M and the user's H photos.

## 2026-11-16 (night) - Printed-paper photos (friend's phone) tested; dataset-only QRS/QT tested on fresh data
- Section H2 (22 straight full-resolution photos primary): bad 3 -> 2, p = 1.0, NOT confirmed; all 52 full-res: 15 -> 10, p = 0.23; finder as taken finds the page on 1 of 22 (needs the orientation step); GREEN wrong 2/19 after V2b. Section AA3 (PTB-XL-only QRS/QT model): QRS passes fresh drawn pages (4.1 ms) but not photos (bias +7.6, slope 0.65); QT fails everywhere; nothing shown. FINAL_NUMBERS 10.17, 10.18. Compressed copies (secondary) and the findings test (needs M) still to run.
