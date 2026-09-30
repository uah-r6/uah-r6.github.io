# Objective coverage diagnostic — development events only

This check uses the 266 clean player-map rows from the seven pre-August training events and the 32 previously viewed August EWC development rows. Both September events are excluded. It compares player-map public objective counts to the tracker counts derived from siege-dissect `matchFeedback` completion events; it does not compare Rating values or alter the tracker.

| Development group | Clean player-map rows | Public plants | Replay plants | Public disables | Replay disables |
| --- | ---: | ---: | ---: | ---: | ---: |
| Seven pre-August training events | 266 | 55 | 23 | 7 | 1 |
| August EWC validation | 32 | 11 | 1 | 4 | 0 |

The difference is not only player attribution. In the June 25 North America Stage 1 100 Thieves–Five Fears Lair map (SiegeGG match 4150), the public game target records four plants across its ten players. The complete 11-round replay parses with 78 `Kill` feedback entries and **no plant or disable feedback entries**. Its normalized map therefore records zero plants. The raw siege-dissect JSON used for this check is cached under ignored `data/research/diagnostics/nal-stage1-100t-five-fears-lair-raw.json`.

This shows that the present objective feature is incomplete relative to the public target in this sample. It does not establish which underlying replay packets or SiegeGG definitions account for each difference. The expanded fit's nearly zero objective weight is therefore weak evidence about any true objective contribution. Do not infer missing plants from round wins or silently replace replay values with public target counts; investigate the underlying events and definitions on development replays first. KOST and the live `collegiate_v1` formula were not changed.

The same June replay does contain 1,297 copies of the packet tag that siege-dissect's `readDefuserTimer` listener watches. A read-only dump probe (`research/defuser_probe.py`) found timer strings ending at `0.023`, `0.024`, `0.048`, `0.054`, `0.090`, and `0.092`, but no string beginning `0.00`. The current completion branch in `third_party/siege-dissect/dissect/defuse.go` requires `strings.HasPrefix(timer, "0.00")`; this explains why these near-zero timer packets produce no completion feedback. The tag is present, so the listener itself is not simply absent. No threshold or completion rule was changed: a near-zero timer alone has not yet been validated as a completed plant or disable across multiple rounds and builds.
