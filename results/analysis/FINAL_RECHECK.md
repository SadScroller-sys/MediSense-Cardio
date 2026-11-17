# Independent recomputation of the headline numbers (script: scripts/analysis/final_numbers_recompute.py)

Written fresh from the raw result files; it does not reuse the section scripts. 'reported' = the number in the section report. This is a second script by the same author, NOT a second person.

| quantity | recomputed | reported | check |
|---|---|---|---|
| new 100, clean level 0: wrong >5 bpm | 3/99 | 3/99 | MATCH |
| new 100, resolution level 5: wrong >5 bpm | 47/99 | 47/99 | MATCH |
| new 100, blur level 5: wrong >5 bpm | 17/99 | 17/99 | MATCH |
| new 100, rotate level 5: wrong >5 bpm | 0/99 | 0/99 | MATCH |
| new 100, jpeg level 5: wrong >5 bpm | 0/99 | 0/99 | MATCH |
| new 100, brightness level 5: wrong >5 bpm | 1/99 | 1/99 | MATCH |
| new 100, gridcontrast level 5: wrong >5 bpm | 3/99 | 3/99 | MATCH |
| new 100, rotate level 5: no output | 19/99 | 19/99 | MATCH |
| new 100, blur level 5: no output | 1/99 | 1/99 | MATCH |
| first 50, clean level 0: wrong >5 bpm | 2/49 | 2/49 | MATCH |
| first 50, resolution level 5: wrong >5 bpm | 21/49 | 21/49 | MATCH |
| first 50, blur level 5: wrong >5 bpm | 8/49 | 8/49 | MATCH |
| all 150, clean level 0: wrong >5 bpm | 5/148 | 5/148 | MATCH |
| all 150, resolution level 5: wrong >5 bpm | 68/148 | 68/148 | MATCH |
| all 150, blur level 5: wrong >5 bpm | 25/148 | 25/148 | MATCH |
| bridge run: images whose bad label changed | 0/156 | 0/156 | MATCH |
| Arm B wrong >5 bpm (clean, B1, B2, B3) | 0,1,0,0 | 0,1,0,0 | MATCH |
| simulated new 100 (cleaned): images with a reading / wrong | 1262/113 | 1262/113 | MATCH |
| real captures, original measure: images with a reading / wrong | 1203/168 | 1203/168 | MATCH |
| real captures, cleaned measure: images with a reading / wrong | 1201/46 | 1201/46 | MATCH |
| real captures C4 (phone photo of screen): no output | 53/140 | 53/140 | MATCH |
| CONFIRMATION (40 new photos): bad original / straightened | 14/2 | 14/2 | MATCH |
| CONFIRMATION: newly bad / newly good | 0/12 | 0/12 | MATCH |
| CONFIRMATION: exact McNemar p (4 decimals) | 0.0005 | 0.0005 | MATCH |
| CONFIRMATION: V0 no usable HR / wrong | 4/10 | 4/10 | MATCH |
| CONFIRMATION: V2 no usable HR / wrong | 0/2 | 0/2 | MATCH |
| CONFIRMATION: V1 enlarge bad | 13 | 13 | MATCH |
| CONFIRMATION: V3 straighten+big bad | 3 | 3 | MATCH |
| CONFIRMATION lights V0 | GREEN:20(0 bad);AMBER:7(1 bad);RED:13(13 bad) | GREEN:20(0 bad);AMBER:7(1 bad);RED:13(13 bad) | MATCH |
| CONFIRMATION lights V2 | GREEN:32(0 bad);AMBER:7(1 bad);RED:1(1 bad) | GREEN:32(0 bad);AMBER:7(1 bad);RED:1(1 bad) | MATCH |
| OWN PHONE set 1: V0 no usable HR / wrong (60 photos) | 6/14 | 6/14 | MATCH |
| FIX EXPERIMENT (first 60): bad V1_enlarge | 12 | 12 | MATCH |
| FIX EXPERIMENT (first 60): bad V2_straighten | 2 | 2 | MATCH |
| FIX EXPERIMENT (first 60): bad V3_straighten_big | 6 | 6 | MATCH |
| FIX EXPERIMENT: V0 bad / V2 newly bad / newly good | 20/1/19 | 20/1/19 | MATCH |

**All match: True**
