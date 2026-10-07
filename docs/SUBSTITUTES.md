# Substitute appearances

## Four independent concepts

| Concept | Meaning |
| --- | --- |
| Active / Alumni | Global player status; Sub is never a status |
| Regular membership | Dated membership of at most one UAH team; can be absent |
| Substitute eligibility | Explicit global capability to play for any UAH team |
| Appearance role | Immutable `roster` or `sub` for one player in one logical map |

A regular player may be eligible or ineligible to substitute. Sub-only players
have one global identity, no regular membership and explicit eligibility.
An eligible Alumni player can participate without being reactivated; turning off
eligibility blocks new substitute imports but preserves historical appearances.

## Import rules

The map's organization owner and replay date determine the role. Regular member
of that owner on that date means roster, even if substitute eligible. Otherwise
explicit global eligibility means sub. A known player on the selected replay side
without either qualification blocks import with an actionable error. Unknown
participants remain untracked, never converted into tracked substitutes.

Regular members provide side detection evidence. Globally eligible substitutes
never vote. With insufficient regular evidence, the user must review participants
and explicitly choose replay side 0 or 1. That side must contain a qualified known
participant. Profile IDs remain authoritative; aliases still reject conflicting
bindings, duplicate identities and changing sides. Replay eligibility and manual
Custom Game confirmation as NECC remain unchanged.

Both CLI and admin import use the repository transaction. Role validation is
repeated under the import write lock before any identities or map data are saved.
`map_player_appearances` stores map/player identity, role, classification date and
regular team at import. A trigger rejects role updates. Membership moves, status
changes, eligibility changes, edited date metadata and reparses do not reclassify
old maps. Deleting a map cascades its appearances, preserving player identities.

Rehosts classify against the logical map owner/date, including validation of the
mapped sides of physical sources. Per-map uniqueness prevents segment duplicates.
Source identity checks, explicit round exclusions, final score confirmation,
roster change confirmation and archives retain their existing behavior.

## Migration

`r6stats/db/appearances.py` follows the transaction and version marker conventions.
It uses an immediate write lock and rechecks the marker for concurrent startup.
Eligibility defaults false. Existing bound map participants conservatively become
roster. The original rows and columns in all existing tables remain intact. Failed
migrations roll back; repeated startup does not backfill or rewrite later roles.

The production backup and baseline are private and ignored under
`data/research/substitutes-20261007/`. There are 35 historical map/player roles,
seven maps, 82 rounds, three series and five player identities. The pre-change
working generated JSON lacked series/highlights; its full copy and Git diff were
preserved before regeneration. The committed checkpoint is the public baseline.

## Statistics and public JSON

The engine still calculates a map once using the same trusted event, credited
count, objective and frozen Rating policies. Appearance scopes select which
player-map inputs feed existing aggregation. Ratings aggregate eligible counts
and apply the existing model, never average rounded map Ratings.

- Normal team, season and global player Career totals include roster only.
- Normal profiles' maps, team splits and Rating trends include roster only.
- Team JSON `sub_players` includes only actual subs for that team and period;
  Career never combines substitutions for other teams or unused eligible players.
- Profiles have `sub_teams` referencing team-specific substitute totals and
  `players/<slug>/subs/<team>/<period>.json`. Zero-period files support stable
  historical navigation; a player must actually have subbed to get an entry point.
- Map participants retain `appearance_role`. Series participants expose roster,
  sub or mixed, and keep the same all-played-maps Series Rating. Sub/mixed rows
  receive a compact SUB badge. A mixed participant's `roster_stats` provides only
  roster coverage and Rating for the normal trend; no sub input enters that trend.
- Manual K/D corrections affect only their frozen appearance scope and retain
  the existing map Rating exclusion policy. Highlights include actual participants.

No private replay contents, IDs, paths, R2 details or evidence are exported.
Publishing validates player and team role scopes against actual map participants,
coverage, profile references and history before staging generated JSON.
This is the same independent Siege-style Rating, not an official SiegeGG formula.

## Browser and administration

Player Stats defaults Blue / active season / Roster. The compact Roster/Subs
control uses `?team=white&players=subs`; Roster omits the player query. There is no
combined mode. Team/period changes preserve the chosen scope where applicable.
Substitute Stats is a separate profile area with team and global period selectors,
trusted statistics and actual map history. Sub-only pages remain directly linkable
through Subs leaderboards; no search service or duplicate identity was introduced.

Legacy persistent `necc-season` is ignored. Deliberate choices use sessionStorage
with a 12-hour expiry, preserving navigation and refresh while a fresh or later
visit defaults to the active season. Embeds remain independent and roster only.

Local Roster shows regular membership, the program-wide eligible pool, a global
eligibility control, sub-only creation and dated unassignment without deleting
history. Preview and map detail label participants ROSTER/SUB, their regular team
at classification (or none), and the classification date. No import is automatic.

## Verification

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
npm.cmd --prefix web test
npm.cmd --prefix web run build
npm.cmd --prefix web run build:admin
.\.venv\Scripts\python.exe scripts/verify-substitute-preservation.py
.\.venv\Scripts\python.exe scripts/verify-substitutes-ui.py
& ".\Start NECC Admin.cmd"
.\.venv\Scripts\python.exe scripts/verify-substitute-admin-ui.py
.\.venv\Scripts\python.exe scripts/verify-substitutes-ui.py --url https://uah-r6.github.io/ --output data/research/substitutes-20261007/live
```

The preservation command needs the private pre-change evidence. It compares all
original SQLite columns, all existing values in 30 committed JSON documents,
2,508 protected files and all seven Healthy archives. Only additive role/scope
fields and export freshness differ. SQLite integrity and foreign keys are checked.

Browser verification covers 1440/1100/768/390px, real Blue/White scopes, active
default, Career and URL navigation, profiles, embeds and submission shell. Browser
response interception exercises sub-only/team-specific profiles and Series badges
without adding production fixture data. Admin checks use the actual CMD-launched
server, preview the existing Fortress archive and view frozen match roles; control
mutations are intercepted. Backend API tests use temporary databases and archives.
