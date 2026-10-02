# Independent Bank disable interaction review

## Consumed disagreement, preserved original result

Consumed EWC match6157/game10427/BankR01: the direct timer-component observation
is LoiraDEMON, while the cached SiegeGG round label says DiasLucas disables.
This is a development ownership disagreement. Every diagnostic actor remains
null; the original frozen six-map result remains unchanged, including its three
unresolved disables. No target cache or historical statistics were revised.

The official [Rainbow Six Esports Match Vods grand final](https://www.youtube.com/watch?v=eZiDda6eM6E)
is FURIA versus FaZe, EWC Day10. The
[official Ubisoft match9070](https://www.ubisoft.com/en-us/esports/rainbow-six/siege/match/9070)
confirms Bank3-7, Border5-7, Fortress8-6 and Lair5-7. Its Bank player table lists
Loira2 objectives and Dias0, supporting the replay ownership discrepancy at map
level but not supplying a per-round actor by itself.

Metadata and unaltered format298 frames are cached in ignored
`data/research/video/6157*`. An initial title search returned a FaZe/Liquid
quarterfinal. Its metadata was retained separately as
`6157-quarterfinal-mismatch.info.json`; none of its frames or content were used
as actor evidence. Exact teams, map sequence and scores identify the grand final.

| Video seconds | Round / score / clock | Visible evidence |
| --- | --- | --- |
| 200 | BankR01,FUR0-0FAZE,action1:28 | Establishes round, map, teams and ten players. |
| 285 | BankR01,postplant32.50,3v3 | The defuser is planted. Loira and Dias are distinct living defenders. |
| 290 | BankR01,postplant27.52,3v1 | Loira kills handyy; Dias kills vitaking. Both appear separately on the HUD. |
| **298.50** | **BankR01,postplant19.01,3v0** | **LoiraDEMON card explicitly says Counter-Defusing. Dias has just killed kds and remains active with weapon ammunition.** |
| **298.75** | **BankR01,postplant18.77,3v0** | **Loira still Counter-Defusing; Dias's separate card displays weapon ammunition.** |
| **299.25** | **BankR01,postplant18.27,3v0** | **Dias POV shows LoiraDEMON crouched at the defuser, counter-defusing icon above him; Loira's HUD explicitly says Counter-Defusing. Dias is active with his shotgun.** |
| 299.50 | Stage camera | Broadcast cuts away; the exact completion frame is not visible. |
| 400 | BankR02,FUR1-0FAZE | Confirms the defending team won round1. |

The video independently supports **Loira's disable interaction**, and visibly
distinguishes Dias's last opposing kill from that interaction. Completion itself
is off camera, so this is not a claim that an uninterrupted VOD independently
shows every step through completion. Replay component termination and the official
map-level objective totals are additional supporting evidence. Keep the original
consumed comparison and target text; do not silently mark the disagreement correct.

The replay ledger records Loira state1 start78294218, terminal state2 record78314660
and independently decoded global disable state at78314759. The plant anchor is
78192862. All joins use temporal explicit numeric UID/slot declarations, not score
excess, nearby entity IDs or the last player to kill an opponent.

The mandatory Raid/Aiden and J9O/njr actor controls remain unresolved. This review
does not establish either disputed actor, promote a new resolver, or change live
`siege_style_v2`, SQLite, archives or public data.

Reproduction:

```powershell
.venv\Scripts\python.exe -m yt_dlp --skip-download --write-info-json --no-playlist -o 'data/research/video/6157.%(ext)s' 'https://www.youtube.com/watch?v=eZiDda6eM6E'
.venv\Scripts\python.exe research\vod_frame_probe.py data/research/video/6157.info.json 200 285 290 298.5 298.75 299.25 299.5 400 --format 298
```
