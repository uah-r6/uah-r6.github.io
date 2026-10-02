# UAH corrected-KOST v3 contributions: read-only, failed SAL final gate

Frozen v3 improves new-event MAE but fails its predeclared within0.05 gate. No deployment or historical correction is proposed. SQLite mode=ro; exact archive digests/logical mapping checked. Only complete-actor maps receive a v3 prediction. Whole season v3 is unavailable while any map has unresolved objective ownership. Missing ownership is never zero.

| Map / ID | Rounds | Objectives | Available | Reason |
| --- | ---: | --- | --- | --- |
| Fortress/d64d5478cdb3 | 10 | {'plant': 2} | True | all actors verified |
| Border/8a6357ff307c | 14 | {'plant': 5} | True | all actors verified |
| Kafe Dostoyevsky/5adc26f7a402 | 14 | {'plant': 5} | False | [{'round': 9, 'kind': 'plant', 'reason': 'timer_owner_body_unresolved'}] |
| Border/076d2b6b02bc | 12 | {'plant': 3, 'disable': 3} | True | all actors verified |
| Chalet/b595ffaaec57 | 12 | {'plant': 2} | False | [{'round': 10, 'kind': 'plant', 'reason': 'incomplete_unique_roster_or_roles'}] |

## Player-map controlled comparison

Stored-data v2 is an in-memory recomputation with the unchanged live v2 on stored normalized data. Controlled v2/v3 both use fully objective-corrected KOST and verified objectives, as frozen for the separate corrected-KOST research comparison; other gameplay inputs unchanged. Objective-only addition is raw objective coefficient times objectives/round; total delta also includes frozen coefficient/intercept drift.

| Player / map / ID | Rounds | Verified objectives | Stored-data v2 | Controlled v2 | Controlled v3 | Delta | Objective-only addition |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Tallman3.14/Fortress/d64d5478cdb3 | 10 | 1 | 0.701 | 0.701 | 0.729 | +0.029 | +0.041 |
| AzoozNewzz/Fortress/d64d5478cdb3 | 10 | 0 | 1.199 | 1.199 | 1.189 | -0.010 | +0.000 |
| DinoFireKing/Fortress/d64d5478cdb3 | 10 | 0 | 0.810 | 0.810 | 0.794 | -0.015 | +0.000 |
| Lgon/Fortress/d64d5478cdb3 | 10 | 1 | 1.490 | 1.540 | 1.572 | +0.032 | +0.041 |
| OhWowJay/Fortress/d64d5478cdb3 | 10 | 0 | 1.486 | 1.486 | 1.467 | -0.019 | +0.000 |
| Tallman3.14/Border/8a6357ff307c | 14 | 0 | 0.367 | 0.367 | 0.360 | -0.007 | +0.000 |
| Lgon/Border/8a6357ff307c | 14 | 0 | 1.181 | 1.181 | 1.181 | -0.000 | +0.000 |
| DinoFireKing/Border/8a6357ff307c | 14 | 1 | 0.844 | 0.844 | 0.859 | +0.015 | +0.029 |
| OhWowJay/Border/8a6357ff307c | 14 | 0 | 1.221 | 1.221 | 1.216 | -0.005 | +0.000 |
| AzoozNewzz/Border/8a6357ff307c | 14 | 1 | 0.660 | 0.660 | 0.676 | +0.016 | +0.029 |
| Tallman3.14/Border/076d2b6b02bc | 12 | 1 | 0.913 | 0.913 | 0.933 | +0.019 | +0.034 |
| AzoozNewzz/Border/076d2b6b02bc | 12 | 1 | 1.211 | 1.211 | 1.228 | +0.017 | +0.034 |
| Lgon/Border/076d2b6b02bc | 12 | 1 | 1.345 | 1.345 | 1.371 | +0.026 | +0.034 |
| DinoFireKing/Border/076d2b6b02bc | 12 | 0 | 0.865 | 0.865 | 0.848 | -0.017 | +0.000 |
| OhWowJay/Border/076d2b6b02bc | 12 | 0 | 1.316 | 1.316 | 1.306 | -0.010 | +0.000 |

## Partial aggregation over complete maps only

