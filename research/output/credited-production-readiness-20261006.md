# Credited-count production readiness — 2026-10-06

This review supersedes historical pending-permission text for the explicitly
authorized count migration. Earlier seals and failed hypotheses remain intact.

| Feature | Status | Source / migration policy |
| --- | --- | --- |
| Kills, K/D, KPR, side kills | READY | Direct stable-UID round counter deltas on complete whole maps; 280 official agreements, zero mismatches. Native supplemental ten agreements remain separate. |
| Deaths | READY | Preserve actual victim elimination counts; 200 official map agreements. DBNO adds no death. |
| Multikill sizes/extra | READY | Credited round totals: 200 official size breakdowns and 207 public round summaries agree. No event timing needed. |
| KOST Kill component | READY | Credited round count > 0; preserve objective/survival/legacy trade flags. |
| Opening kills/deaths | NOT READY | Credited owner and DBNO-versus-final-elimination ordering unresolved; retain legacy features. |
| Trades/refrags | NOT READY | Credited-victim identity and timing anchor unresolved; retain legacy policy and document reset limitations. |
| Pivot kills/deaths, untraded kills | NOT READY | Credited event association unresolved; retain legacy values. |
| 1vX | PARTIALLY READY | Preserve final deaths/actual winner; legacy chronology retains known reset limitations. No new migration. |
| Plants/disables | READY | Preserve published supported completing-owner corrections and unsupported abstentions. |
| Headshots/HS% | PARTIALLY READY | Keep finisher shot bits and finisher denominator; credited-owner shot metadata unresolved. |
| Rating input compatibility | READY | Original events and immutable v2 snapshots; exact eight-feature formula/final MAE 0.03623 unchanged. |

## Current preview

Seven maps /82 rounds /816 player-rounds, 575 final elimination records and 28
objective records. Verified backup, complete tables, archive/public hashes and
snapshots are private under `data/research/production-kill-migration-20261006/`.
Every original table and unrelated public field is compared with this baseline.
New sidecars never rewrite raw events or metadata.

Six complete maps (70 rounds) qualify. Entire 12-round Chalet remains legacy:
its rehost's last four rounds have nine distinct participants. No missing player
or counter is synthesized, and the ten-profile rehost guard remains unchanged.

| Player | Kills before → after | Deaths | KOST rounds after /82 |
| --- | ---: | ---: | ---: |
| AzoozNewzz | 57 → 57 | 61 | 50 |
| DinoFireKing | 36 → 36 | 51 | 50 |
| Lgon | 82 → 81 | 48 | 54 |
| OhWowJay | 91 → 91 | 50 | 58 |
| Tallman3.14 | 36 → 37 | 63 | 41 |

Dino's KOST changes 51→50 because a finisher-kill round no longer has a credited
Kill flag and its other components do not qualify. This is an expected supported
change. The private sealed preview includes every map/player's complete old/new
stats, K/D, KPR, multikill-size breakdown and unresolved notes. All five season
Ratings are exactly unchanged, as are objectives, operators, clutches,
opening/trade/pivot/untraded counts and metadata. Coverage is70 credited /12
legacy rounds per tracked player, explicitly a mixed-source season.

## Unresolved research

Nina/OSAdinho and the eight absent kind-5 targets remain unresolved. No counter
increment is linked to a victim by proximity or totals balancing. Kind-5 is not
established as universal. Kheyze's reviewed credit arrives after his own death;
batch +2 packets cannot provide two timestamps. Positive fine countdown brackets
support serialized relative bands only; reset/zero/terminal/missing/legacy
boundaries refuse. These limits do not block independently READY count features.

## Rollback

Stop the admin server, restore verified `before.sqlite` to
`data/r6stats.sqlite`, and restore `before-public/` to `web/public/data/`.
Original normalized events remain available if the overlay is disabled. Never
remove raw replay archives or historical player identities to undo derived stats.
