# Match discovery and team map analytics

## Routes and period

Global `/#/matches` defaults to **All UAH Teams**, newest first. Teams come from
published data; this feature creates no new organization. Opponent search is
partial and case-insensitive, with a native datalist of recorded opponents.
Results remain whole series cards with all their logical maps.

| Query parameter | Values / behavior |
| --- | --- |
| `team` | Published slug or existing alias; omitted/invalid means all teams. |
| `opponent` | Partial opponent name; surrounding whitespace ignored for matching. |
| `sort` | `newest` (default), `oldest`, `opponent`; invalid means newest. Legacy `sort=team` is removed from the URL and falls back to newest. |
| `season` | Published season slug or `career`; otherwise the existing period selection. |

Example: `/#/matches?team=blue&opponent=UCF&season=fall-2026`.
Alphabetical sorts use newest series first as their secondary ordering. Search
replaces the current history entry; selector changes create history entries.
Refresh, sharing and back/forward retain URL state. Clear filters resets
team/opponent/sort and preserves period. On `/#/teams/:teamSlug/matches`, the route
owner overrides any `team` query; only opponent/sort controls appear.

Team navigation adds Maps. Routes:

- `/#/teams/:teamSlug/maps?season=fall-2026`
- `/#/teams/:teamSlug/maps/:mapSlug?season=career`

Team switching retains the detail map slug or match opponent/sort and period.
The period selector updates URL and session selection. Played cards open dedicated
details, which link to existing individual match pages.

## Competitive pool and local admin

The full **tracker-supported catalog** and each season's **competitive map pool**
are separate. Public Maps shows only the selected season's configured pool;
unplayed pool members still show No recorded maps yet. Pool membership is shared
by Blue and White, while statistics remain scoped to the owning team.

Open **Start NECC Admin.cmd → Seasons → Competitive Map Pool**. Choose a season,
check canonical map choices, review the selected count and click **Save Map Pool**.
Saved/unsaved state is visible. Reset discards edits. Season changes, workspace
navigation and reload warn about unsaved changes. An empty save requires explicit
confirmation. Saving refreshes local website data; **Publish Website** deploys it.
No CLI, free-form map names, scraping or automatic pool updates are involved.

Configuration lives in local SQLite: `map_pool_catalog`, `season_map_pool_config`,
`season_map_pool`, and `map_pool_schema_version`. Canonical map FKs and unique
season/map keys protect integrity. Ordering is canonical alphabetical; there is
no arbitrary ordering field. Invalid maps, aliases, duplicate maps, nonexistent
seasons and malformed requests are rejected before changing saved membership.
Empty configured pools are distinct from seasons that have not been configured.
Changing one season never rewrites another.

No trusted intended competitive pool existed at migration. The migration therefore
preserved the previous visible **26-map set** for existing seasons once, with admin
origin `preserved_visible_catalog_v1`. This is **not an official Ubisoft pool**.
Choose the desired competitive subset in Admin. New seasons start unconfigured;
they do not silently inherit a guessed pool. Migration is transactional and
idempotent, including after an intentionally empty save. Adding future canonical
maps also requires a catalog/schema migration; existing pools must not silently grow.

Career displays the **active season's pool**, aggregating that team's historical
results on those maps across seasons. If no season is active, Career uses the most
recent configured season (start date, then ID). A specific season always uses its
own pool. Without any configuration, Maps shows a clear unavailable state.

Removing a map affects only grid membership. Imported matches, Series, profiles,
map counts and statistics remain intact. Played out-of-pool maps retain direct
`/teams/:teamSlug/maps/:mapSlug` analytics and all match links, with a subtle
out-of-pool note. They are not deleted or made inaccessible.

## Source and export

`r6stats/map_analytics.py` consumes the **same public round projection** created
by `r6stats/export.py` for each stored normalized logical map. Side comes from the
owning replay team's players, result from the recorded winner, and site from
`Round.site`. No parser is invoked and nothing is inferred from scores, round
positions, operators or current roster membership.

One lightweight document is generated at
`web/public/data/teams/<team>/maps/<period>.json` for every team and season plus
Career. Team aliases receive identical copies. Current production adds four
documents; all 49 pre-existing documents remain identical except the export
timestamp. Publishing validates analytics against original public match rounds.
The browser never fetches individual match documents to reconstruct analytics.
Schema version 2 adds public `pool` identity/name/configuration/membership, ordered
`maps` for grid cards, and `historical_maps` for played out-of-pool details. Local
origin/update timestamps and database IDs are not exported. One presentation
projection selects records from the unchanged aggregation function; no round
calculations are duplicated. Publishing checks canonical pool membership/order,
season/Career references, consistent pools across teams and every numerical record.

Each map contains integer map W/L and round W/L totals, `attack`, `defense`,
`unknown_side`, side-specific `sites`, and lightweight recent match references.
UI percentages are `wins / rounds`, with denominators visible. Career combines
seasons for one owner, never Blue and White. Substitute roles do not affect team
results. Rehost segments are already combined upstream; only selected logical
rounds count. Identical duplicate logical map IDs count once; conflicting map
duplicates or duplicate logical round numbers fail validation.

Unknown/empty site labels remain explicit unknown buckets with raw values
preserved. They remain in side and overall totals but never enter best-site
ranking. Unknown sides remain in overall totals with their own breakdown.
Unrecognized results fail instead of being guessed. Documents contain no player
identifiers, replay paths, evidence or private archive fields.

