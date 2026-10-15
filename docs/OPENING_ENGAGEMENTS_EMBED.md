# Team opening engagements and Google Sites embed

Date: 2026-10-15. Baseline: `7ea1bbe` (11 maps). Scope: UAH NECC statistics
website only. No Siege Atlas / `r6-spatial-lab` changes.

## Authoritative data and calculation

The original display Entry policy is `r6stats.stats.calculate.calculate_match`:
normalized kill events ordered by descending remaining time, then sequence;
invalid player identities and already eliminated victims are skipped. Environmental
deaths, suicides and teamkills affect the alive set but cannot be the opener.
The first valid opposing player kill credits one opening killer and one victim.
This pass delegates to that implementation for **each round**, rather than
implementing another detector or inferring openings from season player totals.

`r6stats/opening_engagements.py::round_facts` calls that unchanged pure function
with a one-round Match, then associates the credited killer/victim with their
stored round player team IDs. The side is the selected team's normalized player
side; the result uses the stored `Round.winner` against `maps.our_team`.
Objective wins use that same winner, regardless of survival. A normalized Match
already contains selected logical rehost rounds and remapped segment team IDs.
Excluded physical rounds are never revisited or counted again.

Map identity, team ownership and series come from the stored maps row; its
series joins the historical season. Current roster membership does not select
rounds or determine a historical team. All actual participants, including subs,
contribute to team results. Unknown sides stay in overall totals and are counted
separately without guessing Attack or Defense.

This is the **public Entry** policy. Frozen v3 Rating independently uses its
verified native event order. Neither that policy nor any Rating equation/input
was changed. Display Entry, kills/deaths, KOST, objectives and 1vX are unchanged.

For each scope and side, five raw counters are summed:

| Counter | Meaning |
| --- | --- |
| `eligible_rounds` | Round has a valid player opening kill |
| `opening_kills` | Our team gets that opening kill |
| `opening_kill_wins` | Our team wins after getting that opener |
| `opening_deaths` | Our team suffers that opening death |
| `opening_death_wins` | Our team wins after suffering that opener |

The three fractions are:

| Label | Numerator / denominator |
| --- | --- |
| Opening Kill % | `opening_kills / eligible_rounds` |
| Opening Kill Conversion % | `opening_kill_wins / opening_kills` |
| Opening Death Recovery % | `opening_death_wins / opening_deaths` |

Every eligible round contributes to exactly one opening-kill/death bucket for
the selected team. No valid opening means exclusion from all three samples,
not an automatic opening death. Zero denominators export `null` and show **—**
with **0 / 0**; a genuine zero-success sample shows **0.0%**.

Combined fractions divide combined raw counts, including unknown-side rounds.
They do not average side or map percentages. For example, Attack **1 / 2 (50%)**
plus Defense **8 / 10 (80%)** gives **9 / 12 = 75.0%**, not **65.0%**.
Equal-denominator regression: Attack 4/10 plus Defense 8/10 gives 12/20 = 60%.

## Export and placement

No database migration, update, import, replay parsing or historical recalculation
is needed. Export opens production SQLite read-only for this pass. Each match
round adds only `opening: "kill" | "death" | null`, relative to its owner team.
No identity or event log is exposed. Each required document adds
`opening_engagements` with `overall`, `attack`, `defense` and `unknown_side`
counter/fraction records. Values are numeric fractions (0–1), with one-decimal
percentage formatting in the UI. Compact map metadata in player profiles and
global leaderboards does not duplicate these new team summaries.

| User view | Placement and scope |
| --- | --- |
| Team Overview, selected season or Career | Three cards below the season summary and above Player Stats; all that team's selected-period maps |
| Series | Three cards below the series hero and above its recorded map cards; that series' logical rounds |
| Individual map | Three cards in Map performance before Player Stats; that single map's logical rounds |
| Team → Maps → Border (or another map) | Three cards below the aggregate map heading/context, before side/site detail; every appearance in the selected team/period |

