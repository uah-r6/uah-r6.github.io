# UAH Rainbow Six statistics

## Teams, history, and statistics views

The public homepage represents **UAH R6**, with separate UAH Blue and UAH White team pages. All seven existing maps (82 rounds) belong to Blue. White starts empty: no invented roster, matches, or statistics. The current `siege_style_v3` model and all historical statistics remain unchanged.

| View | Scope |
| --- | --- |
| Team season | Maps owned by that team in the selected season |
| Team career | Maps owned by that team across every season |
| Player season | That player's selected season across all teams, with team splits |
| Player career | That player's entire UAH R6 history across all teams |

Ratings aggregate eligible inputs using the existing engine. Display statistics retain every historical map; Rating coverage remains explicit. The period selector includes actual seasons and Career. Alumni are hidden from current rosters/leaderboards by default, with an inclusion control; their profile, map links, operators, and season/career statistics remain accessible.

Public routes use the existing hash router: `/#/teams/blue`, `/#/teams/blue/roster`, `/#/teams/blue/stats`, and `/#/teams/blue/matches` (likewise for White and future teams). Existing `/#/players/<slug>`, `/#/matches/<map-id>`, `/#/players`, `/#/matches`, and methodology routes remain available. Existing public JSON fields remain; new team documents live under `data/teams/<slug>/`. Team slug edits preserve both route aliases and old JSON paths.

## Public presentation and embeds

Player Stats uses compact cards on phones and the sortable table on larger
screens. Player profiles include trusted Series Rating trends, and Matches links
to recorded-series pages with aggregate Player Stats and visible Rating coverage.
Map pages retain individual Ratings and show sparse replay-verified round highlights.
See [series calculation and trust rules](docs/SERIES_EXPERIENCE.md). Help controls explain each metric.
The footer reports the actual public-data export timestamp.

The main Player Stats page shows one team at a time, defaults to UAH Blue, and
keeps team selection in the URL. Career leaderboards are team-specific; player
Career profiles span the program.

Google Sites utility URLs automatically follow the active published season:

