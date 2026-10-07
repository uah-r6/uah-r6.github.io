# Corrected-count whole-event Rating development

v3-credited-event-folds-20261007T043107Z

Frozen v2 reference has seen some earlier development rows; candidate predictions leave the entire event out. Consumed APAC/SAL finals are broad development only, not new final accuracy. Event features retain documented legacy semantics. No individual final residual tuning or coefficient search.

688 clean player-map rows, 69 maps, 9 whole-event folds.

| Model | MAE | RMSE | Median AE | Max AE | within .01 | .02 | .03 | .05 | .10 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| exact_frozen_v2_original | 0.04906 | 0.06585 | 0.03575 | 0.29312 | 15.8% | 29.1% | 43.5% | 62.6% | 87.2% |
| frozen_v2_corrected | 0.03600 | 0.04804 | 0.02706 | 0.17314 | 20.8% | 37.1% | 55.2% | 76.2% | 94.8% |
| corrected_eight | 0.03613 | 0.04823 | 0.02655 | 0.18928 | 18.2% | 38.4% | 55.7% | 75.0% | 94.5% |
| corrected_nine_objectives | 0.03103 | 0.04287 | 0.02273 | 0.19616 | 25.3% | 45.1% | 62.1% | 81.1% | 96.4% |

## Predeclared development qualification

{
  "corrected_eight": {
    "checks": {
      "events": true,
      "rows": true,
      "mae_improvement": true,
      "within_005": false,
      "rmse": true,
      "max_error": true
    },
    "qualified": false
  },
  "corrected_nine_objectives": {
    "checks": {
      "events": true,
      "rows": true,
      "mae_improvement": true,
      "within_005": true,
      "rmse": true,
      "max_error": true
    },
    "qualified": true
  }
}

## Coefficients and whole-event drift

| Model / feature | Raw | v2 raw | Fold min | Fold max |
| --- | ---: | ---: | ---: | ---: |
| corrected_eight/kpr | 0.53896527 | 0.56174501 | 0.52267151 | 0.54567686 |
| corrected_eight/teamkills | -0.17453068 | -0.20333046 | -0.24716399 | -0.10064653 |
| corrected_eight/multikill | 0.27298234 | 0.22713744 | 0.26272271 | 0.29520602 |
| corrected_eight/opening | 0.13930607 | 0.14629314 | 0.13297447 | 0.14533032 |
| corrected_eight/clutch | 0.53826998 | 0.66888255 | 0.52166409 | 0.57248245 |
| corrected_eight/kost | 0.50707018 | 0.50315735 | 0.50199128 | 0.51333504 |
| corrected_eight/survival | 0.49081299 | 0.49004505 | 0.48145119 | 0.49610654 |
| corrected_eight/trade | 0.09162881 | 0.14180459 | 0.08347234 | 0.11549253 |
| corrected_eight/objectives | 0.00000000 | 0.00000000 | 0.00000000 | 0.00000000 |
| corrected_nine_objectives/kpr | 0.56874623 | 0.56174501 | 0.55322356 | 0.57389470 |
| corrected_nine_objectives/teamkills | -0.22237012 | -0.20333046 | -0.26734609 | -0.11491258 |
| corrected_nine_objectives/multikill | 0.24266760 | 0.22713744 | 0.23104060 | 0.26194918 |
| corrected_nine_objectives/opening | 0.14161453 | 0.14629314 | 0.13330539 | 0.14843352 |
| corrected_nine_objectives/clutch | 0.52469072 | 0.66888255 | 0.48989490 | 0.55318615 |
| corrected_nine_objectives/kost | 0.48233943 | 0.50315735 | 0.47800784 | 0.48830478 |
| corrected_nine_objectives/survival | 0.47924289 | 0.49004505 | 0.47169571 | 0.48598090 |
| corrected_nine_objectives/trade | 0.09573848 | 0.14180459 | 0.08906231 | 0.11586582 |
| corrected_nine_objectives/objectives | 0.43814020 | 0.00000000 | 0.40820015 | 0.45703141 |

Exact per-event metrics, all thresholds, fold models, residual quantiles, objective-positive and kill-credit-affected residuals are preserved in the private experiment. No new final event was selected or opened.
