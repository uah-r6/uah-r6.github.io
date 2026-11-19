# White replay credited-evidence repair — 2026-10-29

## Result

UAH White vs Niner Esports Gold, Nighthaven Labs, 2026-10-28, 8–6:
map `5c8647f0cede` was already imported with all 14 rounds and a Healthy
archive. The failure was secondary Rating evidence collection, not a lost map.
It is now Rating-eligible through the actual CMD-launched local admin API.
All 18 current maps are eligible. No re-upload or re-import is needed.
Local website JSON was regenerated and validated; nothing was published.

## Root cause and bounded recovery

Physical R08 starts with a standalone `Death` feedback event for Nachofries_08
at 2:52. The legacy feedback reader leaves that event's physical `killOffset`
at zero. The production credited reader treated zero as the earliest elimination
boundary. Every genuine positive-offset baseline therefore failed
`baseline_not_before_first_elimination`; unresolved continuity propagated into
R09. This did not mean that all ten scoreboard counters were missing.

The repository already had a diagnostic native feedback callback observer.
Production `ReadKillCredit` now shares that observer. It calls the original
feedback callback exactly once, requires one emitted event and an exact marker,
and associates the event by callback index, identity, type, clock and original
offset. Only that proof can supply a standalone Death's missing physical offset.
Kill offsets and ordinary feedback remain unchanged. No neighboring packet,
clock heuristic, elimination owner or missing counter is inferred.

The real event is at offset **72,793,401**, with callback end **72,793,480**;
the unchanged action boundary is **72,761,607**. All ten R08 direct counter
deltas validate, and all 14 rounds pass whole-map continuity and full frozen-v3
input validation. Baseline, stable-UID identity, participant, objective, native
order and parity safeguards remain enforced.

## Historical data preservation

Full-map direct scoreboard credit differs from the historical finisher-based
display by one transferred kill: Flex.UAH 10→11 and Nachofries_08 14→13.
Their corresponding extra-multikill inputs are 4→5 and 5→4. This is observed
counter evidence, not a change to the Rating formula.

The existing historical display replacement guard still rejects that change.
The existing sealed Rating-only evidence mechanism now also accepts this
narrow recovery when every original counter sample, identity, physical/logical
round, participant observation and existing positive finish offset is unchanged.
Every recovered boundary must carry exact native callback proof. It independently
checks the current reader against the Healthy archive and prepares full v3 inputs
before saving. Other incomplete-evidence reasons do not qualify.

Only one Rating evidence row and two audit rows were appended. All other **25
SQLite tables are exactly unchanged**, including normalized rounds, kill events,
the original incomplete display sidecar, identities and old Rating snapshots.
All **216 protected file hashes** match the backup, covering all 18 replay
archives/manifests and frozen statistics/Rating sources. All 17 previously eligible
maps retain exactly identical full v3 inputs. Every exported raw display value
is unchanged when compared by identity; only Rating fields, Rating-driven list
ordering and the export timestamp changed in 17 JSON documents.

The admin audit reports `complete (Rating only)` and no credited issues for this
map, while retaining `display_credited_status: incomplete` for historical audit.

| White player | Recovered map Rating |
| --- | ---: |
| CtrlAltDyleted | 1.2384741735461944 |
| Flex.UAH | 0.9127633882647745 |
| Gloop... | 0.9585007580932414 |
| Jellyholic.UAH | 1.0981103963217047 |
| Nachofries_08 | 1.2427908668999634 |

## Verification

- 839 Python tests passed, one optional replay test skipped, six subtests passed.
  Includes the actual admin repair endpoint, idempotence, historical preservation
  and 18 negative cases for changed or unproven evidence.
- Go `test ./...` and `vet ./...` passed. The optional production-reader smoke
  test also passed against this actual R08. A sanitized structural fixture retains
  exact typed offsets/counters with generic names and ordinal UIDs; no replay bytes.
- Both public/admin builds passed. Frontend tests: 69 passed, three failed before
  repair because existing assertions freeze older White player/series counts.
  No frontend implementation was changed to address those unrelated assertions.
- All 67 public JSON documents passed `validate_public_data`; no staging/push.
- Launched with `& '.\Start NECC Admin.cmd'`. It restarted the outdated server,
  verified repository module paths and used `.venv\Scripts\python.exe`.
  The live repair endpoint returned `eligible: true`, `credited_issues: []`,
  `blockers: []`, `changes: ["Rating-only credited evidence"]`.
- Subsequent live audit: 18/18 eligible, including the recovered map; archives
  Healthy. Read-only admin browser audit checks the displayed result on desktop
  and mobile without making further repair/import/publish requests.

Private backup, original and recovered reader output, trial database, live API
responses, export differences and preservation report are under ignored
`data/research/white-death-offset-20261029/`. The pre-existing uncommitted export
of today's 18th map was preserved. No commit, push or website publication.

## Changed source files

- `third_party/siege-dissect/dissect/credited_kills.go`
- `third_party/siege-dissect/dissect/credited_feedback_envelope.go`
- `third_party/siege-dissect/dissect/credited_white_death_test.go`
- `r6stats/rating_credit_evidence.py`
- `r6stats/rating_evidence.py`
- `tests/test_death_offset_recovery.py`
- `tests/fixtures/credited-kills-white-first-death-y11.json`
- This report and the current status checkpoint; generated local Rating exports.
