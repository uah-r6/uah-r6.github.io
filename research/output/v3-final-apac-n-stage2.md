# One-shot v3 APAC North Stage 2 final evaluation

Experiment `v3-final-apac-n-20261002T220620Z`. Event permanently consumed; no automatic deployment.

Evidence: {'clean_rows': 86, 'clean_maps': 11, 'distinct_rosters': 8, 'objective_positive_rows': 15}. Gates: {'min_clean_rows': True, 'min_clean_maps': True, 'min_distinct_rosters': True, 'min_objective_positive_rows': True, 'max_mae': True, 'relative_mae_improvement': True, 'within_005': False, 'max_abs_error': True, 'rmse_not_worse': True}. Passed: False.

| Model | N | MAE | RMSE | Median AE | Max AE | within .01 | .02 | .03 | .05 | .10 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Frozen v2 | 86 | 0.04217 | 0.05699 | 0.03177 | 0.20680 | 15.1% | 33.7% | 47.7% | 73.3% | 91.9% |
| Frozen v3 objectives | 86 | 0.03406 | 0.04803 | 0.02150 | 0.16537 | 24.4% | 47.7% | 61.6% | 75.6% | 94.2% |

Inputs keep occurrence-free KOST identical in both arms and add verified objectives only. No actor labels or Rating residuals used for eligibility. Missing actors exclude entire maps. All 12 prospectively selected archives had predictions and quality decisions saved before the first Rating read. Scope is the linked-archive snapshot, not every event match. Live v2 and historical data unchanged.
