# Independent HUD versus declared component state

Same manually labeled official VOD samples as `objective_liveness_vod_audit.py`; three Bank action-phase snapshots, 30 player states, plus three independently inspected Nighthaven Labs player snapshots. Preparation sample excluded because its byte position was not independently aligned. No fresh actor reserve used.

Counts `(HUD alive, raw state)`: `{'(True, 0)': 10, '(False, 4)': 20, '(True, 2)': 3}`.

Source: [official grand-final VOD](https://www.youtube.com/watch?v=pTsWYqy7H2k). Additional samples: Nighthaven R01, t650/action1:10 Ambi active; t700/action0:20 Canadian selected and aiming/reloading; R03 t1180/action1:25 Nuers active. All three have raw state2. Frame cache filenames use video seconds and format298.

These samples support state0 and state2 for living active players, and state4 for eliminated players. State2 must not be a hard DBNO/death exclusion. Two further visual samples show downed HUD crosses: R01 njr t644/1:16 and kyno t713/7.79. Corresponding raw paths have state3 between nearby clock ticks (njr77->76; kyno8->7), then state4. Their transitions occur within a displayed second, so no exact byte/frame alignment or universal state3 eligibility rule is claimed. Revive and disconnect semantics remain unvalidated. Positive HP alone was already shown insufficient by seven confirmed death cases.
