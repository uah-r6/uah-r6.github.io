# Current-cohort clutch weighting - 2026-10-01

Preregistered at `65b66a6`; record `clutch-20261001T222014Z`. The single tested change weights each successful first sole-survivor clutch by its original opponent count X, divided by rounds. The current total-clutch feature weights each clutch once. All other families and the 299-row seven-event / 32-row August split are fixed.

| Clutch feature | Pooled event-fold MAE | August MAE |
| --- | ---: | ---: |
| Equal credit per clutch | 0.03647 | **0.03453** |
| Linear size weight | **0.03491** | 0.03525 |

The pooled difference is larger than earlier tiny variant effects, but August moves the opposite way. The training support is sparse: 20 1v1, five 1v2, three 1v3, one 1v4, zero 1v5. Weighted improvement is not consistent across development views; retain equal credit. The older 118-row experiment also favored weighting in pooled folds but worsened August, so this is a repeated pattern rather than a newly stable win. No five-size coefficient fit is justified.

See [clutch audit](clutch-audit.md) for the actual first sole-survivor/winner definition. Nothing in this experiment changes match statistics or the live Rating.
