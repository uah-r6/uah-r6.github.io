"""Render new additive reports from sealed, cached comparison evidence."""
from collections import Counter
from pathlib import Path
import subprocess
import sys

from credited_round_dataset import DATA, read
from credited_feedback_identity_probe import DATA as UID_DATA
from v3_final_reserve import ROOT, sha


def sizes(row):
    return "/".join(str(row["multikill_sizes"][str(i)]) for i in (2, 3, 4, 5))


def number(value):
    return "unavailable" if value is None else f"{value:.3f}"


def main():
    guard = [sys.executable, str(ROOT/"research/verify_global_uid_checkpoint.py")]
    subprocess.run(guard, check=True)
    dataset = read(DATA/"dataset.json")
    preview = read(DATA/"production-preview.json")
    gap = read(DATA/"chalet-gap-audit.json")
    batches = read(DATA/"counter-batch-audit.json")
    frames = read(UID_DATA/"uid-roster-frames.json")
    lines = ["# Credited-kill production preview — read-only, 2026-10-03", "",
        "Production objective migration is complete and published. This new preview starts from the current corrected objective data. **No historical kill migration, public regeneration or publication has occurred.** Original reviews, experiments, v2 evaluation and failed v3 finals remain immutable.", "",
        "## Evidence and coverage", "",
        "The established counter study has **280 independent official agreements, zero mismatches**, with40 unavailable comparisons. A separately validated native-envelope reader supplies10 additional agreements on APAC8156; its source remains opt-in and rejected by the existing Python adapter. These are existing consumed results, not a new final evaluation or an increase in independent validation from duplicate observations.", "",
        f"The new canonical cached dataset contains **{dataset['counts']['maps']}maps, {dataset['counts']['rounds']}rounds, {dataset['counts']['player_rounds']}player-rounds** across builds " + ", ".join(map(str, dataset["counts"]["builds"])) + ". It was assembled without a parser run, download, model fit or repeated old experiment.", "",
        f"Complete round evidence: {dataset['counts']['complete_rounds']}/{dataset['counts']['rounds']}, {dataset['counts']['validated_player_rounds']}player-rounds. Strict whole-map eligibility: {dataset['counts']['complete_maps']}/{dataset['counts']['maps']}, {dataset['counts']['whole_map_eligible_player_rounds']}player-rounds. These denominators differ intentionally. APAC8156 remains incomplete under the original source because R03 has legacy death offset0; Chalet remains incomplete because its last4rounds have9participants. Native supplemental evidence is not silently substituted.", "",
        "Canonical private dataset: `data/research/credited-round-dataset/dataset.json`. Each row preserves profile/numeric UID, username, cohort/map/physical/logical round/segment/build, start/end counters, direct owner/component samples, increments, finishes, victim eliminations, source/reason, round and whole-map eligibility. Credited-victim association, downer and precise event time remain null. `feedback_sequence` is the ordinal in the filtered elimination inventory, not the original all-feedback array index. Offsets order observations; they are never converted to seconds.", "",
        "## Exact Stage A methodology", "",
        "For a whole complete map, join every counter round to stored normalized participants by exact nonnil Ubisoft profile UUID. Require ten distinct participants and a full bijection between raw and normalized teams, preserving confirmed rehost team flips. Count kills as terminal minus initial counter within each round. Each new segment must satisfy the existing explicit reset guard; never subtract across resets. Refuse manual K/D overrides pending separate reconciliation.", "",
        "Count 2K/3K/4K/5K from each player's credited round total. Multikill-extra is max(kills−1,0). KOST Kill is credited_kills>0; Objective, Survival and Trade components retain current stored behavior. DBNO adds no death. Victim final eliminations, objective actors, operator/action boundary, metadata, participation and all existing event features are untouched.", "",
        "Only the four complete UAH maps (50rounds) qualify. **Entire12-round Chalet retains legacy counts** in the conditional scenario. The58supported-round discovery remains separately useful; it is not permission to mix corrected and legacy rounds inside Chalet. The9-player diagnostic deltas are not admitted.", "",
        "## Current UAH map impact", "",
        "KOST uses the already-published objective corrections. MK is2K/3K/4K/5K. Chalet's credited result is unavailable; its conditional display preserves the whole legacy map.", "",
        "| Map / ID | Player | Current K/D | Credited K | K/D after | KPR after | MK before → after | KOST rounds |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- | ---: |"]
    for map_ in preview["maps"]:
        for p in map_["players"]:
            before, after = p["before"], p["conditional_display"]
            ready = map_["whole_map_ready"]
            lines.append(f"| {map_['map']} `{map_['map_id']}` | {p['player']} | {before['kills']}/{before['deaths']} | {after['kills'] if ready else 'unavailable'} | {number(after['kd']) if ready else 'legacy'} | {number(after['kpr']) if ready else 'legacy'} | {sizes(before)} → {sizes(after)} | {before['kost_rounds']} → {after['kost_rounds']} |")
    lines += ["", "## Conditional season display, not fully credited season totals", "",
        "| Player | Current K/D | Conditional K/D | KPR before → after | MK before → after | MK-extra before → after | KOST rounds /62 |",
        "| --- | ---: | ---: | --- | --- | --- | ---: |"]
    for p in preview["season"]:
        a, b = p["before"], p["conditional_mixed_source"]
        lines.append(f"| {p['player']} | {a['kills']}/{a['deaths']} | {b['kills']}/{b['deaths']} ({number(b['kd'])}) | {number(a['kpr'])} → {number(b['kpr'])} | {sizes(a)} → {sizes(b)} | {a['multikill_extra']} → {b['multikill_extra']} | {b['kost_rounds']}/62 |")
    lines += ["", "Fully credited season totals are unavailable for all five players. Conditional known-map changes are Lgon−2, Jay+1, Dino+1, Azooz/Tallman0. All5players' deaths, objective credits and KOST totals remain unchanged in this Stage A preview. Exact projected JSON retains unrounded KD/KPR and all map count deltas.", "",
        "## Four Chalet rounds: exact gap classification", "",
        "Logical9–12 are physicalR01–R04 of segment2. All four have the same9header profiles,5UAH players versus4opponents,9distinct direct UID values and9scoreboard declarations. Natedog.UMich/profile51428074-6d7b-4fb3-8586-fa5a0c6bda26/numericUID17173956937034554342 appears in priorR08 but is absent from each current header and the direct UID-property inventory. There is no extra unbound UID in that typed view.", "",
        "The9known participants do have kill-counter routes. The existing Go reader stops before deriving their samples because it correctly refuses an incomplete10-player roster. This is a **participant identity inventory gap after rehost**, not evidence of missing counters for the tracked five, a counter reset error or an alternate counter format. Cannot distinguish a true5v4 from an unrecorded participant using only these views. A reset is observed for all nine, but does not satisfy the existing same-ten-profile reset rule. No tenth identity or zero counter is invented. Retain the whole-map refusal.", "",
        "## Native Death envelope: field semantics", "",
        "The observer wraps the existing parser callback once. Broader controls preserve headers/operators/action/raw feedback68/68, supported counters67/67 and465eliminations; only the known legacy-zero Jin boundary is recovered. It adds callback bounds and event index, not a second kill decoder.", "",
        "| Concept | What the envelope actually supplies |",
        "| --- | --- |",
        "| Victim | Raw feedback victim username; unique header binding can supply UID, no direct literal UID in the12reviewed callback controls |",
        "| Finisher | Raw Kill username; Death can have no named finisher; header binding is separate |",
        "| Credited killer / downer | No decoded field; no credited username or full UID in the two reviewed split callbacks |",
        "| Ordering | Exact start/end byte positions, original event index, legacy offset, marker/bounds validity |",
        "| Time | Existing coarse remaining timer, not a newly decoded elapsed or credited-kill timestamp |",
        "| Cause | Existing Kill/Death and headshot/weapon feedback where present; no independent environmental/suicide cause field decoded |",
        "| Team / suicide / TK | Header identity/team comparisons; no new native flags |",
        "| DBNO relation | None decoded; separately identity-bound body observations cannot identify the attacker |", "",
        "## Event timing and mandatory split controls", "",
        "| Reviewed case | Raw3 / DBNO support | Counter increment | Raw4 / elimination | Finisher feed | Credited vs finisher |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
        "| SAL8580 LairR06 Stk |74255864|74275879 (5→6)|74275897|74276292|Kheyze vs Maia|",
        "| SAL8583 ClubhouseR02 resetz |86443440|86448083 (0→1)|86448101|86448473|Neskin vs pino|", "",
        "Previously reviewed official HUD independently supports the DBNO/final death/credited owner in both cases, but not the downing shot. Downer remains unresolved. Credit is serialized alongside final elimination rather than the earlier DBNO in these two cases. The Neskin/pino first-final-death case is a mandatory regression, not proof of a universal opening policy when multiple DBNOs occur first.", "",
        "**Counter time cannot universally stand in for a per-kill event time.** New canonical evidence contains2656positive counter-change packets, including3batched +2updates. Keep each batch as one count observation; do not split it into guessed victim events.", "",
        "| Consumed batch | Player | Build | Offset | Counter | Same-round pre-first-death raw3 observations |",
        "| --- | --- | ---: | ---: | --- | ---: |"]
    for r in batches["records"]:
        c = r["batched_change"]
        lines.append(f"| {r['map_id']} R{r['round']:02d} | {r['player']} | {r['build']} | {c['offset']} | {c['before']}→{c['after']} | {len(r['raw3_candidates_before_first_final_death'])} |")
    lines += ["", "These are exhaustive batched observations in the current canonical dataset, not independent per-victim ground truth. Private timelines retain all same-round counters, uniquely routed body states and elimination packets. Raw3 outside reviewed controls remains a DBNO candidate, not a universal enum proof.", "",
        "Replay serialization/known packet offsets preserve observed final-elimination order, corroborated by two official plant-clock reset controls. Remaining-time sorting changes19/207SAL rounds;88inversions all cross planting. Zero-clock/overtime and missing elapsed clock precision remain explicit gaps. Do not subtract different countdown epochs or byte positions to implement trades.", "",
        "## Feature readiness and migration boundaries", "",
        "| Feature | Decision | Evidence and limitations |", "| --- | --- | --- |",
        "| Kills / KD / KPR | READY on whole complete maps; NOT complete season |280official agreements+10separate native; four UAH maps complete; nine-participant Chalet refusal; victim deaths unchanged|",
        "| Round multikills | READY on whole complete maps |200SAL official size breakdowns/207public round summaries; requires valid round attribution, no event time|",
        "| KOST Kill | READY on whole complete maps as Stage A component |Positive credited round count; retain corrected Objective and legacy Survival/Trade; cannot claim fully corrected T semantics|",
        "| Openings | NOT READY for general runtime |193/200original,198/200packet-order,200/200case-supported consumed aggregates; generic credited-victim join and competing-DBNO policy unresolved|",
        "| Trades / refrags | NOT READY |139/200original trade-count,121/200traded-death,83both; no validated victim-linked credited owner/window start/elapsed timer|",
        "| Pivot | NOT READY for credited migration |Current own-alive<=foe-alive immediately before finisher elimination; credited player can already be dead; identity/order/DBNO alive policy unresolved|",
        "| Untraded kills/deaths | NOT READY |Depend on previous owner, trade qualification and event timing; retain complete legacy event ledger|",
        "| Clutch / survival / deaths | Preserve, not claimed chronologically fixed |Actual eliminations, not DBNO; packet-order changes can affect first1vX state; isolate future chronology fix|",
        "| Headshots / HS% | NOT READY for credited ownership |Existing bit belongs to finisher event; do not divide legacy finisher headshots by a new credited denominator|", "",
        "For A-downs-V/B-finishes-V, V's teammate killing B may trade the finisher; killing A may trade the credited owner only if A's credit and time are independently victim-bound. Existing sources do not establish that mapping generically. Neither timing nor ownership is promoted from proximity. Teamkill/suicide finish fixtures retain deaths but manufacture no opponent kills; unnamed Death stays cause-unresolved rather than automatically called environmental.", "",
        "## Mixed semantics and public UI decision", "",
        "A silent flat replacement is unacceptable. Legacy kills_traded+untraded_kills still sums to finisher kills, and legacy headshot rate uses a finisher denominator. Correcting the flat kills field while presenting those as the same kill population would break conservation and confuse comparisons. Likewise a62-round season containing a wholly legacy Chalet is not fully credited.", "",
        "A defensible opt-in Stage A export would separate `credited_basic` (Kills/KD/KPR/multikills/KOST K) from `legacy_elimination_features` (finisherKills, headshots/HS%, entries/trades/pivot/untraded and clocks), provide source/completeness per map and season, and label the Rating's frozen inputs separately. Preserve old events and both owner concepts. Either hide unsupported event comparisons on the basic leaderboard or label them explicitly. The current UI/data have not been changed; approval of this policy precedes migration.", "",
        "## Immutable Rating inputs", "",
        "siege_style_v2's MAE0.03623 belongs to its original frozen research inputs. The5historical snapshot rows remain byte-identical and immutable. No projected corrected Rating was computed. Existing `rating_stats` deliberately refuses nonobjective input drift; Stage A must not bypass it by rewriting a snapshot or silently using projected basic stats. A future reviewed projection adapter should calculate the displayed Rating exclusively from those immutable originals and expose the input semantics. No new v3 development/final begun.", "",
        "## Prepared migration / rollback procedure", "",
        "1. Review the whole-map refusal policy, mixed-source public labels and unchanged event features. Current research does not authorize a live kill migration or publication.",
        "2. Capture consistent SQLite and public JSON backups, archive fingerprints, normalized/source digests, metadata, identities, manual corrections and all Rating snapshot hashes. Existing objective backup remains a separate historical checkpoint.",
        "3. Store optional versioned per-round credited counts/provenance separately from the preserved finisher/elimination ledger. Require complete source/participant/team/reset validation before accepting a whole map. Retain unsupported Chalet entirely on legacy semantics; do not import9-player diagnostic output.",
        "4. Apply a reviewed count-only projection transactionally; preserve match IDs, objectives, raw events, action/operators and immutable v2 snapshots. Reconcile every changed field against this preview; reject any other count or metadata delta. Keep event features and their denominators explicitly separate.",
        "5. Regenerate/validate local JSON under explicit authorization, compare map/season/career counts and all Ratings, then review UI source labels. Publishing is a separate authorized action. A publishing failure cannot alter local match data.",
        "6. Roll back by disabling/removing only the new optional projection or restoring the consistent backups. Never delete raw identities, archived replays, old events or v2 snapshots. Re-export only if authorized.", "",
        "## Verification and continuation", "",
        "421Python tests passed,1optional real-replay smoke skipped,6subtests passed. Go tests including Y11/parser fixtures and go vet passed. No Go/default/shared stat/export/web source changed; public/admin builds remain their previously passing production builds and were not redundantly rerun. Protected objective/SQLite/archive/public/Rating and prior research guards pass. All new research remains local.", "",
        "NEXT ACTION: preserve this additive checkpoint, then characterize remaining unclassified UID structures or explicit identity-linked damage records; obtain independent competing-DBNO and elapsed-clock controls on consumed replays. Do not use counter offset, first DBNO candidate, last UID or final totals to guess ownership/time. Stage B and complete-season credit remain unresolved.", ""]
    target = ROOT/"research/output/credited-kill-production-preview.md"
    target.write_text("\n".join(lines), encoding="utf-8")
    discovery = ["# Consumed UID list framing — 2026-10-03", "",
                 "Explicit framing discovery in the two previously sealed buffers, not a damage/DBNO/downer decoder.", "",
                 "| Buffer | Complete ten-entry lists | Literal UID occurrences covered | Unclassified remaining | Distinct UID orders |",
                 "| --- | ---: | ---: | ---: | ---: |"]
    for r in frames["records"]:
        discovery.append(f"| {r['map_id']} R{r['round']:02d} | {r['frame_count']} | {r['literal_uid_matches_covered']} | {r['remaining_unclassified']} | {r['orders']} |")
    discovery += ["", "Observed local framing: byte0x0a followed by10entries, each8-byte little-endian known UID plus exactly3opaque bytes (`20 00 ff` or `21 00 ff`), total111bytes. Accept only all10distinct expected header UIDs; reject duplicates, unknown replacement, wrong count, width/suffix, truncation and overlap. Array order is not an ownership rule. This recognizes a raw counted list; its outer network packet/type and suffix semantics remain undecoded.", "",
                  "526lists/5260literal UID matches are now framed.12070other occurrences remain unclassified, besides20known UID property records. Repeated full roster lists occur as ordinary same-round controls; none of these exact fixed-width lists appears within±50000bytes of the independently reviewed DBNO/credit/final-death/finish anchors. The window is a byte-context control, never a time interval or proof of absence elsewhere. A fuller variable-width structure remains a separate lead.", "",
                  "No directed attacker/victim field, HP/life-state meaning, downer or event timestamp is established by this list. Do not assign from nearby references or count. All decoded raw offsets/lists and opaque suffix distributions stay private. No old discovery result overwritten, parser/default change, historical migration or target/evaluation repeated.", ""]
    (ROOT/"research/output/credited-uid-roster-framing.md").write_text("\n".join(discovery), encoding="utf-8")
    subprocess.run(guard, check=True)
    print("New production preview and UID framing reports rendered; protected state unchanged")


if __name__ == "__main__":
    main()
