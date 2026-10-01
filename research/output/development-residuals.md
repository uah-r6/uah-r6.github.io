# Development residual review - 2026-10-01

Public objective labels are diagnostic groups only, never model inputs. Each row is a player-map; within-map rows are correlated. Operator groups use modal operator, not side-specific rating targets. Roster ID denotes team grouping, not verified team name. No region/role labels are inferred.

Saved models only; no refits. Both September events excluded. Small cells are descriptive and are not grounds for player/team/operator adjustments.

## Existing baseline: August development

| Dimension | Group | Player-maps | Maps | MAE | Signed bias |
| --- | --- | ---: | ---: | ---: | ---: |
| clutch | none | 31 | 4 | 0.0354 | -0.0110 |
| clutch | present | 1 | 1 | 0.0070 | -0.0070 |
| event | Esports World Cup 2026 | 32 | 4 | 0.0345 | -0.0109 |
| kost | 0.5-0.75 | 16 | 4 | 0.0358 | -0.0172 |
| kost | <0.5 | 9 | 4 | 0.0440 | -0.0035 |
| kost | >=0.75 | 7 | 4 | 0.0194 | -0.0059 |
| length | overtime 13+ | 8 | 1 | 0.0408 | -0.0210 |
| length | regulation 10-12 | 14 | 2 | 0.0230 | -0.0074 |
| length | short <=9 | 10 | 1 | 0.0456 | -0.0076 |
| multikill | none | 7 | 4 | 0.0379 | +0.0172 |
| multikill | present | 25 | 4 | 0.0336 | -0.0187 |
| opening_activity | none | 4 | 3 | 0.0146 | +0.0146 |
| opening_activity | present | 28 | 4 | 0.0374 | -0.0145 |
| public_objective_label | none | 21 | 4 | 0.0303 | +0.0034 |
| public_objective_label | present | 11 | 4 | 0.0425 | -0.0382 |
| survival | <0.25 | 13 | 4 | 0.0378 | -0.0064 |
| survival | >=0.25 | 19 | 4 | 0.0323 | -0.0140 |
| trades | none | 9 | 2 | 0.0365 | +0.0144 |
| trades | present | 23 | 4 | 0.0338 | -0.0208 |

## Separate-opening diagnostic: seven held-out event folds

| Dimension | Group | Player-maps | Maps | MAE | Signed bias |
| --- | --- | ---: | ---: | ---: | ---: |
| clutch | none | 271 | 43 | 0.0346 | +0.0008 |
| clutch | present | 28 | 22 | 0.0561 | +0.0087 |
| event | Asia Pacific Kickoff 2026 | 32 | 5 | 0.0330 | -0.0029 |
| event | Asia Pacific League Stage 1 2026 | 17 | 2 | 0.0454 | -0.0083 |
| event | Europe MENA League Stage 1 2026 | 35 | 5 | 0.0300 | -0.0040 |
| event | North America League Stage 1 2026 | 125 | 18 | 0.0383 | +0.0101 |
| event | Salt Lake City Major 2026 | 42 | 6 | 0.0426 | -0.0057 |
| event | Six Invitational 2026 | 10 | 2 | 0.0346 | +0.0001 |
| event | South America League Stage 1 2026 | 38 | 5 | 0.0301 | -0.0053 |
| kost | 0.5-0.75 | 167 | 41 | 0.0357 | +0.0028 |
| kost | <0.5 | 59 | 31 | 0.0392 | +0.0017 |
| kost | >=0.75 | 73 | 34 | 0.0367 | -0.0016 |
| length | overtime 13+ | 46 | 8 | 0.0258 | +0.0022 |
| length | regulation 10-12 | 151 | 21 | 0.0367 | +0.0040 |
| length | short <=9 | 102 | 14 | 0.0414 | -0.0026 |
| multikill | none | 60 | 31 | 0.0439 | +0.0065 |
| multikill | present | 239 | 43 | 0.0348 | +0.0002 |
| opening_activity | none | 38 | 24 | 0.0369 | -0.0039 |
| opening_activity | present | 261 | 43 | 0.0366 | +0.0023 |
| public_objective_label | none | 241 | 43 | 0.0337 | +0.0113 |
| public_objective_label | present | 58 | 31 | 0.0488 | -0.0393 |
| survival | <0.25 | 122 | 42 | 0.0349 | +0.0043 |
| survival | >=0.25 | 177 | 42 | 0.0378 | -0.0004 |
| trades | none | 30 | 19 | 0.0375 | +0.0002 |
| trades | present | 269 | 43 | 0.0365 | +0.0016 |

Full player/roster/operator group diagnostics are cached privately in `data/research/experiments/development-residuals.json`. No side-level rating or role target exists in these observations, so those effects cannot be separately estimated from map-level errors.
