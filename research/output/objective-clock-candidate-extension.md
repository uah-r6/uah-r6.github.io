# Standalone score / clock interval development experiment

Consumed cases only. Unfrozen hypothesis; no production actor credit. See source function for exact logic. A candidate needs one +100 eligible score change before the first score tick ends, with that tick at completion or immediately next. Kill/death or positive kill/assist counter inside the interval vetoes the candidate. Unknown death offsets abstain. Disables are not selected by this plant-only mode.

Extension counts: `{"plant": {"correct": 23, "unresolved": 9}, "disable": {"unresolved": 12}}`.

| Match/game/round/kind | Candidate | Verdict | Reason | Clock interval |
| --- | --- | --- | --- | --- |
| 3579/6706/R01/plant | SpeakEasy.WBG | correct | standalone_clock_interval | {'start': 69401653, 'end': 69404407, 'state_tick': 44, 'score_tick': 44} |
| 3579/6706/R02/plant | Ape5G.WBG | correct | standalone_clock_interval | {'start': 60968344, 'end': 60971949, 'state_tick': 44, 'score_tick': 44} |
| 3579/6706/R04/plant | Ape5G.WBG | correct | standalone_clock_interval | {'start': 75962724, 'end': 75966491, 'state_tick': 44, 'score_tick': 44} |
| 3579/6706/R04/disable | unresolved | unresolved | disable_not_supported | {} |
| 3579/6707/R02/plant | Ape5G.WBG | correct | standalone_clock_interval | {'start': 68395902, 'end': 68399577, 'state_tick': 44, 'score_tick': 44} |
| 3579/6707/R04/plant | Ape5G.WBG | correct | standalone_clock_interval | {'start': 48977195, 'end': 48981946, 'state_tick': 44, 'score_tick': 44} |
| 3563/6673/R01/plant | Canadian | correct | standalone_clock_interval | {'start': 68420621, 'end': 68425602, 'state_tick': 44, 'score_tick': 44} |
| 3563/6673/R03/plant | unresolved | unresolved | not_single_standalone_increment | {'start': 63947514, 'end': 63951183, 'state_tick': 44, 'score_tick': 44} |
| 3563/6675/R02/plant | unresolved | unresolved | kill_or_death_in_interval | {'start': 57656460, 'end': 57660835, 'state_tick': 44, 'score_tick': 44} |
| 3563/6675/R02/disable | unresolved | unresolved | disable_not_supported | {} |
| 3563/6675/R10/plant | kyno | correct | standalone_clock_interval | {'start': 66011063, 'end': 66014488, 'state_tick': 44, 'score_tick': 44} |
| 3563/6675/R10/disable | unresolved | unresolved | disable_not_supported | {} |
| 3563/6676/R09/plant | unresolved | unresolved | kill_or_death_in_interval | {'start': 62264903, 'end': 62269501, 'state_tick': 44, 'score_tick': 44} |
| 4283/8685/R01/plant | RORICK.VP | correct | standalone_clock_interval | {'start': 69314759, 'end': 69317267, 'state_tick': 44, 'score_tick': 44} |
| 4283/8685/R04/plant | p4sh4.VP | correct | standalone_clock_interval | {'start': 88347422, 'end': 88352464, 'state_tick': 44, 'score_tick': 44} |
| 4283/8686/R01/plant | unresolved | unresolved | kill_or_death_in_interval | {'start': 74452896, 'end': 74456820, 'state_tick': 44, 'score_tick': 44} |
| 4283/8686/R01/disable | unresolved | unresolved | disable_not_supported | {} |
| 4283/8686/R09/plant | unresolved | unresolved | kill_or_death_in_interval | {'start': 82447087, 'end': 82452323, 'state_tick': 44, 'score_tick': 44} |
| 4283/8686/R09/disable | unresolved | unresolved | disable_not_supported | {} |
| 4283/8686/R14/plant | AsK.Geekay | correct | standalone_clock_interval | {'start': 77871608, 'end': 77876278, 'state_tick': 44, 'score_tick': 44} |
| 4283/8687/R05/plant | AsK.Geekay | correct | standalone_clock_interval | {'start': 66860485, 'end': 66863026, 'state_tick': 44, 'score_tick': 44} |
| 4283/8687/R08/plant | SkyZs.VP | correct | standalone_clock_interval | {'start': 78322337, 'end': 78326919, 'state_tick': 44, 'score_tick': 44} |
| 4283/8687/R08/disable | unresolved | unresolved | disable_not_supported | {} |
| 6157/10428/R03/plant | kds | correct | standalone_clock_interval | {'start': 60679781, 'end': 60681442, 'state_tick': 44, 'score_tick': 44} |
| 6157/10428/R09/plant | unresolved | unresolved | kill_or_death_in_interval | {'start': 70089801, 'end': 70094872, 'state_tick': 44, 'score_tick': 44} |
| 6157/10428/R10/plant | VolpsZ | correct | standalone_clock_interval | {'start': 59513970, 'end': 59518306, 'state_tick': 44, 'score_tick': 44} |
| 6157/10430/R01/plant | unresolved | unresolved | kill_or_death_in_interval | {'start': 84809219, 'end': 84815115, 'state_tick': 44, 'score_tick': 44} |
| 6157/10430/R07/plant | unresolved | unresolved | kill_or_death_in_interval | {'start': 76086282, 'end': 76091895, 'state_tick': 44, 'score_tick': 44} |
| 6157/10430/R07/disable | unresolved | unresolved | disable_not_supported | {} |
| 6157/10430/R10/plant | Dias | correct | standalone_clock_interval | {'start': 63478194, 'end': 63481846, 'state_tick': 44, 'score_tick': 44} |
| 6157/10430/R12/plant | Bokzera | correct | standalone_clock_interval | {'start': 65456233, 'end': 65459285, 'state_tick': 44, 'score_tick': 44} |
| 6157/10430/R12/disable | unresolved | unresolved | disable_not_supported | {} |
| 6158/10563/R04/plant | Skeptic.TH | correct | standalone_clock_interval | {'start': 37982265, 'end': 37985906, 'state_tick': 44, 'score_tick': 44} |
| 6158/10563/R05/plant | Skeptic.TH | correct | standalone_clock_interval | {'start': 42902923, 'end': 42907856, 'state_tick': 44, 'score_tick': 44} |
| 6158/10563/R05/disable | unresolved | unresolved | disable_not_supported | {} |
| 6158/10563/R06/plant | Zaara.TH | correct | standalone_clock_interval | {'start': 61435384, 'end': 61439388, 'state_tick': 44, 'score_tick': 44} |
| 6158/10563/R06/disable | unresolved | unresolved | disable_not_supported | {} |
| 6158/10563/R07/plant | Nayqo.VP | correct | standalone_clock_interval | {'start': 79100558, 'end': 79104175, 'state_tick': 44, 'score_tick': 44} |
| 6277/10576/R01/plant | Skeptic.TH | correct | standalone_clock_interval | {'start': 69226398, 'end': 69233119, 'state_tick': 44, 'score_tick': 44} |
| 6277/10576/R01/disable | unresolved | unresolved | disable_not_supported | {} |
| 6277/10576/R06/plant | unresolved | unresolved | kill_or_death_in_interval | {'start': 70776840, 'end': 70783426, 'state_tick': 44, 'score_tick': 44} |
| 6277/10576/R06/disable | unresolved | unresolved | disable_not_supported | {} |
| 6277/10576/R11/plant | Creedz.SECRET | correct | standalone_clock_interval | {'start': 76640797, 'end': 76644776, 'state_tick': 44, 'score_tick': 44} |
| 6277/10576/R12/plant | Hungry.SECRET | correct | standalone_clock_interval | {'start': 98497596, 'end': 98502012, 'state_tick': 44, 'score_tick': 44} |
| 4139/None/R07/plant | unresolved | unresolved | kill_or_death_in_interval | {'start': 61871294, 'end': 61875729, 'state_tick': 44, 'score_tick': 44} |

This experiment tests boundaries derived from replay clock changes rather than fixed byte gaps. It does not prove that the score is objective credit: gadget scores and delayed earlier scoring remain competing causes. The fresh reserve remains sealed. Every wrong result must be analyzed before any candidate freeze.
