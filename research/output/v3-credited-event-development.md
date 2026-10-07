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

Exact per-event metrics, all thresholds, fold models, residual quantiles, objective-positive and kill-credit-affected residuals are preserved in the private experiment. No new final event was selected or opened during this development experiment.

## Candidate event folds and subgroup residuals

| Held-out event | Rows | Exact v2 MAE | Candidate MAE | within .05 |
| --- | ---: | ---: | ---: | ---: |
| APAC Kickoff | 50 | .05145 | .02897 | 84.0% |
| ASIA Stage 1 | 18 | .04526 | .03629 | 72.2% |
| APAC North Stage 2 (consumed development) | 100 | .05093 | .03419 | 77.0% |
| EWC | 30 | .03872 | .02451 | 86.7% |
| EMEA Stage 1 | 50 | .04570 | .02540 | 86.0% |
| NA Stage 1 | 150 | .04988 | .02890 | 84.0% |
| Salt Lake City Major | 60 | .05197 | .03220 | 81.7% |
| SAL Stage 1 | 50 | .03900 | .02676 | 86.0% |
| SAL Stage 2 (consumed development) | 180 | .05153 | .03456 | 77.2% |

The pooled development qualification passes; several individual events remain below80%. Those failures/limits are preserved and are not grounds for residual-specific tuning or regrading their historical finals.

| Subgroup | Rows | MAE | RMSE | Median AE | Max AE | within .05 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Objective-positive | 147 | .03075 | .04097 | .02470 | .16662 | 83.0% |
| Kill-credit-affected | 194 | .03029 | .04157 | .02280 | .14898 | 82.5% |

Candidate pooled signed residual mean+.00012, median+.00442; quantiles5/10/25/50/75/90/95% are-.07534/-.05296/-.02011/+.00440/+.02435/+.04594/+.06321. Raw intercept.07071561632224965. The exact standardized model and full-precision coefficients remain in the frozen candidate; these rounded report values must not become runtime constants.
