# NECC Rainbow Six statistics

### Verified objective actors

The local parser attributes completed plants/disables through the completing
interaction's stable player UID, declared timer/body components, side and
validated objective occurrence. Canceled/restarted attempts stay separate;
ambiguous identity, unknown body states and incomplete rosters stay unresolved.
Actor provenance is stored and duplicate legacy timer credit is prevented.
Existing SQLite matches are not automatically reparsed or corrected. The deployed
`siege_style_v2` formula remains unchanged. See the [current checkpoint](docs/STATUS_NEXT_STEPS.md).

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

## Rating research

The default Rating is `siege_style_v2`, an independent model frozen before its final professional replay evaluation. `collegiate_v1` remains available as a historical Rating version in Settings. The exact formula, test results, and objective-attribution limitation are in [the deployment review](research/output/rating-deployment-review.md). The reproducible research pipeline uses official Ubisoft replay downloads and public SiegeGG player-map ratings; its sources and commands are in [research/README.md](research/README.md). Downloads, normalized replays, targets, and experiment caches stay under ignored `data/research/`.

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

`data/*.sqlite`, raw replays, ZIPs, parsed data, and private settings are ignored by Git. The committed website JSON omits Ubisoft profile IDs and all opponent player identities. The default `siege_style_v2` Rating uses the frozen eight-feature model and an eight-second trade window; it is neither official Ubisoft EPS nor official SiegeGG Rating. The previous `collegiate_v1` formula remains selectable. KOST counts a round once if any of Kill, verified Objective, Survival, or Traded death applies. A 1vX clutch counts once when a player first becomes their team's only living player against one to five living opponents and their team wins the round; X is fixed at that first moment. Plants and disables remain stored and visible in detailed statistics. `siege_style_v2` deliberately has no player-objective coefficient because replay actor attribution is unresolved.

Objective actor data in current Y11 replays remains under investigation. A unique +100 score change is not reliable proof of who planted or disabled. New Y11 imports require a verified player-packet actor source, and recalculation rejects even historical objective credits that give a plant to a defender, a disable to an attacker, or an event to the wrong team. Stored replay events remain available for later parser repair. The local website JSON only reflects a recalculation after **Statistics → Recalculate Statistics**; nothing is published until **Publish Website** is used.

For current Y11 replays, attacker operator usage uses the replay header's post-repick selection after the prep timer resets to the action timer. The parser records the initial selection and its action-start source in its local JSON diagnostics. If that header selection is missing or unknown, the player still receives the round and other statistics, but the operator is marked `Unknown` and excluded from operator usage counts. Defense selection retains the original parser behavior. A corrected parser does not rewrite an already imported map by itself: use **Matches → Open map → Reparse this map** with the original replay folder, then review the local statistics before choosing to publish.
