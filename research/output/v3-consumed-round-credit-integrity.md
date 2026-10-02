# Consumed SAL round-credit integrity: exact map K/D is insufficient

Completed cached direct-UID scoreboard evidence is compared with the already-frozen accepted opponent finishes. No replay parsing, model fitting, numerical target grading or eligibility change occurs. All 20 prediction/quality/API/stat digests are checked against the prospective seal. Both permanent failed finals and all 86 live file hashes are checked.

Coverage and discrepancies: `{'maps': 20, 'rounds': 207, 'player_maps': 200, 'player_round_differences': 52, 'rounds_with_differences': 26, 'player_map_patterns': 46, 'map_total_differences': 43, 'eligible_player_map_patterns': 3, 'eligible_player_round_differences': 6}`.

All 200 scoreboard credited-kill totals match independent official and original public totals. Three previously eligible player-map rows contain offsetting per-round differences, so exact map K/D does not validate their round-level credited-kill pattern. This is a limitation of the frozen studies, not a revised final result or proof of a particular Rating error.

| Official / player | Credited map kills | Opponent finishes | Offsetting round evidence |
| --- | ---: | ---: | --- |
| 8580/Kheyze.TLAW | 13 | 13 | R06: credit 1, finishes 0; R13: credit 0, finishes 1 |
| 8591/Bokzera.FURIA | 11 | 11 | R04: credit 1, finishes 0; R05: credit 2, finishes 3 |
| 8594/vitaking.FaZe | 10 | 10 | R05: credit 1, finishes 2; R10: credit 3, finishes 2 |

## Raw-feed negative control

Raw Kill packets versus accepted opponent finishes: `[{'official_match_id': 8596, 'round': 10, 'player': 'mitrix.IMP', 'credited': 0, 'opponent_finishes': 0, 'raw_kill_packets': 1, 'frozen_eligible': True}]`. The single mitrix-to-Legacy packet in 8596/R10 is a teamkill, already excluded correctly. It is separate from the 52 credited-opponent-kill differences; the original raw audit is retained.

The independent [Y11 broadcast review](v3-consumed-dbno-vod-review.md) establishes one credited-kill versus displayed-finisher split, without claiming the downing shot is visible. The full [direct-UID counter ledger](v3-consumed-sal-kill-credit.md) records all rounds and rehost continuity.

A future explicit credited-kill design must preserve displayed finisher and death timing separately, require event/victim identity and DBNO/revive evidence, and validate on development data before any new prospective final. Never assign a victim by nearest counter update or public expected total. No runtime kill/operator/action boundary or objective changes are authorized by this diagnostic.

Live v2 remains unchanged. Both v3 final failures, original actor comparisons, all frozen dependencies, SQLite, private archives and public JSON are preserved. No publish or push.
