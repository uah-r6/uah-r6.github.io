# Deep production Rating evidence recovery

Baseline: `e179add`, nine Healthy archives, six eligible maps. The ignored
`data/research/deep-rating-recovery-20261008/` baseline contains a SQLite backup,
all 22 tables (including evidence sidecars and audit), 49 public documents,
archive/manifest/binary/source hashes and exact six-map v3 features/Ratings.
Raw diagnostics are private and read-only. No model fitting is involved.

## Required facts and guards

The archive fingerprint, manifest digest, executable/cache digest, sidecar seal,
compare-and-swap, logical/physical source identity and historical v2 snapshot
are **provenance/integrity guards**. They bind facts to this match and prevent
stale or conflicting observations; they cannot be made optional.

`rating_inputs_v3.prepare()` requires these **feature facts**:

- Actual participants, stable profile identity and teams/sides for every round.
  A missing participant cannot be assigned zero kills or presumed absent.
- Each participant's official credited kills, not feedback finishers; the
  multikill and kill component of KOST use those per-round counts.
- Every elimination's victim, finisher, teamkill status and time, in physical
  order. Survival, trades and native opening/clutch features depend on these.
  Positive unique increasing native offsets and exact normalized feedback parity
  are ordering/identity guards proving these facts. Finisher identities remain
  appropriate only for the frozen native opening and trade semantics; they are
  not credited-count substitutions.
- The first sole-survivor state and actual winner for clutch credit. Starting
  with an invented tenth player changes this feature and is unacceptable.
- Every completed plant/disable and its unique actor, side and team, including
  whether the event occurred at all. Objectives and objective KOST require this.
- Nonzero actual round denominators; the frozen eight-second trade window.

`credited_refresh.round_counts()` guards exact normalized/profile participation
and team bijection. `kill_credit.validate_map_credit()` guards direct integer
baseline/terminal deltas, unchanged counter identity, physical continuity and
explicit rehost resets. The native reader guards baseline before action/first
elimination, monotonic counter samples and component ownership. No total from
the kill feed can replace these observations. An assumed ten-player roster is
a guard for completeness, not itself a model feature: any alternative must
prove the entire actual participant inventory independently.

`objective_refresh` guards exact replay, rounds, winners, profiles, teams and
unchanged unrelated counts. The native objective reader guards single planted
state, independently winning side, unique typed UID/slot/class ownership,
monotonic full completing timer, cancellation/competition/orphan rejection,
known death offsets, actor alive and opponents still alive, and stable body
ownership/state. The body guard protects actor eligibility; positive HP alone
cannot substitute for it. Alternative proofs must establish the completing
actor without promoting unknown body states generally.

## Proven archive findings

- Kafe R9: the sole completing timer belongs to Kenbot.USU, UID
  `7731509929217799239`, profile `75658e22-b077-4663-8a46-0e0de586ddf3`.
  Timer interval `34172749–34203671`, `6.974 → 0.002`, explicit state-2
  termination; global plant state `34204105`. Same typed body owner throughout;
  body `0 → 1 → 0`, final state-0 write `34202030`, before completion. Existing
  resolver rejected the intermediate state 1. The new
  `terminal_active_numeric_bonus_timer_owner_v1` proof independently checks
  the same body at every complete atomic write: baseline 110, ceiling 130,
  positive HP 117 down to 111, and float fraction `(HP - baseline) / baseline`
  within `1e-6`. Body state must return to an existing known active state before
  completion. State 1 at completion, downed/dead/unknown states, conflicting
  ownership, cancellation and competing timers remain rejected. This is a
  separate bounded proof, not the earlier unapproved general state-1 candidate.
  R9's stored Defense-side Tallman3.14 plant is corrected to Kenbot.USU.
- Placements Border R6: only one completed plant, AzoozNewzz, state anchor
  `74204451`; independently observed score advances Attack `2 → 3`, Defense
  stays `3`. No phase-1 disable interaction. Legacy feedback labels a second
  `0.00` timer as disable and attributes it to already-dead Lxgacy.MAV through
  a default player index. The two zero samples, `74204042` (`0.008`) and
  `74204267` (`0.004`), belong to the same completing plant timer, and both
  precede completion `74204277` and the global plant transition. The new
  `repeated_plant_zero_before_transition_v1` proof requires those positive facts,
  one plant occurrence, no phase-1 interaction/orphan, and independent score
  consistency. It removes the false Lxgacy.MAV disable without inventing an
  actor. Missing parser output alone cannot authorize deletion.
