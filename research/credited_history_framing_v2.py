"""Second structural framing trial; roles/time/production remain unresolved.

Opaque kind10 width26 is independently bounded by exact single-item appends.
Preserve earlier failed framing unchanged. Never skip an unknown item.
"""
import argparse
from collections import Counter
import json
import subprocess
import sys
from pathlib import Path

from credited_late_history_container_probe import container_at
from credited_uid_pair_inventory import reference_at, paired_at
from credited_late_event_layout_probe import candidate_at
from credited_feedback_identity_probe import DATA as UID_DATA, direct_references
from credited_late_history_controls import DATA as SIX_DATA
from credited_late_history_development import DATA as BROAD_DATA, immutable_write
from credited_round_dataset import read, cached_index, cached_observation
from v3_final_reserve import ROOT, sha, source_sha

DATA = ROOT/"data/research/credited-history-framing-v2"


def framed_items(data, box, players, candidates):
    at, items = box["start"]+25, []
    for ordinal in range(box["item_count"]-1):
        candidate = candidates.get(at)
        if candidate:
            end = candidate["end"]
            item = {"ordinal": ordinal, "start": at, "end": end,
                    "kind_byte": candidate["kind_byte"], "candidate": candidate}
        elif at+26 <= box["end"] and data[at] == 10 and data[at+25] == 1:
            ref = reference_at(data, at+5, players)
            if ref is None:
                return partial(data, box, at, items, "kind10_reference_unresolved")
            end = at+26
            item = {"ordinal": ordinal, "start": at, "end": end, "kind_byte": 10,
                    "reference": ref, "opaque_scalar": int.from_bytes(data[at+1:at+5], "little"),
                    "opaque_tail_u8": data[at+25], "event_role": None}
        else:
            return partial(data, box, at, items, "unknown_item_layout_not_skipped")
        if end > box["end"]:
            return partial(data, box, at, items, "item_outside_declared_bounds")
        item["raw_hex"] = data[at:end].hex()
        items.append(item)
        at = end
    if at != box["end"]:
        return partial(data, box, at, items, "trailing_bytes_not_skipped")
    return {"complete": True, "items": items, "reason": "exact_count_and_bytes"}


def partial(data, box, at, items, reason):
    return {"complete": False, "items": items, "reason": reason, "unresolved_offset": at,
            "remaining_hex": data[at:box["end"]].hex()}


def cumulative_consensus(containers):
    complete = [c for c in containers if c["framed"]["complete"]]
    if not complete:
        return {"complete": False, "reason": "no_complete_container", "items": []}
    longest = max(complete, key=lambda c: c["item_count"])
    whole = [i["raw_hex"] for i in longest["framed"]["items"]]
    for c in complete:
        part = [i["raw_hex"] for i in c["framed"]["items"]]
        if part != whole[:len(part)]:
            return {"complete": False, "reason": "cumulative_items_changed_or_reordered", "items": []}
    if any(not c["framed"]["complete"] for c in containers):
        return {"complete": False, "reason": "partial_container_retained", "items": longest["framed"]["items"]}
    scalars = [i.get("opaque_scalar", i.get("candidate", {}).get("opaque_scalar")) for i in longest["framed"]["items"]]
    return {"complete": True, "reason": "exact_cumulative_prefixes", "items": longest["framed"]["items"],
            "scalars_nondecreasing": all(a <= b for a,b in zip(scalars, scalars[1:])),
            "scalar_ties": dict(Counter(str(s) for s in scalars if scalars.count(s) > 1)),
            "elapsed_seconds": None, "production_authoritative": False}


def inspect(data, players, candidates):
    by_start = {c["start"]: c for c in candidates}
    if not by_start:
        return {"unresolved": "no_candidate_anchor", "containers": []}
    first = min(by_start)
    descriptors = set()
    for possible in range(max(0, first-512), first):
        descriptor = data[possible:possible+9]
        if len(descriptor) != 9 or descriptor[0] != 9 or descriptor[5:] != b"\x03\x00\x00\x00":
            continue
        box = container_at(data, possible, descriptor, by_start)
        if box and box["start"] < first < box["end"]:
            descriptors.add(descriptor)
    if len(descriptors) != 1:
        return {"unresolved": "unique_descriptor_not_established", "containers": []}
    descriptor = next(iter(descriptors))
    cursor, containers = 0, []
    while (at := data.find(descriptor, cursor)) >= 0:
        cursor = at+1
        box = container_at(data, at, descriptor, by_start)
        if box:
            containers.append({k: box[k] for k in ("start", "end", "item_count", "payload_length")} |
                              {"framed": framed_items(data, box, players, by_start)})
    return {"descriptor": descriptor.hex(), "containers": containers,
            "complete_containers": sum(c["framed"]["complete"] for c in containers),
            "partial_containers": sum(not c["framed"]["complete"] for c in containers),
            "cumulative": cumulative_consensus(containers)}


