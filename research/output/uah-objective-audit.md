# UAH objective occurrence audit - read-only

Occurrence parser; no historical corrections applied. All new actors remain unresolved.
Stored actor side/operator are historical context, not evidence of newly resolved credit.

| Map / ID | Round | Kind | Stored actor (side; operator) | New occurrence | New actor | Evidence / discrepancy |
| --- | ---: | --- | --- | --- | --- | --- |
| Fortress / d64d5478cdb3 | 7 | plant | Kenbot.USU (Defense; Operator(456757346397)) | yes | unresolved | defuser_state_v1; historical actor remains unverified |
| Fortress / d64d5478cdb3 | 8 | plant | Kenbot.USU (Defense; Operator(456757346397)) | yes | unresolved | defuser_state_v1; historical actor remains unverified |
| Border / 8a6357ff307c | 5 | plant | Lxgacy.MAV (Defense; Ela) | yes | unresolved | defuser_state_v1; historical actor remains unverified |
| Border / 8a6357ff307c | 6 | disable | Lxgacy.MAV (Defense; Thorn) | unresolved / absent | unresolved | No supported occurrence; historical credit disagrees |
| Border / 8a6357ff307c | 6 | plant | Lxgacy.MAV (Defense; Thorn) | yes | unresolved | defuser_state_v1; historical actor remains unverified |
| Border / 8a6357ff307c | 7 | plant | Tallman3.14 (Defense; Mute) | yes | unresolved | defuser_state_v1; historical actor remains unverified |
| Border / 8a6357ff307c | 11 | plant | Tallman3.14 (Defense; Smoke) | yes | unresolved | defuser_state_v1; historical actor remains unverified |
| Border / 8a6357ff307c | 12 | plant | Tallman3.14 (Defense; Smoke) | yes | unresolved | defuser_state_v1; historical actor remains unverified |
| Kafe Dostoyevsky / 5adc26f7a402 | 1 | plant | Kenbot.USU (Defense; Maestro) | yes | unresolved | defuser_state_v1; historical actor remains unverified |
| Kafe Dostoyevsky / 5adc26f7a402 | 2 | plant | Kenbot.USU (Defense; Mute) | yes | unresolved | defuser_state_v1; historical actor remains unverified |
| Kafe Dostoyevsky / 5adc26f7a402 | 9 | plant | Tallman3.14 (Defense; Pulse) | yes | unresolved | defuser_state_v1; historical actor remains unverified |
| Kafe Dostoyevsky / 5adc26f7a402 | 11 | plant | Tallman3.14 (Defense; Goyo) | yes | unresolved | defuser_state_v1; historical actor remains unverified |
| Kafe Dostoyevsky / 5adc26f7a402 | 14 | plant | Kenbot.USU (Defense; Solis) | yes | unresolved | defuser_state_v1; historical actor remains unverified |
| Border / 076d2b6b02bc | 2 | disable | none | yes | unresolved | defuser_state_and_defense_win_v1 |
| Border / 076d2b6b02bc | 2 | plant | none | yes | unresolved | defuser_state_v1 |
| Border / 076d2b6b02bc | 6 | disable | none | yes | unresolved | defuser_state_and_defense_win_v1 |
| Border / 076d2b6b02bc | 6 | plant | none | yes | unresolved | defuser_state_v1 |
| Border / 076d2b6b02bc | 8 | disable | none | yes | unresolved | defuser_state_and_defense_win_v1 |
| Border / 076d2b6b02bc | 8 | plant | none | yes | unresolved | defuser_state_v1 |
| Chalet / b595ffaaec57 | 5 | plant | none | yes | unresolved | defuser_state_v1 |
| Chalet / b595ffaaec57 | 10 | plant | none | yes | unresolved | defuser_state_v1 |

Maps: 5. Rounds: 62. Detected plants: 17; disables: 3. Resolved actors: 0.
Checked 616 player-round identity/side/operator tuples. All 310 tracked player-rounds / 102 tracked operator usage groups match stored data. SQLite SHA-256 unchanged.

Occurrence does not establish who acted. The known personal disable remains unattributed; no player is selected from recollection. Historical changes require review.

## Pre-existing operator differences

Kafe Dostoyevsky / 5adc26f7a402 R08: stored [('hidebuff.USU', 'Attack', 'Unknown')], pre-objective baseline and occurrence parser [('hidebuff.USU', 'Attack', 'Solid Snake')]
