# Consumed countdown scope and full death ordering

{'rounds': 207, 'rounds_with_unique_plant_state': 47, 'rounds_with_full_order_change': 19, 'inverted_pairs': 88, 'cross_plant_inverted_pairs': 88, 'other_inverted_pairs': 0, 'zero_remaining_feedback_events': 100, 'raw_finisher_refrag_candidate_pairs': 648, 'candidate_pairs_crossing_plant': 51}

Uses only cached parser headers, explicit defuser-state plant anchors, raw death offsets and sealed replay identities. No downloads, parsing jobs, targets, fits or original derivation is repeated. The two independent official HUD controls corroborate the plant-reset explanation. No actor credit is needed to identify the occurrence anchor.

| Map / round | Plant state anchor | Inverted pairs across plant / other | Raw refrag candidates across plant | Zero-clock deaths |
| --- | --- | --- | --- | --- |
| 8580/R03 | [67137798] | 1 / 0 | 2 | 0 |
| 8580/R06 | [74412136] | 1 / 0 | 3 | 1 |
| 8581/R03 | [88885642] | 4 / 0 | 0 | 0 |
| 8581/R07 | [80412176] | 6 / 0 | 1 | 0 |
| 8582/R02 | [67447326] | 4 / 0 | 2 | 1 |
| 8582/R03 | [69458591] | 5 / 0 | 2 | 1 |
| 8582/R05 | [66165600] | 4 / 0 | 3 | 0 |
| 8583/R03 | [86249743] | 4 / 0 | 2 | 0 |
| 8583/R06 | [75939401] | 6 / 0 | 3 | 2 |
| 8583/R11 | [77572314] | 6 / 0 | 1 | 3 |
| 8585/R09 | [76297911] | 4 / 0 | 0 | 0 |
| 8586/R03 | [71281765] | 2 / 0 | 1 | 1 |
| 8587/R08 | [72480284] | 2 / 0 | 2 | 0 |
| 8587/R11 | [69818502] | 3 / 0 | 2 | 0 |
| 8591/R07 | [82116704] | 7 / 0 | 3 | 0 |
| 8594/R02 | [75199160] | 2 / 0 | 1 | 0 |
| 8594/R07 | [91932480] | 18 / 0 | 3 | 0 |
| 8597/R06 | [49269132] | 3 / 0 | 1 | 0 |
| 8599/R11 | [66876469] | 6 / 0 | 1 | 0 |

Plant state byte anchors distinguish serialization epochs, not exact elapsed-time boundaries. Clock0 can span planting overtime and round end. Coarse remaining differences across a reset are invalid elapsed time; within a phase they are only coarse observations. No generic credited-victim join, subsecond timestamp, trade policy or live ordering change is derived.

A later generic event model needs sequence/physical source, explicit clock epoch, separate raw remaining time and an unresolved elapsed-time field where overtime/terminal clocks cannot be calibrated. A scoreboard counter increment is a credited count observation, not a victim-linked timed elimination. Do not replace the live chronological helper or original v2 inputs from this descriptive inventory. Final-death ordering, generic credited ownership and trade elapsed time need separate validation and versioning.
