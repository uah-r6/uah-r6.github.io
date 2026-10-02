# UAH frozen v3 contributions: read-only, failed final gate

Frozen v3 improves new-event MAE but fails its predeclared within0.05 gate. No deployment or historical correction is proposed. SQLite mode=ro; exact archive digests/logical mapping checked. Only complete-actor maps receive a v3 prediction. Whole season v3 is unavailable while any map has unresolved objective ownership. Missing ownership is never zero.

| Map / ID | Rounds | Objectives | Available | Reason |
| --- | ---: | --- | --- | --- |
| Fortress/d64d5478cdb3 | 10 | {'plant': 2} | True | all actors verified |
| Border/8a6357ff307c | 14 | {'plant': 5} | True | all actors verified |
| Kafe Dostoyevsky/5adc26f7a402 | 14 | {'plant': 5} | False | [{'round': 9, 'kind': 'plant', 'reason': 'timer_owner_body_unresolved'}] |
| Border/076d2b6b02bc | 12 | {'plant': 3, 'disable': 3} | True | all actors verified |
| Chalet/b595ffaaec57 | 12 | {'plant': 2} | False | [{'round': 10, 'kind': 'plant', 'reason': 'incomplete_unique_roster_or_roles'}] |

## Player-map controlled comparison

Stored-data v2 is an in-memory recomputation with the unchanged live v2 on stored normalized data. Controlled v2/v3 both use occurrence-free KOST, as frozen for the research comparison; other gameplay inputs unchanged. Objective-only addition is raw objective coefficient times objectives/round; total delta also includes frozen coefficient/intercept drift.

| Player / map / ID | Rounds | Verified objectives | Stored-data v2 | Controlled v2 | Controlled v3 | Delta | Objective-only addition |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Tallman3.14/Fortress/d64d5478cdb3 | 10 | 1 | 0.701 | 0.701 | 0.737 | +0.037 | +0.047 |
| AzoozNewzz/Fortress/d64d5478cdb3 | 10 | 0 | 1.199 | 1.199 | 1.190 | -0.009 | +0.000 |
| DinoFireKing/Fortress/d64d5478cdb3 | 10 | 0 | 0.810 | 0.810 | 0.794 | -0.016 | +0.000 |
| Lgon/Fortress/d64d5478cdb3 | 10 | 1 | 1.490 | 1.490 | 1.529 | +0.039 | +0.047 |
| OhWowJay/Fortress/d64d5478cdb3 | 10 | 0 | 1.486 | 1.486 | 1.467 | -0.019 | +0.000 |
| Tallman3.14/Border/8a6357ff307c | 14 | 0 | 0.367 | 0.367 | 0.361 | -0.007 | +0.000 |
| Lgon/Border/8a6357ff307c | 14 | 0 | 1.181 | 1.181 | 1.180 | -0.001 | +0.000 |
| DinoFireKing/Border/8a6357ff307c | 14 | 1 | 0.844 | 0.844 | 0.863 | +0.019 | +0.034 |
| OhWowJay/Border/8a6357ff307c | 14 | 0 | 1.221 | 1.221 | 1.215 | -0.006 | +0.000 |
| AzoozNewzz/Border/8a6357ff307c | 14 | 1 | 0.660 | 0.660 | 0.682 | +0.022 | +0.034 |
| Tallman3.14/Border/076d2b6b02bc | 12 | 1 | 0.913 | 0.913 | 0.938 | +0.024 | +0.040 |
| AzoozNewzz/Border/076d2b6b02bc | 12 | 1 | 1.211 | 1.211 | 1.231 | +0.019 | +0.040 |
| Lgon/Border/076d2b6b02bc | 12 | 1 | 1.345 | 1.345 | 1.376 | +0.031 | +0.040 |
| DinoFireKing/Border/076d2b6b02bc | 12 | 0 | 0.865 | 0.865 | 0.847 | -0.018 | +0.000 |
| OhWowJay/Border/076d2b6b02bc | 12 | 0 | 1.316 | 1.316 | 1.305 | -0.012 | +0.000 |

## Partial aggregation over complete maps only

These are not full-season ratings: Kafe and Chalet are excluded entirely, including their already-resolved objectives.

