# First v3 verified-objective development comparison

Experiment`v3-objectives-20261002T213548Z`. Fixed raw standardized ridge alpha1, no parameter search. Train284 rows versus original v2299; EWC development22 versus original32. Both September final events excluded. Maps with unresolved objective actors excluded, not treated as zero.

A is the exact frozen v2 model and coefficients. B fits the exact same raw family plus verified plants+disables/round. Every eight-feature input and baseline prediction is checked against the original observation. Recomputed KOST is reported in the derivation report and kept out of this one-feature experiment. The candidate train subset differs, so drift can also reflect sample selection. Deployed v2 and its final MAE0.03623 are unchanged.

| Split / model | N | MAE | RMSE | Median AE | Max AE | within .01 | .02 | .03 | .05 | .10 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| train/frozen_v2 | 284 | 0.03390 | 0.04538 | 0.02610 | 0.18155 | 22.2% | 38.4% | 56.7% | 77.5% | 96.1% |
| train/v3_objectives | 284 | 0.02970 | 0.03973 | 0.02301 | 0.15241 | 27.1% | 43.0% | 63.7% | 81.7% | 97.5% |
| development/frozen_v2 | 22 | 0.02949 | 0.03770 | 0.02248 | 0.07923 | 27.3% | 45.5% | 63.6% | 77.3% | 100.0% |
| development/v3_objectives | 22 | 0.02345 | 0.02762 | 0.01814 | 0.06072 | 18.2% | 54.5% | 72.7% | 95.5% | 100.0% |

## Every coefficient drift

| Feature | v2 standardized | v3 standardized | v2 raw | v3 raw | Raw change |
| --- | ---: | ---: | ---: | ---: | ---: |
| kpr | 0.17833840 | 0.18199896 | 0.56174501 | 0.57512133 | 0.01337632 |
| teamkills | -0.00374096 | -0.00423832 | -0.20333046 | -0.25023561 | -0.04690515 |
| multikill | 0.04305946 | 0.04196195 | 0.22713744 | 0.22184550 | -0.00529194 |
| opening | 0.02035351 | 0.02041090 | 0.14629314 | 0.14712835 | 0.00083520 |
| clutch | 0.01919180 | 0.01841958 | 0.66888255 | 0.63429489 | -0.03458766 |
| kost | 0.08461565 | 0.08010175 | 0.50315735 | 0.48381183 | -0.01934553 |
| survival | 0.08714551 | 0.08158621 | 0.49004505 | 0.46305371 | -0.02699134 |
| trade | 0.01937037 | 0.01676777 | 0.14180459 | 0.12778144 | -0.01402315 |
| objectives | 0.00000000 | 0.02225588 | 0.00000000 | 0.47422249 | 0.47422249 |

Standardized intercept: 0.96632107 -> 0.97031690.

## Objective-heavy player-map residual changes

Objective-heavy means at least2 verified objectives on the map; selected from replay features, not errors. Residual is prediction minus target; negative AE change improves. Every qualifying row is listed.

| Split / match / game / player | Objectives | v2 residual | v3 residual | AE change |
| --- | ---: | ---: | ---: | ---: |
| train/4150/7419/Hotancold.100T | 2 | -0.04646 | 0.02485 | -0.02160 |
| train/4137/8073/Spiker.WC | 2 | -0.03493 | 0.01615 | -0.01878 |
| train/4112/8360/live.LOUD | 3 | -0.12644 | -0.01335 | -0.11308 |
| train/3563/6673/Canadian | 2 | -0.15078 | -0.06792 | -0.08286 |
| train/3554/6679/kyno | 2 | -0.15204 | -0.04693 | -0.10511 |
| train/3880/7625/Pikanzu.Daystar | 2 | -0.06298 | 0.02812 | -0.03486 |
| train/3880/7625/SpeakEasy.WBG | 2 | -0.05149 | 0.02507 | -0.02642 |
| development/6156/10425/kyno | 3 | -0.07020 | 0.01398 | -0.05622 |
| development/6157/10430/vitaking | 2 | -0.01745 | 0.04322 | 0.02577 |

## Interpretation and next gate

This is one deliberate development experiment, not a final result or deployment approval. Inspect objective coefficient stability and sample exclusion before choosing a new frozen candidate. A different untouched event must be metadata-reserved before its objective/Rating outcomes are examined. Never use the old NA Stage2 set as a new final holdout. No v3 runtime model/default is installed.

86 protected live file hashes, original dataset/frozenv2 hashes unchanged. Reproduce `.venv/Scripts/python.exe research/v3_objective_fit.py`; a matching dataset/experiment is deduplicated and never refit or appended twice.
