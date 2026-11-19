# White vs AVL Rating repair — 2026-11-11

## Result

The failed map was **Nighthaven Labs, 7–2**, map `140cedd0f64e`, in White's
2026-11-04 AVL series `3caeefb3fa26`. The upload had succeeded, with all nine
rounds safely archived. The failure was subsequent Rating evidence validation.

Repaired locally through **Start NECC Admin.cmd → admin browser → Statistics →
Repair From Healthy Archive**. The live response has `eligible: true`,
`credited_issues: []`, `blockers: []` and complete Rating-only credit. The AVL
Series Ratings are now complete for all five tracked players. All **23** stored
maps remain evidence-eligible; Placements remains excluded from aggregate stats.
Local JSON was regenerated, and all **74** public documents validate. No import,
delete, commit, push or website publication was performed in this pass.

## Root cause

Physical **R08** contains nine active participants and a named disconnected
opponent slot. That slot retains its username but has an operator ID of zero,
a nil profile, the invalid all-ones UID, and an explicit absent body before
action start. The opponent reconnects later with a new runtime UID and does not
become a playable combatant during that round. The new body has state 4 and zero
health, baseline, maximum and bonus fraction throughout its recorded fields.
Its scoreboard initializes to zero and then restores the prior cumulative four
kills. Those four restored kills must never be treated as new round kills.

The existing nine-player exception supports an anonymous empty slot, with no
extra runtime UID. It correctly refused this different layout as
`incomplete_or_ambiguous_uid_roster`. Whole-map continuity consequently failed
through R08 and R09. Removing the roster check or pretending that the reconnect
was an ordinary ten-player round would have been unsafe.

## Verified evidence and bounded implementation

New proof source: `explicit_inactive_reconnect_participant_v1`.

- Unchanged action-start boundary: **72,026,634**.
- Explicit absent-body declaration: **68,989**; named slot: **69,086**.
- Post-action body declaration: **72,238,731**; zero-vitals/state-4 fields
  **72,238,765–72,238,815**.
- Scoreboard declaration: **72,239,058**; transient zero counter **72,239,092**.
- New typed runtime UID: **72,239,711**; restored four counter **72,240,335**.
- R07's terminal four equals the restored four and R09's initial four. R09
  independently binds the new runtime UID to the same historical profile/name.
  Every other identity and direct counter is continuous through both boundaries.

The Go reader requires the complete ten-slot table, exactly nine active profiles,
the named nil-profile/invalid-UID/zero-operator slot, explicit absent and late
body declarations, unique ownership, exactly supported zero-vitals/state-4
fields, one late UID and the bounded zero→restored counter sequence. It refuses
an active body, missing vitals, unknown extra accounts, ambiguous routes,
changed counters or any feedback involving the inactive account.

Python independently validates that proof and requires both surrounding rounds:
same source folder/consecutive physical rounds, the exact removed/returning
profile/name/team, the new UID on return and unchanged restored counters. The
nine other identities and counters must match exactly. A standalone nine-player
header, a gap without a proved return, and a reconnect without these facts remain
unsupported. No player, profile, kill, objective or operator is synthesized.

Existing sealed Rating-only evidence and objective backfill perform the repair.
The historical display sidecar, normalized matches, events and Rating snapshots
stay intact. The Rating formula, action-start detection and operator logic were
not changed.

## Recovered values

| Player | Nighthaven Labs Rating | AVL Series Rating |
| --- | ---: | ---: |
| CtrlAltDyleted | 1.3600709904837576 | 1.4737143864916398 |
| Flex.UAH | 0.8898424425975775 | 1.1369492246939314 |
| Gloop... | 1.714381643827739 | 1.6684213203008074 |
| Jellyholic.UAH | 0.7422528117464884 | 0.9577051190171455 |
| Nachofries_08 | 1.5264270942182434 | 1.3049321407306558 |

## Preservation and tests

- Pre-change SQLite backup, original JSON and raw diagnostic outputs are ignored
  under `data/research/white-avl-rating-20261111/`. Actual raw replay files remain
  private and unchanged; committed fixtures use ordinal UIDs/profiles and names.
- **24 database tables** unchanged exactly. Only one Rating-credit evidence row,
  one objective evidence row and three audited evidence rows were appended, all
  for this map.
- All **22 other maps' complete Rating input sets** are identical. All **265
  protected archive/statistics file hashes** match. Public changes in 17 documents
  are Rating fields, Rating-driven ordering and the export timestamp only; every
  displayed raw statistic and the no-count policy is unchanged.
- **897 Python tests + six subtests** passed; one optional replay test skipped.
  New cases cover actual three-round continuity, no synthetic combatant/kill,
  unsafe body/identity/counter/return mutations and the real admin repair endpoint.
- Go `test ./...`, `vet ./...` and the optional smoke/capture on the actual R08
  passed. New Go tests use exact sanitized typed observations and reject unsafe
  proof variants.
- **75 frontend tests** and both public/admin builds passed. Actual CMD-launched
  browser repair and subsequent 23-map evidence audit passed at desktop/mobile
  widths. The browser made only the one targeted repair POST.

## Files changed in this pass

- `third_party/siege-dissect/dissect/participant_reconnect.go` and its test.
- `third_party/siege-dissect/dissect/participant_inventory.go`: retain the strict
  original validator as a separate helper.
- `third_party/siege-dissect/dissect/reader.go`: guarded participant-proof fallback.
- `r6stats/participant_inventory.py`, `r6stats/kill_credit.py` and the audit wording
  in `r6stats/rating_credit_evidence.py`.
- `tests/test_inactive_reconnect.py`, two sanitized reconnect fixtures, this report
  and the status checkpoint; generated local Rating JSON.

The prior uncommitted standalone-Death recovery files were preserved.
