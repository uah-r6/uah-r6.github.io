# Kill-credit review addendum — 2026-10-03

The [original migration review](credited-kill-migration-review.md) and its `eeca495` source/result seal remain unchanged. This addendum records separate consumed development evidence. Historical migration remains pending user review; SQLite, archived replays, generated public data and original v2 inputs are unchanged.

## Opening attribution and order

Both timer-order discrepancies now have independent official broadcast evidence:

- [Clubhouse 8583 round 3](credited-kill-opening-hud.md): Gabu eliminates pino before planting. Neskin eliminates Flastryy after planting resets the countdown. Raw feedback records `0:32` then `0:43`; sorting the whole round by remaining seconds reverses those deaths.
- [Bank 8594 round 7](credited-kill-opening-bank-hud.md): vitaking eliminates Bassetto before planting, and Handyy eliminates Neskin after the reset. Raw feedback records `0:06` then `0:42`. The broadcast also shows planting overtime while the action clock remains zero.
- [Clubhouse 8583 round 2](credited-kill-opening-owner.md): resetz is visibly downed before the first final death. The feed names pino as the finisher, but Neskin's visible kill counter rises from zero to one while pino gains an assist. This independently corroborates the credited owner for this particular opening.

Two packet-order corrections plus the independently filmed owner case explain all 200 consumed SAL player-map opening aggregates. This is a descriptive development comparison, not a universal opening rule or a new final accuracy result. The original 193/200 timer-order and 198/200 packet-order comparisons remain sealed. No per-victim owner is assigned from nearby counter updates or expected totals. The frames do not identify the damaging shot or distinguish a general DBNO-time versus final-death-time policy when multiple players are downed before any death.

## Native Death envelope

[APAC8156 structural follow-up](credited-kill-native-envelope.md) establishes why the original counter validator refused round 3: the parser's empty-killer branch emits a `Death` without setting `killOffset`.

A separate, opt-in Go reader wraps the existing feedback callback once and records its exact marker, start/end and single emitted event index. Jin's native envelope is `41873708..41873781`; the original event keeps offset zero. The unchanged counter validator can now verify this single-segment map using the direct envelope boundary. Unknown, ambiguous, duplicated, bad-marker, late-baseline and unsupported-structure cases still refuse.

Ten native rounds give ten official/public credited-kill agreements and ten official victim-death agreements, with no mismatch. All ten round headers/operator snapshots and raw feedback match the original reader; five archived UAH first-round controls also preserve header/operator/feedback/counter output. A sanitized 9.7 KiB real structured fixture and six Go test functions protect this path.

This is a separate development reader and evidence source. The current Python validator deliberately does not accept its source version. The default reader, original source/binary and original 31-complete-map audit remain unchanged. Promotion needs explicit adapter/version integration and broader native-envelope controls; these ten supplemental agreements do not revise either failed v3 final.

## Trade evidence and migration boundary

The [independent trade aggregate audit](credited-kill-trade-aggregate-audit.md) reads original frozen features and already-consumed primary targets using independently verified name/team bindings:

| Comparison | Agreements / player-maps |
| --- | ---: |
| Original refrags versus official `tradeKills` | 139 / 200 |
| Original traded deaths versus official `deathsByTradedKill` | 121 / 200 |
| Both aggregates | 83 / 200 |

Similarly named aggregate fields do not establish event-level equivalence. These results cannot identify whether a discrepancy comes from ownership, window definition, phase timing, packet precision or another target policy. No alternate trade windows were searched. Keep opening, trade, traded-death KOST, pivot, untraded, headshot and original v2 event inputs unchanged.

The supported count proposal remains the original read-only UAH audit: 58 validated rounds out of 62; Lgon −2, OhWowJay +1, DinoFireKing +1, AzoozNewzz and Tallman3.14 zero kill deltas. Four Chalet rounds still lack a complete ten-player roster. There is no complete credited season total. Core objective proposals, unresolved historical-credit policy, immutable v2 input snapshots, review-before-write and rollback steps remain as documented in the original review.

## Next action

1. Verify both credited-count checkpoint seals before further development.
2. Audit plant-boundary clock epochs and planting overtime on consumed events; retain raw packet order and mark elapsed-time ambiguity explicitly. Do not subtract remaining values across a reset or treat byte distance as elapsed time.
3. Investigate explicit identity-linked damage/DBNO/death records for generic credited-victim association. Do not infer one from nearest counters, totals or camera subject. A focused control where competing DBNOs precede deaths is needed to distinguish opening policies.
4. Keep native-envelope source promotion separate from counter-count migration. Broader callback parity/ambiguity controls must precede any default wiring.
5. Historical/public migration awaits user review of this package, the incomplete Chalet policy and original-v2 snapshot/version plan. No corrected export, actor application, Rating refit or Phase2 push is authorized by this audit alone.
