## Current actor evidence: explicit timer components (2026-10-02)

Research-only temporal typed UID -> declared slot27c08dca/classb2216bf3 ->
timer property ownership binds112/113 consumed interaction spans. The mixed
4150/R11 span separates into two canceled Kason attempts and a Hotancold attempt
using explicit component state records. No actor is credited.

The 230 already-consumed objective-free rounds contain93 attempts across68rounds.
Two reach near zero and state2 despite no global plant flag: near-zero plus
state2 is **not** a completion rule. Keep the validated occurrence gate.
The observed state0/1 start and2 terminal semantics remain research hypotheses.
See [ownership alignment](output/objective-timer-owner-alignment.md),
[state runs](output/objective-timer-component-episodes-all-consumed.md),
[negative controls](output/objective-timer-negative-controls-all-consumed.md), and
[cancellation audit](output/objective-timer-cancellation-audit.md).

Independent [Fortress video review](output/objective-fortress-vod-review.md)
contradicts the original Raid target, but the explicit mandatory4139/R07 control
still remains actor-unresolved. J9O/njr remains independently unverified.
Frozen A and all three immutable validation results are unchanged. No live v2,
SQLite, archives, public data, production actor implementation, fit or publish.
Read the newest `docs/STATUS_NEXT_STEPS.md` checkpoint before continuing.

## Earlier actor-only research continuation (2026-10-02)

Frozen local combined diagnostic `cd28f76` has completed its one-shot five-map reserve:
plants3correct/0wrong/5unresolved; disables1correct/0wrong/1unresolved; no occurrence
mismatches. [Exact plan](objective-combined-plan.md), [result](output/objective-combined-reserve.md).
All sixty replay predictions preceded actor-label access. That reserve is now consumed;
do not reuse it as fresh validation. Deployed `siege_style_v2`, SQLite, archives and public
data remain untouched. Four resolved events are too small a sample for broad runtime
credit. Next audit unused source provenance and validate unchanged logic on another
distinct set. Read the newest `docs/STATUS_NEXT_STEPS.md` checkpoint.

## Previous actor-only research continuation (2026-10-01)

Deployed `siege_style_v2` remains frozen. New [liveness extension](output/objective-liveness.md), [development audit](output/objective-liveness-development.md), and [official VOD review](output/objective-vod-review.md) improve the diagnostic evidence without crediting any production actor. All datasets used for these diagnostics were already consumed. The five-map actor reserve remains unopened. Read the newest checkpoint in `docs/STATUS_NEXT_STEPS.md` before continuing.

The research observer reuses siege-dissect's existing kill/death offsets and captures timer strings. It does not modify the parser or decode kills independently. Rebuild only this separate ignored helper, then run the cached diagnostics from the repository root:

```powershell
Push-Location third_party/siege-dissect
& '..\..\.local-tools\go\bin\go.exe' build -o '..\..\.local-tools\bin\actor-feedback-probe.exe' '..\..\research\actor_feedback_probe.go'
Pop-Location
.\.venv\Scripts\python.exe research/objective_actor_liveness.py
.\.venv\Scripts\python.exe research/objective_liveness_development.py
```

These commands write only research reports and ignored diagnostics, including `data/research/diagnostics/objective-player-ledger-v2.json`. The optional VOD frame tool and its dependencies are documented in the VOD report; they are not needed for the application or liveness audits. Do not re-run rating fits, export website data, update SQLite, or publish as part of this work.

# SiegeGG-style rating research

Latest objective work: the frozen occurrence rule passed [twelve independent maps](output/objective-occurrence-validation.md) (32 plants, 12 disables, 92 negative rounds; no errors). Go now emits separate occurrence metadata with unresolved actors. Production parity passed 415 professional rounds without changing existing gameplay fields. The [five-map read-only UAH audit](output/uah-objective-audit.md) found 17 plants / three disables and preserved all tracked operators. Player attribution remains unsolved, so Rating observations and coefficients are unchanged. See [objective coverage](objective-coverage.md).

