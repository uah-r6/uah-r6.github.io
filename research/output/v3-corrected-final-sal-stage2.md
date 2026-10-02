# One-shot corrected-KOST v3 South America Stage 2 final evaluation

Experiment `v3-corrected-final-sal-20261002T223637Z`. Event permanently consumed; no automatic deployment.

Evidence: {'clean_rows': 141, 'clean_maps': 18, 'distinct_rosters': 10, 'objective_positive_rows': 24}. Gates: {'min_clean_rows': True, 'min_clean_maps': True, 'min_distinct_rosters': True, 'min_objective_positive_rows': True, 'max_mae': True, 'relative_mae_improvement': True, 'within_005': False, 'max_abs_error': True, 'rmse_not_worse': True}. Passed: False.

| Model | N | MAE | RMSE | Median AE | Max AE | within .01 | .02 | .03 | .05 | .10 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Frozen v2 | 141 | 0.04142 | 0.05538 | 0.02905 | 0.16479 | 16.3% | 33.3% | 51.1% | 71.6% | 90.8% |
| Frozen v3 objectives | 141 | 0.03496 | 0.04957 | 0.02226 | 0.18693 | 27.0% | 44.7% | 59.6% | 75.9% | 94.3% |

Inputs keep fully objective-corrected KOST identical in both arms and add verified objectives only. No actor labels or Rating residuals used for eligibility. Missing actors exclude entire maps. All prospectively selected archives had predictions and quality decisions saved before the first Rating read. Scope is the linked-archive snapshot, not every event match. Live v2 and historical data unchanged.
