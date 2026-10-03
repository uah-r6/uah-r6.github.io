# UAH credited kills migration audit — read-only

Current stored/displayed K/D includes any existing manual map corrections. The counter derives official-style credit, not independently filmed UAH ground truth. Unsupported rounds/maps stay unresolved; known-round subtotals are not substituted for complete season statistics. No events, SQLite, archives or public JSON changed.

| Player | Current kills | Current deaths | Credited kills | Complete difference | Proposed KD | Known-round credit/finish difference | Unresolved rounds |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Lgon | 61 | 38 | None | None | None | -2 | [('Chalet', 9), ('Chalet', 10), ('Chalet', 11), ('Chalet', 12)] |
| OhWowJay | 58 | 39 | None | None | None | 1 | [('Chalet', 9), ('Chalet', 10), ('Chalet', 11), ('Chalet', 12)] |
| AzoozNewzz | 45 | 48 | None | None | None | 0 | [('Chalet', 9), ('Chalet', 10), ('Chalet', 11), ('Chalet', 12)] |
| Tallman3.14 | 28 | 49 | None | None | None | 0 | [('Chalet', 9), ('Chalet', 10), ('Chalet', 11), ('Chalet', 12)] |
| DinoFireKing | 30 | 38 | None | None | None | 1 | [('Chalet', 9), ('Chalet', 10), ('Chalet', 11), ('Chalet', 12)] |

## Map totals

| Map / ID | Player | Current kills / deaths | Credit | Difference | Proposed KD | Unresolved |
| --- | --- | --- | ---: | ---: | ---: | --- |
| Fortress/d64d5478cdb3 | Lgon | 12/6 | 11 | -1 | 1.8333333333333333 | [] |
| Fortress/d64d5478cdb3 | OhWowJay | 10/6 | 10 | 0 | 1.6666666666666667 | [] |
| Fortress/d64d5478cdb3 | AzoozNewzz | 9/7 | 9 | 0 | 1.2857142857142858 | [] |
| Fortress/d64d5478cdb3 | Tallman3.14 | 4/8 | 4 | 0 | 0.5 | [] |
| Fortress/d64d5478cdb3 | DinoFireKing | 4/6 | 5 | 1 | 0.8333333333333334 | [] |
| Border/8a6357ff307c | Lgon | 15/11 | 14 | -1 | 1.2727272727272727 | [] |
| Border/8a6357ff307c | OhWowJay | 15/10 | 16 | 1 | 1.6 | [] |
| Border/8a6357ff307c | AzoozNewzz | 5/13 | 5 | 0 | 0.38461538461538464 | [] |
| Border/8a6357ff307c | Tallman3.14 | 2/13 | 2 | 0 | 0.15384615384615385 | [] |
| Border/8a6357ff307c | DinoFireKing | 7/10 | 7 | 0 | 0.7 | [] |
| Kafe Dostoyevsky/5adc26f7a402 | Lgon | 16/6 | 15 | -1 | 2.5 | [] |
| Kafe Dostoyevsky/5adc26f7a402 | OhWowJay | 11/9 | 12 | 1 | 1.3333333333333333 | [] |
| Kafe Dostoyevsky/5adc26f7a402 | AzoozNewzz | 12/11 | 12 | 0 | 1.0909090909090908 | [] |
| Kafe Dostoyevsky/5adc26f7a402 | Tallman3.14 | 8/12 | 8 | 0 | 0.6666666666666666 | [] |
| Kafe Dostoyevsky/5adc26f7a402 | DinoFireKing | 6/9 | 6 | 0 | 0.6666666666666666 | [] |
| Border/076d2b6b02bc | Lgon | 13/7 | 14 | 1 | 2.0 | [] |
| Border/076d2b6b02bc | OhWowJay | 12/7 | 11 | -1 | 1.5714285714285714 | [] |
| Border/076d2b6b02bc | AzoozNewzz | 10/6 | 10 | 0 | 1.6666666666666667 | [] |
| Border/076d2b6b02bc | Tallman3.14 | 6/7 | 6 | 0 | 0.8571428571428571 | [] |
| Border/076d2b6b02bc | DinoFireKing | 5/7 | 5 | 0 | 0.7142857142857143 | [] |
| Chalet/b595ffaaec57 | Lgon | 5/8 | None | None | None | [9, 10, 11, 12] |
| Chalet/b595ffaaec57 | OhWowJay | 10/7 | None | None | None | [9, 10, 11, 12] |
| Chalet/b595ffaaec57 | AzoozNewzz | 9/11 | None | None | None | [9, 10, 11, 12] |
| Chalet/b595ffaaec57 | Tallman3.14 | 8/9 | None | None | None | [9, 10, 11, 12] |
| Chalet/b595ffaaec57 | DinoFireKing | 8/6 | None | None | None | [9, 10, 11, 12] |

## Every tracked player-round difference

| Map / ID | Logical (physical) round | Player | Credited | Finishes | Delta |
| --- | --- | --- | ---: | ---: | ---: |
| Fortress/d64d5478cdb3 | 4 (4) | Lgon | 3 | 4 | -1 |
| Fortress/d64d5478cdb3 | 4 (4) | DinoFireKing | 2 | 1 | 1 |
| Border/8a6357ff307c | 9 (9) | Lgon | 1 | 2 | -1 |
| Border/8a6357ff307c | 9 (9) | OhWowJay | 3 | 2 | 1 |
| Kafe Dostoyevsky/5adc26f7a402 | 8 (8) | Lgon | 2 | 3 | -1 |
| Kafe Dostoyevsky/5adc26f7a402 | 8 (8) | OhWowJay | 3 | 2 | 1 |
| Border/076d2b6b02bc | 3 (3) | Lgon | 1 | 0 | 1 |
| Border/076d2b6b02bc | 3 (3) | OhWowJay | 1 | 2 | -1 |

Exact UID, start/end counter, packet offsets and raw finish events are in ignored `data/research/credited-kills-v1/uah-audit.json`. No discrepancy is called a specific victim/downer reassignment without independent evidence.

## Hypothetical downstream changes on validated rounds

These are impact calculations, not authorized production migrations. Core actor scenario replaces only supported same-kind credits and retains unresolved historical credit for review. Missing rounds are excluded from every scenario.

| Player | Kill-only KOST round delta | Core-only objective KOST delta | Combined KOST delta | Credited multikill extra delta |
| --- | ---: | ---: | ---: | ---: |
| Lgon | 0 | 1 | 1 | -3 |
| OhWowJay | 0 | 0 | 0 | 1 |
| AzoozNewzz | 0 | 0 | 0 | 0 |
| Tallman3.14 | 0 | 0 | 0 | 0 |
| DinoFireKing | 0 | 0 | 0 | 1 |

Actual new-reader/structural evidence parity: 5 first-round checks, one per map; operators/players and full credit/finish report identical. All 86 protected files unchanged.

Core objectives: 18 supported proposals; Kafe R09 body1 remains research-only, Chalet R10 nine-player roster remains unresolved. Review the [separate objective proposal](uah-final-actor-correction-proposal.md). Original v2 input semantics/rating remain unchanged; no v3 fit or final evaluation.
