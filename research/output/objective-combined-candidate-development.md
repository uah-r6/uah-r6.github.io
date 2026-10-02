# Combined guarded objective diagnostic: development

Consumed development only; not independently validated or deployed. Exact modes in `objective_combined_candidate.py`. All candidates require a complete seven-second timer run, stable declared body identity and scoreboard identity, no unknown death offsets or PlayerLeave, and active state0/2 throughout interaction. Sole mode requires every other teammate killed before interaction plus state4 throughout. Standalone plant mode retains clock and kill/assist guards. Conflicts abstain; relative disable score never selects an actor alone.

Counts: `{'plant': {'correct': 39, 'unresolved': 22}, 'disable': {'unresolved': 7, 'correct': 1}}`. Resolved modes: `{'plant': {'standalone_clock_with_body_guard': 37, 'sole_proven_survivor_throughout_interaction': 1, 'score_and_sole_agree': 1}, 'disable': {'sole_proven_survivor_throughout_interaction': 1}}`.

| Match/game/round/kind | Candidate | Verdict | Mode / abstention |
| --- | --- | --- | --- |
| 4150/None/R03/plant | Forrest.5F | correct | standalone_clock_with_body_guard |
| 4150/None/R07/plant | Hotancold.100T | correct | standalone_clock_with_body_guard |
| 4150/None/R09/plant | unresolved | unresolved | no_unambiguous_guarded_mode |
| 4150/None/R11/plant | Hotancold.100T | correct | standalone_clock_with_body_guard |
| 4132/None/R05/plant | JJBlaztful.5F | correct | standalone_clock_with_body_guard |
| 4132/None/R10/plant | unresolved | unresolved | no_unambiguous_guarded_mode |
| 4132/None/R10/disable | unresolved | unresolved | no_unambiguous_guarded_mode |
| 4132/None/R13/plant | Fenz.5F | correct | standalone_clock_with_body_guard |
| 4132/None/R15/plant | unresolved | unresolved | no_unambiguous_guarded_mode |
| 3585/None/R04/plant | unresolved | unresolved | no_unambiguous_guarded_mode |
| 3585/None/R06/plant | unresolved | unresolved | no_unambiguous_guarded_mode |
| 3585/None/R07/plant | unresolved | unresolved | no_unambiguous_guarded_mode |
| 3585/None/R07/disable | unresolved | unresolved | no_unambiguous_guarded_mode |
| 3585/None/R08/plant | Lycolis.ORC | correct | standalone_clock_with_body_guard |
| 6156/None/R01/plant | kyno | correct | standalone_clock_with_body_guard |
| 6156/None/R05/plant | unresolved | unresolved | no_unambiguous_guarded_mode |
| 6156/None/R07/plant | unresolved | unresolved | no_unambiguous_guarded_mode |
| 6156/None/R07/disable | unresolved | unresolved | no_unambiguous_guarded_mode |
| 6156/None/R10/plant | Yoggah | correct | standalone_clock_with_body_guard |
| 6156/None/R10/disable | unresolved | unresolved | no_unambiguous_guarded_mode |
| 3073/None/R03/plant | unresolved | unresolved | incomplete_score_identity |
| 3073/None/R08/plant | unresolved | unresolved | incomplete_score_identity |
| 3554/None/R05/plant | kyno | correct | standalone_clock_with_body_guard |
| 3554/None/R09/plant | unresolved | unresolved | no_unambiguous_guarded_mode |
| 4112/None/R01/plant | unresolved | unresolved | no_unambiguous_guarded_mode |
| 4112/None/R03/plant | unresolved | unresolved | no_unambiguous_guarded_mode |
| 4112/None/R04/plant | R4re.BD | correct | standalone_clock_with_body_guard |
| 4112/None/R07/plant | Gabu7z.LOUD | correct | standalone_clock_with_body_guard |
| 4112/None/R09/plant | live.LOUD | correct | standalone_clock_with_body_guard |
| 4112/None/R11/plant | live.LOUD | correct | standalone_clock_with_body_guard |
| 4112/None/R12/plant | live.LOUD | correct | standalone_clock_with_body_guard |
| 3637/None/R02/plant | unresolved | unresolved | no_unambiguous_guarded_mode |
| 3637/None/R10/plant | Alem4o.G2 | correct | standalone_clock_with_body_guard |
| 4140/None/R11/plant | Rexen.SR | correct | standalone_clock_with_body_guard |
| 4118/None/R03/plant | Handyy.FaZe | correct | standalone_clock_with_body_guard |
| 4118/None/R07/plant | live.LOUD | correct | standalone_clock_with_body_guard |
| 4141/None/R10/plant | Beeno.4FUN | correct | standalone_clock_with_body_guard |
| 4134/None/R04/plant | Canadian.SR | correct | standalone_clock_with_body_guard |
| 4134/None/R08/plant | Dream.SSG | correct | standalone_clock_with_body_guard |
| 4148/None/R03/plant | unresolved | unresolved | no_unambiguous_guarded_mode |
| 4139/None/R04/plant | Hotancold.100T | correct | standalone_clock_with_body_guard |
| 4139/None/R07/plant | unresolved | unresolved | no_unambiguous_guarded_mode |
| 3639/None/R03/plant | Flexy.SECRET | correct | sole_proven_survivor_throughout_interaction |
| 3639/None/R03/disable | Lollo.HERETICS | correct | sole_proven_survivor_throughout_interaction |
| 3639/None/R05/plant | noa.SECRET | correct | standalone_clock_with_body_guard |
| 3639/None/R06/plant | Mowwwgli.SECRET | correct | standalone_clock_with_body_guard |
| 3639/None/R07/plant | AquiX.HERETICS | correct | standalone_clock_with_body_guard |
| 4127/None/R01/plant | Gunnar.M80 | correct | standalone_clock_with_body_guard |
| 4127/None/R04/plant | Ashn.M80 | correct | standalone_clock_with_body_guard |
| 4127/None/R05/plant | Savage.M80 | correct | standalone_clock_with_body_guard |
| 4137/None/R10/plant | Spiker.WC | correct | standalone_clock_with_body_guard |
| 4137/None/R15/plant | Spiker.WC | correct | standalone_clock_with_body_guard |
| 4138/None/R04/plant | Ewzy.C9 | correct | standalone_clock_with_body_guard |
| 4119/None/R03/plant | R4re.BD | correct | standalone_clock_with_body_guard |
| 4120/None/R08/plant | unresolved | unresolved | no_unambiguous_guarded_mode |
| 4120/None/R09/plant | dotz.FX | correct | standalone_clock_with_body_guard |
| 4133/None/R03/plant | J9O.DZ | correct | score_and_sole_agree |
| 4133/None/R03/disable | unresolved | unresolved | no_unambiguous_guarded_mode |
| 4133/None/R07/plant | unresolved | unresolved | unknown_death_offset |
| 3880/None/R02/plant | unresolved | unresolved | no_unambiguous_guarded_mode |
| 3880/None/R04/plant | unresolved | unresolved | no_unambiguous_guarded_mode |
| 3880/None/R06/plant | SpeakEasy.WBG | correct | standalone_clock_with_body_guard |
| 3880/None/R09/plant | Pikanzu.Daystar | correct | standalone_clock_with_body_guard |
| 3880/None/R10/plant | unresolved | unresolved | no_unambiguous_guarded_mode |
| 3880/None/R10/disable | unresolved | unresolved | no_unambiguous_guarded_mode |
| 3879/None/R03/plant | JoeGoR.KZ | correct | standalone_clock_with_body_guard |
| 3879/None/R12/plant | MARKELELE.SH | correct | standalone_clock_with_body_guard |
| 3879/None/R13/plant | unresolved | unresolved | no_unambiguous_guarded_mode |
| 3073/None/R08/disable | unresolved | unresolved | missing_completion_anchor |

State2 is independently seen on active players, so it is not excluded as DBNO. State3/unknown never establishes eligibility or teammate death. Fresh reserve remains sealed until specification, consumed results, targeted tests and a clean local freeze commit.
