# Series that do not count — 2026-11-04

## Browser workflow

1. Launch **Start NECC Admin.cmd**, choose the team and season, and open **Matches**.
2. Check **Exclude this series from statistics (no count)** on any series card.
   It saves immediately; the status below the checkbox confirms the saved state.
3. Use **Publish → Publish Website** when ready to update GitHub Pages.
4. Uncheck to restore statistics. No re-import, replay parse or CLI is needed.

The Blue **Placements** series (`170b708e12f1`) is checked locally. Its three maps
and 38 rounds remain recorded; aggregate statistics exclude them. The current
21 recorded maps become **18 counted maps / 184 rounds**: Blue **12 / 125**,
White **6 / 59**. No other series was marked no count.

## Meaning and storage

`series.exclude_from_stats` is a checked SQLite integer, default zero, exposed
as a boolean in public JSON. An automatic serialized migration adds it to
existing databases without changing any map, identity or evidence. The setting
belongs to a series; existing and later maps inherit it through their series
join. New series default to counting, and moving a map uses its destination's
policy. Metadata editing, recalculation and publishing preserve the flag.

The localhost-only, token-protected endpoint is
`PATCH /api/admin/series/{id}/statistics` with
`{"exclude_from_stats": true}` or `false`. Other fields and coerced string/number
values are rejected. It changes only this policy and regenerates public data.
It does not publish automatically.

Excluded series contribute to none of these aggregate statistics:

- Player season and Career statistics, leaderboards, team splits and operators.
- Regular or substitute statistics and Rating aggregates.
- Rating trend points, even when standalone historical Ratings are valid.
- Team/program counted map records, rounds and wins.
- Aggregate map/site/side and opening engagement statistics.

They remain in match discovery, recent history and player map history with a
**Does not count toward statistics** label. Series/map pages retain their own
box scores, standalone Ratings, rounds and opening summaries under an explicit
exclusion notice. Evidence eligibility and counting policy are separate.
Program **Recorded maps/series** inventory continues to include history; team
records use counted maps only. Aggregate exports include `excluded_maps` to
explain why their counted `maps` total can be smaller than history length.

## Preservation and verification

Only the new series column and Placements' true value changed in SQLite. All
**26 other tables** match the backup exactly, all **21 maps' trusted v3 input
sets** are identical, and all **246 protected archive/statistics hashes** match.
Every individual map's existing public performance and Rating is unchanged;
its only new field is the inherited exclusion flag. No rating formula or replay
parser changes were made in this pass. The previous death-boundary repair's
uncommitted work was preserved separately.

Tests cover all aggregate scopes, substitutes, zero counted maps, exact restore,
metadata edits, recalculation, later imports, regrouping, repeated/concurrent
migration, API validation and stale publishing projections. Frontend tests
verify that excluded numeric Ratings cannot become trend points and that the
series stays discoverable. Existing history tests now compare counted data and
actual participants rather than assuming fixed roster sizes.

The actual CMD-launched admin checkbox was checked, unchecked and checked again,
then verified after reload at 1440px and 390px. Only three policy PATCH requests
were made; no import, reparse, deletion or publish. Twenty static public browser
checks at 1440/1100/768/390px verified series/map/history notices, profile trends,
retained game logs and overview counts, with no JavaScript errors or API writes.
All **71 public JSON documents** validate. **850 Python tests and six subtests**
passed (one optional replay test skipped), all **75 frontend tests** passed,
and both public/admin builds passed.

Private baseline, trial database, checks and screenshots are ignored under
`data/research/series-no-count-20261104/`. Source changes are committed locally
so the ordinary Publish Website action can push the feature with generated
data. No external publication was performed in this pass.
