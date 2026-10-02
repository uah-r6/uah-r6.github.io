# UAH completing-owner proposals: read-only

Maps5, counts`{'rounds': 62, 'plant': 17, 'plant_resolved': 15, 'plant_unresolved': 2, 'disable': 3, 'disable_resolved': 3}`. Gameplay parity failures`[]`. SQLite opened mode=ro; every source archive file hash verified against its manifest. Old stored actors are comparison context, not target labels. Proposed corrections are not applied.

| Map/ID | Round | Kind | Completing owner | Evidence / unresolved reason | Prior stored actor | Proposed correction |
| --- | ---: | --- | --- | --- | --- | --- |
| Fortress/d64d5478cdb3 | 7 | plant | Lgon. | completing_timer_owner_v1 | Kenbot.USU(Defense) | Lgon. |
| Fortress/d64d5478cdb3 | 8 | plant | Tallman3.14 | completing_timer_owner_v1 | Kenbot.USU(Defense) | Tallman3.14 |
| Border/8a6357ff307c | 5 | plant | DinoFireKing | completing_timer_owner_v1 | Lxgacy.MAV(Defense) | DinoFireKing |
| Border/8a6357ff307c | 6 | plant | AzoozNewzz | completing_timer_owner_v1 | Lxgacy.MAV(Defense) | AzoozNewzz |
| Border/8a6357ff307c | 7 | plant | ExtremeHorizon9 | completing_timer_owner_v1 | Tallman3.14(Defense) | ExtremeHorizon9 |
| Border/8a6357ff307c | 11 | plant | Lxgacy.MAV | completing_timer_owner_v1 | Tallman3.14(Defense) | Lxgacy.MAV |
| Border/8a6357ff307c | 12 | plant | ExtremeHorizon9 | completing_timer_owner_v1 | Tallman3.14(Defense) | ExtremeHorizon9 |
| Kafe Dostoyevsky/5adc26f7a402 | 1 | plant | DinoFireKing | completing_timer_owner_v1 | Kenbot.USU(Defense) | DinoFireKing |
| Kafe Dostoyevsky/5adc26f7a402 | 2 | plant | Tallman3.14 | completing_timer_owner_v1 | Kenbot.USU(Defense) | Tallman3.14 |
| Kafe Dostoyevsky/5adc26f7a402 | 9 | plant | unresolved | timer_owner_body_unresolved | Tallman3.14(Defense) | none |
| Kafe Dostoyevsky/5adc26f7a402 | 11 | plant | MaliKitE.USU | completing_timer_owner_v1 | Tallman3.14(Defense) | MaliKitE.USU |
| Kafe Dostoyevsky/5adc26f7a402 | 14 | plant | Tallman3.14 | completing_timer_owner_v1 | Kenbot.USU(Defense) | Tallman3.14 |
| Border/076d2b6b02bc | 2 | plant | Tallman3.14 | completing_timer_owner_v1 | none | Tallman3.14 |
| Border/076d2b6b02bc | 2 | disable | briancatM.UMich | completing_timer_owner_v1 | none | briancatM.UMich |
| Border/076d2b6b02bc | 6 | plant | AzoozNewzz | completing_timer_owner_v1 | none | AzoozNewzz |
| Border/076d2b6b02bc | 6 | disable | ormeek.UMich | completing_timer_owner_v1 | none | ormeek.UMich |
| Border/076d2b6b02bc | 8 | plant | getSpoopd | completing_timer_owner_v1 | none | getSpoopd |
| Border/076d2b6b02bc | 8 | disable | Lgon. | completing_timer_owner_v1 | none | Lgon. |
| Chalet/b595ffaaec57 | 5 | plant | Lgon. | completing_timer_owner_v1 | none | Lgon. |
| Chalet/b595ffaaec57 | 10 | plant | unresolved | incomplete_unique_roster_or_roles | none | none |

## Tracked proposals, not applied

| Player | Kind | Count |
| --- | --- | ---: |
| AzoozNewzz | plant | 2 |
| DinoFireKing | plant | 2 |
| Lgon | disable | 1 |
| Lgon | plant | 2 |
| Tallman3.14 | plant | 4 |

Lgon Attack original38rounds: `{'Striker': 4, 'Ace': 2, 'Sens': 1, 'Grim': 2, 'Gridlock': 3, 'Zofia': 4, 'Twitch': 1, 'Deimos': 1}`. All archived rounds: `{'Striker': 5, 'Ace': 4, 'Sens': 1, 'Grim': 4, 'Gridlock': 4, 'Zofia': 6, 'Twitch': 1, 'Deimos': 3, 'Capitao': 1, 'Thatcher': 1}`. Every parsed player/operator/kill/death/winner/site/physical-score field matches the previous binary. Completion clocks are not invented: new normalized credits carry0.0 as unknown timing; statistics use round/actor counts. Structural confidence means all replay guards pass, not externally labeled UAH accuracy. Unsupported/missing identity remains unresolved.

86 database/archive/public file hashes unchanged; SQLite SHA256`f3dc10210ab29f62e83317600e8bfcd55b1e6f17c6dbcaf0abf4556af55bef4e`. No recalculation, import, archive mutation, website JSON regeneration, Rating change or publish.

Reproduce `.venv/Scripts/python.exe research/uah_completer_readonly.py`. Separate actor candidate binary is used explicitly; this script does not install it or alter configured live paths.
