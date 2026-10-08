# Production Rating evidence repair — 2026-10-08

Baseline: `f62263e`, nine maps / 103 rounds. The database was authoritative.
All nine private archives verified Healthy before and after maintenance.
The frozen `siege_style_v3` model and every eligibility gate are unchanged.

## Result

| Map ID | Team / opponent | Map | Rounds | v3 before → after |
| --- | --- | --- | ---: | --- |
| `035ff71d4884` | White / FSU Maroon | Nighthaven Labs | 14 | Unrated → eligible |
| `5525677668c0` | White / FSU Maroon | Border | 7 | Eligible → unchanged |
| `076d2b6b02bc` | Blue / Michigan | Border | 12 | Eligible → unchanged |
| `b595ffaaec57` | Blue / Michigan | Chalet | 12 | Unrated → blocked |
| `5adc26f7a402` | Blue / Placements | Kafe Dostoyevsky | 14 | Unrated → blocked |
| `8a6357ff307c` | Blue / Placements | Border | 14 | Unrated → blocked |
| `d64d5478cdb3` | Blue / Placements | Fortress | 10 | Eligible → unchanged |
| `8af0a6db6c39` | Blue / UCF | Border | 11 | Eligible → unchanged |
| `9db26f1b6ca7` | Blue / UCF | Nighthaven Labs | 9 | Eligible → unchanged |

Six maps / 63 rounds now contribute v3 inputs. Every map still contributes its
ordinary performance statistics. All eight maps with complete credited evidence
retain those original evidence records; Chalet's incomplete record is retained.
The four existing objective sidecars are unchanged. White Nighthaven was repaired
in normalized objective data rather than given a contradictory sidecar.

## White Nighthaven root cause

Logical R6 contains a canceled plant by poussson.FSU, then a complete plant by
Avner.oL. After closing the canceled interaction, Siege redeclares the same timer
component and repeats its exact terminal snapshot: state 2, progress bits
1062342746, timer 5.737. The resolver previously treated that repeated closed
snapshot as an unbound new interaction. That orphan conservatively vetoed the
later, independently complete timer owner.

The generic Go extraction fix recognizes an identical closed terminal snapshot
only while its unique typed owner, player, entity, slot and class remain
continuous. Changed fields, intervening objective properties, new interactions,
owner loss/change, shared ownership or class changes invalidate that recognition.
Completion thresholds, body-state requirements, identity checks, occurrence
sources and action-start detection are unchanged. A reduced structural fixture
tests the positive case and twelve negative controls; no replay bytes are stored
in Git.

Fresh archive parsing resolves R6 to Avner.oL with UID 5319349670349841180,
`actor_source = actor_reason = completing_timer_owner_v1`, occurrence source
`defuser_state_v1`, and plant-state offset 104858758. All other logical rounds
were compared independently. The existing objective overlay guards and full
`prepare()` passed before writing. The existing `load_inputs()` passed inside
the write transaction and after it.

Exact correction: **R6 previously had no plant credit; it now credits the proven
FSU opponent plant to Avner.oL.** No tracked UAH plant, disable, KOST or other raw
count changes. The map keeps its original round IDs, score 6–8, two physical
segments, exclusions, confirmed team remapping, metadata and frozen appearances.
Original v2 snapshots remain byte-for-byte unchanged. The private audit contains
complete before/after normalized data, exact actor change and parser/manifest
hashes. A following repair-check audit records before/after eligibility.

## Three remaining blockers

- **Kafe R9:** legacy normalized data credits Tallman3.14 with a plant while on
  Defense. The fresh trusted occurrence at offset 34204105 remains unbound:
  `timer_owner_body_unresolved`. The archive does not establish a supported final
  actor under the existing body-state rules. No actor is guessed or legacy credit
  erased. Full exclusion remains
  `Objective credits lack complete unique core occurrence evidence.`
- **Placements Border R6:** the trusted parser supports AzoozNewzz's plant, but
  provides no trusted disable occurrence for the legacy Lxgacy.MAV disable credit.
  Attack won that round. There is no independently supported replacement actor;
  deleting the legacy event to gain eligibility would not be a proven correction.
  Full exclusion remains
  `Objective credits lack complete unique core occurrence evidence.`
- **Michigan Chalet R9–12:** confirmed segment 2's physical R01–R04 contain nine
  header participants and nine unique credited UIDs. The current archive reader
  still reports `incomplete_or_ambiguous_uid_roster`, incomplete round counters
  and continuity through unresolved rounds. Missing participation cannot be
  synthesized into a ten-player roster. The original credited record and
  anti-overwrite safeguards remain intact. Full exclusion remains
  `Incomplete credited-kill evidence`.

Fresh observations use the current local Go binaries and binary/replay-hash
keyed caches. These are evidence limitations, not forced eligibility exceptions.

## Every series participant

Each row was independently checked against its database participation, full v3
map inputs and round-weighted aggregation, with tolerance 1e-12 before rounding
for this table. A SUB receives actual map/series Rating while remaining excluded
from normal Season/Career and Rating trends.

