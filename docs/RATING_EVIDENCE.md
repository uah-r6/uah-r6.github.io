# Historical Rating evidence audit — 2026-10-07

## Current Series Rating availability (2026-10-08)

Series Rating requires complete player-specific map **and** round coverage.
Incomplete series use `rating: null`, with coverage and all other performance
retained. Normal trends contain complete regular-roster Series Ratings only and
need two complete series before drawing a line. The shared series projection
and publishing validator enforce this rule. See [Series experience](SERIES_EXPERIENCE.md).

Blue Placements (1/3 maps, 10/38 rounds) and Michigan (1/2 maps, 12/24 rounds)
are unavailable for all five players. UCF (2/2 maps, 20/20 rounds) stays numeric.
White FSU retains complete player-specific coverage and numeric Series Ratings,
including its substitute. No map Rating, Season/Career Rating, formula, evidence
or archive changed. The older partial aggregate numbers below are historical
diagnostics and no longer public Series Ratings.

Baseline: `1b00f59`. All seven production maps and every participating player
were audited through the existing frozen `siege_style_v3` load/prepare path.
All seven archives verified Healthy against their manifests. Archive health
proves file integrity; it does not prove a complete roster or objective actor.

## Actual archive findings

| Map ID | Series / map | Rounds | Kill sidecar | Objective evidence | Result |
| --- | --- | ---: | --- | --- | --- |
| `b595ffaaec57` | Michigan / Chalet | 12 | Incomplete | Stored normalized evidence | Unrated |
| `076d2b6b02bc` | Michigan / Border | 12 | Complete | Existing valid sidecar | Eligible, preserved |
| `5adc26f7a402` | Placements / Kafe | 14 | Complete | Incomplete core actors | Unrated |
| `8a6357ff307c` | Placements / Border | 14 | Complete | Missing trusted disable | Unrated |
| `d64d5478cdb3` | Placements / Fortress | 10 | Complete | Existing valid sidecar | Eligible, preserved |
| `9db26f1b6ca7` | UCF / Nighthaven Labs | 9 | Complete | Existing valid sidecar | Eligible, preserved |
| `8af0a6db6c39` | UCF / Border | 11 | Complete | Existing valid sidecar | Eligible, preserved |

**No complete new production evidence was recoverable with the current trusted
readers. No sidecar was replaced, no objective actor was corrected, and no
historical statistic or Rating changed.** The three maps remain ineligible.

- **Chalet:** logical rounds 9–12 (segment 2, physical R01–R04) have nine
  players in both stored normalized data and current trusted reader output.
  The missing opponent profile is present in segment 1 but absent from segment
  2. The current kill-reader binary hash equals the stored evidence hash
  (`b2adb09550986f177a4cf1a81f8658c5af34ecb9955bfe81bab9eda06172f921`).
  Collection reproduced `incomplete_or_ambiguous_uid_roster`; all four rounds
  lack usable complete counters. Ten-player participation and cross-segment
  continuity cannot be established. Confirmed logical mapping was retained;
  no player, counter, or round was synthesized.
- **Kafe:** current archive parsing verifies the stored actors at R01, R02,
  R11 and R14. R09's plant occurrence has offset `34204105` but no actor UID
  or actor; its reason is `timer_owner_body_unresolved`. The stored Tallman
  credit therefore cannot receive a complete trusted occurrence sidecar.
- **Placements Border:** all five plant actors match stored credits. R06 has
  a trusted plant by AzoozNewzz, but the stored opponent disable has no trusted
  disable occurrence or completing actor. Current parsing omits that disable.
  Removing the historical credit or attaching another actor would be an
  unsupported correction. The evidence-only repair correctly refuses it.

Raw current-parser JSON for both objective maps, parsed diagnostics, the full
audit, database backup, hash baseline, browser reports and preservation report
are kept privately in the ignored evidence-repair research directory. Raw
replays and private identities are not published.

## Historical eligible-input aggregates (superseded public semantics)

Coverage below applies to every listed player, using actual participation.

| Player | Placements: 1/3 maps, 10/38 rounds | Michigan: 1/2 maps, 12/24 rounds | UCF: 2/2 maps, 20/20 rounds |
| --- | ---: | ---: | ---: |
| Lgon | 1.501034386050 | 1.434264770896 | 1.415675265769 |
| OhWowJay | 1.474568776866 | 1.242348683278 | 1.838290866810 |
| AzoozNewzz | 1.207769246684 | 1.237996958881 | 0.927376305897 |
| Tallman3.14 | 0.814596937757 | 0.934669056495 | 0.823155079647 |
| DinoFireKing | 0.870825762203 | 0.842426825076 | 0.664660243830 |

