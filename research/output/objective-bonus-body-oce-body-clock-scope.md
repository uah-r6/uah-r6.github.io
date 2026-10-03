# Consumed OCE HUD: scoped first clock epoch follow-up

[Official OCE Day4 broadcast](https://www.youtube.com/watch?v=ZCQqoIH4O0U&t=1132s), same preserved ten frames/labels as the initial strict report, two consumed Nighthaven rounds.

The initial comparison leaves five R01frames unresolved: a postplant clock reset is written before the existing serialized plant occurrence anchor, so its conservative whole-range monotonicity guard refuses every sample in the range. That initial JSON is preserved byte-for-byte. This additive diagnostic bounds only the first countdown following the unchanged existing action marker. Its end is the first observed clock increase, or the existing anchor if no increase occurs. It never selects a later phase, omits a physical round or changes action-start/operator parsing.

| Video seconds | Round / player | HUD clock | Named HUD observation | Raw value | Original strict raw |
| ---: | --- | --- | --- | --- | --- |
| 1130 | R01/Proxy.RVL | 1:20 | active | 0 | None |
| 1132 | R01/Proxy.RVL | 1:18 | downed | 3 | None |
| 1138 | R01/Proxy.RVL | 1:12 | downed | 3 | None |
| 1146 | R01/Proxy.RVL | 1:04 | downed | 3 | None |
| 1148 | R01/Proxy.RVL | 1:02 | active_after_recovery | 2 | None |
| 2735 | R07/Elementz77. | 2:03 | active | 0 | 0 |
| 2750 | R07/Elementz77. | 1:48 | downed | 3 | 3 |
| 2754 | R07/Elementz77. | 1:44 | downed | 3 | 3 |
| 2759 | R07/Elementz77. | 1:39 | active_after_recovery | 2 | 2 |
| 2800 | R07/Elementz77. | 0:58 | eliminated | 4 | 4 |

Counts: `[{'hud': 'active', 'raw_value': 0, 'frames': 2}, {'hud': 'downed', 'raw_value': 3, 'frames': 5}, {'hud': 'active_after_recovery', 'raw_value': 2, 'frames': 2}, {'hud': 'eliminated', 'raw_value': 4, 'frames': 1}]`; unresolved `0`. Already projected R07values remain unchanged.

The two named downed-cross/recovery sequences corroborate raw3 during visible DBNO and raw2 after recovery on classb529300b in these consumed cases. Raw0 accompanies active cards; raw4 accompanies an eliminated WATCHING card. Same-owner typed route checks and stable state across the full displayed second are retained. No exact within-second synchronization, numeric HUD health, downer identity, complete reviver identity, universal enum, disconnect behavior or bonus-health plant evidence is established. Selection follows exposed consumed transitions and is not fresh.

The conservative production class remains0c98c63f. No old outcome/actor/gate is regraded, no bonus candidate is changed and no actor is credited. Original ASIA/OCE insufficient and both failed v3 finals remain permanent. SQLite, archives, public JSON, live Rating/operator/kill logic and website remain unchanged; no push/publish.
