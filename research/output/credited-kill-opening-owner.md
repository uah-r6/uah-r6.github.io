# Independent opening-credit case: Neskin versus pino

[Official SAL Stage2 Day1 broadcast](https://www.youtube.com/watch?v=Ao6SRRhCmbg&t=14872s). This separate consumed review preserves the earlier sealed opening-order result.

| Video second | Independently inspected HUD |
| ---: | --- |
| 14872 | R02, score0-1, clock0:35,5v5; Neskin0/1/1, pino0/1/1; resetz alive0/1/0. |
| 14874 | R02, clock0:33,5v5; resetz taking damage; no elimination feed; Neskin0/1/1, pino0/1/1. |
| 14875 | R02, clock0:32,5v5; resetz POV and observer card both show downed cross; Neskin0/1/1, pino0/1/1. |
| 14876 | R02, clock0:31,5v4; only feed pino.L5 -> resetz.LOUD; Neskin1/1/1, pino0/1/2; resetz dead0/2/0. |
| 14880 | R02, clock0:27,5v4; same sole feed and counters; first final death resetz; no second elimination yet. |

The first final death is resetz. The feed identifies pino as the finisher, while the visible scoreboard increments Neskin kills0→1 and pino assists1→2 without a pino kill. This independently supports assigning this particular opening credit to Neskin; it was not inferred from the nearest replay counter or the expected map total.

Direct temporal UID/body evidence agrees: resetz raw3 at86443440, eliminated raw4 at86448101; Neskin kills0→1 at86448083, pino finish86448473, pino assist1→2 at86448897. Byte order is serialization, not server causality or subsecond timing. The damaging shot/downer identity was not independently observed. No generic victim/downer packet was recovered.

Separate descriptive comparison: {'player_maps': 200, 'case_supported_official_matches': 200, 'case_supported_public_matches': 200}. Two packet-order corrections plus this independently filmed owner case explain all consumed SAL map opening-count discrepancies. This is development corroboration, not a new final accuracy score or validated universal rule. The original193/200 timer-order and198/200 packet-order results remain unchanged.

Production opening/trade/pivot/untraded/headshot semantics remain unchanged. Exact official opening policy when competing DBNOs precede deaths is still unverified. No historical SQLite write, public regeneration, Rating-input update or application of this one-off reviewed case.
