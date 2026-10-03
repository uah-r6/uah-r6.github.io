# Verified historical objective migration - 2026-10-03

## Root cause and data flow

Fresh parsing and archive reparse use `parse_match` -> installed `.local-tools/bin/siege-dissect.exe` -> `normalize`. The approved resolver is `completing_timer_owner_v1` in `dissect/objective_actor.go` (core source f534b31, production boundary 7d4bc8a). The adapter requires matching numeric UID, complete unique ten-player roster, correct side, occurrence source and defense winner for disables. Trusted occurrences produce both normalized occurrence metadata and `Objective` rows. `insert_map` / `reparse_map` persist `maps.normalized_json` plus `rounds`, `round_players`, `kill_events` and `objective_events`. Player objective totals are derived, not stored aggregates. `calculate_match` reads the normalized objectives; `export` aggregates map/season/career values into sanitized public JSON.

Admin Recalculate only calls export against stored normalized maps. Regenerate also calls export. Publish exports/builds/commits/pushes this data. None reparses archives. The old actor was therefore retained in SQLite: older maps had wrong-side legacy actors, while Michigan Border had occurrence metadata without player objective rows. Recalculate could not discover the new actor.

## Approved parser and read-only audit

Built exactly git 7d4bc8a under ignored research storage; binary SHA256 `2508a9b37188e09b58e0b0d2d4e6aa20ffc6fb5b3d832ce5cac8b56cf3dadf31`. Installed binary SHA256 `22cfe0f12a36addc6e1d4fa4afe13fb63ce12931470cb2ab2ce40d37c24f93d1`; its Michigan occurrence/actor output matched the isolated approved build exactly. All physical archive hashes verified. Five maps / 62 logical rounds / 20 current occurrences: 15 supported plants and 3 supported disables; 2 unsupported plants retained without corrections. The default binary includes separately callable credited-kill research files, but default actor/runtime source is unchanged from 7d4bc8a. Migration used the isolated approved build anyway.

## Every objective: SQLite actor vs approved parser

Category A was applied; C/D were retained. Logical/physical round and segment are explicit. All rows have a detected occurrence. Raw numeric UIDs, timer-owner entities, completion intervals, terminals, side, reason and exact parser JSON are retained in ignored `data/research/objective-migration/preview.json` and content-addressed raw JSON.

| Map / ID | Logical / physical / segment | Type | Stored actor | Approved actor | Side | Category / reason |
| --- | --- | --- | --- | --- | --- | --- |
| Fortress / d64d5478cdb3 | 7 / 7 / 1 | plant | Kenbot.USU | Lgon. | Attack | A / completing_timer_owner_v1 |
| Fortress / d64d5478cdb3 | 8 / 8 / 1 | plant | Kenbot.USU | Tallman3.14 | Attack | A / completing_timer_owner_v1 |
| Border / 8a6357ff307c | 5 / 5 / 1 | plant | Lxgacy.MAV | DinoFireKing | Attack | A / completing_timer_owner_v1 |
| Border / 8a6357ff307c | 6 / 6 / 1 | plant | Lxgacy.MAV | AzoozNewzz | Attack | A / completing_timer_owner_v1 |
| Border / 8a6357ff307c | 7 / 7 / 1 | plant | Tallman3.14 | ExtremeHorizon9 | Attack | A / completing_timer_owner_v1 |
| Border / 8a6357ff307c | 11 / 11 / 1 | plant | Tallman3.14 | Lxgacy.MAV | Attack | A / completing_timer_owner_v1 |
| Border / 8a6357ff307c | 12 / 12 / 1 | plant | Tallman3.14 | ExtremeHorizon9 | Attack | A / completing_timer_owner_v1 |
| Kafe Dostoyevsky / 5adc26f7a402 | 1 / 1 / 1 | plant | Kenbot.USU | DinoFireKing | Attack | A / completing_timer_owner_v1 |
| Kafe Dostoyevsky / 5adc26f7a402 | 2 / 2 / 1 | plant | Kenbot.USU | Tallman3.14 | Attack | A / completing_timer_owner_v1 |
| Kafe Dostoyevsky / 5adc26f7a402 | 9 / 9 / 1 | plant | Tallman3.14 | unresolved | unresolved | C / timer_owner_body_unresolved |
| Kafe Dostoyevsky / 5adc26f7a402 | 11 / 11 / 1 | plant | Tallman3.14 | MaliKitE.USU | Attack | A / completing_timer_owner_v1 |
| Kafe Dostoyevsky / 5adc26f7a402 | 14 / 14 / 1 | plant | Kenbot.USU | Tallman3.14 | Attack | A / completing_timer_owner_v1 |
| Border / 076d2b6b02bc | 2 / 2 / 1 | plant | none | Tallman3.14 | Attack | A / completing_timer_owner_v1 |
| Border / 076d2b6b02bc | 2 / 2 / 1 | disable | none | briancatM.UMich | Defense | A / completing_timer_owner_v1 |
| Border / 076d2b6b02bc | 6 / 6 / 1 | plant | none | AzoozNewzz | Attack | A / completing_timer_owner_v1 |
| Border / 076d2b6b02bc | 6 / 6 / 1 | disable | none | ormeek.UMich | Defense | A / completing_timer_owner_v1 |
| Border / 076d2b6b02bc | 8 / 8 / 1 | plant | none | getSpoopd | Attack | A / completing_timer_owner_v1 |
| Border / 076d2b6b02bc | 8 / 8 / 1 | disable | none | Lgon. | Defense | A / completing_timer_owner_v1 |
| Chalet / b595ffaaec57 | 5 / 5 / 1 | plant | none | Lgon. | Attack | A / completing_timer_owner_v1 |
| Chalet / b595ffaaec57 | 10 / 2 / 2 | plant | none | unresolved | unresolved | D / incomplete_unique_roster_or_roles |

