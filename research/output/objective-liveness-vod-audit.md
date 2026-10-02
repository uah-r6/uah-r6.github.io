# Independent HUD liveness check

Source: [official DarkZero–Shopify grand-final VOD](https://www.youtube.com/watch?v=pTsWYqy7H2k&t=7020s), Bank R02, match 3563/game6675. Frames were manually inspected before comparison. This is one consumed round, not broad build validation.

Results: `{"states": 40, "hud_alive": 20, "hud_dead": 20, "diagnostic_unknown": 0, "disagreements": 0}`.

| VOD seconds | Phase / clock | HUD alive | HUD dead | Diagnostic disagreements |
| --- | --- | ---: | ---: | ---: |
| 6900 | prep / None | 10 | 0 | 0 |
| 7020 | action / 84 | 4 | 6 | 0 |
| 7060 | action / 44 | 3 | 7 | 0 |
| 7092 | action / 12 | 3 | 7 | 0 |

The query offset is the last kill packet strictly before the HUD clock, restricted to the pre-plant phase. This checks victim identity/order against an independent visible roster; it does not establish the exact byte-to-video timestamp relationship. Surf dies at replay clock 0:44 **after planting**; including that packet at action-phase 0:44 would incorrectly mark him dead. Packet order and phase prevent this clock-reset mistake.

## Unvalidated states and failure modes

- A positive value is absence of an earlier decoded death. Missing kills or disconnected players can therefore appear alive. It is not proof of interaction eligibility.
- The probe currently retains Kill/Death only, omitting PlayerLeave. No disconnected-player eligibility claim is justified.
- The parser Death branch has no killOffset assignment; those events have zero offset and yield unknown, never dead.
- DBNO and revive are not represented by this diagnostic. Health entity nearest-ID mapping is unverified for actor work and must not be used to fill the gap.
- No independent rehost/missing-roster, post-round or DBNO ground truth was acquired in this audit. The broadcast cuts away before the disable; no new actor label follows from it.
- Existing unit tests verify before/after-death and unknown-offset mechanics, not replay completeness.

Decision: keep liveness as provisional supporting evidence. This small HUD check does not justify a universal hard actor filter.
