# Status and next steps — 2026-09-30

## CURRENT RATING RESEARCH CHECKPOINT — 2026-09-30 14:28 UTC

- HEAD before this checkpoint: `dcd3172`. Keep this section current after each research milestone and commit code/documentation locally. Do not push or publish.
- Fitted data: 26 complete maps, 260 player-map rows, 182 clean rows, nine parsed events. All current operator rounds resolve. September Stage 2's 16 rows were evaluated once and are now a historical benchmark.
- Fully parsed and target-matched events: Six Invitational 2026, Asia Pacific Kickoff 2026, Salt Lake City Major 2026, Asia Pacific League Stage 1 2026, Europe MENA League Stage 1 2026, Esports World Cup 2026, Europe MENA League Stage 2 2026, North America League Stage 1 2026, and South America League Stage 1 2026. Thirteen distinct ZIPs back their 26 included maps.
- North America Stage 1 addition: official M80–DarkZero July 2 ZIP `BR62026_NAL_S1D8_DZvM80.zip`, replay folder `Match-2026-07-02_15-28-09-4828`, SiegeGG match `4133` / game `7860`, Kafe 7–0. Both targets cached; 8 of 10 rows pass exact K/D; 2 excluded for kill attribution differences. Previous HTTP 500 was transient. No event is currently awaiting target matching.
- Excluded within matched data: 78 player-map rows, mostly per-player K/D discrepancies, plus two unverified aliases; see `research/quality-report.md`. No event has been rejected in full.
- Best current validation: raw nine-family ridge `grouped-operator-20260930T103355Z`, August EWC 32 rows, MAE 0.0353. Operator-relative variants were worse. Historical September Stage 2 benchmark: 16 rows, MAE 0.0632; do not tune on it. `collegiate_v1` remains live and unchanged.
- South America Stage 1: official [LOUD–Black Dragons July 4 match](https://www.ubisoft.com/en-us/esports/rainbow-six/siege/match/8551) archive `BR62026_SAL_S1D7_LOUDvBD.zip`, replay `Match-2026-07-04_12-56-31-39776`, SiegeGG match `4112` / game `8360` was fully matched: Lair 12 rounds, 7–5, ten players, zero unresolved Attack operators; eight player rows passed exact public K/D, two remain excluded. `ROMEO.BD` ↔ `MRZLL` and `Gabu7z.LOUD` ↔ `GABU` alias evidence is recorded in `sources.json`.
- Source discovery helper `research/preflight_ubisoft.py` scanned official match IDs 8545–8560 and cached all pages. Four July 4–5 South America candidates have exact SiegeGG match pages and HTTP 200 player-stats targets: FURIA–FaZe (Ubisoft 8554 / SiegeGG 4115), LOUD–FaZe (8557 / 4118), Imperial–Black Dragons (8558 / 4119), FURIA–Fluxo W7M (8559 / 4120).
- The new `research/collect_candidates.py` cached/ZIP-verified/extracted the FURIA–FaZe archive and both targets. Its Clubhouse replay is fragmented across two folders: 8 rounds with 4–4 score and 5 rounds with 2–3 score, totaling 13 versus the public 7–5/12 rounds. Exclude this candidate until the rehost/duplicate round can be independently identified; do not guess or merge it into observations. Cache is retained under ignored `data/research/`.
- Three further South America ZIPs and their SiegeGG target pairs are cached and ZIP-verified via `collect_candidates.py`. Each contains one complete parsed map with zero unresolved Attack operators: LOUD–FaZe official 8557 / SiegeGG 4118 game 8666, Nighthaven Labs 10 rounds 7–3, folder `Match-2026-07-05_11-17-25-19616`; Imperial–Black Dragons 8558 / 4119 game 8672, Lair 10 rounds 3–7, folder `Match-2026-07-05_12-16-14-19616`; FURIA–Fluxo W7M 8559 / 4120 game 8673, Kafe 10 rounds 3–7, folder `Match-2026-07-05_13-23-50-19616`. None is in fitted data yet. Replay `LOBEX.FX` has profile UUID `8d24a413-c6d6-4aa6-a0df-5781887b7ea2`; public stats.cc history identifies the same account as Lobin, supporting target `L0BINN`.
- **NEXT ACTION:** Add exact replay-to-SiegeGG player-ID maps for the three complete South America matches to `research/sources.json`, record verified aliases, run `pipeline.py all` and `quality_report.py`, then checkpoint clean-row counts. Keep September out of model selection.

## Part 1: private replay archive

Implemented and tested. Confirmed imports through the CLI or local admin create a private, map-ID keyed copy in `data/replay-archive/<season-slug>/<map-id>/` after SQLite import succeeds. A staging copy is made first, then verified against the import fingerprint before it becomes a completed archive. Rejected, preview-only, and failed imports do not produce a completed archive. The original MatchReplay folder is never moved. The manifest contains replay identity, original source/folder, parser binary hash, map, round count, physical R## filenames, sizes, and SHA-256 digests.

The admin map page shows archive status, Verify, Open in Explorer, Backfill older map, and Reparse from archive. Reparse checks archive integrity and replay identity before the existing transactional map replacement. Metadata, roster identities, and map ID remain intact. The map delete confirmation explicitly covers both statistics and the archived replay; the archive is parked while database deletion runs and restored if database deletion fails. No SQLite schema migration was needed. Public export contains no archive metadata. Publishing stages only `web/public/data/**/*.json`.

The three existing Fall 2026 NECC maps were backfilled from their exact fingerprint-matching source folders without changing stored statistics:

| Map | Map ID | Rounds | Archive status |
| --- | --- | ---: | --- |
| Fortress | `d64d5478cdb3` | 10 | Healthy |
| Border | `8a6357ff307c` | 14 | Healthy |
| Kafe Dostoyevsky | `5adc26f7a402` | 14 | Healthy |

The private archive currently occupies roughly 368 MiB and is ignored by Git. Keep a backup of both `data/r6stats.sqlite` and `data/replay-archive/` for machine failure recovery. Archive and research paths passed `git check-ignore`. The publishing test confirms only generated public JSON is staged, even with a private replay present.

Files: `.gitignore`, `r6stats/replay_archive.py`, `r6stats/cli.py`, `r6stats/admin/server.py`, `web/src/admin.tsx`, `web/src/admin.css`, `tests/test_replay_archive.py`, `tests/test_admin.py`, `tests/test_import.py`, `tests/test_publishing.py`, and `README.md`. The small nil-UUID identity fix and Consulate map label are in `r6stats/parser/models.py`, `r6stats/parser/siege_dissect.py`, and `tests/test_lan_player_identity.py`.

Verification: 49 Python tests passed, one optional real-replay smoke test skipped, six subtests passed. Both public and admin Vite builds passed. The three real archives each verified Healthy after all changes. A live launcher/browser click-through was not performed in this session; admin endpoints were exercised by TestClient. No website publish was attempted.

## Part 2: SiegeGG-style rating research

Thirteen distinct official Ubisoft replay ZIPs are cached and matched to public SiegeGG targets: 26 complete maps across nine named events, yielding 260 player-map observations. **182 pass strict quality gates.** All currently derived final-operator rounds resolve. Sixteen clean rows from two September Stage 2 maps were reserved for one final evaluation and are now a historical benchmark. Downloads, normalized rounds, targets, and observations stay under ignored `data/research/`. Exact provenance, replay/game mappings, and alias evidence are in [research/sources.json](../research/sources.json).

The professional Y11 operator failure was a parser version gate: six earlier verified online builds took the legacy path despite containing the same structural action-start marker and pre-action final operator IDs used by the current UAH build. The existing action-start boundary logic was enabled for those builds; Solid Snake's valid numeric operator ID was added. The original 375 unresolved attacker player-rounds are now resolved, and read-only reparses of all three UAH maps exactly matched their prior 85 operator usage counts. No private map was reimported.

The [quality audit](../research/quality-report.md) lists all 78 excluded observations: 77 have per-player public/replay K/D discrepancies; two lack independent alias confirmation (one overlaps). Twenty-five of 26 map-wide kill/death totals match. Public round logs align on all 280 winners; 38 of 464 multikill notes disagree with replay-derived round kills. Cumulative scoreboard counters were found but their player offsets are not yet reliable enough to correct event attribution. Quality gates were not relaxed.

The new raw nine-family ridge model trained on 118 clean rows from five earlier events. August EWC validation has 32 clean rows: MAE 0.0353, RMSE 0.0478, 72% within 0.05, versus `collegiate_v1` MAE 0.2615. Operator-relative variants with 20-round shrinkage all performed worse. A controlled metric-definition search did not improve independent August validation. The frozen raw model was evaluated once on September Stage 2's 16 clean rows: MAE 0.0632, RMSE 0.0749, 38% within 0.05, maximum error 0.1553, versus `collegiate_v1` MAE 0.2124. Full split, coefficients, thresholds, and dataset hash are in [experiment-log.jsonl](../research/experiment-log.jsonl). The September result is too small and weak to justify deployment. **Do not tune on or rerun this final event.**

The [UAH comparison report](../research/uah_comparison.md) gives per-player map and season experimental ratings and nine component contributions for the current 38 rounds. UAH results were never used to fit the model. `collegiate_v1` remains the only live/default rating, and no website publishing occurred. See [research/README.md](../research/README.md) for definitions, reproducibility, and limits.

Next: independently resolve replay/public kill attribution where possible; add distinct events with verified aliases; reserve a new later untouched final event before further fitting; build more stable operator baselines and teamkill support. Do not implement a runtime candidate or change the default until new held-out evidence supports it.

The North America Stage 1 M80–DarkZero ZIP was downloaded and integrity-checked in ignored research storage. Its seven-round Kafe replay parses with both rosters and zero unresolved Attack operators. SiegeGG's corresponding target recovered from a transient HTTP 500. The match was added to `sources.json` with exact map and roster mapping; eight player rows passed quality gates, and two kill mismatches remain excluded.

The South America Stage 1 LOUD–Black Dragons ZIP was also added: one twelve-round Lair map, 7–5, with eight exact K/D rows and two excluded kill-attribution differences. The ambiguous Romeo/MRZLL and Gabu7z/Gabu names have independent roster/profile evidence recorded in the source manifest.

### Exact continuation commands

Run from the repository root in PowerShell:

```powershell
.\.venv\Scripts\python.exe research\pipeline.py all
.\.venv\Scripts\python.exe research\pipeline.py derive
.\.venv\Scripts\python.exe research\quality_report.py
.\.venv\Scripts\python.exe -m pytest -q
cd web
npm.cmd run build
npm.cmd run build:admin
```

`pipeline.py all` is cached and resumable. Fit scripts append experiment records, so run them only for deliberate new experiments. The recorded September final evaluation must not be rerun or used for tuning. Do not commit `data/research/`, `data/replay-archive/`, private SQLite/settings, `.rec`, or ZIP downloads. Do not publish or change the default rating without user review.
