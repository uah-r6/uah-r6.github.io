# Rating deployment review - frozen research candidate

**Status: review only.** The raw candidate was frozen in local commit `eb747f8` before the reserved North America Stage 2 event was evaluated once. It has not replaced `collegiate_v1`, recalculated live history, changed public JSON, or been published. Proposed version name if approved: `siege_style_v2`. This is an independent approximation of public SiegeGG ratings, not an official or exact SiegeGG formula.

## Formula and feature definitions

The authoritative [frozen model](../frozen-rating-candidate.json) uses training-only centering/scaling and ridge alpha 1. Its equivalent raw-unit expression, rounded here for reading, is:

```text
Rating = 0.0729573564
       + 0.5617450120 * kills_per_round
       - 0.2033304627 * teamkills_per_round
       + 0.2271374370 * extra_multikill_kills_per_round
       + 0.1462931438 * opening_differential_per_round
       + 0.6688825547 * successful_clutches_per_round
       + 0.5031573547 * KOST_rounds_per_round
       + 0.4900450520 * survival_rounds_per_round
       + 0.1418045861 * trade_differential_per_round
```

`extra_multikill_kills` is `sum(max(opponent_kills_in_round-1,0))`. Opening differential is opponent opening kills minus opening deaths. A clutch is one round won after the player first became their team's sole survivor against one to five living opponents; all sizes have equal credit. KOST is the OR of opponent kill, verified credited objective, survived round, or traded death. A death is traded when a teammate kills its killer within the inclusive eight-second timer window. A kill is traded when the victim's teammate kills its killer within that window. Trade differential is deaths traded minus kills traded. All rates divide by player rounds. The saved model contains a ninth objective coefficient of **exactly zero**; objectives are functionally omitted because trustworthy player attribution is unavailable. Operator normalization is not applied.

The formula above is display-rounded. Use the exact model in the frozen JSON for any implementation or comparison; avoid introducing rounding drift. The [trade audit](trade-semantics-audit.md) documents equal timestamps, chains and coarse whole-second replay timers. The model uses current normalized kill identities and inherits their limits.

## Data and method

Official Ubisoft professional replay archives and cached public SiegeGG player-map targets are enumerated in [sources.json](../sources.json). The dataset has 56 maps / 560 player-map observations. Strict replay map/score/roster, public K/D, round-count, and alias checks leave 407 clean rows. Seven earlier events supply 299 training rows. August EWC provides 32 development rows from four maps. Sixteen clean historical September EMEA rows were evaluated by an earlier model and excluded here. The reserved NA Stage 2 event contributes 60 clean rows across seven maps. No final rows informed features, coefficients, regularization or candidate choice. The [frozen record](../frozen-rating-candidate.json) includes the dataset, source manifest, parser binary, adapter and derivation code hashes plus exact source events, coefficients and scaler values.

Event-held-out development CV uses whole events, avoiding player rows from the same match appearing in both sides of a fold. Current model structure is raw standardized ridge, alpha 1 with unpenalized intercept. [Pre-freeze review](pre-freeze-review.md) compares trade, multikill, opening, KOST/survival and clutch variants. The existing eight-family raw baseline was selected for consistency and simplicity. Operator-relative methods performed worse across the earlier event folds; sparse per-operator samples did not justify revisiting them.

## Accuracy on development and reserved final event

| Evaluation | N / maps | MAE | RMSE | Median AE | Max AE | Within .05 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Seven-event pooled CV | 299 / 43 | 0.03647 | 0.04898 | unavailable in saved CV | 0.1838 | 74.6% |
| August EWC development | 32 / 4 | 0.03453 | 0.04626 | 0.02248 | 0.1338 | 71.9% |
| **Frozen NA Stage2 final** | **60 / 7** | **0.03623** | **0.04945** | **0.03080** | **0.1494** | **81.7%** |
| `collegiate_v1` on same NA rows | 60 / 7 | 0.23875 | 0.2940 | 0.1963 | 0.7322 | 10.0% |

The [one-time final report](final-na-rating-evaluation.md) also gives exact rounded match rate 13.3%, within .01/.02/.03/.05/.10 of 20.0/35.0/45.0/81.7/93.3%, signed bias -0.0047 and the eight largest misses. `collegiate_v1` was evaluated on the exact same 60 clean rows without tuning. The final event cannot serve again as untouched validation for a revised candidate.

The last clean-data expansion moved each varying raw-unit slope by less than 0.007; an earlier expansion moved clutch by about 0.061. Nine training teamkills, 29 clutch rounds and zero 1v5 rounds mean some coefficients have weak support despite useful aggregate prediction. The latest candidate differences were assessed across seven event folds and August; no small single-split gain justified extra features.

## Residual limits and UAH sanity check

The final set's 17 publicly objective-credited player-map rows have candidate signed bias **-0.0378**; 43 rows without such credit have **+0.0084**. The analogous August pattern was -0.0382 versus +0.0034. This is consistent with missing player objective information, but does not establish causal credit or permit inserting public labels into the model. Eight final rows on Border have MAE 0.0630; these and individual misses are descriptive after the one-time test, not grounds for refitting on it. Seven maps still give limited event diversity. The clean quality gate excludes 153 other observations with documented identity, kill/death or round-count issues. See [quality report](../quality-report.md).

A [read-only UAH comparison](uah-frozen-sanity.md) used five stored NECC maps / 62 rounds; database SHA-256 was unchanged. Season comparisons are:

| Player | Current `collegiate_v1` | Frozen candidate | Difference |
| --- | ---: | ---: | ---: |
| Tallman3.14 | 0.421 | 0.718 | +0.297 |
| OhWowJay | 1.541 | 1.248 | -0.292 |
| DinoFireKing | 0.986 | 0.895 | -0.091 |
| Lgon | 1.441 | 1.242 | -0.200 |
| AzoozNewzz | 0.892 | 0.990 | +0.098 |

These are two different rating scales and are not UAH ground truth. The candidate was fitted only to professional data; UAH maps did not influence feature selection or coefficients. The UAH archive's 17 plant and three disable **occurrences** remain actor-unresolved. The known actor diagnostic wrongly credited Aiden in professional 4139 R07 and was not promoted. Player objective credit and KOST remain conservative.

## Proposed implementation and versioning, subject to approval

If approved, implement `siege_style_v2` as an explicit alternate rating version using the frozen exact coefficients and training normalization, with `collegiate_v1` preserved for comparison. Calculate from stored normalized rounds so existing maps can be evaluated without `.rec` reparsing. Store the rating version with generated values and keep historical identity, match and objective data intact. Recompute derived ratings transactionally in a local migration or export path, then validate map/season/career aggregation and website labels before any publish. Do not silently overwrite the current public rating; a display-default change and website publication should be separate reviewed actions. The objective limitation should be visible in methodology if the candidate is exposed publicly.

No deployment is performed in this review. Python verification after the research changes: 107 passed, one optional replay smoke test skipped, six subtests passed. Frontend and Go code were unchanged during this research phase.
