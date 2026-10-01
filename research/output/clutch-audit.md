# Clutch evidence audit - 2026-10-01

The stats engine processes normalized deaths in round order. At the first state where one living teammate remains against one to five living opponents, it saves the player and opponent count. It awards one clutch only when that team is the round winner; an objective win qualifies even if the surviving player later dies. Teamkills and suicides affect the alive set but are not opponent kills. The engine never infers a clutch from score alone. Synthetic cases in `tests/test_clutches.py` cover 1v1 through 1v5, downsizing, losses, zero opponents, objective wins, and aggregation.

`research/pipeline.py` stores every clean player's round-level total and `clutch_1v1` to `clutch_1v5`. The raw baseline uses `clutches/rounds`. The current seven-event training set has only 29 clutch player-rounds: 20 1v1, five 1v2, three 1v3, one 1v4, zero 1v5. The 32 August rows add only one clutch. A five-coefficient model is unsupported by these counts.

An earlier 118-row fit tested linear size weighting (`sum(X * clutch_1vX)/rounds`). It improved pooled early-event CV MAE from 0.04100 to 0.03933, but worsened August development from 0.03528 to 0.03662. The data and model were older, so one preregistered linear-weighting test on the present 299-row cohort is reasonable. No other clutch variants or weight search are planned.