Each card shows a large **combined** percentage with its numerator/denominator
beside it. **ATK and DEF percentages and raw samples are always visible directly
underneath**, with no expansion required. An unknown-side note appears if needed.
All three use their full labels and keyboard/mouse-accessible definition popovers,
linked to Methodology → Advanced Stats. Empty team/map scopes still expose
zero-sample cards. Team, season, Career, series and canonical map filtering use
the existing architecture, including historical maps outside the current pool.

Publishing validation recomputes match/series/team summaries from the public
logical-round facts and map aggregates from the same existing map projection.
Inconsistent counts, stale percentages and malformed opening round facts fail
validation. Duplicate logical maps count once; conflicting copies/duplicate
logical rounds are rejected.

## Real production QA

These results are fixtures for the report only, never implementation constants:

| Scope | Opening Kill % | Conversion % | Recovery % |
| --- | --- | --- | --- |
| Blue Fall 2026, nine maps / 103 rounds | 64/103 = **62.1%** | 48/64 = **75.0%** | 15/39 = **38.5%** |
| White Fall 2026, two maps / 21 rounds | 10/21 = **47.6%** | 5/10 = **50.0%** | 1/11 = **9.1%** |
| Blue vs West Point, two maps / 21 rounds | 14/21 = **66.7%** | 11/14 = **78.6%** | 3/7 = **42.9%** |
| West Point Fortress, 11 rounds | 6/11 = **54.5%** | 5/6 = **83.3%** | 2/5 = **40.0%** |
| Blue Border aggregate, four maps / 47 rounds | 25/47 = **53.2%** | 19/25 = **76.0%** | 8/22 = **36.4%** |

Blue Attack: opening **29/51 = 56.9%**, conversion **20/29 = 69.0%**,
recovery **9/22 = 40.9%**. Defense: opening **35/52 = 67.3%**,
conversion **28/35 = 80.0%**, recovery **6/17 = 35.3%**.
White's same generic code includes its substitute's team openings without
changing that substitute's separate player statistics.

All 11 maps reconcile their new opening-kill/death counts exactly with the
existing per-player display Entry calculation for the owner team. Eight sample
rounds (four West Point Fortress and four White Nighthaven) were inspected against
normalized killer/victim identity, chronology, team IDs, side and round winner.
For example, West Point Fortress R1 is an opening death and team win (Recovery),
R2 an opening kill and team loss, R3 an opening kill and team win (Conversion),
R4 an opening death and loss. No survival-based result inference occurs.

Private audit details, source samples, backup, table snapshots and screenshots
are ignored under `data/research/opening-embed-20261015/`.

## Google Sites presentation

Embed URL: <https://uah-r6.github.io/#/embed/blue/player-stats>.
Equivalent White route uses `white`. Existing active-season selection and valid
explicit `?season=fall-2026` overrides remain; invalid periods remain invalid.

The screenshot's relevant **content area** is pale gray with dark regular type;
its dark top navigation/banner belongs to Google Sites, not the table embed.
The isolated `web/src/embed.css` matches that content area with:

- Explicit **#f3f3f3** document/table background, **#202020** main text. A matched
  background avoids dependence on the parent iframe's transparency settings.
- Regular **Arial/Helvetica/system sans-serif** as the practical web-safe
  approximation; 14px table text, compact 12px headers, smaller text at 850px.
- No outer card, blue stripe, rounded frame, Rating cell fill, team/logo banner,
  global navigation, footer, large title or standalone application shell.
- Fine 1px gray row/header dividers, ordinary heading weight, 8px horizontal
  cell spacing and **12px outer gutters**. Full available content width.
- No viewport minimum height or filler. Content is roughly 300px high for five
  Blue rows (White is shorter). Size the Google Sites embed to its content,
  allowing about 300–330px for Blue including the narrow-width scrollbar.
