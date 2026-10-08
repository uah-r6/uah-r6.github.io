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
2. Enter opponent, match date and your name. Discord/notes are optional and private.
3. Choose **How many maps are you submitting?** (1–5). Each map independently
   chooses **Normal**, **Rehosted**, or **Not sure**; there is no series-wide rehost flag.
4. Under **Add your replays**, drag the whole `MatchReplay` folder from Explorer,
   or one/multiple match folders. **Choose MatchReplay Folder** and **Browse for
   replay folder** remain available. Discovery never starts an upload.
5. Assign discovered folders to map slots. **Normal** requires exactly one folder;
   **Rehosted** requires at least two ordered parts. Add/remove parts and use
   keyboard-accessible **Move up/down** controls. **Not sure** preserves one or
   more folders for administrator classification. One folder cannot be assigned twice.
6. Candidates appear **oldest first**, with file-time ranges, original folder names,
   file counts and sizes. The scrollable pool is shared by all map slots. File times
   come from browser `File.lastModified`; missing/invalid times show unavailable.
   They identify folders, not official match starts. Repeated additions are kept once
   by inventory and SHA-256; conflicting content is rejected.
7. Adding maps preserves selections. Removing populated maps or switching a
   populated rehost to Normal asks before releasing assignments. Released folders
   remain in the discovery pool.
8. Review the team/season and **Map → Part → Folder** hierarchy, dates and totals.
   Confirm and click **Submit for Review**. Checking, transfer and verification
   progress identifies Map/Part; only assigned files upload, in the saved part order.
9. Keep the page and original selection open when retrying. Completed files remain
   complete; only unfinished files transfer again. Cancel releases the session
   through cleanup. Expired sessions return to selection for a new submission.
10. A receipt appears only after all declared files pass storage checks.
    Submission alone does not publish or import statistics.