This research was conducted separately from the tracker. Its frozen eight-feature model was later approved for deployment as `siege_style_v2`; `collegiate_v1` remains available as a historical formula. Neither is an official SiegeGG formula. [SiegeGG's rating rebalance explanation](https://siege.gg/news/946-player-rating-rebalance) identifies nine metric families and operator-relative comparisons, but does not publish its exact implementation.

## Data and reproducibility

The cached dataset contains 56 complete logical maps from ten named events and 560 player-map observations. **407 rows pass strict gates** for map, score, roster, round count, exact public K/D, and alias evidence. Seven North America Stage 2 maps contribute 60 clean rows and are [reserved event-wide](final-test-reservation.json) for a future untouched final evaluation. Sixteen clean Europe MENA Stage 2 rows were evaluated once earlier and are now a historical benchmark. The other 153 rows remain excluded; see the [quality audit](quality-report.md) for each row and cause. The [source manifest](sources.json) records official replay URLs, exact replay-folder to SiegeGG game mappings, public player IDs, and independently verified alias evidence.

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

The later September North America replay build `9883691` needed the same exact-build gate. Its 25 audited rounds all contain a structural action-start marker and the final attacker operator ID before it for all 125 attacker player-rounds; 80 initial operator headers differ from final roles. June 18 North America build `9734089` also changed two player identity packet markers; after matching those observed bytes, all 24 physical rounds in two split archives parse, each has the action-start marker, and all 120 attacker player-rounds have pre-action final operator IDs. The existing boundary logic was not changed. Across the current 56-map dataset there are **zero unresolved final-operator rounds**. Read-only reparses of all three private UAH maps reproduced all 85 operator usage count rows exactly, including Lgon's corrected Attack distribution. `operator_diagnostics.py`, `analyze_operator_evidence.py`, and `verify_uah_operators.py` preserve the diagnostic and regression procedure. This coverage applies to the verified builds and current sample, not every future Siege build.

## Quality investigation

Of 153 excluded player-map rows, 152 have replay/public per-player K/D differences and two lack independent alias confirmation; one row has both issues. Most discrepancies transfer kills among players within a map. Fifty-three of 56 maps have exactly matching map-wide kills and deaths. Three maps differ by one replay kill. `scoreboard_probe.py` and the opt-in Go scoreboard diagnostic found cumulative counters, but player-entity offsets vary across builds and maps. A separate `round_log_probe.py` matched all 605 replay/public round winners and compared 1023 public multikill notes by unique round operator; 74 notes disagree with replay-derived kills. These independent notes reinforce the attribution issue, but are incomplete and cannot safely correct every kill. Neither probe rewrites kill events or relaxes quality gates. Two aliases remain unverified and excluded. The [quality audit](quality-report.md) lists every exclusion.

## Model experiments

The current nine families are KPR, teamkills, extra multikill kills, opening differential, successful 1vX clutches, KOST, survival, trade differential, and objectives. These are hypotheses about SiegeGG's definitions. Models are standardized ridge regressions with alpha 1. The trade baseline uses eight seconds. The exact splits, coefficients, predictions, thresholds, and dataset SHA-256 are in [experiment-log.jsonl](experiment-log.jsonl).

| Evaluation | Clean rows | Raw MAE | Raw RMSE | Within 0.05 | `collegiate_v1` MAE |
| --- | ---: | ---: | ---: | ---: | ---: |
| August EWC validation, separate event | 32 | 0.0353 | 0.0478 | 72% | 0.2615 |
| September Stage 2 final, evaluated once | 16 | 0.0632 | 0.0749 | 38% | 0.2124 |
| Expanded 266-row raw fit, August development validation | 32 | 0.0346 | 0.0466 | 72% | 0.2615 |

The raw model trained on 118 clean rows from five earlier events. Operator-relative versions used training-only operator means and variances shrunk toward side baselines with 20 prior rounds; all three operator methods performed worse on August validation (MAE 0.0503, 0.0522, and 0.1094). Sixty-eight operators appear in training and 41 have fewer than 20 rounds. A controlled search over 12 metric-definition variants selected a weighted-clutch variant on grouped early-event cross-validation, but its August MAE of 0.0366 was worse than the raw baseline's 0.0353. No variant was selected based on the September result. The earlier nine-map experiment remains in the log as a historical benchmark, not an untouched test.

The raw model beats `collegiate_v1` on these public targets, but its September max error is 0.1553. The small final sample, weak teamkill support, and slightly negative objective coefficient make the fitted weights unsuitable for deployment. In particular, the model does not establish official operator normalization or exact trade, clutch, opening, multikill, or objective definitions. Keep `collegiate_v1` unchanged.

The preregistered expanded raw fit [recorded in the experiment log](experiment-log.jsonl) uses 266 clean rows from seven pre-August events and the previously viewed August EWC event for development validation. Its August MAE is 0.03464 versus 0.03528 for the earlier 118-row fit; both have 72% of ratings within 0.05. The new training set contains eight teamkill events, moving that raw-unit slope from +0.052 to -0.211. The objective raw-unit slope moved from -0.107 to -0.008. These unstable or near-zero terms still need investigation. No North America Stage 2 Rating residual was calculated, and that event remains untouched.

The later fixed-form provisional refit after admitting four rehosts and removing false objective credits has 292 earlier-event training rows and 32 previously viewed August validation rows. Its August MAE is 0.03484 (RMSE 0.04632, 72% within 0.05), versus 0.03466 when applying the prior 266-row model to the same safeguarded validation inputs. The objective feature is now constant zero and its coefficient is unidentified. Leave-one-earlier-event-out checks give raw MAE 0.03659 versus best operator-relative MAE 0.05215; raw wins all seven folds. These are development diagnostics only, not evidence to deploy a new rating or to evaluate the reserved final event.

The predeclared [June NAL rehost refit](nal-rehost-refit-plan.json) added seven exact K/D player rows for 299 earlier-event training observations. Its same-form raw ridge gives previously viewed August EWC MAE 0.03453 (RMSE 0.04626; 72% within 0.05), versus 0.03484 for the prior 292-row fit on the same validation data. All varying raw-unit slopes changed by less than 0.007. Grouped earlier-event MAE is 0.03647 for raw versus 0.05288 for the best operator-relative method, with raw best on all seven folds. The objective coefficient remains unidentified because the safeguarded feature is constant zero. These are provisional development results; the reserved North America Stage 2 Rating targets remain unevaluated.

A development-only leave-one-event-out check on the seven pre-August events gives pooled MAE 0.03665 for raw features, 0.05266 for weighted operator means, 0.05872 for round-normalized operator features, and 0.10827 for operator-segment normalization. Raw wins every event fold. Of 70 operator-side groups, 23 have fewer than 20 training rounds; only five held-out player-rounds use an unseen operator. These results do not support operator-relative normalization in this sample.

The [objective coverage diagnostic](objective-coverage.md) finds a large mismatch even on K/D-clean development rows: the earlier 266 pre-August rows contain 55 public plants and seven public disables, while the old replay adapter counted only 23 plants and one disable. A deeper audit found every one of 42 emitted plant events assigned to a defender and all five emitted disables credited to a different actor than the public round log. The Y11 defuser timer listener uses a stale player identity offset. The adapter now omits these unverified events from newly derived research data; all 55 maps were rederived and there are zero counted objectives until reliable actor extraction is implemented. This safeguards attribution but leaves the objective feature unusable for model interpretation. The private NECC database was inspected read-only and still contains 12 defender-credited plants and one potentially misattributed disable; it was not modified. A non-rating objective-count probe briefly looked at reserved September maps before this audit; that exposure is [recorded](final-test-reservation.json). Their Rating targets and residuals remain unexamined.

The later [predeclared packet validation](objective_actor_validation_plan.md) rejected a narrower +100-score actor rule: one held-out planter was assigned to another player, and three near-zero timer runs had no public objective event. These were non-reserved development maps. No objective actor rule was promoted to the parser, and the reserved final Rating event remains sealed.

Five previously excluded professional [rehost maps](rehosts.md) have a unique score-continuous logical-round reconstruction: each official ZIP has 13 physical rounds across two folders, and the second folder resumes from the score before the first folder's last round. Excluding that one abandoned physical round produces 12 logical rounds and the exact public final score. Four have matching map-wide K/D; the fifth is one replay kill short and contributes only seven exact per-player rows. A reusable logical map layer preserves every segment and source mapping. The five maps now enter the reproducible research pipeline, adding 33 clean rows without loosening any quality gate. Another split archive has a missing physical round and remains excluded. The dataset is now 56 maps, 560 player-map rows, and 407 clean rows; 60 clean September North America rows remain reserved and unevaluated.

The [UAH comparison](uah_comparison.md) applies the frozen raw professional model to the three private maps and all 38 rounds without training on UAH data. It lists every player-map and season rating plus nine component contributions. It is a review artifact, not a proposed website update.

## Next evidence needed

Investigate kill attribution against independent round logs before admitting excluded rows. The full North America League Stage 2 event is now reserved as the untouched final event; its current seven maps provide 60 clean rows. The [expanded development fit plan](expanded-fit-plan.json) uses seven earlier events for training and the previously viewed August EWC event for validation. Neither September event enters selection. Grow per-operator samples, especially rare operators and teamkills. Only consider a non-default runtime candidate if the new untouched final event supports it. Do not publish or change the default rating without review.

The seven September North America maps all match the official and SiegeGG map, score, round, and roster records. They add 60 clean rows and ten excluded per-player K/D mismatches. Their source entries are explicitly marked `reserved_for_final_test`; the pipeline rejects any entry from that event without the flag. The reservation was committed before any candidate Rating residual was inspected. Cached targets contain public ratings for eventual one-time evaluation, but the current development scripts exclude those rows.

The [official North America Stage 1 M80 vs DarkZero replay](https://www.ubisoft.com/en-us/esports/rainbow-six/siege/match/8016) is included after the [corresponding SiegeGG target](https://siege.gg/matches/4133-nal-na-m80-vs-darkzero-esports) became available. Its seven-round Kafe map matches the public 7–0 score and ten-player roster; eight player rows have exact public K/D. The two mismatched kill rows remain excluded. The earlier HTTP 500 was transient.

Four more official North America Stage 1 maps are included: M80 vs Five Fears Lair (9 clean rows), Shopify Rebellion vs DarkZero Clubhouse (5), M80 vs Wildcard Clubhouse (8), and DarkZero vs Cloud9 Nighthaven Labs (8). All 42 rounds match public team scores and resolve final operators. Ten rows with public/replay K/D differences remain excluded. JJBlaztful, Kanzen, and Bae94 handle variants have independent identity evidence in `sources.json`. The M80 vs Five Fears map adds a second map-wide one-kill discrepancy, now listed by the generated quality audit.

The official June 8–9 Europe MENA Stage 1 archives use replay build `9718747`, which had not been enabled for the action-start operator path. Raw inspection across four maps found the structural action marker in all 43 rounds and pre-action packets for all 215 attacker header operator IDs. Six initial attacker picks differ from the final header role, and no final roles are missing. The existing resolver was enabled for that exact build, and the rebuilt parser resolved all 215 final attacker operators without changing the action-start algorithm. A read-only reparse of all three private UAH maps preserved all 85 operator usage rows. G2 vs Geekay Fortress contributes 10 clean rows and Team Secret vs Heretics Lair contributes eight. The Virtus.pro vs Fnatic SiegeGG target lacks one replay player; the Falcons vs Twisted Minds target API omits the final round and reports 6–5 against the replay and Ubisoft 7–5. Those two archives remain cached but excluded from observations. The included maps' rosters, team scores, maps, round counts, and alias mappings passed the same gates as earlier sources.

Four additional North America Stage 1 maps contribute 23 clean rows: Outlast vs Cloud9 Fortress (4), 100 Thieves vs Five Fears Lair (8), For Fun vs Wildcard Fortress (6), and 100 Thieves vs Spacestation Fortress (5). The M80 vs Shopify and Spacestation vs DarkZero official ZIPs each contain two replay folders totaling 13 rounds against a 12-round public map; both remain cached and excluded pending independent identification of the extra round. Four earlier South America Stage 1 ZIPs were cached and ZIP-tested but the local parser panics at `dissect/stats.go:214` for every candidate folder while indexing a missing dynamic scoreboard player; they are also excluded. Their failures do not affect included maps.

Three July 2 North America maps add 21 clean rows: Five Fears vs Wildcard Bank (6), Shopify vs Spacestation Fortress (7), and Outlast vs 100 Thieves Lair (8). Cloud9 vs For Fun from the same day has two replay folders totaling 13 rounds against a 12-round public match and remains excluded. Four earlier June 18–19 North America archives were also excluded: two are fragmented with 13 or 11 physical rounds against 12 public, while two trigger the same `PlayerStats()` panic as the early South America archives. All rejected ZIPs are cached for later parser/source investigation.

Shopify vs Outlast Fortress and For Fun vs Five Fears Bank on July 3 add another 16 clean rows, reaching 314 clean player-map rows. The two maps have complete replay rounds and exactly matching public maps, scores, rosters, and aliases. Four remaining per-player K/D differences stay excluded. This passes the first 300-row collection target. The next gate is a later distinct event reserved for a new untouched final evaluation before further model selection; September Europe MENA Stage 2 was already evaluated and remains historical only.

The [official South America Stage 1 LOUD vs Black Dragons replay](https://www.ubisoft.com/en-us/esports/rainbow-six/siege/match/8551) adds a twelve-round Lair map with matching 7–5 score and ten-player roster. Eight player rows have exact public K/D. The Romeo/MRZLL and Gabu7z/Gabu identities have external evidence in `sources.json`; the two kill mismatches remain excluded.

Three July 5 South America maps add 24 clean rows: LOUD–FaZe (six), Imperial–Black Dragons (ten), and FURIA–Fluxo W7M (eight). All have exact map, score, roster, and round agreement, with zero unresolved Attack operators. The excluded rows differ in kill attribution. A separate FURIA–FaZe archive is cached but excluded because two rehost fragments total 13 replay rounds against the public 12-round map; the redundant round has not been verified.
# Latest controlled experiments (2026-10-01)

Objective occurrence is validated; player attribution remains unavailable. The latest [actor decision](output/objective-actor-decision.md) rejects a structurally bound score-residual rule because it still credits Aiden instead of Raid in 4139 R07. Player objectives remain excluded from Rating experiments.

Preregistered [multikill](output/multikill-experiment.md) and [opening](output/opening-experiment.md) experiments did not establish improvements over the existing raw baseline. Saved-model [residual analysis](output/development-residuals.md) documented systematic underprediction among publicly objective-credited players without using those credits as features. The NA Stage2 final ratings were still sealed at this stage; the later evaluation is recorded below. See the newest section of `docs/STATUS_NEXT_STEPS.md` before running commands below; do not rerun already recorded fits.

## Frozen candidate and completed final evaluation (2026-10-01)

The later [trade audit](output/trade-semantics-audit.md), [trade window](output/trade-window-experiment.md), [trade representation](output/trade-definition-experiment.md), [KOST/survival](output/kost-survival-experiment.md), and [clutch](output/clutch-experiment.md) studies retained the eight-family raw baseline. The [pre-freeze review](output/pre-freeze-review.md) selected it, and [frozen-rating-candidate.json](frozen-rating-candidate.json) was committed at `eb747f8` before any reserved NA evaluation. The reserved event was then evaluated exactly once: 60 clean rows / seven maps, MAE 0.03623 versus 0.23875 for `collegiate_v1` on identical rows. The [final report](output/final-na-rating-evaluation.md) and [deployment review](output/rating-deployment-review.md) include limitations, especially unresolved player objective credit. The 60-row NA event is now **consumed** as a final test and cannot be used to tune a revised model while retaining that designation. The later approved deployment changed the configured runtime default to `siege_style_v2`; this research itself did not rewrite the local match database.
