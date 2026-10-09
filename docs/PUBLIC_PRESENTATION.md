# Public presentation and Google Sites embeds

## Competitive map pools and match sort cleanup (2026-10-08)

Public Maps now uses a season-specific competitive pool configured under local
**Admin → Seasons → Competitive Map Pool**. Canonical supported maps remain a
separate catalog. Career shows the active season's pool with Career team results;
without an active season it falls back to the latest configured season. Unplayed
selected maps remain empty cards; removed played maps retain historical detail
URLs. Grid order is alphabetical. Existing visible maps were preserved once during
migration because no trusted intended pool existed; the user can narrow it in Admin.
This initial list is not an official Ubisoft pool.

Matches sort options are Newest, Oldest and Opponent. UAH Team sorting was removed;
the Team filter is unchanged. Legacy `sort=team` URLs normalize to Newest without
losing team/opponent/period context. See [MAP_ANALYTICS.md](MAP_ANALYTICS.md).

## Match discovery and Maps (2026-10-08)

Matches now has URL-backed team/opponent/sort filters, preserving whole series
and season/Career context. Team Matches retains owner scope without a redundant
team filter. Team navigation adds Maps and dedicated map details, with map records,
round/Attack/Defense rates, separate side-specific sites, visible samples and
recent-match links. Supported unplayed maps show no recorded data, never fake
zero performance. The browser reads one exported analytics document per team/period.
See [MAP_ANALYTICS.md](MAP_ANALYTICS.md) for query parameters, trusted source data,
catalog maintenance, sample rules and independently verified production counts.

## Program and team presentation (2026-10-08)

Series Rating availability was subsequently corrected to complete-only coverage.
Normal trends now contain complete regular-roster Series Ratings and draw a line
only after two complete series. Broader Season/Career profile summary Ratings
retain their existing trusted-map coverage. See [Series experience](SERIES_EXPERIENCE.md).

The public site is a program hub with a compact UAH Rainbow Six hero, Player Stats
and Submit Replays actions, selected-period summary, logo-forward team cards and
the latest four recorded series. Counts and latest matchups come from the existing
season/team exports. No backend aggregation or public JSON fields were added.
Only published team records create cards; installed Grey/Black logos do not.

Team routes share a prominent identity hero with map record, maps, rounds and a
latest-matchup link. Native team switching retains the route section and Sub
query. Persistent tabs expose their active state with `aria-current`. Overview
places season numbers, the existing player table/cards, then recent series below
the hero, without repeating the same team title. Roster and Player Stats keep
their controls, membership filters, role separation and exact trusted values.

Series history and series pages emphasize the owning UAH team, opponent text,
date and **Recorded maps**. This is an imported-map score, not a claim that a
complete competitive series was won. Series pages show one summary card per map
before player stats. Map cards show both team scores, WIN/LOSS and a small explicit
Rating-eligibility label. Individual map heroes emphasize map, opponent, round
score and period/date. Opponents have no fabricated branding.

Player heroes show Rating, K-D and difference, KOST, and opening K-D/difference.
Rating is the existing exported value, with a Partial label when exported coverage
is incomplete. Regular scoped `team_splits`, rather than current membership or
sub appearances, determine identity. Exactly one contributing team uses its mark;
multiple teams use the program mark and contribution chips. Career remains global,
and Sub Stats stays a separate view. The existing Series Rating trend, detailed
performance, sides, operators and map history retain their values and interaction.

`PublicIdentity.tsx` shares identity and score primitives; `PublicHub.tsx`,
`PublicMatches.tsx`, and `ProfileHero.tsx` compose page context.
`publicView.ts` contains presentation-only counts, grouping, identity, date and
eligibility formatting; it does not calculate Ratings. `publicLayout.css` groups
public composition by identity, hub, team, matches, profile and responsive rules.
Obsolete small card/header/series-hero styling was removed from the earlier CSS
files. Shared tables, help, compact embeds, uploader and admin keep their components.
TeamLogo lookup, fallback and all original PNG bytes are preserved.

