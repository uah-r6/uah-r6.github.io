# Native event order and clutch-size development

v3-native-order-20261007T053828Z

Credited count-derived KPR/MK/KOSTKill and supported objective signal preserved. Native opening explicitly measures FINISHER first opposing elimination, not inferred credited opening owner. Legacy trade and KOST trade flags retained under v2 compatibility; precise credited trades remain NOT READY. This does not change production chronology, action-start operators, or historical v2 snapshots. Old 118/299-row linear clutch studies remain rejected; APAC/SAL/CNL final failures remain permanent, never rerun. CNL is now consumed development, not new independent accuracy.

988 clean rows, 99 maps, 10 whole-event folds. CNL is permanently consumed development.

Exact within-.05 coverage: native_linear_size0.7995951417004049 (FAIL80%); native_triangular_size0.8097165991902834 (PASS development). Rounded table labels are display only. The triangular arm improves MAE7.0% over native count with9/10event wins. Objective-positive233rowsMAE0.03118657; kill-credit-affected303rowsMAE0.02884043. These are development results; several individual events remain below80%, and a new untouched final is required.

| Arm | MAE | RMSE | Median AE | Max AE | .01 | .02 | .03 | .05 | .10 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| exact_frozen_v2_original | 0.053661 | 0.072360 | 0.038048 | 0.337887 | 15.0% | 27.5% | 40.7% | 59.3% | 83.7% |
| legacy_count | 0.032552 | 0.045291 | 0.024288 | 0.352266 | 24.0% | 43.7% | 59.6% | 79.4% | 96.3% |
| native_count | 0.032602 | 0.045217 | 0.023945 | 0.355371 | 23.2% | 43.0% | 59.9% | 79.1% | 96.6% |
| native_linear_size | 0.030990 | 0.041936 | 0.023427 | 0.196435 | 24.0% | 44.0% | 61.5% | 80.0% | 97.3% |
| native_triangular_size | 0.030317 | 0.040982 | 0.022388 | 0.175312 | 24.6% | 44.9% | 62.1% | 81.0% | 97.4% |

## Whole-event validation

| Event | Rows | exact_frozen_v2_original | legacy_count | native_count | native_linear_size | native_triangular_size |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Asia Pacific Kickoff 2026 | 50 | 0.05145 / 66.0% | 0.03003 / 84.0% | 0.03036 / 84.0% | 0.02616 / 86.0% | 0.02374 / 92.0% |
| Asia Pacific League Stage 1 2026 | 18 | 0.04526 / 61.1% | 0.03712 / 77.8% | 0.03696 / 77.8% | 0.03653 / 77.8% | 0.03704 / 77.8% |
| Asia Pacific League Stage 2 - APAC N 2026 | 100 | 0.05093 / 65.0% | 0.03487 / 78.0% | 0.03515 / 77.0% | 0.03370 / 77.0% | 0.03279 / 78.0% |
| China League 2026 Stage 1 | 300 | 0.06422 / 51.7% | 0.03524 / 75.3% | 0.03487 / 74.7% | 0.03367 / 74.3% | 0.03286 / 76.0% |
| Esports World Cup 2026 | 30 | 0.03872 / 73.3% | 0.02501 / 86.7% | 0.02643 / 86.7% | 0.02438 / 90.0% | 0.02355 / 90.0% |
| Europe MENA League Stage 1 2026 | 50 | 0.04570 / 58.0% | 0.02609 / 82.0% | 0.02597 / 84.0% | 0.02493 / 86.0% | 0.02415 / 86.0% |
| North America League Stage 1 2026 | 150 | 0.04988 / 60.7% | 0.02914 / 84.0% | 0.02909 / 83.3% | 0.02825 / 83.3% | 0.02800 / 83.3% |
| Salt Lake City Major 2026 | 60 | 0.05197 / 58.3% | 0.03279 / 78.3% | 0.03285 / 81.7% | 0.03177 / 81.7% | 0.03116 / 78.3% |
| South America League Stage 1 2026 | 50 | 0.03900 / 70.0% | 0.02717 / 86.0% | 0.02722 / 86.0% | 0.02507 / 88.0% | 0.02630 / 86.0% |
| South America League Stage 2 2026 | 180 | 0.05153 / 61.1% | 0.03433 / 78.3% | 0.03480 / 77.8% | 0.03225 / 80.6% | 0.03147 / 82.8% |

## Qualification

{
  "native_count": {
    "checks": {
      "events": true,
      "rows": true,
      "mae_improvement": true,
      "within_005": false,
      "rmse": true,
      "max_error": false,
      "objective_positive": true,
      "kill_credit_affected": true
    },
    "qualified": false
  },
  "native_linear_size": {
    "checks": {
      "events": true,
      "rows": true,
      "mae_improvement": true,
      "within_005": false,
      "rmse": true,
      "max_error": true,
      "objective_positive": true,
      "kill_credit_affected": true,
      "mae_vs_native_count": false,
      "broad_event_wins": true
    },
    "qualified": false
  },
  "native_triangular_size": {
    "checks": {
      "events": true,
      "rows": true,
      "mae_improvement": true,
      "within_005": true,
      "rmse": true,
      "max_error": true,
      "objective_positive": true,
      "kill_credit_affected": true,
      "mae_vs_native_count": true,
      "broad_event_wins": true
    },
    "qualified": true
  }
}

