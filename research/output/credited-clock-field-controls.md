# Explicit clock-field controls — 2026-10-03

Base `1c4568b`. New separate Go `cmd/clock-field-inspect` uses the existing six consumed buffers across four builds. No default reader/action-start/operator path, historical statistics, targets or Rating experiments are changed.

## External hypothesis and observed contradiction

A [primary implementation's binary-format notes](https://github.com/wnc-replay/replay-tool/blob/dd535f6499069c8268841fda76c68a04b19ba104/docs/BINARY_FORMAT.md) describe property0x6C463718 as a round timestamp in milliseconds and0xA374F4B6 as a possible sequence counter. That source is a hypothesis, not a replay-format contract. The exact source bytes, commit and hash are cached privately. No external nearest-packet, DBNO-window or hit-zone interpretation is adopted.

In these controls,0x6C463718 is a width4 unsigned property on exactly one entity per replay. It **decreases** through prep/action countdowns, increases at action/plant resets, and becomes zero at some boundaries. The elapsed-since-round-start interpretation is contradicted. The other property occurs on many entities with frequent decreases; it does not supply a monotonic replay clock here.

| Source | Build |0x6C463718 samples | Coarse countdown observations | Exact floor(raw/1000) correspondence |
| --- | ---: | ---: | ---: | ---: |
| SAL8580 Lair R06 |9879602 |6,274 |228 |228 |
| SAL8583 Clubhouse R02 |9879602 |6,378 |226 |226 |
| SAL8583 Clubhouse R03 |9879602 |6,830 |243 |243 |
| SAL8594 Bank R07 |9883691 |7,442 |268 |268 |
| UAH Fortress R04 |9901603 |5,723 |207 |207 |
| UAH Michigan Border R03 |9918362 |5,343 |193 |193 |
| **Total** |4 builds |**37,990** |**1,365** |**1,365** |

Correspondence uses the first framed clock property at/after each exact integer countdown listener marker, not a credited-kill counter join. This is descriptive consumed development evidence; it is not 1,365 independent unseen validation cases. Same-prefix structural linkage is the next control. Raw sample steps commonly differ by33–38 units, with larger gaps; recording-rate constants are not assumed.

## Metadata and boundaries

All raw plain header key/value fields through teamscore1 were retained in physical order, including repeated player fields. Their build matches the cached parsed header. There is a starttime wallclock-like value and a datetime string, but no named FPS, recording-frame-rate or tick-rate field. A single starttime value is not an ongoing event clock.

Known countdown-reset controls remain explicit:

- LairR06: raw29199→44965 at74411806.
- ClubhouseR03: raw29019→44952 at86249427.
- BankR07: raw0→44952 at91932178; the zero-clock planting-overtime interval is not resolved by a decreasing remaining-clock field.

These transitions preserve serialization order; remaining-time sorting remains invalid. Last-feed brackets also expose limitations:

- LairR06's last elimination has previous raw0 and no later property sample.
- MichiganBorderR03's last elimination brackets raw34676 against terminal0. Treating that drop as elapsed time would be invalid.

No interpolation, history-scalar division, byte-distance timing, precise shot timestamp, trade window or cross-phase elapsed clock is inferred. Repeated late history copies retain their original opaque scalar/list order and are not timed at their physical copy offsets.

## Verification and next action

487 Python tests passed, one optional real-replay smoke skipped, six subtests passed. Full Go/Y11 tests and go vet passed, including four new clock/header tests. Prior web builds apply because web/shared statistics/export code are unchanged. The protected objective correction, database, archives, public JSON and immutable v2 inputs remain unchanged.

Next: exact same-prefix relationship between integer countdown and candidate finer field, explicit serialized epochs and zero/terminal/overtime controls, then broaden only if those controls are sound. Credited-victim association and generic cause/recovery roles remain unresolved. The count-only UAH migration preview is unchanged; no historical kill migration, Rating fit or publishing is authorized by these clock findings.
