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

Five official Ubisoft replay ZIPs downloaded and cached (about 751 MiB compressed), parsed into nine maps. Public SiegeGG player-map target APIs were cached. See [research/README.md](../research/README.md) and [research/sources.json](../research/sources.json) for exact provenance and replay/game mappings. Nine maps yield 90 player-map observations; 57 pass exact K/D and round-count checks plus alias verification. Data, raw and normalized replay files, targets, and generated observations remain in ignored `data/research/`.

Experiment 1 is a standardized, ridge-regularized raw nine-family model. Training used 32 Kickoff rows. Held-out SI validation had 10 rows, MAE 0.033 and RMSE 0.044. The independent Stage 1 test first had five rows from one map (MAE 0.021) and was expanded **without refitting** to 15 rows from two maps (MAE 0.047). On the expanded holdout, 53% of ratings were within 0.05. The same expanded rows under `collegiate_v1` had MAE 0.232. The exact coefficients, split and accuracy thresholds are in [research/experiment-log.jsonl](../research/experiment-log.jsonl). These results establish that the collection/fit pipeline works, not that the formula is accurate enough for deployment.

Important unresolved issues: 33 rows fail quality gates; 375 Y11 attacker player-rounds in professional online replays have unresolved final operators; the Stage 1 test is much too small; trade, clutch, multikill, opening and objective definitions remain hypotheses. The model's teamkill coefficient is zero because none occurred in training, and the small negative objective coefficient is unstable. There is no trustworthy operator-relative fit yet, no `siege_style_v2` runtime model, and no UAH comparison report. `collegiate_v1` remains the only live rating and its formula was not changed. No publishing occurred.

The current professional data needs investigation before broad fitting: compare replay kill/death logs with SiegeGG map logs, independently verify Stage 1 aliases, and understand why Y11 professional attacker action-start snapshots are missing. Preserve current NECC action-start behavior. Acquire several additional distinct events for train/validation; reserve another later event for final untouched testing. Estimate operator baselines with per-operator sample counts and shrinkage only after final operators are trustworthy. Then compare candidate definitions and generate the requested per-player UAH map/season contribution report for review before any default change.

### Exact continuation commands

Run from the repository root in PowerShell:

```powershell
.\.venv\Scripts\python.exe research\pipeline.py all
.\.venv\Scripts\python.exe research\pipeline.py derive
.\.venv\Scripts\python.exe research\fit_baseline.py
.\.venv\Scripts\python.exe -m pytest -q
cd web
npm.cmd run build
npm.cmd run build:admin
```

`pipeline.py all` is cached and resumable. `fit_baseline.py` appends a new experiment record each time, so run it only for a deliberate experiment. Do not commit `data/research/`, `data/replay-archive/`, private SQLite/settings, `.rec`, or ZIP downloads. Do not publish or change the default rating without user review.
