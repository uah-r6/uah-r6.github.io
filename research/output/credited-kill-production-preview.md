# Credited-kill production preview — read-only, 2026-10-03

Production objective migration is complete and published. This new preview starts from the current corrected objective data. **No historical kill migration, public regeneration or publication has occurred.** Original reviews, experiments, v2 evaluation and failed v3 finals remain immutable.

## Evidence and coverage

The established counter study has **280 independent official agreements, zero mismatches**, with40 unavailable comparisons. A separately validated native-envelope reader supplies10 additional agreements on APAC8156; its source remains opt-in and rejected by the existing Python adapter. These are existing consumed results, not a new final evaluation or an increase in independent validation from duplicate observations.

The new canonical cached dataset contains **37maps, 387rounds, 3866player-rounds** across builds 9879602, 9883691, 9901603, 9918362. It was assembled without a parser run, download, model fit or repeated old experiment.

Complete round evidence: 382/387, 3820player-rounds. Strict whole-map eligibility: 35/37, 3650player-rounds. These denominators differ intentionally. APAC8156 remains incomplete under the original source because R03 has legacy death offset0; Chalet remains incomplete because its last4rounds have9participants. Native supplemental evidence is not silently substituted.

Canonical private dataset: `data/research/credited-round-dataset/dataset.json`. Each row preserves profile/numeric UID, username, cohort/map/physical/logical round/segment/build, start/end counters, direct owner/component samples, increments, finishes, victim eliminations, source/reason, round and whole-map eligibility. Credited-victim association, downer and precise event time remain null. `feedback_sequence` is the ordinal in the filtered elimination inventory, not the original all-feedback array index. Offsets order observations; they are never converted to seconds.

## Exact Stage A methodology

For a whole complete map, join every counter round to stored normalized participants by exact nonnil Ubisoft profile UUID. Require ten distinct participants and a full bijection between raw and normalized teams, preserving confirmed rehost team flips. Count kills as terminal minus initial counter within each round. Each new segment must satisfy the existing explicit reset guard; never subtract across resets. Refuse manual K/D overrides pending separate reconciliation.

Count 2K/3K/4K/5K from each player's credited round total. Multikill-extra is max(kills−1,0). KOST Kill is credited_kills>0; Objective, Survival and Trade components retain current stored behavior. DBNO adds no death. Victim final eliminations, objective actors, operator/action boundary, metadata, participation and all existing event features are untouched.

Only the four complete UAH maps (50rounds) qualify. **Entire12-round Chalet retains legacy counts** in the conditional scenario. The58supported-round discovery remains separately useful; it is not permission to mix corrected and legacy rounds inside Chalet. The9-player diagnostic deltas are not admitted.

## Current UAH map impact

KOST uses the already-published objective corrections. MK is2K/3K/4K/5K. Chalet's credited result is unavailable; its conditional display preserves the whole legacy map.

