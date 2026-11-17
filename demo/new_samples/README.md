# New sample photos for the demo

Research prototype, not a medical device.

## What these files are
Six **simulated phone photos of an ECG shown on a laptop screen**. Each one starts from a clean ECG page of your Q-set (pages Q02, Q05, Q09, Q12, Q15, Q18). A script tilts the page, adds a dark screen edge, camera noise, a vignette, and then blur or shadow where noted. They are saved as 1440 x 1080 JPEGs, like your own phone photos.

They are **not real photos**. For a live test, show a page on your laptop and photograph it with your phone, which is how your 100 real phone photos were made.

## How to use them in the demo
1. Start the demo: double-click `demo\run_demo.bat`, then open http://127.0.0.1:7860.
2. Drop a sample into the upload box and press **Check this photo** (about 35 s).
3. Tick "Also run the original photo without straightening" to show what the straightening fix changes (takes twice as long).

## What each sample shows

| File | Page | True HR (bpm) | What was done | What it demonstrates |
|---|---|---|---|---|
| `sample1_straight_clean.jpg` | Q02 | 57.0 | Straight on, no damage | The normal case: the digitizer should read it, and the light is the baseline |
| `sample2_angled_left.jpg` | Q05 | 74.6 | Viewed from the left | Tilt. The straightener should flatten the page, and without it the reading can fail |
| `sample3_angled_from_below.jpg` | Q09 | 77.6 | Tilted on two axes | A harder tilt, the case where straightening helped most in the study (14 of 40 bad down to 2) |
| `sample4_dim_uneven_light.jpg` | Q12 | 69.3 | Shadow across the page | Uneven light. In the simulation, brightness damage barely changed the heart rate |
| `sample5_far_and_small.jpg` | Q15 | 62.4 | Page fills only half the frame | Few pixels per page, like the low-resolution damage that hurt the most (47% wrong at the worst level) |
| `sample6_blurry_and_angled.jpg` | Q18 | 48.3 | Out of focus and angled | Blur plus tilt. Heavy blur was the second-worst damage (17% wrong) |

The true heart rate is measured from the original PTB-XL 100 Hz lead II with the same code the study uses (cleaned measure). A reading is **wrong** if it is more than 5 bpm away.

## How to read the demo screen
- **Page after straightening:** the picture the digitizer actually reads.
- **Digitised lead II:** the signal it recovered from the picture.
- **Heart rate:** measured on that recovered signal.
- **Traffic light:**
  - GREEN: no warning.
  - AMBER: have a person check.
  - RED: do not trust the heart rate.
  - The reasons are listed beside it.
- A GREEN light is not a guarantee. In the study, GREEN readings on the competition captures were still wrong 0.2% of the time (2 of 917).

## About the ECG image itself
**What is on the page** (look at `sample2_angled_left.jpg`):
- **Pink-red grid.** Small squares are 1 mm and big squares are 5 mm. The grid is the ruler: 25 mm = 1 second across, 10 mm = 1 mV up.
- **Black trace.** The ECG line, 12 leads in the standard layout: row 1 is I, aVR, V1, V4; row 2 is II, aVL, V2, V5; row 3 is III, aVF, V3, V6. A long lead II strip runs along the bottom.
- **Square pulse at the left of each row.** The calibration mark, which shows how tall 1 mV is.
- **Text.** Lead names, "25mm/s", "10mm/mV" and the page label (Q05). The label is not the PTB-XL id.

**How it was made (digital to paper-style):** the 100 Hz numbers of a PTB-XL recording are plotted by ECG-Image-Kit at 200 dpi, so 1 pixel = 5.08 ms across and 0.0127 mV up. The clean page is 2200 x 1700 px. It looks like paper but is only pixels.

**Colour type:**
- The clean page is a PNG with 8-bit RGB plus an alpha channel (RGBA). The alpha is fully opaque and unused.
- The digitizer loads every image with `mode="RGB"`, so it always works on 3 channels (red, green, blue).
- The sample photos here are 8-bit RGB JPEGs, 1440 x 1080 px, with no alpha channel.
- The pink grid and black trace differ in their red, green and blue values, which is how the model separates grid from trace.
- A black-and-white scan would be three equal channels, with no grid colour to help. Your pages are colour only, which is a stated limit.

**What a photo changes:** tilt squeezes the grid, so pixels per millimetre differ across the page. Blur and low resolution smear the thin black line. Shadow changes the brightness. The straightener fixes tilt, and the traffic light warns when the signal looks wrong.

## What to say when you show it
"A photo of an ECG goes in. The page is straightened, the digitizer turns it back into a signal, we measure the heart rate, and a traffic light says whether to trust it. On bad photos the tool should say RED instead of giving a confident wrong number."

## Expected results (checked 2026-11-13 on this machine, GPU, with straightening)

| File | True HR | Read HR | Light | Plain reading |
|---|---|---|---|---|
| `sample1_straight_clean.jpg` | 57.0 | 56.9 | GREEN | Correct |
| `sample2_angled_left.jpg` | 74.6 | 74.6 | GREEN | Correct: the tilt was fixed |
| `sample3_angled_from_below.jpg` | 77.6 | 77.6 | GREEN | Correct: a harder tilt was fixed |
| `sample4_dim_uneven_light.jpg` | 69.3 | 69.4 | GREEN | Correct: the shadow did not matter |
| `sample5_far_and_small.jpg` | 62.4 | 62.4 | GREEN | Correct (the first attempt hit a temporary memory error, the rerun worked) |
| `sample6_blurry_and_angled.jpg` | 48.3 | 61.5 | **RED** | Wrong by 13 bpm, and the light correctly said not to trust it |

