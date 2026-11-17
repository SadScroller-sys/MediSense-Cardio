# Reference heart rate: 100 Hz vs 500 Hz (check of 2026-11-04)

Script: run inline (NeuroKit2 0.3.0, wfdb 4.3.1) on the 50 study recordings; same peak detector and settings as the sweep notebook.
Our stored gt_hr (computed from the 100 Hz record the pages were drawn from) is reproduced to within 0.05 bpm.

## Finding 1: the reference heart rate depends on the sampling rate of the signal it is computed from
| Quantity | Value |
|---|---|
| Median abs difference, HR(500 Hz) minus HR(100 Hz) | 0.1 bpm |
| 90th percentile | 8.4 bpm |
| Maximum | 22.9 bpm (01126_lr: 49.5 vs 72.3) |
| Records differing by more than 5 bpm | 8 of 50 |
| Records differing by more than 10 bpm | 3 of 50 |

The detector finds different numbers of beats at the two rates (for example 8 vs 12 in 10 s), so on about one record in six the
"true" heart rate from this method is uncertain by more than our 5 bpm threshold.

## Finding 2: the digitised heart rate follows the 100 Hz reference, except for one recording
On the 8 recordings where the two references disagree, the digitised heart rate (clean image and mild damage) agrees with the
100 Hz reference on 7 of them (within 0.1 to 1.8 bpm). The page is drawn from the 100 Hz signal, so the comparison "digitised vs
100 Hz reference" is like for like. On the 42 recordings where the two references agree, digitised vs reference differ by a
median of 0.10 bpm.

Exception: 14808_lr (PTB-XL flag: extra beats, premature ventricular beats). Reference at 100 Hz 73.3 bpm, at 500 Hz 81.4 bpm,
digitised clean image 82.2 bpm. The digitised value matches the 500 Hz reference, so the 100 Hz reference looks wrong for this
recording. It is the single largest source of bad readings (27 of 31 versions, including the clean image).

## What it means
- Our damage results are not inflated by this: the like-for-like reference is the 100 Hz one for 7 of the 8 recordings.
- The largest "hard recording" (14808_lr, 27 of the 99 bad readings, bad even on the clean image) is mainly a reference or detector
  mismatch on an irregular recording, not an effect of image damage. This strengthens the point that most failures are about the
  recording, not the damage; it also means the 4.1% bad rate on clean images is one recording.
- The extension notebook records both references (gt_* at 100 Hz as before, gt500_* at 500 Hz), so this can be checked on 100 more recordings.
- Caveat: one detector (NeuroKit2 "neurokit" method) was used throughout; a different detector might disagree less.

## Clean-image aligned SNR (real data, 6 pilot images, lead II only; not the 50 study pages)
Median 10.3 dB, range 1.7 to 16.3 dB (n = 6; recordings 1 to 6 of PTB-XL, pilot renders in results/multi_sample_test).
The extension notebook will compute this for 100 recordings and for the damaged images. Do not quote the n = 6 figure as a result.
