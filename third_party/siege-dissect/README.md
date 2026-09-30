# Local siege-dissect source

This source is based on `lumina-r6/siege-dissect` revision
`ea662d31f4dc2a66576088c49ab8d3174b0b3989` (MIT license in `LICENSE`).
Only Go source and module files are included; upstream replay fixtures and private
`.rec` files are excluded.

The verified Y11 operator selection uses the replay's timer reset as the action-phase
boundary. At that point it resolves attacker operator names from the replay
header's post-repick `RoleName` snapshot, provided that operator also appears
in a packet before action start. The initial `readPlayer` operator is
retained for local diagnostics as `initialOperator`. If the header has no known
operator name, the final operator is `Unknown` with source `unresolved`.
Y11 headers can end with `teamscore1` immediately after the final player's
role fields. The local `readHeader` flushes that final player so their
post-repick role is retained. The parser JSON keeps both operator name and ID.
Defense uses the upstream behavior. The Y9S3+ `Skip(402)` logic remains for
older replays. Verified professional Y11S1, Y11S2 and early Y11S3 builds also
use the action-start path. The exact build IDs are in `dissect/version.go`;
unknown earlier Y11 builds stay unresolved until a real replay verifies them.
The original UAH Y11S3 boundary logic is unchanged. The local operator table
maps replay ID `444310693746` to Solid Snake, as confirmed by its final header
role and [Ubisoft's operator listing](https://www.ubisoft.com/en-us/game/rainbow-six/siege/game-info/operators/solid-snake).

`scripts/install-parser.ps1` builds this local source into the ignored
`.local-tools/bin/siege-dissect.exe` and checks source hashes on every launch,
so edits to this source cannot leave a stale binary in normal use.