- Chalet R9–12, segment 2 R01–R04: nine active names/profiles/UIDs and nine
  directly owned scoreboard components. The tenth initial player packet is an
  explicit empty slot, with blank name/profile, zero operator/entity and UID
  `18446744073709551615`. Natedog.UMich is absent, not dropped by the parser.
  Rehost UIDs for the nine retained profiles are stable across segment 2.
  `explicit_ten_slot_empty_participant_v1` binds the full ten-slot packet table,
  exact nine initial/runtime profiles, nonzero stable UIDs, 5/4 team inventory,
  offsets before the unchanged action-start marker and the empty-slot sentinel.
  A nine-player header alone is still rejected. Every actual participant has
  direct initial/terminal counter deltas, using the unchanged
  `stable_uid_scoreboard_delta_v1` semantics. The new R01/all-zero reset requires
  the retained profiles to be an exact known subset and the independently proven
  empty slot; reconnect ambiguity and unknown within-round gaps still fail.
  No tenth participant or count is synthesized; no conservation inference is
  needed. R9 illustrates why finishers cannot substitute for credit:
  Tallman's two finishes yield one credit, and Jay's one finish yields two.
  A new sealed private `map_v3_kill_evidence` record supplies only Rating inputs;
  the original incomplete `map_kill_credit` record and displayed counts remain
  exact. The same inventory also unlocks the existing completing-timer proof for
  Ophanbear.UMich's previously omitted R10 plant. Maintenance refreshes the whole
  objective inventory when recovering participants, even if old empty objective
  lists passed validation.

## Validation classification

| Check / layer | Required feature fact | Provenance or integrity guard |
| --- | --- | --- |
| `load_inputs` | Complete replay, no unresolved manual K/D, frozen eight-second window | Map existence; objective and credited payload/fingerprint/normalized hashes; stale evidence abstention |
| `prepare` / `native_state` | Full actual roster, team/winner, elimination identities/time/headshots, first opening, sole survivor and enemy count | Unique profile/name mapping, native/normalized parity, positive unique physical order, unique ordinals, no duplicate death |
| `validate_objectives` | Every completed objective's actor, kind, side/team; defense-win constraint for disable | Supported occurrence type, unique anchored occurrence, source-specific structural proof, exact stored/observed inventory |
| `round_counts` | Official per-player per-round counts for actual participants | Exact nonnil profiles and participation, complete team bijection, matching logical rounds |
| `validate_map_credit` | Integer terminal minus initial, per-round counts, no unknown participant | Unique physical/logical sources, supported direct source, UID uniqueness, counter bounds/continuity; explicit reset proof |
| Native counter reader | Direct initial/terminal values for each actual player | Typed owner/component binding, baseline before action/first elimination, monotonic samples, ambiguity rejection |
| Native objective reader | Complete interaction and unique living eligible actor | Stable typed UID/body/timer ownership, slot/class, full monotonic timer, terminal state, no canceled/competing/orphan interactions, physical death order |
| Parser adapter / objective overlay | Same participants, winners, objective counts/actors | Exact replay and logical source, safe team mapping, unchanged other normalized fields; no unknown actor-source fallback |
| Sidecar store / repair transaction | Full validated v3 input set | Healthy archive, binary/manifest hashes, cache key, payload seal, compare-and-swap, no complete evidence overwrite, atomic audit/snapshot/repair |

The assumed ten active players is replaced only by a full proof of the actual
nine-plus-empty inventory. Unknown body state is replaced only by a separately
validated bounded proof with an already-supported terminal state. No feature
requirement, occurrence completeness requirement, credited-kill semantics or
formula parameter was removed.

## Maintenance and preservation

The candidate binaries freshly extracted all nine archives. Every per-round
feature row and map Rating for all six original eligible maps matched exactly.
The real guarded maintenance then repaired a baseline SQLite copy, followed by
the actual quoted **Start NECC Admin.cmd** launcher and its authenticated local
`POST /api/admin/rating-evidence/repair-all` endpoint: nine audited, six already
eligible, three repaired, zero blocked. The launcher rebuilt the local binaries,
restarted the outdated process and opened Chrome. Runtime imported the project
`.venv` and repository source, and its two binary hashes exactly matched the
trial candidates. Binary/replay-hash cache keys generated fresh observations.

All nine maps / 103 recorded rounds now pass the complete stored `load_inputs`
path. The trial and production normalized payloads/objective rows/sealed evidence
match exactly. Seven new audit entries preserve before/after payloads,
affected logical rounds, new sources, parser/reader and manifest hashes, and
full final eligibility. Old audit entries are intact.

Exact normalized changes:

- Kafe R9: replace Tallman3.14's invalid Defense plant with Kenbot.USU's plant.
  The old side-invalid plant was already ignored by display calculation, so
  Tallman's displayed plants and KOST do not change; Kenbot's plants go **0 → 1**.
