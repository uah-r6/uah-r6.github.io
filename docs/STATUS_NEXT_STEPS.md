# Status and next steps — 2026-09-30

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

Eleven distinct official Ubisoft replay ZIPs are cached and matched to public SiegeGG targets: 24 complete maps across seven named events, yielding 240 player-map observations. **166 pass strict quality gates.** All currently derived final-operator rounds resolve. Sixteen clean rows from two September Stage 2 maps were reserved for one final evaluation. Downloads, normalized rounds, targets, and observations stay under ignored `data/research/`. Exact provenance, replay/game mappings, and alias evidence are in [research/sources.json](../research/sources.json).

The professional Y11 operator failure was a parser version gate: six earlier verified online builds took the legacy path despite containing the same structural action-start marker and pre-action final operator IDs used by the current UAH build. The existing action-start boundary logic was enabled for those builds; Solid Snake's valid numeric operator ID was added. The original 375 unresolved attacker player-rounds are now resolved, and read-only reparses of all three UAH maps exactly matched their prior 85 operator usage counts. No private map was reimported.

The [quality audit](../research/quality-report.md) lists all 74 excluded observations: 73 have per-player public/replay K/D discrepancies; two lack independent alias confirmation (one overlaps). Twenty-three of 24 map-wide kill/death totals match. Public round logs align on all 261 winners; 35 of 431 multikill notes disagree with replay-derived round kills. Cumulative scoreboard counters were found but their player offsets are not yet reliable enough to correct event attribution. Quality gates were not relaxed.

The new raw nine-family ridge model trained on 118 clean rows from five earlier events. August EWC validation has 32 clean rows: MAE 0.0353, RMSE 0.0478, 72% within 0.05, versus `collegiate_v1` MAE 0.2615. Operator-relative variants with 20-round shrinkage all performed worse. A controlled metric-definition search did not improve independent August validation. The frozen raw model was evaluated once on September Stage 2's 16 clean rows: MAE 0.0632, RMSE 0.0749, 38% within 0.05, maximum error 0.1553, versus `collegiate_v1` MAE 0.2124. Full split, coefficients, thresholds, and dataset hash are in [experiment-log.jsonl](../research/experiment-log.jsonl). The September result is too small and weak to justify deployment. **Do not tune on or rerun this final event.**

The [UAH comparison report](../research/uah_comparison.md) gives per-player map and season experimental ratings and nine component contributions for the current 38 rounds. UAH results were never used to fit the model. `collegiate_v1` remains the only live/default rating, and no website publishing occurred. See [research/README.md](../research/README.md) for definitions, reproducibility, and limits.

Next: independently resolve replay/public kill attribution where possible; add distinct events with verified aliases; reserve a new later untouched final event before further fitting; build more stable operator baselines and teamkill support. Do not implement a runtime candidate or change the default until new held-out evidence supports it.

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