| Map / ID | Player | Current K/D | Credited K | K/D after | KPR after | MK before → after | KOST rounds |
| --- | --- | ---: | ---: | ---: | ---: | --- | ---: |
| Border `076d2b6b02bc` | Lgon | 13/7 | 14 | 2.000 | 1.167 | 2/1/0/0 → 2/1/0/0 | 10 → 10 |
| Border `076d2b6b02bc` | OhWowJay | 12/7 | 11 | 1.571 | 0.917 | 2/1/0/0 → 1/1/0/0 | 9 → 9 |
| Border `076d2b6b02bc` | AzoozNewzz | 10/6 | 10 | 1.667 | 0.833 | 1/2/0/0 → 1/2/0/0 | 8 → 8 |
| Border `076d2b6b02bc` | Tallman3.14 | 6/7 | 6 | 0.857 | 0.500 | 2/0/0/0 → 2/0/0/0 | 7 → 7 |
| Border `076d2b6b02bc` | DinoFireKing | 5/7 | 5 | 0.714 | 0.417 | 1/0/0/0 → 1/0/0/0 | 8 → 8 |
| Kafe Dostoyevsky `5adc26f7a402` | Lgon | 16/6 | 15 | 2.500 | 1.071 | 4/2/0/0 → 5/1/0/0 | 9 → 9 |
| Kafe Dostoyevsky `5adc26f7a402` | OhWowJay | 11/9 | 12 | 1.333 | 0.857 | 2/1/0/0 → 1/2/0/0 | 9 → 9 |
| Kafe Dostoyevsky `5adc26f7a402` | AzoozNewzz | 12/11 | 12 | 1.091 | 0.857 | 5/0/0/0 → 5/0/0/0 | 8 → 8 |
| Kafe Dostoyevsky `5adc26f7a402` | Tallman3.14 | 8/12 | 8 | 0.667 | 0.571 | 2/0/0/0 → 2/0/0/0 | 8 → 8 |
| Kafe Dostoyevsky `5adc26f7a402` | DinoFireKing | 6/9 | 6 | 0.667 | 0.429 | 2/0/0/0 → 2/0/0/0 | 10 → 10 |
| Border `8a6357ff307c` | Lgon | 15/11 | 14 | 1.273 | 1.000 | 4/1/0/0 → 3/1/0/0 | 9 → 9 |
| Border `8a6357ff307c` | OhWowJay | 15/10 | 16 | 1.600 | 1.143 | 3/1/1/0 → 2/2/1/0 | 8 → 8 |
| Border `8a6357ff307c` | AzoozNewzz | 5/13 | 5 | 0.385 | 0.357 | 2/0/0/0 → 2/0/0/0 | 7 → 7 |
| Border `8a6357ff307c` | Tallman3.14 | 2/13 | 2 | 0.154 | 0.143 | 0/0/0/0 → 0/0/0/0 | 5 → 5 |
| Border `8a6357ff307c` | DinoFireKing | 7/10 | 7 | 0.700 | 0.500 | 2/0/0/0 → 2/0/0/0 | 8 → 8 |
| Chalet `b595ffaaec57` | Lgon | 5/8 | unavailable | legacy | legacy | 2/0/0/0 → 2/0/0/0 | 5 → 5 |
| Chalet `b595ffaaec57` | OhWowJay | 10/7 | unavailable | legacy | legacy | 1/0/1/0 → 1/0/1/0 | 8 → 8 |
| Chalet `b595ffaaec57` | AzoozNewzz | 9/11 | unavailable | legacy | legacy | 2/0/0/0 → 2/0/0/0 | 8 → 8 |
| Chalet `b595ffaaec57` | Tallman3.14 | 8/9 | unavailable | legacy | legacy | 3/0/0/0 → 3/0/0/0 | 6 → 6 |
| Chalet `b595ffaaec57` | DinoFireKing | 8/6 | unavailable | legacy | legacy | 1/0/0/0 → 1/0/0/0 | 8 → 8 |
| Fortress `d64d5478cdb3` | Lgon | 12/6 | 11 | 1.833 | 1.100 | 1/1/1/0 → 1/2/0/0 | 8 → 8 |
| Fortress `d64d5478cdb3` | OhWowJay | 10/6 | 10 | 1.667 | 1.000 | 2/0/1/0 → 2/0/1/0 | 8 → 8 |
| Fortress `d64d5478cdb3` | AzoozNewzz | 9/7 | 9 | 1.286 | 0.900 | 1/1/0/0 → 1/1/0/0 | 7 → 7 |
| Fortress `d64d5478cdb3` | Tallman3.14 | 4/8 | 4 | 0.500 | 0.400 | 1/0/0/0 → 1/0/0/0 | 4 → 4 |
| Fortress `d64d5478cdb3` | DinoFireKing | 4/6 | 5 | 0.833 | 0.500 | 0/0/0/0 → 1/0/0/0 | 6 → 6 |

## Conditional season display, not fully credited season totals

| Player | Current K/D | Conditional K/D | KPR before → after | MK before → after | MK-extra before → after | KOST rounds /62 |
| --- | ---: | ---: | --- | --- | --- | ---: |
| Lgon | 61/38 | 59/38 (1.553) | 0.984 → 0.952 | 13/5/1/0 → 13/5/0/0 | 26 → 23 | 41/62 |
| OhWowJay | 58/39 | 59/39 (1.513) | 0.935 → 0.952 | 10/3/3/0 → 7/5/3/0 | 25 → 26 | 42/62 |
| AzoozNewzz | 45/48 | 45/48 (0.938) | 0.726 → 0.726 | 11/3/0/0 → 11/3/0/0 | 17 → 17 | 38/62 |
| Tallman3.14 | 28/49 | 28/49 (0.571) | 0.452 → 0.452 | 8/0/0/0 → 8/0/0/0 | 8 → 8 | 30/62 |
| DinoFireKing | 30/38 | 31/38 (0.816) | 0.484 → 0.500 | 6/0/0/0 → 7/0/0/0 | 6 → 7 | 40/62 |

Fully credited season totals are unavailable for all five players. Conditional known-map changes are Lgon−2, Jay+1, Dino+1, Azooz/Tallman0. All5players' deaths, objective credits and KOST totals remain unchanged in this Stage A preview. Exact projected JSON retains unrounded KD/KPR and all map count deltas.

