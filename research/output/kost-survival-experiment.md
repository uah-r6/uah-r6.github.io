# KOST and survival overlap - 2026-10-01

Preregistered `research/kost-plan.json`. Record `kost-20261001T221820Z` stores all seven event folds, coefficients, August metrics and drift. Development data remain 299 clean pre-August and 32 August player-map observations. Training has 3,215 player-rounds: 1,986 KOST-positive, 925 survival-positive and zero verified player-objective credits. The current KOST implementation marks a round if the player got an opponent kill, valid credited objective, survived, or had a traded death; all four are OR conditions. Because no clean training player-round has objective credit, current research KOST is effectively kill OR survive OR death traded.

| Features | Pooled fold MAE | August MAE | KOST raw slope | Survival raw slope |
| --- | ---: | ---: | ---: | ---: |
| Existing KOST + survival | **0.03647** | **0.03453** | +0.5032 | +0.4900 |
| KOST without survival path + survival | 0.04654 | 0.04055 | +0.4806 | +0.7186 |
| Existing KOST only | 0.06548 | 0.06811 | +0.9113 | absent |

Separate survival information is useful on this development sample, even though it is also one path into KOST. Removing that path worsens all seven event folds and increases the separate survival slope by about 0.229. Dropping the separate survival family also worsens every fold and nearly doubles the KOST slope. These changes do not support simplifying the baseline or claiming the two metrics cancel.

The objective limitation remains: credited actions are unavailable in this clean training cohort, and public credits were never used to construct KOST or any predictor. The model may still underpredict objective-heavy players; coefficient changes must not be interpreted as recovering missing objective credit.

NEXT: audit existing clutch semantics and prior weighted-clutch experiment against current larger cohort. The current clean training sample has only 29 clutch player-rounds (20 1v1, five 1v2, three 1v3, one 1v4, zero 1v5). Avoid a five-coefficient clutch fit unless new data support it. Keep final NA60 sealed.
