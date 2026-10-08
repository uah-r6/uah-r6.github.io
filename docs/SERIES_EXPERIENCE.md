# Series Rating, player trends and round highlights

## Public experience

Matches links to `/#/series/:seriesId`. Each series page shows its team, season,
opponent, date, recorded map W–L, map scores and shared Player Stats. A map's
existing `/#/matches/:mapId` route remains intact, with a return link when the
series contains multiple maps. **Recorded maps** does not assert an official
full-series result or completeness.

Series Player Stats include everyone historically bound to the played maps,
including Alumni and substitutions. The default order is descending Series
Rating, with unrated players retained below rated players. Desktop tables and
phone cards reuse the existing stat definitions, sorting and help components.
Visible secondary text shows each player's rated maps and rounds.

The normal player trend contains **complete exported Series Ratings from regular
roster appearances only**. Substitute-only series are excluded. Mixed-role series
use only regular-roster inputs in normal history; the Series table retains all
applicable appearances and its SUB badge. Each track requires complete coverage
of the player's own participation. See [substitute architecture](SUBSTITUTES.md).
Hover, keyboard focus, click or tap selects the exact two-decimal Rating and
opponent/date/recorded W–L/team/coverage context. Arrow keys select adjacent
points. Season profiles contain that season's series; career profiles include
all teams chronologically. Same-date ordering uses recorded export order rather
than invented start times. Incomplete series remain in history but never become
points or recent Rating controls. Zero or one complete series renders **no SVG
or line graph**: a compact message explains that two fully rated series are
required, with the latest complete Rating shown when one exists. Map Ratings and
recent-map links remain available.

## Calculation and coverage

`r6stats/series_export.py.series_rating_complete` is the authoritative export and
publishing rule: nonzero played maps/rounds, `rating_maps == maps` and
`rating_rounds == rounds`. Denominators are actual player participation, not
total series maps. A player who played two of three maps requires those two maps
and their rounds. Regular and substitute tracks use the same rule.

Only when complete, the projection combines trusted **counts** from existing
`rating_inputs_v3.load_inputs` results, then calls the existing aggregate engine
and frozen `siege_style_v3` model once. Cached or rounded map Ratings are not
inputs. Formula, coefficients, trade window and all eligibility gates are
unchanged. Incomplete series return `rating: null`; no partial aggregate is
calculated or exposed as a Series Rating.

Display statistics independently aggregate **all recorded maps that the player
played**, using current credited K/D, finisher HS denominator, KOST, entry,
objectives, clutch and manual K/D display policies. This preserves the existing
distinction between displayed performance and eligible Rating evidence.

`rating_maps / maps` and `rating_rounds / rounds` are player-specific. Maps where
a player did not play do not enter that player's denominators. Missing any
relevant map or round means `rating: null`, displayed as **—**, with coverage
retained. Complete Series Ratings evaluate the unchanged model once.

The frontend also refuses stale numeric series entries with incomplete coverage.
All chart points are complete and filled. Map Ratings are unchanged. Season and
Career Ratings independently aggregate trusted eligible map inputs in `export.py`;
they do not consume Series Ratings and retain existing coverage semantics.
Profile summary Partial Rating labels still apply to those broader aggregates.
Historical evidence gaps remain abstentions; no evidence repair is part of this
pass. See [Rating evidence](RATING_EVIDENCE.md).

### Mathematical relationship to map Ratings

The frozen model has the form

```text
R(C, n) = b + Σ_j w_j × ((C_j / n − μ_j) / σ_j)
```

Each `C_j` is additive across eligible maps, including signed opening/trade
differences, weighted clutch counts and plants + disables. For eligible map
round counts `n_i`, let `N = Σ_i n_i`. Then:

```text
R(Σ_i C_i, N)
  = b + Σ_j w_j × ((Σ_i C_ij / N − μ_j) / σ_j)
  = Σ_i (n_i / N) × R(C_i, n_i)
```

Thus the aggregate-input Rating equals a round-weighted mean of **full-precision**
eligible map Ratings, up to floating-point roundoff. An unweighted average, or
an average of rounded display values, generally differs. Aggregate trusted
inputs remain the implementation authority. Tests verify one/two/three maps,
unequal lengths, partial eligibility, poisoned cached Rating values and
substitution coverage. Lgon's UCF Rating is approximately **1.415675** from 11
and 9 eligible rounds, while the unweighted map average is **1.434718**.

## Public export and integrity

- `series/<series_id>.json`: safe public metadata, recorded result, logical map
  summaries, displayed player totals and player-specific Rating coverage.
- `players/<slug>/<season-or-career>.json.series_ratings`: compact exported
  series context and the same trusted Rating, consumed directly by the chart.
- `matches/<map_id>.json.rounds[].highlights`: compact safe display groups only.

