# Consumed OCE unknown component: independent DBNO/recovery HUD controls

[Official Rainbow Six Esports OCE Stage1 Day4 broadcast](https://www.youtube.com/watch?v=ZCQqoIH4O0U), uploaded2026-06-16, exact channelUCWKHac5bjhsUtSnMDFCT-7A. Match8082 ManLFO–Rival, Nighthaven Labs.

Ten manually inspected frames from two already-consumed raw3-to2 observations. Named player cards supply independent labels; the camera subject is explicitly not used as the target identity. Labels and frame hashes were preserved before this interval projection. Selection was informed by consumed raw transitions and is not blind, representative or prospective.

| Video seconds | Round / named player | HUD action clock | Visible status | Stable raw value | Interval outcome |
| ---: | --- | --- | --- | --- | --- |
| 1130 | R01/Proxy.RVL | 1:20 | active | None | clock_reset_inside_action_bounds |
| 1132 | R01/Proxy.RVL | 1:18 | downed | None | clock_reset_inside_action_bounds |
| 1138 | R01/Proxy.RVL | 1:12 | downed | None | clock_reset_inside_action_bounds |
| 1146 | R01/Proxy.RVL | 1:04 | downed | None | clock_reset_inside_action_bounds |
| 1148 | R01/Proxy.RVL | 1:02 | active_after_recovery | None | clock_reset_inside_action_bounds |
| 2735 | R07/Elementz77. | 2:03 | active | 0 | stable_raw_value_over_displayed_second |
| 2750 | R07/Elementz77. | 1:48 | downed | 3 | stable_raw_value_over_displayed_second |
| 2754 | R07/Elementz77. | 1:44 | downed | 3 | stable_raw_value_over_displayed_second |
| 2759 | R07/Elementz77. | 1:39 | active_after_recovery | 2 | stable_raw_value_over_displayed_second |
| 2800 | R07/Elementz77. | 0:58 | eliminated | 4 | stable_raw_value_over_displayed_second |

Grouped observations: `[{'hud': 'active', 'raw_value': None, 'frames': 1}, {'hud': 'downed', 'raw_value': None, 'frames': 3}, {'hud': 'active_after_recovery', 'raw_value': None, 'frames': 1}, {'hud': 'active', 'raw_value': 0, 'frames': 1}, {'hud': 'downed', 'raw_value': 3, 'frames': 2}, {'hud': 'active_after_recovery', 'raw_value': 2, 'frames': 1}, {'hud': 'eliminated', 'raw_value': 4, 'frames': 1}]`; unresolved frames `5`.

## Interpretation and limits

Existing parser action markers and occurrence offsets bound the action clock epoch. Each displayed second is bracketed by adjacent clock ticks; missing ticks, a reset or raw transition within that second abstains. Typed component ownership is checked throughout the bracket, at retained property offsets and every declaration change. Byte/frame synchronization within a displayed second is not claimed.

The downed crosses and later active weapon cards corroborate two recovery sequences on classb529300b. The visual evidence supports raw3 as downed and raw2 as active in these cases; it does not authorize a universal enum or class mapping. It does not establish numeric HUD health, the downing shooter, which player performed the complete revival, bonus-health plant semantics or disconnect behavior. No component is approved because its HP is positive.

All frozen candidates and original ASIA/OCE classifications remain unchanged. These are DBNO/recovery compatibility controls, not new bonus-health actor observations or corrections. The seven primary plant-owner supports remain consumed and the31older plant actors remain unresolved in production. No SQLite/archive/public/Rating/operator/kill change, push or publish.