These are not full-season ratings: Kafe and Chalet are excluded entirely, including their already-resolved objectives.

| Player | Included rounds | Objectives | Controlled v2 | Controlled v3 |
| --- | ---: | ---: | ---: | ---: |
| AzoozNewzz | 36 | 2 | 0.993 | 1.002 |
| DinoFireKing | 36 | 1 | 0.842 | 0.837 |
| Lgon | 36 | 2 | 1.335 | 1.353 |
| OhWowJay | 36 | 0 | 1.327 | 1.316 |
| Tallman3.14 | 36 | 2 | 0.642 | 0.653 |

## Every standardized feature contribution change

Entries are v3 minus v2 centered contributions; their sum plus the intercept delta equals total rating delta. Centered objective contribution may be negative for zero-objective players; the objective-only addition above has no centering offset.

| Player / map ID | kpr | teamkills | multikill | opening | clutch | kost | survival | trade | objectives |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Tallman3.14/d64d5478cdb3 | -0.0059 | -0.0000 | +0.0004 | -0.0002 | -0.0046 | +0.0032 | +0.0005 | -0.0010 | +0.0321 |
| AzoozNewzz/d64d5478cdb3 | +0.0024 | -0.0000 | -0.0011 | -0.0001 | -0.0046 | -0.0029 | -0.0019 | +0.0025 | -0.0086 |
| DinoFireKing/d64d5478cdb3 | -0.0059 | -0.0000 | +0.0011 | -0.0002 | +0.0003 | -0.0008 | -0.0043 | -0.0010 | -0.0086 |
| Lgon/d64d5478cdb3 | +0.0073 | -0.0000 | -0.0034 | +0.0003 | +0.0003 | -0.0049 | -0.0043 | +0.0001 | +0.0321 |
| OhWowJay/d64d5478cdb3 | +0.0040 | -0.0000 | -0.0026 | +0.0002 | -0.0046 | -0.0049 | -0.0043 | -0.0022 | -0.0086 |
| Tallman3.14/8a6357ff307c | -0.0101 | -0.0000 | +0.0011 | -0.0003 | +0.0003 | +0.0041 | +0.0036 | -0.0015 | -0.0086 |
| Lgon/8a6357ff307c | +0.0052 | -0.0000 | -0.0021 | -0.0001 | +0.0003 | -0.0017 | +0.0001 | +0.0026 | -0.0086 |
| DinoFireKing/8a6357ff307c | -0.0042 | -0.0000 | +0.0001 | -0.0003 | +0.0003 | -0.0003 | -0.0016 | -0.0032 | +0.0205 |
| OhWowJay/8a6357ff307c | +0.0052 | -0.0000 | -0.0031 | -0.0003 | +0.0003 | -0.0003 | -0.0016 | -0.0007 | -0.0086 |
| AzoozNewzz/8a6357ff307c | -0.0066 | -0.0000 | +0.0001 | -0.0003 | -0.0032 | +0.0012 | +0.0036 | -0.0032 | +0.0205 |
| Tallman3.14/076d2b6b02bc | -0.0042 | -0.0000 | -0.0001 | -0.0001 | +0.0003 | -0.0005 | -0.0047 | -0.0008 | +0.0253 |
| AzoozNewzz/076d2b6b02bc | +0.0013 | -0.0020 | -0.0020 | -0.0002 | +0.0003 | -0.0022 | -0.0067 | -0.0008 | +0.0253 |
| Lgon/076d2b6b02bc | +0.0054 | -0.0000 | -0.0014 | -0.0002 | +0.0003 | -0.0056 | -0.0047 | +0.0031 | +0.0253 |
| DinoFireKing/076d2b6b02bc | -0.0056 | -0.0000 | +0.0005 | -0.0003 | +0.0003 | -0.0022 | -0.0047 | -0.0008 | -0.0086 |
| OhWowJay/076d2b6b02bc | +0.0040 | -0.0000 | -0.0014 | +0.0000 | +0.0003 | -0.0039 | -0.0047 | +0.0001 | -0.0086 |

Intercept delta +0.00399583.
All86 protected live file hashes unchanged; no SQLite statistics write, reparse/import, archive mutation, public regeneration or publishing.