## Four Chalet rounds: exact gap classification

Logical9–12 are physicalR01–R04 of segment2. All four have the same9header profiles,5UAH players versus4opponents,9distinct direct UID values and9scoreboard declarations. Natedog.UMich/profile51428074-6d7b-4fb3-8586-fa5a0c6bda26/numericUID17173956937034554342 appears in priorR08 but is absent from each current header and the direct UID-property inventory. There is no extra unbound UID in that typed view.

The9known participants do have kill-counter routes. The existing Go reader stops before deriving their samples because it correctly refuses an incomplete10-player roster. This is a **participant identity inventory gap after rehost**, not evidence of missing counters for the tracked five, a counter reset error or an alternate counter format. Cannot distinguish a true5v4 from an unrecorded participant using only these views. A reset is observed for all nine, but does not satisfy the existing same-ten-profile reset rule. No tenth identity or zero counter is invented. Retain the whole-map refusal.

## Native Death envelope: field semantics

The observer wraps the existing parser callback once. Broader controls preserve headers/operators/action/raw feedback68/68, supported counters67/67 and465eliminations; only the known legacy-zero Jin boundary is recovered. It adds callback bounds and event index, not a second kill decoder.

| Concept | What the envelope actually supplies |
| --- | --- |
| Victim | Raw feedback victim username; unique header binding can supply UID, no direct literal UID in the12reviewed callback controls |
| Finisher | Raw Kill username; Death can have no named finisher; header binding is separate |
| Credited killer / downer | No decoded field; no credited username or full UID in the two reviewed split callbacks |
| Ordering | Exact start/end byte positions, original event index, legacy offset, marker/bounds validity |
| Time | Existing coarse remaining timer, not a newly decoded elapsed or credited-kill timestamp |
| Cause | Existing Kill/Death and headshot/weapon feedback where present; no independent environmental/suicide cause field decoded |
| Team / suicide / TK | Header identity/team comparisons; no new native flags |
| DBNO relation | None decoded; separately identity-bound body observations cannot identify the attacker |

## Event timing and mandatory split controls

| Reviewed case | Raw3 / DBNO support | Counter increment | Raw4 / elimination | Finisher feed | Credited vs finisher |
| --- | ---: | ---: | ---: | ---: | --- |
| SAL8580 LairR06 Stk |74255864|74275879 (5→6)|74275897|74276292|Kheyze vs Maia|
| SAL8583 ClubhouseR02 resetz |86443440|86448083 (0→1)|86448101|86448473|Neskin vs pino|

Previously reviewed official HUD independently supports the DBNO/final death/credited owner in both cases, but not the downing shot. Downer remains unresolved. Credit is serialized alongside final elimination rather than the earlier DBNO in these two cases. The Neskin/pino first-final-death case is a mandatory regression, not proof of a universal opening policy when multiple DBNOs occur first.

**Counter time cannot universally stand in for a per-kill event time.** New canonical evidence contains2656positive counter-change packets, including3batched +2updates. Keep each batch as one count observation; do not split it into guessed victim events.

| Consumed batch | Player | Build | Offset | Counter | Same-round pre-first-death raw3 observations |
| --- | --- | ---: | ---: | --- | ---: |
| 8583 R01 | Flastryy.LOUD | 9879602 | 63839080 | 1→3 | 0 |
| 8585 R04 | Legacy.IMP | 9879602 | 73341168 | 1→3 | 0 |
| 8589 R11 | vitaking.FaZe | 9879602 | 65570590 | 11→13 | 1 |

These are exhaustive batched observations in the current canonical dataset, not independent per-victim ground truth. Private timelines retain all same-round counters, uniquely routed body states and elimination packets. Raw3 outside reviewed controls remains a DBNO candidate, not a universal enum proof.

Replay serialization/known packet offsets preserve observed final-elimination order, corroborated by two official plant-clock reset controls. Remaining-time sorting changes19/207SAL rounds;88inversions all cross planting. Zero-clock/overtime and missing elapsed clock precision remain explicit gaps. Do not subtract different countdown epochs or byte positions to implement trades.

## Feature readiness and migration boundaries

