# Claims register: what we are allowed to claim, and the evidence each claim must earn

Written 2026-11-04, before the extension results exist. A claim enters the papers, deck or diary only at grade A or B. Grade C claims are worded as "preliminary". Grade D claims are not made.

Grades: **A** = all four marks. **B** = marks 1 and 2. **C** = one sample only (first 50). **D** = not supported.
Marks: (1) repeated on the held-out 100 recordings; (2) holds with and without reference-uncertain recordings and with a second heart-rate detector;
(3) reproducible across digitiser runs (bridge run); (4) rechecked by a second person from the raw files.

| # | Claim (always "in the simulation") | Evidence needed | Today | Target |
|---|---|---|---|---|
| 1 | Low resolution (worst level) and blur cause wrong heart rates; JPEG, brightness, grid fading and rotation mostly do not | marks 1 to 4; verdict rule C1 | C: first 50 only (resolution 43%, blur 18% at level 5) | A |
| 2 | Most other failures follow the recording (premature beats, noise bursts, pacemaker), not the damage | marks 1, 2; descriptive C2 with intervals | C: flagged 14.1% vs unflagged 3.5% wrong; clean images 0% in unflagged | B |
| 3 | The heart-rate reference is reliable except for about 13% of recordings whose reference depends on sampling rate | mark 2; checked on all 150 | B for heart rate on 150 (done 2026-11-04); agreement with 12SL only on the first 50 | A |
| 4 | NeuroKit2 PR and QRS do not track commercial algorithms; QT and QTc only moderately | agreement with 12SL on all 150 | C: first 50 only | B |
| 5 | The digitiser's output availability is not repeatable between runs (163 vs 30 unreadable images); where both ran, heart rate agrees 98% | bridge run, mark 3 | C: sweep 1 vs 2 only | A |
| 6 | A five-score photo-quality detector discriminates wrong readings within these six damage types | C3 rules on the held-out 100, plus oracle and leave-one-damage-out | D: dev AUC 0.607, fails on unseen types; expected not demonstrated | report as measured, no claim of usefulness |
| 7 | Flagging the most suspicious 10 to 30% of photos lowers the wrong-reading rate among kept photos from about 6.5% to about 4% | coverage curve on held-out 100 | C | B (descriptive only) |
| 8 | False reassurance (heart rate or QTc) is rare and appears only at the most severe levels | five-outcome table on 150 | C: heart rate 2 axes at 2 levels; QTc 2 to 6 events | descriptive, no rate claimed |
| 9 | Clean-image aligned SNR and its relation to heart-rate error | bridge + new 100 | not measured (n = 6 pilot only, do not quote) | B (descriptive) |

**Never claimed:** clinical accuracy of PR, QRS or QTc; any guarantee for the gate; benefit to patients; behaviour on real phone photos (unless the optional photos are done, and then only descriptively).

**Second-person recheck (mark 4):** after the freeze, a team member or the guide reruns three headline numbers from the raw files with our scripts. Their name and the date go next to the claim.
