# Professional replay rehosts — physical and logical rounds

The official replay ZIPs below contain two physical `Match-*` folders for one public competitive map. `research/rehost_audit.py` saves every source `.rec` filename, hash, replay ID, timestamp, roster, team score transition, winner, site, kill, opening, objective, and operator under ignored `data/research/diagnostics/rehost/<official-match-id>/`. `research/logical_rehost.py` applies the generic `r6stats.parser.logical_map.stitch_segments` score-continuity rules without altering either segment. Public K/D is checked only **after** the score transition identifies the excluded round.

| Official / SiegeGG | Map | Physical folders | Score reset at rehost | Excluded physical round | Logical result | Map-wide replay/public K-D | Clean identified rows, preliminary |
| --- | --- | ---: | --- | --- | --- | --- | ---: |
| FURIA–FaZe, 8554 / 4115 | Clubhouse | 8 + 5 | 4–4 → 3–4 | first folder R08, FURIA win | FaZe 7–5, 12 rounds | 94–94 / 94–94 | 6/10 |
| M80–Shopify, 8007 / 4147 | Lair | 8 + 5 | 3–5 → 3–4 | first folder R08, Shopify win | M80 7–5, 12 rounds | 80–80 / 80–80 | 8/10 |
| SSG–DarkZero, 8009 / 4149 | Nighthaven Labs | 2 + 11 | 0–2 → 0–1 | first folder R02, DarkZero win | DarkZero 7–5, 12 rounds | 88–89 / 88–89 | 8/10 |
| Cloud9–For Fun, 8019 / 4136 | Bank | 2 + 11 | 0–2 → 0–1 | first folder R02, For Fun win | For Fun 7–5, 12 rounds | 92–92 / 92–92 | 4/10 |

Each pair has the same map and ten original player profile IDs across its first physical rounds, but different replay IDs. Team score states are consecutive inside each segment. The second segment starts exactly at the score **before** the excluded final round of the first segment. This is a unique score-state join; no time-gap threshold or K/D combinatorial search is used. M80–Shopify's abandoned R08 has only nine player identities, a separate sign that the round did not complete normally. The generic layer allows this incomplete roster only for an excluded physical round; every counting round must retain the confirmed roster. Physical R## numbering restarts in the second folder. Logical rounds are renumbered 1–12, and the source mapping retains each physical filename, hash, replay ID, original round number, and exclusion reason.

Two other cached split candidates remain blocked by the existing `siege-dissect` `PlayerStats()` scoreboard panic in both folders: M80–Cloud9 7998 / 3905 (10+3 physical vs public 12) and DarkZero–Wildcard 7999 / 3906 (2+9 vs public 12). No logical map or row is admitted from these until the parser can supply trustworthy normalized rounds. The read-only audits preserve their parser errors.

**Current status:** these four reconstructed logical maps are under ignored research diagnostics and have not yet entered `research/sources.json` or the 51-map/374-clean-row dataset. Per-player alias mappings and pipeline cache integration are the next admission gates. The four maps can add up to 26 strictly K/D-matched rows from the preliminary identity audit without relaxing any existing quality requirement. Their current raw public objective counts have not been used to select rating definitions.