Selected: native_triangular_size. No new final target opened.

## Raw coefficients and whole-event drift

| Arm / feature | Full | v2 | Fold min | Fold max |
| --- | ---: | ---: | ---: | ---: |

legacy_count raw intercept: 0.0713634230

| legacy_count/kpr | 0.58408328 | 0.56174501 | 0.56874623 | 0.59002011 |
| legacy_count/teamkills | -0.16941630 | -0.20333046 | -0.22237012 | -0.11343883 |
| legacy_count/multikill | 0.22976533 | 0.22713744 | 0.21919160 | 0.24266760 |
| legacy_count/opening | 0.14229079 | 0.14629314 | 0.13635617 | 0.14731595 |
| legacy_count/clutch | 0.56418441 | 0.66888255 | 0.52469072 | 0.58435836 |
| legacy_count/kost | 0.46690033 | 0.50315735 | 0.46231455 | 0.48233943 |
| legacy_count/survival | 0.48570297 | 0.49004505 | 0.47924289 | 0.49040782 |
| legacy_count/trade | 0.09080683 | 0.14180459 | 0.08612744 | 0.10174616 |
| legacy_count/objectives | 0.44674451 | 0.00000000 | 0.43108784 | 0.45941566 |

native_count raw intercept: 0.0739523741

| native_count/kpr | 0.58060491 | 0.56174501 | 0.56465734 | 0.58670155 |
| native_count/teamkills | -0.15646295 | -0.20333046 | -0.22102034 | -0.09746009 |
| native_count/multikill | 0.23229862 | 0.22713744 | 0.22088865 | 0.24770977 |
| native_count/opening | 0.14907393 | 0.14629314 | 0.14324719 | 0.15441555 |
| native_count/clutch | 0.54293454 | 0.66888255 | 0.49103216 | 0.55946113 |
| native_count/kost | 0.46516925 | 0.50315735 | 0.46030615 | 0.48395505 |
| native_count/survival | 0.48736271 | 0.49004505 | 0.47947575 | 0.49158272 |
| native_count/trade | 0.08962265 | 0.14180459 | 0.08561413 | 0.10036604 |
| native_count/objectives | 0.44159651 | 0.00000000 | 0.42595079 | 0.45427028 |

native_linear_size raw intercept: 0.0736797181

| native_linear_size/kpr | 0.58593389 | 0.56174501 | 0.57409117 | 0.59112908 |
| native_linear_size/teamkills | -0.16750011 | -0.20333046 | -0.21319882 | -0.11152127 |
| native_linear_size/multikill | 0.22084203 | 0.22713744 | 0.21192400 | 0.23280189 |
| native_linear_size/opening | 0.15354060 | 0.14629314 | 0.14584282 | 0.15936266 |
| native_linear_size/clutch | 0.42687074 | 0.66888255 | 0.41868441 | 0.43316783 |
| native_linear_size/kost | 0.46263758 | 0.50315735 | 0.45776526 | 0.47714161 |
| native_linear_size/survival | 0.48500298 | 0.49004505 | 0.47699760 | 0.48872775 |
| native_linear_size/trade | 0.09289131 | 0.14180459 | 0.08900978 | 0.10115376 |
| native_linear_size/objectives | 0.44276572 | 0.00000000 | 0.42728104 | 0.45434982 |

native_triangular_size raw intercept: 0.0737371448

| native_triangular_size/kpr | 0.58934525 | 0.56174501 | 0.58012537 | 0.59347802 |
| native_triangular_size/teamkills | -0.17239941 | -0.20333046 | -0.22386218 | -0.11435179 |
| native_triangular_size/multikill | 0.22024796 | 0.22713744 | 0.21313075 | 0.22909978 |
| native_triangular_size/opening | 0.15314679 | 0.14629314 | 0.14403245 | 0.15958058 |
| native_triangular_size/clutch | 0.24526145 | 0.66888255 | 0.24195967 | 0.25187865 |
| native_triangular_size/kost | 0.45918062 | 0.50315735 | 0.45466198 | 0.47206013 |
| native_triangular_size/survival | 0.48817554 | 0.49004505 | 0.48026535 | 0.49160402 |
| native_triangular_size/trade | 0.09612610 | 0.14180459 | 0.09261589 | 0.10375085 |
| native_triangular_size/objectives | 0.45020061 | 0.00000000 | 0.43498454 | 0.46251505 |

Subgroup, residual quantiles, all fold coefficients, all row errors and immutable input hashes are preserved in the private experiment and compact public experiment log. Fixed size transforms have sparse 1v4/5 support; no individual size coefficients were fitted.
