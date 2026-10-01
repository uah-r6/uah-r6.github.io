# Frozen objective occurrence validation - 2026-10-01

Rule frozen at `8b18365`; twelve-map extension locked at `4f17c21` before results. No rule changes were made during this validation. The set is independent of the 291-round property discovery, but has prior Rating development history. NA Stage 2 is excluded.

Rule: Bomb mode, unambiguous winner side, one state1 on one entity, no conflicting state sequence. That establishes a plant candidate. A defender score-derived win additionally implies a disable. State0 with an attacker win is cleanup, not a disable. No timer threshold, public actor, score bonus or heuristic win-condition label is used.

| Metric | Plants | Disables |
| --- | ---: | ---: |
| Public known | 32 | 12 |
| Detected | 32 | 12 |
| Missed | 0 | 0 |
| False positives | 0 | 0 |

Twelve maps / five event labels / 124 rounds / five header code versions. All 92 objective-free rounds remain negative. One post-plant state0 with an Attack win (6158/10563 R07) was correctly excluded as a disable. Original development: 61 plants and eight disables across 291 rounds, no mismatches, 230 negative rounds and the 4112 R11 cleanup correctly excluded. All actors remain unresolved.

| Match / game | Event | Map | Header version (first physical round) | Rounds | Plants | Disables |
| --- | --- | --- | --- | ---: | ---: | ---: |
| 3579 / 6706 | Asia Pacific Kickoff 2026 | Clubhouse | Y11S1_Alpha03/9636829 | 8 | 3 | 1 |
| 3579 / 6707 | Asia Pacific Kickoff 2026 | Nighthaven Labs | Y11S1_Alpha03/9636829 | 7 | 2 | 0 |
| 3563 / 6673 | Salt Lake City Major 2026 | Nighthaven Labs | Y11S1_Alpha03/9658832 | 9 | 2 | 0 |
| 3563 / 6675 | Salt Lake City Major 2026 | Bank | Y11S1_Alpha03/9658832 | 11 | 2 | 2 |
| 3563 / 6676 | Salt Lake City Major 2026 | Kafe Dostoyevsky | Y11S1_Alpha03/9658832 | 9 | 1 | 0 |
| 4283 / 8685 | Europe MENA League Stage 1 2026 | Lair | Y11S2_Alpha04/9769907 | 10 | 2 | 0 |
| 4283 / 8686 | Europe MENA League Stage 1 2026 | Chalet | Y11S2_Alpha04/9769907 | 15 | 3 | 2 |
| 4283 / 8687 | Europe MENA League Stage 1 2026 | Fortress | Y11S2_Alpha04/9769907 | 9 | 2 | 1 |
| 6157 / 10428 | Esports World Cup 2026 | Border | Y11S2_Alpha04/9820472 | 12 | 3 | 0 |
| 6157 / 10430 | Esports World Cup 2026 | Lair | Y11S2_Alpha04/9820472 | 12 | 4 | 2 |
| 6158 / 10563 | Europe MENA League Stage 2 2026 | Border | Y11S3_Alpha04/9879602 | 10 | 4 | 2 |
| 6277 / 10576 | Europe MENA League Stage 2 2026 | Bank | Y11S3_Alpha04/9879602 | 12 | 4 | 2 |

## Limits and next action

This establishes occurrence agreement on these sampled builds, not actor accuracy. Device ownership, stable player binding and simultaneous scoring remain unsolved. The February discovery replay is Y10S4_01/9486312; its filename suffix 11944 is not the parser code version. Implement occurrence metadata separately from credited player objectives only after reviewing the grammar and winner provenance. Preserve all prior statistics and operators.

Cached results: ignored `data/research/diagnostics/objective-occurrence-holdout/summary.json`. Resume: `.\.venv\Scripts\python.exe research/objective_occurrence_holdout.py` (cached).
