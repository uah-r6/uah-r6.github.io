# Public presentation and Google Sites embeds

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
the selected heading. White's empty state shows no Blue statistics.

Historical map ownership remains authoritative because the existing team export
is used directly. **Career leaderboard is team-specific; global player Career
profiles remain cross-team.** Embeds retain their independent team route and
active-season behavior. No statistics are recalculated in the browser.

Read-only local/live scoping checks:

```powershell
.\.venv\Scripts\python.exe scripts/verify-player-stats-scope-ui.py
.\.venv\Scripts\python.exe scripts/verify-player-stats-scope-ui.py --url https://uah-r6.github.io/ --output data/research/player-stats-scoping-20261007/live
```

## Embed Player Stats

In Google Sites, choose **Insert → Embed → By URL** and paste one of:

- Blue: https://uah-r6.github.io/#/embed/blue/player-stats
- White: https://uah-r6.github.io/#/embed/white/player-stats

The same route works with any valid team slug. These utility URLs are public
and unlisted. They render only Player Stats, without navigation, period selector,
title or footer. Player and definition links open the full website in another tab.

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

- Player Rating trends use **exported `siege_style_v3` Series Ratings**, calculated
  once from combined trusted eligible map counts. Ineligible, missing or invalid
  values are omitted, never converted to zero. Context shows player-specific map
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
.\.venv\Scripts\python.exe scripts/verify-public-presentation-ui.py
.\.venv\Scripts\python.exe scripts/verify-public-presentation-ui.py --url https://uah-r6.github.io/ --output data/research/public-presentation-20261007/live
```

The browser suite uses actual exported data plus isolated synthetic future-team,
active-season and single/empty profile fixtures. It checks 1440/1150/768/390px
public routes and 1000/800/600/390px embeds. It performs no real submissions,
imports, reparses or database writes. Evidence remains in ignored research data.
