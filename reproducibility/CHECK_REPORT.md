# Check report

Run: 2026-11-14 23:10, Python 3.13.15 on Windows 11.

| Check | Result | Last line of its output |
|---|---|---|
| 36 headline numbers recomputed from the raw files | **PASS** | ALL MATCH: True |
| Second-person number 3: GREEN wrong on the competition captures (2/917) | **PASS** | GREEN wrong: 2/917 / reported 2/917 / MATCH |
| Traffic-light unit tests | **PASS** | ALL TESTS PASSED |
| Demo wording tests | **PASS** | 19 tests passed |

What this proves: the saved result files give the reported numbers when recounted by a second script, and the tests pass, in this environment. What it does not prove: it does not re-run the digitiser, and a second PERSON has not been involved unless you wrote your name in `SECOND_PERSON_CHECK.md`.
