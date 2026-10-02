# Independent Fortress round 7 target contradiction

## Evidence and unchanged required safeguard

The required 4139/R07 resolver outcome remains **unresolved**, never a confident Aiden credit. No actor rule, target cache, immutable validation result, SQLite or public data was changed. This report records independent evidence contradicting the earlier Raid target; it does not override that explicit user constraint.

Official [Rainbow Six Esports Match Vods: 100Thieves versus Spacestation](https://www.youtube.com/watch?v=sQNarwuswkg), NAL Stage1 Group Stage, July3,2026. The [official Ubisoft match page](https://www.ubisoft.com/en-us/esports/rainbow-six/siege/match/8022) confirms the 7-5 Fortress match. Replays correspond to SiegeGG4139. Metadata and format298 frames are cached in ignored `data/research/video/4139*`; no full video or replay redownload.

| Video seconds | Round / score / clock | Visible evidence |
| --- | --- | --- |
| 1800 | FortressR07,100T3-3SSG,prep0:21 | Establishes round and phase. |
| 1958 | FortressR07,3-3,action0:43 | Two attackers Aiden.SSG and Raid.SSG versus SpiriTz.100T. Aiden card shows the yellow defuser carrier icon. |
| **1963** | **FortressR07,3-3,action0:38** | **Aiden.SSG card explicitly reads "Planting the Defuser", location2F Bedroom. Raid.SSG is separately active with weapon ammunition at EXT Hammam Roof.** |
| 1967 | FortressR07,3-3,post-plant44.80 | Completed plant; Aiden is alive in2F Bathroom, Raid is active separately on the roof. |
| 1970 | FortressR07,3-3,post-plant41.82 | SpiriTz kills Aiden; Raid remains last attacker. Plant is already complete. |

The visible broadcast attributes the interaction to Aiden, not Raid. The subsequent Raid clutch/last-survivor state must not be mistaken for planting. This is a target contradiction requiring review. It explains why score and the newly observed declared timer component both point toward Aiden, but their observation alone would not have been enough to reject the public label.

## Research handling

- Keep the existing mandatory control unresolved and all earlier primary results exactly as recorded.
- Do not change a global resolver to special-case this round, silently substitute a target or declare previously rejected score logic safe.
- Store the separate visual observation and source timestamp. New component-owner evidence remains research-only with no actor credit.
- Broad attribution still needs decoded interaction state semantics, interrupted/non-objective controls, cross-build identity validation and a new frozen validation plan. The disputed BankR02 J9O/njr disable remains unverified; its broadcast cuts away.

Reproduction:

```powershell
.venv\Scripts\python.exe -m yt_dlp --skip-download --write-info-json --no-playlist -o 'data/research/video/4139.%(ext)s' 'https://www.youtube.com/watch?v=sQNarwuswkg'
.venv\Scripts\python.exe research\vod_frame_probe.py data/research/video/4139.info.json 1800 1958 1963 1967 1970 --format 298
```
