# SiegeGG-style rating research

This is a separate experiment. The application and public website still use `collegiate_v1`. The fitted coefficients below are **not** an official SiegeGG formula and are not installed as a rating version.

[SiegeGG's rating rebalance explanation](https://siege.gg/news/946-player-rating-rebalance) describes nine performance categories and operator-relative comparisons. It does not publish the exact weights or enough implementation detail to reproduce official ratings directly.

## Reproduce the dataset

From the repository root on Windows, after normal project setup:

```powershell
.\.venv\Scripts\python.exe research\pipeline.py all
.\.venv\Scripts\python.exe research\fit_baseline.py
```

`pipeline.py collect` downloads only missing archives and targets, verifies each ZIP, extracts safely, and caches normalized rounds. `pipeline.py derive` validates each replay map against its public SiegeGG game: map, score, round count, both rosters, and named player mapping. It writes one row per player-map to ignored `data/research/experiments/player_maps.jsonl`, including round-level operator and performance snapshots. It flags rows with mismatched public K/D, round counts, or unverified player aliases; only rows without flags enter fitting. `fit_baseline.py` appends a machine-readable record to `data/research/experiments/experiment-log.jsonl`. A snapshot of experiments performed in this session is in [experiment-log.jsonl](experiment-log.jsonl).

Source URLs and exact replay-folder ↔ SiegeGG game mappings are in [sources.json](sources.json). The five official Ubisoft archives are from [NIP vs Weibo at SI 2026](https://www.ubisoft.com/en-us/esports/rainbow-six/siege/match/7580), [Weibo vs Daystar at Kickoff 2026](https://www.ubisoft.com/en-us/esports/rainbow-six/siege/match/7952), [Daystar vs Team Orchid at Kickoff 2026](https://www.ubisoft.com/en-us/esports/rainbow-six/siege/match/7960), [PSYKN vs Soul's Heart at Stage 1](https://www.ubisoft.com/en-us/esports/rainbow-six/siege/match/8124), and [Daystar vs Weibo at Stage 1](https://www.ubisoft.com/en-us/esports/rainbow-six/siege/match/8125). Their public targets are [SiegeGG matches 3073](https://siege.gg/matches/3073-invitational-intl-ninjas-in-pyjamas-vs-weibo-gaming), [3579](https://siege.gg/matches/3579-apacl-apac-weibo-gaming-vs-daystar), [3585](https://siege.gg/matches/3585-apacl-apac-team-orchid-vs-daystar), [3879](https://siege.gg/matches/3879-apacl-apac-souls-heart-esport-vs-psykn-company), and [3880](https://siege.gg/matches/3880-apacl-apac-daystar-vs-weibo-gaming). Downloads and target JSON remain Git-ignored.

## Experiment 1: raw nine-family baseline

Nine maps across three events produced 90 player-map rows. Fifty-seven have exact public K/D and round count and independently supported player aliases. The predeclared event split used 32 Kickoff rows for training and 10 SI rows for validation. The Stage 1 holdout was first evaluated on five rows from one map, then **expanded without refitting** to 15 rows across two maps. The ridge model uses KPR, teamkills/round, extra kills after the first in each round, opening differential/round, successful 1vX clutches/round, KOST, survival, `(deaths_traded - kills_traded)/round`, and `(plants + disables)/round`. All features are standardized on training data; ridge alpha is 1. The site’s default eight-second trade window is used.

| Split | Rows | Raw model MAE | Raw RMSE | Within 0.05 | `collegiate_v1` MAE |
| --- | ---: | ---: | ---: | ---: | ---: |
| SI validation | 10 | 0.033 | 0.044 | 70% | 0.197 |
| Stage 1 test, initial | 5 | 0.021 | 0.023 | 100% | 0.113 |
| Stage 1 test, expanded | 15 | 0.047 | 0.055 | 53% | 0.232 |

The trained intercept is 0.9803 in standardized feature space. Standardized coefficients are KPR 0.1460, teamkills 0, multikill 0.0501, opening 0.0293, clutch 0.0344, KOST 0.0757, survival 0.0889, trade 0.0070, and objectives -0.0026. These coefficients are exploratory: no teamkills occurred in training, and the slightly negative objective coefficient is a warning about sample size and correlated features. Expansion of the untouched holdout from one to two maps more than doubled MAE, illustrating the fragility of the small sample. The model uses raw metrics only. It is intentionally absent from runtime code and configuration.

## Blocking data quality issues

- Thirty-three of 90 rows are excluded. Most have replay-derived kills or deaths different from SiegeGG's public map stats; four Stage 1 aliases lack independent identity confirmation. The per-row issues are printed by `pipeline.py derive`. **Every one of the nine maps has exactly matching total team-wide kills and deaths** between the replay and SiegeGG; the discrepancies are in per-player attribution. Some differences are one kill transferred between players, while some SI LAN deaths differ. They require event-level investigation before widening the fit set.
- SI LAN replays use the same nil Ubisoft profile UUID for every player. The adapter now uses usernames as identity keys for that sentinel; cached SI normalized rounds were reparsed. This restored distinct player metrics but did not eliminate all public-stat discrepancies.
- All 375 unresolved operator player-rounds are Y11 attacking rounds in the four online matches. A directly inspected professional R01 parser JSON had `gameVersion=Y11S1_Alpha03` but no `actionPhaseDetected`, `operatorSource`, or `operatorSeenBeforeAction` fields. The local parser therefore cannot trust the attacker header selection after repick. The current NECC/Y11 action-start logic remains unchanged. Public SiegeGG's representative operator icons cannot substitute for per-round final operators. An operator-relative model should wait for reliable replay-side snapshots or a parser enhancement validated against these professional files.
- The current replay event schema does not prove SiegeGG's exact trade, clutch, multikill, opening, or objective definitions. With 57 usable rows, systematically comparing many definitions would overfit. A larger, independently validated set is needed before model selection.

Next, acquire more events with complete replays, independently verify username aliases, investigate kill/death attribution against round logs, and resolve final Y11 professional attacker operators. Then run grouped validation across several events, preserve a later event for one final test, compare operator normalization methods, and only then consider a versioned candidate rating and UAH comparison report. Do not switch the site default before review.
