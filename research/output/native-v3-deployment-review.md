# Passing v3 UAH deployment review

No UAH fitting. Historical tables, original v2 snapshots, all display statistics and raw replays are unchanged. V3 requires whole-map credited/core objective/native parity. All 82 historical display rounds remain; only 42 rounds across four maps contribute to Rating.

Runtime/research maximum difference 0, 240 comparisons (tracked rounds, maps, season and career).

| Player | Rating | Eligible rounds | Maps |
| --- | ---: | ---: | ---: |
| AzoozNewzz | 1.082885288 | 42 | 4 |
| DinoFireKing | 0.764537724 | 42 | 4 |
| Lgon | 1.441310153 | 42 | 4 |
| OhWowJay | 1.581421174 | 42 | 4 |
| Tallman3.14 | 0.852978563 | 42 | 4 |

## Whole-map eligibility

| Map | ID | Eligible | Reason |
| --- | --- | --- | --- |
| Fortress | d64d5478cdb3 | True | Complete validated inputs |
| Border | 8a6357ff307c | False | Objective credits lack complete unique core occurrence evidence. |
| Kafe Dostoyevsky | 5adc26f7a402 | False | Objective credits lack complete unique core occurrence evidence. |
| Border | 076d2b6b02bc | True | Complete validated inputs |
| Chalet | b595ffaaec57 | False | Incomplete credited-kill evidence |
| Border | 8af0a6db6c39 | True | Complete validated inputs |
| Nighthaven Labs | 9db26f1b6ca7 | True | Complete validated inputs |

No parser or operator/action-start logic change. Native finisher opening is not credited-owner opening. Legacy trades remain frozen at 8 seconds. Larger independent events, precise credited event ownership/timing, and unsupported objective compatibility remain future work.

## Implementation verification

543 Python tests passed, one optional real-replay smoke skipped, six subtests passed. Go tests including Y11 and go vet passed. Public and admin builds passed. Exact v2 map/season/career exports reproduce all historical values; only methodology text changed. The current source/table/archive/public guard passes all 20 documents.

The actual quoted CMD launcher restarted the outdated server, imported current repository source through .venv Python, and opened the default browser. Live local API reports siege_style_v3. Headless Edge verifies admin Settings plus public Lgon/methodology rendering, exact coverage text, Rating1.44 and zero page errors. Evidence is private/ignored.

The verified before.sqlite, before-settings.json and before-public backups provide local rollback after stopping the server; restore them to their original locations. Raw archives never move. New v3 core occurrence evidence is private and bound to fingerprint/normalized SHA; stale evidence is invalidated automatically after reparse or objective refresh. New imports reuse stored normalized/core and Go credited/native evidence without a separate workflow.

## Deployment and live verification

Deployment commit6ae184a is pushed. GitHub Pages [run37580585635](https://github.com/uah-r6/uah-r6.github.io/actions/runs/37580585635) completed successfully. At2026-10-07T06:22:12UTC, all20JSON documents matched committed LF bytes at both normal and cache-busted URLs and decoded local exports. All5players' season/career pages and methodology rendered correct v3 Ratings and42/82round,4/7map coverage, with zero JavaScript page errors. Credited counts, current objective corrections, historical table snapshots, archive bytes and v2 reproducibility remain verified; no private fields or paths appear in public data. Evidence: research/native-v3-live-checkpoint.json. Current guard passes after all verification. Authorized stop condition reached.
