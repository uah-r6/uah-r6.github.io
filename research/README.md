# SiegeGG-style rating research

This research is separate from the tracker. `collegiate_v1` remains the only live rating. None of these coefficients is an official SiegeGG formula or a selectable application rating version. [SiegeGG's rating rebalance explanation](https://siege.gg/news/946-player-rating-rebalance) identifies nine metric families and operator-relative comparisons, but does not publish its exact implementation.

## Data and reproducibility

The cached dataset contains 29 distinct official Ubisoft replay archives represented by 30 source-manifest entries, 42 complete maps from nine named events, and 420 player-map observations. **298 rows pass strict gates** for map, score, roster, round count, exact public K/D, and alias evidence. Sixteen clean September Stage 2 rows from two maps were reserved for a one-time final evaluation and are now a historical benchmark. The other 122 rows remain excluded; see the [quality audit](quality-report.md) for each row and cause. The [source manifest](sources.json) records official replay URLs, exact replay-folder to SiegeGG game mappings, public player IDs, and independently verified alias evidence.

Downloads, extracted `.rec` files, normalized rounds, public targets, and derived observations stay under ignored `data/research/`. `pipeline.py` caches by source URL and parser binary SHA-256 plus replay-file signature. A changed parser binary triggers reparsing. `--force` explicitly reparses. The derived `player_maps.jsonl` retains each player's operator, side, kills, deaths, teamkills, opening results, clutch size counts, KOST result, survival, trades, plants and disables for every round. Normalized replay JSON retains event-level detail for later metric definitions. Raw downloads are never committed.

From the repository root on Windows:

```powershell
.\.venv\Scripts\python.exe research\pipeline.py all
.\.venv\Scripts\python.exe research\quality_report.py
.\.venv\Scripts\python.exe -m pytest -q
```

`pipeline.py derive` regenerates player-map observations without downloading or reparsing. The fit scripts append records to [experiment-log.jsonl](experiment-log.jsonl); run them only for a deliberate new experiment. **Do not rerun `final_evaluation.py` or tune against the September final event.** Its one-time result is already recorded.

## Professional Y11 final operators

Before this investigation, 375 attacking player-rounds in the initial professional Y11 dataset were unresolved. The old parser enabled the action-start final-operator path only for the local UAH build at or after `Y11S3_Alpha04` (`9901603`); professional Y11S1/Y11S2 builds took the older parser path. Raw packet inspection found the structural 0-to-179 timer transition and final-header operator IDs before action start in all sampled builds and rounds. The parser now enables the existing action-start path for six verified earlier build IDs. The boundary algorithm itself was not changed. The valid Solid Snake numeric ID was also added to the operator table, supported by [Ubisoft's operator listing](https://www.ubisoft.com/en-us/game/rainbow-six/siege/game-info/operators/solid-snake).

After rebuilding and rederiving, the 420 current player-map rows have **zero unresolved final-operator rounds**. Read-only reparses of all three private UAH maps reproduced all 85 operator usage count rows exactly, including Lgon's corrected Attack distribution. `operator_diagnostics.py`, `analyze_operator_evidence.py`, and `verify_uah_operators.py` preserve the diagnostic and regression procedure. This coverage applies to the verified builds and current sample, not every future Siege build.

## Quality investigation

Of 122 excluded player-map rows, 121 have replay/public per-player K/D differences and two lack independent alias confirmation; one row has both issues. Most discrepancies transfer kills among players within a map. Forty of 42 maps have exactly matching map-wide kills and deaths. Europe MENA Stage 1 Chalet and North America Stage 1 Five Fears vs M80 Lair each differ by one replay kill. The Chalet replay includes a teamkill, but current evidence cannot prove how the public target counted it. `scoreboard_probe.py` and the opt-in Go scoreboard diagnostic found cumulative counters, but player-entity offsets vary across builds and maps. A separate `round_log_probe.py` matched all 453 replay/public round winners and compared 763 public multikill notes by unique round operator; 55 notes disagree with replay-derived kills. These independent notes reinforce the attribution issue, but are incomplete and cannot safely correct every kill. Neither probe rewrites kill events or relaxes quality gates. Two aliases remain unverified and excluded. The [quality audit](quality-report.md) lists every exclusion.

## Model experiments

The current nine families are KPR, teamkills, extra multikill kills, opening differential, successful 1vX clutches, KOST, survival, trade differential, and objectives. These are hypotheses about SiegeGG's definitions. Models are standardized ridge regressions with alpha 1. The trade baseline uses eight seconds. The exact splits, coefficients, predictions, thresholds, and dataset SHA-256 are in [experiment-log.jsonl](experiment-log.jsonl).

| Evaluation | Clean rows | Raw MAE | Raw RMSE | Within 0.05 | `collegiate_v1` MAE |
| --- | ---: | ---: | ---: | ---: | ---: |
| August EWC validation, separate event | 32 | 0.0353 | 0.0478 | 72% | 0.2615 |
| September Stage 2 final, evaluated once | 16 | 0.0632 | 0.0749 | 38% | 0.2124 |

The raw model trained on 118 clean rows from five earlier events. Operator-relative versions used training-only operator means and variances shrunk toward side baselines with 20 prior rounds; all three operator methods performed worse on August validation (MAE 0.0503, 0.0522, and 0.1094). Sixty-eight operators appear in training and 41 have fewer than 20 rounds. A controlled search over 12 metric-definition variants selected a weighted-clutch variant on grouped early-event cross-validation, but its August MAE of 0.0366 was worse than the raw baseline's 0.0353. No variant was selected based on the September result. The earlier nine-map experiment remains in the log as a historical benchmark, not an untouched test.

The raw model beats `collegiate_v1` on these public targets, but its September max error is 0.1553. The small final sample, weak teamkill support, and slightly negative objective coefficient make the fitted weights unsuitable for deployment. In particular, the model does not establish official operator normalization or exact trade, clutch, opening, multikill, or objective definitions. Keep `collegiate_v1` unchanged.

The [UAH comparison](uah_comparison.md) applies the frozen raw professional model to the three private maps and all 38 rounds without training on UAH data. It lists every player-map and season rating plus nine component contributions. It is a review artifact, not a proposed website update.

## Next evidence needed

Investigate kill attribution against independent round logs before admitting excluded rows. Acquire more distinct later events with verified player identities; reserve a new future event before fitting. Grow per-operator samples, especially rare operators and teamkills. Reassess operator-relative methods and metric definitions using grouped validation on the larger data. Only consider a non-default runtime candidate if a new untouched final event supports it. Do not publish or change the default rating without review.

The [official North America Stage 1 M80 vs DarkZero replay](https://www.ubisoft.com/en-us/esports/rainbow-six/siege/match/8016) is included after the [corresponding SiegeGG target](https://siege.gg/matches/4133-nal-na-m80-vs-darkzero-esports) became available. Its seven-round Kafe map matches the public 7–0 score and ten-player roster; eight player rows have exact public K/D. The two mismatched kill rows remain excluded. The earlier HTTP 500 was transient.

Four more official North America Stage 1 maps are included: M80 vs Five Fears Lair (9 clean rows), Shopify Rebellion vs DarkZero Clubhouse (5), M80 vs Wildcard Clubhouse (8), and DarkZero vs Cloud9 Nighthaven Labs (8). All 42 rounds match public team scores and resolve final operators. Ten rows with public/replay K/D differences remain excluded. JJBlaztful, Kanzen, and Bae94 handle variants have independent identity evidence in `sources.json`. The M80 vs Five Fears map adds a second map-wide one-kill discrepancy, now listed by the generated quality audit.

The official June 8–9 Europe MENA Stage 1 archives use replay build `9718747`, which had not been enabled for the action-start operator path. Raw inspection across four maps found the structural action marker in all 43 rounds and pre-action packets for all 215 attacker header operator IDs. Six initial attacker picks differ from the final header role, and no final roles are missing. The existing resolver was enabled for that exact build, and the rebuilt parser resolved all 215 final attacker operators without changing the action-start algorithm. A read-only reparse of all three private UAH maps preserved all 85 operator usage rows. G2 vs Geekay Fortress contributes 10 clean rows and Team Secret vs Heretics Lair contributes eight. The Virtus.pro vs Fnatic SiegeGG target lacks one replay player; the Falcons vs Twisted Minds target API omits the final round and reports 6–5 against the replay and Ubisoft 7–5. Those two archives remain cached but excluded from observations. The included maps' rosters, team scores, maps, round counts, and alias mappings passed the same gates as earlier sources.

Four additional North America Stage 1 maps contribute 23 clean rows: Outlast vs Cloud9 Fortress (4), 100 Thieves vs Five Fears Lair (8), For Fun vs Wildcard Fortress (6), and 100 Thieves vs Spacestation Fortress (5). The M80 vs Shopify and Spacestation vs DarkZero official ZIPs each contain two replay folders totaling 13 rounds against a 12-round public map; both remain cached and excluded pending independent identification of the extra round. Four earlier South America Stage 1 ZIPs were cached and ZIP-tested but the local parser panics at `dissect/stats.go:214` for every candidate folder while indexing a missing dynamic scoreboard player; they are also excluded. Their failures do not affect included maps.

Three July 2 North America maps add 21 clean rows: Five Fears vs Wildcard Bank (6), Shopify vs Spacestation Fortress (7), and Outlast vs 100 Thieves Lair (8). Cloud9 vs For Fun from the same day has two replay folders totaling 13 rounds against a 12-round public match and remains excluded. Four earlier June 18–19 North America archives were also excluded: two are fragmented with 13 or 11 physical rounds against 12 public, while two trigger the same `PlayerStats()` panic as the early South America archives. All rejected ZIPs are cached for later parser/source investigation.

The [official South America Stage 1 LOUD vs Black Dragons replay](https://www.ubisoft.com/en-us/esports/rainbow-six/siege/match/8551) adds a twelve-round Lair map with matching 7–5 score and ten-player roster. Eight player rows have exact public K/D. The Romeo/MRZLL and Gabu7z/Gabu identities have external evidence in `sources.json`; the two kill mismatches remain excluded.

Three July 5 South America maps add 24 clean rows: LOUD–FaZe (six), Imperial–Black Dragons (ten), and FURIA–Fluxo W7M (eight). All have exact map, score, roster, and round agreement, with zero unresolved Attack operators. The excluded rows differ in kill attribution. A separate FURIA–FaZe archive is cached but excluded because two rehost fragments total 13 replay rounds against the public 12-round map; the redundant round has not been verified.
