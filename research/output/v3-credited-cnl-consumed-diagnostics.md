# Consumed CNL feature diagnostics

The final FAIL remains at its original SHA; this is a post-final diagnostic and never a replacement final score. All300frozen rows are included.

The raw percentage comparison below used a .51-point tolerance. The subsequent native-order audit establishes that SiegeGG truncates percentages: survival actually agrees300/300 and KOST216/300. Thus the raw survival/percentage disagreement labels below are not all semantic errors. Exact integer opening/clutch comparisons are unaffected. See `v3-credited-cnl-order-diagnostics.md`.

{
  "kost_agreements": 138,
  "survival_agreements": 244,
  "clutches_agreements": 298,
  "opening_kills_agreements": 253,
  "opening_deaths_agreements": 263,
  "clutch_size_agreements": 291,
  "positive_clutch_rows": 47,
  "kost_disagreements": 162,
  "opening_kills_disagreements": 47,
  "survival_disagreements": 56,
  "opening_deaths_disagreements": 37,
  "clutch_size_disagreements": 9,
  "clutches_disagreements": 2
}

| Player / map game | Residual | Replay first-sole clutch | Independent public clutch log |
| --- | ---: | --- | --- |
| Direction/7212 | -0.35227 | [{'round': 10, 'size': 5}] | [{'round': 10, 'size': 5}] |
| Cpk/7341 | -0.18710 | [{'round': 11, 'size': 4}] | [{'round': 11, 'size': 4}] |
| POPO/6825 | +0.14718 | [] | [] |
| Chichoo/6901 | -0.14404 | [] | [] |
| Reif/7356 | -0.14386 | [] | [] |
| J1ahao/7356 | +0.13295 | [] | [] |
| bottomLove/7212 | -0.13094 | [] | [] |
| MomoWiNGs/6834 | -0.12933 | [] | [] |
| rockstarKa/6829 | -0.12174 | [] | [] |
| Yoviker/6975 | -0.11530 | [] | [{'round': 3, 'size': 3}] |
| Yoviker/6926 | -0.11063 | [] | [] |
| nRea117/7341 | -0.11038 | [] | [] |

Direction 9-5,KOST60%,survival50%,openings0-0 and one clutch all independently match. His largest residual accompanies a publicly corroborated1v5; Cpk has a corroborated1v4. This motivates a structural size-feature audit, not removing outliers, changing targets, or fitting individual size coefficients. The old small-cohort linear size experiment remains rejected at its original result; a new larger-cohort study would need a separate prospective plan and entirely new final event.
