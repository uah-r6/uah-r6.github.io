# UAH packet-order sensitivity — read only

{'supported_rounds': 58, 'full_order_changed_rounds': 10, 'unavailable_rounds': 4}

Exact normalized sequence is checked against archived physical feedback using complete profile bindings. Isolated copies of the existing pure calculator change only event ordering; both Rating formulas are suppressed. The live module and stored events remain unchanged. This measures sensitivity, not proposed correct trade statistics.

| Player | Known-round event-feature deltas under packet ordering only |
| --- | --- |
| Lgon | {'pivot_kills': -2} |
| OhWowJay | {'pivot_kills': -1, 'pivot_deaths': 1, 'opening_kills': 1, 'opening_deaths': -1} |
| AzoozNewzz | {'pivot_deaths': 1} |
| Tallman3.14 | {'pivot_deaths': -1} |
| DinoFireKing | {'pivot_deaths': 1} |

| Map / round / player | Original / packet-order-only |
| --- | --- |
| Border/8a6357ff307c/R06/Lgon | {'pivot_kills': 2} / {'pivot_kills': 1} |
| Border/8a6357ff307c/R06/OhWowJay | {'pivot_kills': 2} / {'pivot_kills': 3} |
| Border/8a6357ff307c/R06/AzoozNewzz | {'pivot_deaths': 0} / {'pivot_deaths': 1} |
| Border/8a6357ff307c/R11/OhWowJay | {'pivot_kills': 2} / {'pivot_kills': 1} |
| Border/8a6357ff307c/R11/Tallman3.14 | {'pivot_deaths': 1} / {'pivot_deaths': 0} |
| Border/8a6357ff307c/R11/DinoFireKing | {'pivot_deaths': 0} / {'pivot_deaths': 1} |
| Border/8a6357ff307c/R12/OhWowJay | {'pivot_deaths': 0} / {'pivot_deaths': 1} |
| Kafe Dostoyevsky/5adc26f7a402/R02/Lgon | {'pivot_kills': 1} / {'pivot_kills': 0} |
| Kafe Dostoyevsky/5adc26f7a402/R02/OhWowJay | {'opening_kills': 0, 'opening_deaths': 1} / {'opening_kills': 1, 'opening_deaths': 0} |
| Border/076d2b6b02bc/R06/OhWowJay | {'pivot_kills': 1} / {'pivot_kills': 0} |

Packet order sensitivity only; retains legacy remaining-seconds8s trade predicate and raw finisher owner. Not a validated trade clock/credited event projection. Four incomplete Chalet rounds are excluded explicitly; deltas are not complete corrected season totals. No Rating computation, module monkeypatch, normalized event mutation, SQL write or public regeneration.

Kills, deaths, headshots, objectives, teamkills, survival, rounds/wins, side splits and operators are unchanged in all assessed tracked rounds. Event-derived differences must be separately reviewed/versioned; this report does not authorize changing original v2 inputs or live chronology.
