# Frozen NA Stage 2 Rating evaluation

Freeze commit `eb747f8fa4358b6206bb8d64e45db7d38807d880`; evaluation `frozen-na-20261001T223911Z`. Reserved event contains 60 clean player-map rows across 7 maps. The frozen model was evaluated once; no fit or feature selection used this event.

| Model | MAE | RMSE | Median AE | Max AE | Exact rounded | Within .01 | .02 | .03 | .05 | .10 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Frozen raw eight-family | 0.0362 | 0.0494 | 0.0308 | 0.1494 | 0.1333 | 0.2000 | 0.3500 | 0.4500 | 0.8167 | 0.9333 |
| Live collegiate_v1 | 0.2387 | 0.2940 | 0.1963 | 0.7322 | 0.0000 | 0.0167 | 0.0167 | 0.0667 | 0.1000 | 0.1833 |

Frozen candidate signed bias: -0.0047; collegiate_v1: -0.0013.

## Largest candidate misses

| Player | Map | Actual | Predicted | Error | Public objective credits |
| --- | --- | ---: | ---: | ---: | ---: |
| Spiker.WC | Villa | 1.08 | 0.9306 | -0.1494 | 0 |
| Beeno.4FUN | Border | 1.15 | 1.0066 | -0.1434 | 1 |
| Ewzy.C9 | Nighthaven Labs | 1.94 | 1.8019 | -0.1381 | 0 |
| Spoit.SR | Border | 1.06 | 1.1707 | +0.1107 | 0 |
| MikeW.4FUN | Border | 0.59 | 0.6771 | +0.0871 | 0 |
| SpiriTz.100T | Chalet | 1.15 | 1.0684 | -0.0816 | 2 |
| Canadian.SR | Villa | 0.59 | 0.5118 | -0.0782 | 1 |
| MikeW.4FUN | Kafe Dostoyevsky | 0.54 | 0.6114 | +0.0714 | 0 |

## Descriptive residual groups

Groups overlap and rows from the same map are correlated. Public objective credits are analysis labels only; they were never model inputs.

| Dimension | Group | Rows | Maps | MAE | Signed bias |
| --- | --- | ---: | ---: | ---: | ---: |
| kpr | <0.8 | 38 | 7 | 0.0389 | -0.0022 |
| kpr | >=0.8 | 22 | 7 | 0.0316 | -0.0089 |
| map | Border | 8 | 1 | 0.0630 | +0.0027 |
| map | Chalet | 6 | 1 | 0.0425 | -0.0114 |
| map | Kafe Dostoyevsky | 10 | 1 | 0.0237 | +0.0113 |
| map | Nighthaven Labs | 18 | 2 | 0.0314 | -0.0069 |
| map | Villa | 18 | 2 | 0.0340 | -0.0123 |
| public_objective_credit | no | 43 | 7 | 0.0350 | +0.0084 |
| public_objective_credit | yes | 17 | 6 | 0.0392 | -0.0378 |
| survival | <0.3 | 28 | 7 | 0.0348 | -0.0005 |
| survival | >=0.3 | 32 | 7 | 0.0375 | -0.0083 |
| trade_activity | <2 | 25 | 7 | 0.0322 | -0.0024 |
| trade_activity | >=2 | 35 | 7 | 0.0391 | -0.0063 |

The model stays frozen regardless of this result. This event cannot be reused as an untouched final test for a revised model. The live/default Rating and public site remain unchanged.
