# Independent VOD check: 3563 / game 6675 / Bank R02

Research-only manual visual review, 2026-10-01. The unresolved replay score residual names njr; the cached SiegeGG event names J9O. No target label or production actor was changed.

## Source and observed sequence

Official [Rainbow Six Esports grand-final VOD](https://www.youtube.com/watch?v=pTsWYqy7H2k), DarkZero vs Shopify Rebellion, Salt Lake City Major, May 17 2026. Video ID `pTsWYqy7H2k`, duration 12,974 seconds. The [official event page](https://www.ubisoft.com/en-us/esports/rainbow-six/siege/competition/502) independently identifies the matchup and date.

Sampled frames were retrieved by HTTP range seeking in public video formats 135 and 298, using FFmpeg. No full-video download was required. Metadata and images remain in ignored `data/research/video/`.

| VOD position | Seconds | Visible evidence |
| --- | ---: | --- |
| 1:50:00 | 6600 | Bank round 1 ban/reveal UI; establishes map segment. |
| 1:55:00 | 6900 | Bank round 2, DarkZero leads 1-0, preparation timer 0:24. |
| 1:57:00 | 7020 | Round 2 action timer 1:24, two surviving defenders J9O/njr. |
| 1:57:40 | 7060 | Round 2, 0:44, two defenders versus Surf. |
| 1:58:12 | 7092 | Surf planting, 0:12 on round clock. |
| 1:58:14 | 7094 | Defuser planted, 44.20 post-plant clock; Surf's POV faces J9O. |
| 1:58:16 | 7096 | Broadcast has cut to player camera. |
| 1:58:20-1:58:35 | 7100-7115 | Crowd/player cameras; no disable interaction visible. |
| 1:58:40 | 7120 | Tactical timeout camera. |

The VOD confirms the map/round and Surf's plant but **does not independently identify the disabler**. It cuts away before the relevant interaction. The score discrepancy remains unresolved. Do not infer an actor from the player camera, from who made the final kill, or from which player receives a round-end score residual.

## Reproduction

Optional research dependencies installed only in `.venv`: `yt-dlp==2026.8.19`, `imageio-ffmpeg==0.6.0`. They are not application requirements. Metadata URLs expire; refresh only if additional uncached frames are needed.

```powershell
.\.venv\Scripts\python.exe -m yt_dlp --skip-download --write-info-json --no-playlist -o 'data/research/video/3563.%(ext)s' 'https://www.youtube.com/watch?v=pTsWYqy7H2k'
.\.venv\Scripts\python.exe research/vod_frame_probe.py data/research/video/3563.info.json 7092 7094 7096 7098 7100 7105 7110 7115 7120 --format 298
```