The four layouts are checked at **1440/1100/768/390px**, including series with
complete or unavailable Ratings, all nine maps, both teams, normal/sub profiles, Methodology,
Submit Replays and both embeds. Screenshots are inspected as well as DOM assertions.
Phone score sections stack deliberately; table/nav scrolling remains confined to
those elements. Focus and reduced-motion behavior remain available. Future empty
teams show no fabricated 0-0 record; Grey/Black/unknown and multi-team Career use
intercepted browser fixtures without writing production data.

Current focused verification:

```powershell
.\.venv\Scripts\python.exe scripts/verify-public-redesign-ui.py
.\.venv\Scripts\python.exe scripts/verify-public-redesign-ui.py --url https://uah-r6.github.io/ --output data/research/public-redesign-20261008/live
.\.venv\Scripts\python.exe scripts/verify-complete-series-ui.py
.\.venv\Scripts\python.exe scripts/verify-series-completeness-preservation.py
.\.venv\Scripts\python.exe scripts/verify-substitutes-ui.py
.\.venv\Scripts\python.exe scripts/verify-logical-submissions-ui.py
```

The ignored `data/research/public-redesign-20261008/` baseline holds a SQLite
backup, full table rows, original public JSON, protected file hashes and before/
after screenshots. Preservation checks cover all 22 SQLite tables, 49 public JSON
files, 219 backend/parser/archive/logo/submission/trusted-component files, integrity,
foreign keys and all nine Healthy archives. No import/reparse/recalculation/export
or cloud mutations are part of this pass. Tests use temporary/local fixtures;
uploader browser checks intercept uploads, not a real human Turnstile submission.

## Main Player Stats team scope

The main **Player Stats** navigation opens `/#/players?team=blue`. Plain
`/#/players` also defaults to UAH Blue. The visible **Team** selector comes from
the same published team index as existing public team pages, including public
team archives under the existing visibility rules. Future team names/colors
and existing aliases work without a separate frontend list.

The canonical team slug is stored in the hash route's query string. Switching
teams adds browser history; missing/invalid/removed aliases normalize safely to
Blue, or the first active team if Blue is unavailable. With no available default
the page shows an empty state. Refresh and browser back/forward preserve scope.

The existing global season selection remains authoritative. Both season and
Career leaderboards fetch only `teams/<slug>/<period>.json`, sharing the same
Player Stats renderer as `/teams/<slug>/stats`. Sort/Alumni choices survive team
switches; an old network response never renders another team's players under
the selected heading. An empty team never shows another team's statistics.

Historical map ownership remains authoritative because the existing team export
is used directly. **Career leaderboard is team-specific; global player Career
profiles remain cross-team.** Embeds retain their independent team route and
active-season behavior. No statistics are recalculated in the browser.

Current read-only local/live checks include team scope, Career, sorting and Sub
navigation alongside the presentation regression:

```powershell
.\.venv\Scripts\python.exe scripts/verify-public-redesign-ui.py
.\.venv\Scripts\python.exe scripts/verify-public-redesign-ui.py --url https://uah-r6.github.io/ --output data/research/public-redesign-20261008/live
```

## Embed Player Stats

In Google Sites, choose **Insert → Embed → By URL** and paste one of:

- Blue: https://uah-r6.github.io/#/embed/blue/player-stats
- White: https://uah-r6.github.io/#/embed/white/player-stats

The same route works with any valid team slug. These utility URLs are public
and unlisted. They render a compact 32px team identity row and Player Stats,
without navigation, period selector, full-page hero or footer. Player and
definition links open the full website in another tab.

The default URL always reads `active_season` from exported `index.json`, ignoring
the normal site's saved period. Embeds do not access browser storage, so a frame
can render even when that access is restricted. After activating a new season, regenerate and
publish website data; the existing embed then follows that season when loaded.
For a fixed historical view, append `?season=fall-2026` **after the hash route**.
Unknown teams or seasons show a friendly error rather than another team's data.

