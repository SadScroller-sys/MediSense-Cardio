# Section FG: failure gallery (descriptive)
Selection rules: `docs/plan/analysis_plan_changes.md`, 'Section FG' (logged before any card was drawn). Cases are picked by a rule. They show what a failure looks like, not how often it happens; counts are in `results/FINAL_NUMBERS.md`.

Figure: `results/analysis/sectionFG_failure_gallery.png` (also `docs/reports/figures/fig4_fg_failure_gallery.png`). Table: `sectionFG_cards.csv`.

| Card | Rule | What the card shows |
|---|---|---|
| 1 | GREEN wrong, competition | C3_phone_photo_print; true HR 51.6 bpm, read 60.8 bpm; light GREEN, score 0.148; no picture file on this computer |
| 2 | GREEN wrong, competition | C8_mold_scan_bw; true HR 67.5 bpm, read 51.1 bpm; light GREEN, score 0.247; no picture file on this computer |
| 3 | 3. GREEN but wrong (simulated photo) | G035_angled (simulated phone photo, extra: blur); true HR 75.9 bpm, read 63.5 bpm after straightening; light GREEN.  |
| 4 | 4. Largest error after straightening | G079_angled (simulated phone photo, extra: blur); true HR 87.5 bpm, read 65.1 bpm after straightening; light RED. error 22.4 bpm. |
| 5 | stays wrong after straightening (Q2) | page Q13, A_straight shot; true HR 57.9 bpm, read 66.0 bpm; light AMBER; the same page gave 66 bpm on both photos |
| 6 | axis failure (W confirmation) | page P13; 12SL axis 148 deg, ours -91 deg (error 121 deg); right-axis recording; the next largest error is 70 deg or less; aVF trace is upside down against the true aVF (r = -0.89) |
| 7 | AF page with a PR value | page G004 (9 AF/flutter pages in G); our PR 209 ms; 12SL gives no PR (no P waves); light AMBER, beat-spacing variation 0.23; demo guard hides it: yes |
| 8 | no usable HR (Z, original photo) | G021_angled (extra: blur); the digitiser gave no usable heart rate on the photo as it is; after straightening: 94.1 bpm vs true 97.7, light RED |
| 9 | amplitude shrink (R, own phone P) | page P10, angled shot, photo as taken (no straightening); gain error -91% (the trace is much smaller than the true one); light RED, wrong HR: yes |
| 10 | false alarm on a right reading (AF page) | page G071, atrial fibrillation / flutter; heart rate right (100.4 vs 99.8 bpm), light AMBER; 7 of 9 AF pages with a right heart rate are not GREEN |

Waveform match (Pearson r of the digitised against the true trace after the best lag; the gain is not fitted): card 1: Lead II 0.06; card 2: Lead II 0.89; card 3: Lead II 0.20; card 4: Lead II 0.24; card 5: Lead II 0.97; card 6: Lead I n/a; Lead aVF -0.89; card 7: Lead II 0.95; card 8: Lead II, after straightening 0.16; card 9: Lead II 0.12; card 10: Lead II 0.97.
Reading: where r is high (cards 2, 5 and 7) the traced waveform follows the true one, so the wrong number comes from the step after tracing (the heart-rate or interval measure), as the clean-page diagnosis in Section I found. Where r is low (cards 1, 3 and 4) the trace itself is wrong; cards 1 and 3 were still GREEN, which is why GREEN is not a guarantee. On card 6 the aVF trace is upside down against the true aVF (negative r), which is consistent with the wrong axis. Card 8: the trace is still poor after straightening (low r), so the heart rate that looks close (94.1 against 97.7) is partly luck, and the light is RED. Card 9: the trace of an angled, unstraightened photo is far too small (large negative gain error), and the light is RED. Card 10 is the other kind of failure, a false alarm: the trace is good (r about 0.97) and the heart rate is right, but atrial fibrillation beats are irregular, so the light is not GREEN (the cost recorded in FINAL_NUMBERS 3.1).

Cards 1 and 2 have no picture because the competition image files are not stored on this computer (only their digitised signals). Signals are shown as mean-removed lead II (mV) with the digitised trace shifted by the best lag within 0.5 s; the gain is not fitted.
