# Public replay submissions

## Architecture and privacy

The [public submission page](https://uah-r6.github.io/#/submit) remains part of the
static GitHub Pages website. It sends selected replay folders to a Cloudflare
Worker; it cannot modify the local statistics database. The Worker does not parse
replays or calculate statistics. The Windows local admin remains the trusted
review/import authority. No submitter account or hosted admin login is required.

| Resource | Production identifier |
| --- | --- |
| Worker | `uah-r6-submissions` |
| Worker URL | `https://uah-r6-submissions.r6-necc-stats.workers.dev` |
| R2 bucket, Standard class | `uah-r6-replay-submissions` |
| D1 database | `uah-r6-submissions` |
| D1 ID | `f8e47ffc-7049-4bcd-b35a-407c5ee065b2` |
| Turnstile widget | `UAH R6 Replay Submissions`, managed, `uah-r6.github.io` only |
| Cleanup schedule | Hourly, minute 17 UTC |

R2 has no public bucket URL. Object names are generated UUIDs, never supplied
paths. Original folder/filenames, submitter name, optional Discord and notes,
requested team/season, date and opponent stay in the private inbox. They are not
included in exported public statistics. Public completion reveals only a display
ID. Administrator notes and submission identifiers are not copied into map notes.
Normal published opponent/date/statistics still come from confirmed local imports.

Upload tokens are random, limited to one submission and expire after two hours.
Only their hashes are stored in D1. Admin authorization is a separate strong
Worker secret. The public browser and localhost browser never receive that secret:
the local FastAPI backend reads `data/private/submissions.json` automatically.
The private directory, staging files, replay archive, SQLite and downloaded raw
replays are ignored by Git. Back up the existing database and private archive;
R2 is a temporary inbox, not their replacement.

## Submitter workflow

1. Open Submit Replays; explicitly select the UAH team and active season.
2. Enter opponent, match date, name, and No/Yes/Not sure for rehost. Discord/notes
   are optional and private.
3. Select the installed game's `MatchReplay` folder. Granting directory access
   scans locally; it does not upload the whole directory. The alternate folder
   picker supports browsers without `showDirectoryPicker`.
4. Select the complete folders belonging to this one series, including rehosts.
   The list shows folder dates, names, `.rec` counts and sizes, newest first.
5. Review the prominent team/season and totals. Check the confirmation and click
   **Submit for Review**. Hashing and transfer progress are displayed.
6. Keep the page and original selection open if retrying an interrupted upload.
   Completed files are retained; only unfinished files transfer again. Cancel
   releases the session through cleanup. Expired sessions require a new submission.
7. A receipt appears only after every declared file passes server storage checks.
   Submission alone does not publish or import statistics.

Replays are inside the game's installation directory, according to [Ubisoft's
Match Replay help](https://www.ubisoft.com/en-ca/help/article/000100946). The form
provides Steam/Ubisoft Connect guidance and an example path; library locations
and launcher menu wording vary. No ZIP creation or individual-file picking is
needed. Browser scanning identifies replay folders, not Ranked/Custom eligibility:
only the trusted local parser establishes match type and team membership.

## Local review and import

Launch **Start NECC Admin.cmd**, then open **Submissions**. The pending badge,
private list and storage card update without entering CLI commands.

- Review shows **Submitted as** and editable **Importing as** context. A mistaken
  public team/season can be corrected here. Changing context clears inspected
  selections and requires validation again.
- **Download, verify & inspect locally** saves to
  `data/submission-staging/<submission-uuid>/<folder-uuid>/`. Physical `.rec`
  filenames remain intact. Inventory, ownership, size, SHA-256 and replay header
  are rechecked. Existing intact downloads are reused.
- Inspection uses the existing Siege parser and roster matching. Ranked and
  other matchmaking replays remain ineligible; a Custom Game is not automatically
  NECC. Existing replay identity/fingerprint duplicate checks remain authoritative.
- Select one normal map, or multiple segments of one rehosted map, and choose
  **Open existing import review**. The existing preview, team identity, duplicate,
  explicit NECC, rehost ordering/exclusion/roster/final-score safeguards apply.
  Import multiple normal maps separately; do not combine a whole series as one
  rehost. Rehost notes are hints, not score/order authority.
- A folder is consumed only after SQLite import and a verified healthy local
  archive. A series stays Reviewing until all folders are imported or rejected.
- If cloud status sync fails, valid local stats/archive remain intact. The local
  receipt is saved first. Use **Retry cloud status sync**; do not import again.
- Reject remaining folders with a reason and optional private notes. Rejection
  does not change historical data. If some folders were already imported, those
  remain imported and the remainder is recorded as rejected.

Cloud objects for imported/rejected submissions are retained seven days, then
removed. Lightweight private audit metadata remains. Pending/reviewing objects
never expire merely because they are old. Manual terminal-file removal requires
the display ID; it preserves local archives. Verified staging remains private
on this PC and can be removed after local import/rejection when no retry is needed.

## Storage, abuse controls and costs

Default cap: **9 GiB / 9,663,676,416 bytes**, including actual R2 bytes and active
reservations. An atomic D1 transaction reserves the full declared submission
before any transfer. Concurrent intake cannot exceed the configured cap. Warning
crossings at 75/85/95/100 percent are recorded; the local card displays the current
threshold. Reconciliation counts actual R2 object sizes, including unexpected
objects, repairs interrupted acknowledgments and detects missing objects.
Maintenance leases serialize cleanup/reconciliation across Worker instances.

| Limit | Value | Observed local baseline |
| --- | ---: | ---: |
| Single `.rec` | 64 MiB | Largest 14,626,922 bytes; mean 9,141,834 bytes across 209 files |
| One series submission | 2 GiB | Largest existing folder 144,741,994 bytes |
| Folders per submission | 12 | Headroom for BO5 and multiple rehosts |
| `.rec` files per submission | 240 | Headroom for long maps and rehosts |
| Upload session | 2 hours | Expired partial uploads are cleaned |
| Submission rate | 5/hour per hashed IP; 30/hour globally | No raw IP stored |
| Terminal cloud retention | 7 days | Pending/reviewing never age out |

Streamed uploads check their byte length, `.rec` names and `dissect` replay header.
R2 independently validates SHA-256; local downloads validate it again. No untrusted
ZIP extraction, supplied destination path or cloud replay execution exists.
Turnstile, a honeypot, strict origins, ownership checks and expiring capabilities
complement the rate/cap limits. Turnstile can be omitted deliberately by removing
both site-key and secret bindings, but production uses it.

This deployment did not enable a paid plan/add-on. [R2 Standard free allowances](https://developers.cloudflare.com/r2/pricing/)
include 10 GB-month storage, one million Class A and ten million Class B requests;
internet egress is free. [Workers Free limits](https://developers.cloudflare.com/workers/platform/limits/)
include 100,000 requests/day and a 100 MB request body ceiling, above our 64 MiB
file limit. The implementation streams each file rather than buffering a series.
The cap covers this bucket; account-wide free allowances also include other R2
usage. It is a storage guard, not a guarantee against every possible request-based
bill. Monitor the Cloudflare account usage dashboard. Do not enable paid products
to work around a quota; pause intake and review/clean it instead.

## Routine maintenance and emergency disable

All normal maintenance is in the local Submissions page:

- **Reconcile storage** follows paginated R2 inventory and updates actual/reserved
  accounting. Uploads/reservations pause during the scan; retry if transfers or
  another maintenance step are active. Interrupted scans restart safely after
  their lease expires.
- **Run retention cleanup** removes expired partial sessions and terminal objects
  whose safety window ended. Each run handles up to four submissions; hourly cron
  continues the queue. It is idempotent and skips active transfers.
- **Sync team/season choices** updates public intake options from real active local
  teams/seasons after changing semesters or adding a team. Publish the normal site
  data as well so public options agree. The public browser requires both sources
  to recognize the choices.
- **Disable public submissions** immediately rejects new intake while preserving
  reviewable files and valid local statistics. Enable again after maintenance.
  Existing scoped sessions can complete. For account-level emergency shutdown,
  set `SUBMISSIONS_ENABLED` to `false` and redeploy the Worker.

Unexpected R2 objects are included in usage but never silently deleted. Investigate
their ownership before removal through the private Cloudflare bucket dashboard,
then reconcile. Normal accepted/abandoned uploads have generated keys and are
handled automatically.

## Deployment and credential rotation (debug/power-user)

Wrangler OAuth is stored by Wrangler outside this repository. No OAuth token is
copied into project files. From `cloudflare/submissions`:

```powershell
npm.cmd ci
npm.cmd test
npx.cmd wrangler d1 migrations apply uah-r6-submissions --remote
npx.cmd wrangler deploy
```

Migration SQL must retain LF and uppercase BEGIN; `.gitattributes` enforces LF.
The first deployment encountered Cloudflare's compound-trigger statement splitter;
parenthesized CASE expressions and LF fixed it, and remote migration succeeded.

Worker secrets: `ADMIN_SECRET`, `IP_SALT`, `TURNSTILE_SECRET`. The site key and
Worker URL are intentionally public. Rotate the admin secret by generating a new
32-byte random value into ignored private configuration, updating the Worker
secret through Wrangler's secure stdin/file input, then changing `admin_token`
in `data/private/submissions.json` to the same value. Never paste the full secret
into logs, issue bodies, tracked files or public browser configuration. The local
backend rereads its private configuration each request; no daily manual token entry
is needed. Keep `IP_SALT` private; rotating it resets effective per-IP grouping.
Rotate Turnstile through its Cloudflare widget and update the Worker secret.

Public configuration is `web/public/submissions-config.json` (URL only). Public
release uses the existing Pages workflow; routine statistics publishing still
stages only generated `web/public/data/**/*.json`. It cannot stage private inbox
data. The source feature deployment is a normal reviewed repository commit.

## Troubleshooting and future work

- Inbox unavailable: check public config URL, Worker enable switch, account quotas,
  storage/reservations and Turnstile. Local statistics remain safe.
- Upload failed: keep the page open and retry unfinished files. Back out for a new
  bot challenge if session creation failed. An expired capability requires restart.
- Download checksum/inventory failure: retry staging; `.part` files are removed.
  Do not import a partially verified folder.
- Parser/roster/rehost failure: resolve through existing local review; do not weaken
  parser/team safeguards to accept a public submission.
- Local import succeeded but cloud says Reviewing: retry receipt sync. The local
  archive and database are authoritative. Do not reimport.
- Local inbox not configured: restore the ignored private config on this PC using
  a newly rotated secret. Public config must never contain the admin secret.

Future remote administration should use individual accounts/roles and audited
approvals, not a shared plaintext password. It is not implemented here. Possible
later storage alternatives include a user-managed Drive/Dropbox inbox or storage
on a trusted server; each needs explicit authorization, privacy/access review and
cost limits. Neither replaces the verified private historical replay archive.
