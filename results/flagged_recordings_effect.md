# Effect of PTB-XL-flagged and hard recordings on the damage-type results (2026-11-04)

Target: heart rate unreadable or off by more than 5 bpm. Script: scripts/analysis/flagged_recordings_effect.py.

Flagged records among the 49: 14 (['08002_lr', '11236_lr', '12772_lr', '13323_lr', '14808_lr', '15673_lr', '16637_lr', '17191_lr', '17750_lr', '17820_lr', '18442_lr', '20052_lr', '20053_lr', '21504_lr']).
Top-5 hardest: ['01126_lr', '11236_lr', '13316_lr', '13323_lr', '14808_lr'].

## Overall
```
     set  records  tests  bad  bad_rate_%  clean_bad_%
     all       49   1519   99         6.5          4.1
no_flags       35   1085   38         3.5          0.0
 no_top5       44   1364   34         2.5          0.0
```

## Bad-reading rate (%) by damage type and level: all
```
level           1    2    3     4     5
axis                                   
blur          2.0  4.1  6.1  12.2  18.4
brightness    6.1  6.1  2.0   2.0   2.0
gridcontrast  6.1  4.1  4.1   4.1   4.1
jpeg          8.2  0.0  2.0   4.1   4.1
resolution    2.0  2.0  8.2  10.2  42.9
rotate        4.1  2.0  6.1   6.1  12.2
```

## Bad-reading rate (%) by damage type and level: no_flags
```
level           1    2    3    4     5
axis                                  
blur          0.0  0.0  5.7  8.6  14.3
brightness    2.9  2.9  0.0  0.0   0.0
gridcontrast  2.9  0.0  0.0  0.0   0.0
jpeg          8.6  0.0  0.0  0.0   2.9
resolution    0.0  0.0  5.7  8.6  40.0
rotate        0.0  0.0  0.0  0.0   5.7
```

## Bad-reading rate (%) by damage type and level: no_top5
```
level           1    2    3    4     5
axis                                  
blur          0.0  0.0  0.0  4.5  13.6
brightness    0.0  2.3  0.0  0.0   0.0
gridcontrast  0.0  0.0  0.0  0.0   0.0
jpeg          4.5  0.0  0.0  0.0   0.0
resolution    0.0  0.0  2.3  2.3  38.6
rotate        0.0  0.0  2.3  0.0   6.8
```

## Ranking of damage types, level5 (bad rate %)

- all: resolution 42.9, blur 18.4, rotate 12.2, jpeg 4.1, gridcontrast 4.1, brightness 2.0
- no_flags: resolution 40.0, blur 14.3, rotate 5.7, jpeg 2.9, brightness 0.0, gridcontrast 0.0
- no_top5: resolution 38.6, blur 13.6, rotate 6.8, brightness 0.0, jpeg 0.0, gridcontrast 0.0

## Ranking of damage types, pooled (bad rate %)

- all: resolution 13.1, blur 8.6, rotate 6.1, gridcontrast 4.5, brightness 3.7, jpeg 3.7
- no_flags: resolution 10.9, blur 5.7, jpeg 2.3, brightness 1.1, rotate 1.1, gridcontrast 0.6
- no_top5: resolution 8.6, blur 3.6, rotate 1.8, jpeg 0.9, brightness 0.5, gridcontrast 0.0
