# Section T: a better QT method, tested once on the new 100 (EXPLORATORY, added after the freeze)

Rules fixed before any code ran (`docs/plan/analysis_plan_changes.md`, 2026-11-14). Development on the first 50 original signals chose **candidate B_tangent** with a constant offset of **-40.5 ms** (see the development table below). The acceptance rule is the assistant's proposal and is **not approved by the guide**: median absolute difference <= 20 ms, at least 90% within 40 ms, |bias| <= 10 ms, and at least 90% of recordings with a value, for BOTH the original signal in the photo windows (a) and the digitised photo (b).

Primary set: clean pages of the new 100 recordings, 21205 excluded: 99 recordings. Difference = measured minus 12SL (ms).

| Measurement | Recordings with a value | rho with 12SL | Median abs diff (95% CI) | 90th pct abs diff | Bias (95% CI) | Within 40 ms | Rule |
|---|---|---|---|---|---|---|---|
| (a) frozen method on the original signal, photo windows | 99 of 99 | 0.83 | 7.8 (6.9 to 9.6) | 36.2 | +6.6 (+1.9 to +11.8) | 92% | **meets** |
| (b) digitised clean page | 99 of 99 | 0.81 | 13.5 (9.6 to 16.9) | 31.3 | +10.5 (+5.1 to +16.1) | 92% | **does not meet** |
| (c) digitised minus (a): what the photo adds | 99 | | 7.2 | 14.7 | +3.9 | | |

Share with a value: original 100%, digitised 100%. **QT validated under the pre-set rule: NO** ((a) meets: True, (b) meets: False, both value shares at least 90%: True).

For comparison, the earlier NeuroKit2 method (Section S): original 36 ms typical error, digitised 26 ms, 54 to 55% within 40 ms, 69 to 70% of recordings with a value.

## Secondary (descriptive): digitised, all versions, by damage type and level; GREEN images only

| Group | Images | Median abs / bias (ms) | Within 40 ms | Value share |
|---|---|---|---|---|
| all versions | 1287 | 17 / +19 | 83% | 98% |
| GREEN images only | 903 | 14 / +12 | 90% | 100% |
| clean | 99 | 13 / +11 | 92% | 100% |
| blur 3 | 99 | 27 / +27 | 81% | 100% |
| blur 5 | 99 | 49 / +56 | 33% | 97% |
| rotate 3 | 99 | 13 / +12 | 92% | 98% |
| rotate 5 | 99 | 14 / +11 | 91% | 79% |
| jpeg 3 | 99 | 13 / +11 | 91% | 100% |
| jpeg 5 | 99 | 13 / +11 | 92% | 99% |
| resolution 3 | 99 | 17 / +14 | 90% | 100% |
| resolution 5 | 99 | 41 / +48 | 47% | 99% |
| brightness 3 | 99 | 12 / +10 | 93% | 100% |
| brightness 5 | 99 | 13 / +10 | 92% | 99% |
| gridcontrast 3 | 99 | 13 / +10 | 92% | 100% |
| gridcontrast 5 | 99 | 14 / +10 | 92% | 100% |

## Development table (first 50 recordings; for the record)

| Candidate | Recordings with a value | Bias before offset | Offset | Median abs after offset | rho |
|---|---|---|---|---|---|
| A_tangent | 100% | -23.6 | -26.8 | 14.2 | 0.46 |
| A_threshold | 74% | -9.6 | -14.0 | 18.0 | 0.38 |
| B_tangent | 100% | -50.5 | -40.5 | 10.9 | 0.54 |
| B_threshold | 100% | -42.2 | -37.5 | 13.5 | 0.53 |
| C_tangent | 100% | +3.2 | -5.0 | 22.4 | 0.35 |
| C_threshold | 100% | +24.7 | -4.8 | 25.3 | 0.36 |

## Limits

- 12SL is an algorithm, not an expert measurement; 12SL and Glasgow differ by 4 to 6.5 ms.
- The method was developed on 50 recordings with 6 candidates and one offset, so a small amount of overfitting is possible; the 100 test recordings were not used to tune it.
- One digitiser, simulated pages. QTc is not evaluated. Nothing from this section is shown to patients unless the verdict above says YES.