- Placements Border R6: delete the positively disproven Lxgacy.MAV disable.
  His disables go **1 → 0**, KOST rounds **12 → 11**. Azooz's plant stays intact.
- Chalet R10: add the uniquely proven Ophanbear.UMich plant, **0 → 1**.

These opponent changes are stored and audited. All public tracked-player raw
counts, KOST, operators, roles, ownership, scores, metadata and highlights are
exact. All original display sidecars, objective sidecars, frozen v2 snapshots,
round IDs, player identities, rehost mappings and other database tables remain
unchanged. Archive bytes and manifests remain exact; all nine remain Healthy.
No match import or full stored replay reparse occurred.

All 49 public documents validate. Twenty change only in Rating, trusted Rating
coverage/eligibility/exclusion, resulting Rating sorting and export freshness.
The six original map documents and UCF/White Series documents remain exact.
Every series participant's Rating is independently checked against a single
aggregation of their trusted map feature inputs. Normal Season/Career projections
are independently checked against regular appearances. Series coverage is now
Placements **3/3, 38/38**, Michigan **2/2, 24/24**, UCF **2/2, 20/20**; White
retains its existing player-specific complete coverage, including substitutes.
Complete-only semantics and the UI are unchanged. Blue profiles naturally gain
three real trend points; White retains its compact one-series view.

The frozen v3 source, coefficients, scaling, intercept and eight-second trade
window are unchanged. No fitting, downloads, cloud mutation or unrelated feature
work was performed. The focused recovery is complete; no blocked map remains.

## Exact newly produced Ratings

These are the unrounded exported numbers. Series evaluates the frozen model once
on combined trusted counts; it is not an arithmetic mean of map Ratings.

| Player | Kafe | Placements Border | Chalet | Placements Series | Michigan Series |
| --- | ---: | ---: | ---: | ---: | ---: |
| AzoozNewzz | 1.028621076162262 | 0.6704412739619303 | 0.9295319715343993 | 0.9438043518046677 | 1.08376446520794 |
| DinoFireKing | 0.9210136871714595 | 0.850424143089836 | 1.0271856481283834 | 0.8817996643603304 | 0.9348062366024169 |
| Lgon | 1.4529425360403 | 1.131879570337306 | 0.7220483481329694 | 1.3473119302574625 | 1.0781565595142777 |
| OhWowJay | 1.1202199982493741 | 1.2757182324775775 | 1.264488863004982 | 1.2707584999695087 | 1.2534187731416586 |
| Tallman3.14 | 0.8328260265097219 | 0.34864626955589506 | 0.8233780177790317 | 0.6496468821707915 | 0.8790235371369184 |

## Rebuilt tools and final gates

Parser SHA-256: `f3440d93bf3a2b882003eadd879d07b52e82ed52e040e64fc8e8d96a7a3a83f4`.

Credit reader SHA-256: `96ade560862f7fbc5935cdbd3dd76b4fa416bd2629206b85ffca5ccb3dc71d28`.

52 new Python regression cases and reduced Go structural fixtures cover unique
proof acceptance; ambiguous/conflicting ownership; wrong side/winner; stale UID,
marker and seals; missing provenance; canceled/duplicate/late interactions;
explicit empty-slot versus missing-player rejection; reconnect ambiguity;
finisher-versus-credit differences; binary-keyed caches; atomic correction plus
Rating-only evidence; old complete-evidence preservation and idempotent repair.
No inference is implemented because every actual participant has direct counters.

Final local gates: **781 Python tests + six subtests**, one optional replay smoke
skipped; **59 frontend tests**, **19 Worker tests**, Go tests/vet and both builds.
The existing TestClient deprecation and Windows pytest-cache permission warnings
remain nonfatal. No public/admin source layout or bundled asset changed. Broad
33-route and focused nine-profile/four-series checks pass at four widths with
no JS errors or unintended mutations; substitute regression passes.

## Deployment verification

Release **`a14e57b`**, pushed to `main`, deployed successfully in
[Pages run 37855146633](https://github.com/uah-r6/uah-r6.github.io/actions/runs/37855146633).
All **49 live JSON documents** exactly match the validated local exports.
The focused nine-profile/four-series check and broad 33-route check passed live
at **1440, 1100, 768 and 390px**. Every map's displayed Ratings/scores and every
series participant's Rating/coverage match exports; all five Blue profiles have
three complete points and White retains one-series summaries. Zero/one/two-point,
stale partial, long-opponent and multi-team fixtures still enforce complete-only
semantics. Screenshots were inspected at every width; no JS errors or unintended
mutations occurred. Final production preservation and SQLite integrity checks
passed after browser verification. The repository checkpoint is clean and pushed.
**Stop: all three maps are defensibly recovered; no blocker remains.**
