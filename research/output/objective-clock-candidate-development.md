# Standalone score / clock interval development experiment

Consumed cases only. Unfrozen hypothesis; no production actor credit. See source function for exact logic. A candidate needs one +100 eligible score change before the first score tick ends, with that tick at completion or immediately next. Kill/death or positive kill/assist counter inside the interval vetoes the candidate. Unknown death offsets abstain. Disables are not selected by this plant-only mode.

Development counts: `{"plant": {"correct": 38, "unresolved": 23}, "disable": {"unresolved": 8}}`.

| Match/game/round/kind | Candidate | Verdict | Reason | Clock interval |
| --- | --- | --- | --- | --- |
| 4150/None/R03/plant | Forrest.5F | correct | standalone_clock_interval | {'start': 74487035, 'end': 74492899, 'state_tick': 44, 'score_tick': 44} |
| 4150/None/R07/plant | Hotancold.100T | correct | standalone_clock_interval | {'start': 81742579, 'end': 81747762, 'state_tick': 44, 'score_tick': 44} |
| 4150/None/R09/plant | unresolved | unresolved | not_single_standalone_increment | {'start': 68434291, 'end': 68439717, 'state_tick': 44, 'score_tick': 44} |
| 4150/None/R11/plant | Hotancold.100T | correct | standalone_clock_interval | {'start': 74408809, 'end': 74412516, 'state_tick': 44, 'score_tick': 44} |
| 4132/None/R05/plant | JJBlaztful.5F | correct | standalone_clock_interval | {'start': 66782800, 'end': 66785998, 'state_tick': 44, 'score_tick': 44} |
| 4132/None/R10/plant | unresolved | unresolved | not_single_standalone_increment | {'start': 87617471, 'end': 87622087, 'state_tick': 44, 'score_tick': 44} |
| 4132/None/R10/disable | unresolved | unresolved | disable_not_supported | {} |
| 4132/None/R13/plant | Fenz.5F | correct | standalone_clock_interval | {'start': 78525828, 'end': 78530393, 'state_tick': 44, 'score_tick': 44} |
| 4132/None/R15/plant | unresolved | unresolved | not_single_standalone_increment | {'start': 75856753, 'end': 75861124, 'state_tick': 44, 'score_tick': 44} |
| 3585/None/R04/plant | unresolved | unresolved | kill_or_death_in_interval | {'start': 73403512, 'end': 73408518, 'state_tick': 44, 'score_tick': 44} |
| 3585/None/R06/plant | unresolved | unresolved | not_single_standalone_increment | {'start': 71488361, 'end': 71492643, 'state_tick': 44, 'score_tick': 44} |
| 3585/None/R07/plant | unresolved | unresolved | kill_or_death_in_interval | {'start': 88541592, 'end': 88546465, 'state_tick': 44, 'score_tick': 44} |
| 3585/None/R07/disable | unresolved | unresolved | disable_not_supported | {} |
| 3585/None/R08/plant | Lycolis.ORC | correct | standalone_clock_interval | {'start': 69041375, 'end': 69044321, 'state_tick': 44, 'score_tick': 44} |
| 6156/None/R01/plant | kyno | correct | standalone_clock_interval | {'start': 57766621, 'end': 57769833, 'state_tick': 44, 'score_tick': 44} |
| 6156/None/R05/plant | unresolved | unresolved | not_immediate_complete_clock_interval | {} |
| 6156/None/R07/plant | unresolved | unresolved | not_immediate_complete_clock_interval | {} |
| 6156/None/R07/disable | unresolved | unresolved | disable_not_supported | {} |
| 6156/None/R10/plant | Yoggah | correct | standalone_clock_interval | {'start': 82076676, 'end': 82082635, 'state_tick': 44, 'score_tick': 44} |
| 6156/None/R10/disable | unresolved | unresolved | disable_not_supported | {} |
| 3073/None/R03/plant | unresolved | unresolved | incomplete_identity | {} |
| 3073/None/R08/plant | unresolved | unresolved | incomplete_identity | {} |
| 3554/None/R05/plant | kyno | correct | standalone_clock_interval | {'start': 75156064, 'end': 75159372, 'state_tick': 44, 'score_tick': 44} |
| 3554/None/R09/plant | unresolved | unresolved | kill_or_death_in_interval | {'start': 57623622, 'end': 57630248, 'state_tick': 44, 'score_tick': 44} |
| 4112/None/R01/plant | unresolved | unresolved | kill_or_death_in_interval | {'start': 74773982, 'end': 74778390, 'state_tick': 44, 'score_tick': 44} |
| 4112/None/R03/plant | unresolved | unresolved | kill_or_death_in_interval | {'start': 70285280, 'end': 70291436, 'state_tick': 44, 'score_tick': 44} |
| 4112/None/R04/plant | R4re.BD | correct | standalone_clock_interval | {'start': 54763431, 'end': 54766794, 'state_tick': 44, 'score_tick': 44} |
| 4112/None/R07/plant | Gabu7z.LOUD | correct | standalone_clock_interval | {'start': 64876808, 'end': 64879578, 'state_tick': 44, 'score_tick': 44} |
| 4112/None/R09/plant | live.LOUD | correct | standalone_clock_interval | {'start': 72870330, 'end': 72875988, 'state_tick': 44, 'score_tick': 44} |
| 4112/None/R11/plant | live.LOUD | correct | standalone_clock_interval | {'start': 82232908, 'end': 82237369, 'state_tick': 44, 'score_tick': 44} |
| 4112/None/R12/plant | live.LOUD | correct | standalone_clock_interval | {'start': 79586161, 'end': 79590439, 'state_tick': 44, 'score_tick': 44} |
| 3637/None/R02/plant | unresolved | unresolved | kill_or_death_in_interval | {'start': 77659045, 'end': 77663681, 'state_tick': 44, 'score_tick': 44} |
| 3637/None/R10/plant | Alem4o.G2 | correct | standalone_clock_interval | {'start': 76295954, 'end': 76299521, 'state_tick': 44, 'score_tick': 44} |
| 4140/None/R11/plant | Rexen.SR | correct | standalone_clock_interval | {'start': 75028099, 'end': 75031986, 'state_tick': 44, 'score_tick': 44} |
| 4118/None/R03/plant | Handyy.FaZe | correct | standalone_clock_interval | {'start': 56882550, 'end': 56887024, 'state_tick': 44, 'score_tick': 44} |
| 4118/None/R07/plant | live.LOUD | correct | standalone_clock_interval | {'start': 54233696, 'end': 54236614, 'state_tick': 44, 'score_tick': 44} |
| 4141/None/R10/plant | Beeno.4FUN | correct | standalone_clock_interval | {'start': 66168012, 'end': 66172229, 'state_tick': 44, 'score_tick': 44} |
| 4134/None/R04/plant | Canadian.SR | correct | standalone_clock_interval | {'start': 50598304, 'end': 50601369, 'state_tick': 44, 'score_tick': 44} |
| 4134/None/R08/plant | Dream.SSG | correct | standalone_clock_interval | {'start': 59116757, 'end': 59119818, 'state_tick': 44, 'score_tick': 44} |
| 4148/None/R03/plant | unresolved | unresolved | kill_or_death_in_interval | {'start': 58567999, 'end': 58572040, 'state_tick': 44, 'score_tick': 44} |
| 4139/None/R04/plant | Hotancold.100T | correct | standalone_clock_interval | {'start': 79657061, 'end': 79659818, 'state_tick': 44, 'score_tick': 44} |
| 4139/None/R07/plant | unresolved | unresolved | kill_or_death_in_interval | {'start': 61871294, 'end': 61875729, 'state_tick': 44, 'score_tick': 44} |
| 3639/None/R03/plant | unresolved | unresolved | kill_or_death_in_interval | {'start': 64229152, 'end': 64234812, 'state_tick': 44, 'score_tick': 44} |
| 3639/None/R03/disable | unresolved | unresolved | disable_not_supported | {} |
| 3639/None/R05/plant | noa.SECRET | correct | standalone_clock_interval | {'start': 77354576, 'end': 77358439, 'state_tick': 44, 'score_tick': 44} |
| 3639/None/R06/plant | Mowwwgli.SECRET | correct | standalone_clock_interval | {'start': 76371741, 'end': 76377356, 'state_tick': 44, 'score_tick': 44} |
| 3639/None/R07/plant | AquiX.HERETICS | correct | standalone_clock_interval | {'start': 83485177, 'end': 83489518, 'state_tick': 44, 'score_tick': 44} |
| 4127/None/R01/plant | Gunnar.M80 | correct | standalone_clock_interval | {'start': 71802812, 'end': 71807903, 'state_tick': 44, 'score_tick': 44} |
| 4127/None/R04/plant | Ashn.M80 | correct | standalone_clock_interval | {'start': 70345445, 'end': 70348155, 'state_tick': 44, 'score_tick': 44} |
| 4127/None/R05/plant | Savage.M80 | correct | standalone_clock_interval | {'start': 68842659, 'end': 68847747, 'state_tick': 44, 'score_tick': 44} |
| 4137/None/R10/plant | Spiker.WC | correct | standalone_clock_interval | {'start': 46430842, 'end': 46435609, 'state_tick': 44, 'score_tick': 44} |
| 4137/None/R15/plant | Spiker.WC | correct | standalone_clock_interval | {'start': 58253181, 'end': 58255650, 'state_tick': 44, 'score_tick': 44} |
| 4138/None/R04/plant | Ewzy.C9 | correct | standalone_clock_interval | {'start': 60783747, 'end': 60787184, 'state_tick': 44, 'score_tick': 44} |
| 4119/None/R03/plant | R4re.BD | correct | standalone_clock_interval | {'start': 68076408, 'end': 68080989, 'state_tick': 44, 'score_tick': 44} |
| 4120/None/R08/plant | unresolved | unresolved | kill_or_death_in_interval | {'start': 71362637, 'end': 71365417, 'state_tick': 44, 'score_tick': 44} |
| 4120/None/R09/plant | dotz.FX | correct | standalone_clock_interval | {'start': 78416984, 'end': 78420715, 'state_tick': 44, 'score_tick': 44} |
| 4133/None/R03/plant | J9O.DZ | correct | standalone_clock_interval | {'start': 42848446, 'end': 42851829, 'state_tick': 44, 'score_tick': 44} |
| 4133/None/R03/disable | unresolved | unresolved | disable_not_supported | {} |
| 4133/None/R07/plant | unresolved | unresolved | unknown_death_offset | {'start': 56349434, 'end': 56356090, 'state_tick': 44, 'score_tick': 44} |
| 3880/None/R02/plant | unresolved | unresolved | kill_or_death_in_interval | {'start': 81668322, 'end': 81671976, 'state_tick': 44, 'score_tick': 44} |
| 3880/None/R04/plant | unresolved | unresolved | kill_or_death_in_interval | {'start': 75339651, 'end': 75342190, 'state_tick': 44, 'score_tick': 44} |
| 3880/None/R06/plant | SpeakEasy.WBG | correct | standalone_clock_interval | {'start': 65757647, 'end': 65761186, 'state_tick': 44, 'score_tick': 44} |
| 3880/None/R09/plant | Pikanzu.Daystar | correct | standalone_clock_interval | {'start': 57556912, 'end': 57560093, 'state_tick': 44, 'score_tick': 44} |
| 3880/None/R10/plant | unresolved | unresolved | kill_or_death_in_interval | {'start': 68024858, 'end': 68029748, 'state_tick': 44, 'score_tick': 44} |
| 3880/None/R10/disable | unresolved | unresolved | disable_not_supported | {} |
| 3879/None/R03/plant | JoeGoR.KZ | correct | standalone_clock_interval | {'start': 78718820, 'end': 78723503, 'state_tick': 44, 'score_tick': 44} |
| 3879/None/R12/plant | MARKELELE.SH | correct | standalone_clock_interval | {'start': 70847331, 'end': 70849639, 'state_tick': 44, 'score_tick': 44} |
| 3879/None/R13/plant | unresolved | unresolved | kill_or_death_in_interval | {'start': 67449717, 'end': 67453121, 'state_tick': 44, 'score_tick': 44} |
| 3073/None/R08/disable | unresolved | unresolved | no_completion_state_anchor | {} |

This experiment tests boundaries derived from replay clock changes rather than fixed byte gaps. It does not prove that the score is objective credit: gadget scores and delayed earlier scoring remain competing causes. The fresh reserve remains sealed. Every wrong result must be analyzed before any candidate freeze.
