# Independent consumed APAC actor and K/D review

No frozen model, actor rule, eligibility, predictions, target or final result is changed. Replay proposals were fixed before these primary and public actor fields were projected.

Totals: `{'maps': 12, 'rounds': 118, 'primary_reviewed_maps': 9, 'primary_reviewed_rounds': 92, 'plant': 25, 'resolved_plant': 25, 'primary_identity_unresolved_maps': 3, 'disable': 3, 'resolved_disable': 3}`. Original lower-confidence actor comparison: `{('plant', 'agreement'): 25, ('disable', 'agreement'): 3}`. Separate independently constrained actor comparison: `{('plant', 'agreement'): 9, ('disable', 'agreement'): 3}`. K/D consistency: `{'official_public_agreement': 90, 'all_three_agree': 68}`.

| Official / map | Replay occurrence / actor resolution | Aggregate conflicts | Independent round constraints |
| --- | --- | --- | --- |
| [8154](https://www.ubisoft.com/en-us/esports/rainbow-six/siege/match/8154)/Clubhouse | {} | [] |  |
| [8155](https://www.ubisoft.com/en-us/esports/rainbow-six/siege/match/8155)/Fortress | {'plant': 3, 'resolved_plant': 3} | [] | R09 plant: Eclair / agreement |
| [8156](https://www.ubisoft.com/en-us/esports/rainbow-six/siege/match/8156)/Nighthaven Labs | {'plant': 3, 'resolved_plant': 3} | [] | R05 plant: Akusu / agreement |
| [8157](https://www.ubisoft.com/en-us/esports/rainbow-six/siege/match/8157)/Clubhouse | {'primary_identity_unresolved_maps': 1} | Unavailable: primary identity unresolved |  |
| [8158](https://www.ubisoft.com/en-us/esports/rainbow-six/siege/match/8158)/Clubhouse | {'plant': 5, 'resolved_plant': 5, 'disable': 1, 'resolved_disable': 1} | [] | R04 disable: AsveL / agreement; R03 plant: Yurivst / agreement; R04 plant: Yurivst / agreement; R06 plant: Yurivst / agreement |
| [8159](https://www.ubisoft.com/en-us/esports/rainbow-six/siege/match/8159)/Villa | {'primary_identity_unresolved_maps': 1} | Unavailable: primary identity unresolved |  |
| [8160](https://www.ubisoft.com/en-us/esports/rainbow-six/siege/match/8160)/Clubhouse | {'plant': 1, 'resolved_plant': 1} | [] | R05 plant: Anitun / agreement |
| [8161](https://www.ubisoft.com/en-us/esports/rainbow-six/siege/match/8161)/Clubhouse | {'plant': 4, 'resolved_plant': 4, 'disable': 2, 'resolved_disable': 2} | [] | R14 disable: FishLike / agreement; R10 disable: Aokayu / agreement; R14 plant: Aokayu / agreement |
| [8162](https://www.ubisoft.com/en-us/esports/rainbow-six/siege/match/8162)/Clubhouse | {'plant': 5, 'resolved_plant': 5} | [] | R01 plant: Novashatol / agreement |
| [8163](https://www.ubisoft.com/en-us/esports/rainbow-six/siege/match/8163)/Chalet | {'primary_identity_unresolved_maps': 1} | Unavailable: primary identity unresolved |  |
| [8164](https://www.ubisoft.com/en-us/esports/rainbow-six/siege/match/8164)/Chalet | {'plant': 3, 'resolved_plant': 3} | [] |  |
| [8165](https://www.ubisoft.com/en-us/esports/rainbow-six/siege/match/8165)/Bank | {'plant': 1, 'resolved_plant': 1} | [] | R02 plant: Woogiman / agreement |

## Explicit primary identity exclusions

- 8157: [{'player': 'munu74.TMT', 'profile_id': '81c2f901-84a7-4435-8e5f-4b121946d352', 'identity_spellings': ['', 'munu74'], 'candidates': [], 'reason': 'No unique explicit primary identity; no spelling guess'}].
- 8159: [{'player': 'munu74.TMT', 'profile_id': '81c2f901-84a7-4435-8e5f-4b121946d352', 'identity_spellings': ['', 'munu74'], 'candidates': [], 'reason': 'No unique explicit primary identity; no spelling guess'}].
- 8163: [{'player': 'munu74.TMT', 'profile_id': '81c2f901-84a7-4435-8e5f-4b121946d352', 'identity_spellings': ['', 'munu74'], 'candidates': [], 'reason': 'No unique explicit primary identity; no spelling guess'}].

The earlier strict three-map review and exact source are preserved in the ignored `consumed-primary-review/initial-strict-audit` cache. This revision proceeds past identity-blocked maps by reporting them as unavailable; it retains the original complete unique ten-player guard. No primary actor/KD verdict is assigned on those maps and no frozen alias is changed.


Original public disagreements/unresolved actors:


Unique official team objective totals plus independently verified occurrence/side constrain an actor; these are explicit inferences, not direct round actor fields or visual verification. Multiple-player totals cannot assign individual rounds. Missing replay body/UID evidence remains unresolved even when an official total constrains a name. No actor is filled from a remaining external count.

Independent official/public K/D agreement does not establish each round-level credited-kill pattern. The separate stable-UID counter audit investigates that limitation without changing original quality decisions. Official/public telemetry may share upstream data; broadcast evidence is separately identified.

Both permanent failed v3 finals, live v2, all 86 protected hashes and both source freezes remain unchanged. No import, historical correction, public regeneration, push, publish or deployment.