Michigan Border R08 disable independently resolves Lgon. UID `13288554563263043925`, completing owner entity `4026988329`, timer interval `68405323..68434693`, explicit state-2 terminal, known active body throughout, Defense side. Plant anchor `68392605`. This is replay evidence, not user recollection. The three Michigan disables resolve R02 briancatM.UMich, R06 ormeek.UMich, R08 Lgon.

Kafe R09 remains body-state unresolved; Kenbot.USU is only a research bonus-health proposal, excluded. Its historical Tallman plant row stays intact and remains filtered from display because Tallman was on Defense. Chalet logical R10 / segment2 physical R02 still has nine players and stays unresolved. A separate legacy disable row at first Border R06 has no current approved disable occurrence; it is preserved as unsupported history. No old unproven actor is removed merely to increase coverage.

## Player totals and KOST preview

| Player | Display plants before -> after | Disables before -> after | KOST rounds before -> after / 62 | Frozen v2 Rating |
| --- | --- | --- | --- | --- |
| Lgon | 0 -> 2 | 0 -> 1 | 40 -> 41 | 1.241709326 |
| OhWowJay | 0 -> 0 | 0 -> 0 | 42 -> 42 | 1.248132541 |
| AzoozNewzz | 0 -> 2 | 0 -> 0 | 38 -> 38 | 0.989660434 |
| Tallman3.14 | 0 -> 4 | 0 -> 0 | 30 -> 30 | 0.717751285 |
| DinoFireKing | 0 -> 2 | 0 -> 0 | 40 -> 40 | 0.894786033 |

Stored raw objective rows differ from displayed counts: prior Tallman had five plant rows on Defense, all rejected by the existing stats safeguard. After correction he has four supported Attack plants plus the retained unsupported Kafe R09 Defense row. No team/roster safeguard was weakened.

Only Lgon Fortress R07 gains a KOST success: 0 -> 1; map KOST 7/10 -> 8/10, season/career 40/62 -> 41/62 (64.516% -> 66.129%). Border R08 disable does not add another KOST success because that round already qualifies. Without snapshots Fortress v2 Rating would change 1.490079260 -> 1.540394995; season 1.241709326 -> 1.249824768. This impact was reported before migration. Immutable original normalized-map input snapshots now preserve exact historical map/season/career Ratings. Displayed objective KOST is separate from Rating input KOST. Frozen engine, coefficients, final MAE0.03623 and failed v3 results are untouched. No credited-kill or event-order migration was applied.

## Transactional replacement and reconciliation

New `objective_refresh` overlays supported occurrence actors onto a copy of the original normalized map. Other parser differences are discarded. Verified archive identity and confirmed rehost team mapping precede the overlay. Snapshots and existing transactional `reparse_map` replacement commit together. Unsupported objective rows remain unchanged. The new admin Refresh objective actors button uses this same path.

After every map, exact semantic comparisons checked metadata/series/seasons/roster/aliases/segments/manual K-D, round winners/sites, participation/team/operator, and every kill event. All nonobjective count fields stayed identical: kills/deaths/headshots/entries/trades/pivots/clutches/multikills/survival. All public JSON differences are restricted to plants, disables, objectives, displayed KOST and methodology text; every Rating/eligibility and operator value is unchanged. Archive bytes are identical. SQL counts: 5maps,62rounds,616player-rounds,434kill-events,20objective-events,5original-v2 snapshots. No map was added or duplicated.

Backup DB SHA256 `f3dc10210ab29f62e83317600e8bfcd55b1e6f17c6dbcaf0abf4556af55bef4e`; migrated SHA256 `2136ab3d282ae06729c3ab40a162d520ca902b3c8dc719417cbf7b28a40638c3`. Backup, old public JSON and execution checkpoint are in ignored `data/research/objective-migration/backup/`. Private preview/application evidence and scripts remain cached there.

## Verification and publishing

389 Python tests passed, one optional replay smoke skipped, six subtests passed. New endpoint regression covers stale import -> archive actor refresh -> recalc/export with corrected objective/KOST and unchanged map/season/career Rating. Guards cover research sources, missing UID/identity, wrong side, duplicate occurrence, rollback, unrelated input changes and rehost team reversal with nine-player preservation. Go tests/vet and both web builds passed. Known warnings are Starlette/httpx deprecation, Windows pytest cache permissions and Vite React Router use-client directives.

Actual Start NECC Admin.cmd launched via correctly quoted CMD call, restarted outdated server and opened Chrome. Runtime verified repository .venv Python and current source imports. Live admin Recalculate/Regenerate succeeded. Live Michigan Border objective refresh returned zero further corrections (idempotent), preserving corrected data. Publishing status and live verification will be recorded in STATUS_NEXT_STEPS.

## Rollback and research provenance

Stop local admin before restoring `backup/r6stats.sqlite` and `backup/public-data` to the local DB/public paths. Verify the recorded old DB hash and archive hashes; rebuild/publish old data only if intentionally rolling back the published correction. The archive is never modified by this migration.

Old research checkpoints remain immutable. Their guards against changing the live DB/public files now fail by design; the authorized objective transition needs its separate checkpoint. Before this session, launcher setup had already changed the default executable from frozen SHA e7f375b8... to 22cfe0f1..., so the legacy chained verification already failed before migration. The two old original-v3 source mismatches are superseded by its separately frozen corrected candidate; no studies were repeated/regraded. All credited source/result/evidence seals remain unchanged. New verification records these historical exceptions explicitly rather than replacing old seals.
