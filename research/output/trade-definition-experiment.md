# Trade representation experiment - 2026-10-01

Preregistered `research/trade-definition-plan.json` and fitted at the fixed eight-second window. Record `trade-def-20261001T220800Z` contains full seven-fold metrics, saved models and coefficients. The 299-row pre-August / 32-row August development split and all other features are unchanged. Objectives are unavailable and omitted. Both September events remain excluded.

| Feature | Pooled event-fold MAE | August MAE | Raw trade slope |
| --- | ---: | ---: | ---: |
| Current `(deaths_traded-kills_traded)/rounds` | **0.03647** | **0.03453** | +0.1418 |
| `deaths_traded/rounds` only | 0.03917 | 0.03625 | +0.1253 |
| `kills_traded/rounds` only | 0.03770 | 0.04004 | -0.1750 |

The differential carries more information than either component alone. Removing either component shifts other weights: death-only changes KPR by 0.0327, multikill by 0.0341 and survival by 0.0417; kill-only changes KOST by 0.1111 and survival by 0.0723. That pattern reinforces retaining the current simple differential. It does not establish SiegeGG's exact trade rule.

The eight-second source semantics are detailed in [trade-semantics-audit.md](trade-semantics-audit.md). The window experiment found no robust reason to alter eight seconds. Both trade experiments kept the cached eight-second KOST; changing the live setting would also affect KOST, so these isolated fits must not be deployed as a runtime setting change.

NEXT: audit KOST versus survival using development player-rounds. The clean training rows contain 1,986 KOST-positive player-rounds and 925 survival-positive player-rounds among 3,215 player-rounds; player objective credits are zero. Compare a small preregistered set of KOST/survival definitions with the same event splits, watching for coefficient instability and proxy compensation for missing objectives.