Five photos are read correctly with GREEN, and the one bad photo gets RED. This is a demonstration on simulated photos, not new evidence: the study numbers stay in `results/FINAL_NUMBERS.md`. The "straight" and "far" photos are easy cases, so do not present them as proof that the tool is accurate.

## The health condition behind each sample
Each picture was drawn from a real PTB-XL recording. The labels below are PTB-XL's own diagnosis labels (from `pages_mapping.csv` and `scp_statements.csv`). They are a dataset label, not a diagnosis made by this tool.

| Sample | Heart rate read | Condition labelled in PTB-XL | Can our tool see it? |
|---|---|---|---|
| 1 | 57 bpm | Normal ECG | n/a |
| 2 | 75 bpm | Left ventricular hypertrophy (thickened heart muscle), non-specific ischemic changes, non-specific conduction delay | **No** |
| 3 | 78 bpm | Complete left bundle branch block (a conduction problem) | **No** |
| 4 | 69 bpm | Incomplete right bundle branch block, non-specific ST changes | **No** |
| 5 | 62 bpm | Left ventricular hypertrophy, possible old inferior heart attack (low likelihood, 15 of 100) | **No** |
| 6 | 62 bpm (wrong, RED) | Normal ECG (likelihood 80 of 100) | n/a |

**The teaching point:** four of the six samples are abnormal ECGs, yet the tool reads a normal heart rate with GREEN on them, and it is right about the heart rate. The tool measures only how fast the heart beats. Conduction problems, thickened muscle and old heart attacks change the *shape and timing* of each beat, which this tool does not look at. So a GREEN light means "the heart rate was probably read correctly", never "this ECG is normal". This is the same reason the project's title is about false reassurance.

**What the demo says about health** (section "Your ECG photo, in plain words", fixed sentences, rules in `docs/plan/EXPLANATION_WORDING.md`):
- A table of the nine ECG parameters (heart rate, rhythm, P wave, PR, QRS, QT, ST, T wave, axis), each with its meaning and what the tool got from the photo.
- GREEN: the heart rate in plain words (slow below 60, usual range 60 to 100, fast above 100) and a rough beat-spacing note. AMBER: the heart rate with "we are not sure it is right". RED or no output: "Not given", and no comment on the heart.
- Every parameter except heart rate and rhythm says "Not measured by this tool". No QT number is given, because our own results show it is too weak for a patient-facing statement. It can be added if a QT check against the original 12SL values passes a rule written in advance.
- A general list of what an ECG can help doctors find (arrhythmia, heart attack signs, reduced blood supply, heart blocks, fast or slow heartbeat, thickened chambers, potassium or calcium changes), marked as general information and not a result for the patient.
- Always: it cannot diagnose anything and is not a medical device.
- The labelled condition above is shown only to the presenter (closed section "Technical details for the presenter"), and only for these six test samples. An uploaded photo never gets a condition, because the tool cannot know it.

## The demo now explains each photo
After you press **Check this photo**, a section called **About this photo (what the tool recognised)** appears under the plots. It says in plain words:
- the photo's size, file type and colour type;
- whether the page was found and straightened;
- which page layout the digitizer recognised, or that it could not match one;
- how many leads it read, and how many seconds of lead II;
- how many beats were found and the heart rate;
- whether five beat finders agree;
- what the traffic light means for this photo.

## PR interval on the six samples (checked 2026-11-14 after the atrial-fibrillation guard; GREEN, straightened and steady beat spacing only)

| Sample | Light | PR shown | 12SL PR for the same recording | Comment |
|---|---|---|---|---|
| 1 | GREEN | 172 ms | 168 ms | 4 ms apart |
| 2 | GREEN | 213 ms | 212 ms | 1 ms apart |
| 3 | GREEN | not shown | 172 ms | the method found no P wave, so nothing is shown (the row stays "Not measured") |
| 4 | GREEN | **not shown** (was 174 ms before the guard) | none | 12SL found no PR for this recording, so the number could not be checked; the beat-spacing guard (variation 0.14 > 0.12) now hides it |
| 5 | GREEN | 187 ms | 182 ms | 5 ms apart |
| 6 | RED | not shown | 182 ms | RED photos never show PR |

The three values that are still shown (samples 1, 2, 5) are within 5 ms of 12SL. This is a demonstration on drawn pages, not new evidence: the evidence is in `results/FINAL_NUMBERS.md` section 10.6, with its limits (the thresholds are not approved by the guide; recordings without a 12SL PR were left out of the statistics; PR was never tested on rhythms without P waves).

## Frontal QRS axis on the six samples (checked 2026-11-14, GREEN and straightened photos only; degrees, no verdict word)

| Sample | Light | Axis shown | 12SL axis | Difference |
|---|---|---|---|---|
| 1 | GREEN | 19 degrees | 11 | +8 |
| 2 | GREEN | -20 degrees | -19 | -1 |
| 3 | GREEN | 2 degrees | 9 | -7 |
| 4 | GREEN | -39 degrees | -30 | -9 |
| 5 | GREEN | 61 degrees | 55 | +6 |
| 6 | RED | not shown | 78 | |

All five shown values are within 9 degrees of 12SL. The evidence is in `results/FINAL_NUMBERS.md` section 10.8 (99% within 30 degrees on 100 fresh pages, 95% on 100 phone photos, one gross failure on one recording; right-axis detection not shown to work; thresholds not approved by the guide).

**Run-to-run note:** the digitiser breaks ties with a tiny random number, so the same photo gives slightly different signals on different runs. The PR of sample 1 came out 171.9 ms in one run and 163.7 ms in another (the 12SL value is 168 ms), and sample 5 gave 187.4 and 192.4 ms. This repeat variation (a few ms) is inside the quoted typical difference of about 12 ms, but it was not measured separately.
