# Corrected-KOST SAL consumed final diagnostics

The permanent one-shot result fails its 80% within0.05 gate. This report describes the already-consumed fixed cohort; it fits nothing, changes no gate, and does not admit excluded rows or revise historical metrics.

## Verified objective strata

| Stratum | N | v2 MAE | v3 MAE | v2 signed bias | v3 signed bias | v2 within .05 | v3 within .05 | Improved / worsened |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| all | 141 | 0.04142 | 0.03496 | -0.00121 | -0.00243 | 71.6% | 75.9% | 93 / 48 |
| verified_objective_positive | 24 | 0.05581 | 0.03328 | -0.05364 | -0.01781 | 58.3% | 79.2% | 20 / 4 |
| verified_objective_zero | 117 | 0.03847 | 0.03531 | +0.00954 | +0.00073 | 74.4% | 75.2% | 73 / 44 |
| objective_count_0 | 117 | 0.03847 | 0.03531 | +0.00954 | +0.00073 | 74.4% | 75.2% | 73 / 44 |
| objective_count_1 | 20 | 0.05311 | 0.03701 | -0.05051 | -0.01965 | 65.0% | 75.0% | 16 / 4 |
| objective_count_2 | 4 | 0.06930 | 0.01461 | -0.06930 | -0.00859 | 25.0% | 100.0% | 4 / 0 |

Paired map-cluster bootstrap (2000 draws, seed20261002, 18 maps): 95% percentile interval for v3 minus v2 MAE [-0.00936, -0.00356]. Descriptive uncertainty only: no new gate, tuning or claim of a fresh evaluation.

## Every objective-positive player-map residual

Raw objective addition is coefficient times objectives/round, without centering. Total prediction change also includes all frozen coefficient/intercept drift. These observational strata cannot isolate a causal effect of objectives.

| Official / player | Objectives | Target | v2 | v3 | AE change | Raw objective addition |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 8580/Nade.TLAW | 2 | 1.020 | 0.966 | 1.005 | -0.03973 | +0.05818 |
| 8582/R4re.BD | 2 | 1.440 | 1.323 | 1.408 | -0.08517 | +0.10181 |
| 8582/Swag.BD | 1 | 1.070 | 0.915 | 0.939 | -0.02423 | +0.05090 |
| 8584/Loira.FURIA | 1 | 0.930 | 0.898 | 0.932 | -0.03036 | +0.05090 |
| 8584/Nuxxga.LOS | 1 | 0.600 | 0.463 | 0.509 | -0.04540 | +0.05090 |
| 8586/HerdsZ.FURIA | 1 | 1.070 | 1.032 | 1.049 | -0.01702 | +0.03394 |
| 8587/Bassetto.L5 | 2 | 0.770 | 0.723 | 0.774 | -0.04331 | +0.05818 |
| 8589/cyber.FaZe | 1 | 1.020 | 0.996 | 1.009 | -0.01335 | +0.03702 |
| 8589/kds.FaZe | 1 | 1.300 | 1.198 | 1.222 | -0.02415 | +0.03702 |
| 8590/Dotz.FX | 1 | 0.860 | 0.848 | 0.866 | -0.00603 | +0.03394 |
| 8591/Dias.FURIA | 1 | 0.720 | 0.705 | 0.736 | +0.00091 | +0.04072 |
| 8591/FelipoX.TLAW | 2 | 1.490 | 1.431 | 1.498 | -0.05055 | +0.08145 |
| 8591/Kheyze.TLAW | 1 | 1.480 | 1.353 | 1.387 | -0.03352 | +0.04072 |
| 8592/stemp.LOUD | 1 | 1.050 | 0.995 | 1.033 | -0.03817 | +0.04525 |
| 8594/kds.FaZe | 1 | 0.720 | 0.690 | 0.718 | -0.02723 | +0.04072 |
| 8594/vitaking.FaZe | 1 | 1.490 | 1.423 | 1.450 | -0.02704 | +0.04072 |
| 8595/Maia.TLAW | 1 | 1.440 | 1.453 | 1.483 | +0.03073 | +0.05090 |
| 8595/live.LOUD | 1 | 0.450 | 0.427 | 0.474 | +0.00137 | +0.05090 |
| 8596/Hasaqui.IMP | 1 | 0.670 | 0.683 | 0.716 | +0.03247 | +0.04072 |
| 8596/Loira.FURIA | 1 | 1.270 | 1.258 | 1.281 | -0.00052 | +0.04072 |
| 8597/Bassetto.L5 | 1 | 0.740 | 0.699 | 0.730 | -0.03153 | +0.04072 |
| 8597/WIZARD.L5 | 1 | 1.310 | 1.197 | 1.238 | -0.04138 | +0.04072 |
| 8598/Daffo.LOS | 1 | 0.640 | 0.614 | 0.662 | -0.00380 | +0.05090 |
| 8599/Stk.INTZ | 1 | 0.910 | 0.884 | 0.912 | -0.02375 | +0.03394 |

## Largest 15 candidate errors

