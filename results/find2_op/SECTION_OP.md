# New operating point for the 8 research-only patterns (EXPLORATORY; rules logged before the thresholds were computed)

Thresholds chosen on validation data only (specificity 0.97 there; 0.95 and 0.99 as a sensitivity analysis). The sets below were seen before for other analyses, so this is not a new confirmatory test.

## Share of items flagged (at least one of the 8 patterns)

| Set | Threshold | Clean items | Clean items flagged | Items with a pattern | Of those flagged | Flags per clean item |
|---|---|---|---|---|---|---|
| T2 drawn pages (300) | old Youden | 176 | 86 (49%) | 124 | 123 (99%) | 0.80 |
| T2 drawn pages (300) | spec 0.95 | 176 | 52 (30%) | 124 | 105 (85%) | 0.40 |
| T2 drawn pages (300) | spec 0.97 (used) | 176 | 34 (19%) | 124 | 93 (75%) | 0.24 |
| T2 drawn pages (300) | spec 0.99 | 176 | 17 (10%) | 124 | 73 (59%) | 0.10 |
| T3 screen photos (140) | old Youden | 88 | 63 (72%) | 52 | 51 (98%) | 1.38 |
| T3 screen photos (140) | spec 0.95 | 88 | 43 (49%) | 52 | 47 (90%) | 0.75 |
| T3 screen photos (140) | spec 0.97 (used) | 88 | 26 (30%) | 52 | 40 (77%) | 0.39 |
| T3 screen photos (140) | spec 0.99 | 88 | 15 (17%) | 52 | 33 (63%) | 0.22 |
| set N drawn pages (120) | old Youden | 4 | 4 (100%) | 116 | 113 (97%) | 3.00 |
| set N drawn pages (120) | spec 0.95 | 4 | 4 (100%) | 116 | 109 (94%) | 2.50 |
| set N drawn pages (120) | spec 0.97 (used) | 4 | 3 (75%) | 116 | 102 (88%) | 1.50 |
| set N drawn pages (120) | spec 0.99 | 4 | 2 (50%) | 116 | 74 (64%) | 0.75 |
| set N simulated photos (120) | old Youden | 4 | 4 (100%) | 116 | 114 (98%) | 3.75 |
| set N simulated photos (120) | spec 0.95 | 4 | 4 (100%) | 116 | 112 (97%) | 2.50 |
| set N simulated photos (120) | spec 0.97 (used) | 4 | 2 (50%) | 116 | 102 (88%) | 1.00 |
| set N simulated photos (120) | spec 0.99 | 4 | 2 (50%) | 116 | 84 (72%) | 0.75 |

## Sensitivity / specificity per pattern (old Youden threshold, new threshold used: specificity 0.97 on validation)

| Set | Pattern | Positives | Old sens / spec | New sens / spec |
|---|---|---|---|---|
| T2 drawn pages (300) | A:ASMI | 34 | 94 / 84 | 82 / 94 |
| T2 drawn pages (300) | A:NDT | 25 | 80 / 82 | 16 / 98 |
| T2 drawn pages (300) | A:LVH | 21 | 81 / 85 | 67 / 95 |
| T2 drawn pages (300) | A:LAFB | 25 | 92 / 91 | 72 / 98 |
| T2 drawn pages (300) | A:IRBBB | 22 | 91 / 90 | 50 / 97 |
| T2 drawn pages (300) | B:AF | 23 | 91 / 87 | 91 / 92 |
| T2 drawn pages (300) | B:LBBB | 2 | 50 / 96 | 50 / 95 |
| T2 drawn pages (300) | B:1dAVb | 12 | 100 / 76 | 50 / 97 |
| T3 screen photos (140) | A:ASMI | 4 | 100 / 77 | 100 / 89 |
| T3 screen photos (140) | A:NDT | 12 | 33 / 73 | 0 / 98 |
| T3 screen photos (140) | A:LVH | 16 | 94 / 67 | 69 / 81 |
| T3 screen photos (140) | A:LAFB | 10 | 90 / 89 | 40 / 98 |
| T3 screen photos (140) | A:IRBBB | 8 | 75 / 96 | 12 / 100 |
| T3 screen photos (140) | B:AF | 12 | 100 / 81 | 100 / 89 |
| T3 screen photos (140) | B:LBBB | 4 | 100 / 94 | 100 / 93 |
| T3 screen photos (140) | B:1dAVb | 4 | 100 / 61 | 100 / 97 |
| set N drawn pages (120) | A:ASMI | 26 | 92 / 66 | 73 / 86 |
| set N drawn pages (120) | A:NDT | 2 | 100 / 87 | 50 / 98 |
| set N drawn pages (120) | A:LVH | 24 | 67 / 88 | 46 / 95 |
| set N drawn pages (120) | A:LAFB | 35 | 91 / 85 | 57 / 98 |
| set N drawn pages (120) | A:IRBBB | 16 | 69 / 88 | 44 / 98 |
| set N drawn pages (120) | B:AF | 30 | 93 / 77 | 87 / 84 |
| set N drawn pages (120) | B:LBBB | 22 | 100 / 84 | 100 / 83 |
| set N drawn pages (120) | B:1dAVb | 23 | 100 / 44 | 65 / 82 |
| set N simulated photos (120) | A:ASMI | 26 | 77 / 59 | 69 / 82 |
| set N simulated photos (120) | A:NDT | 2 | 50 / 88 | 0 / 99 |
| set N simulated photos (120) | A:LVH | 24 | 62 / 66 | 46 / 73 |
| set N simulated photos (120) | A:LAFB | 35 | 71 / 88 | 40 / 96 |
| set N simulated photos (120) | A:IRBBB | 16 | 50 / 95 | 31 / 99 |
| set N simulated photos (120) | B:AF | 30 | 77 / 79 | 70 / 86 |
| set N simulated photos (120) | B:LBBB | 22 | 77 / 87 | 77 / 86 |
| set N simulated photos (120) | B:1dAVb | 23 | 87 / 43 | 70 / 81 |