Series grouping uses the existing series ID and **internal player ID bindings**,
not username strings or today's roster. Inconsistent team/season/opponent/week/
notes metadata or duplicate logical map IDs raises an error; no historical
records are rewritten. Rehost segments stay within one logical map and logical
round numbering is retained. Public validation checks series/map/profile
references, metadata, coverage and safe highlight limits before publishing.

No raw profiles, parser offsets, replay paths, archive metadata, evidence blobs,
fingerprints or submission/admin data are added to public JSON. Existing public
display-name and player-slug policies remain unchanged.

## Highlight trust and restraint

`r6stats/round_highlights.py` reads already-stored normalized data and sealed
evidence. It does not parse `.rec` files or change statistics. Historical player
bindings and the imported map's team are required; opponents are excluded.

| Label | Required evidence |
| --- | --- |
| ACE / 4K / 3K | Existing complete validated credited round counters, roster and logical-round parity; enemy-kill counts only |
| 1v1–1v5 | Existing validated `native_state` first-sole-survivor/actual-winner logic, exact native roster and finish parity |
| Plant / Disable | Existing corrected core occurrence/actor source, UID, side, offset, unique objective-credit parity; Disable also corroborated by defense win |

Core objective evidence must match the stored replay fingerprint and normalized
digest. Integrity failures fail export; a stale seal cannot supply new actors.
Validation is isolated per round and objective kind, so an unsupported objective
does not suppress another independently supported kind or a credited multikill.
Absent/uncertain native evidence produces no clutch label. Incomplete credited
evidence produces no multikill label; legacy finisher counts are never used as a
substitute. Manual K/D corrections also suspend count/native highlights. Verified
objective labels may remain independently eligible.

Priority is **ACE > 4K > 1v2–1v5 > 3K > 1v1 > Disable > Plant**. At most two
player groups and two labels per player are exported. Same-player moments combine
into one group, such as `Lgon · 3K · Plant`. Losing-round multikills are valid.
Opening kills, routine 2Ks, trades/refrags, operators, event times and kill logs
are omitted to preserve a short round summary. The frontend renders the curated
metadata; it does not infer events or calculate highlights.

### Existing-map audit

| Series | Map | Highlighted / recorded rounds |
| --- | --- | ---: |
| Placements | Fortress | 5 / 10 |
| Placements | Border | 5 / 14 |
| Placements | Kafe Dostoyevsky | 6 / 14 |
| Michigan | Border | 6 / 12 |
| Michigan | Chalet | 1 / 12 |
| UCF | Border | 4 / 11 |
| UCF | Nighthaven Labs | 4 / 9 |

**31 of 82 rounds** have a highlight; **51 are unlabelled**. Chalet's incomplete
credited evidence abstains from multikill/clutch labels; its independently
verified plant remains. Older objective gaps do not become eligible Rating maps
merely because individual highlight evidence is valid.

Blue Series coverage for all five players is Placements **1/3 maps,
10/38 rounds**, Michigan **1/2 maps, 12/24 rounds**, and UCF **2/2 maps, 20/20
rounds**. Only UCF retains a numeric Series Rating; Placements and Michigan are
unavailable. White FSU keeps complete player-specific coverage and numeric Series
Ratings, including its substitute. Each current normal profile has just one
complete series, so no line graph appears. All six eligible maps / 63 rounds and
nine recorded maps / 103 rounds are preserved.

## UX reference and verification

The [SiegeGG results overview](https://siege.gg/matches?tab=results) and
[Twisted Minds–Virtus.pro match page](https://siege.gg/matches/8095-eul-eu-twisted-minds-vs-virtuspro)
were inspected for hierarchy: matchup overview, map results, then optional round
context. Only that structural idea informed this implementation. The existing
UAH components, theme and styles were extended; no source, CSS, graphics or logos
were copied. No Rating research or new replay downloads were performed.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
Push-Location web
npm.cmd test
npm.cmd run build
npm.cmd run build:admin
Pop-Location
.\.venv\Scripts\python.exe scripts/verify-complete-series-ui.py
.\.venv\Scripts\python.exe scripts/verify-series-completeness-preservation.py
.\.venv\Scripts\python.exe scripts/verify-public-redesign-ui.py
.\.venv\Scripts\python.exe scripts/verify-substitutes-ui.py
```

Each browser script also accepts `--url https://uah-r6.github.io/` for read-only
production checks. Evidence and preservation reports are ignored under
`data/research/series-completeness-20261008/`. The suites exercise
1440/1100/768/390px widths, actual complete/unavailable Series Ratings, coverage,
mouse/focus/keyboard context, zero/one/two-complete graph states, stale numeric
partial fixtures, multiple teams, long names, substitutions and compact embeds.
No imports, reparses, database writes or real cloud submissions are required.
