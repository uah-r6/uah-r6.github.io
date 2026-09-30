# Objective coverage diagnostic — development events only

This check uses the 266 clean player-map rows from the seven pre-August training events and the 32 previously viewed August EWC development rows. Both September events are excluded. It compares player-map public objective counts to the tracker counts derived from siege-dissect `matchFeedback` completion events; it does not compare Rating values or alter the tracker.

| Development group | Clean player-map rows | Public plants | Replay plants | Public disables | Replay disables |
| --- | ---: | ---: | ---: | ---: | ---: |
| Seven pre-August training events | 266 | 55 | 23 | 7 | 1 |
| August EWC validation | 32 | 11 | 1 | 4 | 0 |

The difference is not only player attribution. In the June 25 North America Stage 1 100 Thieves–Five Fears Lair map (SiegeGG match 4150), the public game target records four plants across its ten players. The complete 11-round replay parses with 78 `Kill` feedback entries and **no plant or disable feedback entries**. Its normalized map therefore records zero plants. The raw siege-dissect JSON used for this check is cached under ignored `data/research/diagnostics/nal-stage1-100t-five-fears-lair-raw.json`.

This shows that the present objective feature is incomplete relative to the public target in this sample. It does not establish which underlying replay packets or SiegeGG definitions account for each difference. The expanded fit's nearly zero objective weight is therefore weak evidence about any true objective contribution. Do not infer missing plants from round wins or silently replace replay values with public target counts; investigate the underlying events and definitions on development replays first. KOST and the live `collegiate_v1` formula were not changed.

The same June replay does contain 1,297 copies of the packet tag that siege-dissect's `readDefuserTimer` listener watches. A read-only dump probe (`research/defuser_probe.py`) found timer strings ending at `0.023`, `0.024`, `0.048`, `0.054`, `0.090`, and `0.092`, but no string beginning `0.00`. The current completion branch in `third_party/siege-dissect/dissect/defuse.go` requires `strings.HasPrefix(timer, "0.00")`; this explains why these near-zero timer packets produce no completion feedback. The tag is present, so the listener itself is not simply absent. No threshold or completion rule was changed: a near-zero timer alone has not yet been validated as a completed plant or disable across multiple rounds and builds.

## Packet and actor audit — four development maps

`research/objective_timer_audit.py` now records each physical round's defuser timer runs and nearby Y11 per-entity scoreboard changes. `research/defuser_identity_probe.go` extracts the raw player identity refs for that read-only join. All output stays under ignored `data/research/diagnostics/`. The four audited maps are June 25 North America Lair (SiegeGG 4150), July 2 North America Chalet (4132), April 25 Asia Pacific map three (3585), and August 15 EWC map one (6156). Their public round logs are used **only to validate** packet hypotheses.

| Map target | Public plants/disables | Complete timer runs seen | Incomplete near-zero examples | Actor finding |
| --- | ---: | --- | --- | --- |
| 4150 | 4/0 | Four plant rounds end at 0.023–0.054 seconds | One no-plant attempt stops at 0.429 | An attacker gets a nearby +100 score update in all four plant rounds; each matches the public actor. |
| 4132 | 4/1 | Plant/disable runs reach 0.000–0.026 | A no-plant run stops at 0.102 | Some nearby +100 updates match; the disable produces several team-wide +100 updates, so one bonus does not uniquely identify its actor. |
| 3585 | 4/1 | Runs reach 0.001–0.054 | No equally low no-plant run in this map | Nearby +100 updates sometimes name a different teammate than the public planter. |
| 6156 | 4/2 | Runs reach 0.011–0.074 | One no-plant attempt stops at 0.551 | Some plants have no nearby attributable +100 update; disable rounds have team-wide score changes. |

The old fixed-offset `readDefuserTimer` player ID is not a valid Y11 actor reference in the known June round: its four bytes do not match any of the ten `DissectID` values. The tag is a progress tick, not a player identity. A nearby +100 scoreboard change is useful evidence in some rounds, but is neither present nor unique for all plants and disables. This matches the limitations visible in [the upstream score-bonus approach](https://github.com/ImAAhmad/r6-dissect/blob/main/dissect/defuse.go); it is not sufficient for our parser to credit an objective.

A wider development-data audit exposed false positives in the previously derived normalized data: 38 resolved plants were credited to defenders, four more to players with nil profile IDs that also resolve to defenders by username, and all five emitted disables had a different actor than the public round log. These 47 events are **not trustworthy objective observations**. The Python adapter now rejects role-impossible completions and requires an explicit verified actor source for Y11 completion events. This is a conservative data-integrity safeguard; it does not recover the real plants/disables. The low-level parser must provide an independently verified replay-derived actor signal before these events can be counted or the fitted objective weight interpreted. Raw replay archives and cached public targets remain available for rederivation.