| Team / opponent | Player | Role | Rated maps | Rated rounds | Series Rating |
| --- | --- | --- | --- | --- | ---: |
| Blue / Placements | Lgon | Roster | 1/3 | 10/38 | 1.50103439 |
| Blue / Placements | OhWowJay | Roster | 1/3 | 10/38 | 1.47456878 |
| Blue / Placements | AzoozNewzz | Roster | 1/3 | 10/38 | 1.20776925 |
| Blue / Placements | DinoFireKing | Roster | 1/3 | 10/38 | 0.87082576 |
| Blue / Placements | Tallman3.14 | Roster | 1/3 | 10/38 | 0.81459694 |
| Blue / Michigan | Lgon | Roster | 1/2 | 12/24 | 1.43426477 |
| Blue / Michigan | OhWowJay | Roster | 1/2 | 12/24 | 1.24234868 |
| Blue / Michigan | AzoozNewzz | Roster | 1/2 | 12/24 | 1.23799696 |
| Blue / Michigan | Tallman3.14 | Roster | 1/2 | 12/24 | 0.93466906 |
| Blue / Michigan | DinoFireKing | Roster | 1/2 | 12/24 | 0.84242683 |
| Blue / UCF | OhWowJay | Roster | 2/2 | 20/20 | 1.83829087 |
| Blue / UCF | Lgon | Roster | 2/2 | 20/20 | 1.41567527 |
| Blue / UCF | AzoozNewzz | Roster | 2/2 | 20/20 | 0.92737631 |
| Blue / UCF | Tallman3.14 | Roster | 2/2 | 20/20 | 0.82315508 |
| Blue / UCF | DinoFireKing | Roster | 2/2 | 20/20 | 0.66466024 |
| White / FSU | Flex.UAH | Roster | 2/2 | 21/21 | 1.04203008 |
| White / FSU | Nachofries_08 | Roster | 2/2 | 21/21 | 1.01538162 |
| White / FSU | Gloop... | Roster | 2/2 | 21/21 | 0.73600535 |
| White / FSU | Dinoted11 | SUB | 2/2 | 21/21 | 0.68583538 |
| White / FSU | CtrlAltDyleted | Roster | 2/2 | 21/21 | 0.55905993 |

## Future imports and local maintenance

Both normal and confirmed rehost imports now automatically attempt trusted
credited collection, objective evidence maintenance and full frozen v3
validation after the core map and archive succeed. Secondary evidence failure
keeps that valid import and reports **Map imported successfully**, **Rating
eligible: NO / UNAVAILABLE**, its exact exclusion and expandable reader findings.
The same local repair action is available immediately and on map detail.

**Statistics → Audit / Repair All Rating Evidence** verifies every map
independently. Existing eligible maps are no-ops. Blocked maps do not stop other
maps. Changes regenerate public exports; maintenance itself does not publish.
Repair attempts record changes, blockers, before/after eligibility and available
parser/archive-manifest hashes. Supported actor corrections require the existing
objective guards, exact replay/player/team identity, complete credited inputs and
full v3 validation under a transaction. Evidence-only matching actors continue
to use the existing immutable sidecar path.

The actual `.cmd` launcher started the repository `.venv` Python and current
repository modules, opened Chrome, and served the real admin endpoints. Browser
clicks repaired White Nighthaven, then bulk-audited nine maps: **six already
eligible, zero additional repairs, three blocked**. Repeated eligible repairs
make no changes. Import status/repair UI tests intercept every write; actual
normal/rehost import API tests use isolated fixture databases and archives.

## Verification and recovery

- **708 Python tests**, six subtests passed; one optional real-replay smoke skip.
- **39 frontend tests**; both Vite builds passed.
- Full Go tests and `go vet ./...` passed.
- Admin audit/bulk/detail, import-failure/repair fixtures, all four public series,
  all 103 round highlights, Blue partial/full trend keyboard/touch behavior,
  White full-coverage profiles, real/synthetic SUB views, embeds and Submit Replays
  shell passed at 1440/1100/768/390px without JavaScript errors.
- Preservation checked **22 original tables**, **49 public JSON documents**,
  **116 protected archive/formula/validator files**, all nine Healthy archives,
  exact five previously eligible maps' full-precision v3 inputs, immutable v2
  snapshots, roster identities/memberships/roles and every unrelated raw count.
  SQLite integrity and foreign keys pass.

Ignored recovery/evidence directory: `data/research/rating-evidence-production-20261008/`.
Backup `before.sqlite` SHA-256:
`d77e18a41e2cb56129ed24f3ad17235c25cf8e4f5dfabb0b474542c472a3fa53`.
It also contains full baseline tables, public JSON, protected hashes, exact
objective diagnostics, current credited observations and browser reports.
No archive bytes, SQLite, private paths, replay downloads or research-model data
are committed or published.

Read-only verification commands (from the repository root):

```powershell
.\.venv\Scripts\python.exe scripts\verify-rating-production.py
.\.venv\Scripts\python.exe scripts\verify-rating-production.py --verify
.\.venv\Scripts\python.exe scripts\verify-rating-production-admin-ui.py
.\.venv\Scripts\python.exe scripts\verify-rating-production-public-ui.py
```

The preservation mode uses this pass's private baseline. The admin script's
`--repair` option was used once for the explicitly authorized initial production
repair; its default mode only audits and uses intercepted import fixtures.
**Stop after this reliability pass.** The three remaining maps stay visibly
partial until independent trustworthy evidence becomes available.