Replays are inside the game's installation directory, according to [Ubisoft's
Match Replay help](https://www.ubisoft.com/en-ca/help/article/000100946). No ZIP
creation or individual-file picking is needed. Browser scanning identifies replay
folders, not Ranked/Custom eligibility:
only the trusted local parser establishes match type and team membership.

### Finding replays and protected game folders

**Show me where to find my replays** has numbered instructions and keyboard
accessible Steam/Ubisoft Connect tabs. Steam comes first:

- Steam: open Steam → Library → find and right-click Rainbow Six Siege → Manage
  → Browse local files. In Explorer, find MatchReplay. Drag the whole folder or
  open it and drag the folders for the series. This menu route is documented in
  [official Steam support](https://help.steampowered.com/en/faqs/view/4DBA-E6A9-1115-7852).
- Ubisoft Connect: open and sign in → Library → Rainbow Six Siege → Manage →
  Properties. Read/copy the location in **Installation directory**. Open Explorer
  (Windows + E), paste it into the address bar and press Enter, then find MatchReplay.
  This uses [Ubisoft's current installation-location guide](https://www.ubisoft.com/en-gb/help/connectivity-and-performance/article/finding-the-installation-location-for-your-ubisoft-game/000063991),
  rendered and checked on 2026-10-07. The current article confirms that section;
  it does not establish an Open folder button. For a Steam installation use Steam's
  steps. The previous unverified Local files/Open folder instructions were removed.

Paths appear only in collapsed **Still can't find it?** help. The Steam example
uses the real local game's folder name `Tom Clancy's Rainbow Six Siege` and is
explicitly an example; another drive/library may be used. No Ubisoft default
game path is needed in the public UI.

Chrome/Edge's native `showDirectoryPicker()` can block Program Files/game locations
as sensitive/system folders. The page explains the refusal and provides **Show
me how**; drag the folder from Explorer or try **Browse for replay folder**.
The browser sometimes uses the same `AbortError` for cancellation, sensitive
directories and denied permission, so that case says **No folder added** with
neutral guidance, not an alarming failure. Existing selections stay intact.
See [the picker exceptions](https://developer.mozilla.org/en-US/docs/Web/API/Window/showDirectoryPicker).

Desktop Chrome/Edge are the tested browsers. Drops prefer Chromium's read-only
`webkitGetAsEntry` (or `getAsEntry`) and complete paginated directory reads.
The modern handle API is used only if a read-only entry is unavailable, and is
captured during the event. Both feed the same grouping/selection rules as the native picker
and standard `webkitdirectory` input. Only `.rec` content enters replay groups.
Repeated whole-folder/child-folder additions compare the complete names/size
inventory and SHA-256 content; conflicting same-name folders are rejected. Scans
finish before review is enabled. All selected-file limits and cloud safeguards
remain unchanged. See [Chrome's File System Access guide](https://developer.chrome.com/docs/capabilities/web-apis/file-system-access)
and [directory input documentation](https://developer.mozilla.org/en-US/docs/Web/API/HTMLInputElement/webkitdirectory).

An initial modern-first drop implementation still caused the user's real
**contains system files** popup. Chromium's
[directory-handle access checks](https://chromium.googlesource.com/chromium/src/+/main/content/browser/file_system_access/file_system_access_manager_impl.cc)
apply the picker sensitivity check and prompt to modern dropped directory handles,
too. The correction avoids requesting that API when a read-only entry exists;
capturing both APIs eagerly is insufficient because the modern request itself
can open the blocking prompt. Clicking or keyboard-activating the drop box now
uses the standard read-only input. The explicitly named native picker remains.
See [read-only directory drop guidance](https://web.dev/articles/files/drag-and-drop-directories)
and [entry documentation](https://developer.mozilla.org/en-US/docs/Web/API/DataTransferItem/webkitGetAsEntry).

The standard input is a distinct, read-only browse path and also serves browsers
without the native picker. Chrome and Edge automated input selection successfully
discovered **30 folders / 209 replay files** in the real protected Steam MatchReplay
folder without transfer. Automation supplies the files directly, so this does
**not** prove that every OS chooser permits that path. It is a useful secondary
option, not a guaranteed workaround; Explorer drag/drop remains the primary
fallback. Mobile keeps compact browse controls and recommends the gaming PC.

Browser regression scripts cover modern/legacy whole/single/multiple drops,
duplicates, cancellation/refusal, native/input discovery, keyboard help, rehosts,
selected-only upload manifests, retry/progress/receipt, and four screen widths.
Cloud responses in these tests are synthetic; no production submission is created.
An additional CDP trusted browser drop passes the **real protected directory path**
to Chrome and Edge, exercising their actual directory entry/read implementations:
30folders/209files discovered and zero modern-handle requests. This strengthens
the earlier synthetic drop tests but does not reproduce the Windows Explorer
mouse gesture. The minimal manual final check is: open the live page
in normal Chrome, drag the real MatchReplay folder onto **Add your replays**, and
confirm the discovered folders. **Do not submit** for this check.

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
- Review displays **logical map cards**, the original submitted classification and
  ordered folders, file times/counts/sizes, inspection and roster results.
  **Open Normal Import** opens one reviewed map; **Open Rehost Builder** hands
  off only that map's ordered segments. Both retain the trusted preview, Custom
  Game, team identity, duplicate, explicit NECC, roster/sub, exclusions, round
  mapping and final-score confirmations. No submitter label bypasses validation.
- Correct types, folder assignments and part order locally, then **Save reviewed
  map structure**. Every folder must remain assigned exactly once. The private
  `review.json` records original structure, reviewed structure and dated changes;
  the original cloud submission is preserved. Imported/rejected maps are frozen.
  Unclassified **Not sure** maps cannot open an importer. Legacy flat submissions
  remain available, initially as separate unclassified cards, for explicit grouping.
- After the first confirmed import, later maps reuse the actual local series's
  opponent/team/season/date and `series_id` when scope matches. Corrected team/season
  survives inspection. Changing scope requires fresh inspection and does not
  silently discard structure edits. Submitted dates/file times never create a
  series or override parser/rehost authority.
- A folder is consumed only after SQLite import and a verified **Healthy** archive.
  Rehost segments are consumed together as exactly one reviewed map in reviewed
  order. Other maps remain available. The submission stays **Reviewing** until
  every folder is imported or rejected.
- Cloud failure cannot roll back valid local stats/archive. A private receipt is
  saved first; **Retry cloud status sync** sends only unsynchronized receipts.
  Local receipts also block repeat import and rejection of already imported folders.
- Reject one map's remaining folders, an individual remaining folder, or all
  remaining folders with a reason/private notes. Imported maps remain valid.
  Mixed imported/rejected submissions finish as Imported, with folder dispositions
  retained individually.

Cloud objects for imported/rejected submissions are retained seven days, then
removed. Lightweight private audit metadata remains. Pending/reviewing objects
never expire merely because they are old. Manual terminal-file removal requires
the display ID; it preserves local archives. Verified staging remains private
on this PC and can be removed after local import/rejection when no retry is needed.

## Versioned private hierarchy and migration

New browser submissions use `schema_version: 2`. Intake map indices are 1–5;
`normal` has one segment, `rehost` two or more, `unsure` one or more. Segment
indices are contiguous and explicit, never inferred from timestamps. The Worker
assigns UUID map/folder/file identities and generates private object keys. D1's
additive `0002_logical_maps.sql` stores immutable submitted maps and folder bindings,
private `first_file_modified_at`/`last_file_modified_at`, separate reviewed structure,
and archive import receipts. Existing v1 records default to schema version 1,
with nullable new folder fields; no old pending record is destructively regrouped.

Corrected structure enters the cloud audit only with a verified import receipt;
original map rows remain unchanged. A D1 transaction, review revision check and
receipt guard reject competing claims atomically, including partial segment claims.
Idempotent receipt retries do not overwrite newer corrections. Receipts bind exact
owned folders/order to the local map. All existing global folder/file/byte/storage
limits apply across maps. The overall submission retains **all** its cloud objects
while any map/folder is unreviewed; the seven-day window starts only at terminal
status. Hourly cleanup/reconciliation and private UUID object ownership are unchanged.

### Regression verification

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
npm.cmd --prefix web test
npm.cmd --prefix cloudflare/submissions test
npm.cmd --prefix web run build
npm.cmd --prefix web run build:admin
& ".\Start NECC Admin.cmd"
.\.venv\Scripts\python.exe scripts/verify-logical-submissions-ui.py
.\.venv\Scripts\python.exe scripts/verify-replay-selection-ui.py --source "<actual MatchReplay folder>"
```

The browser tests intercept cloud responses; they do not submit production data.
The required **Normal A + Rehost B/C** workflow runs through real local D1/R2
bindings in Worker tests and both trusted importers/Healthy archive checks in
isolated Python SQLite. Browser tests cover assignment, timestamps, confirmation,
interrupt/retry/cancel/expiry, Turnstile callbacks, corrected admin context, ordered
handoffs and shared confirmed series at 1440/1100/768/390px. The protected-folder
script separately sends real directory paths through Chromium's trusted CDP drops
and input selection in Chrome/Edge. It does not emulate the Windows Explorer mouse
gesture or solve an actual managed Turnstile challenge. `verify-submissions-ui.py`
now delegates to the structured regression. The opt-in live-upload script remains
available for a human Turnstile session; it is not run by normal verification.

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
- Folder blocked/system files: open the in-page **Show me how** help, find
  MatchReplay through Steam or Ubisoft Connect, and drag it from Explorer.
  **Browse for replay folder** is another option; do not change Windows permissions.
- No replay files found: choose MatchReplay or its actual match folders, rather
  than individual files or an unrelated folder. Ensure Siege Match Replay is enabled.
- Folder already added: it is kept once, with its selections intact. A same-name
  folder with different replay contents requires a separate submission.
- Browser verification failed: use **Retry verification** or refresh in your normal
  browser. Managed Turnstile can reject automated browser sessions even when a
  human clicks their checkbox; normal Chrome was independently confirmed to pass.
  [Cloudflare error guidance](https://developers.cloudflare.com/turnstile/troubleshooting/client-side-errors/) explains these challenge failures.
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