| Feature | Decision | Evidence and limitations |
| --- | --- | --- |
| Kills / KD / KPR | READY on whole complete maps; NOT complete season |280official agreements+10separate native; four UAH maps complete; nine-participant Chalet refusal; victim deaths unchanged|
| Round multikills | READY on whole complete maps |200SAL official size breakdowns/207public round summaries; requires valid round attribution, no event time|
| KOST Kill | READY on whole complete maps as Stage A component |Positive credited round count; retain corrected Objective and legacy Survival/Trade; cannot claim fully corrected T semantics|
| Openings | NOT READY for general runtime |193/200original,198/200packet-order,200/200case-supported consumed aggregates; generic credited-victim join and competing-DBNO policy unresolved|
| Trades / refrags | NOT READY |139/200original trade-count,121/200traded-death,83both; no validated victim-linked credited owner/window start/elapsed timer|
| Pivot | NOT READY for credited migration |Current own-alive<=foe-alive immediately before finisher elimination; credited player can already be dead; identity/order/DBNO alive policy unresolved|
| Untraded kills/deaths | NOT READY |Depend on previous owner, trade qualification and event timing; retain complete legacy event ledger|
| Clutch / survival / deaths | Preserve, not claimed chronologically fixed |Actual eliminations, not DBNO; packet-order changes can affect first1vX state; isolate future chronology fix|
| Headshots / HS% | NOT READY for credited ownership |Existing bit belongs to finisher event; do not divide legacy finisher headshots by a new credited denominator|

For A-downs-V/B-finishes-V, V's teammate killing B may trade the finisher; killing A may trade the credited owner only if A's credit and time are independently victim-bound. Existing sources do not establish that mapping generically. Neither timing nor ownership is promoted from proximity. Teamkill/suicide finish fixtures retain deaths but manufacture no opponent kills; unnamed Death stays cause-unresolved rather than automatically called environmental.

## Mixed semantics and public UI decision

A silent flat replacement is unacceptable. Legacy kills_traded+untraded_kills still sums to finisher kills, and legacy headshot rate uses a finisher denominator. Correcting the flat kills field while presenting those as the same kill population would break conservation and confuse comparisons. Likewise a62-round season containing a wholly legacy Chalet is not fully credited.

A defensible opt-in Stage A export would separate `credited_basic` (Kills/KD/KPR/multikills/KOST K) from `legacy_elimination_features` (finisherKills, headshots/HS%, entries/trades/pivot/untraded and clocks), provide source/completeness per map and season, and label the Rating's frozen inputs separately. Preserve old events and both owner concepts. Either hide unsupported event comparisons on the basic leaderboard or label them explicitly. The current UI/data have not been changed; approval of this policy precedes migration.

## Immutable Rating inputs

siege_style_v2's MAE0.03623 belongs to its original frozen research inputs. The5historical snapshot rows remain byte-identical and immutable. No projected corrected Rating was computed. Existing `rating_stats` deliberately refuses nonobjective input drift; Stage A must not bypass it by rewriting a snapshot or silently using projected basic stats. A future reviewed projection adapter should calculate the displayed Rating exclusively from those immutable originals and expose the input semantics. No new v3 development/final begun.

## Prepared migration / rollback procedure

1. Review the whole-map refusal policy, mixed-source public labels and unchanged event features. Current research does not authorize a live kill migration or publication.
2. Capture consistent SQLite and public JSON backups, archive fingerprints, normalized/source digests, metadata, identities, manual corrections and all Rating snapshot hashes. Existing objective backup remains a separate historical checkpoint.
3. Store optional versioned per-round credited counts/provenance separately from the preserved finisher/elimination ledger. Require complete source/participant/team/reset validation before accepting a whole map. Retain unsupported Chalet entirely on legacy semantics; do not import9-player diagnostic output.
4. Apply a reviewed count-only projection transactionally; preserve match IDs, objectives, raw events, action/operators and immutable v2 snapshots. Reconcile every changed field against this preview; reject any other count or metadata delta. Keep event features and their denominators explicitly separate.
5. Regenerate/validate local JSON under explicit authorization, compare map/season/career counts and all Ratings, then review UI source labels. Publishing is a separate authorized action. A publishing failure cannot alter local match data.
6. Roll back by disabling/removing only the new optional projection or restoring the consistent backups. Never delete raw identities, archived replays, old events or v2 snapshots. Re-export only if authorized.

## Verification and continuation

421Python tests passed,1optional real-replay smoke skipped,6subtests passed. Go tests including Y11/parser fixtures and go vet passed. No Go/default/shared stat/export/web source changed; public/admin builds remain their previously passing production builds and were not redundantly rerun. Protected objective/SQLite/archive/public/Rating and prior research guards pass. All new research remains local.

NEXT ACTION: preserve this additive checkpoint, then characterize remaining unclassified UID structures or explicit identity-linked damage records; obtain independent competing-DBNO and elapsed-clock controls on consumed replays. Do not use counter offset, first DBNO candidate, last UID or final totals to guess ownership/time. Stage B and complete-season credit remain unresolved.
