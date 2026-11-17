# MediSense-Cardio — Plan (Simple Version)

*Plain English. For day-to-day use. See [PLAN.md](PLAN.md) for the technical version with sources — that's the one for your teacher and your paper.*

## Where things stand (2026-09-20, plain words)

- **The big experiment is done.** We made 1,550 damaged versions of ECG pictures (50 real recordings, 6 kinds of
  damage, 5 strengths each) and checked what the program could still read.
- **What we found:** the program is fine on clean pictures and mild damage. Only **very heavy blur or very low
  resolution** makes it wrongly say "heart rate normal" when it isn't. Tilting the picture doesn't give wrong
  answers, but sometimes no answer at all. Compression, faded grid lines and bad lighting barely matter.
- **A catch:** 6 of the 50 recordings are hard for the program to read (it fails on most of their versions), and 4 of those fail even when the picture is perfectly clean.
- **Not done yet:** checking timing measurements (PR/QRS/QT) and real diagnoses; the "can we tell the picture is
  bad?" part (Contribution 2); and the paper's Results section. The deadline is **2026-09-28**.
- Details: [SWEEP-RESULTS.md](SWEEP-RESULTS.md) and the newest entries in [PROGRESS-LOG.md](PROGRESS-LOG.md).

## What your project is

A patient has an ECG printout. It is paper with squiggly lines. They cannot read it.

Your app will:

1. Take a **photo** of the paper
2. Turn the squiggly lines back into **numbers** (like "heart rate = 72")
3. Explain those numbers in **simple words**
4. Never say "you have a disease" — only state facts, then say "go see a doctor"

That part of your plan is good. Keep it.

## The problem: you also need something new

College will not accept "I built an app." You must find something nobody knew before.

Your plan said the new thing was *"we joined these pieces together."*

I searched. Other people already did each piece. So that answer is weak, and a teacher can easily attack it.

## Your new discovery

What happens if the **photo is bad**? The hand shakes. The light is poor. The paper is bent.

- The real answer was **480**. That is bad. This person needs a doctor.
- The blurry photo makes your app read **420**.
- Your app says: **"You are normal. Nothing to worry about."**
- **The patient stays home. But they were not fine.**

A bad photo became bad medical advice.

**Nobody has measured this.** Other researchers only check "did we read the lines correctly?" They stop there. They never ask "did the patient get told the wrong thing?"

That is your discovery. You can prove it with just your laptop and free data. No permission forms. No interviewing people.

## You will do two new things

**Thing 1 — Measure the problem.**
Take good ECGs where you already know the right answer. Damage the photos on purpose: blur them, tilt them, darken them. Run them through your app. Count how often the app tells the patient something wrong.

**Thing 2 — Fix the problem.**
Teach the app to notice a bad photo and say:
> *"Your reading is about 460, but this photo was unclear, so this may not be exact. Please confirm with your doctor."*

Right now, every app in the world just states the number confidently, even when it is wrong.

## Your title

> **From Paper to Patient: Quantifying and Mitigating Digitization-Induced False Reassurance in Automated ECG Explanation**

| Part | Normal words |
|---|---|
| From Paper to Patient | The journey: paper → a person reading it |
| Quantifying | Measuring. Thing 1 |
| Mitigating | Fixing. Thing 2 |
| False Reassurance | The app says "you're fine" when you are not |
| Digitization-Induced | The bad photo caused it |

In one sentence, the title means:
> **"Bad photos can make a health app wrongly tell people they are fine. We measured how often. Then we fixed it."**

## What was wrong in your original plan

**1. You cannot test your own filter with itself.** 🔴

Your app has a filter that blocks unsafe sentences. You planned to test that filter by using the filter. That is like marking your own exam paper — you will always score 100%. Someone else must check the answers.

**2. Your "new idea" was already partly done.** 🔴

Fixed by the discovery above.

**3. You wrote "use Node.js OR FastAPI" and never chose.** ✅ Settled (2026-08-10)

Confirmed with your teacher: no specific language is required. Going with **FastAPI** — your whole project is one language (Python) instead of two, which means less work connecting the pieces.

**4. One dataset (MIMIC) needs special permission.** 🟠

It takes 2 to 6 weeks, with training courses and forms. You marked it "optional." Then drop it, or start today. Do not let an optional thing block you.

**5. Measure accuracy in two ways, not one.** 🟡

One way misses small details. And small details are exactly what your app measures. Use both.

**6. Free AI accounts have daily limits.** 🟡

You will send thousands of requests. Save every answer to a file. Then you never pay twice for the same question, and you keep the records your paper needs.

**7. Skip the plugin setup for now.** ⚪

It does not affect your grade. Do it after your first review.

## What to do next

**Step 1 — Ask your teacher two questions. Today. No coding.**
- *"Is the bad-photo idea new enough to count as research?"*
- *"Must I use a specific technology?"*

Do this first. If the answer to the first is no, everything else is wasted work.

**Step 2 — Test that the tools work. One day.**

Take **one** ECG. Push it through every step. Write ugly code. Throw it away after.

You are checking one thing only: *do all the pieces connect on my computer?*

If something is broken, you lose one day. If you skip this, you find out in two months.

**Step 3 — Set up the folder properly. 30 minutes.**

Tell Git to ignore the data folder **before** you download the data. The data is 3 GB. Once it is inside Git, removing it is very hard.

## Three traps to avoid

**Trap 1 — Starting with the website.** The login page and the dashboard are fun and easy. That is why they are dangerous. They carry no risk, so building them first means you meet the hard part in month three with no time left.

**Trap 2 — Forgetting to include sick patients.** When you pick your test ECGs, you must include people with **abnormal** readings. If every test patient is healthy, the app can never wrongly say "you are fine" — because they *are* fine. You would run the whole experiment and measure nothing. Decide this early; fixing it later means starting over.

**Trap 3 — Picking a closed-box tool.** Some tools take a photo and give numbers, but never tell you how confident they were. Your fix needs that confidence. **Solution:** don't ask the tool. Check the photo yourself — is it blurry, tilted, dark, too small? That works with any tool, and it is better, because you can check *before* processing and just ask for a clearer photo.

## Getting a bad result is fine

If your fix does not work, **that is still a real finding.** "We tried to detect bad photos automatically and here is why it is harder than expected" is a genuine research result. It is not a failed project. Write it down honestly either way.
