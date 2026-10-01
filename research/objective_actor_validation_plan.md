# Predeclared objective actor validation — 2026-10-01

## Discovery sample and frozen candidate

The seven already inspected development maps (SiegeGG matches 4150, 4132, 3585, 6156, 3073, 3554, 4112) have 32 public objective events. The broad nearby +100-score heuristic had three demonstrably wrong uniquely named planters. In those three cases, the scoreboard entity was 8, 14, or 19 below the selected player `DissectID`; the normal score entity association in correctly joined cases is exactly four below. This suggests an entity-identity collision, though it does not prove the +100 reward is always for an objective.

Freeze this **diagnostic candidate** before inspecting the validation targets:

1. Use the pre-existing defuser timer-run grouping and a minimum timer value `<= 0.10` seconds to define a completion candidate.
2. Inspect only +100 cumulative score changes in the same physical round that occur from 0 through 2,000 decompressed bytes after the terminal timer packet.
3. Accept a player candidate only when the score property's entity is exactly `player DissectID - 4` and exactly one distinct player satisfies the rule for that completion.
4. Leave all other actors unresolved. Do not use public actor names, sole-survivor inference, or a wider score window to fill gaps.

This candidate names 17 of 32 discovery events, with 15 exact public-name matches, two evident aliases (`JJBlazt`/`JJBlaztful`, `Riv4l`/`Rival`), zero definite mismatches, 14 unresolved, and one ambiguous disable. This is **in-sample**, so it is not a production rule. No disable actor is reliably identified in the discovery sample.

## Locked independent development validation set

Selected from cached complete physical maps and three distinct events **before opening their public round-actor logs**:

| Event | SiegeGG match/game | Replay folder |
| --- | --- | --- |
| Europe MENA Stage 1, G2–Geekay | 3637 / 6842 | `Match-2026-06-08_20-21-34-35484` |
| North America Stage 1, Shopify–Outlast | 4140 / 8330 | `Match-2026-07-03_17-34-53-12240` |
| South America Stage 1, LOUD–FaZe | 4118 / 8666 | `Match-2026-07-05_11-17-25-19616` |

Check objective occurrence, event order, every named candidate, missed event, and wrong actor separately by map and event. Any wrong named actor falsifies the current candidate. A good result remains preliminary and must be checked on further events before affecting parser output, KOST, Rating inputs, UAH statistics, or public JSON. The reserved North America Stage 2 Rating event is excluded from this work.