All 15 player/series rows were recomputed independently from the actual eligible
map raw inputs, evaluated once by the existing formula, and compared within
`1e-12` with exported values and round-weighted full-precision map Ratings.
There is no rounded-map arithmetic averaging. Those partial aggregates are now
historical diagnostics and unavailable publicly; missing maps are never zero.

## Local maintenance

Launch **Start NECC Admin.cmd → Statistics → Audit Rating Evidence**. Each map
shows its ID, rounds, archive health, evidence status and exact exclusion.
**Repair From Healthy Archive** requires an explicit map confirmation. It uses
the same current trusted Go collector/cache and objective archive parser.
Already eligible maps are preserved. This interface is localhost only.

When a future archive extraction genuinely supports repair:

1. The manifest and replay identity must verify against the stored fingerprint.
   Confirmed rehost mapping is authoritative; excluded physical rounds never
   become logical rounds through inference.
2. Complete kill collection must pass `validate_map_credit`, exact logical
   inventory, ten nonnil profiles and a complete team bijection. The standard
   `store()` still refuses conflicting evidence. Explicit incomplete-evidence
   reconciliation rereads the healthy archive, requires identical sources and
   overlapping UID/profile/name/team identities, preserves existing complete
   round counts, and refuses historical display-stat changes. A compare-and-swap
   update stores the entire prior/new evidence in one private audit transaction.
3. Objective backfill copies only occurrence evidence into the stored Match,
   after checking replay, logical rounds, roster, sides and winners. Every
   stored credit must match a unique core completing owner. Actor mismatch,
   missing UID or unsupported occurrence refuses the operation. Historical
   normalized rounds are not replaced by this interface.
4. Objective evidence is sealed to fingerprint, normalized SHA-256 and payload
   SHA-256. Conflicting/stale evidence cannot be overwritten. Stale seals
   explicitly abstain; corrupted payloads fail integrity checks. Sidecar and
   provenance audit insertion are one transaction.
5. Full v3 validation runs again, including native elimination parity,
   profile/name roster, complete unique physical offsets, opening and clutch
   derivation. Repairing one gate never bypasses the next. Genuine remaining
   exclusions are reported. Unsupported checks persist private audit metadata
   with manifest/parser hashes, without changing valid statistics.
6. A successful evidence change regenerates local public JSON. An unsuccessful
   check preserves exports; Regenerate Website Data remains a separate action.
   Publishing is separate and stages only intended generated public JSON.

## Historical public presentation and verification (superseded)

Partial Rating trend points are hollow rings. Their selected detail displays a
subtle **PARTIAL** below the prominent Rating and precise player map/round
coverage. Full points remain filled. Hover, focus, arrow keys, click and tap
retain the existing interaction. Normal trends still exclude substitute
appearances; Series pages retain all actual participants and existing coverage.

Verification: 657 Python tests plus six subtests passed, one optional real-replay
smoke test skipped; 37 frontend tests and both builds passed. Real CMD-launched
admin checks exercised all seven-map audit rows and all three guarded repair
buttons. Public browser checks cover real partial/full points and Series pages
at 1440/1100/768/390px, including hover/focus/keyboard/tap. Player Stats/Sub Stats,
embeds and mocked submission flow regressions passed.

Release `88d858e` was deployed by
[Pages run 37708846633](https://github.com/uah-r6/uah-r6.github.io/actions/runs/37708846633).
The same browser checks passed live at all four widths, including all five
players on each Series page and Lgon's partial Placements/Michigan versus full
UCF points. All 30 live JSON files and both public assets match the release
exactly. Submission configuration remains enabled and available; no cloud
upload was performed. The subsequent documentation checkpoint records the
completed verification. This focused pass is complete; stop here.

Preservation compared all 21 preexisting SQLite tables, all 30 public documents
(only freshness allowed), all four eligible maps and the UCF series exactly,
and 168 protected archive/parser/formula files. All seven archives remain
Healthy; SQLite integrity and foreign keys pass. Private audit metadata is the
only database addition. Frozen coefficients, v2 snapshots, operators, KOST,
plants/disables, kills/deaths, clutches, highlights, identities, appearances,
ownership, scores and grouping are unchanged.

Read-only continuation check:

```powershell
.\.venv\Scripts\python.exe scripts/verify-rating-evidence-repair.py verify
.\.venv\Scripts\python.exe scripts/verify-rating-evidence-admin-ui.py
```

The verifier's `baseline` mode refuses to overwrite an existing backup.
`--repair` on the admin browser verifier is an explicit local maintenance action.
Do not restart parser research or change Rating gates as part of this pass.
