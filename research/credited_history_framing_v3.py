"""Additive typed framing trial, never a runtime parser or credited join.

Walk declared item count/bounds. Exact header references required. Preserve
opaque values and list order. Earlier failed/refused predictions stay frozen.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import subprocess
import sys

from credited_history_framing_v2 import DATA as PREVIOUS, cumulative_consensus
from credited_uid_pair_inventory import reference_at
from credited_late_history_development import immutable_write
from credited_round_dataset import read, cached_index, cached_observation
from v3_final_reserve import ROOT, sha, source_sha

DATA = ROOT/"data/research/credited-history-framing-v3"
WIDTHS = {1:62, 2:62, 3:41, 5:53, 7:53, 10:26}


def decode_at(data, at, end, players):
    if not 0 <= at < end <= len(data):
        return None
    kind = data[at]
    width = WIDTHS.get(kind)
    if width is None or at+width > end:
        return None
    scalar = int.from_bytes(data[at+1:at+5],"little")
    if not scalar:
        return None
    row = {"start":at,"end":at+width,"kind_byte":kind,"opaque_scalar":scalar,
           "raw_hex":data[at:at+width].hex(),"elapsed_seconds":None,"event_role":None}
    if kind in (1,2,3):
        row["weapon_id"] = int.from_bytes(data[at+5:at+13],"little")
        row["entity_reference"] = int.from_bytes(data[at+13:at+21],"little")
        identity_offset = at+21
    elif kind in (5,7):
        row["entity_reference"] = int.from_bytes(data[at+5:at+13],"little")
        identity_offset = at+13
    else:
        identity_offset = at+5
    if "entity_reference" in row and not row["entity_reference"]:
        return None
    first = reference_at(data,identity_offset,players)
    if first is None:
        return None
    if kind in (1,2,5,7):
        second = reference_at(data,identity_offset+20,players)
        if second is None:
            return None
        row.update(first=first,second=second)
    else:
        row["reference"] = first
    if kind in (1,2):
        if data[at+61] not in (0,1):
            return None
        row["headshot"] = bool(data[at+61])
    elif kind == 10:
        if data[at+25] not in (1,2):
            return None
        row["opaque_tail_u8"] = data[at+25]
    return row


def decode_box(data,box,players):
    at, items = box["start"]+25, []
    for ordinal in range(box["item_count"]-1):
        item = decode_at(data,at,box["end"],players)
        if item is None:
            return {"complete":False,"items":items,"reason":"unknown_or_invalid_item_not_skipped",
                    "unresolved_offset":at,"remaining_hex":data[at:box["end"]].hex()}
        items.append({**item,"ordinal":ordinal})
        at = item["end"]
    return {"complete":at == box["end"],"items":items,
            "reason":"exact_count_and_bytes" if at == box["end"] else "trailing_bytes_not_skipped",
            "remaining_hex":data[at:box["end"]].hex()}


def feed_parity(items, finishes):
    projected, expected = [], []
    for i in items:
        if i["kind_byte"] in (1,2):
            projected.append(("Kill",i["first"]["username"],i["second"]["username"],i["weapon_id"],i["headshot"]))
        elif i["kind_byte"] == 3:
            projected.append(("Death",i["reference"]["username"],None,None,None))
    # Keep the existing filtered feedback sequence; do not sort a legacy zero
    # offset ahead of known offsets or silently substitute the native source.
    for e in finishes:
        f = e["feedback"]
        if f["type"]["name"] == "Kill":
            expected.append(("Kill",f["username"],f["target"],f["weaponID"],f.get("headshot",False)))
        elif f["type"]["name"] == "Death":
            expected.append(("Death",f["username"],None,None,None))
        else:
            raise ValueError("Unsupported original elimination kind")
    return {"exact_original_filtered_feed_identity_weapon_headshot_order":projected == expected,
            "projection":projected,"original":expected,"eliminations":len(expected),
            "legacy_zero_offset_count":sum(e["offset"] == 0 for e in finishes),
            "cause_for_single_reference_deaths":None,"ordering_source":"original_filtered_feedback_sequence"}


def main():
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument("--cohort",choices=("six","68"),default="six")
    args = args.parse_args()
    guard = [sys.executable,str(ROOT/"research/verify_history_framing_checkpoint.py")]
    subprocess.run(guard,check=True)
    previous_path = PREVIOUS/("result-"+args.cohort+".json")
    selection = read(previous_path)["records"]
    reservation = {"base_head":"9b491ac","previous_result_sha256":sha(previous_path),
                   "helper_hashes":{str(p.relative_to(ROOT)).replace("\\","/"):source_sha(p) for p in (
                       Path(__file__),ROOT/"research/credited_history_framing_v2.py",ROOT/"research/credited_uid_pair_inventory.py")},
                   "width_predictions":WIDTHS,"kind10_opaque_tail_predictions":[1,2],
                   "kind3_append_sha256":sha(ROOT/"data/research/credited-history-append-development/result.json"),
                   "kind2_scope":"Separate kill-shaped friendly-item hypothesis, require independent feed parity, no generic credit policy",
                   "scope":"Consumed cached structural controls, no elapsed seconds or credited/runtime promotion"}
    reservation = json.loads(json.dumps(reservation))
    immutable_write(DATA/("reservation-"+args.cohort+".json"),reservation)
    index, records = cached_index(), []
    for source in selection:
        old_path = PREVIOUS/"records"/(source["replay_sha256"]+".json")
        previous = read(old_path)
        dump = ROOT/previous["dump_path"]
        if sha(dump) != previous["dump_sha256"]:
            raise ValueError("Fixed dump changed")
        cache, observation = cached_observation(index,source["replay_sha256"])
        data, players = dump.read_bytes(),observation["header"]["players"]
        boxes = [{k:box[k] for k in ("start","end","item_count","payload_length")} |
                 {"framed":decode_box(data,box,players)} for box in previous["containers"]]
        cumulative = cumulative_consensus(boxes)
        parity = feed_parity(cumulative["items"],observation["credit"]["finishes"])
        record = ({k:previous[k] for k in ("event","map_id","round","replay_sha256","dump_path","dump_sha256")} |
                 {"containers":boxes,"cumulative":cumulative,"feed_parity":parity,
                  "original_counter_complete":observation["credit"]["complete"],
                  "inputs":{str(p.relative_to(ROOT)).replace("\\","/"):sha(p) for p in (cache,old_path)},
                  "kind_counts":dict(Counter(i["kind_byte"] for i in cumulative["items"]))})
        immutable_write(DATA/"records"/(source["replay_sha256"]+".json"),record)
        records.append(record)
        print(source["event"],source["map_id"],source["round"],"history",cumulative["complete"],
              "feed",parity["exact_original_filtered_feed_identity_weapon_headshot_order"],record["kind_counts"],flush=True)
    result = {"records":[{k:r[k] for k in ("event","map_id","round","replay_sha256")} |
                         {"complete":r["cumulative"]["complete"],"feed_parity":r["feed_parity"]["exact_original_filtered_feed_identity_weapon_headshot_order"]} for r in records],
              "complete_histories":sum(r["cumulative"]["complete"] for r in records),
              "matching_feed_histories":sum(r["feed_parity"]["exact_original_filtered_feed_identity_weapon_headshot_order"] for r in records),
              "complete_containers":sum(b["framed"]["complete"] for r in records for b in r["containers"]),
              "partial_containers":sum(not b["framed"]["complete"] for r in records for b in r["containers"]),
              "eliminations":sum(r["feed_parity"]["eliminations"] for r in records),
              "status":"explicit_count_bounded_history_roles_and_seconds_unresolved"}
    immutable_write(DATA/("result-"+args.cohort+".json"),result)
    subprocess.run(guard,check=True)


if __name__ == "__main__":
    main()