Start with **800px wide × 360px high** for five players. Google Sites controls
the frame dimensions; a cross-origin page cannot reliably resize that frame.
Resize the embed once in the Sites editor if its surrounding layout requires it.
Additional roster members may require more height. A browser may retain published
data briefly under GitHub Pages caching; reloading refreshes the view.

| Frame width | Columns |
| --- | --- |
| 900px or wider | Player, Rating, KOST, K-D, Entry, KPR, SRV, HS%, Plants, 1vX |
| 650–899px | Player, Rating, KOST, K-D, Entry, KPR, 1vX |
| Under 650px | Player, Rating, KOST, K-D, Entry |

Rating remains visible. Current-season Alumni filtering follows the normal table;
no manually maintained statistics are used. Normal phone views use player cards,
while embeds remain compact tables. Desktop/tablet views retain sortable tables.

Google's [Sites embedding instructions](https://support.google.com/sites/answer/90569?hl=en)
describe the editor workflow. Framing is controlled by HTTP headers, including
[`frame-ancestors`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/frame-ancestors).
Production headers and a real cross-origin iframe are tested by this release.
An actual authenticated Google Sites editor session is not part of these tests.

## What is displayed

- Player Rating trends use **complete exported `siege_style_v3` Series Ratings**,
  calculated once from all trusted counts for the player's relevant participation.
  Incomplete, missing or invalid values are omitted, never converted to zero.
  Zero or one complete series has a compact summary with no graph; two or more
  renders a line. Context shows player-specific map
  and round coverage. Season/career scoping comes from the requested public
  profile; no Rating is recalculated in the frontend. See
  [Series experience](SERIES_EXPERIENCE.md) for the formula and trust rules.
- Dates are chronological. Within one date, the existing export's recorded
  order is reversed from newest-first to oldest-first. No precise start time is
  invented when only a date is available. Hover, focus, click or tap selects
  series context and its exact Rating; arrow keys move between points. Recent
  chips select the same data. Individual map Ratings remain on map pages.
- Series group by authoritative `series_id`, team and season. Logical map IDs
  appear once. **Recorded maps** summarizes stored W/L only; it does not assert
  that the complete competitive series was imported or won.
- Shared stat definitions drive desktop tables, mobile cards and embeds. Sort
  buttons and help controls are separate. Focus or hover reveals help; Enter or
  Arrow Down focuses its Methodology link. Escape, outside click and leaving
  focus dismiss it. Popovers fit the viewport, including narrow iframe widths.
- Team colors come from stored hex colors. Existing `teamTheme` derives readable
  accents/foregrounds for Blue, White, black, gray, yellow and other colors.
  Labels communicate team/result identity independently of color.
- `index.json.generated_at` is UTC export metadata. The footer formats that
  supplied time in the viewer's timezone. It is not browser current time and
  does not represent replay date, deployment time or database modification time.

## Metadata and verification

The favicon and social image reuse the unmodified official Esports asset documented
in [BRANDING.md](BRANDING.md). Public route titles update in the browser. Static
GitHub Pages hash routes share one HTML response, so social crawlers receive the
program-level Open Graph preview rather than route-specific player/map previews.

Verification commands from the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
Push-Location web
npm.cmd test
npm.cmd run build
npm.cmd run build:admin
Pop-Location
.\.venv\Scripts\python.exe scripts/verify-public-redesign-ui.py
.\.venv\Scripts\python.exe scripts/verify-public-redesign-ui.py --url https://uah-r6.github.io/ --output data/research/public-redesign-20261008/live
```

The current browser suite uses actual exported data plus isolated future-team and
multi-team Career fixtures. It checks 1440/1100/768/390px public routes and embeds.
The separate substitute and uploader regressions retain their existing cases.
It performs no real submissions,
imports, reparses or database writes. Evidence remains in ignored research data.
