# Independent review of the cached-map actor discrepancy

The full frozen result was committed as `91594f3` before this review. Its primary grading remains **10 correct / 1 incorrect / 4 unresolved plants**, with all three disables unresolved. Neither cached target nor immutable result was edited. The six maps are consumed.

## Source

Official [Rainbow Six Esports Match Vods semifinal](https://www.youtube.com/watch?v=ISlfYfpK4Tw), DarkZero versus FaZe, May 16, 2026. Video duration 10,009 seconds. The [official Ubisoft match page](https://www.ubisoft.com/en-us/esports/rainbow-six/siege/match/9027) independently confirms Clubhouse 7-8, Bank 7-3, Chalet 7-1 and the matchup/date. This is the match mapped to SiegeGG3554, Chalet game6679.

Public video metadata and selected format298 frames were retrieved with yt-dlp and FFmpeg range seeking, cached in ignored `data/research/video/3554*`. No full-video or replay redownload. The initial optional HTTP client import failed because requests is not installed; the alternative r6tv page returned HTTP403. Official YouTube metadata and frame access worked. An initial metadata read using Windows cp1252 failed; UTF-8 fixed it.

## Visible evidence

| Video seconds | Round / score / clock | Evidence |
| --- | --- | --- |
| 8700 | ChaletR04, DarkZero3-0, prep0:19 | Kyno HUD card shows the yellow defuser carrier symbol. |
| 8750 | ChaletR04, DarkZero3-0, action2:29 | Establishes action phase and roster; Fultz is playing Twitch, kyno Blackbeard. |
| 8800 | ChaletR04, DarkZero3-0, action1:39 | Five attackers and four defenders alive. |
| **8817** | **ChaletR04, DarkZero3-0, action1:22** | **Kyno's card explicitly reads "Planting the Defuser", location2F Master Bedroom. Fultz's separate active card has no plant status.** |
| **8822** | **ChaletR04, DarkZero3-0, action1:17** | **Kyno's card still explicitly reads "Planting the Defuser". Picture-in-picture shows the planting player kneeling at the site.** |
| 8824 | ChaletR04, DarkZero3-0, post-plant44.67 | Defuser planted banner; picture-in-picture shows the player standing from that interaction. |
| 8826 | ChaletR04, DarkZero3-0, post-plant42.69 | Confirms completed plant and continuing round. |

This independently identifies **kyno** as the planter, in agreement with the unchanged frozen replay prediction. The public round label **Fultz plants defuser** contradicts visible official broadcast evidence. This is a documented target discrepancy, not an actor-rule correction, per-event blacklist or a reason to rewrite the historical primary result. The primary disagreement remains in every frozen result report; a separate broadcast-reviewed tally would count this one prediction as supported.

The replay packet ledger is in `objective-cached-false-credit.md`: timer6.967->0.045, action clock82->75 then post-plant44, completion57527888, kyno score950->1050 at57528646 before clock43. Stable UID/controller/score declarations bind kyno uniquely. All five attacker body states are0 throughout the interaction; no score/sole disagreement, nearby Kill/Death or kill/assist counter in the frozen scoring interval. The known disputed Bank disable J9O/njr remains unresolved; this review says nothing about its actor.

## Limits and next action

Broadcast confirmation resolves this target contradiction; it does not prove all immediate +100 changes are objective credit. Gadget scores, delayed rewards, packet omissions and legacy score-binding compatibility remain concerns. Across the three newly opened sets only14 plant predictions and1 disable prediction have named actors. The SI extension entirely abstains. Preserve original A and all immutable results. Continue with a **read-only** UAH evidence report and additional consumed semantic controls; do not deploy actor credit, modify SQLite/public JSON/archive or begin v3 fitting on this limited basis.

Reproduction:

```powershell
.venv\Scripts\python.exe research\objective_cached_false_credit.py
.venv\Scripts\python.exe -m yt_dlp --skip-download --write-info-json --no-playlist -o 'data/research/video/3554.%(ext)s' 'https://www.youtube.com/watch?v=ISlfYfpK4Tw'
.venv\Scripts\python.exe research\vod_frame_probe.py data/research/video/3554.info.json 8817 8822 8824 8826 --format 298
```
