# Combined guarded objective diagnostic: extension

Consumed development only; not independently validated or deployed. Exact modes in `objective_combined_candidate.py`. All candidates require a complete seven-second timer run, stable declared body identity and scoreboard identity, no unknown death offsets or PlayerLeave, and active state0/2 throughout interaction. Sole mode requires every other teammate killed before interaction plus state4 throughout. Standalone plant mode retains clock and kill/assist guards. Conflicts abstain; relative disable score never selects an actor alone.

Counts: `{'plant': {'correct': 25, 'unresolved': 7}, 'disable': {'unresolved': 9, 'correct': 3}}`. Resolved modes: `{'plant': {'standalone_clock_with_body_guard': 21, 'sole_proven_survivor_throughout_interaction': 2, 'score_and_sole_agree': 2}, 'disable': {'sole_proven_survivor_throughout_interaction': 3}}`.

| Match/game/round/kind | Candidate | Verdict | Mode / abstention |
| --- | --- | --- | --- |
| 3579/6706/R01/plant | SpeakEasy.WBG | correct | standalone_clock_with_body_guard |
| 3579/6706/R02/plant | Ape5G.WBG | correct | standalone_clock_with_body_guard |
| 3579/6706/R04/plant | Ape5G.WBG | correct | standalone_clock_with_body_guard |
| 3579/6706/R04/disable | unresolved | unresolved | no_unambiguous_guarded_mode |
| 3579/6707/R02/plant | Ape5G.WBG | correct | standalone_clock_with_body_guard |
| 3579/6707/R04/plant | Ape5G.WBG | correct | standalone_clock_with_body_guard |
| 3563/6673/R01/plant | Canadian | correct | standalone_clock_with_body_guard |
| 3563/6673/R03/plant | unresolved | unresolved | no_unambiguous_guarded_mode |
| 3563/6675/R02/plant | Surf | correct | sole_proven_survivor_throughout_interaction |
| 3563/6675/R02/disable | unresolved | unresolved | no_unambiguous_guarded_mode |
| 3563/6675/R10/plant | kyno | correct | standalone_clock_with_body_guard |
| 3563/6675/R10/disable | Spoit | correct | sole_proven_survivor_throughout_interaction |
| 3563/6676/R09/plant | unresolved | unresolved | no_unambiguous_guarded_mode |
| 4283/8685/R01/plant | RORICK.VP | correct | standalone_clock_with_body_guard |
| 4283/8685/R04/plant | p4sh4.VP | correct | standalone_clock_with_body_guard |
| 4283/8686/R01/plant | Yoggah.Geekay | correct | sole_proven_survivor_throughout_interaction |
| 4283/8686/R01/disable | unresolved | unresolved | no_unambiguous_guarded_mode |
| 4283/8686/R09/plant | unresolved | unresolved | no_unambiguous_guarded_mode |
| 4283/8686/R09/disable | unresolved | unresolved | no_unambiguous_guarded_mode |
| 4283/8686/R14/plant | AsK.Geekay | correct | standalone_clock_with_body_guard |
| 4283/8687/R05/plant | AsK.Geekay | correct | standalone_clock_with_body_guard |
| 4283/8687/R08/plant | SkyZs.VP | correct | standalone_clock_with_body_guard |
| 4283/8687/R08/disable | unresolved | unresolved | no_unambiguous_guarded_mode |
| 6157/10428/R03/plant | kds | correct | standalone_clock_with_body_guard |
| 6157/10428/R09/plant | unresolved | unresolved | no_unambiguous_guarded_mode |
| 6157/10428/R10/plant | VolpsZ | correct | standalone_clock_with_body_guard |
| 6157/10430/R01/plant | unresolved | unresolved | no_unambiguous_guarded_mode |
| 6157/10430/R07/plant | unresolved | unresolved | no_unambiguous_guarded_mode |
| 6157/10430/R07/disable | unresolved | unresolved | no_unambiguous_guarded_mode |
| 6157/10430/R10/plant | Dias | correct | standalone_clock_with_body_guard |
| 6157/10430/R12/plant | Bokzera | correct | score_and_sole_agree |
| 6157/10430/R12/disable | kds | correct | sole_proven_survivor_throughout_interaction |
| 6158/10563/R04/plant | Skeptic.TH | correct | standalone_clock_with_body_guard |
| 6158/10563/R05/plant | Skeptic.TH | correct | standalone_clock_with_body_guard |
| 6158/10563/R05/disable | unresolved | unresolved | no_unambiguous_guarded_mode |
| 6158/10563/R06/plant | Zaara.TH | correct | score_and_sole_agree |
| 6158/10563/R06/disable | SkyZs.VP | correct | sole_proven_survivor_throughout_interaction |
| 6158/10563/R07/plant | Nayqo.VP | correct | standalone_clock_with_body_guard |
| 6277/10576/R01/plant | Skeptic.TH | correct | standalone_clock_with_body_guard |
| 6277/10576/R01/disable | unresolved | unresolved | no_unambiguous_guarded_mode |
| 6277/10576/R06/plant | unresolved | unresolved | no_unambiguous_guarded_mode |
| 6277/10576/R06/disable | unresolved | unresolved | no_unambiguous_guarded_mode |
| 6277/10576/R11/plant | Creedz.SECRET | correct | standalone_clock_with_body_guard |
| 6277/10576/R12/plant | Hungry.SECRET | correct | standalone_clock_with_body_guard |
| 4139/None/R07/plant | unresolved | unresolved | no_unambiguous_guarded_mode |

State2 is independently seen on active players, so it is not excluded as DBNO. State3/unknown never establishes eligibility or teammate death. Fresh reserve remains sealed until specification, consumed results, targeted tests and a clean local freeze commit.
