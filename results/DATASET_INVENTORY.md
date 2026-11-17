# Dataset inventory (written by scripts/analysis/dataset_inventory.py)

One row per recording is in `DATASET_INVENTORY.csv` (columns: set, recording_id, ecg_id, signal source and rate, true signal available, number of leads, number of images and conditions, image type and size, calibration, whether digitised 12-lead signals are saved, 12SL availability and values, reference heart rates, flags).

## Per set

| Set | Recordings | Images | Image type | True signal | 12SL | Digitised signals saved |
|---|---|---|---|---|---|---|
| simulated first50 | 50 | 1550 | computer-drawn page (ECG-Image-Kit), colour RGBA PNG | 50 of 50 | 50 of 50 | 0 of 50 recordings |
| simulated new100 | 100 | 1300 | computer-drawn page (ECG-Image-Kit), colour RGBA PNG | 100 of 100 | 100 of 100 | 100 of 100 recordings |
| real captures Arm C | 40 | 360 | real scans and phone photos | 40 of 40 | 0 of 40 | 40 of 40 recordings |
| real captures C+ | 100 | 900 | real scans and phone photos | 100 of 100 | 0 of 100 | 100 of 100 recordings |
| own phone set 1 (P01-P30) | 30 | 60 | phone photo of a screen (page drawn by ECG-Image-Kit) | 30 of 30 | 30 of 30 | 30 of 30 recordings |
| own phone set 2 (Q01-Q20) | 20 | 40 | phone photo of a screen (page drawn by ECG-Image-Kit) | 20 of 20 | 20 of 20 | 20 of 20 recordings |

## Reference quality (simulated sets)

- Reference-uncertain (100 Hz and 500 Hz heart rates differ by more than 5 bpm): 20 of 150.
- PTB-XL quality flag (drift, static, burst noise, electrodes, extra beats, pacemaker): 45 of 150.

## What this sheet shows and what is missing

- Pairs: every image has a true digital signal. For the simulated sets and your phone pages the page IS drawn from that signal, so the pair is exact. For the real captures the Challenge provides the true signal (we exported lead II only, 10 s at 1,000 Hz; so waveform comparison for real captures is limited to lead II).
- 12SL commercial measurements exist for all PTB-XL recordings (PTB-XL+). They do not exist for the Challenge recordings, which have their own ids.
- The first 50 recordings have no saved digitised signals, so no waveform or interval error can be computed for them.
- No expert beat annotations (P, QRS, T boundaries) are used; 12SL and Glasgow medians are the interval references.
- Image quality is described by the damage type and level (simulated) or capture type (real), not by one quality number.
