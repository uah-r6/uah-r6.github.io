# Credited-kill and core-objective migration review — pending user review

No historical migration is applied. SQLite, replay archives, public JSON and the deployed Rating are unchanged. The approved core actor code was pushed as `7d4bc8a` on `main`; this Phase2 implementation remains local and opt-in. The new Go reader and Python projection are available for preparation, without changing the default importer/exporter or frozen statistics engine.

## Methodology and evidence

The authoritative count source is `stable_uid_scoreboard_delta_v1`: full distinct ten-player UID roster, explicit temporal owner → scoreboard slot `eb219b38` / class `18a591a1`, framed width4 kill counter `1cd2b19d`, early baseline, monotonic cumulative values and terminal-minus-initial round delta. The baseline precedes known action start and first elimination; prep increments, unknown death boundary, changed/shared routes, unsupported class/width, implausible delta and unfinished/ambiguous winner refuse complete credit. Missing counters are unresolved, never zero-filled.

Map totals sum validated **round deltas**, with continuity checked between rounds. A reset requires a new physical folder R01, the same ten distinct nonzero profile UUIDs and all-zero initial counters. SAL8596 logicalR06 exercises that real reset. Within-round reconnect/component replacement currently abstains; there is no unvalidated reconnect repair. Confirmed rehost team-index flips can join normalized profiles only through a complete bijection between the two five-player groups. No final-map minus first-segment subtraction is used.

Raw replay `Kill` events retain finisher, victim, sequence, headshot and elimination clock. The new report also retains their parser-owned packet offsets. Counter samples preserve numeric UID/profile, owner/component/declaration offset, initial/terminal values and every observed update. No victim or downer is assigned from a counter, packet proximity, last update or target totals. A future normalized per-round credit sidecar can preserve this evidence without replacing `Kill.killer` or requiring a new SQL kill-event schema.

The [professional audit](credited-kill-professional-audit.md) verifies 32 consumed maps/325 rounds against cached evidence. The [feature audit](credited-kill-feature-audit.md) independently verifies all200 SAL victim deaths, all200 official credited multikill-size breakdowns and all207 public round multikill summaries. Original finisher size breakdowns match only176/200. These cohorts are consumed development controls, not a new untouched Rating final.

Ubisoft's [August2021 DBNO notes](https://www.ubisoft.com/en-us/game/rainbow-six/siege/news-updates/1YPQ5yw9TaRhQwghjStqn2) describe the downer receiving credit while the final damage dealer appears in the feed. The existing [modern official broadcast review](v3-consumed-dbno-vod-review.md) corroborates that distinction in Y11. In the [Stk packet chronology](credited-kill-timing.md), the counter increments with final elimination serialization after the observed DBNO transition; byte order does not establish server causality or precise event time. No generic downer field was established.

## Current UAH audit

See the [map/round/player audit](credited-kill-uah-audit.md). Five stored maps/62 rounds; four maps and58 round structures have trustworthy complete counters. Chalet logicalR09–12 has only nine header players, so complete credited map/season totals remain unknown. No safeguard is relaxed to fill them.

| Player | Current season kills/deaths | Validated-round credit minus finishes | Conditional season K/D if only four complete maps migrate and Chalet is retained |
| --- | --- | ---: | --- |
| Lgon | 61/38 | −2 | 59/38 = 1.553 |
| OhWowJay | 58/39 | +1 | 59/39 = 1.513 |
| AzoozNewzz | 45/48 | 0 | 45/48 = 0.938 |
| Tallman3.14 | 28/49 | 0 | 28/49 = 0.571 |
| DinoFireKing | 30/38 | +1 | 31/38 = 0.816 |

The last column is a **conditional mixed-source scenario**, not fully credited season statistics or a recommendation to hide Chalet's uncertainty. A complete migration cannot assert these as authoritative credited season totals. The audit lists all eight changed player-rounds with direct start/end counter evidence; no specific DBNO victim is guessed from those deltas. All player deaths remain as stored.

On the58 validated rounds, replacing only KOST's Kill flag has zero tracked-player KOST effect. Credited multikill-extra changes: Lgon−3, OhWowJay+1, DinoFireKing+1; Azooz/Tallman0. The combined supported-core-objective/Kill scenario adds one Lgon KOST round; unresolved Chalet rounds are not assessed.

## Core objective corrections — separate categories

- **A, supported core:**15plant and3disable proposals with guarded completing timer owner. [Per-objective evidence and stored credits](uah-final-actor-correction-proposal.md) remain the authoritative review package. Resolved-only tracked counts: Lgon2plants/1disable, Azooz2/0, Dino2/0, OhWowJay0/0, Tallman4/0.
- **B, research-only:**Kenbot.USU KafeR09 bonus/body1 proposal is excluded.
- **C, unresolved:**ChaletR10 incomplete roster and all unknown older structures remain unresolved. Do not approve them by class/health inference. KafeR09's old Tallman credit requires an explicit retain/remove policy; the resolved-only Tallman4 count is not guaranteed final historical total.

