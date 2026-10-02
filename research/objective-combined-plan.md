# Conservative combined actor diagnostic freeze

This is a research diagnostic. It does not modify the deployed parser,
historical data, public data, KOST or `siege_style_v2`. The prior original and
extension sets are consumed. The five-map reserve is sealed until this plan,
code, consumed outcomes and tests are committed locally with a clean tree.

## Exact shared prerequisites

- Ten distinct header usernames and ten distinct nonzero numeric player IDs;
  exactly five eligible players on Attack for a plant or Defense for a disable.
- Complete one-to-one eligible scoreboard identity, using the existing typed
  UID/component declaration join. No nearest-ID or mutable slot assignment.
- Each eligible player has a unique direct UID-owner-to-health declaration:
  slot `4154dcc4`, class `0c98c63f`. A reused UID owner or shared health component
  is rejected. Body property `e788f6a5` must be a complete width-four field.
- No `PlayerLeave` anywhere in the round: its timing is unknown. Any Kill/Death
  with a nonpositive packet offset causes whole-event abstention.
- A validated objective occurrence and a unique completion state anchor.
  The last completed timer run after the preceding state must start between
  6.5 and 7.1, end at or below 0.1, contain at least two packets, and finish before
  completion. This reuses the existing diagnostic timer grouping: a timer
  increase greater than 0.5 or a byte gap greater than 100,000 starts a new run.
  These grouping limits are provisional and are not a decoded interaction ID.
- Candidate body state is known at timer start and throughout the timer-to-
  completion interval, using the last preceding sample plus every intervening
  sample. Only values 0 and 2 support eligibility. Independent HUD samples show
  active players in both states. Missing/unknown/state3/state4 abstain for the
  candidate; state3 is not hard-coded as DBNO or teammate death.

## Mode A: standalone plant score and body evidence

Use the exact existing `objective_clock_candidate.candidate`:

1. Collapse repeated identical clock values into distinct epochs.
2. Find the first eligible positive score change after completion. Its epoch
   must contain completion or be the immediately following epoch, and must
   have a subsequent clock epoch to establish its end.
3. From completion onward through that score epoch's end, exactly one eligible
   positive score increment exists, and its delta is exactly 100.
4. From the beginning of the completion epoch through that same end, any
   Kill/Death or positive kill/assist counter vetoes this score mode. No fixed
   kill/assist point subtraction is allowed.
5. The selected player's declared body state is active throughout interaction,
   and no existing death occurs before completion.

Clock epochs are not causal network frames. Gadget scoring and delayed prior
credit remain possible competing causes; development agreement is not proof
that every +100 means an objective. Disables never use this mode.

## Mode B: sole proven survivor throughout interaction

At timer start exactly one eligible player has no prior confirmed Kill/Death.
That player stays uneliminated and has body state0/2 throughout interaction.
Every other eligible teammate has BOTH a confirmed Kill/Death before timer
start AND body state4 throughout interaction. Unknown/DBNO/body-only evidence
never excludes another teammate. A revive/body conflict causes abstention.

For disables, inspect the completion epoch plus the following distinct epoch
through the next epoch or EOF. Sum eligible positive score deltas; observe a
common positive delta shared by at least three defenders and a unique +100
excess. If that observed excess conflicts with Mode B, abstain. Relative score
alone never selects an actor. Ambiguous or absent excess supplies no new actor.

## Mode agreement and conflicts

If both modes propose different players, abstain before choosing any fallback.
If they agree, report `score_and_sole_agree`. Otherwise retain the individually
guarded mode. A remote/gadget kill can veto Mode A while Mode B still proves
the actor independently; it never makes the sole planter dead. Later actor or
teammate kills outside Mode A's clock interval do not veto its earlier evidence.

## Consumed results and mandatory controls

| Cohort | Plants correct/wrong/unresolved | Disables correct/wrong/unresolved |
| --- | --- | --- |
| Original | 39 / 0 / 22 | 1 / 0 / 7 |
| Consumed extension | 25 / 0 / 7 | 3 / 0 / 9 |

Original plant modes:37 standalone,1 sole,1 agreement. Extension:21 standalone,
2 sole,2 agreement. All four resolved disables use sole mode. Exact reports:
`output/objective-combined-candidate-{development,extension}.md`.

4139/R07 remains unresolved, never Aiden. 3563/game6675/R02 disable remains
unresolved, never an unsupported njr credit. 4139/R04 and4150/R07 correctly
retain Hotancold.100T's earlier plant despite later actor/teammate kills.

## One-shot reserve protocol

`objective-combined-freeze.json` hashes all executable evidence dependencies,
candidate code and validation adapter. Source hashes normalize CRLF to LF;
binary/replay hashes use exact bytes. Run `objective_combined_reserve.py` only
after local freeze commit and clean status. It refuses changed frozen inputs.
Record all sixty logical round predictions, preserving rehost physical files,
before opening any actor label. The ignored run ledger marks label opening
durably. Interrupted runs resume identical cached evidence, never retuned logic.
Completed results are immutable: reruns only display the prior result.

Report all eight plants and two disables, correct/wrong/unresolved, per-mode
counts and occurrence mismatches. Permanently record wrong actors before any
analysis. This small reserve alone cannot establish broad production accuracy.
It becomes consumed immediately upon label opening, whether validation passes
or fails. Obtain further distinct unused events before a broad deployment claim.

No historical SQLite/public/archive update, push or Rating refit is authorized
by this research freeze. Any UAH assessment must remain read-only.