| Player | Included rounds | Objectives | Controlled v2 | Controlled v3 |
| --- | ---: | ---: | ---: | ---: |
| AzoozNewzz | 36 | 2 | 0.993 | 1.006 |
| DinoFireKing | 36 | 1 | 0.842 | 0.839 |
| Lgon | 36 | 2 | 1.321 | 1.342 |
| OhWowJay | 36 | 0 | 1.327 | 1.315 |
| Tallman3.14 | 36 | 2 | 0.642 | 0.658 |

## Every standardized feature contribution change

Entries are v3 minus v2 centered contributions; their sum plus the intercept delta equals total rating delta. Centered objective contribution may be negative for zero-objective players; the objective-only addition above has no centering offset.

| Player / map ID | kpr | teamkills | multikill | opening | clutch | kost | survival | trade | objectives |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Tallman3.14/d64d5478cdb3 | -0.0050 | +0.0000 | +0.0001 | -0.0002 | -0.0033 | +0.0041 | +0.0008 | -0.0013 | +0.0374 |
| AzoozNewzz/d64d5478cdb3 | +0.0017 | +0.0000 | -0.0009 | -0.0001 | -0.0033 | -0.0017 | -0.0019 | +0.0029 | -0.0100 |
| DinoFireKing/d64d5478cdb3 | -0.0050 | +0.0000 | +0.0006 | -0.0002 | +0.0002 | +0.0002 | -0.0046 | -0.0013 | -0.0100 |
| Lgon/d64d5478cdb3 | +0.0057 | +0.0000 | -0.0025 | +0.0002 | +0.0002 | -0.0017 | -0.0046 | +0.0001 | +0.0374 |
| OhWowJay/d64d5478cdb3 | +0.0031 | +0.0000 | -0.0020 | +0.0001 | -0.0033 | -0.0036 | -0.0046 | -0.0027 | -0.0100 |
| Tallman3.14/8a6357ff307c | -0.0084 | +0.0000 | +0.0006 | -0.0003 | +0.0002 | +0.0049 | +0.0042 | -0.0019 | -0.0100 |
| Lgon/8a6357ff307c | +0.0040 | +0.0000 | -0.0016 | -0.0001 | +0.0002 | -0.0006 | +0.0004 | +0.0031 | -0.0100 |
| DinoFireKing/8a6357ff307c | -0.0036 | +0.0000 | -0.0001 | -0.0002 | +0.0002 | +0.0008 | -0.0016 | -0.0039 | +0.0239 |
| OhWowJay/8a6357ff307c | +0.0040 | +0.0000 | -0.0024 | -0.0003 | +0.0002 | +0.0008 | -0.0016 | -0.0009 | -0.0100 |
| AzoozNewzz/8a6357ff307c | -0.0055 | +0.0000 | -0.0001 | -0.0003 | -0.0023 | +0.0022 | +0.0042 | -0.0039 | +0.0239 |
| Tallman3.14/076d2b6b02bc | -0.0036 | +0.0000 | -0.0002 | -0.0001 | +0.0002 | +0.0005 | -0.0051 | -0.0010 | +0.0295 |
| AzoozNewzz/076d2b6b02bc | +0.0008 | -0.0039 | -0.0016 | -0.0002 | +0.0002 | -0.0011 | -0.0073 | -0.0010 | +0.0295 |
| Lgon/076d2b6b02bc | +0.0042 | +0.0000 | -0.0011 | -0.0002 | +0.0002 | -0.0043 | -0.0051 | +0.0036 | +0.0295 |
| DinoFireKing/076d2b6b02bc | -0.0047 | +0.0000 | +0.0002 | -0.0002 | +0.0002 | -0.0011 | -0.0051 | -0.0010 | -0.0100 |
| OhWowJay/076d2b6b02bc | +0.0031 | +0.0000 | -0.0011 | -0.0000 | +0.0002 | -0.0027 | -0.0051 | +0.0001 | -0.0100 |

Intercept delta +0.00399583.
All86 protected live file hashes unchanged; no SQLite statistics write, reparse/import, archive mutation, public regeneration or publishing.