## Impact inventory

| Feature | Current source | Proposed source / time | Ready for a separate reviewed migration? | Remaining requirement |
| --- | --- | --- | --- | --- |
| Kills, KD, KPR | Accepted opponent feed finishes / victim deaths / participant rounds | Per-round credited UID deltas; no event time needed | Supported complete maps only | Resolve or visibly mark unsupported map/season data; review audit |
| Side kill splits | Feed counts and action-start side | Credited round count; existing validated player side | Supported complete maps | Preserve confirmed rehost identity/team mapping |
| Deaths, survival, clutch alive state | Victim final eliminations, round winner | Same raw death events | Preserve current source |200official deaths agree; DBNO adds no death |
| Multikill sizes/extra | Feed kills per round | Credited round deltas; no victim timing needed | Validated count projection only |200official size breakdowns and207public round summaries agree; original v2 inputs stay frozen |
| KOST Kill component | Feed kill boolean | Credited per-round positive count | Supported rounds after review | Preserve Survival/Trade semantics; unsupported round must stay unknown |
| KOST Objective component | Stored legacy actor events | Supported core completing owner | Supported A corrections after review | Retain explicit B/C uncertainty and old-credit policy |
| Opening K/D | First accepted opponent elimination sorted by coarse remaining timer | Unsettled: first elimination order and credited owner are separate | **No** |193/200 original opening comparisons agree; packet-order hypothesis198/200. Two owner discrepancies remain. Need independent per-round DBNO/entry evidence |
| Trades/refrags | Finisher identity, victim elimination clock,8s window | Credited killer/time only if independently victim-bound | **No** | No generic victim/downer relation; counter update offset is not a trade start |
| Pivot / untraded event features | Finisher event order and alive state | Unsettled | **No** | Validate DBNO, elimination ordering and trade association separately |
| Headshots / HS% | Finisher's raw headshot bit | Credited-owner shot metadata unproven | **No** | Preserve raw bit; do not divide finisher headshots by credited kills as a validated new metric |
| Teamkills | Raw teammate/suicide finish classification | Same raw evidence | Preserve |SAL8596R10 negative control remains excluded from opponent credited kills |
| `siege_style_v2` | Original finisher-derived KPR/multikill/opening/KOST/trade inputs | Immutable original input snapshot | Preserve original version |MAE0.03623 belongs exclusively to original evaluated semantics |

## Proposed migration and rollback sequence

1. User reviews the read-only kill/objective audit, incomplete Chalet policy and unresolved old objective-credit policy. No write occurs before this review.
2. Take a consistent SQLite backup and copy existing generated public JSON; retain verified replay archives. Capture map metadata, IDs, participation, raw normalized JSON and source hashes.
3. Preserve immutable **original v2 per-round/map input snapshots** before any objective or kill projection changes. Existing runtime `calculate_match` reads mutable `Round.objectives` into KOST even though the objective coefficient is zero; changing those inputs would change v2. The core parser push alone did not alter stored maps. Historical/future corrected display counts must be separated from original evaluated Rating inputs, with explicit public methodology/version labels. No new-input calculation may inherit the original MAE claim.
4. Implement an explicit reviewed migration path: store optional round-credit evidence/source version separately from raw finish events; apply only complete validated count projections and supported A actor overlays transactionally. Keep map IDs, metadata, roster identities, original events and original v2 snapshots. Unsupported maps/rounds remain visibly unresolved or legacy, never silently complete.
5. Rebuild local map/season/career display projections only after verifying per-round and aggregate totals, deaths, sides, aliases, reset boundaries, uncertainty and Rating provenance against the reviewed audit. No new v3 fit/final evaluation.
6. Regenerate and validate local public JSON only as a separate authorized post-review step; preview both UIs. Publication requires its own authorization. This session exports/publishes no corrected data.
7. Rollback by disabling the credited/actor projection version and restoring the consistent SQLite/public JSON backups if a write migration was performed. Original raw events/identities/archive files and v2 snapshots remain available; never delete history to roll back derived counts.

## Remaining work

The code is deliberately opt-in. Live wiring, normalization persistence, Rating snapshot/version display and historical/public regeneration remain pending review. Investigate consumed8583/pino-versus-Neskin opening attribution and8583R03/8594R07 clock/order discrepancies with independent official round evidence. Keep event-feature migrations separate. No speculative bonus/older-class actor extension or v3 deployment is included.