## Catalog maintenance

`r6stats/map_catalog.py` centralizes presentation identities from the local
siege-dissect `Map` enum in `third_party/siege-dissect/dissect/header.go` and the
adapter's existing `MAP_LABELS` / known numeric labels. Its **26 canonical replay
maps** include legacy maps: this is **not a current competitive/pro map pool**.

Native aliases (`ClubHouseY10`, `KafeDostoyevskyY10`, `ConsulateY7`, etc.) share
readable canonical identities. Production canonical names and native parser
behavior remain unchanged. An unfamiliar recorded label is preserved as an
additional played entry marked unsupported, never silently dropped or guessed.
Tests require every native enum name to resolve into the catalog. Maintain the
catalog when the enum changes. There is no separate React map array or invented
site catalog.

## Presentation and samples

Configured pool cards use canonical alphabetical order. Unplayed cards/details show **No recorded maps yet**, without
0–0 records or fake 0% performance. A side without rounds shows an em dash and
**No recorded rounds**. Defense sites and Attack vs sites stay separate. Commas
may display as slashes without changing the canonical raw site string.

Detailed sites sort by sample descending, rate descending, name ascending.
Best-site summaries require a known site with **at least two rounds**, then rank
by rate, sample and name. Every summary includes record and sample. With no
qualifying site, it says Limited sample. Full site lists are on detail pages;
cards stay compact. Mobile uses one column and reflowing site lists. No new map
images or minimaps are introduced.

## Independent production check

Recomputed from original public rounds without using the analytics helper:

| Owner / map | Maps W–L | Overall rounds | Attack | Defense |
| --- | ---: | ---: | ---: | ---: |
| Blue Border (three maps) | 2–1 | 20–17 | 8–11 | 12–6 |
| Blue Kafe Dostoyevsky | 1–0 | 8–6 | 5–2 | 3–4 |
| Blue Chalet | 1–0 | 7–5 | 2–4 | 5–1 |
| Blue Fortress | 1–0 | 7–3 | 3–1 | 4–2 |
| Blue Nighthaven Labs / UCF | 1–0 | 7–2 | 3–0 | 4–2 |
| White Border | 0–1 | 0–7 | 0–6 | 0–1 |
| White Nighthaven Labs | 0–1 | 6–8 | 3–4 | 3–4 |

UCF Nighthaven (`9db26f1b6ca7`) has Defense W,W,L,W,L,W, then Attack W,W,W.
Defense Command/Servers is 2–0, Storage/Control 1–1, Assembly/Tank 1–1.
Attack Command/Servers is 2–0, Storage/Control 1–0. Overall rate is 77.8%,
Attack 100%, Defense 66.7%.

## Verification

```powershell
.\.venv\Scripts\python.exe -m pytest -q
Push-Location web
npm.cmd test
npm.cmd run build
npm.cmd run build:admin
Pop-Location
.\.venv\Scripts\python.exe scripts/verify-competitive-pool.py
.\.venv\Scripts\python.exe scripts/verify-competitive-pool-ui.py
.\.venv\Scripts\python.exe scripts/verify-competitive-pool-ui.py --url https://uah-r6.github.io/ --output data/research/competitive-map-pool-20261008/live
```

The original analytics-pass preservation verifier uses the ignored baseline in
`data/research/match-map-analytics-20261008/`: every row in all 23 SQLite tables,
every existing public document, protected source/binary/brand hashes, all nine
archive manifests/files and Healthy status, and all nine v3 eligibility paths.
Browser evidence stays in that ignored directory. Future-team, empty-period and
unknown-site fixtures are intercepted responses only. Tests never submit, import,
reparse or modify production data.

Release `0982b0c` passed [Pages deployment](https://github.com/uah-r6/uah-r6.github.io/actions/runs/37858456292).
799 Python tests plus six subtests passed (one optional real-replay smoke skipped),
69 frontend tests, 19 Worker tests, Go tests/vet and both builds passed. Local and
live feature browser checks plus the 33-route public/admin regression passed at
1440/1100/768/390px. All 53 live JSON documents match local exports exactly.
The nine-profile/four-series Rating browser regression passed locally too.

The competitive-pool pass uses its own ignored baseline/reports in
`data/research/competitive-map-pool-20261008/`. The SQLite backup SHA-256 is
`ebcd6f44cddd8d20fa50b55cbc9e19c86edd321d440c3eac6ab7c99a361ab219`.
Migration was first tested on a copy; all 23 original tables and numerical records
were preserved. The real CMD launcher applied migration and opened Chrome.
Admin editor save/reload/isolation/empty-confirmation tests use an isolated fixture
database only; checks of the actual production admin are read-only.

Competitive-pool release `5bfd256` passed
[Pages deployment](https://github.com/uah-r6/uah-r6.github.io/actions/runs/37864885384).
806 Python tests plus six subtests passed (one optional real-replay smoke skipped),
70 frontend tests, 19 Worker tests, Go tests/vet and both builds passed. Isolated
admin saves and local/live public plus actual admin browser checks pass at
1440/1100/768/390px, including the existing 33-route regression. All 53 live JSON
documents match local exports exactly. All nine Ratings and archives remain valid.