def six_sources():
    old = read(UID_DATA/"global-uid-inventory.json")
    six = [{"event": "SAL", "map_id": r["map_id"], "round": r["round"],
            "replay_sha256": r["replay_sha256"], "dump_path": str((UID_DATA/(r["replay_sha256"]+".dump")).relative_to(ROOT)).replace("\\", "/"),
            "dump_sha256": r["dump_sha256"]} for r in old["records"]]
    six += [{"event": r["cohort"], "map_id": r["map_id"], "round": r["logical_round"],
             "replay_sha256": r["replay_sha256"], "dump_path": r["dump_path"], "dump_sha256": r["dump_sha256"]}
            for r in read(SIX_DATA/"result.json")["records"]]
    return six


def main():
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument("--cohort", choices=("six", "68"), default="six")
    args = args.parse_args()
    guard = [sys.executable, str(ROOT/"research/verify_history_development_checkpoint.py")]
    subprocess.run(guard, check=True)
    if args.cohort == "six":
        sources = six_sources()
    else:
        sources = []
        for r in read(BROAD_DATA/"sample-68.json")["records"]:
            record = read(ROOT/r["record_path"])
            dumps = [(n,h) for n,h in record["inputs"].items() if n.endswith(".dump")]
            if len(dumps) != 1:
                raise ValueError("Exact dump source required")
            sources.append({k: record[k] for k in ("event", "map_id", "round", "replay_sha256")} |
                           {"dump_path": dumps[0][0], "dump_sha256": dumps[0][1]})
    reservation = {"base_head": "33cb8f2", "sources": sources,
                   "helper_hashes": {str(Path(p).relative_to(ROOT)).replace("\\", "/"): source_sha(p)
                                     for p in (Path(__file__), ROOT/"research/credited_late_history_container_probe.py",
                                               ROOT/"research/credited_uid_pair_inventory.py", ROOT/"research/credited_late_event_layout_probe.py")},
                   "kind10_evidence_sha256": sha(SIX_DATA/"append-inventory.json"),
                   "limits": "Structural26-byte kind10 only; unknowns refuse; no roles/clock/runtime promotion"}
    immutable_write(DATA/("reservation-"+args.cohort+".json"), reservation)
    index, records = cached_index(), []
    for source in sources:
        dump = ROOT/source["dump_path"]
        if sha(dump) != source["dump_sha256"]:
            raise ValueError("Consumed buffer changed")
        cache, observation = cached_observation(index, source["replay_sha256"])
        data, players = dump.read_bytes(), observation["header"]["players"]
        refs = direct_references(data, players)["literal_numeric_uid_references"]
        pairs = [p for at in sorted({r["relative_offset"] for r in refs}) if (p := paired_at(data, at, players))]
        candidates = [c for p in pairs if (c := candidate_at(data, p))]
        result = {**source, "inputs": {str(cache.relative_to(ROOT)).replace("\\", "/"): sha(cache)}, **inspect(data, players, candidates)}
        immutable_write(DATA/"records"/(source["replay_sha256"]+".json"), result)
        records.append(result)
        print(source["event"], source["map_id"], source["round"], "framed", result.get("complete_containers",0),
              "partial", result.get("partial_containers",0), "cumulative", result.get("cumulative",{}).get("reason",result.get("unresolved")), flush=True)
    summary = {"records": [{k:r[k] for k in ("event", "map_id", "round", "replay_sha256")} |
                           {"complete": r.get("cumulative",{}).get("complete",False),
                            "reason": r.get("cumulative",{}).get("reason",r.get("unresolved"))} for r in records],
               "complete_containers": sum(r.get("complete_containers",0) for r in records),
               "partial_containers": sum(r.get("partial_containers",0) for r in records),
               "complete_histories": sum(r.get("cumulative",{}).get("complete",False) for r in records)}
    immutable_write(DATA/("result-"+args.cohort+".json"), summary)
    subprocess.run(guard, check=True)


if __name__ == "__main__":
    main()
