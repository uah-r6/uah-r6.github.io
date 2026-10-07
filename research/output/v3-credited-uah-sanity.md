# Frozen v3 read-only UAH sanity

UAH is not training/validation truth. All-map scores below are diagnostics only; whole-map credited/objective coverage must be resolved explicitly before deployment. No coefficients, live version, database or generated data changed.

Stored occurrence inventories can be incomplete for historical imports. An empty unresolved-objective list below does **not** prove complete supported objective coverage. The prior independent audit retains an unverified Tallman Kafe R09 plant and the unsupported nine-player Chalet R10 plant. These historical displayed counts stay intact, but must not silently become trusted v3 objective inputs. A deployment needs explicit supported-input eligibility, separately from the preserved displayed statistics and historical v2 snapshots.

| Player | Rounds | Diagnostic all-map v3 | Round/aggregate delta |
| --- | ---: | ---: | ---: |
| Lgon | 82 | 1.28239808 | 0 |
| OhWowJay | 82 | 1.38882070 | 0 |
| AzoozNewzz | 82 | 0.97450803 | 0 |
| Tallman3.14 | 82 | 0.75563708 | 0 |
| DinoFireKing | 82 | 0.84474043 | 0 |

## Map feature coverage

[
  {
    "map_id": "d64d5478cdb3",
    "map": "Fortress",
    "rounds": 10,
    "credit_complete": true,
    "unresolved_objectives": []
  },
  {
    "map_id": "8a6357ff307c",
    "map": "Border",
    "rounds": 14,
    "credit_complete": true,
    "unresolved_objectives": []
  },
  {
    "map_id": "5adc26f7a402",
    "map": "Kafe Dostoyevsky",
    "rounds": 14,
    "credit_complete": true,
    "unresolved_objectives": []
  },
  {
    "map_id": "076d2b6b02bc",
    "map": "Border",
    "rounds": 12,
    "credit_complete": true,
    "unresolved_objectives": []
  },
  {
    "map_id": "b595ffaaec57",
    "map": "Chalet",
    "rounds": 12,
    "credit_complete": false,
    "unresolved_objectives": []
  },
  {
    "map_id": "8af0a6db6c39",
    "map": "Border",
    "rounds": 11,
    "credit_complete": true,
    "unresolved_objectives": []
  },
  {
    "map_id": "9db26f1b6ca7",
    "map": "Nighthaven Labs",
    "rounds": 9,
    "credit_complete": true,
    "unresolved_objectives": []
  }
]

Individual map scores are preserved privately; no NaN or missing tracked player. Exact feature aggregation matches the research predictor within1e-12.
