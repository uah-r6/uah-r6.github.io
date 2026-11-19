# Blue vs MIZ Black Rating evidence repair — 2026-11-18

Series `322593609acf` has three imported maps. Border (`e3b1cc9cd5fd`, 8–6)
and Fortress (`1117c1e1fbcb`, 7–4) were already Rating-eligible. Chalet
(`969aff1ee48a`, 2–7, nine rounds) was excluded for incomplete credited-kill
evidence in R01 and continuity through R02. This was an evidence-reader issue,
not a Rating formula failure.

## Direct replay proof

In Chalet R01, opponent `rec-_-` changed UID within the round while keeping
the same profile and scoreboard owner. The native replay has two distinct
score components with a **direct zero kill-counter sample on each**. The first
sample precedes the action start, and the second follows it. The reader's
ordinary UID route missed both. R02 has the same player profile, the new UID,
and a direct zero baseline before action. All other nine players have direct
continuous counters. The parser now exposes the two physical samples and
their offsets as a proof object without declaring the round complete. A
separate, strict cross-round check uses that proof to complete only the sealed
Rating input. The historical display sidecar stays intact and incomplete.

R02's plant was separately excluded because a standalone `Death` callback had
legacy offset zero. The native feedback observer proves its exact boundary.
The parser uses that offset solely while determining objective ownership and
restores the original feedback offset afterward. The owner is `rec-_-` on the
opposing team. No Blue player objective count changes.

## Applied local result

The repair was first applied to a private SQLite clone and then to the live
local SQLite database. Chalet is Rating-eligible; all three MIZ maps and all
five Blue player Series Ratings are numeric. The 87 generated JSON documents
validate. Compared with the pre-repair SQLite backup, only the Chalet
`maps.normalized_json` row, one opponent `objective_events` plant row, one
`map_v3_kill_evidence` row, and three audit rows differ. The other 30 maps,
all displayed kill/death/round/player statistics, all original credited
sidecars, snapshots, and roster identities are unchanged. The Chalet archive
still verifies Healthy. The v3 formula is unchanged.

Private backup, clone, diagnostic output, and table comparison script are under
ignored `data/research/miz-blue-rating-20261118/`. No raw replay or private
database belongs in Git.

## Verification

The real R01/R02 Go replay smoke test and strict synthetic refusal tests pass.
Go `test ./...` and `vet ./...` pass. Both web builds pass. Frontend tests pass
75/75 after making the series coverage fixture independent of the newest map
count. The full Python suite and publication status are recorded in the
checkpoint after completion.
