# Observed score-counter grammar by replay build

Consumed 12-map actor-validation rounds only. Each entry is a single positive score packet within 5,000 decompressed bytes **after** one isolated kill or assist counter increment on the same score component, at least 20,000 bytes from every objective state transition. This is packet adjacency, not proof that the counter caused the entire score delta. Delayed or combined updates are excluded rather than assigned a fixed value.

| Code version | Counter | Score delta counts | Example round(s) |
| ---: | --- | --- | --- |
| 9636829 | assists | +75: 12 | 3579/6706 R01, 3579/6706 R02 |
| 9636829 | kills | +100: 13, +120: 11, +130: 4, +110: 2, +200: 2, +105: 1 | 3579/6706 R01, 3579/6706 R01 |
| 9658832 | assists | +75: 5 | 3563/6673 R01, 3563/6673 R01 |
| 9658832 | kills | +120: 12, +100: 10, +200: 1, +220: 1, +105: 1, +125: 1, +140: 1, +130: 1, +2450: 1 | 3563/6673 R01, 3563/6673 R01 |
| 9769907 | assists | +75: 13, +175: 4 | 4283/8685 R01, 4283/8685 R01 |
| 9769907 | kills | +120: 17, +100: 10, +130: 6, +110: 6, +200: 3, +220: 1, +140: 1 | 4283/8685 R01, 4283/8685 R01 |
| 9820472 | assists | +75: 14, +175: 1, +245: 1 | 6157/10428 R03, 6157/10428 R09 |
| 9820472 | kills | +100: 14, +120: 9, +130: 7, +110: 5, +200: 2, +140: 1, +220: 1, +280: 1, +125: 1, +138: 1 | 6157/10428 R03, 6157/10428 R03 |
| 9879602 | assists | +75: 15, +2425: 1 | 6158/10563 R06, 6158/10563 R06 |
| 9879602 | kills | +100: 23, +120: 12, +130: 3, +110: 2, +140: 1, +220: 1, +105: 1, +2470: 1 | 6158/10563 R04, 6158/10563 R04 |

The same counter type can be followed by different score deltas within a build. A universal kill=100 or assist=75 subtraction is unsupported. Pairing must also account for score packets that precede or batch with later game-state packets.
