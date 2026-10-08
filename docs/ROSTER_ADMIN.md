# Roster administration and mistaken-player deletion

## Corrected White roster — 2026-10-07

`nachofries_08` already existed as global player **10**, with the exact
case-insensitive alias `Nachofries_08`. It was Active, unassigned, not substitute
eligible, not profile-bound, and had no imported appearances. The default Roster
filter hid this identity. Trying to add it again reached the case-insensitive
unique alias constraint and returned `UNIQUE constraint failed: aliases.username`.
The attempted insertion rolled back; it did not establish a second identity.

The existing identity was assigned to UAH White through dated membership, starting
**2026-10-07**. No imported White replay or pending submission supported an earlier
competitive date. Its username, aliases, Active status, profile state and substitute
eligibility were retained. The Add / Assign form now recognizes current usernames
and aliases across all teams and unassigned players, regardless of visible filters.
It offers assignment of the existing identity or a link to its row. The server
independently rejects duplicate identities with an actionable message.

`Nanor555` is global player **12**, also Active, unbound and not substitute eligible,
with no imported history. Its mistaken White membership began the same day.
Because membership intervals require an end strictly after the start, removal
on that start date **cancelled only the unused membership**. The player and alias
remain globally, in the clearly labelled Unassigned state. No global deletion was
requested or performed for Nanor555.

Current White regular roster:

- CtrlAltDyleted
- Flex.UAH
- Gloop...
- Jellyholic.UAH
- Nachofries_08

Dinoted11 remains an eligible, unused sub-only identity. These players have no
approved match statistics. White Player Stats and Sub Stats remain empty; linked
zero-match profiles show unavailable Rating/KD rather than invented values.

## Three separate operations

Launch **Start NECC Admin.cmd**, select a team and season, and open **Roster**.

| Action | Effect |
| --- | --- |
| **Remove from roster** | Requires an effective date and confirmation. Ends regular membership; keeps identity, aliases, profile binding, Active/Alumni status, substitute eligibility and all history. |
| **Mark Active / Mark Alumni** | Changes player status independently of membership and substitute eligibility. |
| **Advanced / Danger zone → Delete mistaken player** | Permanently deletes only a proven unused identity, its aliases and configuration memberships. Requires the exact current Ubisoft username. |

Membership dates remain start-inclusive and end-exclusive. Removing on a later
date preserves the historical membership row. Cancelling a same-day assignment
is allowed only when the historical audit proves that the player has no imported
history. A historical same-day membership is retained and requires a later end
date. Unassigned and sub-only players are valid identities and are never
automatically deleted. Assigning an eligible substitute to a regular team retains
their substitute eligibility; edit that setting separately if desired.

## Hard-deletion safeguards

`r6stats/db/player_history.py` audits every current SQLite table and all foreign
keys referencing `players`, plus `player_id` columns without declared foreign
keys. It checks `round_players`, frozen `map_player_appearances`, map K/D
corrections, normalized replay JSON, frozen Rating snapshots, credited/objective
evidence and retained before/after audit JSON. Exact aliases and bound profile
IDs also detect unbound historical participants. Similar display names do not
establish identity. Unreadable historical JSON conservatively blocks deletion.

Aliases and regular memberships alone are removable configuration. Any historical
reference blocks deletion and directs the user to **Remove from roster** or
**Mark Alumni**. There are no new historical cascade deletions, null bindings or
map deletions. The audit also protects newly discovered tables with cascade FKs.

The DELETE operation repeats confirmation and the history audit under SQLite
`BEGIN IMMEDIATE`, then removes aliases, memberships and the unused player in one
transaction. Public exports are generated in a private temporary project directory,
validated, and installed with the previous public directory retained until commit.
Export, validation, installation, SQL deletion and commit failures restore the
database and previous public JSON. Staging directories are cleaned automatically.
This is a local operation; GitHub Pages remains static/read-only.

API routes use the existing localhost/CSRF protections:

- `POST /api/admin/roster/{id}/remove-from-roster`: explicit `team_id` and `effective_date`.
- `GET /api/admin/roster/{id}/deletion`: current eligibility and historical references.
- `DELETE /api/admin/roster/{id}`: `confirm_username`; locked recheck and staged export.

## Verification

- **687 Python tests + six subtests passed**, one optional replay smoke test skipped.
  Thirty new focused tests cover history preservation, every discovered reference,
  same-day cancellation, rollback at five failure points, stale eligibility,
  exact confirmation, alias/profile conflicts and existing-player assignment.
- **39 frontend tests passed**, including existing/ambiguous alias resolution.
  Both public and admin builds passed. Existing fixture assertions were updated
  to accommodate newly added zero-match identities and the 44-file export.
- Actual `.cmd` launcher restarted the stale server and opened Chrome. Running
  server PID at verification: **5752**. Python:
  `C:\Users\logan\Documents\R6\r6-necc-stats\.venv\Scripts\python.exe`.
  Server and parser imports came from the current repository source.
- The real browser/admin API created one explicitly temporary player, added an
  alias, removed its membership, verified sub-only/Active state, changed Alumni
  and Active separately, assigned its existing alias back to White, rejected
  incorrect typed confirmation, and permanently deleted it. Historical Lgon
  deletion was denied in both UI and API (HTTP 400). No test identity remains.
- Admin and public checks passed at **1440/1100/768/390px**, with no horizontal
  overflow or JavaScript errors. Public checks cover White's five-player roster,
  empty season/Career Player Stats, Nacho's empty profile, retained Nanor profile,
  Blue statistics and isolated Sub Stats. Existing Series Rating/trend/highlight,
  substitute, embed and submission-shell regression checks passed.
- Preservation compares all **22 preexisting SQLite tables** and **44 public JSON
  documents**, allowing only the two requested membership changes and export
  freshness. All seven maps / **82 rounds**, frozen appearances, corrections,
  statistics, Ratings, Series Ratings and archives remain unchanged. All seven
  archives are Healthy; **101 protected archive/parser/formula files** match
  their original SHA-256 hashes. SQLite integrity and foreign-key checks pass.

The ignored backup/evidence directory is
`data/research/roster-deletion-20261007/`. SQLite backup SHA-256:
`6c9e7714bfb8a91bb857ff3241f0e4e444aea74ae7842fc125e75e2c81b116cf`.
The initial dirty public exports and diff were backed up and preserved; existing
roster additions were included in the regenerated output.

Read-only verification scripts:

```powershell
.\.venv\Scripts\python.exe scripts\verify-roster-deletion-preservation.py
.\.venv\Scripts\python.exe scripts\verify-roster-public-ui.py
```

The opt-in production admin script creates and deletes a temporary unused player:

```powershell
& '.\Start NECC Admin.cmd'
.\.venv\Scripts\python.exe scripts\verify-roster-admin-ui.py --allow-temporary-player
```

Public browser verification accepts `--url https://uah-r6.github.io/` and compares
every published JSON document to the local export. Never publish the SQLite
database, private settings, replay archives, test screenshots or backup files.
