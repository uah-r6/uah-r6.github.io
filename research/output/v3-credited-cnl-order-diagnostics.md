# Consumed CNL native-order audit

{
  "rounds": 320,
  "verified_positive_offsets": 2252,
  "zero_offsets": 0,
  "clutch_log_agreements": 298,
  "opening_kills_agreements": 275,
  "opening_deaths_agreements": 297,
  "kost_truncation_agreements": 216,
  "survival_truncation_agreements": 300,
  "legacy_reordered_rounds": 53
}

All 300 frozen rows remain in the audit. The CNL FAIL is unchanged. No production data, Rating, or feature policy changed. Native callbacks are serialized by increasing marker offset in Go Reader.Read; exact normalized finisher/victim/time/headshot parity is checked per round.

| Player / game | Legacy clutch | Native-order clutch | Public log |
| --- | --- | --- | --- |
| Lyda/6942 | [{'round': 7, 'size': 1}] | [{'round': 7, 'size': 3}] | [{'round': 7, 'size': 3}] |
| Yoviker/6975 | [] | [] | [{'round': 3, 'size': 3}] |
| Douhua/6976 | [{'round': 7, 'size': 1}] | [{'round': 7, 'size': 2}] | [{'round': 7, 'size': 2}] |
| Songla/6976 | [{'round': 6, 'size': 1}] | [{'round': 6, 'size': 1}] | [] |
| rockstarKa/6932 | [{'round': 12, 'size': 1}] | [{'round': 12, 'size': 2}] | [{'round': 12, 'size': 2}] |
| Direction/7211 | [{'round': 1, 'size': 2}] | [{'round': 1, 'size': 1}] | [{'round': 1, 'size': 1}] |
| YaaaaZ/7213 | [{'round': 5, 'size': 1}, {'round': 7, 'size': 1}] | [{'round': 5, 'size': 2}, {'round': 7, 'size': 2}] | [{'round': 5, 'size': 2}, {'round': 7, 'size': 2}] |
| Asylum/7358 | [{'round': 8, 'size': 2}] | [{'round': 8, 'size': 1}] | [{'round': 8, 'size': 1}] |
| Asylum/7359 | [{'round': 1, 'size': 2}] | [{'round': 1, 'size': 1}] | [{'round': 1, 'size': 1}] |

Exact header/event identity parity; native callback ordinal; all positive offsets strictly increasing. Zero legacy offsets explicitly retained, not invented.

Native finisher order is not DBNO or credited-owner chronology. Trade windows and credited opening owners remain unsupported.

Survival matches all 300 public values after percentage truncation. KOST uses actual integer round counts rather than a .51 percentage tolerance; remaining differences are semantic, not rounding. Public clutch sizes may also count downed players differently; contradictions cannot justify an inferred DBNO state.
