# Our reference intervals vs PTB-XL+ algorithms (2026-11-04)

50 recordings (clean-image rows of results_v2.csv). Difference = first minus second. bias = mean difference; MAD = median absolute difference; p90 = 90th percentile of the absolute difference; rho = Spearman correlation.

Algorithms: Marquette 12SL and Glasgow (commercial, from a median beat) and ECGDeli (open). PTB-XL+ global values are in ms or bpm.

## heart rate (bpm)
```
         comparison  n  bias  mad  p90  rho
   NeuroKit2 - 12SL 50   0.5  0.4  3.1 0.99
NeuroKit2 - Glasgow 50   1.2  0.7  3.2 0.98
     12SL - Glasgow 50   0.7  1.0  1.0 0.99
```

## PR (ms)
```
         comparison  n   bias   mad   p90  rho
   NeuroKit2 - 12SL 46  -54.3  53.2  97.7 0.26
NeuroKit2 - Glasgow 50  -52.3  48.0 100.7 0.26
NeuroKit2 - ECGDeli 50 -168.1 170.3 203.0 0.43
     12SL - Glasgow 46    1.5   4.0  14.0 0.92
     12SL - ECGDeli 46 -108.9 105.5 139.0 0.53
  Glasgow - ECGDeli 50 -115.8 108.0 146.2 0.61
```

## QRS (ms)
```
         comparison  n  bias  mad   p90  rho
   NeuroKit2 - 12SL 50  81.3 73.6 136.2 0.15
NeuroKit2 - Glasgow 50  79.5 71.4 134.2 0.03
NeuroKit2 - ECGDeli 50  16.4 27.7  79.6 0.33
     12SL - Glasgow 50  -1.8  4.0  10.0 0.91
     12SL - ECGDeli 50 -64.9 66.0  80.2 0.61
  Glasgow - ECGDeli 50 -63.1 65.0  78.0 0.61
```

## QT (ms)
```
         comparison  n   bias   mad   p90  rho
   NeuroKit2 - 12SL 50   -0.5  47.4 113.8 0.43
NeuroKit2 - Glasgow 50    1.4  49.2  87.8 0.53
NeuroKit2 - ECGDeli 50 -101.5 100.0 189.2 0.53
     12SL - Glasgow 50    1.8   6.0  18.6 0.93
     12SL - ECGDeli 50 -101.0  95.0 167.3 0.70
  Glasgow - ECGDeli 50 -102.9 100.5 174.3 0.73
```

## QTc Bazett (ms)
```
         comparison  n  bias  mad   p90  rho
   NeuroKit2 - 12SL 50  -1.8 56.6 123.5 0.12
NeuroKit2 - Glasgow 50   1.9 54.6 108.8 0.02
     12SL - Glasgow 50   3.6  6.5  17.2 0.93
```

## Recordings called prolonged QTc (female >= 460 ms, male >= 450 ms), out of 50
```
                          source  prolonged    n
NeuroKit2 Bazett (our reference)         21  NaN
            NeuroKit2 Fridericia         16  NaN
                     12SL Bazett         11 50.0
                 12SL Fridericia          6 50.0
                  Glasgow Bazett          9 50.0
              Glasgow Fridericia          4 50.0
```

## Does 500 Hz fix it? NeuroKit2 at 100 Hz vs 500 Hz, each against 12SL (50 recordings)
```
quantity  source   n   rho   MAD(ms)  bias(ms)
PR        nk100   46  0.26   53.2    -54.3
PR        nk500   46  0.35   56.3    -58.5
QRS       nk100   50  0.15   73.6    +81.3
QRS       nk500   50  0.06   84.1    +93.5
QT        nk100   50  0.43   47.4     -0.5
QT        nk500   50  0.47   35.9    +13.9
QTc       nk100   50  0.12   56.6     -1.8
QTc       nk500   50  0.28   52.7    +19.7
```
No. The higher sampling rate does not make NeuroKit2's lead-II measurements track the commercial algorithms.

## Reading the two sections together
- Heart rate: NeuroKit2 agrees with 12SL and Glasgow (median abs difference 0.4 to 0.7 bpm, rho 0.98 to 0.99). The reference is fine.
- PR, QRS, QT, QTc: the two commercial algorithms agree with each other closely (median abs difference 4 to 6.5 ms, rho 0.91 to 0.93).
  NeuroKit2 (single lead, mean over beats) does not track either of them (rho 0.03 to 0.53, median abs difference 36 to 84 ms).
  QRS from NeuroKit2 is about 80 ms longer than 12SL on average. Part of the gap is definition (12-lead "global" intervals from a median
  beat vs lead II), but a low correlation is noise, not a definition offset.
- Prolonged QTc: NeuroKit2 Bazett calls 21 of 50 recordings prolonged; 12SL Bazett 11, Glasgow 9; with Fridericia 6 and 4.
- ECGDeli measures on yet another definition (QRS median 160 ms, PR 272 ms); it is not a like-for-like reference for these.

## Consequences
- Interval errors in results_v2.csv measure how far the digitised signal's NeuroKit2 intervals are from NeuroKit2 intervals on the
  original signal. That is a valid "is the measurement preserved" comparison, but it is not clinical accuracy.
- The QTc "truly prolonged" set (21 records) is not a reliable clinical truth, so QTc false reassurance should be described as
  "by this measurement method", not as a clinical rate. The heart-rate results are not affected.
- The extension notebook therefore saves all 12 digitised leads, so a more robust (multi-lead) interval method can be applied later
  without re-digitising.
