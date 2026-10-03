# Exact native feedback-envelope recovery: consumed APAC8156

{'rounds': 10, 'complete_native_rounds': 10, 'uah_first_round_parity_controls': 5, 'actual_reader_header_operator_parity': 10, 'actual_reader_raw_feedback_parity': 10, 'complete_original_rounds': 9, 'recovered_death_envelopes': 1, 'official_matches': 10, 'official_mismatches': 0, 'public_matches': 10, 'official_death_matches': 10}

The existing readMatchFeedback empty-killer branch emits a Death without setting its private killOffset. The separate observer wraps that existing callback once, records its exact marker/entry/end and the index of its single emitted event. It does not duplicate low-level replay parsing or match by proximity. Existing MatchFeedback and the original v1 refusal are preserved.

Jin.RRX/R03 has original offset0 and exact native envelope41873708..41873781, legacy clock1:11. This boundary now permits the unchanged pre-action/pre-death baseline validator to verify all ten rounds in this isolated map. Unknown, duplicate, bad-marker, ambiguous and late-baseline evidence still refuses. It does not assign a credited victim or infer whether this Death was suicide/teamkill/other cause.

| Player | Native credited kills | Official / public | Victim deaths / official |
| --- | ---: | --- | --- |
| mity.DK | 6 | 6 / 6 | 5 / 5 |
| Levy.DK | 12 | 12 / 12 | 6 / 6 |
| Faallz.DK | 5 | 5 / 5 | 4 / 4 |
| YURI.DK | 5 | 5 / 5 | 7 / 7 |
| ionzera.DK | 11 | 11 / 11 | 7 / 7 |
| Jin.RRX | 7 | 7 / 7 | 9 / 9 |
| Yuyu.RRX | 4 | 4 / 4 | 7 / 7 |
| KoroMomoZ.RRX | 1 | 1 / 1 | 9 / 9 |
| Maou.RRX | 7 | 7 / 7 | 8 / 8 |
| akusu.RRX | 10 | 10 / 10 | 7 / 7 |

The eeca495 study remains31complete maps/280official matches/40unavailable at its sealed hash. These ten additional consumed agreements are a separate structural improvement, not a retroactive regrade of that study or either failed v3 final. No live source migration, SQLite/public write, actor promotion, operator/action-start change or Rating recomputation.

Exact decoder invocation supplies an envelope byte boundary, not a precise event time, cause of Death, killer or downer. Default v1 source and all baseline guards unchanged. Native source is not accepted by current Python map validator; explicit integration/verification needed before any promotion.
