# Multikill definition experiment - 2026-10-01

Preregistered at `709c41c`; implementation `a0608ab`. Record `multikill-20261001T195254Z` in experiment-log.jsonl contains all models, seven event folds, metric thresholds, raw coefficient drift and fold ranges. Dataset hash is fixed in multikill-plan.json. No reparsing or rederivation; objectives are unavailable and excluded. The former objective coefficient was exactly zero, so dropping that constant column does not change the comparison. Baseline results were reused, not refit.

| Definition | Seven-event pooled MAE (299) | August MAE (32) |
| --- | ---: | ---: |
| Existing kills beyond first | 0.036467 | 0.034530 |
| Fraction of rounds with 2+ kills | 0.039443 | 0.036818 |
| Separate 2K / 3K / 4K / 5+K fractions | 0.036508 | 0.034119 |

The binary 2+ indicator loses useful information and worsens both comparisons. Its KPR slope rises by 0.1041 (18.5%) and KOST falls by 0.0673 (13.4%). Do not adopt it.

Separate buckets barely improve August (0.000411) and slightly worsen pooled event validation (0.000041). Shared raw-unit slopes stay within 0.004271 of baseline. Learned bucket slopes are 0.2081, 0.4477, 0.7170 and 0.0; the first three approximately reproduce increasing kills-beyond-first weight. The zero 5+ coefficient reflects no training observations, not evidence that aces have zero value. Extra degrees of freedom do not establish an improvement. Retain the simpler existing definition for the next experiment; no final candidate is frozen.

The largest August miss remains Nuers on Chalet: bucket prediction 1.4831 versus 1.61. Yoggah on Chalet remains overpredicted (0.0310 versus -0.06), and AsK on Kafe underpredicted (1.1101 versus 1.19). These residuals do not justify tuning individual players. Baseline pooled median error was not saved previously and is not reconstructed by another fit. New variants save median error and signed bias as well as the existing threshold metrics.

Both September events remain excluded, including all 60 final NA rows. Tests: 99 Python passed, one optional smoke skipped, six subtests passed. No runtime formula, database, archives, public JSON or publishing changed.

NEXT: preregister separate opening-kill and opening-death terms against the unchanged baseline. Keep multikills as kills beyond first, trades at the existing eight seconds, alpha=1 and the same event splits; assess whether the equal/opposite opening constraint is supported. Do not combine successful-looking family changes without a separate controlled plan.