| Official / player | Target | v2 | v3 | v3 AE | Objectives |
| --- | ---: | ---: | ---: | ---: | ---: |
| 8585/FelipoX.TLAW | 1.370 | 1.205 | 1.183 | 0.18693 | 0 |
| 8580/AngelzZ.INTZ | 0.790 | 0.637 | 0.633 | 0.15657 | 0 |
| 8582/Swag.BD | 1.070 | 0.915 | 0.939 | 0.13101 | 1 |
| 8592/rappz.INTZ | 0.580 | 0.722 | 0.708 | 0.12843 | 0 |
| 8591/Bokzera.FURIA | 1.270 | 1.142 | 1.145 | 0.12544 | 0 |
| 8592/resetz.LOUD | 1.790 | 1.672 | 1.666 | 0.12435 | 0 |
| 8594/Bassetto.L5 | 0.290 | 0.421 | 0.405 | 0.11515 | 0 |
| 8580/FelipoX.TLAW | 0.870 | 0.782 | 0.769 | 0.10076 | 0 |
| 8582/Fntzy.FX | -0.080 | 0.018 | 0.019 | 0.09873 | 0 |
| 8598/dash.LOS | -0.080 | 0.018 | 0.019 | 0.09873 | 0 |
| 8591/Kheyze.TLAW | 1.480 | 1.353 | 1.387 | 0.09336 | 1 |
| 8584/Nuxxga.LOS | 0.600 | 0.463 | 0.509 | 0.09126 | 1 |
| 8585/mitrix.IMP | 1.010 | 0.928 | 0.919 | 0.09077 | 0 |
| 8597/LOBEX.FX | 0.940 | 1.041 | 1.030 | 0.08983 | 0 |
| 8594/PSYCHO.L5 | 0.850 | 0.948 | 0.939 | 0.08877 | 0 |

## Frozen feature contribution changes for the largest errors

| Official / player | kpr | teamkills | multikill | opening | clutch | kost | survival | trade | objectives |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 8585/FelipoX.TLAW | -0.0009 | -0.0000 | -0.0019 | -0.0003 | -0.0046 | -0.0008 | -0.0092 | +0.0001 | -0.0086 |
| 8580/AngelzZ.INTZ | -0.0042 | -0.0000 | +0.0001 | -0.0003 | +0.0003 | +0.0027 | +0.0036 | -0.0007 | -0.0086 |
| 8582/Swag.BD | -0.0083 | -0.0000 | +0.0011 | -0.0002 | +0.0003 | -0.0039 | -0.0098 | -0.0013 | +0.0423 |
| 8592/rappz.INTZ | -0.0070 | -0.0000 | +0.0011 | -0.0002 | +0.0003 | -0.0045 | +0.0026 | -0.0012 | -0.0086 |
| 8591/Bokzera.FURIA | +0.0057 | -0.0000 | -0.0034 | -0.0001 | +0.0003 | +0.0012 | +0.0029 | +0.0001 | -0.0086 |
| 8592/resetz.LOUD | +0.0113 | -0.0000 | -0.0039 | -0.0000 | -0.0051 | -0.0045 | -0.0054 | +0.0053 | -0.0086 |
| 8594/Bassetto.L5 | -0.0125 | -0.0000 | +0.0011 | -0.0003 | +0.0003 | +0.0032 | -0.0019 | -0.0010 | -0.0086 |
| 8580/FelipoX.TLAW | -0.0054 | -0.0000 | +0.0006 | -0.0003 | +0.0003 | -0.0003 | -0.0033 | +0.0001 | -0.0086 |
| 8582/Fntzy.FX | -0.0125 | -0.0000 | +0.0011 | -0.0006 | +0.0003 | +0.0114 | +0.0053 | +0.0001 | -0.0086 |
| 8598/dash.LOS | -0.0125 | -0.0000 | +0.0011 | -0.0006 | +0.0003 | +0.0114 | +0.0053 | +0.0001 | -0.0086 |
| 8591/Kheyze.TLAW | +0.0057 | -0.0000 | -0.0026 | -0.0001 | +0.0003 | -0.0029 | -0.0043 | +0.0013 | +0.0321 |
| 8584/Nuxxga.LOS | -0.0083 | -0.0000 | +0.0011 | -0.0002 | +0.0003 | +0.0038 | +0.0023 | +0.0001 | +0.0423 |
| 8585/mitrix.IMP | -0.0009 | -0.0000 | -0.0004 | -0.0002 | -0.0046 | +0.0012 | +0.0005 | +0.0001 | -0.0086 |
| 8597/LOBEX.FX | -0.0009 | -0.0000 | -0.0004 | -0.0001 | +0.0003 | -0.0049 | +0.0005 | -0.0010 | -0.0086 |
| 8594/PSYCHO.L5 | -0.0009 | -0.0000 | -0.0011 | -0.0003 | +0.0003 | -0.0008 | +0.0005 | -0.0022 | -0.0086 |

Intercept drift +0.00399583. All141 full decompositions are cached separately. The unchanged nine-family feature contract is not an operator-relative model; unresolved professional operators remain a compatibility limitation and were not guessed or introduced into this candidate.

Permanent result SHA256 `73b17d45f73cc7f07da5fc996bd9e1379017120d451e67c5e145ad1c1b9cbaa2` and all86 protected local hashes unchanged. Live v2, SQLite, private archives and public JSON remain unchanged. No fit, deployment or publishing.
