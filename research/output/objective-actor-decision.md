# Objective actor decision - 2026-10-01

Production occurrence remains frozen at `75d17a4`. No player credit is added.

The original discovery cohort contains 61 plants and eight disables. A new diagnostic joins an explicitly declared scoreboard component to a controller, then a typed numeric UID to the header identity. It avoids the rejected mutable username join. The test requires complete actor-team binding, a score delta shared by at least three teammates, a unique +100 residual, and no concurrent kill/assist counter increase for the candidate. Public actor labels and previously verified aliases are used only after prediction to grade it.

| Action | Correct | Incorrect | Unresolved |
| --- | ---: | ---: | ---: |
| Plant | 42 | 1 | 18 |
| Disable | 4 | 0 | 4 |

**Rejected:** 4139 R07 predicts Aiden; the public log identifies Raid. Team deltas are Raid 210, Aiden 200, and three teammates 100. Raid has a concurrent counter increase. Even team-relative score decomposition plus stable identity does not establish the actor. These discovery results are not independent validation; the twelve-map extension was not used for actor tuning.

Five contrasting rounds also yielded no typed reference edge from the objective-state entity to a player. The partial upstream UID adjacency pattern covers only nine of fifty player slots. Another table identifies five SSG entities in 4139 R07, but their spawn counter is 154, consistent with drones, not player bodies. The [upstream movement decoder](https://raw.githubusercontent.com/wnc-replay/replay-tool/main/dissect/movement.go) was useful prior art, not proof of complete ownership mapping. Four inspected Y11 rounds bind ten score identities each; the February layout does not support that declaration join.

The precise remaining gap is a verified player/controller/pawn-to-interaction relationship, or a score-event decomposition that survives simultaneous actions and scoreboard batches. This is not evidence that attribution is impossible. Carrier ownership, completion time, and component identity must not be conflated. No trustworthy new actor has been recovered, including the user's personal UAH disable; the existing read-only audit remains 17 plants and three disables with unresolved actors across 62 rounds.

No rederive is warranted: player features are unchanged. Continue controlled Rating experiments with player objectives explicitly unavailable/excluded. Keep occurrence metadata and all production safeguards. Diagnostics and cached evidence live under ignored `data/research/diagnostics/`; reproduction: `python research/objective_actor_batch_validation.py`.