- All nine existing stat columns, actual values, rows, sorting, semantic table
  headers, focusable scrolling region, keyboard controls and new-tab player links
  remain. Narrow views retain columns through contained horizontal scrolling.
- Dark positive/negative colors and light tooltip surfaces keep contrast readable.
  The standalone site retains its dark theme, original typography, chrome and
  responsive mobile player cards.

The result visually blends with the screenshot's content section. The exact
Google Sites font rendering, parent content width/padding, iframe outer height
and a later change in parent background cannot be controlled inside a cross-origin
iframe. There is no parent DOM access, sizing hack or parent CSS dependency.

## Verification and preservation

New deterministic tests cover weighted/equal samples, Attack/Defense, wins/losses,
objective winners, no valid kill, environmental deaths/teamkills/suicides,
invalid identities and dead victims under existing Entry rules, zero samples,
unknown sides, logical deduplication, confirmed rehost exclusions/swapped indices,
series/map/repeated-map/team/season/Career scopes, roster-history isolation and
publishing rejection of corrupted summaries. Frontend tests cover the three
definitions, one-decimal display, raw fractions and zero denominators.

Existing frontend assertions tied to the previous nine-map checkpoint now scope
their historical golden cases explicitly; current-data checks follow recorded
map participation instead of stale total-round literals. No formula or old golden
Rating value was changed to make tests pass.

Browser QA checks both embeds at **1200, 1000, 800, 600 and 390px**, including all
columns, exact rows/Ratings, sorting, keyboard tooltips, new-tab links, computed
colors/fonts, absence of chrome/frame, compact height and no page clipping.
No internal table scrolling is needed at 800px or wider; 600/390px intentionally
scroll within the table. Opening cards are checked at **1440/1100/768/390px** for
all four scopes and White, with exact combined/side samples, Career/team switching
and a browser-only zero-sample fixture. Screenshots are local and ignored.

All 27 production tables remain exactly equal to the pre-change backup. All 56
public documents retain every existing field/value (apart from export time);
only the new opening projections are added. All 11 archives and manifests retain
their exact SHA-256 hashes and verify Healthy, and all 11 maps retain v3 eligibility.
Protected parser, Rating, original stats engine, credited/objective corrections,
manual K/D and series aggregation sources are byte-identical. Replay data,
snapshots, roster/season history, rehost mappings and publication behavior remain.

Reproducible checks from the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
npm.cmd --prefix web test
npm.cmd --prefix web run build
npm.cmd --prefix web run build:admin
.\.venv\Scripts\python.exe scripts/verify-opening-engagements.py
.\.venv\Scripts\python.exe scripts/verify-opening-embed-ui.py
.\.venv\Scripts\python.exe scripts/verify-public-redesign-ui.py --admin= --output data/research/opening-embed-20261015/regression
```

Worker tests and Go tests/vet also pass; their sources are unchanged. No private
backup, replay, credentials, machine-specific paths or screenshot is committed.

Final local results: **819 Python tests plus six subtests passed**, one optional
real-replay smoke test skipped; **72 frontend tests**, **19 Worker tests**, Go
`test ./...` and `vet ./...`, both public/admin builds, the focused opening/embed
browser suite and the **36-route public regression at four widths** passed.
No JavaScript errors or API mutations were observed. The optional integration
test skip and existing Starlette test-client deprecation warning are unrelated
to this change.

## Release and live verification

Release **`3478160`** is pushed and deployed successfully:
[Pages run 38690029730](https://github.com/uah-r6/uah-r6.github.io/actions/runs/38690029730).
All **56 live JSON documents match local exports exactly**. The focused opening
and embed browser suite passed against the deployed site at every listed width,
and the **36-route regression passed live at four widths**. No JavaScript errors,
page overflow or API mutations were observed. Local HEAD, origin/main and remote
main agreed after push; the tree was clean before this final documentation-only
checkpoint. This completes the requested pass.