- [Blue Player Stats embed](https://uah-r6.github.io/#/embed/blue/player-stats)
- [White Player Stats embed](https://uah-r6.github.io/#/embed/white/player-stats)

Start with an 800 × 360px frame. See [PUBLIC_PRESENTATION.md](docs/PUBLIC_PRESENTATION.md)
for responsive columns, historical overrides, keyboard help, framing verification
and static social-preview limitations.

## Public replay submissions

Use [Submit Replays](https://uah-r6.github.io/#/submit) to send complete MatchReplay folders privately for review, including rehost segments. Select the team and season explicitly. Uploading does not import or publish statistics.

The local **Submissions** section downloads and verifies the private inbox, then opens the existing normal/rehost review. It also manages storage, retention, rejection, context corrections and cloud status retries. Cloudflare R2 is temporary; the local verified archive remains authoritative. See [SUBMISSIONS.md](docs/SUBMISSIONS.md) for privacy, limits, configuration and maintenance.

## Local administration

Double-click **Start NECC Admin.cmd**. Choose an **active team** and **season** in the persistent top controls. An initial team choice is required; the application never silently assigns an import to Blue.

- **Teams:** add teams, edit names/slugs/colors/order, activate/deactivate. Deactivation preserves history. Color accents adapt for readable contrast.
- **Roster:** add a teammate with a membership start date, maintain aliases, inspect membership history, move an existing player with an effective date, or mark Active/Alumni. Moves close the old membership and open the new one without duplicating the player or moving past maps. Dates use half-open intervals: the move date belongs to the new team.
- **Import Match:** scan, select one Custom Game, preview the selected team's dated roster matches, and confirm opponent/season/NECC membership. The final button names the team and season. Changing context clears the preview; the API independently rejects mismatched context. Ranked/Standard/Quick Match stay ineligible. Rehost segments must validate for the same team/season.
- **Matches:** scoped history, metadata editing, confirmed deletion, and existing archive operations. A map's organization team is immutable; series grouping cannot cross team/season. Archive reparse retains ownership and stored historical player bindings.
- **Statistics / Publish:** maintenance and publishing operate across the program, all teams and seasons. Public Pages remains static/read-only. Publishing failure never rolls back local data.
- **Settings:** program branding, local replay path, existing statistics and Git settings. Individual team colors/names belong in Teams.

Player status is separate from team membership. Use only **Active** and **Alumni**. Show other teams/unassigned players to move an existing identity instead of adding a duplicate.

CLI/debug imports additionally support `--organization-team <stable-id>`; `--team 0/1` still means the replay's Siege side. Roster CLI additions also require `--organization-team`. Normal management uses the browser.

The metadata migration is automatic and transactional on connection, with a one-time version marker. Existing players retain status and identity, existing maps/series become Blue, and White remains empty. Back up **both** SQLite and `data/replay-archive/`. This deployment's ignored pre-migration backup and preservation report are under `data/research/team-architecture-20261007/`.

Verification commands (PowerShell, repository root):

```powershell
.\.venv\Scripts\python.exe -m pytest -q
npm.cmd --prefix web test
npm.cmd --prefix web run build
npm.cmd --prefix web run build:admin
.\.venv\Scripts\python.exe scripts\verify-team-migration.py --backup data/research/team-architecture-20261007
# Optional browser checks require Playwright and Microsoft Edge:
.\.venv\Scripts\python.exe scripts\verify-team-ui.py
.\.venv\Scripts\python.exe scripts\verify-team-admin-ui.py
```

Official logo/font/color provenance: [BRANDING.md](docs/BRANDING.md). The program-level root can later support a broader Esports landing page. Public replay submission, authentication, queues, other games, and hosted storage are future work and are not implemented here.

### Credited kill counts

Complete validated whole maps use Ubisoft's stable UID scoreboard round deltas
for kills, K/D, KPR, side kills, multikills, and KOST's Kill component. Raw replay
finisher events remain stored separately. Unsupported whole maps retain legacy
counts; player pages and public JSON report credited/legacy round coverage.
Openings, trades, pivots, untraded features and clutch chronology retain existing
event semantics. Headshot percentage retains finisher headshots/finisher kills.
Original v2 Rating inputs and objective corrections are preserved.

New confirmed imports collect counts locally from their verified archive; parser
compatibility failures retain the valid imported map with an explicit legacy
source. Recalculate/Regenerate use stored evidence and never reparse archives.
See [readiness and rollback](research/output/credited-production-readiness-20261006.md).

### Verified objective actors

The local parser attributes completed plants/disables through the completing
interaction's stable player UID, declared timer/body components, side and
validated objective occurrence. Canceled/restarted attempts stay separate;
ambiguous identity, unknown body states and incomplete rosters stay unresolved.
Actor provenance is stored and duplicate legacy timer credit is prevented.
Existing SQLite matches are not automatically reparsed or corrected. The deployed
`siege_style_v3` formula remains unchanged, and original v2 inputs stay preserved. See the [current checkpoint](docs/STATUS_NEXT_STEPS.md).

A local, NECC-only replay tracker. Python parses explicitly selected Siege match folders or ZIPs with [Lumina's siege-dissect](https://github.com/lumina-r6/siege-dissect), stores normalized rounds in private SQLite, and exports teammate-only JSON to a React/Vite site. The public GitHub Pages site is static and read-only. A separate FastAPI admin runs on your Windows PC at `http://127.0.0.1:8000/admin` for day-to-day management. Replay files have no NECC tag: a manually selected and confirmed **Custom Game** is assigned `competition = "NECC"` by this application. Ranked, Standard, Quick Match, and other matchmaking replays are rejected before any database write. Scrims and other Custom Games are never imported automatically.

## Requirements

- Windows with Python 3.12 or newer (`py -3.12`), Node.js 22 or newer, and Git.
- Internet access during the first setup so Go dependencies can be downloaded. The script builds the checked-in [local siege-dissect source](third_party/siege-dissect/README.md), based on a pinned Lumina revision. It downloads a portable Go toolchain into the ignored `.local-tools` folder if Go is not already installed.
- A complete Rainbow Six MatchReplay **match folder** containing all `.rec` rounds. One `.rec` is deliberately rejected.

Double-click **`Start NECC Admin.cmd`** in this repository. On first launch it runs setup, starts the local FastAPI server, and opens the admin dashboard in your default browser. If you prefer to run first-time setup explicitly, use PowerShell in this repository:

```powershell
.\scripts\setup.ps1
```

If PowerShell blocks scripts, run `powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1` from a terminal. The script creates `.venv`, installs Python and Node dependencies, builds the local admin UI and replay parser, copies `config/settings.example.json` to your private `config/settings.json`, and initializes SQLite. It never changes global execution policy.

## Start the local admin

After setup, **double-click `Start NECC Admin.cmd`** in this folder for normal use. It starts the local server in the background and opens the admin in your default browser. If a server from this project is already running, the launcher checks its imported paths and startup source hashes; it restarts that server when the Python source has changed. A replay scan always requests fresh results. The underlying [start.ps1](start.ps1) activates `.venv` and completes setup if needed. For server logs or troubleshooting, start it from PowerShell instead:

If launching the CMD file from a terminal, keep its spaced filename as one argument: use `& ".\Start NECC Admin.cmd"` in PowerShell or `call "Start NECC Admin.cmd"` in CMD.

```powershell
.\scripts\start-admin.ps1
```

The address is **http://127.0.0.1:8000/admin**. Keep the PowerShell window open if you used the troubleshooting command. The server binds to your PC's loopback address; it does not expose the private database to GitHub Pages.

For troubleshooting, **http://127.0.0.1:8000/api/admin/runtime** shows the running process ID, Python executable, working directory, imported module paths, parser executable and SHA-256 hash, and startup source hashes. The launcher uses this information to avoid reusing old code. Python is run from this repository's working directory; setup installs dependencies into `.venv`, not a separate copy of `r6stats` into site-packages.

In **Settings**, enter your team name and Siege `MatchReplay` folder. The default folder is `Documents\My Games\Rainbow Six - Siege\MatchReplay`. Settings also holds the trade window, Rating version, GitHub repository URL, branch, and optional public website URL. In **Seasons**, create your semester, such as “Fall 2026,” and optionally set start and end dates. You can rename it later without changing its stable ID or historical maps. In **Roster**, add teammates' exact Ubisoft usernames, with optional display names. Matching ignores case and surrounding whitespace. You can update a username, add aliases, edit display names, and deactivate players without deleting past match data. The UI shows whether a Ubisoft profile ID has been linked, without displaying the ID itself prominently.

The **Dashboard** shows the active season, tracked roster count, real maps, last import, last successful publish, and database integrity. **Matches** defaults to the active season. Open any map to review its rounds, edit its date or series grouping, change opponent/week/notes, or delete an accidental import after a confirmation dialog. Deletion removes that map's rounds and events, recalculates public aggregates, and retains roster identities. To correct stored replay-derived fields after a parser fix, paste that map's original replay folder path into **Reparse this map**. Reparse verifies the replay ID and content fingerprint, replaces rounds in one transaction, and preserves season, opponent, date, week, notes, series, map ID, and player identities. It regenerates local website data without publishing. **Statistics** has separate **Recalculate Statistics** and **Regenerate Website Data** actions. Both read stored normalized matches and rebuild derived values; there is no separate aggregate cache to become stale. **Publish** validates and submits generated website data to GitHub. These routine tasks do not require CLI commands.

## Import an NECC map in your browser

Open **Import replay**, then click **Scan replay folder**. The scan lists the 12 most recent replay folders and match types without importing anything. Custom Games with a complete set of rounds are eligible for normal manual selection. Ranked, Standard, Quick Match, and other matchmaking types are ineligible. A one-round Custom Game cannot be imported as a normal map, but can be selected as a segment of an explicitly confirmed rehost. You may also paste the path to one complete match folder or a ZIP containing exactly one whole match folder.

Locally generated Siege folders are named `Match-...` and contain `Match-...-R01.rec`, `-R02.rec`, and so on. The app takes round numbers from those filenames because current siege-dissect output numbers rounds from zero. Missing or duplicate physical round suffixes are rejected. The scan's **roster matches** count means distinct configured active Ubisoft usernames or linked profile IDs found across the replay's rounds; it does not imply that a Custom Game was an NECC match.

Click **Preview** on the Custom Game you recognize as an NECC map. Review the map, score, rounds, date, game mode, and tracked teammates. If the roster does not identify one side clearly, choose the team after inspecting both player lists. Select the season (the active season is preselected), enter the opponent, and optionally set the NECC week and notes. For later maps in the same matchup, choose the existing series from the dropdown. Check the explicit NECC confirmation box and click **Import NECC map**. This manual choice assigns `competition = "NECC"` internally; the replay itself needs no NECC identifier. Each map is deduplicated by replay ID and content fingerprint. Opponent replay identities stay in local SQLite and never appear in public JSON.

Import refreshes the local public JSON. Open **Publish** and click **Publish website** when ready to update GitHub Pages. Scrims and other Custom Games stay out of the season unless you manually select and confirm them.

## Private replay archive

For a competitive map that continued in a new Custom Game lobby, open **Import Match → Rehosted map**. Select the physical MatchReplay folders in their competitive order, including any one-round abandoned lobby, mark each abandoned physical round as excluded with a reason, and check the proposed logical round order and score. Enter the final competitive score and explicitly confirm that the folders belong to one NECC map. The preview shows actual players in each segment and each round. A changed roster requires an additional confirmation; an absent player receives no stats or round participation for rounds they missed. A correctly carried physical score needs no override. If a later lobby physically restarted at 0–0 after competitive rounds were played, review and confirm the logical-score override. The server verifies map, mode, shared team identities, round mapping, and score before import. Long downtime is allowed. The normal one-folder import remains the default and requires no rehost settings.

An imported rehost has one map ID and a private archive with separate `segment-01`, `segment-02`, and later folders. Its map detail shows the physical-to-logical round mapping. **Reparse from archive** verifies all segment hashes and reapplies the stored exclusions. Manual reparse or backfill requires every original segment folder in the confirmed order.

If a competitive map is missing trustworthy replay rounds, open it under **Matches → Manual K/D Correction**. Enter each affected roster player's final map kills and deaths, a reason, and an optional note. The admin shows the replay totals and computed adjustment, and allows editing or removing the correction. Only displayed map, season, and career kills/deaths/KD change. KPR, KOST, Rating features, operators, objectives, and other round-derived statistics remain replay-derived. The map is marked partial and excluded from Rating; season and career Rating use only complete eligible maps. Removing a correction restores raw replay K/D, but leaves the map marked partial until the missing replay data is actually recovered. Corrections and reasons stay in local SQLite and are not published.

Every confirmed, successful NECC map import copies its complete `.rec` rounds to `data/replay-archive/<season-id>/<map-id>/`. The original MatchReplay files stay in place. The archive is local and Git-ignored; its manifest records the replay fingerprint, parser hash, source path, original filenames, physical round numbers, file sizes, and SHA-256 hashes. Previewing a replay or rejecting an import does not create a completed archive.

Open a map in **Matches** to see its archive status. **Verify archive** checks every round before **Reparse from archive** can use it. Reparse keeps the map ID, season, opponent, date, week, notes, series, and player identities; a failed reparse leaves stored statistics intact. Older maps show **Not archived** until you backfill from their original complete replay folder or ZIP. Backfill checks the exact stored replay fingerprint and round count and does not change statistics. **Open archive folder** opens the private copy in Explorer.

When you intentionally delete a map, the confirmation also covers its private replay archive. The normal delete removes both, while preserving historical roster identities. Keep independent backups of `data/r6stats.sqlite` and `data/replay-archive/` if you need disaster recovery. Publishing stages only generated website JSON under `web/public/data/`; it never stages archives or research downloads.

**Recalculate Statistics** rebuilds aggregates from stored parsed data; it does not rerun the replay parser. **Regenerate Website Data** exports that data. Parser improvements need an archive operation first. On a map, **Refresh objective actors** reparses its verified archive and updates only supported completing-timer-owner plants/disables. It retains unsupported historical credits, kills, operators, identities, metadata, and the confirmed rehost mapping. **Reparse from archive** is the broader replay replacement operation.

Objective-only refresh saves the original normalized map in an immutable `siege_style_v2` input snapshot before replacement. Corrected objective counts and displayed KOST use the upgraded data; historical map/season/career v2 Ratings use the original inputs. The frozen coefficients and original final MAE 0.03623 are unchanged. If a subsequent reparse changes nonobjective inputs covered by a snapshot, export refuses it pending review rather than silently changing the historical Rating baseline. Unsupported Kafe R09 and incomplete-roster Chalet R10 objective actors remain unresolved by the production resolver.

## Rating research

The default Rating is `siege_style_v3`, the frozen nine-feature credited-count/native-order model that passed its untouched APAC North Stage 1 final. `siege_style_v2` and `collegiate_v1` remain selectable in Settings; original v2 snapshots and coefficients are unchanged. V3 uses only whole maps with complete credited-kill, native elimination and verified core objective evidence. Current UAH Rating coverage is 4 maps / 42 rounds, while all 7 maps / 82 rounds remain in displayed statistics. Rating tooltips/player pages report coverage. See the [v3 deployment review](research/output/native-v3-deployment-review.md), [final result](research/output/v3-native-final-apac1-result.md), and [historical v2 review](research/output/rating-deployment-review.md). The reproducible research pipeline uses official Ubisoft replay downloads and public SiegeGG player-map ratings; its sources and commands are in [research/README.md](research/README.md). Downloads, normalized replays, targets, and experiment caches stay under ignored `data/research/`.

## GitHub Pages setup and publishing

```powershell
.\scripts\start-admin.ps1
```

Use the local admin for previews and publishing after the one-time GitHub setup. **Publish Website** exports and validates public JSON, builds the public site, stages only generated `.json` under `web/public/data`, creates a commit identifying the active season and map count, and pushes to the branch set in **Settings**. If you enter a GitHub repository URL in Settings, the publish action configures the local `origin` remote. A failed build, commit, or push never changes valid SQLite match data. A failed push can be retried with the same button even if the JSON has not changed. If there is no Git repository yet, create one, commit the application once, create a GitHub repository, add its remote, and push `main`; subsequent stat updates use the browser.

For a new GitHub repository, after creating an **empty public repository** named `r6-necc-stats` in GitHub, run these once from this project directory (replace `YOUR_GITHUB_NAME`):

```powershell
git init
git branch -M main
git add -- .gitignore README.md pyproject.toml requirements.txt config/settings.example.json r6stats tests scripts web .github start.ps1 "Start NECC Admin.cmd"
git commit -m "Create NECC stats tracker"
git remote add origin https://github.com/YOUR_GITHUB_NAME/r6-necc-stats.git
git push -u origin main
```

Private settings and SQLite are ignored. `web/public/data` initially contains clearly labeled synthetic sample data; a real export replaces it after your first import.

In GitHub, open **Settings → Pages → Build and deployment → Source** and choose **GitHub Actions**. The included workflow builds on every push to `main` and deploys `web/dist`. On GitHub Free, use a public repository; verify that its published JSON contains only the teammates and match context you want public. The site uses a repository-aware Vite base path and hash routes, so player links work under a Pages project URL. These steps follow [GitHub's custom Pages workflow guide](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).

## Demo and recalculation

```powershell
.\.venv\Scripts\python.exe -m r6stats demo
.\.venv\Scripts\python.exe -m r6stats demo --clear
.\.venv\Scripts\python.exe -m r6stats recalculate
```

These are optional debugging commands. Demo creates four deterministic synthetic maps and fills missing roster places with clearly named demo players. The website labels synthetic data. Clear demo maps **before** importing a real match; real and demo maps cannot coexist. The browser's **Recalculate data** button rebuilds published aggregates from authoritative normalized rounds, so a trade-window change does not require reimporting replay files.

## Optional CLI

The CLI remains available for debugging and power users:

```powershell
.\.venv\Scripts\python.exe -m r6stats scan
.\.venv\Scripts\python.exe -m r6stats import "C:\path\to\Match-folder"
.\.venv\Scripts\python.exe -m r6stats roster list
.\.venv\Scripts\python.exe -m r6stats season list
.\.venv\Scripts\python.exe -m r6stats recalculate
.\.venv\Scripts\python.exe -m r6stats publish
```

The CLI import also requires explicit NECC confirmation. `python -m r6stats update` and `scripts/update-stats.ps1` remain available for an interactive terminal workflow.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
cd web
npm.cmd run build
npm.cmd run build:admin
```

Tests cover adapter normalization, Custom Game eligibility and explicit confirmation in both CLI and admin API, rejection of matchmaking types, duplicate imports, season editing and database upgrades, map grouping and deletion, historical player retention, publishing validation, entries, trades, KOST, survival, clutch wins, pivot examples and a Rating snapshot. A real replay integration test remains dependent on a supplied compatible `.rec` match folder.

To run that optional integration test, set the environment variable for one terminal session before `pytest`:

```powershell
$env:R6_TEST_REPLAY_PATH = "C:\path\to\complete\Match-folder"
.\.venv\Scripts\python.exe -m pytest -q
```

## Common problems

- **Parser not found:** rerun `scripts/install-parser.ps1`; it builds the repository parser source into `.local-tools/bin`. The normal launcher also rebuilds when source hashes change.
- **Wrong replay folder:** set the MatchReplay directory in the admin **Settings** page.
- **Ranked/Standard/Quick Match rejected:** this is intentional; select the Custom Game replay from your NECC match and confirm it with **NECC**. Other Custom Games, such as scrims, should be left unselected.
- **Teammate renamed:** add the new username on the admin **Roster** page; conflicting profile IDs are rejected.
- **Duplicate replay:** select a different map. Already imported maps cannot double count.
- **Unable to inspect a replay:** keep the folder intact. Some locally generated rounds still make the pinned siege-dissect parser fail; the scanner leaves those folders ineligible and imports no data. Rebuild the pinned parser after a compatible upstream fix and scan again.
- **Git authentication failed:** authenticate Git, then run `git push origin main`.
- **Site not redeploying:** confirm GitHub Pages source is **GitHub Actions** and inspect the repository's Actions tab.
- **No events or wrong score:** keep the replay folder locally and use the CLI's `--verbose` flag for debugging; parser formats can change across Siege seasons. Do not import a preview whose score or roster looks wrong.

## Data and methods

`data/*.sqlite`, raw replays, ZIPs, parsed data, and private settings are ignored by Git. The committed website JSON omits Ubisoft profile IDs and all opponent player identities. The default `siege_style_v3` Rating uses its frozen nine-feature model and eight-second legacy trade policy; it is neither official Ubisoft EPS nor official SiegeGG Rating. Both previous `siege_style_v2` and `collegiate_v1` formulas remain selectable. KOST counts a round once if any of Kill, verified Objective, Survival, or Traded death applies. A 1vX clutch counts once when a player first becomes their team's only living player against one to five living opponents and their team wins the round; X is fixed at that first moment. Plants and disables remain stored and visible in detailed statistics. `siege_style_v2` has no separate player-objective coefficient: its weights remain frozen from research conducted before trustworthy actor attribution was available. Verified objectives can still qualify a round for KOST.

The local parser now requires a validated objective completion plus a unique completing interaction owner, stable UID, correct side, and supported body/lifecycle evidence. A unique +100 score change or near-zero timer is insufficient. Canceled attempts do not receive credit, and unsupported or ambiguous evidence remains unresolved. Installing the parser does not correct stored maps automatically. Recalculation rejects historical objective credits that give a plant to a defender, a disable to an attacker, or an event to the wrong team. Stored replay events remain available for later parser repair. The local website JSON only reflects a recalculation after **Statistics → Recalculate Statistics**; nothing is published until **Publish Website** is used.

The separate v3 objective research improved new-event MAE but failed its frozen acceptance gate; it is not deployed. See the [one-shot result](research/output/v3-final-apac-n-stage2.md) and [UAH read-only contribution report](research/output/v3-uah-readonly.md). No historical corrections or public data updates were applied during that research.

For current Y11 replays, attacker operator usage uses the replay header's post-repick selection after the prep timer resets to the action timer. The parser records the initial selection and its action-start source in its local JSON diagnostics. If that header selection is missing or unknown, the player still receives the round and other statistics, but the operator is marked `Unknown` and excluded from operator usage counts. Defense selection retains the original parser behavior. A corrected parser does not rewrite an already imported map by itself: use **Matches → Open map → Reparse this map** with the original replay folder, then review the local statistics before choosing to publish.

### V3 input safety and rollback

Recalculate/Regenerate derive v3 from stored normalized rounds, complete credited evidence, and private objective occurrence evidence; neither reparses archives. New imports already collect the Go credited/native evidence. Reparse/Refresh invalidate historical v3 objective evidence when normalized input hashes change; fresh data must pass all gates again. Unsupported maps are preserved and shown unrated rather than assigned guessed or zero inputs. Global legacy display chronology and action-start operators are unchanged. Native openings explicitly mean the first opposing **finisher** elimination, not an inferred credited owner. Clutches use the first sole-survivor state in verified serialized order with weight X(X+1)/2. Precise credited trades remain unresolved; v3 retains its tested legacy 8-second trade inputs.

The deployment's verified rollback backup is private under `data/research/native-v3-deployment-20261007/`: `before.sqlite`, `before-settings.json`, and `before-public/`. To roll back locally, stop the admin server, restore these to `data/r6stats.sqlite`, `config/settings.json`, and `web/public/data/`; archives stay intact. Production publication rollback would require a reviewed revert/export commit. Historical research seals stay immutable; use the current `research/verify_native_v3_checkpoint.py` guard after deployment, not older source-hash checkpoint guards.

### Substitute players

Local **Roster** administration supports a regular roster, global eligibility to
substitute for any UAH team, and sub-only players without a regular membership.
Active/Alumni remains separate. Preview shows ROSTER/SUB before confirmation,
and map details retain the frozen import role. Public Player Stats defaults to
Blue / active season / Roster; Subs and player **View Sub Stats** are separate.
Sub appearances never enter normal season, Career or Rating trends.
See [substitute architecture and verification](docs/SUBSTITUTES.md).
