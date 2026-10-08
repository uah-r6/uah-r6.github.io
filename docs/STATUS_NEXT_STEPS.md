## Current: match discovery and map analytics - 2026-10-08

**COMPLETE, PUSHED AND LIVE VERIFIED. STOP AFTER THIS PASS.**
Release `0982b0c` deployed successfully in
[Pages run 37858456292](https://github.com/uah-r6/uah-r6.github.io/actions/runs/37858456292).
This final documentation checkpoint records the verified release.
Baseline `dd4a584`. Focused public Matches filters and team Maps views; no Rating,
parser, evidence, archive, roster, uploader or Worker changes.
See [MAP_ANALYTICS.md](MAP_ANALYTICS.md) for architecture, URLs and exact counts.

- Global Matches defaults to All UAH Teams with dynamic team choices, partial
  opponent search/suggestions, newest/oldest/team/opponent sort, URL state and
  filter-aware clear/empty states. Whole series remain intact. Team Matches is
  owner-scoped without a redundant team filter.
- Team Maps and map detail routes use one new team/period JSON. The centralized
  catalog covers 26 tracker-supported replay identities including legacy maps;
  it makes no current competitive-pool claim. Unplayed maps show no recorded data.
  Map/round W/L, Attack/Defense rates, side-specific sites and recent maps derive
  from existing logical round projections. Best sites require two known rounds.
- Independently verified UCF Nighthaven is 7-2 / nine rounds: Attack 3-0,
  Defense 4-2. Blue Border/Kafe/Chalet and White Border/Nighthaven were verified
  independently too. Career is team-specific and substitutes do not change results.
- All 49 previous public documents match exactly except generated_at. Four new
  analytics documents pass publishing validation. Every row in all 23 SQLite
  tables is unchanged. All nine maps remain v3-eligible and archives Healthy;
  all protected source/binary/brand/archive hashes match the private baseline.
- Local browser checks pass at 1440/1100/768/390px: filters, back/forward, refresh,
  period, scope, catalog, played/unplayed details, site samples and links. Existing
  33-route public/admin and nine-profile/four-series regressions also pass.
  No mutation, import, reparse or submission was performed.
- Actual quoted `Start NECC Admin.cmd` restarted the repository-source server,
  confirmed .venv Python and parser/server paths, and opened Chrome. Admin remains
  responsive for both teams without API writes.

Private verification baseline/reports/screenshots:
`data/research/match-map-analytics-20261008/` (ignored).
Verification: **799 Python tests + six subtests** (one optional replay smoke skipped),
**69 frontend tests**, **19 Worker tests**, Go tests/vet and both builds passed.
- All **53 live JSON documents match local exports exactly**. Live browser checks
  pass at all four widths for global/team Matches, filters/history/share/clear,
  Blue/White Maps, played/unplayed details, rates/sites/sample sizes and match links.
  The 33-route public/admin regression also passes against the deployed site with
  no page overflow, JavaScript errors or API mutations.
  Links: [Matches](https://uah-r6.github.io/#/matches),
  [Blue Maps](https://uah-r6.github.io/#/teams/blue/maps),
  [White Maps](https://uah-r6.github.io/#/teams/white/maps),
  [UCF Nighthaven](https://uah-r6.github.io/#/teams/blue/maps/nighthaven-labs?season=fall-2026).
**STOP after this pass; do not begin spatial analytics or other features.**

---

## Current: deep Rating evidence recovery — 2026-10-08

**COMPLETE, PUSHED AND LIVE VERIFIED. STOP AFTER THIS PASS.**
Release `a14e57b` deployed successfully in
[Pages run 37855146633](https://github.com/uah-r6/uah-r6.github.io/actions/runs/37855146633).
This final documentation checkpoint records the verified recovery.
Baseline `e179add`. All **nine maps / 103 rounds** now pass the whole-map frozen
v3 input path. Kafe, Placements Border and Michigan Chalet are recovered through
generic structurally validated replay proofs, never guessed actors or counters.
See [DEEP_RATING_RECOVERY.md](DEEP_RATING_RECOVERY.md) for exact Ratings, feature
versus provenance classification, offsets, sources and all preservation results.

- Kafe R9 uses `terminal_active_numeric_bonus_timer_owner_v1`: exact same-body
  numerical proof throughout the uniquely owned completing timer, with known
  active terminal state; corrects the invalid Tallman Defense plant to Kenbot.
- Placements Border R6 uses `repeated_plant_zero_before_transition_v1`: both
  zero samples are the same plant timer before planting, independently consistent
  with Attack's score increment; removes the false Lxgacy disable.
- Chalet R9–12 uses `explicit_ten_slot_empty_participant_v1`: nine actual stable
  profiles plus one explicitly empty initial slot. Every actual participant has
  direct `stable_uid_scoreboard_delta_v1` counters. No missing player/count is
  invented. Rating-only sealed evidence preserves the original historical display
  sidecar and counts. The same full inventory recovers Ophanbear's R10 plant.
- All five Blue profiles now have complete Placements **3/3, 38/38**, Michigan
  **2/2, 24/24** and UCF **2/2, 20/20** Series Ratings and three trend points.
  White keeps its exact complete Series Ratings and compact one-series summaries.
  Series still aggregates trusted feature counts once; incomplete fixtures remain
  null. Normal/Sub projections remain isolated. Season/Career Ratings update
  independently from newly eligible maps; no formula or feature semantics changed.
- Actual quoted **Start NECC Admin.cmd** rebuilt repository binaries, restarted
  the outdated process and opened Chrome. The live local admin API audited nine,
  preserved six and repaired three, with zero blockers. Imported repository paths
  and `.venv` Python were verified, and binary hashes equal trial candidates.
- Strict production/trial comparison passes. Original six per-round features and
  Ratings are exact; all original display/objective sidecars, v2 snapshots,
  identities, roles, round IDs, rehost mappings, metadata and unrelated tables
  remain unchanged. Seven new audited entries and one sealed Rating-only table.
  All archives/manifests retain exact hashes and all nine remain Healthy.
- Three normalized objective changes are explicit. Calculated count deltas are
  opponent-only: Kenbot plants 0→1; Lxgacy disables 1→0 and KOST rounds 12→11;
  Ophanbear plants 0→1. All public player raw statistics and highlights remain
  exact; 20 of 49 public documents change only Rating/coverage/availability,
  resulting Rating sorting and freshness. Six map and UCF/White Series JSON
  documents remain exact. Every series participant and normal Season/Career
  Rating was independently checked against trusted aggregate inputs.
- **781 Python tests + six subtests**, one optional smoke skipped; **59 frontend
  tests**, **19 Worker tests**, Go tests/vet and both builds pass. Existing
  TestClient deprecation and pytest-cache permission warnings are nonfatal.
  New proof rejection, integrity, cache and transactional tests are included.
- Read-only admin, broad 33-route, focused nine-profile/four-series and substitute
  browser gates pass at **1440/1100/768/390px**, with no JS errors or unintended
  mutations. Screenshots inspected at every width. Public/admin frontend source
  and bundles, formula, branding, uploader and Worker remain unchanged.
- Live verification passes: all **49 deployed JSON documents exactly match**
  local validated values. All nine profiles, all four series and all nine maps
  pass browser checks at the four widths; the 33-route presentation regression
  and zero/one/two-complete/stale-partial fixtures pass live. Lgon has three
  genuine complete points; White retains its one-series summary. Live screenshots
  were inspected at every width. No JS errors or unintended mutations occurred.

Verification: `scripts/verify-deep-rating-recovery.py verify`,
`scripts/verify-complete-series-ui.py`, `scripts/verify-public-redesign-ui.py`,
`scripts/verify-substitutes-ui.py`, and read-only
`scripts/verify-rating-production-admin-ui.py`.
Ignored backup/evidence/reports: `data/research/deep-rating-recovery-20261008/`.
The older baseline-specific preservation scripts describe previous checkpoints;
use the deep-recovery verifier for the current production state.

**STOP. This focused recovery is complete and live.**
No map-history fallback, further fitting or unrelated feature is planned.

## Earlier: complete Series Ratings and trends — 2026-10-08

**COMPLETE, PUSHED AND LIVE VERIFIED. STOP AFTER THIS PASS.**
Baseline `339cbd0`; release `f10eda6` is pushed and deployed by successful
[Pages run 37844094626](https://github.com/uah-r6/uah-r6.github.io/actions/runs/37844094626).
This documentation checkpoint records the verified correction.
This changes Series Rating availability only; the frozen v3
formula, map eligibility/evidence and independent Season/Career Rating stay intact.

- Shared `series_rating_complete` requires nonzero player-specific played maps
  and rounds with exact trusted map and round coverage. The series projection
  evaluates the existing model once only when complete; otherwise Rating is
  `null`. Coverage counts and all display statistics remain. Publishing uses the
  same rule, including mixed-role regular projections, and refuses numeric
  incomplete, missing complete or nonfinite Ratings.
- Normal profile history still uses only frozen regular-roster appearances.
  Substitute/mixed participant tracks use the same coverage rule independently;
  no substitute inputs leak into normal Season/Career/history. Map Ratings and
  Season/Career Ratings independently consume trusted map inputs in `export.py`,
  without any dependency on Series Ratings; no broader semantics were changed.
- Lgon: UCF **1.4156752657694631**, **2/2 maps, 20/20 rounds**; Michigan
  **unavailable**, **1/2 maps, 12/24 rounds**; Placements **unavailable**,
  **1/3 maps, 10/38 rounds**. All five Blue players have the same completeness
  pattern. White FSU retains complete numeric Series Ratings, including its
  substitute. Every current normal profile has only one complete series.
- Trend accepts only complete finite v3 Series Ratings. Partial helper, hollow
  points and PARTIAL chart labels are removed. Zero/one complete series has no
  SVG or line; compact readable messages and a latest complete fact appear.
  Two or more retains keyboard/focus/hover/click context and complete-only recent
  controls. Incomplete series/history and every recorded performance remain.
- **729 Python tests plus six subtests**, one optional smoke skip; **59 frontend
  tests**, **19 Worker tests**, Go tests/vet and both builds pass. Existing
  TestClient deprecation/pytest-cache permission warnings remain nonfatal.
  Tests prove player-specific participation, aggregate-once/non-arithmetic-mean,
  incomplete map/round abstention, display preservation and appearance isolation.
- Actual quoted **Start NECC Admin.cmd** restarted the outdated project process
  and launched Chrome with `.venv\Scripts\python.exe` / current repository
  source. Broad 33-route/four-width regression and read-only admin checks pass.
  Focused checks cover all nine normal profiles and four Series pages, exact
  complete/unavailable Ratings and coverage, raw stats, SUB badge and help.
  Zero/one/two-complete, stale partial numbers, long names and multi-team fixtures
  pass at **1440/1100/768/390px**. Existing substitute regression also passes.
- Regenerated 49 public documents through a **read-only SQLite connection**.
  Preservation permits exactly **30 incomplete Series Rating fields becoming
  null**, resulting series sorting and export freshness. All other public values
  are exact, including complete Ratings, coverage, map/Season/Career Ratings and
  raw stats. All nine map JSON files remain byte-identical. All **22 SQLite
  tables**, **226 protected parser/formula/evidence/archive/branding/uploader/
  admin/presentation files** and **nine Healthy archives** are unchanged.

Current gates: `scripts/verify-complete-series-ui.py` (build or `--url`),
`scripts/verify-series-completeness-preservation.py`, the updated broad public
redesign gate and substitute browser gate. See [SERIES_EXPERIENCE.md](SERIES_EXPERIENCE.md),
[RATING_EVIDENCE.md](RATING_EVIDENCE.md) and [PUBLIC_METHODOLOGY.md](PUBLIC_METHODOLOGY.md).
Older evidence-audit partial aggregate tables are explicitly historical diagnostics.
Ignored baseline/evidence is `data/research/series-completeness-20261008/`:
SQLite backup/rows, 49 original documents, hashes, archive baseline, screenshots
and reports. No import, reparse, evidence repair, cloud mutation or research.

Live verification PASS: all nine actual normal profiles and four Series pages at
all four widths. Lgon shows one complete UCF Rating with no SVG/line; White shows
one complete FSU Rating with no SVG/line. UCF/FSU numbers remain exact; Michigan/
Placements show unavailable Ratings, exact coverage and all player performance.
Zero/one/two-complete, stale partial, multiple-team and long-opponent fixtures,
hover/focus/click/touch/keyboard context and methodology also pass live. No JS
errors or API/cloud mutations. Actual live screenshots were visually inspected.

All **49 deployed public JSON files** match the corrected export byte for byte
after Git CRLF/LF normalization; all **five branding PNGs** are byte-identical.
Final local preservation again passes all 22 tables, 226 protected files, raw and
map/Season/Career statistics, complete Series Ratings/coverage and nine Healthy
archives. Reports, live screenshots and exact Pages release metadata are in the
ignored evidence directory above.

**STOP.** The complete-Series Rating correction is finished. Do not begin Rating
research, evidence repair, parsing or unrelated features without a new task.

## Previous: public presentation redesign — 2026-10-08

**COMPLETE, PUSHED AND LIVE VERIFIED. STOP AFTER THIS PASS.**
Baseline `b98b46d`; release `da093d1` is pushed to main and deployed by successful
[Pages run 37840479530](https://github.com/uah-r6/uah-r6.github.io/actions/runs/37840479530).
This documentation checkpoint records the verified presentation release.
Public composition only; no statistics/export/backend changes.

- Compact program hero, Player Stats/Submit actions, selected-period summary,
  substantial Blue/White identity cards and latest recorded series. Existing
  exports yield 2 active teams, 9 maps and 4 series for Fall 2026. No new public
  fields or fake Grey/Black teams. Current records remain Blue 6-1 over 7 maps /
  82 rounds and White 0-2 over 2 maps / 21 rounds.
- Shared prominent team hero, native logo/context switcher, persistent active
  tabs and cleaner overview/roster/stats hierarchy. Series history and matchup
  pages emphasize owner, opponent typography and Recorded maps; map summaries
  show exact individual scores and explicit eligibility. Individual map heroes
  lead with map, round score, opponent, result and formatted date/period.
- Player hero shows the existing Rating, K-D/difference, KOST and Entry. Scoped
  regular team contributions choose the mark; multi-team Career uses program
  identity plus team chips. No current-membership inference or sub mixing.
  The existing trend, Series Ratings/partial coverage, sorting, stat help, SUB
  badges, detailed performance, sides, operators and highlights are retained.
- `PublicIdentity`, `PublicHub`, `PublicMatches`, `ProfileHero` and `publicView`
  share presentation components/derivations. Organized public composition CSS
  replaces obsolete small team/series header rules. Original team/program PNGs
  and centralized logo lookup/fallback are unchanged. Compact embed identity/
  tables remain the same size. Uploader/admin components are unchanged.
- **57 frontend tests**, **718 Python tests + six subtests** (one optional smoke
  skip), **19 Worker tests**, Go tests/vet and both builds pass. Python reported
  the existing TestClient deprecation and local pytest-cache permission warning.
  These did not fail tests; no dependency or filesystem repair was attempted.
- Edge regression covers **33 actual routes at 1440/1100/768/390px**: program,
  both team sections, Player Stats, both profiles, a real Sub Stats profile, all
  four full/partial-rated series, all nine maps, global Matches, Methodology,
  Submit Replays and both embeds. Exact scores/Ratings/coverage and active nav
  are checked, with screenshots visually inspected. Future empty Grey/Black/
  unknown and multi-team Career use intercepted fixtures only. Keyboard help/
  trend, native scope switching and reduced motion pass; no JS errors or API
  mutations. Existing logo, substitute and structured-uploader regressions pass.
- Actual quoted **Start NECC Admin.cmd** requests Chrome and serves repository
  source through `.venv\Scripts\python.exe`. Read-only Blue/White admin checks
  pass at all four widths. No administrative redesign or real uploads/imports.
- Preservation PASS: all **22 SQLite tables**, **49 byte-identical public JSON
  files**, **219 protected backend/parser/archive/logo/submission/trusted frontend
  files**, integrity/FKs and **nine Healthy archives**. No import, reparse,
  recalculation, Rating/model/evidence, role/membership, export or cloud mutation.

Read [PUBLIC_PRESENTATION.md](PUBLIC_PRESENTATION.md) and [BRANDING.md](BRANDING.md).
Current regressions: `scripts/verify-public-redesign-ui.py` (build or `--url`),
`scripts/verify-public-redesign-preservation.py`, and the existing substitute,
logical-submission and logo browser checks. Ignored baseline/evidence lives in
`data/research/public-redesign-20261008/`: SQLite backup, all table rows, original
public JSON, protected hashes, before/after screenshots/galleries and reports.
Uploader regression uploads and admin handoffs use isolated browser fixtures;
this pass does not perform a human production Turnstile submission.

Live verification PASS: all 33 actual routes at all four widths, future empty/
multi-team fixtures, exact Ratings/coverage and scores, compact embeds, keyboard
interaction and read-only local admin. Actual deployed screenshots were inspected
for the homepage, Blue/White, series/maps, profiles, embeds and Submit. The live
uploader's unmocked configuration returns HTTP 200 with Blue/White and Fall 2026;
the replay controls and Turnstile script/widget render without a configuration
error. Structured upload/retry/cancel/rehost/admin-handoff regression passes using
isolated fixtures. No human verification or real replay upload is claimed.

All **49 live public JSON files** match the pre-redesign baseline byte for byte
after Git CRLF/LF normalization; all **five live brand PNGs** match byte for byte.
Final local preservation again passes 22 tables, 219 protected files, 49 JSON
files and nine Healthy archives. Live browser, uploader, Pages and preservation
reports/screenshots are in the ignored evidence directory above.

**STOP.** This presentation pass is complete. Do not begin research, statistics,
roster changes, replay parsing or unrelated features without a new task.

## Previous: team logo branding — 2026-10-08

**COMPLETE, PUSHED AND LIVE VERIFIED. STOP AFTER THIS PASS.**
Baseline `1b0d6cb`; release `aa286e6` is pushed to main and deployed by successful
[Pages run 37836254044](https://github.com/uah-r6/uah-r6.github.io/actions/runs/37836254044).
This documentation checkpoint records the verified branding release.

- Four authoritative user PNGs are installed byte for byte under
  `web/public/brand/teams/{blue,white,grey,black}.png`. Valid 1080 x 1080 RGBA,
  64-95 KiB; browser decoding confirms transparent pixels and intact proportions.
  Artwork, canvas and the original program asset remain unchanged.
- Central `teamLogos.ts` registry and shared `TeamLogo.tsx` provide team asset,
  program fallback, then plain UAH if both images fail. Known team slugs resolve
  independently of page code. Grey/Black use frontend fixtures only; production
  still has exactly Blue and White. No public types or exported metadata changed.
- Team overview/roster/stats header, main Player Stats, owning series/map, program
  cards, compact embeds and local admin context/editors use logos. One per context,
  no player-row repetition. Native selectors, program navigation mark and global
  profiles retain their current behavior. Mobile series spacing accommodates the
  logo without splitting the opponent name beside the score.
- **51 frontend tests**, both public/admin builds, and Edge browser checks pass.
  All **21 actual team/roster/stats/series/map routes** were checked at
  **1440/1100/768/390px**, plus both embeds, preserved team/Career/sort selection,
  future-team fixtures, missing images, contrast on dark/team/light panels and
  read-only admin previews. No JavaScript errors or admin mutation requests.
- Actual quoted **Start NECC Admin.cmd** requests Chrome and serves the new admin
  build from this repository. Python:
  `C:\Users\logan\Documents\R6\r6-necc-stats\.venv\Scripts\python.exe`.
  Runtime imports resolve to this repository's `r6stats` sources. Shared logo URLs
  explicitly use `/brand/` in admin, rather than its Vite `/admin/` base.
- Preservation PASS: **22 SQLite tables**, **49 public JSON files**, **210 protected
  archive/backend/parser/rating/submission/cloud files**, original program logo,
  **nine Healthy archives**, integrity and foreign keys. No imports, reparse,
  recalculation, export, team creation, membership edits or cloud mutations.
  Python/export/types, Worker and Go are unchanged, so their suites were not rerun
  for this frontend pass.
- **Live Pages browser regression PASS**: the same 21 actual public routes and
  both embeds at all four widths show the correct Blue/White owning logos and
  no JS errors. Native selection preserves Career/sorting. Grey/Black/unknown
  future teams and missing assets pass intercepted browser fixtures only; no
  production team records were added. The actual launcher admin passes again.
  Four live PNG SHA-256 hashes match the exact source assets; the general program
  PNG is byte-identical. All **49 live public JSON files** match the baseline after
  Git's CRLF/LF normalization; local JSON bytes remain exact. No cloud deployment
  or mutations were made. Local and live screenshots/reports remain ignored.

Read [BRANDING.md](BRANDING.md) for the asset convention and fallback. Regressions:
`scripts/verify-team-logos-ui.py` (build or `--url https://uah-r6.github.io/`) and
`scripts/verify-team-branding-preservation.py`. Ignored baseline and evidence:
`data/research/team-logos-20261008/` (SQLite backup, full table rows, exact public
JSON, protected hashes, PNG metadata, screenshots and verification reports).

Release and verification are complete. **STOP**. Do not resume earlier research
or other production features without a new request.

## Previous: logical map replay submissions — 2026-10-08

**COMPLETE, PUSHED AND LIVE VERIFIED. STOP AFTER THIS PASS.** Baseline `d687542`.
Release `e493f90` is on main; [Pages run 37828061045](https://github.com/uah-r6/uah-r6.github.io/actions/runs/37828061045)
completed successfully. The additive production D1 migration and Worker deployment
succeeded. This documentation checkpoint records the final verification and makes
no application or statistics changes.

- Submit Replays asks for 1–5 maps above folder discovery. Each map independently
  uses Normal (one folder), Rehosted (two or more ordered parts), or Not sure
  (explicit administrator review). The shared candidate pool is chronological,
  compact and keyboard scrollable; cards show private browser file-time ranges,
  original names/counts/sizes. Duplicate assignment is blocked, populated removal
  prompts, and confirmation/progress follow Map/Part. Interrupted uploads retry
  only unfinished files; cancellation and session/Turnstile expiry are covered.
- Schema v2 preserves original intent and UUID folder/object ownership in D1.
  Migration `0002_logical_maps.sql` adds nullable/defaulted metadata without
  regrouping old records. Current schema was inspected and privately exported
  before applying. Four existing terminal legacy records remain accessible and
  unchanged; there were no pending records. Worker version
  `11b311fb-ad38-4454-9da4-2b07de4aa836` is deployed. Live config advertises v1/v2,
  retains Turnstile and the original global limits; an invalid structured request
  is rejected before reservation, with no session/upload created.
- Local Submissions shows map cards, original intent, corrected structure and
  inspection. Corrections save a separate dated local audit; resolved groups
  freeze. Normal/Rehost handoffs retain all existing trusted importer checks.
  Corrected team/season survives inspection; later maps naturally reuse confirmed
  local series context. File times remain identification hints only.
- Healthy archive receipts consume exactly one reviewed map in order, with all
  rehost segments together. D1 revision checks and transaction guards prevent
  concurrent partial claims/audit overwrites. Receipt retry is idempotent.
  Local receipts prevent duplicate import/rejection even if cloud sync fails.
  Partial submissions remain Reviewing; individual/map/remaining-folder rejection
  preserves valid local imports. All objects remain until overall terminal status
  plus seven days; hourly minute-17 cleanup, reconciliation and caps are unchanged.
- **718 Python tests + six subtests**, one optional smoke skip; **44 frontend
  tests**, **19 Worker tests**, Go tests/vet and both builds pass. The required
  Normal A + Rehost B/C fixture exercises D1/R2, upload interruption/retry,
  staging, both local importers, Healthy archives, same-series reuse, independent
  consumption, sync failure/retry and terminal retention. All fixture imports use
  isolated SQLite and parser fixtures; no production map was imported/reparsed.
- Actual quoted **Start NECC Admin.cmd** restarts `.venv` Python from repository
  source and requests the browser. Structured uploader/admin browser checks pass
  at 1440/1100/768/390px. Chrome/Edge trusted CDP drops and read-only input both
  discover the real protected **30 folders / 209 files**, retain assignments on
  duplicate child addition and make zero modern-handle requests. These tests do
  not reproduce the Windows Explorer mouse gesture or a human Turnstile upload.
- The deployed [Submit Replays page](https://uah-r6.github.io/#/submit) passes the
  complete structured browser regression at all four widths: hierarchy, file
  times, duplicate assignment, removal prompts, keyboard reorder, cap errors,
  interrupted upload/retry, cancellation/expiry, and grouped admin handoffs/shared
  confirmed series. Uploads in these browser checks use intercepted fixture cloud
  responses. Separately, an unmocked live browser confirms real Worker config,
  v1/v2 support, configured Turnstile, BO5 cards and responsive layout. No real
  production replay submission/upload/import was created. Real launcher admin
  reads all four preserved terminal legacy records and zero pending records
  through the deployed Worker at all widths, with no JS errors or mutations.
- Preservation PASS: all **22 SQLite tables**, **49 public JSON files**, **171
  archive/parser/formula/validator files**, and all **nine Healthy archives**.
  Integrity/FKs pass; old cloud inbox/storage remain unchanged. No Rating,
  statistics, player/team/role data, rehost reconstruction or public stats output
  changed. All **49 live public statistics JSON documents** match the repository
  baseline byte for byte after Git's Windows/Linux newline normalization; local
  JSON bytes remain exact against the pre-task backup. No new research or
  unrelated feature was started.

Private backup/evidence: `data/research/logical-submissions-20261008/`, including
`before.sqlite`, `d1-before.sql`, schema/deployment logs and browser/preservation
reports. SQLite backup SHA-256:
`6caa9cc4b5ec93931d9ebc490757b823039a6d14233869104e0ea3ca1deb7b03`.
These files, credentials, staging and raw replay bytes remain ignored.

Read [SUBMISSIONS.md](SUBMISSIONS.md) for workflow, migration and recovery guidance.
Focused verification: `scripts/verify-logical-submission-preservation.py --cloud`,
`scripts/verify-logical-submissions-ui.py`, and the extended protected-folder
`scripts/verify-replay-selection-ui.py`. **NEXT ACTION: STOP.** Logical-map intake
is complete. This final documentation checkpoint is pushed separately from the
verified release; normal administration remains browser driven and all existing
statistics/importer safeguards remain authoritative.

## Previous: production Rating evidence reliability — 2026-10-08

**COMPLETE, PUSHED AND LIVE VERIFIED. STOP AFTER THIS PASS.** Baseline `f62263e`.
Release `490e4ff` is on main; [Pages run 37805431015](https://github.com/uah-r6/uah-r6.github.io/actions/runs/37805431015)
completed successfully. All **49 live public JSON documents** match local exports
at `https://uah-r6.github.io/`. White Player Stats, all four series, White
Nighthaven, Blue partial/full trends, real and synthetic SUB views, read-only
embeds and Submit Replays shell passed at 1440/1100/768/390px with no JS errors.
See [RATING_EVIDENCE_PRODUCTION.md](RATING_EVIDENCE_PRODUCTION.md) for the nine-map
audit, exact diagnosis, twenty per-player Series Ratings and preservation checks.

- White Nighthaven `035ff71d4884` is eligible. A generic extraction fix recognizes
  an identical canceled objective terminal snapshot under continuous typed
  ownership. The later complete owner now binds correctly. Only the previously
  unbound FSU opponent Avner.oL R6 plant was added; all unrelated raw UAH stats,
  score, metadata, round IDs, mappings, identities and frozen roles are unchanged.
- White FSU has **2/2 maps / 21/21 rounds** rated for four normal participants and
  Dinoted11's actual SUB appearance. His normal Career/Season/trend remain empty.
- All nine archives Healthy; **six maps / 63 rounds** eligible. Kafe R9 body/owner,
  Placements Border R6 unsupported disable, and Chalet R9–12 nine-player segment
  remain blocked. Blue coverage: Placements 1/3, 10/38; Michigan 1/2, 12/24; UCF
  2/2, 20/20. No evidence guessed and no eligibility gate weakened.
- Normal and rehost imports automatically attempt the existing trusted evidence
  pipeline after core import/archive success. Exact secondary failures are shown
  with a local repair action; valid match data survives them. Map detail shows
  eligibility/exclusion. Bulk maintenance isolates every map's result and never
  publishes. Existing eligible maps are no-ops.
- **708 Python tests + six subtests**, one optional smoke skip; **39 frontend
  tests**, full Go tests, Go vet and both builds pass. Actual quoted
  **Start NECC Admin.cmd** runs repository `.venv` Python and source modules,
  opens Chrome and serves the real admin repair/audit path. Admin, import result
  fixtures, all four Series, White full trends, Blue partial/mobile tooltips, SUB
  views, embeds and submission shell pass at 1440/1100/768/390 with no JS errors.
- Preservation PASS: **22 original SQLite tables**, **49 public JSON documents**,
  **116 protected archive/formula/validator files**, exact five prior eligible
  maps' v3 inputs, all v2 snapshots, unchanged memberships/appearances/operators/
  native inputs, SQLite integrity/FKs. Frozen model and research data unchanged.

Private recovery and diagnostic reports: `data/research/rating-evidence-production-20261008/`.
Backup SHA-256: `d77e18a41e2cb56129ed24f3ad17235c25cf8e4f5dfabb0b474542c472a3fa53`.
Read-only continuation: `scripts/verify-rating-production.py --verify` and the
production admin/public browser scripts documented in the focused report.
**NEXT ACTION: STOP.** This reliability pass is complete. The three blocked maps
remain unrated until independent trustworthy evidence can be proven. Do not
begin another model or unrelated feature. The following documentation checkpoint
records the completed release and live verification; it changes no application
or website data.

## Previous: roster administration and mistaken-player deletion ? 2026-10-07

**COMPLETE, PUSHED AND LIVE VERIFIED. STOP AFTER THIS PASS.** Release `0cf0cfe`
is on main. [Pages run 37720209529](https://github.com/uah-r6/uah-r6.github.io/actions/runs/37720209529) succeeded. Baseline HEAD
`8ff6c46` included user roster additions and dirty public exports; these were
backed up and preserved. See [ROSTER_ADMIN.md](ROSTER_ADMIN.md) for the diagnosis,
real data changes, three separate actions, reference audit and rollback design.

- Existing global **Nachofries_08 / player 10** is now a regular White member from
  **2026-10-07**. No pending/imported White replay supported an earlier date.
  Exactly one identity/alias represents this username. It remains Active, unbound
  and not substitute eligible, with no invented statistics.
- **Nanor555 / player 12** is no longer on White. Its same-day unused mistaken
  membership was cancelled; identity, alias, Active status and eligibility were
  preserved. Nanor555 was not globally deleted.
- Add / Assign detects existing global usernames and aliases case-insensitively,
  including hidden unassigned/sub-only identities. The old failure was a unique
  alias collision from attempting to add an already-existing hidden identity.
- Obvious dated **Remove from roster**, separate **Mark Active/Alumni**, and
  **Advanced / Danger zone ? Delete mistaken player** are available locally.
  Historical deletion is blocked. Unused deletion requires the exact current
  username, repeats the audit under a write lock, and restores database/public
  JSON on export, validation, installation, SQL or commit failure.

Verification: **687 Python tests + six subtests**, one optional replay smoke
skip; **39 frontend tests**; both builds. Actual **Start NECC Admin.cmd** restarted
PID 23388 to **5752**, opened Chrome and confirmed current `.venv` and repository
imports. The real admin browser created, aliased, removed, changed status,
reassigned and permanently deleted a temporary player; no test identity remains.
Lgon deletion was blocked in UI and API. Admin/public checks passed at
1440/1100/768/390px. Existing Series/trend/highlight/substitute/embed/submission
shell checks passed. Public White has five regular roster members and no match
statistics; Nacho's empty profile and retained Nanor profile work.

Preservation PASS: **22 original SQLite tables**, **44 public JSON documents**,
**101 protected archive/parser/formula files**, all **7 Healthy archives**,
7 maps / **82 rounds**, frozen appearances, corrections, statistics, Ratings and
Series Ratings. Only the requested memberships and export freshness changed.
SQLite integrity/FKs pass. Private backup/evidence:
`data/research/roster-deletion-20261007/`; backup SHA-256
`6c9e7714bfb8a91bb857ff3241f0e4e444aea74ae7842fc125e75e2c81b116cf`.
No parser, formula, evidence, appearance classification, ownership/rehost,
archive, submission, Cloudflare or embed implementation was modified.

Live verification PASS at `https://uah-r6.github.io/`: **all 44 JSON documents**
match local exports exactly; White has five current regular members, including
Nachofries_08 and excluding Nanor555. Season/Career empty states, both zero-match
profiles, unchanged Blue Player Stats and empty Sub Stats pass at all four widths
with no JavaScript errors. The temporary production test identity, aliases,
memberships and public JSON are fully gone; the database retains its original
12 real identities. Live evidence is in the ignored `live-browser/` directory.

**NEXT ACTION: STOP.** This roster cleanup is complete. The repository checkpoint
records verified deployment; do not resume research or unrelated features.

---

## Current: historical Series Rating evidence audit - 2026-10-07

**COMPLETE, PUSHED AND LIVE VERIFIED. STOP AFTER THIS PASS.** Release `88d858e`
is on main. [Pages run 37708846633](https://github.com/uah-r6/uah-r6.github.io/actions/runs/37708846633) succeeded.
Baseline HEAD `1b00f59`, initial working tree clean. This focused pass audited
every production map and every participating player, implemented guarded local
evidence maintenance, and added restrained partial Series Rating presentation.
See [the complete audit and repair safeguards](RATING_EVIDENCE.md).

All seven archives are Healthy, but **none of the three missing evidence sets
can be safely recovered by the current trusted readers**:

- Michigan Chalet `b595ffaaec57`: logical R09–R12 / segment 2 R01–R04 have only
  nine players in normalized and fresh trusted kill-reader output. Current and
  prior reader hashes match. Complete kill counters/roster continuity remain
  unavailable; no profile or counter was synthesized.
- Placements Kafe `5adc26f7a402`: R09 plant occurrence has no verified actor or
  UID (`timer_owner_body_unresolved`). Other supported actors match history.
- Placements Border `8a6357ff307c`: R06's stored disable has no trusted disable
  occurrence; its verified plant matches AzoozNewzz. No supported actor correction
  exists. Removing the historical disable would not be an evidence-only repair.

No production evidence sidecar, normalized round, historical objective or Rating
was rewritten. New private audit metadata records actual archive checks and
blockers. Placements remains 1/3 maps / 10/38 rounds; Michigan 1/2 / 12/24; UCF
2/2 / 20/20 for all five participants. All 15 player/series Ratings were verified
against combined eligible raw inputs evaluated once and full-precision weighted
map Ratings within `1e-12`; exact values are in the evidence document.

**Statistics → Audit Rating Evidence / Repair From Healthy Archive** is available
only on localhost. The collector and parser semantics are unchanged. Normal
kill `store()` still rejects overwrite; explicit incomplete reconciliation
requires a fresh Healthy-archive proof, same sources/profile/team identities,
complete inventory, unchanged display counts, compare-and-swap and a private
prior/new audit. Objective backfill requires matching unique core actors and
immutable normalized inputs; sidecar/audit commit together. Conflicting evidence
cannot be overwritten; stale/corrupt seals fail closed. Every repaired map still
runs the complete existing v3 native/opening/clutch path. No eligibility gate or
formula was weakened. The admin reports blocked repairs without exporting.

Partial trend points are hollow rings with subtle **PARTIAL** in selected detail;
full points remain filled. Exact displayed Rating and player map/round coverage
remain prominent. Roster/Sub roles, normal/sub statistics isolation and normal
trend exclusion are preserved.

Verification: **657 Python tests + six subtests passed**, one optional replay
smoke test skipped; **37 frontend tests** and public/admin builds passed. Actual
`Start NECC Admin.cmd` launch restarted the previous server, opened Chrome and
confirmed `.venv\Scripts\python.exe` and repository imports. Real admin browser
buttons audited all seven maps and attempted all three guarded repairs.
Admin and public checks cover 1440/1100/768/390px; trend checks include hover,
keyboard focus/arrow keys and touch taps for partial/full points, all three
Series pages, plus Player Stats/Sub Stats, embeds and mocked submission flow.

Preservation PASS: all **21 preexisting SQLite tables**, all **30 public JSON
documents** (freshness only), all four eligible map Ratings and UCF Series
Ratings exactly, **168 protected archive/parser/formula files**, all seven
Healthy archives, SQLite integrity/FKs. No reimport, normalized replacement,
parser/operator changes, Rating research or substitute refactor occurred.

Private evidence is ignored under `data/research/series-evidence-repair-20261007/`:
unchanged SQLite backup SHA-256
`ad66d9e69c8a82a98a952d2c25dbc1912dd1fb8dabb11394681503de71ff042d`, original
tables/JSON/hashes, complete map audit, current raw objective JSON, actual admin
API/browser results, preservation and all-player raw-input checks. Verification
scripts are `verify-rating-evidence-repair.py`,
`verify-rating-evidence-admin-ui.py` and updated `verify-series-experience-ui.py`.

Live browser verification passed at 1440/1100/768/390px for Lgon's real partial
Placements/Michigan and full UCF trend points, all three Series pages, exact
five-player Ratings/coverage, hover/focus/arrow keys/tap and logical round
highlights. Player Stats/Sub Stats, public presentation/embeds and mocked
submission flow passed live; no cloud upload or production import occurred.
All 30 live JSON files and public JS/CSS match the release byte for byte.
Submission configuration remains enabled, available and Turnstile configured.
Public assets: `index-BroLbviU.js` / `index-Dx1KU8S8.css`; local admin assets:
`admin-JFBeboSB.js` / `admin-cAL6FB7E.css`. Current launcher PID 23388 imported
the repository source. The private audit table contains nine explicit checks
from three verification passes; all recorded the same exclusions and no repair.
All 15 before/after Series Rating/coverage rows compare exactly equal.

The documentation checkpoint following the release records these results.
The focused historical evidence audit and partial presentation pass is finished;
three genuinely unsupported maps remain unrated. **STOP. No additional parser
or Rating research is authorized by this pass.**

## Previous: global substitute eligibility and frozen appearances - 2026-10-07

**COMPLETE, PUSHED AND LIVE VERIFIED. STOP AFTER THIS PASS.** Release `573086b`
is on main. [Pages run 37700419344](https://github.com/uah-r6/uah-r6.github.io/actions/runs/37700419344) succeeded.
Baseline HEAD `f354197`. The initial working tree contained older generated
JSON without series/highlights; its copy and complete diff were preserved under
ignored `data/research/substitutes-20261007/` before current-source regeneration.

Added global substitute eligibility, sub-only creation, dated unassignment and
immutable per-map roles. Existing 35 player/map appearances migrate as roster.
Role classification uses map ownership and historical membership; eligible subs
never vote in side detection. Imports repeat validation inside the write
transaction. Rehosts use the logical map date and retain confirmation/source
safeguards. Aliases/profile binding, one identity, historical roles and archives
are preserved. Active/Alumni is unchanged; explicitly eligible Alumni can sub
without reactivation.

Normal team/season/global Career and Rating trends exclude sub appearances.
Separate team Subs aggregates and per-player/team substitute profiles use the
same existing stat aggregation and frozen Rating. Map/series pages retain actual
subs with a compact SUB badge. Mixed-role series retain all-played Series Rating
while the normal trend uses only roster map inputs. Publishing validates scope
membership/counts and profile references against actual map participants.

Public Player Stats defaults Blue / active season / Roster. Roster/Subs is URL
backed (`?team=white&players=subs`), with sorting/period/navigation preserved.
Old persistent Career selection is ignored; deliberate session choices survive
refresh and expire after 12 hours. Only actual substitute appearances enter
Subs. Relevant global profiles offer a separate View Sub Stats area with team
and period selection. Embeds remain independent, roster only.

Verification: **627 Python tests + six subtests passed**, one optional real
replay smoke test skipped; **36 frontend tests passed**; public/admin builds
passed. Browser checks cover 1440/1100/768/390px: Blue/White Roster/Subs,
active/default/Career/history, sub-only and multi-team profiles, Series SUB
badges, unused-pool exclusion, actual CMD-launched admin Roster, real Fortress
preview and frozen map details. Sub-only/eligibility browser mutations were
intercepted; backend API tests use temporary databases. Public presentation,
cross-origin embeds/storage restrictions and mocked submission checks passed.
No production replay was imported or reparsed into SQLite; the real preview was
read only. No cloud submission or cloud architecture changes occurred.

Production migration/regeneration through the actual launcher/API passed:
all original data in 19 SQLite tables and existing values in 30 public JSON
documents preserved, including all seven maps / 82 rounds / three series /
five identities, memberships, operators, objectives, frozen Ratings, Series
Ratings, trends and highlights. All seven archives Healthy; 2,508 protected
files byte-identical. SQLite integrity/FKs pass. Public diffs add role/scope
metadata and freshness only. All current appearances remain roster, and actual
Subs views are empty. Private backups/evidence stay ignored.

Launcher: `Start NECC Admin.cmd` invoked directly using PowerShell's quoted call
operator. `.venv\Scripts\python.exe` imports the repository source and opens
Chrome at localhost; runtime and launch logs retained privately. Admin build:
`admin-CJLPljeF.js` / `admin-BMfB3oRP.css`. Public build:
`index-kgkqpUj9.js` / `index-C7bM9N6U.css`.

See [SUBSTITUTES.md](SUBSTITUTES.md) for schema, scope semantics, explicit Alumni
policy, migration and read-only verification commands.

Live verification passed for Blue/White Roster/Subs at 1440/1100/768/390px,
active-season default despite stale saved Career, deliberate Career refresh,
URL/back navigation, real normal profiles and unchanged trends. Intercepted
responses exercised sub-only profiles, team-specific Sub Stats, actual Series
SUB badges and unused-pool exclusion against the live frontend without writing
test data. Existing presentation checks passed: all series/map navigation,
exact trusted Ratings, compact Blue/White embeds, real cross-origin framing,
restricted storage, synthetic season rollover and Alumni. Mocked submission
workflow passed. Cloud public config remains enabled/available with Turnstile;
no real challenge or upload was attempted.

Live JS/CSS and all 30 public JSON documents match the tested build and release
bytes exactly. No JavaScript errors or horizontal overflow. Actual launcher
reinvocation opens the final admin build in default Chrome from repository
source. Final preservation recheck passes for original table values, existing
public statistics and seven Healthy archives. No production fixtures remain.
Private SQLite/replay/research paths passed Git ignore checks; no raw files were
staged. The prior protected-folder Explorer gesture and authenticated Google
Sites editor limitations remain separate and unchanged.

**NEXT ACTION: none for this request.** This final documentation checkpoint is
pushed on main, with a clean working tree. STOP. Do not resume Rating research,
parser changes or unrelated feature work.


## Previous: main Player Stats team scope — 2026-10-07

**COMPLETE, PUSHED & LIVE VERIFIED. STOP AFTER THIS PASS.** Release `2c65b0e`
is on main. [Pages run37694748466](https://github.com/uah-r6/uah-r6.github.io/actions/runs/37694748466)
succeeded. Baseline clean `af0e6eb`.
Main Player Stats now shows one team at a time. Plain `/#/players` and invalid
queries canonicalize to `/#/players?team=blue`; the single navigation item also
opens Blue. A visible accessible Team selector uses the published team index and
existing public visibility/alias rules. If Blue is unavailable, the first active
team is selected; no available default produces a safe empty state.

Selection lives in the URL, supporting refresh and browser back/forward. Global
season/Career selection is preserved. Team-colored heading/table/mobile cards
reuse the existing team `/stats` renderer and only fetch existing
`teams/<slug>/<period>.json`. Sort and Alumni choices persist while switching.
A response ownership/period guard prevents old-team players from briefly showing
during a pending fetch. White's empty state shows no Blue players. Team Career
leaderboards remain team-specific; global player Career profiles remain cross-team.
Embeds retain independent active-season/team behavior. No browser recalculation.

Verification: **33 frontend tests passed**; public/admin builds passed. New scope
browser suite passed 1440/1150/768/390px: defaults, Blue/White exact data, canonical
aliases, invalid query, team colors/titles, URL switching, keyboard selection,
refresh/back/forward, period/sort preservation, Career, synthetic future team and
same-player transfers, missing Blue/no teams and delayed-response isolation.
Existing presentation suite passed, including team pages, Alumni/future-season
fixtures, compact embeds and cross-origin iframe. The old synthetic rollover
fixture's team/period metadata was corrected to match the scope it represents;
production exports were not edited. Series/highlight and Methodology suites passed
with all 82 logical rounds/110 frozen points. Mocked submission workflow passed.

Preservation passed against 918 baseline file hashes: all 30 public JSON documents,
SQLite, private settings, all 89 archived files, backend/export/Rating/parser/
statistics/research/Cloudflare code are byte-identical. Only authorized frontend,
browser-test and documentation files differ. No regeneration, parsing, import,
recalculation or real cloud submission occurred.

See [PUBLIC_PRESENTATION.md](PUBLIC_PRESENTATION.md#main-player-stats-team-scope)
for behavior and read-only verification commands. Ignored preservation/browser
reports: `data/research/player-stats-scoping-20261007/`.

Live verification passed for plain `/players`, explicit Blue/White, invalid
parameters, switching/refresh/back/forward, period/Career/sort preservation,
keyboard selection, titles/colors, phone cards, empty White and no mixed data.
Synthetic future-team/alias/transfer/delayed-response fixtures passed against the
live frontend. All requested 1440/1150/768/390px widths passed without overflow.
Existing team pages and global Career profiles, series pages/all 82 rounds,
Methodology 110-point visualization, Blue/White compact embeds and real
cross-origin iframe, storage restrictions and mocked submission workflow passed
live. Public cloud config remains enabled/available with Turnstile configured;
no real cloud upload, challenge completion or backend changes were attempted.

All 30 production JSON documents match committed bytes and remain identical to
the pre-change data. Live JS/CSS match the tested build. Final preservation checks
confirm no production SQLite/archive/settings/statistical changes. Existing
manual protected-folder Explorer gesture and authenticated Google Sites editor
limitations remain separate; no new claims are made about those workflows.

**NEXT ACTION: none for this request.** Deployment and live checks are complete.
This final documentation checkpoint is pushed on main; working tree is clean.
STOP. Do not begin unrelated feature work or resume research/parser/backend work.

## Previous: Series Rating, trends and sparse round highlights — 2026-10-07

**COMPLETE, PUSHED & LIVE VERIFIED. STOP AFTER THIS PASS.** Release `27c4d61`
is on main. [Pages run37692722366](https://github.com/uah-r6/uah-r6.github.io/actions/runs/37692722366)
succeeded, and production serves the exact tested JS/CSS and all 30 committed
public JSON documents. Baseline clean `b270640`. This pass adds public
`/#/series/:seriesId` pages, aggregate
Series Player Stats with visible player-specific Rating coverage, Matches →
series → map navigation, and one exported Series Rating per player trend point.
The exact Rating is prominent on hover/focus/click/tap with date/opponent/team/
recorded W–L/coverage context. Existing map Ratings and map routes remain.

Series Rating combines trusted eligible counts and evaluates frozen v3 once.
Tests prove equivalence to round-weighted **full-precision** map Ratings and
refuse an unweighted or cached-value shortcut. Normal displayed statistics
include all played maps. Coverage is Placements 1/3 maps, 10/38 rounds; Michigan
1/2 maps, 12/24 rounds; UCF 2/2 maps, 20/20 rounds for all five current players.
No eligible rounds means null/— and no trend point, never fake zero.

Breakdown uses existing complete credited counters, validated native clutch
logic and corrected core objective actor evidence, with historical internal-ID
bindings and only the imported UAH team. Max two compact player groups/two labels;
ACE > 4K > 1v2–1v5 > 3K > 1v1 > Disable > Plant. Unsupported types abstain
independently. **31 of 82 rounds highlighted; 51 unlabelled.** No routine 2Ks,
openings, trades, event logs or opponent identities. Chalet retains only its
independently verified plant, without a credited-count/finisher fallback.

See [SERIES_EXPERIENCE.md](SERIES_EXPERIENCE.md) for the mathematical proof,
export schema, evidence rules, real-map audit, reference and continuation commands.

Local verification: **606 Python tests + six subtests passed**, one optional
real-replay smoke test skipped; **29 frontend tests passed**; public and admin
Vite builds passed. New series browser suite and existing presentation suite
passed at 1440/1150/768/390px, including exact five-player Ratings, partial/null
coverage, navigation, actual logical rounds, hover/focus/click/touch, keyboard
selection, career team-move/season fixtures, Alumni and single/empty states.
Existing Methodology suite retains 110 frozen scatter points. Chrome/Edge replay
selection regressions and mocked submission workflow passed. Existing compact
embeds, restricted-storage behavior and real cross-origin iframe passed locally.

Preservation: read-only candidate export and final comparison matched every
previous public field in all 27 original JSON documents after removing only
approved additions and timestamp. Public validation passes all 30 documents.
683 baseline paths were checked: only authorized exporter/validator/docs/public
JSON differ. All 19 SQLite tables, historical normalized data, snapshots,
memberships, frozen Rating/parser/credited/objective/clutch logic, private
settings, research and Cloudflare backend are unchanged. All 89 private archive
files match their hashes and all seven archives verify Healthy. No replay
parsing, imports, recalculation/database writes or real cloud uploads occurred.
Ignored evidence: `data/research/series-experience-20261007/`.

Live verification: new series suite and full presentation suite passed at
1440/1150/768/390px, checking all three series/five player Ratings and coverage,
all 82 rounds, links, exact hover/focus/click/tap values, empty/single/career/Alumni
fixtures and no horizontal overflow. Methodology regression passed with 110 frozen
points and unchanged model accuracy. Existing embeds passed 1000/800/600/390px,
restricted-storage checks and a real cross-origin iframe of production. Chrome
and Edge replay-selection suites passed; mocked submission workflow passed.
Real public cloud config remains HTTP 200, enabled/available, Turnstile configured,
Blue/White. No cloud backend mutation, new real upload or bot challenge completion.

Limitations: incomplete historical evidence intentionally limits Ratings and
highlights; visible coverage is preserved rather than filled with guesses.
Recorded W–L describes only stored maps. The earlier manual Windows Explorer
protected-folder gesture and authenticated Google Sites editor checks remain
separate pending manual checks; their implementations were not changed here.
Static hash routes retain program-level social previews and route-specific
browser titles. No new parser compatibility claims are made by this pass.

**NEXT ACTION: none for this request.** The enhancement, deployment and live
verification are complete. This final documentation checkpoint is pushed on main;
working tree is clean. STOP. Do not resume research, parser changes, remote admin,
notifications, opponent analytics or unrelated work without another request.

## Previous: public presentation and Google Sites embeds — 2026-10-07

**COMPLETE, PUSHED & LIVE VERIFIED. STOP AFTER THIS PASS.** Main release `674faad`
and embed storage safeguard `9c027b9` are on main. Both Pages deployments passed;
[final release run37687556321](https://github.com/uah-r6/uah-r6.github.io/actions/runs/37687556321)
succeeded. Production serves the exact final built JS/CSS. Baseline clean `227fb87`.

Implemented generic unlisted active-season Player Stats embeds, compact phone
cards, trusted exported v3 map Rating trends, recorded-map series summaries,
stronger stored team accents, accessible shared stat help, export freshness,
polished empty-team states, official-asset favicon/social metadata, meaningful
route titles and 404 handling. No new chart dependency. Shared display definitions
and filters serve desktop, mobile and embed views. See
[PUBLIC_PRESENTATION.md](PUBLIC_PRESENTATION.md) for behavior and instructions.

Google Sites **Insert → Embed → By URL**:

- Blue: https://uah-r6.github.io/#/embed/blue/player-stats
- White: https://uah-r6.github.io/#/embed/white/player-stats

Start with **800 × 360px** for five players. The same URL follows the active
published season, independent of the normal site's saved period and without
accessing browser storage. Optional fixed
history: `?season=fall-2026` after the hash route. Responsive embeds keep
10/7/5 columns with Rating always visible and no normal page chrome. Unknown
teams/seasons show a safe error. Future valid team slugs use the same component.

Verification: **24 frontend tests**, **565 Python tests + six subtests** passed;
one optional replay smoke test skipped. Both public/admin Vite builds passed.
The presentation suite passed **locally and LIVE**: 1440/1150/768/390px public
routes; 1000/800/600/390px embeds; exact trusted stats; saved Career isolation,
active-season rollover, **restricted browser storage without any embed storage
access**, generic team, explicit historical override and Alumni
fixtures; sorting and accessible focus/click/keyboard help with viewport-safe
popovers; chronological exact chart values, career scope, single/empty states,
map context and keyboard/tap selection; recorded-series W/L and map links;
404/titles/metadata; and a **real cross-origin iframe of production**. Existing
Methodology regression passed locally/live (110 frozen points). Replay-selection
Chrome/Edge regressions passed locally/live. Mocked submission workflow tests
passed. Live public cloud config is enabled/available with Turnstile configured.
No new real upload, challenge completion, import or reparse was attempted.

The only export addition is UTC `index.json.generated_at`. A read-only SQLite
candidate export matched every previous field in **all27 JSON documents** before
its output was copied to public data. Public validation passed. **All27 live JSON
documents match committed bytes**, and JS/CSS match the tested build. Hash checks
cover158 protected paths: only the authorized exporter metadata change and public
index timestamp differ. SQLite, Rating/parser/objective/credited-kill logic,
archives, historical maps, memberships, private settings and Cloudflare backend
remain exact. Blue stays7maps/82rounds (4v3eligible maps/42rounds); White is empty.
Evidence remains ignored under `data/research/public-presentation-20261007/`.

Limitations: the production response has no X-Frame-Options or CSP framing
restriction and the cross-origin harness passes; an authenticated Google Sites
editor session was not tested. Sites controls frame height. Static hash routes
share program-level Open Graph previews; browser document titles are specific.
Same-date trend ordering uses recorded export order, not invented precise times.
The earlier real Windows Explorer gesture remains a separate pending manual
check; its implementation and recorded limitation are preserved.

**NEXT ACTION: none for this request.** The presentation release and verification
are complete. This final documentation checkpoint is pushed on main; working
tree is clean. Stop. Do not resume research, parser changes, remote administration,
notifications or unrelated backend work without another request.

## Previous: focused replay-folder selection usability — 2026-10-07

**READ-ONLY FOLLOW-UP DEPLOYED; AUTOMATED LIVE CHECKS PASS.** Initial release
`dad2429` and corrective release `0090a04` are pushed on main.
[Pages run37681761490](https://github.com/uah-r6/uah-r6.github.io/actions/runs/37681761490)
succeeded for the correction. Baseline clean `3cf6c77`. The requested frontend improvement is implemented:
whole MatchReplay or single/multiple replay-folder drag/drop, native picker,
standard directory browse, one shared discovery/selection path, SHA-256 duplicate
addition checks, selected-only uploads, friendly protected-folder/cancel guidance,
keyboard-accessible Steam/Ubisoft help, compact mobile selection and newest-first
replay cards. Upload protocol, rehost/Turnstile and backend remain unchanged.

**19 frontend tests and both builds pass.** Chrome and Edge browser suites pass
at 1920/1366/768/390: modern/legacy/refused-handle drop paths, duplicates, native
success/cancellation/refusal, fallback controls, exact sourced help, keyboard tabs,
multiple-map rehost confirmation, selected-only manifest, cap/error/progress/retry
and receipt. The real protected Steam directory yields **30 folders / 209 files**
via automated read-only input in both browsers. No production submission/import.

The user's real drop still displayed **contains system files** after the initial
deployment. Investigation found modern directory drop handles perform the same
sensitive-entry check and popup as the native picker (confirmed in Chromium
source). The follow-up prefers read-only entries and **does not call** the modern
API when an entry exists. Clicking/keyboard-activating the box now opens standard
directory browse. A trusted browser/CDP drop of the real protected folder passes
in both Chrome/Edge with30folders/209files and **zero modern-handle requests**;
those entry/read calls are real browser implementations, not JS file fixtures.

The corrected browser suites pass against **https://uah-r6.github.io/**, including
the trusted browser drop of the real protected path (all209files), zero modern
access requests, and a repeated physical child folder preserving its selection
without duplication. OS Explorer gesture verification remains separate. Served
JS/CSS exactly match the corrected production build;
all27 live statistics documents match committed LF bytes. The real public cloud
config returns HTTP200, enabled/available, Turnstile configured, Blue/White and
Fall2026. Authenticated read-only cloud storage equals the initial snapshot:
zero stored/reserved/pending. Upload/retry/receipt browser tests use mocked Worker
responses only; this pass did not test a new production cloud upload or challenge.

All **158 protected files** (SQLite, public statistics, archive, backend/parser/
Rating/Cloudflare/config/private settings sources) remain byte-for-byte unchanged;
all209 original replay sizes/timestamps remain exact. Cloud inbox was read-only
checked: enabled, cap9GiB, zero stored/reserved bytes or pending submissions.

Instructions were checked against official Steam support and Ubisoft's rendered
current installation-location guide: Library → game → Manage → Properties →
Installation directory. Ubisoft's old unverified Open folder wording is removed.
See [SUBMISSIONS.md](SUBMISSIONS.md) for sources, compatibility and troubleshooting.
Private evidence: `data/research/replay-selection-20261007/`.

**MANUAL CHECK PENDING AFTER FOLLOW-UP:** the initial normal Chrome Explorer
drop failed with the protected-folder popup. The read-only correction is deployed
and live verified; the user was asked to retry Explorer drag after a hard refresh.
Expected discovery:30folders/209files;
**do not submit/upload**. Playwright/CDP does not prove the OS Explorer gesture.
No claim of a verified real Windows drag is made until the user reports its result.

**NEXT ACTION:** record that minimal manual check or fix any reported selection
issue. Corrected implementation/deployment/automated verification are complete. Stop after
this focused fix; no backend/statistics or unrelated feature work.

## Previous: public replay submissions deployed and verified — 2026-10-07

**COMPLETE, PUSHED & LIVE VERIFIED.** Initial release `244fe4d`, verification/retry follow-up `28c489a`, and final implementation `27728ec` are on main. [GitHub Pages run 37673326321](https://github.com/uah-r6/uah-r6.github.io/actions/runs/37673326321) succeeded. Baseline was clean `b82399a`. Public [Submit Replays](https://uah-r6.github.io/#/submit) is live. No paid plan/add-on was enabled. See [SUBMISSIONS.md](SUBMISSIONS.md) for architecture, privacy, limits, workflow, deployment, rotation, maintenance, troubleshooting and future remote-admin/storage alternatives.

### Deployed resources and local configuration

- Worker: `uah-r6-submissions`, `https://uah-r6-submissions.r6-necc-stats.workers.dev`, deployed version `0a8e16ff-cc41-4314-ae76-93ae0fb3f969`.
- Private Standard R2: `uah-r6-replay-submissions`; verified public r2.dev access disabled, no custom domains.
- D1: `uah-r6-submissions`, ID `f8e47ffc-7049-4bcd-b35a-407c5ee065b2`; migration applied remotely.
- Managed Turnstile: `UAH R6 Replay Submissions`, domain restricted to `uah-r6.github.io`.
- Hourly cleanup at minute17 UTC; terminal retention7days, upload capabilities/reservations2hours. Pending/reviewing files never expire merely because they are old.
- Hard cap9GiB (`9,663,676,416` bytes), atomic full reservations, actual R2 reconciliation, durable maintenance leases, warnings75/85/95/100, 64MiB/file, 2GiB/submission, 12folders/240files, hashed-IP/hour and global/hour rates.
- Public `web/public/submissions-config.json` contains the Worker URL only. Ignored `data/private/submissions.json` supplies the backend admin credential automatically. Worker secrets and OAuth credentials are never in public/admin browser JavaScript or Git. Private staging is `data/submission-staging/<uuid>/`.

Public flow explicitly chooses real team/season, groups directory-selected `.rec` files locally, supports modern and fallback pickers, full-folder/multiple-map/rehost selection, rehost No/Yes/Not sure, prominent context/totals confirmation, Web Crypto SHA-256, streamed private transfer, retry/cancel and a receipt only after all stored files verify. The Worker does not parse or import matches. UI now handles failed/expired browser verification with an error and retry control.

Local Submissions has a pending badge/list, storage panel, Submitted as / editable Importing as, verified/resumable staging, existing trusted parser inspection, explicitly labeled selected-team scores, normal/rehost handoff, reject reasons/private notes, receipt retry, terminal cloud removal, cleanup/reconciliation, choices synchronization and emergency intake disable. Existing NECC, roster, duplicate and rehost confirmations remain required. Only successful local import plus a healthy verified archive can consume folders; mixed series stay Reviewing until every folder is resolved. Cloud sync failure cannot roll back valid local stats/archive; saved receipts allow safe retry.

### Verification and preservation

**564 Python tests**, six subtests pass; one optional real-replay smoke skipped. **Nine frontend tests**, **11 Worker tests**, Go `test ./...` and `vet ./...`, both Vite builds pass. Worker tests exercise real Miniflare D1/R2 with full240-file batching, concurrent cap/receipt protection, ownership/CORS/auth/path/rate checks, wrong checksum/missing objects, paginated actual-size reconciliation, expired sessions, old pending preservation, imported/rejected retention and private audit metadata. Synthetic browser tests cover directory fallback/modern handles, required context, confirmation, full inbox before transfer, interruption/retry, completion, verification error/reset and1920/1366/768/390 layouts. Temporary SQLite tests cover both real normal/rehost import hooks, healthy archives and cloud failure/retry. No test imported into production SQLite.

Actual **Start NECC Admin.cmd** was executed through the quoted `.cmd` path twice; it detected/restarted old source. Final PID16928 uses `C:\Users\logan\Documents\R6\r6-necc-stats\.venv\Scripts\python.exe`, cwd repository root, and imports `r6stats/parser/siege_dissect.py` and `r6stats/admin/server.py` from repository source. It opened Chrome. Live local browser exercised authenticated backend options sync/reconciliation, inbox review/staging/inspection, team correction, existing import preview and rejection. No Cloudflare admin token entered the localhost browser.

The user completed real Turnstile and submitted test receipt **R6-546784BFDD** from normal Chrome:10 copied Fortress `.rec` files, **102,627,877 bytes**, submitted as White. Worker/R2 received it privately; local UI downloaded and independently verified it, inspected Fortress /10rounds /CustomGameOnline /5Blue roster matches /existing duplicate. Replay index scores were `[3,7]` because Blue is team1; an overly specific diagnostic assertion initially expected `[7,3]`. The score display was refined to selected-team perspective (**Blue7–3**), without changing replay/stat data. The first test was already cleaned by the script's finally block. A separate explicitly marked test copy was restored through authenticated Wrangler solely to complete remaining live UI checks: corrected Blue context, normal preview duplicate guard, UI rejection and cleanup all passed. This second fixture was not a second public upload; original public-upload proof and remaining review proof are recorded separately.

Both tests' cloud objects and submission/folder/file metadata are removed; private staging is removed. Final authenticated status: **0stored bytes, 0reserved bytes, 0pending, 0remaining submissions**. Synthetic importing/approval tests used temporary databases only. Automated Edge Turnstile failed even with a human click; normal Chrome independently passed. A Chrome debugging launch was blocked by automatic approval review, so no debugging bypass or bot-protection disable was used. The user performed only the normal-browser challenge/upload portion; all administration and cleanup were completed here.

Private evidence: `data/research/submissions-20261007/`, including original and restored live reports, final public regression screenshots, byte checks, runtime/baseline data. All **129 protected files** remain byte-for-byte exact: production SQLite, all27 public statistics documents, all89 archive files, protected parser/stat/Rating code. Settings also match their exact pre-task backup. No production import/reparse, Rating coefficient/input/snapshot, credit/objective/operator/KOST, roster/membership, historical match or archive changes. Secret/private-file audit clean. Live ordinary/cache-busted public stats/config/chart/logo bytes match committed LF data; served public JS/CSS match the final local build. Existing public Methodology/Player Stats browser regression and submission browser checks pass on live Pages at four widths with no page errors/overflow.

**NEXT ACTION:** none for this authorized pass. Public intake and trusted local review are complete. STOP. Do not resume parser/Rating research, automatically import submissions, add remote-admin authentication or enable paid services.

## Current: public Player Stats & interactive Methodology polish — 2026-10-07

**COMPLETE, PUSHED & LIVE VERIFIED.** Release `347fce3` is on main. [GitHub Pages run 37654243337](https://github.com/uah-r6/uah-r6.github.io/actions/runs/37654243337) succeeded. Baseline was clean `3cfcccb`. Public terminology is now **Player Stats**, the main table omits Rounds and the technical kill banner, and normal pages keep concise copy with useful Rating coverage. Table sorting is keyboard accessible and remaining columns have adjusted spacing.

Methodology has five URL-addressable sections, native expandable explanations, four KOST cards, accurate production definitions, team/global season/career scope, frozen v3 technical details and compact Rating history. The interactive scatter projects all **110 exact saved final prediction/target pairs** from APAC North Stage 1 2026. No research evaluation, fitting, downloads or parsing were rerun. Verified final v3 MAE **0.030359332**, original v2 same-row MAE **0.060586453**, **81.8182% within ±0.05**. The small static asset contains public professional identifiers and Ratings only; it lives outside routine generated statistics data. See [PUBLIC_METHODOLOGY.md](PUBLIC_METHODOLOGY.md).

Safety seal: all **144 protected files** (SQLite, all 27 public statistics JSON documents, replay archives and tracked backend/config source) remain byte-for-byte unchanged. No Rating formula/input, historical statistic, team membership, status, parser, archive or import changes. Public JSON validation passes all 27 documents. Six frontend tests, 23 focused Python Rating/team/export/publishing tests and both public/admin builds pass. Headless Edge checks the whole public site at 1920/1366/768/390 widths, keyboard sorting/accordions, URL navigation, chart hover/keyboard/touch and malformed-data fallback; no JS/HTTP errors or document overflow. Private evidence: `data/research/public-polish-20261007/`.

Live verification at **2026-10-07T16:50:09Z**: all 27 public statistics JSON files, the new frozen chart asset and official logo match committed LF bytes at normal and cache-busted URLs. Served JS/CSS match the local production build. Both browser suites pass against **https://uah-r6.github.io/** at all four widths, including team/season/career selection, preserved Alumni history, page/table copy, all Methodology sections, accordion keyboard behavior, chart keyboard selection and actual mobile point taps. No browser JS errors, same-origin HTTP errors or document overflow. Initial parallel asset fetching encountered a transient HTTP 503; bounded retries completed the full byte checks successfully. All 144 safety-sealed local files remain exact. Private reports/screenshots are under `data/research/public-polish-20261007/live-*`.

**NEXT ACTION:** none for this authorized pass. The focused public polish is complete. STOP; do not resume Rating/parser research, public submissions or another feature.

## Current: UAH R6 teams/admin redesign LIVE and verified — 2026-10-07

**COMPLETE.** Backend milestone `0c4ec0c` and production release `ee6844b` are pushed to main. [GitHub Pages run 37643709268](https://github.com/uah-r6/uah-r6.github.io/actions/runs/37643709268) succeeded. Live verification at `2026-10-07T15:26:48Z`: all **27 public JSON documents** and the official logo match committed LF bytes at both normal and cache-busted URLs; deployed JS/CSS match local build bytes. Headless Edge verified root, Blue/White team pages, Blue roster/statistics, both selectors, player season/career, map Rating, methodology and legacy routes at 1920/1366/768/390 widths. Zero JavaScript errors, same-origin HTTP errors, or page overflow. Browser-only Alumni fixtures verified default exclusion and an intact Alumni career profile; real statuses were not changed. Evidence stays private in `data/research/team-architecture-20261007/live-checkpoint.json` and `live-browser/`.

Baseline HEAD: `90739ed`. The prior v3 run below is complete and remains preserved; the current authorized task is the team architecture/redesign. No Rating/parser research has resumed.

Private safety checkpoint: `data/research/team-architecture-20261007/` contains a verified SQLite backup, settings copy, all original public JSON, HEAD/database/public/archive hashes, and candidate migration/export. After candidate verification, production SQLite was migrated to metadata schema version 1. `scripts/verify-team-migration.py` confirms every original database column and every original public JSON field remains exact, all 89 archive files are unchanged, protected parser/stat/Rating/archive source is unchanged, and White is empty. All seven maps / 82 rounds belong to Blue; Blue's team career exactly matches preserved global career statistics. Existing five players remain Active. No new maps, reparses, objective changes, or raw identity changes occurred.

Recovery milestone: `0c4ec0c` introduced the backend and initial scope tests. Implemented: atomic/idempotent metadata migration (including concurrent first connections), immutable map/series ownership, dated memberships, Active/Alumni status, team slug/JSON aliases, team season/career export, global profile splits/history, team CRUD/movement API, explicit import context bound to previews, scoped scans/series/matches/dashboard. Each rehost segment revalidates its dated roster. Publishing validates team ownership/references as well as existing privacy gates and still stages only generated public JSON.

Public/admin redesign is complete: program root, explicit team navigation, season/career selector, Alumni filters, full operator usage, team contribution/history panels, persistent admin context, Teams CRUD, membership dates/moves, and explicit named import confirmations. UAH colors/font were verified against the official guide; the unmodified official Esports homepage logo is installed. See [BRANDING.md](BRANDING.md). Arbitrary colors derive readable accents against both dark cards and muted backgrounds; no team-name theme branches.

Verification: **551 Python tests passed**, one optional real-replay smoke skipped, six subtests passed; **three frontend tests passed**; all Go tests and vet passed; both Vite builds passed. Headless Edge public/admin checks passed at 1920, 1366, 768, and 390 widths with zero JS errors or page overflow. Browser-only Alumni fixtures confirm default exclusion and preserved career profile. The actual quoted CMD launcher opened Chrome, using repository `.venv/Scripts/python.exe` and repository parser/server modules. Live admin scan: 12 recent folders, nine Ranked/ineligible, three existing Custom Games with five Blue roster matches; preview-only checks verify Blue's explicit named confirmation and clearing/revalidation for empty White. No import or database mutation was performed during browser checks. A tablet Seasons-form overflow was found and corrected. All 27 public JSON documents passed preservation/privacy/ownership validation; every original document's old fields remain exact.

**NEXT ACTION:** none for this authorized pass. Launch **Start NECC Admin.cmd**, choose Blue (or another explicitly selected team) and the season, then use the browser. The working application uses the repository's `.venv` and current source. The first-time team choice is deliberate; later choices persist. White is available but empty. This session stops after its completion checkpoint. Future public replay submissions/broader Esports expansion remain documented future work; do not resume Rating/parser research merely because historical notes below contain older next actions.

## Previous completed checkpoint: validated siege_style_v3 LIVE — 2026-10-07

**STOP CONDITION MET.** Runtime/default/public v3 deployment commit `6ae184a` is pushed. GitHub Pages [run37580585635](https://github.com/uah-r6/uah-r6.github.io/actions/runs/37580585635) succeeded. At2026-10-07T06:22:12Z, all20live JSON documents matched committed LF bytes AND decoded local export at both normal and cache-busted URLs. Headless Edge verified all5player season/career pages and methodology, correct Ratings/coverage, zero JavaScript page errors. Public JSON has no private fields, research/archive paths or raw replay data. Live evidence: research/native-v3-live-checkpoint.json; private screenshots/logs: data/research/native-v3-deployment-20261007. Default local publish status now records the verified deployed commit. All7launcher/admin match endpoints independently confirm v3 eligibility and Healthy archives; actual CMD launcher uses repository .venv Python and source files.

### Credited-kill methodology / readiness

Complete whole maps use stable_uid_scoreboard_delta_v1: ten unique nonnil profiles, full five/five team bijection, stable cumulative counters and explicit segment resets. Ubisoft official credited counts remain distinct from preserved kill-feed FINISHER events. Six maps/70rounds use credited kills; the entire12round Chalet map remains legacy due to nine-player rehost participation. No partial-map mixing, invented timestamps, counter-balancing victim joins, or action-start operator redesign.

| Feature | Current policy |
| --- | --- |
| Kills/KD/KPR/side kills | Validated credited counts on70rounds; whole Chalet legacy12 |
| Round multikills / extra kills | Credited round counts on supported whole maps; READY |
| KOST Kill | Any credited kill on supported maps; READY |
| KOST Objective / displayed plants and disables | Production core actor corrections preserved; unsupported historical actors stay as historical data, excluded from v3 whole-map eligibility |
| V3 opening / clutch order | Verified positive serialized offsets and exact native finisher/victim/time/headshot parity; first opposing FINISHER opening, first sole-survivor clutch size and actual winner |
| Credited opening owner / credited victim mapping | NOT READY; native finisher definition is explicit, no downer inference |
| Precise credited trades / refrags | NOT READY; frozen legacy8second trade and KOST-trade inputs retained |
| Pivot / untraded events | Legacy display semantics unchanged; credited upgrade NOT READY |
| HS | Finisher headshots divided by finisher kills; credited-owner shot statistic NOT READY |

Nina/OSAdinho attribution mismatch, Aokayu/missing kind5 relationships, DBNO/recovery ownership and clock epoch/terminal limits remain unresolved. No opaque history kind was promoted from correlation alone. Cumulative counter offsets are not exact elimination timestamps (+2 updates and after-death increments remain permanent regressions). These unresolved relationships do not alter the independently supported count migration or tested explicit finisher/legacy v3 feature definitions.

### Current UAH totals and eligibility

All7maps/82historical rounds,816round-player rows,575kill rows,28objective rows, raw normalized data, players/aliases, operator usage, metadata, rehost structure, archives and immutable v2 snapshots are unchanged by v3 deployment. Lgon's Michigan Border R08 disable remains intact. Current display totals:

| Player | K | D | Plants | Disables | KOST rounds | V3 Rating |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| OhWowJay | 91 | 50 | 2 | 0 | 58 | 1.581421174 |
| Lgon | 81 | 48 | 2 | 2 | 54 | 1.441310153 |
| AzoozNewzz | 57 | 61 | 2 | 0 | 50 | 1.082885288 |
| Tallman3.14 | 37 | 63 | 6 | 0 | 41 | 0.852978563 |
| DinoFireKing | 36 | 51 | 3 | 0 | 50 | 0.764537724 |

V3 Rating uses4whole maps/42rounds per player: Fortress10, Michigan Border12, newer Border11, Nighthaven9. Original Border14 lacks complete verified core evidence for an opponent disable; Kafe14 has an unverified historical plant; Chalet12 lacks complete credit/actor evidence. Those maps remain in display statistics with null v3 Rating. Map/season/career JSON carries Rating coverage; UI shows42of82rounds/4of7maps. This restricted coverage is deliberate, not a silent use of incomplete objective inputs. No UAH training/tuning. V2 remains selectable, with exact old map/season/career Rating reproduction independently verified.

### V3 development, formula and final gate

Prospective plan3a8c3e5, fixed alpha1, four declared arms,988clean player-map observations/99maps/10whole-event folds. Verified1062rounds/7447positive event offsets; old clock sort reordered125rounds. Single triangular clutch-size term X(X+1)/2, not five per-size coefficients. Development MAE0.03031724, RMSE0.04098171, medianAE0.02238762, maxAE0.17531172,80.9717%within.05; native count gain7.0068%,9of10event wins. Native linear79.9595% fails80%; sparse1v4/5 and event heterogeneity remain limitations.

Exact full-precision standardized runtime: r6stats/stats/rating_v3.py, identical to research/v3-native-order-candidate.json. Raw formula below is descriptive/rounded; calculations use full precision. Rates divide by eligible rounds:

`Rating = 0.073737145 + 0.589345247 KPR - 0.172399408 TK rate + 0.220247961 extra MK rate + 0.153146792 native finisher opening differential rate + 0.245261453 triangular clutch rate + 0.459180620 KOST + 0.488175540 survival + 0.096126098 legacy trade differential rate + 0.450200607 objective rate`.

Genuine untouched final: APAC NorthStage1 2026, official505/phase15000, SiegeGG110. All28group archives reserved before targets;17whole maps refused,110clean rows/11maps/8rosters/22objective-positive. Independent profile/IGN/public-ID aliases resolved before targets. Freeze e05dfc4 committed clean before ANYtarget access; model/rows/inputs/binaries/hashes sealed. Evaluated ONCE; event now permanently consumed.

Unchanged final gate:>=100rows/10maps/8rosters/10objective-positive; MAE<=.035,>=10%MAE improvement vs exact original v2,>=80%within.05, RMSE no worse, maxAE<=.15, objective-positive and credit-affected subgroup MAE<=.05 when n>=10. **All gates PASS.**

| Final metric | V3 | Exact original v2 |
| --- | ---: | ---: |
| MAE | 0.030359332 | 0.060586453 |
| RMSE | 0.040205825 | 0.086468027 |
| Median AE | 0.021574044 | See preserved final report |
| Maximum AE | 0.106829999 | 0.397602318 |
| Within .05 | 81.8182% | See preserved final report |

Full threshold/subgroup/error data: research/output/v3-native-final-apac1-result.md. Original CNL, APAC NStage2 and South AmericaStage2 FAIL results remain permanent; no regrade or gate weakening. Frozen candidate's historical qualification-status string is retained as an immutable pre-final artifact; the later one-shot PASS and runtime/live checkpoints establish deployment status.

### Verification, backups and final checkpoint

Runtime/research parity:240tracked round/map/season/career comparisons,maxdifference0; all988consumed development predictor rows also checked in the new parity test without target regrading.543Python tests passed,1optional replay smoke skipped,6subtests; allGo/Y11 tests and go vet pass; public/admin builds pass. Exact historical v2 reproduction passes20documents (only methodology clarification differs). Post-apply source/table/archive/public/privacy guard passes. No parser/action-start code or old v2 coefficients/snapshots changed; default remains v3 while pure historical display calculations retain explicit v2 semantics.

Current guard: `.venv/Scripts/python.exe research/verify_native_v3_checkpoint.py`. Older checkpoint source/public hashes intentionally describe older deployments; do NOT overwrite/rebase them or rerun old migration/fit/evaluation jobs. Private verified backup: data/research/native-v3-deployment-20261007/before.sqlite, before-settings.json, before-public. Stop admin, restore these to data/r6stats.sqlite, config/settings.json, web/public/data for local rollback; raw archives stay intact. V3 adds only a private hash-bound core-occurrence sidecar and active default setting; no historical row rewrite. Stored recalculation/export does not reparse replays, and changed normalized hashes invalidate stale objective evidence automatically.

Remaining FUTURE work: larger independent validation events, rare clutch-size evidence, precise credited victim/opening/trade semantics, incomplete Chalet participation, unsupported objective compatibility under separate approval, and optional operator-relative research only after reliable operators. No new research, Rating version, UI redesign, multi-team or bonus-health work begins in this run. The authorized goal is complete; stop here.

## Historical: passing v3 applied and locally verified; publish/live verification next - 2026-10-07

siege_style_v3 is implemented EXACTLY from the frozen standardized native_triangular_size candidate and selected as the local/new-install default. Current seven maps/82 rounds retain every historical display statistic, credited source coverage, raw event/operator/objective/metadata/identity row and immutable v2 snapshot. Four whole maps/42 rounds are eligible for v3; original Border/Kafe lack complete core objective inventory and Chalet lacks complete credited participation. They remain historical display maps with null v3 Rating. No reparse, operator boundary, research refit or v2 coefficient change.

Verified private backup and reviewed projection: data/research/native-v3-deployment-20261007. Runtime/research parity on tracked rounds/maps/season/career:240comparisons,maxdifference0. Exact v2 reproduction passes all20public documents except methodology clarification. Source/sidecar/default/export guard research/verify_native_v3_checkpoint.py passes; all7archives Healthy,20public JSON validated. Python543passed,1optional skip,6subtests; Go all/Y11 tests and vet pass; public/admin builds pass. Existing React design unchanged; only v3 formula, choice and coverage text/tooltips added.

Actual quoted Start NECC Admin.cmd restarted old15472 process; current server17672 uses repository .venv Python, repository r6stats/parser/admin files. Browser automatically opened. Live local API returns siege_style_v3; headless Edge admin Settings and built public Lgon/methodology pages render correct coverage/Rating with zero page errors. Private screenshot/log evidence retained.

NEXT ACTION: commit reviewed v3 implementation/public data, push main, await existing Pages workflow success, verify all20live JSON against committed LF bytes and all5player season/career pages plus methodology, preserve live evidence/final clean checkpoint, THEN STOP. All publication authorized; no more model work or unrelated features. Frozen APAC Stage1 PASS and earlier CNL/APAC/SAL FAIL results stay permanent.

## Current: frozen APAC North Stage1 final PASS; runtime deployment next - 2026-10-07

Freeze e05dfc4 was committed before any Rating targets. The sole evaluation passed every unchanged gate: 110 clean rows/11 maps/8 rosters, v3 MAE0.03035933, RMSE0.04020582, medianAE0.02157404, maxAE0.10683000, 81.8182% within .05. Exact original v2 MAE0.06058645, RMSE0.08646803. All subgroup gates pass. The event is consumed; never rerun evaluation, refit the qualified model, or change gates. Immutable private result: data/research/v3-native-final-apac-n-stage1/one-shot-result.json. Public report: research/output/v3-native-final-apac1-result.md.

NEXT ACTION: implement EXACT research/v3-native-order-candidate.json standardized model as siege_style_v3; validate native finisher chronology and complete credited/core objective whole-map inputs. Current UAH supported evidence is 4 maps/42 rounds; preserve all 7 maps/82 display rounds and immutable v2 snapshots. Read-only runtime/research parity and migration preview, backups, full tests/Go/vet/both web builds/privacy, then authorized default switch, commit/push/Pages/live verification. Do not stop at another checkpoint; do not retune or open another holdout. Stop after validated v3 is live.

## Current: native-order candidate qualified; APAC N Stage1 targets unopened - 2026-10-07

Native-order study was prospectively committed at3a8c3e5 and fitted ONCE. All988rows/99maps/10whole-event folds: native triangular-size arm MAE0.03031724,RMSE0.04098171,medianAE0.02238762,maxAE0.17531172,80.9717%within.05. Exact frozen original v2 MAE0.05366132/59.3117%within.05. Triangular arm improves MAE7.0068% versus native count and wins9/10events; objective-positive233rowsMAE0.03118657 and kill-credit-affected303rowsMAE0.02884043. Native linear arm79.9595%within.05 FAILS80%; rounded display must not imply a pass. Single triangular X(X+1)/2 clutch coefficient, no per-size fit, no arbitrary coefficient search. Sparse1v4/5 support and event heterogeneity remain explicit. Original CNL FAIL unchanged. See research/output/v3-native-order-development.md and research/v3-native-order-candidate.json.

New genuinely untouched Rating event: official505/phase15000, SiegeGG110, APAC NorthStage1(group BO1). Distinct from consumed AsiaStage1 and APAC NorthStage2. All28group archives prospectively reserved using schedules; playoffs stay reserved outside this fixed snapshot. Initial small sample proved strict older-build refusals; June26sample8142 then proved the complete supported pipeline. All28now have terminal decisions:110clean rows/11maps/8rosters/22objective-positive.17maps refused by supported counter/core actor/identity gates. Do NOT expand old objective compatibility. Stable UUID histories or previously sealed exact profile/IGN/public-ID bindings independently resolve Demic164,Nina666,OKOMESSH; no digit stripping, target totals or remaining-player aliases. Earlier v1/v2 refusals are retained alongside v3 prelabel records. All caches private/ignored, no SQLite/public/default change.

NEXT ACTION: commit candidate, protocol, source/tests, aliases and complete prelabel report; ensure clean tree. Run `research/v3_apac1_final.py freeze`, commit the resulting public row/hash freeze, ensure clean tree, then `targets` and `evaluate` ONCE. The final gate remains100rows/10maps/8rosters/10objective-positive,MAE<=.035,>=10%improvement versus exact v2,>=80%within.05,RMSEno worse,maxAE<=.15,subgroupMAE<=.05. No APAC NStage1 Rating values opened yet. Passing candidate requires runtime parity/supported UAH input coverage and authorized deployment; failure must be permanent and development only. No production v3 yet.

## Historical: CNL final FAILED; native-order development preregistered - 2026-10-07

Permanent one-shot CNL result committed at `1a7d9f0`: 300 clean rows /30 maps /8 rosters. Candidate MAE0.03524430, RMSE0.05088617,75.3333%within.05,maxAE0.35226602. Exact v2 MAE0.06421721,51.6667%within.05. MAE,80% and maximum-error gates FAIL. No regrade, gate change, v3 implementation or deployment. All CNLStage1 is now consumed; it may enter DEVELOPMENT only. See research/output/v3-credited-final-cnl-result.md. Corrected counts remain live at b1023d4; v2 remains default.

Post-final cached diagnostics account for percentage truncation: survival agrees300/300; KOST agrees216/300 (84 actual count differences). Native serialized finisher order independently verifies all2252positive elimination offsets on320CNL rounds. Remaining-clock sorting reordered53rounds; native chronology fixes seven of nine public clutch-log discrepancies and improves opening-death agreement263->297/300 and finisher opening-kill agreement253->275/300. Two clutch contradictions and credited opening ownership remain unresolved. No inferred DBNO/downer or trade timing. See research/output/v3-credited-cnl-order-diagnostics.md. Original raw tolerance audit remains preserved; its percentage disagreement counts include display truncation and are not all semantic errors.

Separate broader native-order development cohort is sealed privately:988rows/99maps/10events,1062rounds/7447positive verified event offsets,125legacy reordered rounds. No source parsing/downloading repeated. All original clean rows retained; source/identity/event parity and complete credited/core objective gates hold. Native clutch support82/40/11/3/1 by1v1..1v5 (137wins). Production normalized data, original v2 inputs/operators/objectives and public JSON unchanged. Six focused chronology/model safeguards pass.

NEXT ACTION: after committing the prospective plan/code/tests and ensuring a clean tree, run `research/v3_native_order_fit.py` ONCE. Fixed alpha1, ten whole-event folds; legacy count control, native count, native linear X, native triangular X(X+1)/2. One clutch coefficient per arm, no per-size fit or weight search. Old small-cohort linear failures remain rejected. New qualification requires >=80%within.05, maxAE<=.20, subgroup limits, and size arms must improve MAE>=5% over native count with >=6 event wins. Do not consume another final if no arm qualifies. Any qualified arm needs a genuinely new untouched Rating event and the unchanged final gates including80%/MAE<=.035/maxAE<=.15. No CNL rerun.

## Historical: fresh CNL final sealed, Rating targets unopened - 2026-10-07

All27selected CNLStage1BO3 archives have terminal prelabel decisions:60scheduled completed maps,300clean rows on30maps,8distinct rosters,86objective-positive rows. Stronger independent primary objective totals audit changes no eligibility. Header/identity/counter/whole-map objective safeguards remain strict. Source8754 ZIP has inconsistent local/central filenames: Python and7-Zip25.01 refuse it; independent first/last65536-byte HTTP ranges exactly match the cached archive. All3affected maps are retained as refusals. Source8734 has a missing completed map and byte-identical duplicate archive copies, recorded explicitly. Other participation/alias/counter refusals remain.

Candidate/model/gates, exact e7c2 v2 parser baseline, all300row identities/hashes, complete private feature seal, source commit3aee9ea(clean), every selected archive/input/binary hash are frozen in research/v3-credited-final-cnl-freeze.json. Full replay-derived round features remain ignored/private. Report: research/output/v3-credited-final-cnl-prelabel.md. No player-stat targets fetched or Rating values opened yet.

NEXT ACTION: from committed clean tree, `research/v3_cnl_final.py targets` stages sealed raw target bytes without projecting Rating, then `research/v3_cnl_final.py evaluate` performs the final ONCE. Preserve any failure permanently; no gate changes, regrading, refitting or selective row replacement. If it passes, implement exact v3 parity and supported input eligibility, preserve displayed stats/v2, then authorized publish/live verification.

Read-only UAH candidate round/aggregate parity is within1e-12 for all5players/82rounds. Independent cached core input audit currently supports4whole maps/42rounds; original Border has a historical opponent disable lacking complete core evidence, KafeR09 an unverified historical plant, Chalet incomplete credited/actor evidence. Preserve displayed history; do not silently use unsupported objective inputs for v3. No DB/replay reparse/default/public-data change during this phase. Python523passed/1optional skip/6subtests; fullGo/Y11 tests andvet pass. Current seven-map production guard passes.

## Corrected-count v3 development qualified; final targets unopened - 2026-10-06

One predeclared experiment on688clean rows/69maps/9whole-event folds is complete; never refit this study. Corrected nine-family core-objective candidate: MAE0.03103384, RMSE0.04287459,81.1047%within.05; exact original frozen v2 reference MAE0.04905846/62.6453%within.05. Corrected eight-family misses80% (75%). Coefficients, event drift, all residual/subgroup metrics and exact model are preserved in research/output/v3-credited-event-development.md, research/v3-credited-candidate.json and the private immutable experiment.

NEXT ACTION: metadata-only untouched-event qualification, beginning CNL2026Stage1(all27currently linked BO3 archives, earliest small pipeline proof). No new final Rating values have been opened. ChinaStage2 is excluded because earlier searches exposed Rating snippets; OCE/ASIAStage2 currently each fall below ten structurally usable maps. Existing80%final gate plus100clean rows/10maps/8rosters/10objective-positive rows/MAE<=.035/maxAE<=.15 remain unchanged. Freeze candidate, complete eligible rows, input hashes, clean source before one-shot final. No v3 runtime/default/deployment change yet.

## Corrected counts LIVE; broad v3 dataset derived - 2026-10-06

Production commit `b1023d4` pushed to main; GitHub Pages run37571010366 completed successfully. All20live JSON documents exactly match committed LF bytes and the current decoded Windows export (CRLF differences recorded explicitly). Current objectives and all five v2 Ratings remain unchanged;70credited/12legacy rounds are visible per player. Guard: research/verify_production_kill_checkpoint.py. Live evidence: research/production-kill-live-checkpoint.json.

Separate corrected professional inventory now79maps/790player-map rows,688clean on69maps across9events. Uses existing470objective-derived development rows plus all32consumed APAC/SAL maps; old decisions/final results remain immutable. Ten whole maps fail complete counter/objective gates; two additional alias rows stay excluded. Exact credited K/D resolves old finisher-based mismatches; no alias is chosen from totals. All-nil LAN records use an explicit exact ten-header-UID/name/team adapter, never known-profile substitution. No new Rating final target is opened.

Predeclared development plan research/v3-credited-development-plan.json: whole-event folds, fixed alpha1, exact original v2 reference, frozen weights/corrected-input control, corrected8/9-family candidates. No new model fit yet. NEXT ACTION: fit that deliberate broad study once, report all event/subgroup/coefficient/residual metrics, and require the declared qualification before selecting an untouched final. Prior80%within.05 gate remains; passing final must be frozen from clean source before targets. UAH is sanity only.

Additional ten-source declared transitive-component audit extends UID routes through depth4:49,332uniquely rooted fields,0incoming numeric target refs,984shared/1,115unknown refusals. Nina/OSAdinho and all eight missing kind5 remain unresolved; no generic credited-victim association is promoted. See research/output/credited-transitive-owned-controls.md. Production/event policies are unchanged from b1023d4.

## Authorized credited-count migration ? 2026-10-06

Recovered user import HEAD `7b2bb57`: seven maps /82 rounds. Verified private backup and new current-state audit preserve the earlier five-map research seals. Six whole maps /70 rounds use stable_uid_scoreboard_delta_v1; all12 Chalet rounds remain legacy because the rehost has nine participants. Raw normalized/elimination/objective records, identities, metadata, operators, archives and original five v2 snapshots are unchanged. Two new-map v2 snapshots were added without replacing existing snapshots.

Current season kills: Lgon81, OhWowJay91, AzoozNewzz57, Tallman3.14 37, DinoFireKing36. Deaths unchanged; all five v2 Ratings exactly unchanged. Dino KOST51->50 is the supported credited Kill-flag correction; all other KOST unchanged. Public map/season/career JSON includes source coverage, finisher kills and multikill sizes. HS retains its finisher denominator; opening/trade/pivot/untraded/clutch event semantics remain legacy. See research/output/credited-production-readiness-20261006.md.

509 Python passed, one optional smoke skipped, six subtests; Go/Y11 tests and go vet passed; public/admin builds passed. Privacy validation and whole-table/public-field comparison pass. Interrupted74-source finisher-refrag audit is preserved:225candidate pairs,73within/99beyond/1straddling/52unresolved,3determinate coarse-window disagreements. No credited identity or precise time promotion.

Publishing is explicitly authorized by the latest task; local corrected data is applied, push/live verification pending. NEXT ACTION: commit and publish validated corrected counts, verify live JSON, then derive a separately versioned corrected-input professional development dataset with whole-event folds. Preserve exact v2 and both failed v3 finals; never rerun/regrade them. Nina/OSAdinho/missing kind5 and event ownership/time remain unresolved; independent READY features have migrated without speculative links. Bonus-health and older objective compatibility remain excluded. No new v3 is fitted/deployed yet. A future candidate must freeze on clean source before new final Rating targets; prior80%within.05 gate cannot be lowered.

## Finisher-refrag clock bands before cached job - 2026-10-03

HEAD `5406610`. Clock case milestone committed; chained preservation guard running (large cached-input hashes), prior full guard passed at016e51e. Command `.venv/Scripts/python.exe research/credited_refrag_clock_controls.py`: fixed74prefix-audited sources, exact original filtered finish identities/order, actual final deaths update alive; duplicates retained/notrecounted, teamkill/self/unnamed death never manufacture opposing kills. Finisher-identity refrag pattern compared with raw same-region span bounds at8000observed countdown units and the old8scoarse numeric expression. No alternate-window search, credited owner, exact elapsed time or production trade policy.

NEXT: inspect all raw-window disagreements/uncertain phase and end boundaries; retain evidence, then direct missing-actor/recovery source research. No target/model/Rating experiment, default helper, SQL/public/archive write or publishing.

## Latest checkpoint: clock-annotated case timelines - 2026-10-03

Base `016e51e`.10fixed cached cases, exact counter/header UID-profile-name-team identity. Reviewed Stk/resetz raw3->raw4 brackets4330-4397/821-889raw units; Kheyze counter increment after his own elimination, beforeStkraw4; Neskin counter before resetzraw4. No event timestamp/downer/credited-victim inference. Missing targets:Aokayu1522-1589,stemp0-67,xSexyCake298-397; fiveothers zero/terminal/missing. Original failedv1counter-id harness source/reservation preserved separately. See research/output/credited-clock-case-timelines.md.

493Pythonpassed,1optional skip,6subtests; prior Go/Y11/vet pass, Go unchanged after. Safe guard `.venv/Scripts/python.exe research/verify_clock_case_checkpoint.py`. NEXT ACTION: same-region finisher-refrag raw-window audit on fixed74consumed sources, no credited/time policy promotion; then direct missing actor/recovery source evidence. Existing broad counter mismatch and every refusal preserved. No historical/default/SQL/archive/public/Rating changes or publishing.

## Case harness schema correction before v2 cached job - 2026-10-03

HEAD `016e51e`. Original case harness failed before any result: counter players use uid rather than header id. Original reservation, failure and exact source retained privately in data/research/credited-clock-case-timelines/. V2 uses exact counter/header UID-profile-name-team equality, unchanged raw-span hypothesis, separately named data/research/credited-clock-case-timelines-v2/. Command `.venv/Scripts/python.exe research/credited_clock_case_timelines.py`. No old reservation overwrite or statistics modification. NEXT remains known live body/counter/finish timeline, then bounded finisher-refrag comparisons.

## Clock-annotated case timelines before cached job - 2026-10-03

HEAD `016e51e`, broad prefix result/limits sealed/clean. Command `.venv/Scripts/python.exe research/credited_clock_case_timelines.py`: fixed reviewed Stk/resetz plus8missing-body targets, existing cached UID/body/counter/history and new clock-prefix outputs only. Annotate exact physical live samples with raw before/after clocks; separately retain late history items, never time them at copy offsets. Mathematical raw countdown span bounds require both sides positive/sameprovider/sameregion; no seconds/interpolation, generic DBNO/downer, credited victim or nearest-counter assignment.

NEXT: inspect raw3->raw4 brackets and known counter/down/finish order, preserve all unsupported boundaries; then same-region finisher-refrag interval audit without credit/time policy promotion. No default/stat/SQL/public/Rating change or publishing.

## Latest checkpoint: same-prefix countdown controls - 2026-10-03

Base `4552019`. All74consumed sources pass oneprovider/width4/action-field/unchangedfeed gates.390086finer samples,15273sameentity/samerecord integer/finer pairs,15273floor1000agreements,0scale failures/ambiguous pairs. Serialized regions retain increases/positive->0, no elapsed clock.506eliminations:454positive same-region brackets,33missing side,18zero/terminal,1legacyoffset0. See research/output/credited-clock-prefix-controls.md.

490Pythonpassed,1optional skip,6subtests; full Go/Y11/vet pass. Safe guard `.venv/Scripts/python.exe research/verify_clock_prefix_checkpoint.py`. NEXT ACTION: reviewed split-credit/down/finish/counter timelines annotated with explicit raw clock brackets; same-region finisher-refrag window audit with no credited identity/time promotion, then generic cause/recovery controls. Bankzero overtime and52nonpositive/missing/terminal limits preserved. No Rating fit, SQL/archive/public/default changes or publishing.

## Same-prefix clock controls before cached job - 2026-10-03

HEAD `4552019`, explicit clock study sealed/clean; prior guard passed. New opt-in Go `clock-prefix-inspect` retains integer countdown0xC9EF071F and finer0x6C463718 fields in the exact same entity/property prefix; no cross-record pairing. Three focused Go tests pass, including separate records/duplicates/unknown-width stops. Current hypothesis: explicit joint updates agree with floor(raw/1000); raw increases/positive->0 partition serialized regions, not elapsed time.

Commands `.venv/Scripts/python.exe research/credited_clock_prefix_controls.py --limit 6`, then `--limit 74` if structural controls hold. Fixed original74consumed buffers across4builds; selection/source/binary reserved before collection. Exact action-field end and original feedback parity required; retain mismatches, multiple providers, unknown widths, absent clock sides and zero/terminal/reset brackets. No interpolation, historyscalar rate, credited-victim join or production promotion. NEXT: inspect same-prefix results/phase boundaries; if warranted retain broader cohort without clock-unit tuning, then generic cause/recovery controls. No historical/public/Rating change.

## Latest checkpoint: explicit countdown field evidence - 2026-10-03

Base `1c4568b`. Fixed6consumed sources across4builds expose37990width4samples of0x6C463718, oneentity perreplay; field decreases/countdown resets, contradicting external elapsed-since-start hypothesis. All1365coarse countdown observations match floor(next raw property/1000), descriptive development evidence only. Metadata has starttime but no named FPS/rate field. Lairlast event missingnext clock and MichiganBorderlast positive->terminal0 bracket retained. Bankplant overtime remains unmeasured. See research/output/credited-clock-field-controls.md.

487Pythonpassed,1optional skip,6subtests; full Go/Y11/vet pass. Safe guard `.venv/Scripts/python.exe research/verify_clock_field_checkpoint.py`. NEXT ACTION: same-prefix integer/finer countdown relationship, serialized epoch/zero/terminal controls, then broader fixed consumed controls if warranted. No elapsed-time interpolation/history-scalar rate, credited-victim join, live migration, Rating study or publishing. New commands/binaries remain opt-in; original SQL/archive/public/v2 state unchanged.

## Clock scale inventory before cached job - 2026-10-03

HEAD `1c4568b`. Fixed6raw source outputs complete. Each has one0x6C463718width4provider,37990updates total; near-all decrease. External elapsed-since-start interpretation is contradicted. Raw header has starttime wallclock and no FPS/tick-rate field. Inspection found next raw property floor(value/1000) equals all1365coarse integer countdown observations. This is descriptive consumed evidence, not new untouched validation.

Command `.venv/Scripts/python.exe research/credited_clock_scale_inventory.py` records the observed floor correspondence, raw increases, per-source step distributions and terminal/reset hazards without interpolating. LairR06last event lacks a next clock; MichiganBorderR03last event brackets positive remaining versus terminal0. NEXT: same-prefix countdown/property framing and independent epochs, zero/overtime/plant transitions; preserve external hypothesis failures and all missing sides. No Rating fit, default clock/action logic, historical/public change.

## Explicit clock fields before cached job - 2026-10-03

HEAD `1c4568b`, owned-prefix milestone sealed/clean. New separate Go `cmd/clock-field-inspect` inventories framed raw properties0x6C463718/0xA374F4B6, exact integer countdown listener markers, and all plain modern header key/value fields without default parsing. External field hypotheses cached from wnc-replay/replay-tool commitdd535f6499069c8268841fda76c68a04b19ba104, not adopted. Four focused Go tests pass.

Commands `.venv/Scripts/python.exe research/credited_clock_field_controls.py --limit 2`, then `--limit 6`. Fixed original consumed6controls across4builds, cached buffers and exact original headers only. Check raw widths/ranges/decreases, exact action countdown, metadata, and structural before/after brackets. No elapsed-second conversion, scalar rate, interpolation, byte-distance time or credited-victim join. NEXT: inspect explicit clock field ranges and phase/reset/overtime controls, preserve failed external hypotheses; then recovery/cause boundaries. No Rating or historical/public change.

## Latest checkpoint: UID-owned prefix controls - 2026-10-03

Base `52a9cfe`. Ten fixed sources (reviewed Stk/resetz plus eight missing kind5 targets) reproduce10/10exact UID/body/raw3 offsets,222context fields/109prefixes. No incoming exact numeric target references in parsed owned components, including reviewed cases; no actor inferred. Six missing targets serialize raw4 within650bytes after raw3, without elapsed-time meaning. Unknown/unowned/array sources remain uninspected. See research/output/credited-owned-property-controls.md.

484Pythonpassed,1optional skip,6subtests; full Go/Y11/vet pass. Safe guard `.venv/Scripts/python.exe research/verify_owned_property_checkpoint.py`. NEXT ACTION: explicit clock/recording metadata controls on fixed consumed sources, then generic cause/recovery boundary controls. Existing counter mismatch, first-reference causal roles and credited-victim joins stay unresolved. No historical kill migration, Rating fit, default parser/stat/SQLite/public change or publication.

## UID-owned property controls before cached job - 2026-10-03

HEAD `52a9cfe`, previous lifecycle and production guard passed. New separate Go `cmd/owned-property-inspect` examines scalar/text prefixes and incremental temporal UID-owner routes, stops unknown widths, and reports exact numeric UID/owner-entity matches as candidates only. Seven focused Go tests passed, including equivalence to existing strict route binding. Default reader/actor/stat/parser paths unchanged.

Commands `.venv/Scripts/python.exe research/credited_owned_property_controls.py --limit 2`, then `--limit 10`. Fixed two independently reviewed split-credit targets (Stk/resetz) plus all eight missing kind5 targets, existing sealed buffers only; reservation before results. Target context [raw3-4096,raw3+8192) is byte context, not time; scan exact numeric reference fields across post-action owned prefixes. No unknown-array skip, nearest-counter join, actor assignment or complete-record claim. NEXT: inspect raw unknowns and any candidate references, preserve failures; then explicit clock/generic cause controls. No historical kill migration, Rating experiment or publication.

## Latest checkpoint: cached history/body lifecycle controls - 2026-10-03

Base `ccfc1bf`. All74consumed sources pass UID/profile/name/team/action/owner/body-route checks. Candidate intervals144/145 match; SAL8583R01 pino kind5 and final share scalar6154, body view has only raw4, so a universal raw3 requirement is invalid. Eight raw3 observations lack any kind5 target entry; no actor inferred. See research/output/credited-history-lifecycle-controls.md. Existing counter mismatch and all prior refusals unchanged.

480 Python passed,1 optional skipped,6 subtests; prior Go/Y11/vet pass, Go unchanged afterward. Safe guard `.venv/Scripts/python.exe research/verify_history_lifecycle_checkpoint.py`. NEXT ACTION: inspect exact UID-owned property frames/source references for eight missing targets, compare reviewed Kheyze/Neskin split cases; Go evidence preferred, no nearest-counter/actor inference. Then explicit clock/generic cause controls; no Rating fit, historical kill migration or publication.

## Latest checkpoint: verified opt-in Go replay interface - 2026-10-03

Base `849f740`. New wrapper retains a local buffer reference while normal Read resolves the header; default release/callbacks unchanged. Six cached controls across four builds and both actual inputs (SAL8583R02, UAHFortressR04) now match saved typed evidence exactly. Source/binary/results separately sealed; original two v1 failures and74cached results preserved. See research/output/credited-history-go-interface-v2.md. No default import/stat/SQL/public wiring.

Full Go tests including Y11/eight new history tests and vet pass; 477 Python passed,1 optional skipped,6 subtests, web sources unchanged. Safe guard `.venv/Scripts/python.exe research/verify_history_go_interface_checkpoint.py`. NEXT ACTION: cached74source Go/body lifecycle coverage audit, retain missing raw3 actor records and every quality refusal; then fixed gadget/source/recovery and explicit clock controls. No credited migration, Rating research or publication. Do not rerun v1 reservations against revised current source.

## Latest checkpoint: opt-in Go trial and integration failure - 2026-10-03

Base `3caf344`. Go typed structural reader matches all 74 cached buffers. Actual `--replay` on SAL8583R02 and UAHFortressR04 fails because `Reader.Read()` releases `r.b` before inspection. Both failures preserved; source snapshots retain historical hashes in research/source-checkpoints/go-history-v1/. See research/output/credited-history-go-reader-controls.md. No default wiring or credited migration.

477 Python passed,1 optional skipped,6 subtests; full Go tests/vet pass. Safe guard `.venv/Scripts/python.exe research/verify_history_go_checkpoint.py` checks historical trial snapshots/binary/evidence plus all prior baseline/studies. NEXT ACTION: opt-in wrapper retains a local buffer reference during normal Read; default release unchanged. Build separate v2 binary, reserve new actual input and buffer controls; keep v1 failures immutable. Then missing source/lifecycle/clock research. No Rating experiment, SQLite/archive/public/default binary modification or publication.

## Latest checkpoint: typed cumulative history - 2026-10-03

Base `9b491ac`. All 74 consumed histories complete, 416 bounded containers, 506 original elimination identity/weapon/headshot/sequence matches. Raw kinds2/3 keep friendly-kill/unnamed-death controls separate; no credited policy or elapsed seconds assigned. Full cached body/identity audit confirms Aokayu raw3 has no kind5 target entry; Nina/OSAdinho credited-victim relation stays unresolved. See research/output/credited-history-typed-layout-controls.md. Earlier hypotheses/refusals unchanged.

474 Python passed,1 optional skipped,6 subtests; default Go/runtime/web unchanged. Safe guard `.venv/Scripts/python.exe research/verify_history_typed_checkpoint.py`. NEXT ACTION: separate opt-in Go structural reader, compare cached typed buffers; retain actor/clock uncertainty, then further fixed source/gadget/lifecycle controls. No historical kill migration, Rating experiment, public export or publication.

## Latest checkpoint: cumulative history framing - 2026-10-03

Base `33cb8f2`. Strict v2 tail1 variant retains initial six controls:27 complete/12 partial containers,3 complete histories; fixed68 cohort:353 complete/24 partial containers,56 complete histories. All unknowns preserved. Exact prefix/count+1 append inventory across74 consumed sources:173 single items, including kind10 width26 with opaque tails1/2 and kind3 width41. See research/output/credited-history-framing-controls.md. Counter mismatch and frozen broad hypothesis unchanged.

467 Python passed,1 optional skipped,6 subtests. Safe guard `.venv/Scripts/python.exe research/verify_history_framing_checkpoint.py`; protects additive evidence and all original baseline/studies. NEXT ACTION: additive structural variant with observed kind10 tails1/2, single-reference kind3 and separately hypothesized friendly kind2; exact count/bounds/prefix and independent feed parity required. Audit missing Aokayu down ownership, retain scalar/list order without seconds; no historical kill migration, default source, Rating research or publication.

## Latest checkpoint: frozen history development controls - 2026-10-03

Base6e18e5c. Fixed 68 consumed sources: 63 agreeing rounds, 1 mismatching round (Nina/OSAdinho), 4 quality refusals (2 ties, friendly-kill layout, unnamed death). 638/640 comparable player counters agree; all failures retained. See research/output/credited-history-development-controls.md. No new target/final evaluation, no tuning or production admission. Independent append bounds show opaque kind10 width26 in three professional/local controls; its role remains unknown. Original failed25-byte result preserved.

463 Python tests passed, 1 optional skipped, 6 subtests. Runtime/Go/web sources unchanged; original verification applies. Safe guard `.venv/Scripts/python.exe research/verify_history_development_checkpoint.py` preserves the new reservation/results/buffers and all authorized baseline/old studies. NEXT ACTION: separate bounded framing trial using declared item counts and exact prefixes; investigate mismatches and missing TK/Death item forms, preserve unknowns and scalar ties. No historical kill migration, export, Rating experiment or publication.

## Latest checkpoint: late event-history controls — 2026-10-03

Latest additive result after `80b45c4`: [credit hypothesis](../research/output/credited-history-credit-hypothesis.md) reconstructs60/60validated round counters on6consumed sources with0mismatches, retaining latest opposing kind5 until kind1 final elimination and clearing on kind7 recovery. This is development corroboration, not new official target agreements or production semantics. Ties/TK/self final-credit policies refuse; no elapsed seconds inferred. Opaque-item extension did not improve21complete/18partial framing outcomes.457Pythonpassed/1optional skip/6subtests; Go/vet unchanged pass. Current guards and all production state unchanged.

Safe latest verification: `.venv/Scripts/python.exe research/verify_credit_hypothesis_checkpoint.py`. NEXT ACTION: fixed68source consumed development controls (the previous native-boundary selection), frozen hypothesis/helpers before new results; incremental cache/dumps, retain all mismatches/quality refusals. No target/model/final reevaluation, no live credited migration/publication, no v3. Complete framing and independent causal/lifecycle/clock evidence remain required.

Count-only milestone `fa220a8` and published objective baseline remain unchanged. New [late-history discovery report](../research/output/credited-late-history-discovery.md): 6 fixed consumed rounds across 4 builds, 41 unique finisher events match identity/weapon/headshot/order; 18 candidate type-5 target raw-3 controls and 2 candidate type-7 active-state controls agree within independent feed bounds. First-reference downer/reviver roles remain pending. Both known plant-reset orders are preserved by opaque event scalars, but professional/local scalar magnitudes differ; no seconds or fixed rate assumed. Whole-container parsing remains partial: 21 complete containers, 18 unknown-item/trailing-data refusals. No event migration or readiness promotion.

Verification: 450 Python passed, 1 optional skipped, 6 subtests; Go tests/vet passed during this session and Go source remains unchanged. No shared runtime/export/web change, so production builds apply. Original sources/results/Rating snapshots, SQLite, archives and public JSON remain identical. Four new ignored sample dumps were produced for this new hypothesis, not an old pipeline rerun.

Safe recovery: `.venv/Scripts/python.exe research/verify_late_history_checkpoint.py`; new separate `research/credited-late-history-checkpoint.json` seals source/results/buffers and invokes the previous authorized guards. NEXT ACTION: characterize unknown late-history item layouts, preserve terminal and duplicate/replacement/truncation controls, independently validate type-5/7 actor roles and recovery lifecycle, then investigate explicit scalar clock/recording cadence/plant overtime semantics. A separate opt-in Go reader needs complete framing and broader validation before runtime promotion. No credited-victim association from totals/proximity, no v3 until semantics settled, no historical kill migration or publish authorized.

Before next cached job: milestone `80b45c4`, clean tree at commit. Hypothesis: an opaque kind10 has scalar plus one exact20-byte header reference; terminal unknown item can be preserved uninterpreted only when declared item count says exactly1remaining and it contains no later recognized candidate. Command `.venv/Scripts/python.exe research/credited_history_opaque_items.py`. Use bounded containers in the fixed6buffers; preserve the sealed partial result and every unknown byte, do not add objective/kill/life semantics. Refuse unknown middle entries, mismatched metadata and truncation. Structural consumption does not establish causal roles or seconds.

Opaque-item hypothesis did not improve complete-container counts; the single-reference prefix leaves additional trailing bytes and unknown middle items. All21complete/18partial outcomes retained, no unknown bytes skipped. Three focused tests pass. Before next cached job, base80b45c4: command `.venv/Scripts/python.exe research/credited_late_credit_hypothesis.py`. Explicit development hypothesis only: latest opposing kind5 first-UID candidate survives to kind1 final elimination unless kind7 recovery clears it. Compare reconstructed round counts to all60independently validated player-round counters in these6consumed sources; preserve mismatches/refusals. No seconds, trade/opening production definition, Rating, source promotion or historical data write. Competing down evidence in BankR07 (cyber down before Bassetto's first final death) is a separate useful opening control, not a universal policy from aggregate labels.

## Body lifecycle controls before cached job - 2026-10-03

HEAD `ccfc1bf`, successful Go interface and historical failures sealed. Commands `.venv/Scripts/python.exe research/credited_history_lifecycle_controls.py --limit 8`, then `--limit 74`; Go raw history plus existing cached state/body UID routes only, no parsing/target/model job. Hypothesis: kind5 targets corroborate raw3, kind7 targets active raw0/2 within independently matched final-feed bounds. Preserve zero-offset anchors, incomplete state routes/header identities and every unmatched interval as unresolved; inventory raw3 players with no kind5 target without assigning an actor. NEXT: inspect all missing life entries and source/operator context, then further fixed cause/clock controls. No generic DBNO enum/actor/elapsed clock or stat migration.

## Retained-buffer v2 interface before new job - 2026-10-03

HEAD `849f740`, original Go trial/failures/snapshots sealed. Opt-in wrapper retains a local decompressed buffer reference before normal Read, then inspects it with final header; default Read release/other parser behavior unchanged. Released-method call now explains the stage limitation. New separately named `.local-tools/bin/siege-history-inspect-v2.exe`; full Go tests/vet pass, including2new stage/invalid-input tests. Before new job `.venv/Scripts/python.exe research/credited_history_go_interface_v2.py`: reserve current source/binary and6fixed cached buffers plus the2original real replay controls, require exact evidence parity. Old failures/binary/results immutable; no old pipeline or evaluation rerun. NEXT: verify actual input parity, seal successful interface separately, continue missing source/lifecycle/clock evidence; no default credited/stat/SQL/public change.

## Explicit Go replay interface control before job - 2026-10-03

HEAD `3caf344`. All74cached Go sources match all typed fields/list ordinals/containers/header identities/null clocks; full Go tests and vet pass. Before job `.venv/Scripts/python.exe research/credited_history_go_replay_controls.py`: two fixed new-interface controls (SAL8583R02, UAHFortressR04), explicit `--replay` must reproduce cached `--buffer` evidence. This validates the newly added Go Reader method on actual input, not an old research pipeline or final rerun. No SQLite/archive/source/stat/public modification. NEXT: preserve any discrepancy, seal opt-in Go evidence, then additional fixed missing-source/lifecycle/clock controls; no credited migration/Rating work yet.

## Opt-in Go reader controls before cached job - 2026-10-03

HEAD `3caf344`; default Go Reader/feedback/operator/objective/stat paths unchanged. New explicit `InspectEventHistoryBuffer` and `Reader.InspectEventHistory`, separate `cmd/history-inspect`; exact count/bounds/header UID/icon/alliance/prefix, retains unknowns, list ties, opaque fields and null elapsed seconds. Six Go evidence tests pass. Kill-free rounds without a two-reference anchor remain an explicit refusal. Before new binary job, build only `.local-tools/bin/siege-history-inspect.exe`, then `.venv/Scripts/python.exe research/credited_history_go_controls.py --limit 6`, extend `--limit 74`. Cached buffers/headers only; reserve source/binary and fixed selection before results. NEXT: investigate every Go/Python structural discrepancy without tuning old evidence; then source/lifecycle/clock controls, no production credited joins or Rating experiments.

## Missing-actor audit before cached job - 2026-10-03

HEAD `9b491ac`. Structural-v3 all74complete histories,416complete containers,506feed eliminations matched; no unknown skipped or default source promoted. Before cached job `.venv/Scripts/python.exe research/credited_history_missing_actor_audit.py`: exact APAC8161R14 mismatch, cached state/body UID routes and original counters only. Hypothesis: typed kind5 target inventory may omit an observed raw3 player; no actor from compensating counts. NEXT: retain full numeric identities, chronology without elapsed time and missing relationships; separate opt-in Go structural reader can provide this evidence without duplicating low-level parsing in the Python tracker. No credited event/Rating/historical SQL/public change.

## Structural v3 trial before cached job - 2026-10-03

HEAD `9b491ac`, previous framing variants sealed and committed. Commands `.venv/Scripts/python.exe research/credited_history_framing_v3.py --cohort six`, then `--cohort 68`. Prediction frozen before results: kind10 observed opaque tails1/2 width26; kind3 single reference width41 with unresolved cause/credit; kind2 prospective kill-shaped two-reference width62, requires independent friendly-kill control. Walk exact declared count/bytes, no unknown skipping; compare explicit list order to original filtered feedback sequence, retaining legacy zero-offset limitation. Five focused tests pass after a syntax fix before reservation/collection. NEXT: retain all refusals, verify cumulative copy prefixes/field parity; audit missing Aokayu ownership and typed cause boundaries. No historical normalization/stat/Rating/public change.

## Additional append inventory before cached job - 2026-10-03

HEAD `33cb8f2`. Framing-v2 kept its strict observed tail1 prediction: six controls27complete/12partial containers,3complete histories; broad68controls353complete/24partial containers,56complete histories. Unknown kind10 tail2 and kind3 remain refused. Before next job: `.venv/Scripts/python.exe research/credited_history_append_development.py`, all74fixed buffers/results cached only. Hypothesis: exact prefix/count+1 reveals additional single-item layouts/tails without guessed widths. Preserve v2 source/results and all refusals. NEXT: evaluate explicit boundaries, then additive structural variant; no actor/clock/rating/default changes.

## Framing trial before cached collection - 2026-10-03

HEAD `33cb8f2`; broad hypothesis and append observations now sealed separately. Command `.venv/Scripts/python.exe research/credited_history_framing_v2.py --cohort six`, followed by `--cohort 68`. Prediction: independently bounded kind10 has26bytes, exact header UID/icon/alliance plus observed opaque tail1. Four framing tests pass. Preserve original failed25-byte interpretation. Any unknown/truncated/trailing/mismatched identity item refuses complete history. Compare every cumulative copy's exact item-byte prefix; explicit list order can retain scalar ties without inventing a tie breaker. No actor role or clock unit promotion. NEXT: inspect all unknown layouts, cumulative replacements, and event-counter mismatches before any semantic/runtime extension.

## Frozen 68-source development extension - 2026-10-03

68-source job completed with immutable results; inspect `sample-68.json` and all mismatches/refusals. Before next cached job, HEAD6e18e5c: hypothesis that consecutive bounded cumulative containers with unchanged item-byte prefix and declared count increase1 give an exact new item's byte boundary. Command `.venv/Scripts/python.exe research/credited_history_append_inventory.py`; six sealed buffers only, no guessed widths or causal/clock meaning. NEXT: characterize independently bounded unknown item bytes, preserve the original incomplete framing and frozen broad hypothesis unchanged.

Base HEAD `6e18e5c`, clean before this extension. Hypothesis and helpers reserved before collection: `last_opponent_kind5_cleared_on_kind7_v1`, no tuning, exact finisher identity/weapon/headshot/order required before counter comparison. Fixed original native-boundary68source cohort; alternate SAL/APAC while preserving each cohort's original order, then remaining SAL. No targets, final evaluation, old pipeline or production changes.

Commands `.venv/Scripts/python.exe research/credited_late_history_development.py --limit 8`, then `--limit 68`. New hypothesis-specific decompressed buffers and immutable per-source results under ignored `data/research/credited-late-history-development/`; preserve every quality refusal and mismatch. Four harness tests pass. NEXT: inspect small sample persistence/refusals, extend incrementally, then audit every mismatch/refusal without altering the frozen hypothesis. Causal roles, complete history framing and elapsed clock units remain unresolved. Safe original guard `research/verify_credit_hypothesis_checkpoint.py`.

## Current credited-kill continuation: canonical round evidence and Stage A preview - 2026-10-03

Base HEAD `b6fffa260d725b09898bfdf4c88c10ea6b322a0d`; previous working tree was clean. All original guards pass. New additive, cached-only dataset:37maps/387rounds/3866player-rounds across4builds;382rounds have complete counters,35whole maps qualify. Native8156R03 remains a separately validated source, not silently admitted. Sources: `research/credited_round_dataset.py`; private `data/research/credited-round-dataset/dataset.json`. No download, replay parser run, fit or old evaluation repeated.

Chalet logical9-12: all9 observed participants have direct scoreboard routes, but Natedog.UMich is absent from both header and numeric UID inventory in every rehost round. No unknown tenth UID appears in that typed view. Classify as participant inventory gap after rehost, not absent tracked counters. Actual5v4 versus unrecorded participant remains unproven. Existing10-player validator and whole-map refusal stay unchanged. Diagnostic9-player deltas are not admitted.

Read-only current-objective Stage A preview: four complete UAH maps/50rounds qualify; entire12-round Chalet retains legacy semantics. Conditional season kills Lgon59/Jay59/Az45/Tall28/Dino31; these are mixed-source62-round values, NOT fully credited totals. KOST retains corrected objectives and existing survival/trade components:41/42/38/30/40 respectively, unchanged. Immutable v2 snapshots unchanged, no corrected Rating computed. Source: `research/credited_production_preview.py`; private `production-preview.json` in the same dataset directory. A public migration and source policy remain unapproved; no live wiring/SQL/export/publish.

UID framing recognizes526complete count-prefixed fixed-width ten-player lists covering5260references in the2sealed buffers. No directed damage/downer relationship inferred; opaque suffixes remain unclassified. No semantic life-state label is assigned. Other12070unclassified references remain. Source `research/credited_uid_roster_frames.py`; private `uid-roster-frames.json`.

Current useful finding:2656counter-change observations contain3batched +2 updates (SAL8583R01 Flastryy,8585R04 Legacy,8589R11 vitaking). A single counter offset cannot establish two separate victim-linked kill times. Cached-only full timelines for all3rounds are complete; raw3 outside independent reviewed cases remains a DBNO candidate. No generic owner/time inferred. See [production preview/readiness/rollback](../research/output/credited-kill-production-preview.md) and [UID framing scope](../research/output/credited-uid-roster-framing.md). Count-only basic features are ready on whole complete maps; event features, headshots and fully credited season remain unresolved. Silent flat mixed-stat exports are unacceptable; source/denominator separation and unsupported-map policy need review before live migration.

Verification:421Python tests passed,1optional skipped,6subtests; Go tests including Y11 fixtures and go vet pass. No shared stat/export/web code changed, so no repeated web build needed. All published objective/SQLite/archive/public/v2 and frozen research guards pass. New separate seal `research/credited-basic-semantics-checkpoint.json`, verified by `research/verify_credited_semantics_checkpoint.py`; preserves new dataset/input/raw replay hashes and original guards. Keep research local.

NEXT ACTION: verify the new semantics checkpoint, then characterize the remaining variable-width UID-bearing structure with explicit count/entry/type bounds and ordinary/DBNO controls. Outer packet/type and suffix semantics remain unknown. Alternatively seek independent competing-DBNO and elapsed-clock controls in consumed replay/broadcast data. Do not use nearest counter/UID, array order, raw3 alone or byte-distance timing to assign downer/credited victim. No v3 until input semantics settled; no historical kill migration/publication approved. Prior job command `.venv/Scripts/python.exe research/credited_counter_batch_audit.py` completed from base HEAD above; hypothesis remains that batched observations constrain event timing while round totals stay useful.

Before next discovery job: local milestone `fa220a8`, clean working tree before this note. Hypothesis: other UID contexts are count-prefixed variable-width roster/state lists; no damage meaning assumed. Command `.venv/Scripts/python.exe research/credited_uid_variable_frames.py` will reuse only the2sealed buffers and literal UID inventory. Require exact count, unique expected IDs and explicit observed byte-form bounds; compare reviewed DBNO interval and ordinary same-round controls. Source/result must remain separate from the fixed-width framing checkpoint. Record coverage, opaque types and any rejected/unknown structures; do not infer an attacker or clock.

Variable discovery job completed: strict original three byte forms add only1initial full-roster frame in8580, none in8583. Diagnostic local spacing inventory found recurring opaque prefixes with consistent extra widths (e.g.21/20-10-ff add8bytes,61-01-ff add9, e1-01-ff add10). This is a framing hypothesis, not typed damage semantics. Next command `.venv/Scripts/python.exe research/credited_uid_flag_layouts.py`: use an explicit observed prefix/width table, preserve the narrower result, refuse unknown/duplicate/truncated entries and evaluate all count10 candidates in both sealed buffers. Base HEADfa220a8; no old source/result modified.

Observed opaque width-table result:1696complete full-roster lists/16960UIDreferences;370references remain unclassified. Those lists occur only at offsets82967..186665 /38164..203116, far before action markers73745626/85827303. No literal second UID appears in16960entry payloads. There are151literal UIDreferences after action start; some late records contain adjacent20-byte references whose UID64+RoleImage64+Alliance32 match exact header fields. Both reviewed split-case credited-player/victim pairs occur among them, but record type/roles/time are not decoded. NEXT discovery command `.venv/Scripts/python.exe research/credited_uid_pair_inventory.py`: preserve exact triples and bounds, examine the full two buffers plus ordinary same-round controls, and retain unknown event semantics. Do not infer damage/downer/credit from tuple membership or HUD totals. Earlier framing results remain separate.

Pair inventory complete:52adjacent pairs/113exact references. All52pairs occur after the last live feed elimination, with repeated earlier payloads; not live event packet times. Hypothesis: late cumulative event-history snapshots. Type-byte1/opaque_u32/weapon64/entity64 precedes some pairs, with a boolean suffix; weapon bytes match ordinary feed weapons in inspected examples. Type-byte5/7 plus opaque_u32/entity64 precedes other pairs. Next command `.venv/Scripts/python.exe research/credited_late_event_layout_probe.py`: compare every bounded candidate1 to independent unchanged same-round feed identity/weapon/headshot/order, preserve duplicate physical copies, and leave5/7roles and scalar time units unresolved. No production promotion from2same-build sources. Basefa220a8; all original guards pass.

Late-history layout probe completed: all12unique type1 entries match raw same-round feed identities/weapon/headshot/order exactly;18additional physical copies preserved as repetitions. Type5 includes Kheyze->Stk and Neskin->resetz with opaque scalar4706/5608; type1 finish scalars4834/5633 differ. Type7 includes Maia->Jv92 after a type5 Jv92->Jv92 candidate. These are meaningful control hypotheses but not promoted downer/revive/time definitions.

Before next long job: current basefa220a8 plus additive discovery files. Hypothesis is a late cumulative history with monotonic event scalar, potentially independent of planted countdown resets. Fixed next controls: SAL8583R03/8594R07 (independent official reset cases), UAH FortressR04/later BorderR03 (current build credit differences). Command `.venv/Scripts/python.exe research/credited_late_history_controls.py`. Only these4new sample dumps may be created with the pinned actor binary; existing2buffers reused, no repeated old pipelines/model/target acquisition. Require exact replay SHA, header identity fields and finisher weapon/headshot controls; raw scalar stays uncalibrated. Record incompatibility/partial coverage rather than repair. NEXT: validate outer list framing, type5/7 independent liveness/role controls, then scalar units/planting overtime before any Stage B semantics.

Four controls completed with exact finisher identity/weapon/headshot/order parity, extending to6rounds/41unique eliminations across4builds. Event scalar preserves both known plant-reset orders. Current UAH samples also encode candidate5 Dino->hidebuff before Lgon's finish, and Lgon->getSpoopd before Jay's finish. Scalar magnitude differs materially: professional inter-kill differences are about30units/countdown second, current local samples about210. Units/rate are not established, so neither30nor210 is used as elapsed time. Next cached command `.venv/Scripts/python.exe research/credited_late_history_clock_scope.py` documents monotonic ordering, separate phase ratios and explicit time limits. Type5/7 causal roles and outer record framing still require independent controls. No default/readiness promotion.

Clock-scope job complete: all6event scalar orders match known physical feed order, including plant resets. Ratios vary on coarse/zero/phase-reset clocks; no elapsed seconds inferred. Next cached-only command `.venv/Scripts/python.exe research/credited_late_history_body_controls.py`: bound5/7candidate target-state observations between independently matched type1/feed anchors. Require exact temporal UID/body routes and known body class; report unresolved intervals explicitly, never use this to assign a first-reference causal role. Prior results immutable. Basefa220a8, no runtime/SQL changes.

Body controls completed:18/18candidate5targets have exactly1raw3 observation in independent feed-anchor bounds;2/2candidate7targets have exactly1active observation. First-UID causal role is still not assigned. Full Python447passed/1skip/6subtests; original Go/vet pass unchanged. Next framing hypothesis: a preceding4-byte opaque header value,8-byte payload length and4-byte item count precede a9-byte reference descriptor and cumulative event records. Candidate first arrays have payload lengths66/181 and counts2/4; length equals4count+9descriptor+record bytes in inspected examples. Command `.venv/Scripts/python.exe research/credited_late_history_container_probe.py` tests exact bounds/count against all6buffers; preserves unknown item kinds/refuses incomplete whole lists. No hardcoded runtime offsets/operator edits.

First container probe stopped at SAL8583R03 because an unknown item precedes the first recognized event; its immediately preceding9bytes are not the list descriptor. No result was written/replaced. Updated discovery selects only unique size/count-bounded descriptors enclosing the event, retains all unknown item kinds as partial, and reruns this new hypothesis on the fixed6buffers. Earlier standalone candidate/parity studies remain unchanged; no production parser path affected.

## Latest consumed discovery: unclassified UID-bearing structures - 2026-10-03

Published objective fix and subsequent native-boundary controls below remain unchanged. Two already-cached buffers contain17350literal full64-bit header UID occurrences:8077SAL8580R06 and9273SAL8583R02. Only20matches use the known numeric UID property prefix;17330are unclassified raw contexts. Many references recur for all ten players. Repeated state/roster snapshots are a hypothesis, not established structure or damage semantics. The prior no-UID-in-callback and no-other-player-in-owned-body conclusions remain narrow; the whole replay identity space was not exhausted.

[Discovery scope](../research/output/credited-global-uid-inventory.md); private offset/prefix distributions in ignored data/research/credited-feedback-identity-probe/global-uid-inventory.json. New separate seal research/credited-global-uid-checkpoint.json; research/verify_global_uid_checkpoint.py also verifies the native and authorized objective checkpoints. No new target, model evaluation, parser/default change, credited/event migration, SQL/archive/public write or publish.399Python tests/1skip/6subtests remain latest full gate; latest diagnostic ran successfully on both buffers with all protected guards before/after. Go/vet/web builds remain applicable from objective release.

NEXT ACTION: verify research/verify_global_uid_checkpoint.py; characterize an unclassified UID-bearing structure with explicit framing/type evidence, comparing independently reviewed DBNO intervals to same-round ordinary controls. Establish whether it is a recurring player snapshot or actual damage/DBNO event before using it; reject duplicate, replacement and truncated relations. Do not associate a victim/downer by UID proximity/co-occurrence/last update, array order, camera or aggregate totals. Keep action/operator and objective core logic frozen. Competing-down opening semantics and precise plant-overtime clocks remain unresolved. New research commits stay local; remote production checkpointb71d612 retains the verified corrected objective data6c99d6c.

## Current continuation: native boundary and exact callback controls - 2026-10-03

Objective migration is complete and live-verified; published commits9755cac/6c99d6c, authorized baselineb71d612. All18 live JSON documents matched corrected output after authenticated Pages retry. New objective guard research/verify_objective_history_checkpoint.py preserves original studies and explicitly records prior legacy differences.

Separate readonly credited-kill continuation: fixed68rounds across32consumed SAL/APAC maps/34segments (each segment first/last plus known unknown-offset cases),465finish/death events. Full actual original/native header/operator/action/raw-feedback parity68/68; originally supported counters67/67 unchanged; native68complete, one previously known Jin/APAC8156R03 envelope recovered. No new unknown-offset case. Source remains rejected by the current Python adapter; no default wiring or historical kill migration.

Exact native callback byte probe: independently reviewed SAL8580LairR06 Maia->Stk versus Kheyze credit, SAL8583ClubhouseR02 pino.L5->resetz.LOUD versus Neskin.L5 credit. All12callbacks in those2rounds have0literal full header UID references; reviewed callbacks contain only finisher/victim usernames, no credited-player name. This negative result is limited to exact callback bounds; separate damage/DBNO packets, indirect entity references and encoded IDs remain unassessed. Existing health-derived DamageDealt is a finisher-based estimate, not an independent attacker/victim stream. No downer or event credited owner inferred.

New cached selection/results/buffers are ignored; new source/result/binary/input seal research/credited-native-boundary-checkpoint.json. [Control report](../research/output/credited-kill-native-boundary-controls.md).399Python tests passed,1optional skipped,6subtests. Go tests/vet and both builds passed for the published objective code; no subsequent Go/web/runtime changes. Authorized DB2136ab3d... and all archives/public JSON/v2 snapshots remain identical throughout follow-up. All old research sources/reviews/results preserved, no regrade or Rating fit.

NEXT ACTION: research/verify_native_boundary_checkpoint.py (includes authorized objective guard); inspect separate explicit damage/DBNO records for typed stable attacker/victim relations. Feedback callback literals are insufficient in the two constrained cases. Preserve finisher/victim/counter observations separately; seek competing-down opening controls and independently constrained elapsed/plant-overtime clocks. No remaining-time subtraction across plant resets, byte-distance timing or nearest-counter ownership. Do not promote native source or migrate credited kills/event ordering without separate review. Keep new research local; verified objective publication is complete.

## Current task: authorized objective-only historical migration - 2026-10-03

Latest user authorization supersedes the prior no-write/no-publish objective hold below. Migration is applied, reconciled, published and live-verified. See [full objective report](OBJECTIVE_HISTORY_MIGRATION.md).

Approved 7d4bc8a parser independently resolves Michigan Border R08 disable to Lgon. All five verified archives audited read-only: 15/17 plants and 3/3 disables supported, 18 category-A corrections applied. Kafe R09 bonus/body1 and Chalet R10 nine-player actors remain excluded; unsupported legacy rows retained. Corrected display totals: Lgon2plants/1disable; Azooz2/0; Dino2/0; Tallman4/0; Jay0/0. Lgon Fortress R07 adds one KOST round (40->41/62). Original v2 map/season/career inputs and Ratings are preserved in immutable snapshots; engine, coefficients and final MAE0.03623 unchanged. No credited-kill or event-order correction applied.

DB backup f3dc1021...; migrated DB2136ab3d... . Private backup/public baseline, full raw parser JSON, preview, application/reconciliation evidence and approved isolated executable are in ignored data/research/objective-migration/. Five maps/62rounds/616player-rounds/434kills unchanged;20objective rows and5rating snapshots after migration. All archive files identical. Every generated Rating/eligibility/nonobjective stat unchanged.

389Python tests passed,1optional skipped,6subtests;Go tests/vet and both public/admin builds passed. Actual Start NECC Admin.cmd restarted to current repository source and opened Chrome; live admin recalc/regenerate succeeded; Michigan objective refresh is idempotent. Code9755cac/data6c99d6c pushed via live admin Publish. Pages run37156303656 attempt1 failed at configure-pages with transient GitHub service failure; authenticated retry attempt2 succeeded. All18 live JSON files independently fetched and matched local output; live Lgon2plants/1disable,41/62KOST,Rating1.2417093264919878.

Old research guards intentionally refer to the old protected live baseline. Do not alter their seals. Before migration their chained verification also already failed because launcher setup rebuilt the default exe22cfe0f1... (frozen e7f375b8...). Record these differences with the new objective transition checkpoint; keep original failed v3/ASIA/OCE results immutable. The credited migration review/addendum remain unchanged and opt-in.

NEXT ACTION: use research/verify_objective_history_checkpoint.py for the authorized new baseline and preserved original study seals. Resume separate read-only/opt-in credited-kill research: explicit identity-linked damage/DBNO/victim records, competing-down opening controls and event-clock requirements; no credited-kill or event-order historical migration. Old reviews and finals remain immutable. Do not rerun old live-state guards expecting the prior DB/public hashes.

## Current task: core actor pushed; credited kills migration audit — 2026-10-03

The user's latest instruction supersedes the older-class NEXT ACTION below. Phase1 is complete: pre-push clean HEAD `3535fa5`; reviewed/pushed HEAD **`7d4bc8a17fccccda3ef963914e6887d67df79a27`**, `main`, `https://github.com/uah-r6/uah-r6.github.io.git`. `git ls-remote origin refs/heads/main` confirmed that exact remote SHA. Core source commit `f534b31` is included; body1/bonus-health and unknown-class extensions remain research-only. [Push review/inventory](../research/output/core-actor-push-review.md) records included/excluded files. No public JSON change, historical correction or local database write. Existing Pages code-push workflow builds unchanged committed data.

Pre-push gates: **348 Python passed, one optional skipped, six subtests passed**; Go tests/vet and public/admin builds passed. All prior source/binary/result/identity/support seals and all86 protected SQLite/archive/public files verified unchanged.

Phase2 is in progress in additive files, preserving all frozen source dependencies: `dissect/credited_kills.go`, `cmd/kill-credit`, `r6stats/kill_credit.py`, new tests and `research/credited_kill_*`. No default import/export/statistics/rating wiring has changed. Stable UID + explicit temporal scoreboard slot/class + monotonic initial/terminal counters derives official-style per-round credited kills. Raw finish/death events, offsets and original rating inputs remain separate. Full identity/counter/continuity gaps refuse complete totals; rehost reset requires a new physical folder R01, same ten nonzero distinct profiles, all-zero baselines. Reconnect/component replacement is conservatively unresolved.

New Go validation reuses already-decoded consumed SAL/APAC structure: **32maps/325rounds**,31complete maps;**280official credited-kill matches/0mismatches/40unavailable**,310public matches/0mismatches. Later independently verified APAC primary identities unlock the80additional kill comparisons without changing original aliases/labels. All290 independently bound victim deaths match;30identity-unbound death rows remain unavailable. APAC8156R03 has unknown death offset, so new baseline guard refuses that map (the historical accepted audit/final remains unchanged). Twenty SAL maps/207rounds/all200 player-map official comparisons still agree. No fresh final, fit or repeated acquisition/parsing pipeline.

Read-only UAH audit: five maps/62rounds,58complete round counter structures; Chalet logical9–12 has incomplete nine-player UID roster and stays unresolved. Four other maps have complete credited totals. Known-round deltas: Lgon−2, OhWowJay+1, DinoFireKing+1, AzoozNewzz0, Tallman3.14 0. These are **58-round deltas, not complete revised season totals**. Five actual first-round reader checks match cached credit/finish output and the pinned actor binary's operator/player snapshots. Cached state observer text has a legacy UTF-8 mojibake issue in accented `roleName`; numeric operator/player/current binary parity is preserved. Full details: [UAH audit](../research/output/credited-kill-uah-audit.md), [professional audit](../research/output/credited-kill-professional-audit.md); private evidence in ignored `data/research/credited-kills-v1/`.

Consumed8580Stk chronology is now measured: raw3/DBNO at74255864, Kheyze credit5→6 at74275879, Stk raw4 at74275897, Maia finish74276292. Credit arrives alongside final-elimination serialization, not the earlier downed transition in this case; no generic victim/downer mapping is inferred. All200 SAL credited multikill-size breakdowns match official data; all207round summaries match public multikill events. Original finisher buckets match176/200. Original opening map counts match193/200; separate packet-order diagnostic198/200, with two remaining pino/Neskin owner differences. Two changed order rounds:8583R03 and8594R07. Production event features remain unchanged. [Migration review](../research/output/credited-kill-migration-review.md) includes the impact inventory, conditional mixed-source UAH scenario, core/research/unresolved actor categories and rollback/version plan.

Additive follow-up after local `eeca495`: independent official HUD now corroborates both changed opening-order rounds as preplant/postplant clock resets. Clubhouse8583R02 visibly shows first victim resetz downed then finished by pino while Neskin receives the kill and pino an assist. This particular credited opening plus the two order corrections explains all200 consumed SAL map opening aggregates; it is descriptive corroboration, not a universal rule or revised final score. Original193/200 and198/200 results remain sealed. Reports: [opening owner](../research/output/credited-kill-opening-owner.md), [Clubhouse clock reset](../research/output/credited-kill-opening-hud.md), [Bank clock reset/overtime](../research/output/credited-kill-opening-bank-hud.md).

A separate native feedback-envelope reader recovers Jin8156R03's exact callback envelope41873708..41873781 without altering the original Death offset0, raw feedback or frozen reader. Ten APAC8156 rounds now validate; all10 independent credited kills/public counts and10 victim deaths agree. Ten header/operator/raw-feedback comparisons and five archived UAH first-round parity controls pass. Six new Go test functions include a sanitized real structured fixture and invalid/ambiguous/duplicate/late-baseline refusals. Native source is deliberately not accepted by the current Python adapter; this development path is not promoted. Original31-complete-map study remains unchanged. [Native follow-up](../research/output/credited-kill-native-envelope.md).

An independent consumed trade aggregate audit compares original features to primary fields without tuning:139/200 refrag/trade-count agreements,121/200 traded-death agreements,83/200 both. Aggregate labels do not establish the target's event semantics; no owner/window/clock change is justified. [Review addendum and next steps](../research/output/credited-kill-migration-addendum.md). Core push remains remote `7d4bc8a`; Phase2 checkpoints remain local only.

Further cached-only clock audit after `eb8ff77`:207SAL rounds,47unique plant anchors;19rounds change full death ordering under remaining-time sort. All88inverted event pairs cross a plant-state boundary; zero other inversions. There are100zero-clock death records and51raw finisher refrag candidate pairs across planting, with elapsed time explicitly unresolved. [Clock scope](../research/output/credited-kill-clock-epochs.md). No packet-distance or cross-epoch seconds calculation is promoted.

Read-only UAH order sensitivity verifies stored sequence against archived physical feedback on58supported rounds; ten have changed ordering. Packet-order-only deltas: Lgon pivotKills?2; OhWowJay pivotKills?1/pivotDeaths+1/openingKills+1/openingDeaths?1; Azooz pivotDeaths+1; Tallman pivotDeaths?1; Dino pivotDeaths+1. Current raw counts/operators/sides are unchanged; four incomplete Chalet rounds are excluded. This hypothetical study keeps the legacy8s trade predicate, suppresses BOTH Rating formulas and never patches the live module. No proposed corrected trade or complete-season result. [Per-map-ID impacts](../research/output/credited-kill-uah-order-impact.md).

Latest verification: **379 Python passed, one optional skipped, six subtests**; twelve new clock/Rating-isolation safeguards. Prior Go tests/vet and public/admin builds remain applicable because no Go/web source changed after their full passes. Both earlier credited checkpoints and all86 protected files remain unchanged. New clock/UAH checkpoint is separate.

**NEXT ACTION:** verify `research/verify_credited_clock_checkpoint.py`, which also verifies both earlier credited seals. Continue explicit identity-linked damage/DBNO/death controls and prospective event-clock requirements; elapsed planting-overtime time is still unknown. Generic credited-victim association, competing-DBNO opening policy and trade timing remain unresolved. Broader native-envelope controls and explicit source integration precede promotion. Historical SQLite writes, public regeneration and UAH core actors await user review of the migration audit/addendum and original-v2 snapshot plan. Preserve v2 original input semantics/MAE0.03623 and both permanently failed v3 finals. Do not change default wiring or publish corrected data. The earlier native/HUD checkpoint passed367Python tests and Go tests/vet. Public/admin builds passed during Phase1, and web source remains unchanged. All86protected files and prior frozen studies verified unchanged.

## Previous checkpoint: older-class controls preserved; bonus support remains insufficient ? 2026-10-03

Local checkpoints include `591731b` (OCE result/consumed review) and `2a7fffe` (older-class lifecycle). No push or publish. The fixed OCE result remains **INSUFFICIENT**: 38 sources, 32 complete maps, 330 rounds, 84 plants, zero bonus recoveries; six whole-map refusals preserved. Later exact identities support 18 consumed reviewed maps, 11 independently constrained agreements, seven parser abstentions and no conflicts. These later observations never regrade the prospective result.

New consumed controls cover all 114 build9734089 rounds: 2,870 typed state properties, 794 known feed-death controls, 47 raw1 numerical patterns with exact historical ownership of all four numeric fields. All 31 plant intervals remain raw0/2, uniquely bound and free of preceding owner deaths; the unknown body class still causes abstention. Raw1 timing explains the apparent rare-case absence: 36 observations are in no-plant rounds; seven belong to another player before planting, two to another player afterward, two to the completing owner before the interval. None belongs to the completer during the full interval. These are property counts, not independent actor cases.

Official OCE Day4 broadcast `ZCQqoIH4O0U` supplies two consumed DBNO/recovery controls (Proxy R01 and Elementz77 R07): ten named HUD frames align with raw0 active, raw3 downed, raw2 recovered and raw4 eliminated in these cases. Initial strict projection retains five R01 abstentions from the postplant clock reset preceding the serialized anchor; separate first-countdown projection resolves those frames while preserving earlier R07 values. Existing action markers/operator logic are unchanged. Proxy later visibly plants after recovery with raw2 on the same component, independently supporting one additional consumed owner beyond the seven sole-player constraints. No numeric HUD health, downer/reviver identity, universal enum or bonus plant is claimed. Timer inventory adds 27 explicit terminals still above completion range (17 with only raw0/2); completion safeguards stay intact.

**Readiness:** supported conservative core remains production-quality; bonus extension and older-class compatibility remain unapproved. No bonus/class port or actor correction was made. Final UAH proposal remains 20 objectives, 18 resolved core proposals and two unresolved plants. Kenbot.USU stays research-only; nine-player Chalet stays unresolved. Unresolved historical-credit policy still needs review before exact final totals can be asserted.

**NEXT ACTION:** follow `research/output/objective-body-class-next-protocol.md`. A separate older-class development specification needs remaining sharing/replacement/disconnect and interaction-spanning negative controls, then an independently frozen unused validation pool before promotion. Keep the original bonus candidate unchanged; any eventual rare-case study must be larger, fixed and genuinely unused, with unchanged gates?not more isolated event chasing. No fresh events were acquired beyond the already completed fixed OCE pool. Preserve all consumed ASIA/OCE/v3 results; do not fit v3 or change live kill credits.

Verification: **348 Python tests passed, one optional real-replay test skipped, six subtests passed**. Seventeen new tests protect temporal routes, death association and displayed-clock phase/transition ambiguity. Later inventory scripts were exercised against cached real data. Source/binary/result/identity/support seals and all 86 protected SQLite/archive/public hashes match. Go/web/runtime sources did not change; prior Go tests/vet and public/admin build passes remain applicable and were not rerun. Live v2 MAE 0.03623, both failed v3 finals, SQLite, archives and public JSON remain unchanged. No import, recalculation, export, publish or push.

Recovery: `.venv/Scripts/python.exe research/objective_oce_consumed_support_verify.py` verifies new consumed hashes and all prior freezes without collection/evaluation/writes. Seals: `research/objective-oce-consumed-lifecycle-checkpoint.json`, `research/objective-oce-consumed-hud-checkpoint.json`. Reports: `objective-bonus-body-oce-body-class-lifecycle.md`, `objective-bonus-body-oce-body-class-hud.md`, `objective-bonus-body-oce-body-clock-scope.md`, `objective-bonus-body-oce-plant-after-recovery.md`, `objective-bonus-body-oce-timer-controls.md`, `objective-bonus-body-oce-numeric-identity.md`, `objective-bonus-body-oce-raw1-timing.md` under `research/output/`. Original one-shot/identity/review creation commands must never be rerun.

## Current checkpoint: fixed OCE study complete; bonus support remains unapproved — 2026-10-03

Recent local checkpoints `21a94ee` (full prelabel seal), `c0fc55c` (prospective identities), `9065d28` (permanent result), `22119ba` (additional consumed identity seal). No push. All38 selected OCE archives completed as32quality-complete maps/330rounds/84plants plus6whole-map refusals. The frozen conservative and isolated bonus candidates both resolve53plants;31abstain. **Zero bonus recoveries**, zero changes to previous credits, zero false proposals across246no-plant controls. Original one-shot pooled status permanently **INSUFFICIENT**. Raw resultSHA `f7b79ae20ed4f6a7fdc07ba00b18ad5a99708f4b2964dd5e85befe1f0ddd1d73`; prelabel sealSHA `c5b5cfaf76978dc26efb4b67a48ad7390f1450e30ab16fbec3d8094279c82160`. Never repeat `objective_bonus_body_oce_review.py --evaluate` or add events after seeing zero positives.

Original prospective identity snapshot:4complete primary-bound maps/28blocked. Four resolved core actors independently agree with sole-player official totals; one independently constrained older actor remains an abstention. No primary aggregate/occurrence conflicts. Further legitimate profile retries using current names found in sealed exact-UUID header inventories succeeded AFTER that result. These additional exact account histories were separately sealed before a **consumed reviewed tier**:18maps/188rounds,11independently constrained agreements,0disagreements,7known actors whose parser abstains,0aggregate/occurrence conflicts;14maps still identity-blocked. This overlaps the original four maps and cannot regrade the prospective result. See `research/output/objective-bonus-body-oce-consumed-primary-review.md`.

Compatibility diagnostic: all31abstentions use build9734089. Direct expected slot4154dcc4 has classb529300b, while the frozen guard expects0c98c63f. Existing raw e788f6a5 interval field values are26zero/5two/noone. This is a typed body-class compatibility lead, not an approved body mapping or evidence of hidden state1 plants. No class allowlist, liveness/HP predicate or actor source changed. All6quality refusals were reproduced from cached pinned headers: score rollbacks and non-unique numeric UIDs (often shared6366317606386794496 across one team). Completed rounds are never dropped to fix chronology. See `objective-bonus-body-oce-body-coverage.md` and `objective-bonus-body-oce-quality-refusals.md` in `research/output/`.

**Readiness:** conservative CORE resolver is production-quality on supported guarded structures; older/unknown structures explicitly abstain. BONUS-HEALTH extension is NOT production-quality yet: the frozen rare-case gate remains unmet. ASIA's original result remains insufficient at its original SHA;16of24identity gaps independently verified,8individual supports remain separate. The final read-only UAH correction report covers20objectives/18core proposals/two unresolved plants with current actor/count and timer/completion/body evidence. Kenbot.USU KafeR09 remains research-only; nine-player ChaletR10 remains unresolved. No SQL correction/recalculation is applied, and resolved proposal totals are not guaranteed final totals until unresolved historical-credit policy is reviewed.

**NEXT ACTION:** continue consumed body-class b529300b diagnosis with exact UID/property/lifecycle/death/DBNO controls and independent completion evidence (seven primary-constrained abstentions are available). Do not reinterpret0/2 or HP>0 as liveness on an unknown class. Any compatibility hypothesis must be isolated from frozen candidates, fully controlled and prospectively reserved before promotion. Keep the current bonus rule unchanged; a future rare-case study needs a genuinely unused, larger predeclared sequential/multi-event pool with fixed maximum events/maps and unchanged zero-error/minimum-case gates, not another isolated event selected because these supplied no positives. Entire OCEStage1/Stage2 events are now consumed; ASIA and all previous events remain consumed. Do not fit v3 or change any live stats/Rating while input quality and rare-case validation remain incomplete.

Cached safe reproduction (no fresh evaluation): `research/objective_oce_body_coverage_diagnostic.py`; `research/objective_oce_consumed_quality_diagnostic.py`; `research/uah_actor_correction_proposal.py`; `research/objective_bonus_body_oce_review.py` with NO evaluation flag verifies the seal. One-shot and sealed identity creation commands are forbidden to repeat. All accepted330physical replay hashes, both failed v3 final results, ASIA/OCE source/binary/seal hashes and all86protected SQLite/archive/public hashes match. Livev2 historical finalMAE0.03623 unchanged; no newfit, runtime/operator/action/kill change, import, public regeneration, archive mutation, push/publish or deployment.

Verification: **331 Python tests passed, one optional real-replay test skipped, six subtests passed**. Known warnings: Starlette/httpx deprecation and Windows pytest-cache permissions. All source/binary/identity seals, permanent ASIA/OCE/v3 results and all86 protected file hashes verified after the suite. No Go/web/runtime sources changed; earlier Go tests/vet and web builds remain applicable, not rerun in this checkpoint.

Further consumed component lifecycle diagnosis: all114 build9734089 rounds/1140header player-rounds/2870unique typed state properties. Raw state1 appears47times and all47meet the numerical bonus pattern, but none is in the31plant intervals; this does not change prospective bonus coverage. Raw3/4properties can retain positiveHP (228cases). Among794known feed-death controls, last preceding rawstate4 inall794; one separate death offset remainsunknown. Seven independently constrained plant timer owners allmatch exact official identity; all31intervals keepunique unchangedtypedroutes/noownerdeath, yet classsemanticsremainunapproved and actorsstillabstain. Six new temporal-sharing/replacement/death/observation tests pass;331fullsuitepasses remain the prior full gate. See `research/output/objective-bonus-body-oce-body-class-lifecycle.md`; new consumed hashes sealed in `research/objective-oce-consumed-lifecycle-checkpoint.json`. NEXT investigate independent official HUD for raw3-to2 recovery/DBNO controls on the older class, without modifying the frozen candidate or grading.

## Actor checkpoint: ASIA identity review, UAH proposals and fixed OCE cohort — 2026-10-03

Local checkpoints `9795bac`, `1efe93a`, `d36d34f`; no push. ASIA identity evidence was separately sealed before consumed actor review: 16 of 24 gaps verified by exact replay UUID username histories. Eight remain unresolved without fuzzy/digit/remaining-player inference. One full primary-bound map has no plants; all 19 plant rounds remain unavailable for full-map ground truth. Eight individual sole-planter supports (zero individual disagreements) are descriptive only. This includes KlzzSS../Klz 8186 R10; exact profile history and Ubisoft sole-player plant total support the one observation, while Jittery lacks exact UUID history. Original prospective ASIA result remains permanently **INSUFFICIENT**, SHA95f866760fa754407e83cf3d4e2be88a5f7a4d12cdc376fb512ed3c9875fff61. No reviewed support regrades it.

8193 diagnosis: first-folder unfinished R05 has ten distinct profile UUIDs, but SpeakEasy/Hoven/Terd/Gotti share numeric UID6366317606386794496. Score remains2–2. Frozen chronology checks identity before recognizing unfinished attempts; whole-map refusal stays unchanged. No player/round repair.

Final read-only UAH proposal: five maps/62 rounds/20 objectives; core resolves15plants and3disables, two plants abstain. Per-objective stored actor/count, direct owner/timer/terminal, completion/body/UID evidence and proposed action are in `research/output/uah-final-actor-correction-proposal.md`. Core is assessed production-quality for supported guarded structures; bonus extension still lacks prospective rare-case coverage. Kenbot.USU KafeR09 remains research-only; nine-player ChaletR10 unresolved. Proposed tracked counts include only resolved core events, not exact post-correction totals while unresolved historical credits await policy review. SQLite opened mode=ro; no correction or recalculation applied.

New fixed actor-only reserve: ALL38 linked BO1 archives from OCEStage1 (competition507/14998,26linked) and OCEStage2 (512/15003,12linked), 56scheduled. Maximum2events/56maps; chronological order; complete fixed sample before labels, no early success or extra-event chasing. Same frozen minimum3bonus cases on2maps/2independently constrained actors and zero wrong-credit/control/regression/conflict gates. Candidate/old dependencies/binaries/quality/identity guards unchanged. `research/objective_bonus_body_oce_cohort.py` reuses the original collector with scoped data/freeze globals; its legacy ASIA literal event label/extraction prefix is ignored in favor of the OCE reservation provenance. Review helper frozen separately before primary targets.

First OCE proof8070Fortress:11rounds/1plant/0bonus. Cached full collection is running through38 selected sources, retaining explicit whole-map quality failures. **NEXT ACTION:** finish `research/objective_bonus_body_oce_cohort.py --limit 38 --seal` (do not launch a second worker while current collection runs); commit full prelabel seal hash/coverage, then project exact official names and independently resolve username/UUID gaps before sealing identities with `research/objective_bonus_body_oce_review.py --identities`; review primary objectives once with `--evaluate`. Do not silently revise the identity snapshot after objective review. Preserve pass/fail/insufficiency and all failed historical results. No actor targets for OCE have been opened yet.

Verification:321fullPython tests passed,1optional skipped,6subtests, plus4new identity-first review tests. OCE/ASIA source/binary freezes, both failed v3 final hashes and all86protected SQLite/archive/public files match. Go/web/runtime sources unchanged; prior Go/vet/build passes remain applicable. Livev2 finalMAE0.03623 unchanged. No Rating fit/default/formula change, SQL/archive/public write, import, push/publish or deployment.

## ASIA one-shot actor result permanently insufficient - 2026-10-02

Checkpoint base033c550. Fresh candidate/sourcefreezea000470 and prelabel quality wrapper9e536df unchanged. All12 selected sources were sealed before targets; prelabel inventory rawSHA8b4a40e5c642cced229e3351e2d91126e2110b0909a10e2d5a5f33f0193e4d72. Ten complete maps/96rounds/19plants:18original actors ->19isolated actors;1bonus recovery on1map (8186/Nighthaven/R10 KlzzSS..);77no-plant controls,0false positives,0changed original actors. Two whole-map quality failures retained:8182score rollback4-3->3-3,8193incomplete full stable10-player roster. No physical round omitted or repaired.

Primary-only one-shot result is permanently **INSUFFICIENT**: frozen20plants/3bonuson2maps/2independent bonus actors not reached. All10complete maps also lack full exact primary username bindings, so0primary-reviewed maps and0independent bonus constraints. Zero detected independent wrong actors is unassessed here, not19verified correct credits. Initial public actor labels remain unopened. Rating values were never requested/projected. Entire ASIA event now consumed for this actor hypothesis. Never reevaluate or reinterpret this as a pass.

Permanent result `data/research/objective-bonus-body-asia/one-shot-primary-result.json` rawSHA95f866760fa754407e83cf3d4e2be88a5f7a4d12cdc376fb512ed3c9875fff61. See `research/output/objective-bonus-body-fresh-asia.md`. No production bonus-health port; original conservative resolver remains installed. Both failed v3 finals, frozen source checks, livev2MAE0.03623 and all86protected hashes unchanged. No SQLite/archive/public changes, newfit, push/publish or deployment.

Additional narrow consumed8580/Stk DBNO probe:342numeric4/8-byte fields across unique temporal victim-owned routes;0literal references to another header playerUID/UID-ownerentity. Stk directbody states2->0->2->3->4 precede Maia finish at74276292; health100->6->0 in this reviewed case. Scope is existing owned fields only, not every possible packet/indirect reference. No downer credit assigned. See `research/output/v3-consumed-dbno-body-reference.md`.

NEXT ACTION: separate consumed ASIA identity review using exact replay-profile UUID histories and explicit official roster spellings, starting8186bonus case. Preserve original strict result; no stripping digits, fuzzy names, remaining-player or objective-count matching. Only independently supported aliases may unlock separate reviewed constraints; cannot satisfy/change the historical fresh gate. Investigate8193missing roster source without weakening full-roster safeguards. Before any future bonus port, reserve a larger genuinely unused actor-validation set and keep current predicate/gates frozen before outcomes. Do not fit/relax either consumed Rating final or mutate protected state.

Reproduction: `research/objective_bonus_body_fresh_collection.py --evaluate` is FORBIDDEN to repeat now; result exists. Read cached result/inventory only. `research/v3_consumed_dbno_body_reference_probe.py` is cached read-only. FullPython300pass plus5newcollector tests; noGo/web/runtime change since prior fullpasses.

## Fresh ASIA actor reserve frozen; acquisition in progress - 2026-10-02

Current local checkpoint9e536df. Consumed bonus evidenceaf4521a; prospective selection/pipeline59bbcc4; candidate/source/binary/gatefreezea000470. All300Python tests passed plus5new collector safeguards. No push. Fixed ASIA Stage2 group-stage snapshot:28scheduled/12linked official archives8182..8193; metadata-only selection, no Rating/actor target inspected before freeze. All existing actor/Rating cohorts remain consumed.

First8182Villa archive failed the unmodified completed-score guard: physical first fragmentR07 ends4-3, rehostR01 starts3-3. Do NOT omit that completed physical round to make chronology fit. The entire map is preserved as an unavailable quality record. A separately frozen prelabel collector addendum records whole-map failures in the fixed12-source inventory, while retaining unchanged actor predicate, gates, original sources, and acceptance thresholds. Only explicit identity/chronology refusals are caught; actor regressions, false positives, feedback changes and implementation bugs abort. All5wrapper safeguard tests passed. Original failed proof log is hashed in the addendum; no target actors were opened.

Second8183Clubhouse pipeline proof succeeded:11complete rounds,2verified plants,0bonus recoveries. Download/extract/parser/direct owner observers and prediction cache work. Batch6is running; all other selected archives must be processed incrementally before opening independent objective totals. A minimum3bonus recoveries on2maps and2independent constrained bonus actors is frozen; insufficient positives is not a pass. Full fixed selection must be sealed as predictions OR whole-map quality failures before actor targets. Public comparison stays separate; no Rating values, newfit, production body changes or correction.

NEXT ACTION: finish cached acquisition with `research/objective_bonus_body_fresh_collection.py --limit 6`, then `--limit 12 --seal`; verify frozen sources, binaries, all86protected hashes and both permanent failed Rating finals. Commit the prospective complete-inventory seal hash/coverage before running `research/objective_bonus_body_fresh_collection.py --evaluate` exactly once. Preserve any failure/insufficiency; never regrade old finals or tune on this actor reserve. Continue independent diagnosis afterward. No SQLite/archive/public mutation, push/publish or deployment; livev2MAE0.03623 unchanged.

## Bonus-health consumed audit complete ? 2026-10-02

Checkpoint base `7d7aca7`; prior SAL evidence `1f5f6c1`. Isolated research only: no production enum or frozen rating dependency changed. The official SAL Day1 HUD independently corroborates KDS8581/Villa/R06 planting while boosted; completion banner appears at8465s. Camera follows xSexyCake, not KDS; numerical120/100HP comes from direct replay body fields. Exact visual limits and hashes are recorded separately.

The candidate retains every original plant guard and only reconsiders an otherwise eligible state1 completer. Direct same-owner body fields must show health>baseline>0, ceiling=baseline+20, health<=ceiling, and positive float bonus matching excess/base at explicit record and interaction endpoints. Each field has a unique temporal body route at its own offset. Unknown/DBNO/dead/missing/sharing/canceled/zero-offset-death cases abstain. Defense remains unchanged.

**All894 consumed professional rounds audited:**221 verified plants,214 original resolved ?217 isolated resolved; zero changes to already-resolved credits; zero false positives across673 no-plant controls. Three new proposals: KDS8581/R06, Nuxxga8588/R02, OSAdinho8163/R09. Only KDS has independent visual corroboration in this study. Four plants remain unresolved:3905/R03,R04,R06 missing known body declaration;4133/R07 unknown death offset. Original targets, exclusions, failed finals and reviewed tiers remain separate and immutable. See `research/output/objective-bonus-body-consumed-audit.md`.

Read-only UAH: five archived maps/62rounds,17plants;15?16 resolved. The extra proposal is untracked opponent Kenbot.USU Kafe/R09. The nine-player Chalet/R10 remains unresolved. No stored correction applied. Lgon original38 Attack usage exactly preserved: Zofia4, Striker4, Gridlock3, Ace2, Grim2, Deimos1, Sens1, Twitch1. See `research/output/uah-bonus-body-readonly.md`.

283 Python tests passed plus one new reduced real KDS regression being verified; one optional test skipped, six subtests passed. Both frozen dependency checks, both failed final hashes and all86protected SQLite/archive/public hashes pass. Existing Go/vet/web passes remain applicable because no runtime source changed. The22KiB public-safe KDS fixture contains structured summaries only, ordinalized header UIDs, no profileUUIDs/rawreplays/privatepaths.

**NEXT ACTION:** prospectively reserve/freeze all currently linked ASIA Stage2 official group-stage archives (competition511/phase15002) for isolated bonus-health actor validation. Metadata discovery found28scheduled/12linked; no new replay or target actor has been opened. First chronological archive8182 proves download?extract?parse?direct owner pipeline before incremental expansion. Candidate/dependencies/parser/acceptance gates must be frozen before opening any outcome. No rating fits or target errors; no runtime body enum change, SQLite write, archive mutation, public regeneration, push/publish/deployment. Livev2 stays frozen at historical finalMAE0.03623; both v3 final failures remain permanent.

Reproduction: `.venv/Scripts/python.exe research/objective_bonus_body_consumed_audit.py --include-prior` (894 cached); `research/uah_bonus_body_readonly.py` (read-only cache); `research/v3_bonus_body_vod_review.py`; `.venv/Scripts/python.exe -m pytest -q`. Never rerun either final evaluation or old derivation.

## APAC extension and body-state hypothesis ? 2026-10-02

Checkpoint base: `1f5f6c1` (completed SAL evidence preserved locally; no push). The consumed APAC audit now covers all 12 maps / 118 rounds / 120 player-map rows with complete continuous direct UID kill counters. Every credited total matches the original public total. There are 32 player-round credit/finish differences, 29 affected player-map patterns, 26 differing map totals, and three already-eligible rows with offsetting differences: OSAdinho (8161/R03,R14), akusu and Yuyu (8162/R06,R08). No original input, eligibility or final metric changes. See `research/output/v3-consumed-apac-kill-credit.md`.

Independent APAC primary review covers nine maps / 92 rounds / 90 players: all official/public K/D totals agree, 68 also agree with opponent finishes; 25 plant and three disable actor agreements against original labels; nine plant and all three disable actors are independently constrained by official single-player totals. Zero aggregate objective contradictions. Three maps (8157,8159,8163) remain unavailable for full primary review because official `MUNU` does not explicitly match the bound account spelling `munu74.TMT`. The complete unique ten-player identity guard is retained. Current UUID history contains munu74/munu74.TMT, but not MUNU; roster membership alone is not used to fill that spelling gap. The first strict three-map review/source remains cached separately. No frozen alias is changed. See `research/output/v3-consumed-apac-primary-review.md`.

The original APAC seal hashes quality JSON with LF normalization, while other file digests use raw bytes. All twelve quality files match the recorded normalized hashes; predictions/API/targets also match. Two regression tests cover Windows CRLF equivalence and reject changed content. Both frozen source checks and permanent failed final hashes pass. **266 Python tests passed, one optional test skipped, six subtests passed**. All 86 protected SQLite/archive/public hashes unchanged; prior Go/vet/web passes remain applicable with no runtime source changes.

All three unresolved professional timer-owner plants have a known stable body component but raw state `1`: SAL8581/R06 kds (Hibana, states0?1), SAL8588/R02 Nuxxga (Finka, state1), APAC8163/R09 OSAdinho (Montagne, state1). No body declaration changes occur during those episodes. The port continues to abstain. See `research/output/v3-consumed-unknown-body-inventory.md`.

A separate numerical audit across all 325 consumed SAL/APAC rounds finds 63 state1 properties: all63 have health above an observed baseline, ceiling baseline+20, and positive float bonus matching `(health-baseline)/baseline`; none follows a known death. This supports a **bonus-health hypothesis**, not an approved body enum. Known state3/4 can retain positive HP (694 properties), so HP>0 must not replace the body guard. Finka's official description supports temporary health boosts but does not define replay integer1. No actor allowlist or operator/action-start logic changed. See `research/output/v3-body-state1-health-hypothesis.md`.

**NEXT ACTION:** independently review a current Y11 bonus-health/body1 timer-owner case in official broadcast HUD, retaining exact replay offsets and visual limitations. Only then consider an isolated consumed-data body1 hypothesis with direct health/UID routes, death/DBNO/revive/cancellation/sharing controls and a separately frozen actor reserve before any port change. Preserve both v3 final failures; do not admit old excluded maps or refit on consumed finals. Live v2 stays frozen at final MAE0.03623. No SQLite writes, archive mutation, public regeneration, push, publish, or deployment.

Reproduction: `.venv/Scripts/python.exe research/v3_consumed_apac_credit_probe.py --limit 12` (completed evidence cached); `research/v3_apac_official_review.py --limit 12`; `research/v3_unresolved_body_inventory.py`; `research/v3_body_state1_health_audit.py`; `.venv/Scripts/python.exe -m pytest -q`. Existing final evaluation commands remain forbidden to repeat.

## SAL actor audit and credited-kill integrity ? 2026-10-02

Checkpoint base: `5460781`. The fixed actor port was frozen before SAL acquisition. Across 20 maps / 207 rounds: 45 of 47 plants and all seven disables resolve. Original public comparison: **45 plant agreements, two unresolved plants; seven disable agreements; zero occurrence differences**. Independent Ubisoft totals constrain 22 resolved plant actors and all seven disable actors, plus one plant actor whose replay still abstains. The remaining 23 resolved plants have aggregate consistency only. Both unknown-body cases remain unresolved. See `research/output/v3-sal-official-actor-constraints.md` and `research/output/v3-sal-original-public-actor-comparison.md`.

The completed direct stable-UID counter audit matches official/public credited-kill totals for all 200 player-map rows. It finds **52 player-round differences in 26 rounds**, affecting 46 player-map patterns. Forty-three map totals differ from accepted opponent finishes. Three already-eligible rows hide six offsetting differences despite exact map K/D: Kheyze (8580/R06,R13), Bokzera (8591/R04,R05), and vitaking (8594/R05,R10). Exact map K/D therefore does not establish round-level credited-kill consistency. The mitrix?Legacy teamkill in 8596/R10 is a separate raw-feed negative control; the tracker already excludes it correctly. See `research/output/v3-consumed-round-credit-integrity.md`.

The initial cumulative-only audit and raw-feed comparison remain cached separately. Rehost counter reset is permitted only at a new physical folder R01 with the same ten distinct nonzero profile UUIDs and all counters initialized to zero; 8596/logical R06 meets this condition. Counter ownership is established from declared component routes, not expected external totals. No event/victim is reassigned.

Independent official Y11 broadcast `Ao6SRRhCmbg`, SAL Day 1 (2026-09-05), verifies 8580/Lair/R06 at 3484?3488 seconds: Stk is DBNO; AngelzZ kills Kheyze; Maia appears as Stk's finisher. Already-dead Kheyze's HUD kills increase 5?6; Maia's kills remain six and assists increase 0?1. The direct UID counters agree. The downing shot is not visible, and observer Ar7hr is not used as an identity inference. This proves one current Y11 credited-kill/finisher split, not every discrepancy's cause. See `research/output/v3-consumed-dbno-vod-review.md`.

Verification: **264 Python tests passed, one optional real-replay test skipped, six subtests passed**. Both frozen dependency checks pass; all 20 prediction/quality/API/stat digests match the prospective seal; both permanent failed v3 result hashes and all 86 protected live-file hashes are unchanged. Cached actor reporting now verifies the actual freeze, parser, permanent result, independent source hashes, embedded constraints, and a separate immutable provenance manifest. Original actor-comparison JSON was not changed. Prior Go/vet/web gates remain applicable: no Go/web/runtime source changes since those passes.

**NEXT ACTION:** checkpoint this evidence locally, then check credited-kill versus finisher consistency on already-consumed APAC/development data, starting with a small cached sample. Preserve frozen eligibility/features/models/results. No new fit on consumed finals, runtime kill/operator/action changes, SQLite writes, archive mutation, public regeneration, push, publish, or v3 deployment. Live v2 remains frozen at historical final MAE 0.03623; both v3 finals remain failed. Any future credited-kill design needs explicit victim/event/DBNO/revive evidence while retaining finisher identity and death timing separately.

Reproduction (repository root): `.venv/Scripts/python.exe research/v3_consumed_cohort_integrity.py`; `.venv/Scripts/python.exe research/v3_sal_public_actor_comparison.py`; `.venv/Scripts/python.exe research/v3_consumed_kill_credit_probe.py --limit 20` (cached observers); `.venv/Scripts/python.exe research/v3_consumed_dbno_vod_review.py`; `.venv/Scripts/python.exe -m pytest -q`. Do not rerun either final evaluation or the old `pipeline.py all/derive`.

## CONSUMED SAL DIAGNOSTICS / CORRECTED UAH READ-ONLY COMPLETE - 2026-10-02

Permanent final checkpoint ae2c7a8; failed75.9%within.05 result unchanged. Descriptive consumed cohort:93/141rows improve,48worsen; objective-positive24rows20improve/4worsen,MAE.05581->.03328 versus zero-objective117rows.03847->.03531. Map-cluster paired2000-draw descriptive95% MAEdelta interval[-.00936,-.00356]; no new acceptancegate, refit or causal-objective claim. Full141feature decomposition checked against exactpredictiondelta; heavy residuals/15largesterrors in output/v3-corrected-final-sal-diagnostics.md.

Independent officialSALplayer-mapK/D totals agree with public for all200rows:157alsoagreewithreplay,43replaykiller-countdifferences. All43deathcountsagree;teamkills0;totalmapkill differencesbalance0. Thus notmissingdeaths or teamkill-count convention. Noalready-eligiblecleanrow has anofficialK/Dcontradiction. Exact already-bound publicIGN Wizard. matchesofficialWizard.; separateconsumed Nuxxga/Nuxga UUIDhistoryreview onlyhelpsprimarydiagnostics, doesnotaltersealedaliases/gates/eligibility. output/v3-corrected-final-sal-kd-constraints.md, primary20pagescachedignored. Agreementmayreflectsharedtelemetry; notproof of a specificfaultyparserpacket.

Separate correctedKOST UAHreport output/v3-corrected-uah-readonly.md:3completeactor maps/36rounds;fullseasonv3UNAVAILABLEbecauseKafeR09unknownbody andChaletR10nine-playerroster. Partialcontrolledv2->v3 Azooz.993->1.002,Dino.842->.837,Lgon1.335->1.353,Jay1.327->1.316,Tallman.642->.653. Lgonchangedbaselineversusfirstcontrolledstudycomesfromverified-objectiveKOST; currentlive/storedv2unchanged. Eachmap/currentstored-data-v2 andallfeaturecontributionslisted. No historicalcorrections.

NEXT ACTION: preserve reports locally; investigate the K/D definition limitation READ-ONLY. Official UbisoftY6S3 notes explicitly distinguish the player earning DBNOkillcredit from the finisher shown in killfeed. This is a plausible currentY11 explanation for balancedteammatecounts, not yet an adjudicatedper-roundcause. Collect exactstableUIDscoreboardcounter evidence and/or officialVOD on oneconsumedSALexample; never substitute nearest-ID or lastscoreplayer, change kill/deathstats/runtimeRating, reopen final/refit or alteroldresults. Continue conservatively on data-quality evidence; operator/actionboundary untouched.86protectedhashes and both permanentfinalSHAsunchanged. NoDB/archive/public export writes/push/publish.

## CORRECTED-KOST SAL FINAL PERMANENTLY CONSUMED / GATE FAIL - 2026-10-02

Prospective quality checkpoint fb9636b; exact model freeze08bc193 unchanged. ONE evaluation `v3-corrected-final-sal-20261002T223637Z`:141cleanrows/18maps/10rosters/24objective-positive rows fromALL20prospectivelylinkedSALarchives/207rounds. Botharms fully objective-corrected KOST. Frozenv2MAE.04142214 ->v3.03496006 (15.60%relativeimprovement);RMSE.05538->.04957;medianAE.02905->.02226;maxAE.16479->.18693. Within.01 16.3%->27.0%,.02 33.3%->44.7%,.03 51.1%->59.6%,.05 71.6%->75.9%,.10 90.8%->94.3%. Required80%within.05 FAILS; all other coverage/accuracy gates pass. No deployment, gate relaxation or final-data refit. EntireSALevent permanently consumed for this candidate, including unavailable later maps which were outside fixed snapshot.

Permanent resultSHA25673b17d45f73cc7f07da5fc996bd9e1379017120d451e67c5e145ad1c1b9cbaa2. Report research/output/v3-corrected-final-sal-stage2.md; experiment log appended; consumption marker written before numerical Ratings. Both firstAPAC failedresultSHA and livev2historicalMAE.03623 unchanged. Corrected input cohort exclusions:8581VillaR06 and8588BorderR02 unknownbody; earlier narrative accidentally saidBorderR09, corrected here (stored normalized evidence/quality decision/seal always had correctR02). 45/47plants+7/7disables resolved, bothmaps excluded wholly; no parser/mapscorefailures. FullPython251/1skip/6subtests;86live hashes unchanged.

NEXT ACTION: local permanent result checkpoint, then consumed read-only objective-heavy/feature-contribution diagnostics and corrected-KOST UAH contribution report using only fully complete actor maps. Do not tune new coefficients/grid on the consumed final, change operator/kill/action logic, relax gates, writeSQLite/publicJSON/archive, push/publish or deploy. Unresolved seasonmaps show unavailable, never zero-fill. Continue useful compatibility/evidence work after milestone.

## SAL CORRECTED-KOST FINAL COHORT SEALED / RATINGS UNOPENED - 2026-10-02

All20 prospectively selected official SAL archives cached and parsed:207rounds,47plants45resolved/2unresolved,7disables7resolved. Eight exact-UUID aliases independently reviewed against profile histories and official roster members (officialGUID fields blank); prospective alias addendum sealed without changing model/parser/input/gates/source. Original unaliased decisions preserved. Terminal quality yields141cleanplayer-maprows/18maps/10rosters/24objective-positive rows; all coverage gates pass. Unresolved plants8581VillaR06 and8588BorderR02 exclude both entire maps. Remaining exactK/D mismatches retained, no eligibility relaxation. All target Rating values/error metrics and actor labels still unopened.

New research/v3_corrected_final_quality_seal.py checks every frozen per-round input equals fully objective-corrected normalized data, verified occurrence actor counts equal credited objectives, and all prediction/API/target/quality digests. Ignored prelabel-quality-seal.json records exact selected20archive cohort and86protected hashes before Rating read. Report research/output/v3-corrected-final-sal-prelabel-quality.md. Original model/dependency freeze08bc193 unchanged. FullPython251passed/1optionalskip/6subtests; only prior upstream/cache-permission warnings. Go/vet/web prior passing gates unchanged. NoDB/archive/publicJSON/runtimeRating/push/publish changes.

NEXT ACTION: local commit of sealed cohort, then ONE invocation `.venv/Scripts/python.exe research/v3_corrected_final_pipeline.py evaluate`; preserve permanent result whether gates pass/fail, never refit/relax using SAL. No automatic deployment. Original APAC final failure SHA c168c369a4c3f754f5a8376401e87a7857698907b6ebd79330cdd007e594afd2 and v2 historicalMAE.03623 remain unchanged. Continue safe evidence/reporting work after milestone.

## CORRECTED-KOST CANDIDATE / INDEPENDENT SAL FINAL FREEZE - 2026-10-02

Current HEAD08bc193; prospective reserve/pipeline6815dae, separate corrected-KOST development c5f148c/3032112. New genuinely separate South AmericaStage2 event, officialcompetition515/SiegeGG187,45group matches. Whole event reserved; fixed snapshot ALL20currently linked official archives, later25unavailable/ playoffs remain reserved outside fixed snapshot. Metadata-only schedule pairing; no SAL Rating/actor outcomes inspected before reserve/freeze. ChinaStage2 aggregate/individual Rating discovery exposure separately recorded, not claimed untouched.

Exact corrected-KOST candidate fromdevelopmentv3-corrected-kost-20261002T221833Z frozen before SALtargets. Botharms use fully objective-corrected KOST, Aexactv2weights,Bfixedraw9familyalpha1; objective slope.40723158. Coverage/accuracy gates prospectively frozen (100rows/10maps/6rosters/15objective-positive;MAE<=.035,>=5%pairedMAEimprovement,>=80%within.05,maxAE<=.20,RMSEnotworse). No production Rating/default change. Original APAC resultSHAc168c369a4c3f754f5a8376401e87a7857698907b6ebd79330cdd007e594afd2, failed75.6%gate and allfirst dependencies unchanged.

Small new SALpipeline proved:8580/6178TLA-INTZ Lair14rounds,5plants+1disable all actors resolved; exactdate/map/score/roster match;6cleanplayer rows,4exactK/D mismatches. AlltargetRatings/error metrics still unopened. New paths isolateddata/research/v3-corrected-final-sal-stage2, reserve/freeze/aliases/result files separate fromfirststudy. Two targeted distinct-storage/repeated-opening tests pass; previous247fullPython plus4newtests passed individually (expected251full). All86liveSQLite/archive/public hashes unchanged.

NEXT ACTION: incremental SALacquisition/label-freequality (first5in progress), then10/15/20usingcached script. Independently resolve UUID aliases if needed; record unsupported objectives/maps and K/D discrepancies. Seal all20predictions/quality plus prospective metadata evidence BEFORE one-shot evaluate. Never reuseoldAPACorNA/EMEA/CNdiscovery as untouched Rating. NoDB/public/archive writes, liveformula/default change,push/publish. Commands `.venv/Scripts/python.exe research/v3_corrected_final_pipeline.py quality --limit 5`, then10/15/20; evaluate once only after allselected sources finalizedandprospectivelysealed.

## SEPARATE CORRECTED-KOST DEVELOPMENT RESULT - 2026-10-02

Plan/code prospectively committed3032112 before one deliberate experiment `v3-corrected-kost-20261002T221833Z`. Same284train/22EWCdev clean objective-complete rows; seven other feature families/objective input unchanged, only verified-objective KOST definition corrected in BOTH arms. Exact original v2 weights A, same fixed raw nine-family ridge alpha1 B. No APAC or September final rows/errors used. Nine player-map KOST counts change (7train/2dev). Development MAE0.02605957 ->0.02133129; RMSE0.03376 ->0.02510; medianAE0.01993 ->0.01981; maxAE0.07020 ->0.04868; within.05 81.8%->100%. Positive objective raw coefficient0.40723158. All coefficient drift, KOST changes, heavy residuals in research/output/v3-corrected-kost-development.md. Small dev sample; different input contract means not directly attributing differences from first study solely to coefficients. Firstmodel/development/finalSHA and86live hashes unchanged; first final dependencies still verify.

NEXT ACTION: checkpoint this separate development result and find a genuinely new event using metadata only, then freeze candidate/input/quality/accuracy gates before new target errors. Do NOT reuse APAC North Stage2 or old NA/EMEA September as untouched. Candidate source discovery: a web search for ChinaStage2 returned aggregate event Rating leaderboard and individual player Rating snippets unexpectedly. No predictions/errors or model choice used them, but CNStage2 must NOT be described as labels-unseen; record this discovery exposure explicitly. Prefer South AmericaStage2 officialcompetition515 using metadata-only schedule projection; use SiegeGG schedule filter, not competition/player leaderboard pages. No runtime v3/default change, push/publish/historical corrections.

## POST-FINAL READ-ONLY DIAGNOSTICS / PRACTICAL INPUT LIMITATION - 2026-10-02

HEADcc6c49f preserves the failed final result. New research/output/v3-uah-readonly.md lists every tracked-player contribution on3complete maps/36rounds; KafeR09 unknown body and ChaletR10 nine-player roster make full-season v3 UNAVAILABLE, never zero-filled. Partial controlled v2->v3: Azooz.993->1.006,Dino.842->.839,Lgon1.321->1.342,Jay1.327->1.315,Tallman.642->.658. These are partial research predictions, not proposed deployment or changed live ratings. Per-feature centered drift and direct objective addition separated. All86protected hashes unchanged.

New consumed K/D audit:26issue incidences all have teamkills0, so none is a public-TK-count convention. Many are balanced +/-1 killer credits with identical deaths. Independent official Ubisoft8154 Clubhouse player totals confirm disputed public REC3,Wqsyo11,yuKiz7,FishLike6 versus replay2,10,8,7. No parser/kill-stat fix, no retroactive eligibility or frozen-metric revision. Official VOD link on8154 is empty; additional independent broadcast review would be needed to establish a specific bad kill packet. Record diagnostic as unresolved attribution discrepancy, not public-label error.

Practical v3 limitation: the first controlled experiment intentionally keeps original occurrence-free KOST. Actual live KOST includes verified objectives, so this frozen candidate's feature contract cannot silently be replaced by corrected KOST at deployment. The candidate already fails final gate and is not deployable. A separate development-only comparison using fully objective-corrected KOST in BOTH A/B arms is a directly related follow-up, with exact same feature family/fixed ridge and no unrelated feature search. Never use the consumed APAC final to tune it or call it fresh. New untouched event and freeze required for any future final candidate. Livev2 formula/default unchanged; ROOTREADME methodology clarified current actor support and retained objective/KOST behavior.

NEXT ACTION: checkpoint read-only reports, then investigate objective-corrected KOST development inputs as a separate logged experiment if useful. Keep both original v3 development/final records permanent, no refit on APAC final. Alternatively continue independent primary/VOD K/D diagnostics without changing engine. All new outputs separate ignored research paths. NoSQLite/public/archive writes/push/publish or historical corrections.

## V3 NEW FINAL EVENT PERMANENTLY CONSUMED / GATE FAIL - 2026-10-02

Starting clean quality-seal HEAD65e6400. One-shot experiment `v3-final-apac-n-20261002T220620Z` evaluated86 clean player-map rows /11maps /8rosters /15objective-positive rows from ALL12 prospectively linked APAC North Stage2 archives. Original freeze c80c62c and documented pre-label addenda unchanged. Every prediction/quality decision saved before first target Rating read; consumption marker saved before numerical outcomes. Event permanently consumed: never refit using it and call it untouched again.

Frozen v2 versus frozen v3: MAE0.04217228 ->0.03406317 (19.23% relative improvement); RMSE0.05699 ->0.04803; medianAE0.03177 ->0.02150; maxAE0.20680 ->0.16537. Within.01 15.1%->24.4%,.02 33.7%->47.7%,.03 47.7%->61.6%,.05 73.3%->75.6%,.10 91.9%->94.2%. Predeclared80% within.05 gate FAILS; every other gate passes. Preserve failure; no relaxed acceptance/no deployment. Report research/output/v3-final-apac-n-stage2.md; ignored one-shot-result.json/marker, appended experiment log. Livev2 historical finalMAE0.03623 remains unchanged; new-event baseline0.04217 is a different sample, not overwrite.

Final sample exclusions: one unresolved Chalet8163/R09 body excludes10rows;24additional exact K/D mismatches. 27/28 plants+3/3disables structurally resolved, no parser/score/map alignment failures. All11 aliases independently checked; no official populated GUID binding claimed. FullPython247passed/1optionalskip/6subtests; Go/vet/web passing gates remain unchanged.86live SQLite/archive/public hashes unchanged. No import/historical correction/public regeneration/push/publish/runtime Rating change.

NEXT ACTION: commit permanent final result before diagnostics. Then safe READ-ONLY exclusion audit (compare raw feedback, opponent-only kills/teamkill/suicide conventions with public K/D without changing engine or frozen gates), and UAH controlled v3 contribution report using only complete-actor maps; unresolved maps must show unavailable, never objective zero. No model refitting on consumed final data. Continue useful evidence/compatibility/checkpoint work; further v3 deployment requires user review and stronger independent evidence after failed gate.

## V3 FINAL QUALITY SEALED / RATINGS NOT YET OPENED - 2026-10-02

HEAD20fe7b0 base; reserve/model freeze c80c62c unchanged. All12 selected official APAC North Stage2 archives acquired incrementally and parsed:118rounds,120player-map rows,86clean from11maps/8rosters,15objective-positive clean rows. Plant actors27/28resolved,disables3/3. One Chalet8163/R09 timer_owner_body_unresolved excludes entire10player map. Other24rows exactK/D mismatches; total26 K/D issue incidences including2 on the unresolved map. No parser/alignment failures. Every current roster uniquely identified after11 independent exact-UUID username-history aliases plus official roster corroboration. Official UbisoftGUID roster fields blank, limitation explicit. No fuzzy/statistical identity guesses. Earlier decisions/registry versions remain in git/ignored caches.

All12 predictions and label-free quality decisions, archive/target digests and current alias registry are sealed before Rating values/errors. Report research/output/v3-final-apac-n-prelabel-quality.md; ignored prelabel-quality-seal.json. Derived objective counts exactly equal verified occurrence actors on every map, no legacy credits. Identical original eight inputs including occurrence-free KOST in both arms; only objective feature differs. Four coverage gates pass; accuracy gates NOT evaluated yet. Model/gates/parser untouched since freeze; documented pre-label implementation addenda only. FullPython247passed/1optional skip/6subtests; existing cache-permission and upstream TestClient warnings. EarlierGo/vet/web passed, unchanged.86protected local file hashes unchanged at every pipeline stage. NoSQLite/public/archive/livev2/push changes.

NEXT ACTION: locally commit quality seal/alias addendum6, then `.venv/Scripts/python.exe research/v3_final_pipeline.py evaluate` ONCE. It marks targets permanently consumed before first Rating float read and refuses repeat. Save permanent result/report/log; never retune and call APACNorthStage2 untouched again. No automatic v3 deployment regardless outcome; livev2 finalMAE0.03623 remains frozen. Continue safe diagnostics/read-only interpretation/checkpointing after final, not voluntary stop.

## NEW APAC NORTH V3 RESERVE / SMALL PIPELINE PROVED - 2026-10-02

Current local HEAD `1b50b0e` (following model freeze `c80c62c`, reserve/pipeline `c81898f`, development `116cb7a`). NEW event-wide reserve: official competition510, SiegeGG189, APAC North Stage2. All28 group matches reserved; fixed final evaluation snapshot is ALL12 currently linked official archives, earliest three used for small pipeline proof. Later16 unavailable matches and future playoffs remain reserved and excluded from this fixed snapshot. No archive chosen by objective presence/errors. Exact selected weights, original eight-input definition plus objectives, acceptance gates and dependencies frozen before new targets; no model refit. Original v2 final0.03623 unchanged.

First three archive proof: 8154/6200 Clubhouse8rounds0objectives;8155/6201 Fortress14rounds3plants all resolved;8156/6202 Nighthaven10rounds3plants all resolved. Date/map/score independently match target metadata. Fortress yields8clean player-map rows; two have exact K/D mismatch. Other maps currently excluded by unresolved identities; no fuzzy/statistical alias guess. Four UUID-bound username histories are corroborated by official SCARZ/KINOTROPE rosters (FishLike,yuKiz,Ayagator,gatorada). All Rating values/error metrics remain unopened.

Original freeze remains immutable. Explicit prospectively committed implementation addenda preserve the initial strict-format quality result, fix public K/D signed-differential formatting, retain unknown-killer team -1 on explicit Death during canonical team relabeling, and key quality caches by source plus alias manifest hashes. Parser/model/gameplay/acceptance unchanged. Initial wrong KIN source URL134 was corrected to319 after primary roster review BEFORE committing the alias seal; initial evidence table retained ignored. No Rating-based code changes. Nine targeted gates pass. Earlier240 full Python pass; expected245 after added gates. Go/vet/web unchanged since passing gates.

NEXT ACTION: continue chronological incremental acquisition/label-free quality (currently through first6 selected matches), independently review remaining UUID aliases, preserve every exclusion and terminal source state. Do NOT run final evaluation until ALL12 predictions/quality decisions are sealed and aliases/dependencies prospectively committed. Final command evaluates once and writes a consumption marker before first Rating read. If gates fail/too few clean rows, permanently record it, never refit and call this event untouched. No SQLite/public/archive modification, live v2 change, push/publish. Commands: `.venv/Scripts/python.exe research/v3_final_pipeline.py quality --limit 6`, then9/12 as cached; final `evaluate` only when gate prerequisites are ready.

## V3 FIRST DEVELOPMENT COMPARISON / DEFAULT PARSER INSTALLED — 2026-10-02

Base HEAD `f534b31`. The normal parser was installed through `scripts/install-parser.ps1` after preserving its old binary/source manifest under ignored `.local-tools/bin/actor-prepromotion-e7c2a2db6d0a7bb68013ab285ff859cb1ae27595a74e58901b3a95e82748f4d5/`. New normal binary SHA256 `e7f375b8ea0e1669bf6e6888d1aa4d93d51ac2ec2af7980c94f3698ff9def58a`; committed completing-owner implementation. Default-path Fortress preview accepted two verified plants without import. All 86 protected SQLite/archive/public hashes unchanged. Existing maps were NOT reparsed into SQLite.

Separate v3 derivation: 47 maps / 470 player-map rows / 306 clean rows, compared with 331 originally clean. Plants 105/110 resolved; disables 18/18 resolved; zero parser/alignment failures. Five plant abstentions exclude entire maps: 3905/7016 R03/R04/R06 missing body declaration; 4133/7860 R07 unknown Death offset; 6156/10426 R06 body unresolved. Original datasets remain unchanged. Full rederived KOST is reported separately; first controlled comparison keeps all eight original v2 inputs identical and adds only verified objectives.

Deliberate experiment `v3-objectives-20261002T213548Z`: fixed ridge alpha 1, train 284 (original v2 299), EWC development 22 (original 32). Development MAE 0.02949 -> 0.02345; RMSE 0.03770 -> 0.02762; median AE 0.02248 -> 0.01814; max AE 0.07923 -> 0.06072. Objective raw coefficient +0.47422249. All coefficient drift, thresholds and all nine objective-heavy residuals recorded in `research/output/v3-objective-first-development.md`. Candidate sample differs from original training; not all drift is caused by the feature. Development subset is small. No new final evaluation, live v2 remains frozen MAE 0.03623.

NEXT ACTION: checkpoint first v3 experiment, reserve a NEW event using metadata alone (official APAC Stage 2 APAC N competition 510 is a candidate), freeze the existing candidate, input rules, gates and dependencies before new Rating errors. Both old September final events are consumed and excluded. Prove a small new replay pipeline, then scale incrementally. Keep frozen actor original/reviewed comparisons separate. Do not run old `pipeline.py all/derive` because its new parser hash would overwrite original cached datasets. Reproduce separate derivation/fit with `research/v3_objective_derive.py` and `research/v3_objective_fit.py`; fit deduplicates existing experiment. No push/publish/DB/archive/public regeneration or live Rating change.

Verification at this checkpoint: 240 Python tests passed, one optional real replay test skipped, six subtests passed; cache write permission warning and upstream TestClient warning only. Earlier Go tests/vet and both web builds passed; no Go/web changes since those gates.

## GO ACTOR PORT / UAH READ-ONLY GATES PASS - 2026-10-02

BaseHEAD3057e34. Conservative Go completing-owner implementation: explicitUID/direct temporal slot/body/phase/terminal/occurrence/side guards; unknown evidence abstains. Python accepts only source+reason completing_timer_owner_v1, matching nonzero unique numericUID/full5v5 roster/correct side; normalized occurrence preserves actor key/UID/source/reason. Verified occurrence supersedes same-kind legacy timer feedback, no double-count. Completion clock unknown remains0.0. Reader call follows existing occurrence resolver; action-start/operator logic unchanged.

Full72physical folders/569consumed rounds: Go actors exactly match142plant+33disable research predictions; occurrence/fullfeedback/operator fields unchanged. First raw comparison had one damage stats variation4140/R10 Logan125/110 andRexen235/220. Four direct runs of UNCHANGED oldbinary reproduce both exactvariants; existing nearest-entity HP map/tie iteration is nondeterministic. No health/stats fix. Only exact independently reproduced variation is informational; first raw failure result retained separately. No other parity failure. Report output/objective-actor-go-parity.md.

UAH5maps/62rounds:17plants15resolved/2unresolved;3disables3resolved. KafeR09 Kenbot.USU has bodyvalues1->0;1 unverified, unresolved. ChaletR10 nine-playerroster unresolved. Tracked proposed plantsAzooz2,Dino2,Lgon2,Tallman4;Lgon disable1;Jay0. All20objective prior/proposed actors/confidence in output/uah-completer-readonly.md; nothing applied. Lgon original38 Attack unchanged:Zofia4,Striker4,Gridlock3,Ace2,Grim2,Deimos1,Sens1,Twitch1.86live file hashes/SQLitef3dc10210ab29f62e83317600e8bfcd55b1e6f17c6dbcaf0abf4556af55bef4e unchanged.

FullPython236passed/1optional skipped/6subtests;Go ./...tests/vet and both webbuilds pass(existing upstream warnings only). SeparateactorbinarySHA240d5db1963fcd8d76d954ef42f7ddd6be7f7d60b7ee8770255d94b69f20b66c. NEXT: checkpoint locally, preserveold defaultbinary/source manifest under ignoredtools, installcurrent source via install-parser.ps1 and verifyhash/livefiles. Then separatev3 dataset/experiment with exactv2 family+verifiedobjectives, developmentevents only. Keep olddatasets/frozenresults/livev2 unchanged; no historicalDB writes/publish/push. Newuntouched event required beforev3 final/deployment.

## CONSUMED STRUCTURAL COMPLETER AUDIT COMPLETE - 2026-10-02

Starting HEAD49da07b. New separate plant completer candidate plus unchanged frozenD disable rule on569 consumed physical rounds.146plants:142resolved/4unresolved, original140agree/2disagree/4unresolved; reviewed142agree/0disagree/4unresolved. The two disagreements are previously official-VOD-reviewed Aiden/Raid and kyno/Fultz.33disables:33resolved, original29agree/4disagree; reviewed33agree/0disagree. Four independently reviewed disable disputes are njr/J9O, handyy/VITAKING, Loira/Dias, Gunnar/Savage. Mixed-source reviewed comparisons are not all independent VOD truth. No known independently verified wrong credit.423objective-free rounds (including original230):0actor proposals.0occurrence/target mismatches. Kason canceled7->2.881 and7->6.694; completing Hotancold7->.015 receives sole proposed plant. Exact timers+UID+body+side+validated completion, no actor score threshold/proximity/label selection.

Plant abstentions:3905/7016 R03/R04/R06 have direct classa859ffff timer owners but missing known body declaration;4133/R07 unknown Death offset. No unknown-class/body fallback. Eight real reduced controls plus22synthetic tests pass. FullPython223passed/1optional skipped/6subtests.86protected live hashes and4immutable actor results unchanged. Report output/objective-completer-consumed-audit.md; rerun `.venv/Scripts/python.exe research/objective_completer_consumed_audit.py` cached.

NEXT ACTION: conservative Go production port of completing-owner rules with existing parser kill offsets, stableUID/temporal ownership and explicit episode lifecycles. Preserve frozenA/D sources/binaries and historic results. Build separate actor candidate binary, run reduced real/synthetic Go tests and full professional parity/negative audit before installing it. Then UAH read-only report each objective/prior stored actor/proposed correction; never DB write. Production decision: broad structural evidence plus separately reviewed September supports conservative implementation; runtime installation requires port parity. No v3 yet; deployedv2/SQLite/public/archive untouched, no push.

## SEPTEMBER DISAGREEMENT ADJUDICATED SEPARATELY - 2026-10-02

Starting HEAD87893de. 6170/10592/Villa physical R07 is classification B (external-label error): frozen timer Gunnar.M80; original public Savage. Official Ubisoft8285/game10622 has M80's sole Defuser win R07 and Gunnar995=1 disable; Savage1004=0, all other M80 players0. Direct UID10462818329288152675 owner4027874753/timer4028366850, state1 start47297207, terminal record47318609/property end47318627, 196 monotonic samples6.932->0, unique active body0. Final opposing killer is Gaveni, not Savage: earlier last-killer coincidence is not universal. Official Day1 VOD1TqU0qsLfDU small inset12245-12249 shows counter-defuse device/highlighted first M80 card; player cameras obscure completion. At12300 next round score3-4 confirms Defense win. Limits documented, no camera-subject actor inference.

Original September result remains5 agreements/1 disagreement/0 unresolved, failed original gate, SHA5296849e55ca07308db296d97e3e8c63796bac7b419e738b52f5f1bfe2c43275. Separate reviewed mixed-source comparison6/0/0; only disputed label independently adjudicated, not six independently visually verified actors. Report output/objective-disable-stage2-adjudication.md; reproduce `.venv/Scripts/python.exe research/objective_disable_stage2_adjudication.py`. All86 protected SQLite/archive/public hashes unchanged. Frozen9165678 rule unchanged. Latest user instructions release old mandatory Aiden abstention for future structural candidates; preserve Raid target and every historical frozen result/test as historical, not ground-truth correctness.

NEXT ACTION: separate consumed structural plant-completer candidate and broad full interaction audit alongside unchanged frozenD disable rule. Check explicit phase0 completed episode -> verified plant anchor -> unique attacker UID/body, canceled/restarted episodes, Kason/Hotancold, unknown routes, 230 objective-free negatives. Compare original labels and separate Aiden/kyno/disable adjudications. Evaluate true known wrong credits and independent evidence before production. No live v2/SQLite/archive/public changes; no v3 until trusted actors; no push.

## SEPTEMBER DISABLE-ONLY IMMUTABLE RESULT - 2026-10-02

Frozen cleanHEAD9165678; ALL67replay predictions saved before publicdisable actor text.7maps/build9883691 have6public disables:5correct,1primaryincorrect,0unresolved;0occurrence mismatches. Predeclared research gate FAILS due primarywrong actor. This set is nowCONSUMED for this evaluation; never retune and call itfresh. Permanent resultSHA2565296849e55ca07308db296d97e3e8c63796bac7b419e738b52f5f1bfe2c43275; ignoredobjective-disable-stage2-validation/result.json and trackedobjective-disable-stage2-validation.md.86protectedSQLite/archive/public SHA and3priorimmutable resultSHAunchanged. NoRating/live-data/import/archive/push changes.

NEXT ACTION: record permanent result locally BEFORE inspectingwrong event. Then investigate actualwrong timerowner identity, directbodyroute, orderedkills/phase/terminal, publiclabel versus independentprimaryUbisoft/VOD evidence. Keepfrozen9165678candidateexactlyunchanged, preserveprimary5/1result regardlessreview. If realactorerror, prioritizeabstention/safetythennewuntoucheddatasetfreeze; if labeldisagreement, documentreviewseparatelyandacquireadditionalindependentactorvalidation, notautomaticproduction/v3. Mandatory4139plant remainsunsupported/unresolved andoriginalAcontrolunchanged. Continueusefulworkaftercommit.

## SEPTEMBER DISABLE-ONLY RESERVE / FREEZE GATE - 2026-10-02

HEADa39c466 preserves502round consumed D hypothesis and primary24agree/3disagree. New metadata-only reservation selectsALL7cached NorthAmericaStage2 maps(6168,6169,6170,6172,6173,6174,6175),67complete rounds,build9883691; exact contiguous physicalR##/scores/rosters/aliases andSHAchecked. No new disable actor labels/owner proposals inspected. PriorRatingdata andlimited objective totals already consumed, so actor-label independence only. All7selected without objective/outcome selection. No download.

Candidate/adapter/spec/acceptance tests complete. FullPython199passed/1optional skipped/6subtests; GoDissecttests andgovetpassed, noGo/runtime changes. Predeclared research gate5correct names>=3maps,0primary wrong/identityunknown,0occurrence errors; allabstain/too few insufficient. Every primary disagreement retained regardless later source review. Freeze all existing research Python/transitive helpers, fourexecutables, manifest/spec/fixtures/tests, verify original A hashes. NEXT commit LOCALfreeze with clean tree; then `.venv/Scripts/python.exe research/objective_disable_stage2_validation.py`. SaveALL67predictions before first publicdisable actor text. Immutable completedresult must be recorded locally before analysis. Stage2candidate names never appliedtoSQLite/public. No v3/production/push; mandatory4139plant remainsunsupported/unresolved; originalA/J9Ocontrolunresolved.

## DISABLE-ONLY CONSUMED HYPOTHESIS COMPLETE - 2026-10-02

HEAD9aafb0f.502distinct consumed physical rounds: original291,179completed rounds from3consumedreserves and32extra consumed extension positive rounds.27public disable rounds all receive UNFROZEN proposals;475rounds without public disable receive0proposals. Primary public alignment24agree/3disagree,0abstain. Disagreements:SI5932FortressR17handyy versusVITAKING;3563BankR02njr versusJ9O;6157BankR01Loira versusDias. Separate official Ubisoft map totals+Defuser round methods support all3proposed owners, but primary outcomes preserved. In all3the primary label names last opposing killer, independently distinct from timer owner; observation does not establish external site's implementation. No confidently accepted historical actor or runtime change.

Nine reduced real selector controls plus19synthetic tests pass(21tests total), including SI literal clears, old global0 omission, body sharing/replacement/unknown/death/disconnect veto, two canceled nearzero plants and unsupported mandatory4139plant. Fixture has no rawrec/dump/profileUUID/private path; UIDs ordinalized, temporal slot histories retained. Original A/B and all3immutable results untouched;86protected files unchanged. No Rating or live-data modifications.

NEXT ACTION: preserve this local consumed checkpoint. Prospectively reserve ALL7cached NorthAmericaStage2 maps for actor-only validation if folder/label provenance confirms they were not actor-graded. Their Rating targets were previously consumed; therefore independent only for NEW actor labels, not event-disjoint Rating. Do not access roundactor labels or new proposed ownership while reserving metadata. Complete specification/acceptance rule and freeze allcandidate dependencies+tests LOCALLY with clean tree before one-shot predictions, then labels. If none or too few disables, record insufficient evidence and continue useful consumed compatibility/source work. Do not automatically promote production/v3. Mandatory4139remains unsupported/unresolved; oldJ9Ocontrol stays unresolved inoriginalA, new njr observation has independent primary evidence separately documented.

## IN PROGRESS: CONSUMED DISABLE-OWNER HYPOTHESIS - 2026-10-02

HEAD9aafb0f. Separate UNFROZEN disable-only candidate does not alter plants, A, runtime or live data. Uses existing occurrence-only Bomb+verified plant+unambiguous Defense score increment; unique temporal UID/timer state1 ownership; full monotonic timer; explicit terminal2 OR literal exact owner/slot clear; no competing/later/unbound evidence; no death/disconnect ambiguity; known body slot/class/state0/2 throughout. Terminal record start is not the last property: exact observed terminal property end used.19synthetic eligibility/identity/phase/clear/negative tests pass. Original mandatory controls remain unchanged/unresolved; new proposals are NOT confident credits.

LONG JOB: `.venv/Scripts/python.exe research/objective_disable_owner_consumed.py`. Entire consumed291round cohort plus completed physical files from three permanently consumed reserves, plus remaining consumed extension positive rounds; SHA verifies original included files and protects original results+86local files. No new labels or downloads. Replay proposals saved separately before consumed comparison. NEXT: inspect every abstention/disagreement, compare reviewed official constraints separately, never rewrite primary results. Then add reduced real-input tests and determine whether further unused actor reserve can be prospectively selected. No push/production/v3/live changes.

## SI TEARDOWN / INDEPENDENT DISABLE LABEL REVIEW - 2026-10-02

HEAD3d312c6. Eight consumed lifecycle controls completed. SI5931BankR03(kds) and5932FortressR17(handyy) have directly UID-bound state1 timers reaching0.002/0.012, then literal slot27c clear(component0,class00000000), with no terminal state2/global0. Each has verified prior plant1 and an independently unambiguous Defense score increment. Old3073/R08 lacks global0 but does have player terminal2. Three negative nearzero plants have Attack winners/no globalplant. Clear/state2/nearzero alone cannot establish completion. No actor credit or original A change.

Primary Ubisoft cached __NEXT_DATA__ for consumed9026Bank,7740Bank/Fortress,9070Bank plus official website enum bundle explicitly Defuser=3 independently constrain labels:9026BankR02njr(1),R10Spoit(1);7740BankR03Kds(1),FortressR17Handyy(1);9070BankR01/R04Loira(2),Dias0. Complete one-based round identity, teams/roles, score and objective totals checked. This is inferred from map totals+round methods, not a direct per-round player field; roundsStats is side aggregates. Pipeline measurement independence is unknown. Original SiegeGG targets and every primary result preserved; mandatory J9O/njr and Raid/Aiden remain unresolved in unchanged diagnostics. Optional Raid/Aiden user clarification is still pending, no reply/permission inferred.

Official VOD samples for disputedBankR02 and bothSI disables cut to player/stage camera before counter-defuse HUD/completion, so no visual actor confirmation claimed. Reports objective-timer-lifecycle-comparison.md and objective-official-disable-review.md. Seven new source-review ambiguity/inconsistency tests pass after fixing research test import path; initial collection error was not app failure.86protected SQLite/archive/public SHA unchanged. Rating/live parser/public/archives untouched, no push.

NEXT ACTION: checkpoint research locally, then define a separate consumed disable-owner hypothesis using EXISTING occurrence-only Bomb+plant+Defense score evidence. Require temporal unique numeric UID ownership, correct phase/role, explicit complete timer run, no player death/disconnect ambiguity, no competing runs. Investigate terminal slot-clear versus state2 structurally; do not change plants or mandatory controls. Check all consumed objective-free rounds and full positive cohort before any freeze or fresh labels. Keep original A/B, original labels/results and action-start/rating unchanged. No production promotion/v3 until independent fresh validation supports trust.

## CONSUMED TIMER CROSS-BUILD OBSERVATIONS / DISABLE REVIEW - 2026-10-02

HEADe68b988 preserved the direct-ownership/negative-control milestone. New43-event observer on the3ALREADY CONSUMED validation sets: first reserve plant5public-label agreements/3unresolved,disable2agreements; SI13plant agreements/2missing disable anchors; six-map plants14agreements/1disagreement(kyno/Fultz,previouslyVOD-reviewed),disables2agreements/1disagreement(Loira/Dias). These are packet-owner alignment counts, NOT new actor accuracy. Actors always null. All3immutable validation SHA and86protected SQLite/archive/public SHA unchanged. Missing scoreboard identity and direct timer identity are distinct. Five new association tests pass, including no anchor, role conflict, multiple completed runs and incomplete attempts; cache access serialized per physical round.

Build9734089/game7016 timer slot27c08dca has literal declaration classa859ffff versusdefaultb2216bf3. Separate isolated research-module instance recovers physicalR03dfuzr,R04Ashn,R06dfuzr complete runs and checksall12consumed rounds;9negative rounds have no completion-like runs. Default observer/frozenA/class allowlists unchanged. Reportobjective-timer-class-variant.md. Do not promote an unknown-class fallback.

Independent official grand-final VODeZiDda6eM6E BankR01 frames298.50/298.75/299.25 explicitly show LoiraDEMON Counter-Defusing while Dias kills last attacker kds and remains active. Completion cuts to stage at299.50, so report limits independent evidence to visible interaction plus laterFUR1-0 and officialUbisoft9070 BankLoira2objectives/Dias0. Preserve original public Dias label/disagreement and earlierA disable abstention. Initial ytsearch returned wrong FaZe/Liquid quarterfinalmetadata; it was retained separately and none of its frames used. Reportobjective-bank-disable-vod-review.md. Both mandatoryRaid/Aiden andJ9O/njr controls remain unresolved.

NEXT ACTION: inspect the two consumedSI disable component lifecycles:5931BanklogicalR03(kds) and5932FortressR17(handyy) have direct state1 nearzero timers but no terminal2/global state0. They end at a slot-declaration boundary. Determine literal clear/replacement and ordered kill/state/clock evidence, comparing old3073R08 and three negative controls; never make missing terminal/unknown liveness a guessed completion. Commands: `.venv/Scripts/python.exe research/objective_timer_consumed_extensions.py` cached43event observer; `.venv/Scripts/python.exe research/objective_timer_class_variant_observation.py` cached12round variant. No candidate promotion/v3/SQLite/archive/public/v2 modifications or push. Continue useful research after local checkpoint.

## TIMER COMPONENT STATE / NEGATIVE CONTROLS COMPLETE - 2026-10-02

StartingHEAD2d574ff. Research-only direct timer owner ledger:112/113 consumed spans unique; one4150/R11 mixed. Existing public label alignment is development only: original plants59agree/1disagree(Aiden versusRaid)/1mixed,disables7agree; extension plants32agree/1disagree(same4139control),disables11agree/1disagree(njr versusJ9O). Missing completion anchors are outside this ledger, not silently resolved. Every actor remains null and original labels/results unchanged.

Explicit timer component state records split93physical objective-bearing rounds into158attempts:122state0,36state1; all terminate2, all timers monotonic. Of those,93plant-like+20disable-like runs reach near zero;45are partial cancellations. State2 is NOT completion: the230previously consumed objective-free rounds yield93attempts on68rounds,65state2terminals/28ownership-declaration boundaries,including2false completion-like runs(4138/R09,4141/R14). In both, all five opposing kills precede the final timer sample; global objective flags remain absent.4141/R06 clears its slot before final opponent death. Preserve validated occurrence gate, not timer-only or state2-only logic. OriginalA untouched.

4150/R11 now separates two canceled Kason runs(7->2.881 and7->6.694) and Hotancold(7->0.015), without byte gaps or label-guided thresholds. Explicit timer fields occur both as first property and0x22continuation; the old feedback listener only observes continuations, so full state-run samples exceed old span counts. No low-level kill/operator/production changes. Eight reduced public-safe structural fixtures preserve these cases;13new targeted tests pass. Full Python163passed/1optional skipped/6subtests; only existing Starlette httpx deprecation warning with cacheprovider disabled. Every original frozenA dependency hash matches. Full protected SQLite hash unchangedf3dc10210ab29f62e83317600e8bfcd55b1e6f17c6dbcaf0abf4556af55bef4e. Ignored cached negative jobs are resumable.

NEXT ACTION: locally preserve this state/negative-control checkpoint, then inspect the same direct timer-slot grammar on already CONSUMED first reserve, SI and six-map cached cohorts. No fresh validation claims or retroactive result corrections. Verify phase/side, canceled attempts and temporal identity before any revised frozen candidate. Both mandatory4139Raid/Aiden and3563BankR02J9O/njr remain actor-unresolved. Independent VOD contradictions remain separate reviewed evidence. No production actors, v3 fit, SQLite/archive/public/v2 edits or push.

## DIRECT TIMER COMPONENT OWNERSHIP / NEW VOD CONTRADICTION - 2026-10-02

HEAD2d574ff. Full Python150passed/1skipped/6subtests after independent Chalet review+UAH read-only report. New research observer objective_player_component_fields.py reads direct typed UID owners and temporal slot declarations. Unknown-owner sharing rejects a join; old cleared/replaced slot components are not unioned. Known name strings are text, not numeric width4/8. Four targeted observer tests pass. No original frozen dependency changed.

Structural discovery: ASCII defuser timer taga9c858d9 occurs as a 0x22 continuation inside an explicit 0x23 component property record. Direct temporal slot27c08dca/classb2216bf3 links timer component to numeric UID owner. Four consumed controls bind every sample:4139R07=Aiden.SSG143;3563BankR02disable=njr105;BankR10disable=Spoit105;3554ChaletR04plant=kyno104. These are PACKET OWNER OBSERVATIONS, no actor credit. Binary progressfielde9a37feb changes throughout the timer; statee58c06e9 changes to2 near completion, pending semantics. No proximity window or score join.

Independent official VOD sQNarwuswkg FortressR07 frame1963/action0:38 explicitly shows Aiden.SSG Planting the Defuser while Raid.SSG is active separately atEXT Hammam Roof;1967 postplant44.80;1970 Aiden dies and Raid becomes sole attacker. This contradicts prior Raid public target. User's hard required control STILL UNRESOLVED, never confident Aiden. No target or earlier result revised. Separate report objective-fortress-vod-review.md; review is necessary before changing that requirement. J9O/njr remains independently unverified.

NEXT LONG JOB: examine direct timer ownership across all CONSUMED original+extension interaction records, then interrupted timers/non-objective controls. Cache by parser/replay/observer hashes. This is semantic discovery, not a new resolver or fresh validation. Keep A, B hypothesis and all three immutable validation results unchanged. No production actors/v3/SQLite/archive/public/v2 changes or push.

## READ-ONLY UAH GUARDED EVIDENCE COMPLETE - 2026-10-02

Frozen A on five private archives/62rounds:17plants13named/4unresolved,3disables1named/2unresolved. These are predictions, not independently labeled accuracy. Tracked candidate plants:AzoozNewzz2,DinoFireKing2,Lgon1,Tallman3.14=4,OhWowJay0. Sole disable candidate is untracked opponent ormeek.UMich,Border076d2b6b02bc/R06. Historical actor rows are context only, many role-impossible. No historical corrections applied. SQLite/archive/public86file SHA snapshots identical; DB hash stillf3dc10210ab29f62e83317600e8bfcd55b1e6f17c6dbcaf0abf4556af55bef4e. Initial report failed only because Windows relative path keys used backslashes; as_posix fixed it and cached rerun completed without reparse.27targeted Python tests pass including broadcast-reviewed Chalet fixture; original six actor-control fixtures and frozen code unchanged.

NEXT ACTION: preserve independent VOD and UAH reports locally. Investigate declared player component fields during verified full objective interactions on CONSUMED controls, especially unresolved disables and score-causality controls. Use explicit typed UID/component declarations, no numeric proximity/drone links, no target-guided score thresholds. This may identify an interaction state instead of attributing scores by timing. Keep experimental observers separate from frozen A. Do not promote production actors or fit v3 yet; no SQLite/public/archive/v2 changes or push.

## IN PROGRESS - READ-ONLY UAH GUARDED EVIDENCE - 2026-10-02

HEAD91594f3. Independent official broadcast review supports kyno, while immutable primary result still records disagreement with Fultz public label. LONG JOB `.venv/Scripts/python.exe research/uah_guarded_actor_readonly.py`: frozen A on five private map archives, exact source manifest physical/logical mapping and SHA checks; SQLite mode=ro; before/after digests protect every archive file, SQLite and public JSON. Research caches only. Output uah-guarded-actor-readonly.md plus ignored detailed JSON. NEXT: inspect compatibility/abstention causes, not historical actor truth. Preserve original actor result and add reduced public Chalet regression. No production actor implementation/v3/refit/push or local-data writes.

## INDEPENDENT BROADCAST RESOLVES PLANT TARGET CONTRADICTION - 2026-10-02

HEAD91594f3 permanently records primary cached reserve plants10correct/1wrong/4unresolved,disables0/0/3. Subsequent official VOD ISlfYfpK4Tw/ChaletR04 independently shows kyno's card explicitly Planting the Defuser at8817(action1:22) and8822(1:17), followed by completed plant at8824(postplant44.67). Fultz's separate card is active/Twitch, not planting. This supports frozen replay candidate kyno and contradicts public Fultz label. Immutable primary grading, raw target and actor code UNCHANGED. Secondary reviewed evidence only; never erase the originally recorded disagreement. Full packet ledger and review in output/objective-cached-false-credit.md and objective-cached-vod-review.md. Both mandatory Raid/Aiden and J9O/njr controls remain unresolved.

NEXT: locally preserve this independent review, then produce a read-only UAH guarded candidate report using exact stored map/archive identities. No SQLite/archive/public changes or production actor credit. Fourteen named plant predictions and one disable prediction across three new sets are still limited; all-abstain SI result gives no accuracy evidence. Continue consumed build/interaction/score-causality controls and additional actor validation before production or v3. No push or refit.

## SIX CACHED ACTOR MAPS PERMANENT RESULT - 2026-10-02

Frozen candidate A from cd28f76 evaluated unchanged at clean commit10cfecf on six cached maps/61 rounds. Plants10correct/1wrong/4unresolved; disables0correct/0wrong/3unresolved; zero occurrence mismatches. All11 named plant predictions used standalone_clock_with_body_guard. All predictions preceded actor labels. The wrong plant is 3554/6679/Chalet/logicalR04: candidate kyno, public Fultz. Permanent result data/research/diagnostics/objective-cached-map-validation/result.json and tracked output/objective-cached-map-validation.md. This actor set is now CONSUMED and cannot be independent validation again.

NEXT ACTION: locally record the complete frozen result before analysis, then reconstruct the wrong round's ordered score/clock/body/death/timer evidence and identity declarations. Determine whether identity, delayed/gadget scoring, interaction association or public label is responsible. Do not retune a score threshold to force the answer. Original A, prior immutable outcomes and sole wrapper B remain unchanged. Do not implement production actor credit or v3 based on these results. SQLite/archive/public/live siege_style_v2 untouched; no push.

## SIX CACHED ACTOR MAPS FREEZE GATE - 2026-10-02

HEAD4b839ba. Metadata-reserved6maps/61completed rounds in objective-cached-map-reserve.json:3554Bank10/Chalet8;3563Chalet9;6156Nighthaven10;6157Bank10/Fortress14. Twelve physical segments,5incomplete rounds excluded by unique score increment; exact public roster IDs and prior verified aliases confirm continuous global score chronology and final score. All61replaySHA256recorded. No download. Public actor labels ungraded; earlier K/D/multikill/occurrence use explicitly documented. These are new actor targets inside studied SLC/EWC events, not untouched event-disjoint Rating data.

Next locally freeze objective_cached_map_validation.py/objective-cached-map-freeze.json after checking original dependency hashes. This adapter uses original cd28f76 candidate A only; new independent-sole wrapper B remains UNFROZEN and is not imported. Only metadata/cache/report paths, alias source records and replay SHA verification differ. NEXT LONG COMMAND after commit/clean tree: `.venv/Scripts/python.exe research/objective_cached_map_validation.py`. Record all61predictions before labels and immutable full result before analysis. Then assess read-only UAH evidence if useful named-actor accuracy is supported; no live data changes, default changes, Rating fits or push.

## SCORELESS SOLE HYPOTHESIS / NEXT CACHED ACTOR SET - 2026-10-02

HEAD4410201. SI abstention diagnosis:13incomplete_score_identity,2missing_completion_anchor. Body identity is complete; two inspected UID-declaration graphs have no direct score slot/counter component join. Never guess legacy score identity. New UNFROZEN wrapper objective_independent_sole_candidate.py changes only the shared missing-score prerequisite: sole mode may use independently complete declared body UID/death/timer evidence without scoreboard identity. All other outcomes delegate to frozen A unchanged. Consumed affected original2plants remain unresolved; consumed SI13plants yield1correct(Adrian,BanklogicalR06),0wrong,12unresolved. These are development outcomes, never retroactive fresh-result corrections.39targeted tests pass. No health class allowlist/score threshold changed; state3 cannot exclude teammates.

NEXT: preserve this hypothesis locally, then prepare a further cached-map validation of the UNCHANGED cd28f76 candidate A. Metadata confirms unused actor maps exist in already-downloaded SLC/EWC archives:3554Bank6678/Chalet6679;3563splitChalet6674;6156splitNighthaven10424;6157splitBank10427/Fortress10429. Source maps and original actor-timer prefixes show these actor labels were not graded; some K/D/multikill/occurrence metadata was previously used, so this is fresh actor evidence only, not wholly untouched Rating/event data. Public objective actors remain unread. Reserve all six maps by completed score/roster chronology before any outcome inspection; no download needed. Keep B unfrozen and uninvolved in those predictions. No SQLite/archive/public/v2 writes or push.

## SI ACTOR EXTENSION PERMANENT RESULT - 2026-10-02

Freeze10531e4 preserved cd28f76 actor rule unchanged. Four SI-final maps58completed rounds evaluated once;13plants =0correct/0wrong/13unresolved;2disables =0/0/2unresolved. Zero occurrence mismatches. All replay predictions preceded labels. Permanent ignored diagnostics/objective-si-final-validation/result.json and tracked research/output/objective-si-final-validation.md. The SI series is now CONSUMED. No retuning or data correction occurred. All-abstain validation cannot establish resolved-actor accuracy; this is a compatibility/coverage limitation requiring diagnosis.

Across the two newly opened sets:23plants/4disables,only3plant actors+1disable actor resolved,zero wrong. This is insufficient broad actor evidence for production implementation or v3 fitting. NEXT: record result locally, inspect exact SI abstention reasons and declaration/UID/state differences with old consumed NIP SI and the new class-variant control; preserve both immutable frozen results. Investigate replay-structural reasons before any new candidate class rule, and obtain another unused validation set for any revised diagnostic. UAH stays read-only; no SQLite/archive/public/live v2 modification or push.

## SI ACTOR EXTENSION FREEZE GATE - 2026-10-02

Four unused SI-final maps reserved in research/objective-si-final-reserve.json:5930Consulate11rounds,5931Bank9,5932Fortress20,5933Border18,total58completed. Consulate rehost global score chronology verified by exact five-player team rosters; first segmentR07 has no unique score increment and is excluded. All58physical replay hashes recorded. Build9486312. Actor labels still UNREAD; only official/map/score/roster metadata inspected. Aliases match public ign/stylized names or prior sources.json; cyberzera=104 comes from previously verified match3554, not leftover-player inference.

New adapter objective_si_final_validation.py reuses frozen cd28f76 candidate and evidence helpers unchanged; only separate manifest/cache/report paths,3173alias source metadata and exact replay digest checking differ. objective-si-final-freeze.json includes original dependency hashes plus new adapter/reserve.34targeted regressions pass; Python helpers compile. Separate class-variant observer full feedback now also matches original helper for all3consumed rounds. No candidate allowlist added.

NEXT LONG COMMAND, after local metadata/adapter freeze commit and clean status: `.venv/Scripts/python.exe research/objective_si_final_validation.py`. Save all58predictions before actor labels; one-shot immutable result in ignored diagnostics/objective-si-final-validation, tracked report research/output/objective-si-final-validation.md. This series is unused actor evidence within the already studied SI event, not a new untouched Rating event. Record complete result before examining errors/retuning. If clean useful coverage, perform read-only UAH evidence evaluation; do not modify historical data or deployed v2. No push.

## IN PROGRESS - UNUSED SI SERIES METADATA / CLASS VARIANT - 2026-10-02

HEADa72fdff. First reserve permanently recorded before follow-up. Three build9734089 abstentions have direct health slot4154dcc4 but classb529300b, not frozen0c98c63f. Separate generated ignored helper observed30player paths in3consumed rounds;22of23death envelopes have priorstate4,one prior2. Frozen helper/candidate unchanged; no allowlist promoted or retroactive result changes. Reports objective-reserve-followup.md and objective-health-class-variant.md.

New unused series acquired from official Ubisoft match7740: SI26_DAY11_FAZEvSECRET.zip,648044851bytes,CRCverified and safely extracted under ignored data/research/extracted/actor-si-final-2026-02-15. Source URL/provenance cached in diagnostics/si-final-acquisition. Official metadata: Six Invitational final3173 on SiegeGG;Consulate7-4,Bank7-2,Fortress9-11,Border10-8. Public actor labels remain UNREAD. No Rating target fitting. Two Consulate physical folders require completion/score-confirmed rehost mapping.

NEXT LONG COMMAND `.venv/Scripts/python.exe research/prepare_actor_si_reserve.py`: cache public metadata IDs/roster only, parse/cache the5physical folders, print only map/score/roster/build/completed-round metadata, never actor labels. Next create a predeclared separate actor reserve manifest and validation adapter for the UNCHANGED cd28f76 candidate. Do not modify candidate to accommodate new classes before an independently frozen validation plan. Use cached ZIP/raw results; no redownload/reparse unchanged inputs. SQLite/archive/public/v2 untouched, no push.

## FROZEN COMBINED RESERVE RESULT - 2026-10-02

Local freeze cd28f76 evaluated once unchanged on the five-map60-round reserve. All replay predictions saved before actor labels. Plants3correct/0wrong/5unresolved (3standalone_clock_with_body_guard); disables1correct/0wrong/1unresolved (1sole_proven_survivor_throughout_interaction). All8plants/2disables detected,zero occurrence mismatches. Permanent ignored result: data/research/diagnostics/objective-combined-reserve/result.json; tracked report: research/output/objective-combined-reserve.md. Run ledger completed_immutable_result; rerun only prints the existing result. Reserve is now CONSUMED, regardless of its original manifest's historical reserved status. Candidate and frozen dependencies unchanged; no retuning during validation.

NEXT ACTION: record this result locally, then audit metadata/provenance for additional distinct, unused actor validation events. Keep the same frozen actor logic; do not call the ten consumed events independent again. The four resolved events have no errors, but sample and coverage are too small for broad production implementation or v3 fitting. Inspect abstention reasons only as consumed supporting evidence, without threshold tuning. The J9O/njr contradiction remains unexplained, so team-relative-only disable scoring stays forbidden. SQLite/archive/public/live siege_style_v2 unchanged; no push.

## COMBINED ACTOR DIAGNOSTIC FREEZE GATE - 2026-10-02

Starting HEADdc14b1c. Conservative combined research candidate fully specified in research/objective-combined-plan.md and dependency-hashed in objective-combined-freeze.json. Consumed original plants39/0/22,disables1/0/7; extension plants25/0/7,disables3/0/9 (correct/wrong/unresolved). Original modes37standalone+1sole+1agreement;extension21standalone+2sole+2agreement. All4disables sole mode. Both mandatory disputed controls unresolved; later actor/teammate kill cases remain Hotancold.100T. No team-relative-only selector. Unknown death offsets, PlayerLeave, missing/reused identity, ambiguous body state or conflicting evidence abstain. State2 is active-capable, not excluded as DBNO; no state3 hard exclusion or guessed revive handling.

Verification: full Python144passed/1optional skipped/6subtests;34targeted actor regressions passed. Go dissect tests,vet and research component decoder tests passed. First targeted invocation referenced a nonexistent liveness test filename, corrected to test_objective_liveness_research.py. Initial fixture expected Hotancold.SSG instead of actual replay username Hotancold.100T; fixed the fixture, not parser/candidate. No production/UI/data modification.

NEXT LONG JOB, only after local freeze commit and clean git status: `.venv/Scripts/python.exe research/objective_combined_reserve.py`. Adapter first records all60replay predictions across5rehost maps, then durably marks labels opened and grades8plants/2disables exactly once. Completed output immutable; interrupted run resumes unchanged cached evidence. Fresh reserve currently remains SEALED until this command reaches its label-opening phase. Permanent result goes under ignored diagnostics/objective-combined-reserve/result.json and tracked research/output/objective-combined-reserve.md. Next record result locally; inspect any wrong actors only after the full result is saved. Even zero wrong on10events is too small for broad production confidence; obtain another distinct unused actor set before changing runtime credit. Do not retune and call reused reserve independent. SQLite/archive/public/deployed siege_style_v2 untouched.

## DECLARED BODY STATE AND DISABLE WAVE CHECKPOINT - 2026-10-02

All93 consumed physical rounds scanned and cached; all930 player-rounds have direct typed UID -> declared health component paths. Every observer feedback list matches the existing parser. Five control death checks:36 zero HP before death,7 positive/missing HP; HP cannot be a death filter. Raw state e788f6a5: independent HUD33states =10active/state0,20dead/state4,3active/state2. The official Nighthaven broadcast shows Canadian aiming/reloading while state2 persists. Do not treat state2 as DBNO/dead. Brief downed icons align qualitatively with state3 intervals, but exact within-second alignment, revives and disconnect timing remain unproven. Full930 state transition ledger cached;343 player-rounds have action state2/3 transitions.

Consumed20disables:14 multiple not eliminated,5 sole not eliminated/state0 at completion,1 old missing completion anchor. Extending the descriptive score interval from completion epoch through the immediately following distinct clock epoch captures split terminal rewards:18/19 anchored disables have a common wave plus one +100 excess;3880 has nonuniform large rewards. This remains observational and unsafe as an actor selector:3563/6675/R02 still points at njr while the public actor is J9O, both state0. The five completion-only sole cases are not all sole throughout the full interaction.

New research-only sources: state_component_probe.go/tests, objective_state_components.py, objective_health_validation.py, objective_state_hud_audit.py, objective_body_transitions.py and objective_disable_structure.py; corresponding reports in research/output. All93 caches reusable; do not rescan unchanged binaries. Targeted Go primitive/continuation tests and vet passed. NEXT ACTION: specify one conservative combined diagnostic using the existing standalone clock plant mode plus sole-survivor-throughout-timer evidence, explicit declared identity/body-state checks, unknown-state abstention, whole-round PlayerLeave veto and disagreement abstention. Never enable team-relative disable credit alone. Evaluate consumed data and targeted regressions before any local freeze. Fresh reserve remains SEALED; no SQLite/archive/public/v2 changes or push.

## IN PROGRESS - DECLARED HEALTH/LIFE STATE EXPANSION - 2026-10-02

HEAD37ee1f3. New direct declaration path links all ten typed player UID entities to health components in five consumed controls, slot4154dcc4/class0c98c63f. Numeric distance/drone joins unused. Health alone is unsafe: seven of43 confirmed deaths retained positive HP. Component fielde788f6a5 carries0/2/3/4; state4 before40kills and2 before3kills. Independent action HUD audit:30states =10active/state0 and20dead/state4, zero mismatches. State2/3 DBNO/revive semantics still unknown; no actor exclusion implemented. New generic typed-record observer captures continuation state fields and preserves parser feedback parity.

Next long run `.venv/Scripts/python.exe research/objective_state_components.py --all-consumed` caches declared identities and health states across93 already-consumed objective-bearing rounds. Fresh reserve remains sealed. Next assess identity completeness, state-at-objective and transition patterns by build, then disable clock batches. No actor freeze, runtime/stat/public/SQLite/archive/v2 modification. Reproduction of controls: objective_state_components.py, objective_health_validation.py, objective_state_hud_audit.py. Run targeted Go component decoder tests/vet after scan; no need to rerun unchanged frontend tests.

## IN PROGRESS - EXPLICIT COMPONENT / HEALTH ROUTE - 2026-10-02

Local HEAD37ee1f3; working tree research-only. Test structurally distinct ownership hypothesis: generic declared 0x1b owner->component paths from typed player UID entities to health-property entities, up to three edges. These are candidates, not pawn proof; no nearest-ID/drone joins. Research state-component observer captures declarations, typed UID/HP properties and full feedback for parity. Run `.venv/Scripts/python.exe research/objective_state_components.py` on five consumed controls; cache under ignored data/research/diagnostics/state-components. Next: inspect any paths for independently verified death/HP correlation, or reject this route and continue disable clock-batch analysis. No fresh labels/SQLite/archive/public/v2 writes.

## CLOCK INTERVAL RESEARCH CHECKPOINT - 2026-10-02

Starting HEAD279d598; preserved and completed the interrupted evidence comparison and independent HUD audit. Eight prior score-resolved extension plants and four sole-survivor plants are disjoint; all eight score actors remain alive in the diagnostic. The 40 manually inspected HUD states matched (20 alive/20 dead), but disconnected/DBNO/revive eligibility remains unknown and Death events have zero offsets. Supporting evidence only. Reports: research/output/objective-evidence-comparison.md and objective-liveness-vod-audit.md.

A new research Go observer emits direct typed entity score/kills/assist records and actual length-prefixed clock values; all exported feedback matched cached parser output on 93 physical rounds. The existing complete ledger supplies increments because direct records alone omit inherited continuation fields. Exact contiguous score runs are serialization adjacency, not network packets. Common team rewards can occupy many runs, including inherited fields; clock epochs give a broader structurally defined interval. No decoded frame or score-reason field was found.

Unfrozen plant hypothesis research/objective_clock_candidate.py: complete one-to-one eligible scoreboard binding; first eligible positive score change must lie in the completion clock epoch or immediately next; exactly one +100 eligible increment before that score epoch ends; abstain on any kill/death or positive kill/assist counter from completion epoch start through score epoch end, or unknown death offsets. No byte threshold or fixed kill-point subtraction. Consumed extension23 correct/0 wrong/9 unresolved plants; original38/0/23. Disables unsupported:0/0/12 extension and0/0/8 original (one original disable has no state anchor, explicitly unresolved).4139R07 is unresolved via death in the structural interval; actor-kill4139R04 and teammate-kill4150R07 retain their earlier independent plant increment. This is development evidence only, not a frozen/fresh-validated actor rule. Gadget/delayed scoring causality is still uncertain.

Verification: 13 targeted Python tests passed; score observer build passed; Go vet passed. Private data/archive/public/v2 unchanged. No fresh reserve labels opened. No UAH correction or publish. Reproduce: `.venv/Scripts/python.exe research/objective_score_structure.py --extension` and `--development`, then `research/objective_clock_candidate.py` and `--development`. Diagnostics are cached by executable/replay hash; no need to rerun observation for unchanged binaries. Reports: objective-score-structure-{controls,extension,development}.md and objective-clock-candidate-{extension,development}.md.

NEXT ACTION: investigate explicit controller/component declarations for health and participation, using current score identity join as a starting graph and avoiding rejected drone/nearest-ID mappings. Also analyze all consumed disable clock batches and unresolved causes. No conservative combined candidate is frozen yet; fresh five-map reserve stays sealed. Do not stop after this milestone or alter deployed siege_style_v2.

## IN PROGRESS - UNCHANGED CLOCK HYPOTHESIS ON ORIGINAL COHORT - 2026-10-02

Standalone clock interval on consumed extension:23 correct plants/0 wrong/9 unresolved; disables unsupported (12 unresolved).4139R07 safely unresolved via kill/death interval. Next run `.venv/Scripts/python.exe research/objective_score_structure.py --development` then `research/objective_clock_candidate.py --development` with unchanged logic across original61plants. No candidate freeze yet: gadget/delayed-score causality not established by tick adjacency. Record every wrong result, add targeted interval regressions, analyze disable clock waves; reserve stays sealed. Runtime/data/v2 unchanged.

## IN PROGRESS - CLOCK INTERVAL HYPOTHESIS - 2026-10-02

HEAD279d598; controls observer/parity succeeded. Exact adjacent score records fragment common rewards; no decoded frame ID exists. Next experiment: annotate full cached canonical score/counter changes with actual distinct clock ticks. Plant candidate requires complete stable identity, unique eligible +100 in completion tick or immediately following tick, and no Kill/Death/positive kill-or-assist counter in that structural interval. This is a new consumed-data hypothesis, not a frozen actor candidate. Run `.venv/Scripts/python.exe research/objective_score_structure.py --extension` to cache ticks/feedback for all32 consumed extension rounds plus4139R07; then evaluate research/objective_clock_candidate.py. No arbitrary bytes/window tuning; fresh reserve stays sealed. Next investigate every false result and disable patterns.

## IN PROGRESS - SCORE RECORD STRUCTURE - 2026-10-02

HEAD279d598; preserved uncommitted comparison/HUD audits. New hypothesis: exact adjacent 18-byte entity score records reveal serialization runs; these are not network frames. Research-only observer includes raw clock ticks, score/kills/assists snapshots, and all feedback for parity. Build research/score_structure_probe.go into ignored .local-tools/bin/score-structure-probe.exe; run `.venv/Scripts/python.exe research/objective_score_structure.py` on four consumed control rounds plus4139R07. Next: examine standalone-vs-team wave record structure, then scale consumed extension only if diagnostic/parity is valid. No actor candidate freeze or reserve opening. SQLite/public/archive/v2 untouched.

## IN PROGRESS - SCORE/LIVENESS SET COMPARISON

Resumed clean `279d598`. Hypothesis: lower plant count reflects different evidence modes, not actor death or changed score boundaries. Cached event intersection shows zero overlap: eight score-only and four liveness-only plants. Next run `python research/objective_evidence_comparison.py` on consumed caches only; preserve full player/score/death context, then independently audit liveness using already-cached official VOD frames. Fresh reserve remains sealed; no production/data/rating writes.

## OBJECTIVE LIVENESS / VOD RESEARCH CHECKPOINT - 2026-10-01

Resumed clean local HEAD `0562cba`; deployment checkpoint `origin/main` remains `059f556`. Earlier batch/grammar/reserve work was preserved. This milestone adds research helpers, reports and tests only. No runtime parser, Rating, public JSON, SQLite or archive changes; no push/publish. `siege_style_v2` remains frozen.

The ledger now joins existing parser kill/death packet offsets to stable player identity, all ordered score changes, score before completion/final score, and kill/assist counters. The research Go observer exposes existing internal offsets without a second kill decoder. Kill/death feedback parity passed on all 32 consumed-extension physical rounds and all 61 original objective-bearing rounds. Unknown death offsets yield unknown liveness; DBNO, gadget-credit reasons and interaction ability remain unavailable. Cached ledgers/probe results remain ignored under `data/research/diagnostics/`.

New **development-only** diagnostic: same sole living eligible player at the beginning of the last complete timer run and at the validated completion-state packet, with no unknown death offsets. Timer grouping reuses the prior diagnostic; start 6.5-7.1 seconds, end <=0.1, at least two packets, after the previous objective state. Missing state anchors or incomplete runs abstain. This is provisional research, not a changed occurrence detector or production actor rule. Original cohort: plants **2 correct / 0 wrong / 59 unresolved**, disables **1 / 0 / 7**. Consumed extension: plants **4 / 0 / 28**, disables **3 / 0 / 9**. These are separate liveness results, not new independent validation or replacements for the frozen score rule's **8/0/24 plants and 0/0/12 disables**. Reports: `research/output/objective-liveness.md` and `objective-liveness-development.md`.

Both mandatory disputed score cases remain unresolved. In 4139 R07, Aiden and Raid are alive at completion; Aiden dies +2,987 bytes later, while Raid kills SpiriTz +14,137. In 3563/6675 R02, J9O and njr both survive throughout the disable, so liveness cannot select between them. A separate official VOD check located Bank R02 at approximately 1:55-1:58:15, but the broadcast cuts to player/crowd cameras immediately after Surf's death and does not show the disable interaction. It cannot independently confirm or overturn the cached J9O actor label. See `research/output/objective-vod-review.md`; metadata and sampled frames are cached under ignored `data/research/video/`.

Verification: full Python suite **118 passed, one optional skipped, six subtests**; Go helper build and `go vet` passed; cached diagnostic runs completed. Pytest reported its existing Starlette deprecation and a nonfatal Windows cache-write warning. SQLite SHA-256 remains `f3dc10210ab29f62e83317600e8bfcd55b1e6f17c6dbcaf0abf4556af55bef4e`. No frontend or runtime Go source changed, so those deployment builds were not repeated.

NEXT ACTION: use the new packet-ordered player ledgers to assess agreement/conflicts between liveness and score candidates on consumed data. Independent liveness auditing needs additional evidence: the inspected cached SiegeGG 3563/6675 R02 event list contains objectives/multikills, not a complete death log. The njr residual in 3563 R02 still has no verified cause or typed interaction-owner corroboration; do not declare it explained by the VOD. A broader score/structural actor rule remains unfinished. Keep the five-map reserve (eight plants/two disables) unopened until a revised rule is justified and frozen. No UAH actor audit or historical correction yet; UAH remains 17 plants/three disables actor-unresolved. Do not refit v2 or use the consumed NA Rating final event for actor research. Local research milestone: `22323da`; working tree was clean after that commit.

## OBJECTIVE ACTOR SCORE RESEARCH - 2026-10-01

Starting HEAD `059f556` (the pushed deployment checkpoint). Current actor work is local only; no production parser, SQLite, archives, public JSON, default Rating, or website publish changed. Frozen diagnostic and exact rule: `research/objective-score-delta-plan.md`; executable: `research/objective_score_delta_validation.py`. The separate twelve-map actor set was evaluated once and is now **CONSUMED**: plants 8 correct / 0 wrong / 24 unresolved; disables 0 correct / 0 wrong / 12 unresolved. The validation event and reason breakdown is cached under ignored `data/research/diagnostics/objective-score-delta-validation/`. Across the 32 plants, 23 abstained for a kill/assist counter in the provisional collision interval and one had no unique close +100; all five eligible scoreboard identities were bound in every round. Fixed kill-point subtraction is unsafe: isolated score changes following kill counters include +100, +120, +110, +130 and larger batches; assist changes most often +75 but also +175/+95.

Local actor-research commits `b2689d0` and `f37b3cb` preserve the rule, reserved set, validation script, packet tables, and the same-build no-objective control; they were **not pushed**. The validation rerun from cached raw ledgers reproduced 8/0/24 and 0/0/12. All four new research scripts compiled with `py_compile`, the comparison report regenerated, and `git diff --check` passed. SQLite SHA-256 remains `f3dc10210ab29f62e83317600e8bfcd55b1e6f17c6dbcaf0abf4556af55bef4e`. Full Python/Go/frontend gates were last run for deployment; no production source changed during this research.

The 12 disable rounds had five stable defender scoreboard bindings but a team score wave, sometimes just **before** the state transition. Eleven public disablers had an extra +100 relative to teammates, but 3563/6675 R02 is a definite counterexample: J9O is the public disabler, whereas njr receives the +200 packet and the other four defenders +100. J9O's earlier kill and njr's earlier assist already have separate +100/+75 updates, leaving njr's extra batch +100 unexplained. A team-relative rule alone would falsely name njr. A same-build negative control, 3563/6675 R04, has **no objective occurrence** but the winning team still has one +200 versus four +100 late packets; J9O's kill counter rose before that +200. The 3563 R02 state entity has no typed reference path to the partial player-entity candidates, so it provides no independent actor corroboration. February 3073 R08 has four winners +2350 and one +2450, but its old layout has no verified scoreboard identity binding. Known false-credit 4139 R07 remains unresolved by the frozen rule: Aiden gets +100 near the plant, Raid gets +10 and later has a kill; the public planter is Raid. See `research/output/objective-score-batch-comparison.md` for every consumed validation disable and plant event.

Fresh independent actor reserve `research/objective-actor-reserve.json` records five previously unused cached Stage 1 rehost maps, 60 counted rounds, eight plant occurrences, two disables, build IDs, physical filenames, and a replay digest. Public actor labels for that reserve have **not** been opened or graded. It excludes the consumed North America Stage 2 Rating final event. The reserve is small; add further distinct events before claiming broad production confidence. Do not apply a revised actor rule to these labels until the rule is frozen. No UAH actor correction is proposed; 17 plants/three disables remain actor-unresolved.

The build-specific packet adjacency table is `research/output/objective-score-grammar.md`: within the same code version, a kill-counter increment can be followed by +100, +120, +110, +130, or a larger combined packet; assist associations are usually +75 but can be +175 or batched. These are observations, not universal causal point awards. Near-plant collisions include teammate GMZ's kill after Hotancold's 4150 R07 plant and Hotancold's own kill after the 4139 R04 plant; neither justifies a fixed subtraction or claymore claim.

NEXT ACTION: identify why 3563 R02 credits njr an unexplained extra +100 and whether a typed interaction/player relationship independently identifies J9O. Examine scoreboard batch packet structure, not a wider byte window chosen to match public labels. The five-map reserve remains unopened. Define a structurally justified conservative actor rule, freeze it, then evaluate the new reserve exactly once. If trustworthy evidence remains insufficient, retain unresolved actors. Keep deployed `siege_style_v2` frozen and actor research local.

## LIVE RATING DEPLOYMENT - 2026-10-01

`siege_style_v2` is the live/default Rating. Deployment commit `cefb746d60a1b2d69fbca601bbf2ff7b53d0bee8` was pushed to `main` through the existing publisher, and GitHub Actions run `36942505666` completed successfully. The public page and `/data/index.json` returned HTTP 200; the index and methodology identify `siege_style_v2`, with five matches and five players. Pre-deployment rollback reference: `42af9169219325a0e1c24aa965aea1ff731e98a9`. The exact frozen coefficients and training normalization are in `research/frozen-rating-candidate.json`, committed at `eb747f8` before the one-time North America final test. The final 60 rows are consumed; MAE was 0.03623, versus 0.23875 for `collegiate_v1` on the same rows.

Read-only UAH runtime parity matched the frozen research predictor for all five complete eligible maps and season aggregates within 1e-12; see `research/output/uah-v2-runtime-parity.md`. No `.rec` reparse, SQLite update, archive change, manual K/D change, or raw-stat change occurred. SQLite SHA-256 before and after publishing: `f3dc10210ab29f62e83317600e8bfcd55b1e6f17c6dbcaf0abf4556af55bef4e`. The generated public JSON semantic diff contained only Rating values/version text and the new multikill count. Full Python suite: 110 passed, one optional skipped, six subtests; public/admin Vite builds passed; 18 JSON files passed privacy/reference validation. The live season returned Lgon Rating 1.241709 over 62 rounds. Player objective actors remain unresolved; the frozen v2 gives them no speculative credit. Historical `collegiate_v1` remains available.

NEXT ACTION: investigate planter/disabler actor attribution through narrow, replay-ordered scoreboard score deltas near the validated completion event. First verify scoring amounts and packet ordering on clean kill, assist, plant, disable and round-end examples. Build a per-player ledger with stable identity mapping and explain known kill/assist/common batch credits before proposing an objective residual. The known Match 4139 R07 public planter is Raid; a resolver must identify Raid independently or leave the actor unresolved, never credit Aiden. Keep the deployed v2 frozen and do not alter historical SQLite without review.

## RATING RESEARCH FINAL CHECKPOINT - 2026-10-01

Local frozen candidate commit eb747f8. Exact dataset/model/provenance research/frozen-rating-candidate.json. Seven earlier train events299clean rows; August development32rows/four maps; both September events excluded from fit/selection. Reserved NA Stage2 final60rows/seven maps evaluated ONCE after freeze (evaluation frozen-na-20261001T223911Z). Candidate MAE0.03623/RMSE0.04945/medianAE0.03080/maxAE0.1494/within.05=81.7%; collegiate_v1 same rows MAE0.23875. This final event is CONSUMED and cannot be reused as untouched test for a revised model. Candidate remains frozen; no post-final retuning. See research/output/final-na-rating-evaluation.md and rating-deployment-review.md.

Trade semantics audited/tested; normalized cache eight-second parity zero mismatches across development rows. 5/6/7/10-second windows did not robustly beat eight; individual death-trade or kill-trade features underperformed the differential. Removing KOST survival path or separate survival strongly worsened validation. Linear clutch weighting improved pooled folds but worsened August; retain equal clutches. Multikill and opening decisions from prior checkpoint unchanged. Exact records/coefficients in research/experiment-log.jsonl; candidate comparison research/output/pre-freeze-review.md. Objective occurrence remains verified, actor unresolved. No player objective credit fabricated. Final objective-positive public labels show signed bias -0.0378 versus +0.0084 for objective-negative rows (analysis labels only).

Read-only UAH sanity comparison used five stored NECC maps62rounds/five players; SQLite SHA unchanged. research/output/uah-frozen-sanity.md. No SQLite/archive/public JSON/live default Rating change; no push/publish. Latest full Python suite107passed/one optional skipped/six subtests. Go/frontend untouched during research.

NEXT ACTION: user review of research/output/rating-deployment-review.md. If approved in a later turn, implement optional versioned siege_style_v2 from exact frozen coefficients, validate historical normalized-data recalculation and public methodology, and separately review any default switch/publish. Do not rerun final NA evaluation or tune on its errors. Without approval, continue only new independent data-quality/objective-actor research that does not rebrand the consumed NA event as untouched, or maintain documentation/tests.

## CURRENT CHECKPOINT - CONTROLLED RATING EXPERIMENTS COMPLETE - 2026-10-01

Starting production HEAD 75d17a4 preserved. Local milestones: 709c41c actor decision/preregistered multikill plan; a0608ab multikill implementation; 430cd1f results/opening plan; c1a967e opening implementation. Current changes are research reports/logs only. No push/publish, SQLite/archive/public JSON or live/default Rating modifications.

Occurrence remains validated (93 plants / 20 disables across 415 professional rounds); actors unresolved. Actor score/controller diagnostic: plants 42 correct / 1 incorrect / 18 unresolved; disables 4 correct / 4 unresolved. Aiden false-credit case rejects deployment. UAH audit unchanged: 17 plants / three disables / 62 rounds, all actors unresolved, personal disable not assigned from recollection. See research/output/objective-actor-decision.md.

Player dataset unchanged: 56 maps, 560 rows, 407 clean; SHA2454eb35ebe06df8d91f950b17cab8cea0a26384d9c40cbdd786f7e4f11b04de. No identical baseline rerun or rederive. Train299, August32, historical September16 excluded, final NA60 sealed. Baseline pooled/August MAE 0.036467/0.034530 remains preferred. Multikill 2+ round rate: 0.039443/0.036818; separate sizes: 0.036508/0.034119. Separate openings: 0.036620/0.034418. Neither experiment establishes robust improvement; retain simpler original definitions. Full coefficients, event folds, drift and metric thresholds recorded in experiment-log.jsonl. Objectives explicitly excluded.

Residual report: public objective-positive rows underpredicted ~0.038 August baseline / ~0.039 separate-opening event folds; public labels are diagnostic groups only, never features. No causal correction or actor inference. Teamkills sparse (nine); clutches29 = 20/5/3/1/0 by size; no training5K multikill. Do not fit unsupported independent size coefficients blindly. Reports: research/output/multikill-experiment.md, opening-experiment.md, development-residuals.md.

Tests: full Python suite 99 passed / one skipped / six subtests after multikill; subsequent opening feature/isolation suite three passed. Go tests/vet previously passed at production checkpoint; no Go/runtime changes since. No frontend changes requiring rebuild.

NEXT ACTION: audit the existing trade event semantics, then preregister 5/6/7/8/10-second research-only comparison using cached normalized rounds and fixed event splits. Do not reparse replays or score final targets. Candidate freeze remains premature. Exact residual reproduction (no fitting): .\.venv\Scripts\python.exe research/development_residuals.py. Existing fit scripts reject duplicate experiment records; inspect cached JSON under data/research/experiments instead. Earlier NEXT ACTION sections below are historical.

## MULTIKILL RESULTS / NEXT OPENING EXPERIMENT - 2026-10-01

Actor decision documented; production credit remains unresolved. Deliberate multikill experiment multikill-20261001T195254Z completed: baseline pooled/August MAE 0.036467/0.034530; 2+ round rate 0.039443/0.036818; size buckets 0.036508/0.034119. Retain simpler kills-beyond-first: bucket benefit is tiny/inconsistent and 5K has no training support. Full results research/output/multikill-experiment.md; record contains coefficients/folds. Python 99 passed, one skipped, six subtests. No live data/default Rating changes; final NA60 sealed.

NEXT ACTION: implement research/opening-plan.json, one controlled separate opening-kill/death variant against reused baseline. Preserve other families and fixed event splits. No repeated fit of already-recorded multikill experiment.

## ACTOR DECISION / MULTIKILL EXPERIMENT PLAN - 2026-10-01

Actor discovery complete: plants 42 correct / 1 incorrect / 18 unresolved; disables 4 correct / 4 unresolved. The explicit component/controller UID join plus team score residual still wrongly credits Aiden in 4139 R07. Rejected for production; see research/output/objective-actor-decision.md. This does not establish that attribution is impossible. Occurrence and UAH audit remain unchanged; no player feature rederive is justified.

NEXT ACTION: implement and run the preregistered research/multikill-plan.json experiment (2+ round rate and separate size buckets), using the unchanged 299/32 event split, reusing stored baseline rather than refitting. Objectives explicitly excluded. Both September events remain excluded; NA final 60 sealed. Production tests last passed 97 Python plus Go/vet. No database/archive/public JSON/default Rating/publish changes. Earlier IN PROGRESS sections below are historical.

# Status and next steps — 2026-10-01

## ACTOR DIAGNOSTICS IN PROGRESS - 2026-10-01

HEAD `75d17a4`; production occurrence remains unchanged. Preserved uncommitted player/entity and reference-graph diagnostics. Five contrasting rounds show no typed reference edge from the objective-state entity to a player. A numeric-ID table in 4139 R07 maps five SSG players to spawn-counter-154 drones, not player bodies; do not use it for actor credit. The older adjacency pattern covers only nine of 50 player slots across these cases, with spawn counters 478/494. No new actor is credited.

The original 61-plant/eight-disable cohort now has a cached raw score-batch ledger. Without player/team binding, common delta plus 100 singles out one raw entity in five plants and five disables; seven residual candidates have concurrent kill/assist counter increases. These are not resolved actors. A new explicit scoreboard-component declaration -> controller numeric UID -> header identity join binds all ten identities in four inspected Y11 rounds (zero in the February layout). This is a structurally distinct diagnostic from rejected username adjacency/fixed offsets. Its team-relative residual hypothesis is being graded on the full original cohort, with the twelve-map extension reserved from actor tuning.

NEXT ACTION: record full actor-batch validation, reject any false-credit rule including Aiden in 4139 R07, checkpoint the limitation, then follow the user's new instruction to continue controlled Rating experiments with player objectives omitted. Do not repeat an identical baseline fit. Resume: `.\.venv\Scripts\python.exe research/objective_actor_batch_validation.py` (cached identity/ledger data); inspect `data/research/diagnostics/objective-score-identity/validation.json`.

## CURRENT OCCURRENCE IMPLEMENTATION CHECKPOINT - 2026-10-01

Independent result committed at `7d1a952`; occurrence rule frozen at `8b18365`, twelve-map set locked at `4f17c21`. The minimum Go occurrence detector is implemented and the tested binary installed through `scripts/install-parser.ps1`. Installed and candidate SHA-256 both `e7c2a2db6d0a7bb68013ab285ff859cb1ae27595a74e58901b3a95e82748f4d5`. The old binary is retained privately as `.local-tools/bin/siege-dissect-before-objectives.exe` for audit comparisons.

- Separate `objectiveOccurrences` metadata records plant/disable evidence with null actor. Python retains it separately in normalized rounds; it never creates player-credited Objective rows. The action-start algorithm, kills, KOST, Rating and match metadata are unchanged. No database migration, historical reparse/import, public-data regeneration, push or publish occurred.
- Go production parity: 38 professional physical maps / 415 rounds; all 93 plants and 20 disables match the frozen discovery/validation results. Existing players/operators, kills, credited objectives, winner, win condition and site match cached normalized data exactly. All 322 objective-free rounds remain negative. Independent validation alone: 12 maps, five events/builds, 124 rounds, 32 plants, 12 disables, 92 negatives, no errors; one cleanup correctly excluded.
- Read-only UAH: five maps / 62 rounds, 17 plants and three disables; all 20 actors unresolved. The disables are Border `076d2b6b02bc` R02/R06/R08. The older Border `8a6357ff307c` R06 historical disable is not supported. All 310 tracked player-rounds / 102 tracked operator usage groups match stored data. Of 616 total player-rounds, one pre-existing opponent mapping differs from historical storage: Kafe R08 hidebuff.USU Unknown -> Solid Snake; both the pre-objective and new binaries agree. SQLite SHA-256 unchanged. See the read-only `research/output/uah-objective-audit.md`; the user's personal disable remains unattributed.
- Verification: 97 Python tests passed, one optional smoke skipped, six subtests; Go tests and go vet passed. Tests explicitly preserve unresolved attribution in 4139 R07 (no Aiden guess). Frontend was not rebuilt for this parser-only change; both builds passed at the earlier grammar milestone.
- Rating observations remain 56 maps / 560 rows / 407 clean, zero unresolved final operators and frozen August MAE 0.03453. No player-resolved objectives were added, so rederivation/refitting would not test corrected player features yet. NA Stage2 60-row final Rating set stays sealed.

NEXT ACTION: investigate stable controller/device/player ownership and round-end score decomposition for planter/disabler attribution, using 4139 R07 and Border R02/R06/R08 as contrasts. Do not reuse mutable username slots, fixed ID offsets, timer-only or +100-only attribution. Cached parity resume: `.\.venv\Scripts\python.exe research/objective_production_check.py`; read-only UAH: `.\.venv\Scripts\python.exe research/uah_objective_occurrence_audit.py`; raw ledger: `.\.venv\Scripts\python.exe research/objective_score_ledger.py 4139:7 3073:8 3880:10`.

## CURRENT FROZEN OCCURRENCE VALIDATION - 2026-10-01

HEAD at validation: `4f17c21` (rule frozen at `8b18365`, grammar milestone `5dc314d`). The interrupted tests were preserved. The unchanged rule matched 32/32 plants and 12/12 disables in the locked twelve-map / 124-round validation, with zero misses or false positives. All 92 negative rounds remained negative; 6158/10563 R07 cleanup was not classified as a disable. The five events span five header code versions. Full per-map results: [occurrence report](../research/output/objective-occurrence-validation.md).

The original 291 development rounds separately matched 61/61 plants and 8/8 disables; all 230 negative rounds stayed negative. The rule requires Bomb, one unambiguous plant-state transition/entity, and an unambiguous winner side; Defense winning after a plant implies a disable. It does not use timer thresholds, score bonuses, or public actor data. Actors remain unresolved. No live database, archives, public JSON, production parser, operators or Rating changed. Research reference remains 56 maps / 560 rows / 407 clean, zero unresolved operators and frozen August MAE 0.03453; the 60 NA Stage2 Rating rows remain sealed.

NEXT ACTION: assess minimum occurrence-only production metadata with no player credit, then investigate independent player/entity ownership and score-ledger collisions. Keep the frozen rule and independent result recorded. Exact replay-only validation resume: `.\.venv\Scripts\python.exe research/objective_occurrence_holdout.py`; focused tests: `.\.venv\Scripts\python.exe -m pytest tests/test_objective_encoding.py -q -p no:cacheprovider`.

## CURRENT OBJECTIVE ENCODING CHECKPOINT - 2026-10-01

Starting HEAD `1be11d4` includes the user's five-map public-data update; it was preserved. Rehost remains accepted. New research-only contiguous-property decoding explains the missed plants: `0x22` continues an explicit `0x23` entity record. The old strict probe required a fresh reference for every property. Discovery was 4132 R13; the frozen grammar was subsequently scanned across all 26 development maps / 291 rounds.

- Near the unchanged +0..1000-byte terminal window: plants **60/61**, disables **7/8**, compared with 46/61 and 7/8 before. The remaining plant (3585 R04) has a valid inherited state1 at +1235 bytes; no window was widened to claim a pass. All 61 plant rounds contain a decoded state1 somewhere in the round.
- All 230 objective-free rounds still have zero decoded state transitions. The three false near-zero timer controls still have none. 4112 R11 retains a later state0 cleanup candidate without a completed disable timer; state0 alone must not be credited.
- 3073 R08 still has no terminal state0 even in raw property hits; it is a February/build11944 replay. The other 15 originally missed events were encoding/window failures, not absent raw plant state. Actor attribution remains unresolved; no score-based fallback was accepted.
- New scripts: `research/objective_encoding_probe.py`, `research/objective_encoding_validation.py`; explicit event/negative sets: `research/output/objective-encoding-validation.md`. Seven focused synthetic grammar/ledger tests pass. Full verification: 91 Python tests passed, one optional smoke skipped, six subtests passed; Go tests and go vet passed; public and admin web builds passed. Existing Starlette deprecation and Vite module-directive warnings remain non-fatal. No production extraction, SQLite, public JSON, operators, Rating data or coefficients changed. Research remains 56 maps / 560 rows / 407 clean, zero unresolved operators, frozen August MAE 0.03453. NA Stage2 60-row Rating test stays sealed.
- NEXT ACTION: inspect the missing 3073 R08 disable's state-entity lifecycle and round end, compare the seven detected disables and 4112 R11 cleanup, then seek independent actor ownership. Do not infer actor from score proximity. Resume: `.\.venv\Scripts\python.exe research/objective_encoding_probe.py 3073:8 4112:11`; `.\.venv\Scripts\python.exe research/objective_encoding_validation.py` (cached).

## CURRENT OBJECTIVE RESEARCH CHECKPOINT — 2026-10-01, state-property contrast

- Product rehost milestone was committed locally as `e0c824a`; no push or publish. Normal import, proper carried-score rehost, explicit 0-0 override, 5v5-to-4v5 participation, archive/reparse, manual K/D, and public-data privacy passed their focused tests. Full Python suite: 84 passed, one optional smoke skipped, six subtests; both web builds, local Go tests, and `go vet` passed. The real three-folder Chalet admin preview was read-only. Real SQLite and generated public JSON were not changed.
- A new read-only, typed entity-property probe found raw hash `ff 39 f4 08` close after a near-zero defuser timer completion. On the existing 26 non-reserved physical development maps (291 rounds), value `01` appeared near 46 of 61 logged plants and `00` near seven of eight logged disables. The other 16 logged events lacked a near-terminal state change. All three known unlogged near-zero timer runs lacked it. A separate full-round negative-control scan found no occurrence of the property in **all 230 objective-free development rounds**. Cached per-round diagnostics are Git-ignored. See [research/objective-coverage.md](../research/objective-coverage.md).
- The property is not sufficient for production: 4112 R11 emitted a later `00` after a plant without any logged disable or second near-zero timer completion. It names no player; a nearby reference in the known wrong-actor 4139 R7 plant points to Aiden, while Raid was the public planter. A probable parent/owner property gave no direct state-entity link. Read-only UAH archive scan found the historically stored Border `8a6357ff307c` R06 disable has only `01` and an Attack win, while a different Border map `076d2b6b02bc` has `00` and `DisabledDefuser` wins in R02/R06. No objective extraction, historical stats, Rating, or UAH database was changed.
- **NEXT ACTION:** Find a replay-derived actor/owner link independent of timer progress, score bonuses, and incidental nearby player references. Use 4139 R7 (Raid vs wrong Aiden), 3880 R10 (plant plus disable), and both UAH Border R06 cases as contrast. Test any proposed actor rule on all cached non-reserved development events and explicit false cases before changing the parser. The 60 North America Stage 2 Rating rows remain sealed. Exact resume: `.\.venv\Scripts\python.exe research\objective_transition_probe.py 4139:7 3880:10 4141:6`; `.\.venv\Scripts\python.exe research\objective_state_negative_controls.py` (cached); `.\.venv\Scripts\python.exe research\uah_objective_state_readonly.py` (read-only). Do not rerun the Rating fit without a validated data change.

## CURRENT PRODUCT CHECKPOINT — 2026-10-01 15:05 UTC, rehost participation and score

- Starting HEAD was `93e3b74` with a clean tree. Audit found normal one-folder import, explicit rehost selection, private archive/reparse, and manual K/D correction working. Exact roster equality prevented a 5v5-to-4v5 rehost; the parser discarded physical score fields; scan blocked one-round abandoned Custom Game segments; first-round-only roster lookup could omit later participants from public JSON.
- Rehost assembly now uses real per-round participants and requires clear shared identities on both teams, while allowing a player to be absent or added. Player stats, rate denominators, operators, and physical Attack/Defense use only rounds actually played. Import requires an extra roster-change confirmation. Physical score state from siege-dissect distinguishes a properly carried score from a 0-0 restart; only the latter requires an explicit override confirmation. Other score discontinuities are rejected. Excluded rounds retain source/archive evidence and contribute no statistics. A one-round Custom Game is selectable only as a rehost segment; matchmaking replays remain ineligible. The normal one-folder flow is unchanged.
- The version-2 private rehost manifest records physical and logical score starts, per-round physical roster snapshots, team mapping, and required confirmations. Reparse preserves the stored mapping and checks the manifest fingerprint; version-1 manifest hashing remains supported. Public JSON contains no replay paths or private rehost manifest. Manual K/D and `collegiate_v1` were not changed.
- Read-only admin preview using the actual local replays `Match-2026-09-30_21-06-48-21500`, `Match-2026-09-30_22-01-18-21500`, and `Match-2026-09-30_22-18-36-21500`, with middle R01 excluded, returned Chalet, 13 physical rounds, 12 counted rounds, canonical score 5-7 (UAH team 1, hence UAH 7-5), 4-4 carry into the abandoned lobby, and a required 0-0 override for the final lobby. The 4v5 segment is missing opponent `Natedog.UMich`; all five UAH tracked players appear. Synthetic tests cover a UAH player missing after a 5v5-to-4v5 rehost. This preview did not call import or write the real SQLite, archives, or public JSON.
- Verification: 84 Python tests passed, one optional real-replay smoke skipped, six subtests passed; focused admin/normal import/manual K/D/publishing tests passed 23; both web builds passed; local Go tests and `go vet` passed. No push, publish, historical database modification, or Rating refit occurred. Current working tree contains the product changes until the local milestone commit.
- **NEXT ACTION:** Commit the tested product changes locally, then resume the recorded objective packet/entity investigation. Start with the known wrong-actor 4139 R7 and the three timer/public mismatches. Do not credit an objective from the rejected timer/+100 rule, repair UAH objective stats, refit Rating, or inspect the sealed North America Stage 2 target rows without stronger evidence. Exact resume commands from the repo root: `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider`; `Push-Location third_party\siege-dissect; & ..\..\.local-tools\go\bin\go.exe test ./...; & ..\..\.local-tools\go\bin\go.exe vet ./...; Pop-Location`; `.\.venv\Scripts\python.exe research\objective_actor_validation.py 4141 4134 4135 3745 4148 4139 3639 4127 4129 4137 4138 4119 4120 4133 3880 3879`.

## CURRENT OBJECTIVE VALIDATION CHECKPOINT — 2026-10-01

- The packet-level +100/entity-offset-four actor hypothesis was frozen in local commit `8b6cbfe` before the first held-out actor logs were inspected. Three held-out physical maps had 35 rounds and five public plants: four exact actor names and one unresolved. A further 16 physical development maps were locked in commit `bf69c60` before their actor diagnostics were inspected.
- Across those 16 additional maps, the unchanged `<=0.10` timer rule found 35 candidate completions against 32 logged events in 168 rounds. Three timer runs occurred in rounds with no public objective (4141 R6/R14, 4138 R9). The actor rule named 22 logged events: 17 exact, four clear name variants, and **one wrong player**. In 4139 R7, Aiden's +100 score passed the rule while the public planter was Raid, a separate SSG player. The frozen actor rule is rejected for production. Across the original seven maps and both validation sets, eight public disables were audited; only one was named by this rule.
- The packet diagnostics remain cached under ignored `data/research/diagnostics/`; [research/objective-coverage.md](../research/objective-coverage.md) records the exact contradictions. A new read-only 4,096-byte proximity probe around timer start/end in a wrong-actor plant, a plant/disable, and an unlogged timer run found no unique actor-bearing `DissectID`; nearby score entity IDs represented multiple players. No parser rule, objective credit, live SQLite, public JSON, default Rating, push, or publish was changed by this validation. The original 56-map research dataset remains 560 rows/407 clean with zero unresolved final operators; the frozen raw development benchmark remains August MAE 0.03453. The 60 North America Stage 2 Rating rows remain sealed.
- Verification after the checkpoint: Python 78 passed, one optional smoke skipped, six subtests; public and admin web builds passed; Go tests and `go vet` passed. One pytest cache-write warning was caused by Windows access denial to `.pytest_cache` and did not affect test results. Normal import, rehost admin/archive, and manual K/D features retain their previous passing regression coverage.
- **NEXT ACTION:** Investigate a distinct replay-derived plant/disable actor or completion-state packet, starting with 4139 R7 and the three timer/public mismatches. The score bonus and near-zero timer cannot independently establish an objective event or actor. Test any new mechanism on the existing development diagnostics before proposing a parser change. Then rerun strict research derivation and the frozen raw development model only if validated production extraction changes. Do not repair UAH objective credits or evaluate reserved final Rating rows yet. Resume with `.\.venv\Scripts\python.exe research\objective_actor_validation.py 4141 4134 4135 3745 4148 4139 3639 4127 4129 4137 4138 4119 4120 4133 3880 3879` and inspect `research/objective-coverage.md`.

## HISTORICAL OBJECTIVE ACTOR PREDECLARATION — 2026-10-01

- A packet-level refinement on the seven already inspected maps uses exact scoreboard entity-to-player offset 4, a +100 score change 0–2,000 bytes after a `<=0.10` timer completion, and unique player identity. It names 17/32 discovery events with 15 exact actor matches, two clear aliases, and no definite mismatch; the remaining 15 are unresolved or ambiguous. This is an in-sample hypothesis and has **not** changed production actor credit.
- `research/objective_actor_validation_plan.md` froze the candidate and three independent cached development maps (3637/6842, 4140/8330, 4118/8666) before their actor logs were inspected. That check and the locked 16-map extension are complete; the current result and next action are at the top of this document.

## CURRENT UAH OBJECTIVE SAFEGUARD CHECKPOINT — 2026-10-01

- A read-only audit of the four-map local SQLite found 13 stored objective event rows: 12 plants credited to defenders and one defender disable without verified actor provenance. Read-only reparsing of the four private archives with the current adapter yields zero verified objective actors. All **89** current tracked-player operator usage rows match stored counts exactly; the earlier 85-row statement referred to the first three maps.
- `calculate_match` now drops role-impossible/team-inconsistent objective rows even when already stored in old normalized JSON. The Y11 adapter no longer treats a unique +100 score bonus as verified actor evidence, because the seven-map audit found three unique but wrong plant candidates. The Rating formula is unchanged, and raw stored replay/event rows are preserved.
- A temporary website export from a migrated **backup copy** of live SQLite shows the only tracked-player aggregate impact: Tallman3.14 Fall 2026 plants 5→0, KOST rounds 27→24, KOST 0.54→0.48, and `collegiate_v1` Rating 0.416700→0.374753. Real SQLite, archives, and current `web/public/data` were not changed. There was no publish, push, or live Rating version change.
- Regression tests cover both normalized and historical invalid objective credits; full Python suite passed 78 tests, one optional smoke skipped, six subtests passed. Go tests and `go vet` passed. The newly added rehost edge tests cover stat-family exclusion, long downtime, incompatible segments, and tampered archive reparse.
- **NEXT ACTION:** Find a replay-derived actor-bearing interaction source on development replays and validate it against all 32 audited objective completions, especially the three wrong unique-score plants and five ambiguous/absent disables. Only then reparse/audit UAH objectives and rebuild/refit professional data. Current public JSON remains stale for the role guard until an intentional local regeneration; do not publish or push. Reproduce the safe audit with `.\.venv\Scripts\python.exe -m research.uah_objective_readonly --reparse` and `.\.venv\Scripts\python.exe -m research.uah_objective_export_diff`. The 60 NA Stage 2 Rating rows remain sealed.

## CURRENT OBJECTIVE RESEARCH CHECKPOINT — 2026-10-01 05:13 UTC

- The seven cached development maps still yield 88 rounds, 27 public objective rounds, and 32 public events (27 plants, five disables). The held 0.10-second timer-run criterion has zero round/count mismatches. Newly generated actor diagnostics for the three independent validation maps are cached under ignored `data/research/diagnostics/`.
- A new read-only audit of +100 score candidates found 16 uniquely named candidates among 32 events: 12 exact public-actor matches, one plausible alias, and three definitely wrong players. Five events have no +100 candidate. All five disables are ambiguous or absent. A local terminal timer-packet scan across all 32 events found no exact player `DissectID` or scoreboard-style nearby entity reference in a -32/+159-byte window. See `research/objective-coverage.md` and `research/objective_actor_audit.py` / `research/objective_identity_offsets.py`.
- **NEXT ACTION:** Reverse engineer a separate actor-bearing interaction packet or entity ownership link using development replays, and test it against the 32 audited events, including wrong-score and disable cases. Do not credit an objective actor from a timer threshold, unique score bonus, or a public target. Do not run UAH objective repair or refit the model until actor attribution is trustworthy. Resume with `.\.venv\Scripts\python.exe research\objective_actor_audit.py 4150 4132 3585 6156 3073 3554 4112` and inspect `research/objective-coverage.md`. The 60 NA Stage 2 Rating rows remain sealed; no publish or push.

## CURRENT PRODUCT CHECKPOINT — 2026-10-01 manual K/D milestone

- Admin map detail now has an auditable final-map K/D editor for roster players. SQLite stores raw replay K/D, final K/D, reason, note, and update timestamp separately from normalized replay/events. Create/edit/remove immediately regenerate local public JSON; removal restores replay K/D and retains the map's partial-data flag.
- Public map, season, and career kills/deaths/KD use final totals when corrected. KPR, KOST, survival, openings, trades, operators, objectives, headshots, side splits, and the rating formula remain replay-derived. Partial maps have null map Rating; season/career Rating uses complete eligible maps only, or null if there are none. Admin explicitly displays partial, correction, and eligibility status. No private correction reason or note appears in public JSON.
- TestClient covers create/edit/remove, replay raw preservation, recalculation, reparse preservation, deletion, aggregation, Rating exclusion, and public privacy. Full Python suite: 71 passed, 1 optional smoke skipped, 6 subtests passed. Both public and admin Vite builds passed. Real SQLite was not modified; no publish or push.
- **NEXT ACTION:** Continue objective actor research on development replays, starting with existing timer occurrence evidence and prior art. Require event-level actor validation before changing objective credit. Then audit UAH read-only and only later rebuild professional data and rerun the frozen raw model. Resume with `.\.venv\Scripts\python.exe research\objective_timer_validation.py --help` or inspect `research/objective-coverage.md` and `research/defuser_probe.py`. Keep the 60 NA Stage 2 Rating rows sealed.

## CURRENT PRODUCT CHECKPOINT — 2026-10-01 rehost admin milestone

- The opt-in browser rehost flow is implemented: select two or more ordered Custom Game replay folders, mark excluded physical R## rounds with a reason, inspect the physical-to-logical mapping, and confirm the final competitive score before import. The normal one-folder import path stays separate and unchanged.
- A rehost creates one logical map and one private format-2 archive with independently hashed physical segments. Archive verification, source backfill, reparse from verified archive, and delete work with the existing map ID and transactional behavior. Public JSON excludes source paths and rehost metadata.
- Full Python suite: 70 passed, 1 optional real-replay smoke test skipped, 6 subtests passed. Admin Vite build passed. Only temporary test databases were written; the real four-map SQLite and archives were not modified. No publish or push.
- **NEXT ACTION:** Implement the narrow auditable final-map K/D correction on tracked players. Keep replay-derived statistics intact, overlay only displayed K/D totals, mark corrected/partial maps Rating-ineligible, and cover create/edit/remove, recalculation/export, deletion, and privacy with tests. Then revisit objective actor attribution on development replays only. Resume with `.\.venv\Scripts\python.exe -m pytest -q` and `cd web; npm.cmd run build:admin`.

## CURRENT PRODUCT CHECKPOINT — 2026-10-01 04:11 UTC

- HEAD before this checkpoint: `3dac52a`. The first opt-in local rehost layer is implemented in `r6stats/parser/confirmed_rehost.py`: ordered two-or-more physical replay folders, explicit counted/excluded R## mapping, team-index remapping by stable roster identities, logical round renumbering, independent final competitive score validation, and source hashes. It allows a later physical lobby to restart at 0–0. It never changes the existing research score-continuity stitcher or the normal one-folder parser.
- The SQLite schema now has private `map_segments` source identities (including a safe backfill for existing one-folder maps), `maps.rehost_json`, `maps.replay_data_complete`, and `map_kd_corrections` storage for later use. Import records each segment's replay ID and fingerprint so an already imported physical folder cannot be counted in another map. The four-map real SQLite was inspected read-only and was **not** migrated or written during development; tests use temporary databases.
- Tests: 19 focused Python tests pass, including existing normal admin/CLI import tests and new two-/three-segment, reset-score, exclusion, swapped-team, wrong-score, unrelated-roster, and duplicate-source cases. The archive, admin rehost UI/API, and K/D correction behavior are **not yet implemented**; do not use these new schema fields for real imports until those flows are complete.
- **NEXT ACTION:** Extend `r6stats/replay_archive.py` with a verified multi-segment manifest while keeping format 1 unchanged. Add rehost preview/import/reparse endpoints and explicit browser controls, then test archive/reparse/delete and normal-import regressions. After that implement auditable final-K/D corrections with Rating ineligibility for incomplete maps. Run full pytest, admin build, publishing/privacy checks, and local commits. No real replay import, publish, push, or live Rating change during implementation.

## CURRENT RESEARCH AND PRODUCT CHECKPOINT — 2026-10-01 03:58 UTC

- HEAD on arrival at this checkpoint: `8fac089`, an external generated-data commit adding a fourth Fall 2026 NECC map. The working tree contained only the objective validation script edit from the ongoing research. Read-only SQLite inspection found four imported maps (Fortress 7–3, Border 6–8, Kafe 8–6, Border 7–5), each with a private single-folder archive. No production database or archive was modified in this research step.
- **Predeclared objective validation completed:** Three new development maps from `Y10S4_01` build `9486312`, `Y11S1_Alpha03` build `9658832`, and `Y11S2_Alpha04` build `9769907` add 35 rounds, 11 public objective rounds, and 12 completion events. The fixed timer-run minimum `<=0.10 seconds` identifies all 11 rounds with zero false positives or negatives, and its qualifying-run count equals the public completion count in every round. The combined seven-map diagnostic covers 88 rounds, 27 objective rounds, and 32 completion events with no count disagreements. This is occurrence evidence only; actor identity is unresolved. No objective credit, parser rule, Rating feature, or private match was changed.
- **User's new priority:** Protect the current normal one-folder scan → preview → explicit NECC confirmation → import → archive → statistics flow. Add an opt-in multi-segment rehost flow with explicit segment order, counted/excluded physical rounds, independent logical score, archive/reparse safety, and then an auditable final-map K/D-only correction. No forfeit workflow. Manual correction must make an incomplete map Rating-ineligible and must not change round-derived KPR, KOST, operators, trades, or other events. The 60 clean North America Stage 2 rows remain sealed for Rating evaluation.
- **NEXT ACTION:** Commit the objective diagnostic result locally. Inspect `r6stats/db/repository.py`, `r6stats/replay_archive.py`, `r6stats/admin/server.py`, and `web/src/admin.tsx` import/detail flows with the four-map read-only database state. Add normal-import regressions first, then implement the opt-in logical rehost path in temporary test databases, preserving raw physical files and existing archives. Run pytest, admin build, and archive/publishing privacy tests before a local checkpoint commit. Do not import new replays into the real SQLite during implementation.

## CURRENT RATING RESEARCH CHECKPOINT — 2026-09-30 20:22 UTC

- **Predeclared objective diagnostic:** The four previously audited development maps have 53 rounds and 16 rounds with public plant/disable events. A timer-run minimum at or below 0.10 seconds identifies those 16 rounds with zero false positives within that inspected sample, but this is an observed correlation, not a parser completion or actor rule. Before considering it further, audit three additional distinct development builds without changing the threshold: Six Invitational NIP–Weibo Clubhouse (SiegeGG 3073/game 5718), Salt Lake City Major DZ–FaZe Clubhouse (3554/6677), and South America Stage 1 LOUD–Black Dragons Lair (4112/8360). Save read-only packet audits under ignored `data/research/diagnostics/`, compare public round events only for validation, and leave live objective attribution unchanged. None is the reserved September final event.
- HEAD before this checkpoint: `d4da4c9`, following parser/rehost recovery `68b0772`. The predeclared plan `research/nal-rehost-refit-plan.json` exactly matched rebuilt dataset SHA-256 `2454eb35ebe06df8d91f950b17cab8cea0a26384d9c40cbdd786f7e4f11b04de`. No new replay was downloaded. Current data are 56 maps, 560 player-map rows, 407 clean; five recovered rehosts contribute 33 clean rows. The sixth split candidate 7999 is excluded because a physical round is missing. All 605 public winners align; zero final operators are unresolved. Objective actor attribution remains unresolved and its inputs are zero.
- **Same-form development fit:** `expanded-raw-20260930T202146Z` used 299 earlier-event clean rows, the same raw nine-family standardized ridge alpha 1 form, and 32 previously viewed August EWC rows. August MAE 0.03453, RMSE 0.04626, 71.9% within 0.05; the prior 292-row model on this same validation data has MAE 0.03484. Every varying raw-unit slope changed by <0.007. Teamkill events in training rose to nine. Objective coefficient remains zero only because the feature is constant zero; this does not estimate its effect. This remains provisional, not a deployable rating.
- **Grouped development check:** `group-cv-20260930T202147Z` yields pooled earlier-event MAE 0.03647 for raw features versus 0.05288 weighted operator mean, 0.05834 round-z, and 0.10403 segment-z. Raw is best in all seven event folds. Twenty-three of 71 operator-side groups have fewer than 20 rounds. Neither September event was scored in these experiments; the 60 clean North America Stage 2 Rating rows remain prospectively reserved and untouched. Europe MENA Stage 2 is historical only. No live rating, SQLite, publish, or push action occurred.
- **NEXT ACTION:** Continue packet-level objective actor recovery on earlier-event development replays. Compare timer/defuser possession and player identity signals against several builds without using public Rating targets as parser input. A candidate must identify a completed plant/disable and the correct actor independently before any production credit or private reparse. Keep rating-formula, action-start logic, and reserved final event unchanged. Resume with `.\.venv\Scripts\python.exe research\objective_timer_audit.py <development replay folder> <SiegeGG match ID> <game ID>` and review `research/objective-coverage.md`, `research/defuser_identity_probe.go`, and ignored diagnostics. Record any blocker and a concrete next experiment here before stopping.

## CURRENT RATING RESEARCH CHECKPOINT — 2026-09-30 20:20 UTC

- **Predeclared next operation (after `68b0772`):** `research/nal-rehost-refit-plan.json` fixes the rebuilt dataset SHA-256 `2454eb35ebe06df8d91f950b17cab8cea0a26384d9c40cbdd786f7e4f11b04de`, 299 earlier-event training rows, 32 previously viewed August EWC development rows, the same nine-family raw standardized ridge alpha 1, and the prior 292-row experiment. This plan is being committed before the fit. The 16 historical and 60 reserved September rows are excluded from scoring. Run `.\.venv\Scripts\python.exe research\expanded_fit.py --plan research\nal-rehost-refit-plan.json`, then `.\.venv\Scripts\python.exe research\group_cv.py` for grouped development checks only.
- HEAD before this checkpoint: `a86628d`. The June 18 North America Stage 1 replay build `9734089` changed its in-round player-ID and UI-ID property markers. The old local `siege-dissect` found header players but no scoreboard players and panicked in `PlayerStats()`. Exact-build support now decodes all 24 physical rounds in split archives 7998 and 7999. All 24 have the structural action-start marker and all 120 attacker player-rounds have pre-action final operator IDs. The existing action-start boundary algorithm was not changed. A fallback now returns a clear unsupported-layout error when a future build decodes no in-round player records.
- **Rehosts:** M80–Cloud9 7998 / 3905 Clubhouse has 10+3 physical rounds; its first R10 is superseded by the second segment. The unique score-continuous 12-round map ends Cloud9 5–M80 7, and all 12 public round winners align. Map-wide replay K/D is 85–86 versus public 86–86; its three mismatched player rows remain excluded and seven exact K/D rows are admitted. DarkZero–Wildcard 7999 / 3906 has 2+9 physical rounds but a missing Wildcard win between segments (2–0 → 2–1); the logical layer rejects it and does not invent a round. Five rehosts are now admitted, one remains unresolved. Exact folder/filename mapping and ignored diagnostics are in `research/sources.json` and `data/research/diagnostics/rehost/`.
- **Rebuild/quality:** A complete cached `research/pipeline.py all` run with the rebuilt parser produced 56 logical maps, 560 player-map rows, 407 clean rows, 153 excluded rows, 605/605 public winners aligned, and zero unresolved final operators. Fifty-three maps have exact map-wide K/D; three are one replay kill short. Objective actor attribution remains unresolved; unverified Y11 plants/disables are omitted. The private NECC SQLite database was not written. A read-only reparse of all three UAH maps still matches all 85 operator usage rows.
- **Testing:** 64 Python tests passed, one optional test skipped, and six subtests passed. Go tests, vet, and the opt-in real June 18 R01 player/action marker test passed. No web changes, push, publish, or live rating change. The 60 clean North America Stage 2 rows remain sealed for Rating evaluation; their rating predictions/residuals have not been computed. The 16 Europe MENA Stage 2 rows remain historical.
- **Model status:** The most recent fixed-form raw development experiment is still the 292-row provisional fit with previously viewed August EWC MAE 0.03484; grouped earlier-event raw MAE 0.03659 versus weighted operator-relative 0.05215. The seven newly recovered clean rows have not yet been fitted. Objective slope is unidentified because objective inputs are zero. No candidate is frozen for reserved final evaluation.
- **NEXT ACTION:** Commit this tested parser/rehost recovery locally. Then predeclare a same-form raw ridge alpha-1 development refit on the expanded 299 earlier-event clean rows, holding August EWC as previously viewed validation and both September events out. Compare coefficients with the 292-row model and run grouped earlier-event checks; do not score the reserved North America Stage 2 Rating targets. Resume with `.\.venv\Scripts\python.exe research\quality_report.py`, `Get-FileHash data\research\experiments\player_maps.jsonl -Algorithm SHA256`, then `.\.venv\Scripts\python.exe research\expanded_fit.py --plan research\<new-plan>.json` only after recording that plan. Continue objective actor packet investigation; do not interpret the zero objective coefficient or reparse the private database.

## CURRENT RATING RESEARCH CHECKPOINT — 2026-09-30 19:59 UTC

- HEAD before this checkpoint: `d010033`. The deliberate post-rehost/objective-safeguard development experiments were appended to `research/experiment-log.jsonl`; no raw replay, private SQLite, push, publish, or live rating change. The 60 clean North America Stage 2 player-map rows remain an untouched Rating final test; no model prediction or residual for them was computed.
- **Data:** 55 logical maps, 550 player-map rows, 400 clean; 26 clean rows from four recovered rehosts, two parser-panic rehosts still excluded. All 55 derived caches include a Python adapter hash. Zero unresolved final operators. Strict K/D/round quality gates unchanged; 53/55 map-wide K/D totals agree, 593 public round winners align, 150 rows remain excluded. Objective player attribution is unresolved and current safeguarded research observations contain zero credited objectives. The private NECC database still contains 12 impossible defender-credited plants and one suspect disable; it was read only and not reparsed.
- **Fixed-form provisional refit:** the predeclared nine-family raw ridge alpha 1 experiment `expanded-raw-20260930T195825Z` trained on 292 earlier-event clean rows (up from 266) and validated on the previously viewed 32 August EWC rows. August MAE 0.03484, RMSE 0.04632, 72% within 0.05; the prior 266-row model on the newly safeguarded August inputs gives MAE 0.03466. Most raw-unit slopes changed by <0.007; clutch changed by -0.061, objectives became exactly zero because every objective input is unresolved. This is a data-integrity diagnostic, not a deployable rating candidate.
- **Grouped development check:** `group-cv-20260930T195850Z` on 292 earlier-event rows gives pooled MAE raw 0.03659, weighted operator mean 0.05215, operator round-z 0.05747, segment-z 0.10442. Raw wins all seven event folds. Of 71 operator-side groups, 23 still have fewer than 20 rounds. This reproduces the earlier raw-versus-operator result after admitting rehosts and discarding false objective credits.
- **NEXT ACTION:** Continue replay-derived objective actor recovery across builds. The June, July, April, and August development examples show a reliable timer progress pattern but no consistently unique score-bonus actor; investigate defuser possession and entity packet paths before any production credit. Preserve all raw archives. Consider the two parser-panic rehosts after objective investigation. Do not interpret the zero objective slope, tune on UAH players, or inspect reserved final Rating residuals. Resume with `.\.venv\Scripts\python.exe research\objective_timer_audit.py <development replay folder> <SiegeGG match ID> <game ID>`, `.\.venv\Scripts\python.exe research\rehost_audit.py 7998 7999`, and `.\.venv\Scripts\python.exe -m pytest -q`.

## CURRENT RATING RESEARCH CHECKPOINT — 2026-09-30, objective actor audit

- HEAD before this checkpoint: `b746430`. The 55-map/550-row/400-clean-row rehost dataset remains intact after full cached rederivation. All 55 normalized cache records now include the Python adapter hash, so future adapter changes invalidate stale derived data. Map/round/K-D quality gates, 593 aligned public round winners, and zero unresolved final operators remain unchanged. No push, publish, or local NECC database write occurred.
- **Critical objective finding:** the old normalized development data included 38 plants credited to a defender with a resolved profile, four more credited to a defender with a nil-profile username fallback, and five disables whose actors all disagree with the public round log. The raw Y11 defuser timer listener's fixed-offset identity does not match any player in the known June replay. Four development maps show genuine plants as timer runs reaching 0.001–0.074 seconds, but near-zero alone is not a safe actor signal. Nearby +100 scoreboard changes sometimes match the planter, sometimes name another teammate or several defenders, and sometimes are absent. Details and exact files in `research/objective-coverage.md`.
- The adapter now rejects role-impossible objectives and requires an explicit verified actor source for Y11 completions. All 55 cached professional maps were rederived; no objective player-rounds remain credited in current research observations. This prevents false attribution but leaves real plants/disables **unresolved**. Objective weight and KOST values involving objectives remain incomplete. `collegiate_v1` formula and the NECC database were not changed.
- A read-only query of private `data/r6stats.sqlite` found 12 stored plant events credited to defenders and one stored disable. These are suspect historical data requiring a trustworthy parser recovery and controlled reparse before they can be corrected; no local import/reparse was performed. Existing public site was not regenerated or published.
- **Model/final-test status:** last completed expanded raw fit remains 266 earlier training rows, August EWC development MAE 0.03464; grouped raw development MAE 0.03665 versus best operator-relative 0.05266. The four rehost maps and objective safeguard have not yet been fitted. The 60 clean North America Stage 2 rows remain untouched for Rating evaluation; the 16 Europe MENA Stage 2 rows are historical only.
- **NEXT ACTION:** Predeclare and run a provisional same-form raw nine-family development refit on the 292 clean earlier-event rows and 32 previously viewed August EWC rows to measure the effect of 26 recovered rehost rows and removal of false objective credits. Treat the objective component as unidentified (all current values are zero), compare slopes to `expanded-raw-20260930T160858Z`, and do not evaluate reserved September North America ratings. Then continue packet-level objective actor recovery, testing candidate signals against multiple builds without using public targets as parser input. Exact resume: `.\.venv\Scripts\python.exe research\pipeline.py all` (cached), `.\.venv\Scripts\python.exe research\quality_report.py`, `.\.venv\Scripts\python.exe research\objective_timer_audit.py <development replay folder> <SiegeGG match ID> <game ID>`.

## CURRENT RATING RESEARCH CHECKPOINT — 2026-09-30, rehost admission

- HEAD before this checkpoint: `96e527b`. Four score-continuous rehost maps are now admitted through `research/rehost_pipeline.py` and explicit multi-segment source metadata. The cached pipeline rederived them without reparsing the existing 51 maps. No push, publish, SQLite import, live rating change, or reserved-final Rating evaluation occurred.
- **Dataset:** 55 complete logical maps, 550 player-map rows, 400 clean rows (up from 51/510/374). The four recovered maps contribute 26 clean and 14 excluded per-player K/D rows. All four have public score, round count, roster, and map-wide K/D agreement; all 48 added round winners align with public logs. Across the full dataset, 53/55 map-wide K/D totals agree, 593 round winners align, and zero final-operator player-rounds are unresolved. The quality report has 150 excluded rows. Quality gates were not weakened.
- **Rehost provenance:** each map's ordered physical folders and excluded filename are fixed in `research/sources.json`; the ignored diagnostic `pipeline-mapping.json` records every physical filename, SHA-256, replay ID, logical number, and exclusion reason. The derived cache signature includes the parser binary, source mapping, and all physical file metadata. Two other split archives, 7998 and 7999, remain excluded due to the low-level scoreboard panic.
- **Objective status:** replay-derived plants/disables remain incomplete against public development targets. No parser or statistic formula changed. The next investigation must distinguish timer zero/near-zero values from true completed plants and disables using development rounds and independent win/feedback evidence; do not infer completion from a timer threshold alone.
- **Model status:** last fixed raw development fit remains 266 training rows and August EWC MAE 0.03464; grouped earlier-event raw MAE 0.03665 versus best operator-relative 0.05266. Recovered rows have not yet been fitted. The 60 clean North America Stage 2 rows remain a prospectively reserved untouched final test; the 16 Europe MENA Stage 2 rows are historical only.
- **NEXT ACTION:** Investigate objective packet semantics in several complete development replays, then make only a validated extraction fix. Re-derive cached maps if the parser changes and rerun strict quality checks. After data is trustworthy, rerun the **same** nine-family raw ridge setup on the expanded earlier-event training set with August EWC development validation; compare coefficient drift against `expanded-raw-20260930T160858Z`. Do not evaluate reserved September North America Rating residuals. Resume with `.\.venv\Scripts\python.exe research\pipeline.py all` (cached), `.\.venv\Scripts\python.exe research\quality_report.py`, and `.\.venv\Scripts\python.exe research\defuser_probe.py <development replay folder>`.

## CURRENT RATING RESEARCH CHECKPOINT — 2026-09-30 19:30 UTC

- HEAD before this checkpoint: `8c99a53`. No push, publish, SQLite import, or live rating change.
- **Current evidence:** 51 complete maps, 510 player-map rows, 374 clean rows from 10 events and 38 distinct official ZIPs. Seven North America Stage 2 maps add 60 clean rows and are prospectively reserved **event-wide** for a new untouched final test. The 16 Europe MENA Stage 2 rows were evaluated once earlier and remain historical. All 51 maps were rederived with the current parser binary; zero final-operator rounds are unresolved. Quality gates are unchanged.
- The seven reserved maps and clean-row counts are DarkZero–Wildcard Villa 7–3 (10), For Fun–SSG Kafe 2–7 (10), M80–Shopify Villa 3–7 (8), 100 Thieves–Cloud9 Nighthaven Labs 0–7 (10), Shopify–For Fun Border 7–1 (8), SSG–Five Fears Nighthaven Labs 7–4 (8), and Wildcard–100 Thieves Chalet 5–7 (6). All have exact map, score, rounds, ten-player roster, and profile-verified alias agreement. Ten new per-player K/D mismatches remain excluded. The seven ZIPs were integrity-checked and cached under ignored `data/research/`.
- All 25 rounds in the first three September maps use replay code build `9883691`, which had fallen below the existing action-start version gate. Raw diagnostics found the 0→179 structural action-start timer in all 25 rounds and the final attacker operator ID in pre-action packets for all 125 attacker player-rounds; 80 initial picks differ from final `RoleName`. The exact build was enabled in the existing action-start parser path; its boundary logic was not changed. Rebuilt parser resolves all 510 included player-map rows' operators. Go tests/vet and 53 Python tests pass; one optional integration smoke test skips.
- The new event was reserved in commit `9c2bfbf` before any rating residual was inspected. `research/final-test-reservation.json` records the event-wide rule, and the pipeline now rejects an unreserved source from that event. No Rating model has been fitted on the 51-map dataset. `research/expanded-fit-plan.json` fixes the next development experiment: train raw nine-family ridge on seven earlier events (266 clean rows), use the previously viewed August EWC event (32 clean rows) for development validation, compare raw-unit slopes against the 118-row historical fit, and exclude both September events. Do not run final evaluation until a candidate and acceptance rule are frozen separately.
- Current quality audit: 136 excluded rows (135 per-player K/D discrepancies and two unverified aliases with one overlap); 49/51 map-wide K/D totals agree, all 545 public round winners align, and 64/910 multikill notes disagree. See `research/quality-report.md`. The new reserved event contributes no map-wide exception.
- The preregistered fixed raw fit `expanded-raw-20260930T160858Z` trained on 266 clean earlier-event rows and validated on the previously viewed 32 August EWC rows. August MAE 0.03464, RMSE 0.04663, 72% within 0.05, max error 0.13593; the prior 118-row fit gave MAE 0.03528, RMSE 0.04779 and the same 72% within 0.05. The marginal 0.00064 MAE improvement is not deployment evidence. Eight teamkill events now enter training; its raw-unit coefficient moved from +0.052 to -0.211. The objective slope moved from -0.107 to -0.008 and remains essentially zero. Other major raw-unit slopes are comparatively stable. Both September events were excluded and their ratings were not evaluated in this run.
- The grouped development check `group-cv-20260930T161201Z` leaves out each of the seven pre-August events in turn, recalculating operator baselines from the other six each time. Pooled 266-row MAE: raw 0.03665, weighted operator mean 0.05266, operator round-z 0.05872, operator segment-z 0.10827. Raw wins all seven event folds (range 0.03135–0.04361). Of 70 observed operator-side groups in full pre-August training, 23 have fewer than 20 rounds. Only 5 held-out operator player-rounds are unseen across all folds, so sparse unseen operators do not explain the operator-relative gap. August and both September events were excluded from this check.
- Pre-August objective coverage is incomplete: across 266 clean training player-maps, public targets record 55 plants and 7 disables versus replay-derived 23 and 1. Previously viewed August's 32 clean rows add public 11/4 versus replay 1/0. An 11-round June North America Lair replay has public four plants but siege-dissect raw feedback contains only 78 kill events and no objective entries. Details in `research/objective-coverage.md`. The near-zero objective fit weight therefore cannot establish that objectives lack value. No model/stat formula changed.
- A parser-quality probe briefly inspected **non-rating** objective totals for the seven newly reserved North America maps and raw feedback for one map before the reservation scope was tightened. This exposure is recorded in `research/final-test-reservation.json`. No reserved Rating prediction or residual was calculated, and no model choice uses the reserved objective evidence. Future objective investigation must use development events only.
- Objective packet clue: the complete June Lair replay has 1,297 occurrences of the existing defuser timer listener tag, but its near-zero strings include `0.023` and `0.024` and never begin `0.00`, while `defuse.go` requires prefix `0.00` to emit a completion. This explains the missing feedback path in that replay but does not prove a safe replacement completion rule. No parser or live objective logic changed. See `research/objective-coverage.md` and `research/defuser_probe.py`.
- The user's newest continuation instructions prioritize real rehost diagnosis and generic logical-round handling ahead of further objective work. The excluded cached candidates include FURIA–FaZe (8554/4115; 8+5 physical rounds vs public 12), M80–Shopify (8007/4147; 8+5 vs 12), SSG–DarkZero (8009/4149; 2+11 vs 12), Cloud9–For Fun (8019/4136; 2+11 vs 12), M80–Cloud9 (7998/3905; 10+3 vs 12), and DarkZero–Wildcard (7999/3906; 2+9 vs public 12). Their ZIPs and targets are cached; none is included. Do not remove a round solely to match public K/D, and do not use a hard time-gap threshold.
- Four cached split maps now have a unique score-continuous rehost reconstruction, documented in `research/rehosts.md`: FURIA–FaZe (8554/4115), M80–Shopify (8007/4147), SSG–DarkZero (8009/4149), and Cloud9–For Fun (8019/4136). Each has 13 physical rounds, one excluded final round in segment one, and 12 logical rounds with exactly matching public final score **and map-wide K/D**. The excluded rounds are respectively R08, R08, R02, R02. Preliminary alias/KD audit finds 6+8+8+4 = 26 clean identified player-map rows; none is in the 51-map dataset yet. Real compact score-state fixtures and seven regression tests cover this structural mapping. The generic layer is `r6stats/parser/logical_map.py`; source hashes, segment boundaries, and excluded-round reasons remain intact. No hard rehost time rule is used.
- Two earlier split candidates, M80–Cloud9 (7998/3905) and DarkZero–Wildcard (7999/3906), still panic in the local parser before trustworthy normalization. Their physical archive structures and parser errors are cached; no rounds admitted.
- **NEXT ACTION:** Integrate the four verified logical maps into the reproducible professional research pipeline using explicit multi-segment source entries and expected excluded-round mappings. Recheck exact player IDs and aliases (FURIA `volpz7`/`Dias` now have repeated UUID and official Ubisoft roster evidence), per-player public K/D, score, round winners, and final operators. Re-derive and report before/after counts. Preserve the two parser-panic maps as excluded. Exact resume commands: `.\.venv\Scripts\python.exe research\rehost_audit.py 8554 8007 8009 8019` and `.\.venv\Scripts\python.exe research\logical_rehost.py 8554 8007 8009 8019` (cached official ZIPs, no downloads).

### Previous collection milestone details

- At 15:46 UTC the entire **North America League Stage 2 2026** event was prospectively reserved as a new untouched final test in `research/final-test-reservation.json`. Ten September 9–10 official Ubisoft replay pages (8283–8292) and corresponding SiegeGG match records (6168–6177) have map/score metadata and replay download links. Do not inspect rating residuals or use any of this event for feature selection. Mark every included source `reserved_for_final_test: true`. The earlier September Europe MENA Stage 2 evaluation remains historical only.
- HEAD before this checkpoint: `ebaf33b`. Keep this section current after each research milestone and commit code/documentation locally. Do not push or publish.
- Quality-gated data: 44 complete maps, 440 player-map rows, 314 clean rows, nine parsed events. All included operator rounds resolve. September Stage 2's 16 rows were evaluated once and are now a historical benchmark. No new model has been fitted on this expanded dataset.
- Fully parsed and target-matched events: Six Invitational 2026, Asia Pacific Kickoff 2026, Salt Lake City Major 2026, Asia Pacific League Stage 1 2026, Europe MENA League Stage 1 2026, Esports World Cup 2026, Europe MENA League Stage 2 2026, North America League Stage 1 2026, and South America League Stage 1 2026. Thirty-one distinct ZIPs back their 44 included maps.
- North America Stage 1 addition: official M80–DarkZero July 2 ZIP `BR62026_NAL_S1D8_DZvM80.zip`, replay folder `Match-2026-07-02_15-28-09-4828`, SiegeGG match `4133` / game `7860`, Kafe 7–0. Both targets cached; 8 of 10 rows pass exact K/D; 2 excluded for kill attribution differences. Previous HTTP 500 was transient. No event is currently awaiting target matching.
- Excluded within matched data: 126 player-map rows, including 125 per-player K/D discrepancies and two unverified aliases (one overlap); see `research/quality-report.md`. No event has been rejected in full. The FURIA–FaZe rehost archive remains cached but excluded as a fragmented map.
- Best current validation: raw nine-family ridge `grouped-operator-20260930T103355Z`, August EWC 32 rows, MAE 0.0353. Operator-relative variants were worse. Historical September Stage 2 benchmark: 16 rows, MAE 0.0632; do not tune on it. `collegiate_v1` remains live and unchanged.
- South America Stage 1: official [LOUD–Black Dragons July 4 match](https://www.ubisoft.com/en-us/esports/rainbow-six/siege/match/8551) archive `BR62026_SAL_S1D7_LOUDvBD.zip`, replay `Match-2026-07-04_12-56-31-39776`, SiegeGG match `4112` / game `8360` was fully matched: Lair 12 rounds, 7–5, ten players, zero unresolved Attack operators; eight player rows passed exact public K/D, two remain excluded. `ROMEO.BD` ↔ `MRZLL` and `Gabu7z.LOUD` ↔ `GABU` alias evidence is recorded in `sources.json`.
- Source discovery helper `research/preflight_ubisoft.py` scanned official match IDs 8545–8560 and cached all pages. Four July 4–5 South America candidates have exact SiegeGG match pages and HTTP 200 player-stats targets: FURIA–FaZe (Ubisoft 8554 / SiegeGG 4115), LOUD–FaZe (8557 / 4118), Imperial–Black Dragons (8558 / 4119), FURIA–Fluxo W7M (8559 / 4120).
- The new `research/collect_candidates.py` cached/ZIP-verified/extracted the FURIA–FaZe archive and both targets. Its Clubhouse replay is fragmented across two folders: 8 rounds with 4–4 score and 5 rounds with 2–3 score, totaling 13 versus the public 7–5/12 rounds. Exclude this candidate until the rehost/duplicate round can be independently identified; do not guess or merge it into observations. Cache is retained under ignored `data/research/`.
- Three July 5 South America maps were added with exact roster and Rating targets: LOUD–FaZe (6/10 clean), Imperial–Black Dragons (10/10), FURIA–Fluxo W7M (8/10). The 6 excluded rows have per-player kill attribution differences, not map/score/round or identity mismatches. `LOBEX.FX` to SiegeGG `L0BINN` is verified through the matching replay UUID and stats.cc account history. All three maps have zero unresolved Attack operators.
- Four North America Stage 1 official replays were cached, ZIP-tested, parsed and matched to SiegeGG: M80–Five Fears Lair 7–2 (Ubisoft 8010 / SiegeGG 4127, 9/10 clean), Shopify Rebellion–DarkZero Clubhouse 2–7 (8012 / 4129, 5/10), M80–Wildcard Clubhouse 7–8 (8020 / 4137, 8/10), and DarkZero–Cloud9 Nighthaven Labs 7–2 (8021 / 4138, 8/10). All 42 rounds have final operators; replay rosters and score-by-roster exactly match public targets. JJBlaztful, Kanzen and Bae94 handle variants have independent account/name evidence in `sources.json`. Ten K/D-mismatched rows remain excluded. Quality audit now dynamically lists both map-wide total exceptions: Five Fears–M80 Lair and Europe MENA Stage 1 Chalet, each short one replay kill against public totals.
- Four Europe MENA Stage 1 June 8–9 official ZIPs were collected and parsed. Their replay build `9718747` previously left every attacker unresolved. The existing action-start path was enabled for this exact build after raw diagnostics found the marker in all 43 rounds and pre-action operator packets for all 215 attacker header IDs. Six attacker headers change operator between initial pick and final role; none lack a final role. The rebuilt parser resolves all 215 final operators. The action-start algorithm itself was unchanged. G2–Geekay Fortress 8–6 (Ubisoft 8027 / SiegeGG 3637) contributes 10/10 clean rows; Secret–Heretics Lair 2–7 (8029 / 3639) contributes 8/10. The Virtus.pro–Fnatic target (8025 / 3635) lacks one Fnatic player, and Falcons–Twisted Minds (8032 / 3642) reports 6–5/11 rounds in SiegeGG's API against the complete 7–5/12-round replay and Ubisoft page. Both remain cached but excluded, with no guessed target correction.
- All 35 included maps were rederived under the new parser hash. The two new maps add 18 clean rows. Go unit tests, `go vet`, and focused Python tests (11 passed, one optional smoke test skipped) passed. A read-only reparse of all three private UAH maps exactly reproduced all 85 stored operator usage rows. The expanded `research/quality-report.md` lists 96 excluded rows; 33/35 map-wide totals agree, all 375 public round winners align, and 45/627 multikill notes disagree.
- Four South America Stage 1 official archives and exact SiegeGG targets were cached and ZIP-verified: Imperial–Fluxo W7M (Ubisoft 8531 / SiegeGG 3768), Team Liquid–FURIA (8532 / 3769), FaZe–Ninjas in Pyjamas (8535 / 3772), and Team Liquid–LOUD (8536 / 3773). None entered observations: every candidate replay panics in the local `siege-dissect` `PlayerStats()` at `stats.go:214` while indexing the dynamic scoreboard, including both FaZe–Ninjas folders. The folders and full parser trace remain cached under ignored research diagnostics; treat these as parser failures pending investigation, never as matched rows.
- Six North America Stage 1 official ZIPs and targets were cached. Four complete maps passed map/score/roster/round/alias gates: Outlast–Cloud9 Fortress 4–7 (8005 / 3745, 4/10 clean), 100 Thieves–Five Fears Lair 7–4 (8006 / 4150, 8/10), For Fun–Wildcard Fortress 2–7 (8008 / 4148, 6/10), and 100 Thieves–Spacestation Fortress 7–5 (8022 / 4139, 5/10). Their 43 rounds have zero unresolved final operators. Logan/Logger, Atom/TRA, Raid/RAIDBULLYS, Rival/GNRIVAL, JJBlaztful, Kanzen and Bae94 mappings have independent evidence in `sources.json`. Seventeen K/D-mismatched rows remain excluded. M80–Shopify (8007 / 4147) has 8+5 replay rounds and Spacestation–DarkZero (8009 / 4149) has 2+11, each against a 12-round public map; both remain cached and excluded as fragments with an extra/overlapping round.
- Four more June 18–19 North America ZIPs and targets were cached but none passed: M80–Cloud9 (7998 / 3905) has 10+3 physical rounds against 12 public; DarkZero–Wildcard (7999 / 3906) has 2+9 against 12; M80–Outlast (8001 / 3741) and Cloud9–Five Fears (8003 / 3743) are single-folder replays but both hit the same `PlayerStats()` scoreboard panic as the June 20 South America candidates. All remain cached and excluded.
- Three July 2 North America maps passed exact map/score/roster/round/alias gates: Five Fears–Wildcard Bank 8–7 (Ubisoft 8015 / SiegeGG 4132, 6/10 clean), Shopify–Spacestation Fortress 7–5 (8017 / 4134, 7/10), and Outlast–100 Thieves Lair 1–7 (8018 / 4135, 8/10). All 35 rounds resolve final operators. Cloud9–For Fun (8019 / 4136) has two physical folders with 2+11 rounds against a 12-round public map and remains excluded. Nine new K/D discrepancies remain excluded. Dataset reaches 298 clean rows.
- Two July 3 North America maps passed all structural and identity gates: Shopify–Outlast Fortress 7–4 (Ubisoft 8023 / SiegeGG 4140, 10/10 clean) and For Fun–Five Fears Bank 8–6 (8024 / 4141, 6/10 clean). All 25 rounds resolve final operators; four K/D-mismatched rows remain excluded. The dataset now exceeds the first 300-clean-row target without relaxing quality gates.
- **NEXT ACTION:** Identify a later distinct event with official replay archives and SiegeGG Rating targets, ideally 50+ clean rows, and mark the entire event `reserved_for_final_test` before examining any model error on it. Keep the already-examined September EML Stage 2 rows as historical only. After reserving the new final event, run a deliberate grouped train/validation experiment on earlier events and measure coefficient stability against the prior fit; do not use reserved ratings in selection.

## Part 1: private replay archive

Implemented and tested. Confirmed imports through the CLI or local admin create a private, map-ID keyed copy in `data/replay-archive/<season-slug>/<map-id>/` after SQLite import succeeds. A staging copy is made first, then verified against the import fingerprint before it becomes a completed archive. Rejected, preview-only, and failed imports do not produce a completed archive. The original MatchReplay folder is never moved. The manifest contains replay identity, original source/folder, parser binary hash, map, round count, physical R## filenames, sizes, and SHA-256 digests.

The admin map page shows archive status, Verify, Open in Explorer, Backfill older map, and Reparse from archive. Reparse checks archive integrity and replay identity before the existing transactional map replacement. Metadata, roster identities, and map ID remain intact. The map delete confirmation explicitly covers both statistics and the archived replay; the archive is parked while database deletion runs and restored if database deletion fails. No SQLite schema migration was needed. Public export contains no archive metadata. Publishing stages only `web/public/data/**/*.json`.

The three existing Fall 2026 NECC maps were backfilled from their exact fingerprint-matching source folders without changing stored statistics:

| Map | Map ID | Rounds | Archive status |
| --- | --- | ---: | --- |
| Fortress | `d64d5478cdb3` | 10 | Healthy |
| Border | `8a6357ff307c` | 14 | Healthy |
| Kafe Dostoyevsky | `5adc26f7a402` | 14 | Healthy |

The private archive currently occupies roughly 368 MiB and is ignored by Git. Keep a backup of both `data/r6stats.sqlite` and `data/replay-archive/` for machine failure recovery. Archive and research paths passed `git check-ignore`. The publishing test confirms only generated public JSON is staged, even with a private replay present.

Files: `.gitignore`, `r6stats/replay_archive.py`, `r6stats/cli.py`, `r6stats/admin/server.py`, `web/src/admin.tsx`, `web/src/admin.css`, `tests/test_replay_archive.py`, `tests/test_admin.py`, `tests/test_import.py`, `tests/test_publishing.py`, and `README.md`. The small nil-UUID identity fix and Consulate map label are in `r6stats/parser/models.py`, `r6stats/parser/siege_dissect.py`, and `tests/test_lan_player_identity.py`.

Verification: 49 Python tests passed, one optional real-replay smoke test skipped, six subtests passed. Both public and admin Vite builds passed. The three real archives each verified Healthy after all changes. A live launcher/browser click-through was not performed in this session; admin endpoints were exercised by TestClient. No website publish was attempted.

## Part 2: SiegeGG-style rating research

Thirty-one distinct official Ubisoft replay ZIPs are cached and matched to public SiegeGG targets: 44 complete maps across nine named events, yielding 440 player-map observations. **314 pass strict quality gates.** All currently derived final-operator rounds resolve. Sixteen clean rows from two September Stage 2 maps were reserved for one final evaluation and are now a historical benchmark. Downloads, normalized rounds, targets, and observations stay under ignored `data/research/`. Exact provenance, replay/game mappings, and alias evidence are in [research/sources.json](../research/sources.json).

The professional Y11 operator failure was a parser version gate: six earlier verified online builds took the legacy path despite containing the same structural action-start marker and pre-action final operator IDs used by the current UAH build. The existing action-start boundary logic was enabled for those builds; Solid Snake's valid numeric operator ID was added. The original 375 unresolved attacker player-rounds are now resolved, and read-only reparses of all three UAH maps exactly matched their prior 85 operator usage counts. No private map was reimported.

The [quality audit](../research/quality-report.md) lists all 126 excluded observations: 125 have per-player public/replay K/D discrepancies; two lack independent alias confirmation (one overlaps). Forty-two of 44 map-wide kill/death totals match. Public round logs align on all 478 winners; 59 of 798 multikill notes disagree with replay-derived round kills. Cumulative scoreboard counters were found but their player offsets are not yet reliable enough to correct event attribution. Quality gates were not relaxed.

The new raw nine-family ridge model trained on 118 clean rows from five earlier events. August EWC validation has 32 clean rows: MAE 0.0353, RMSE 0.0478, 72% within 0.05, versus `collegiate_v1` MAE 0.2615. Operator-relative variants with 20-round shrinkage all performed worse. A controlled metric-definition search did not improve independent August validation. The frozen raw model was evaluated once on September Stage 2's 16 clean rows: MAE 0.0632, RMSE 0.0749, 38% within 0.05, maximum error 0.1553, versus `collegiate_v1` MAE 0.2124. Full split, coefficients, thresholds, and dataset hash are in [experiment-log.jsonl](../research/experiment-log.jsonl). The September result is too small and weak to justify deployment. **Do not tune on or rerun this final event.**

The [UAH comparison report](../research/uah_comparison.md) gives per-player map and season experimental ratings and nine component contributions for the current 38 rounds. UAH results were never used to fit the model. `collegiate_v1` remains the only live/default rating, and no website publishing occurred. See [research/README.md](../research/README.md) for definitions, reproducibility, and limits.

Next: independently resolve replay/public kill attribution where possible; add distinct events with verified aliases; reserve a new later untouched final event before further fitting; build more stable operator baselines and teamkill support. Do not implement a runtime candidate or change the default until new held-out evidence supports it.

The North America Stage 1 M80–DarkZero ZIP was downloaded and integrity-checked in ignored research storage. Its seven-round Kafe replay parses with both rosters and zero unresolved Attack operators. SiegeGG's corresponding target recovered from a transient HTTP 500. The match was added to `sources.json` with exact map and roster mapping; eight player rows passed quality gates, and two kill mismatches remain excluded.

The South America Stage 1 LOUD–Black Dragons ZIP was also added: one twelve-round Lair map, 7–5, with eight exact K/D rows and two excluded kill-attribution differences. The ambiguous Romeo/MRZLL and Gabu7z/Gabu names have independent roster/profile evidence recorded in the source manifest.

Three more July 5 South America maps add 24 clean rows: LOUD–FaZe (6), Imperial–Black Dragons (10), and FURIA–Fluxo W7M (8). Their six excluded rows have per-player kill attribution differences. The separate FURIA–FaZe replay ZIP contains two rehost fragments totaling 13 rounds against a 12-round public map and remains excluded pending an independently verified reconstruction.

### Exact continuation commands

Run from the repository root in PowerShell:

```powershell
.\.venv\Scripts\python.exe research\pipeline.py all
.\.venv\Scripts\python.exe research\pipeline.py derive
.\.venv\Scripts\python.exe research\quality_report.py
.\.venv\Scripts\python.exe -m pytest -q
cd web
npm.cmd run build
npm.cmd run build:admin
```

`pipeline.py all` is cached and resumable. Fit scripts append experiment records, so run them only for deliberate new experiments. The recorded September final evaluation must not be rerun or used for tuning. Do not commit `data/research/`, `data/replay-archive/`, private SQLite/settings, `.rec`, or ZIP downloads. Do not publish or change the default rating without user review.
