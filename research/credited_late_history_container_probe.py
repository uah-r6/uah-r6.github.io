"""Explicit size/count framing controls for consumed late-history candidates.

Only local container structure is assessed. Unknown item kinds produce a
partial result, never a repaired or production-complete event history.
"""
from pathlib import Path
import subprocess
import sys
import json

from credited_round_dataset import read
from credited_feedback_identity_probe import DATA as UID_DATA
from credited_late_history_controls import DATA
from v3_final_reserve import ROOT, sha, source_sha


def container_at(data, descriptor_offset, descriptor, candidates):
    start = descriptor_offset-16
    if start < 0 or data[descriptor_offset:descriptor_offset+9] != descriptor:
        return None
    payload_length = int.from_bytes(data[start+4:start+12], "little")
    count = int.from_bytes(data[start+12:start+16], "little")
    end = start+12+payload_length
    if not 13 <= payload_length <= 65536 or not 1 <= count <= 64 or end > len(data) or end < descriptor_offset+9:
        return None
    at, decoded = descriptor_offset+9, []
    for _ in range(count-1):
        candidate = candidates.get(at)
        if candidate is None:
            return {"start": start, "end": end, "payload_length": payload_length, "item_count": count,
                    "known_items": decoded, "complete": False, "unresolved_offset": at,
                    "unknown_kind_byte": data[at] if at < end else None}
        if candidate["end"] > end:
            return None
        decoded.append(candidate)
        at = candidate["end"]
    return {"start": start, "end": end, "payload_length": payload_length, "item_count": count,
            "opaque_header_u32": int.from_bytes(data[start:start+4], "little"),
            "known_items": decoded, "complete": at == end,
            "unresolved_offset": at if at != end else None,
            "unknown_kind_byte": data[at] if at < end else None}


def main():
    guard = [sys.executable, str(ROOT/"research/verify_credited_semantics_checkpoint.py")]
    subprocess.run(guard, check=True)
    original = read(UID_DATA/"late-event-layout-probe.json")
    controls = read(DATA/"result.json")
    # Fixed prior results supply candidate positions, not invented byte searches.
    inputs, rows = {}, []
    inventory = read(UID_DATA/"global-uid-inventory.json")
    for row in original["records"]:
        old = next(r for r in inventory["records"] if r["map_id"] == row["map_id"])
        rows.append({"cohort": "SAL", "map_id": row["map_id"], "number": row["round"],
                     "dump": UID_DATA/(row["replay_sha256"]+".dump"), "dump_sha256": old["dump_sha256"],
                     "candidates": row["candidates"]})
    # Fixed controls retained unique payloads, so reconstruct their physical copies.
    from credited_late_event_layout_probe import candidate_at
    from credited_uid_pair_inventory import paired_at
    from credited_feedback_identity_probe import direct_references
    from credited_round_dataset import cached_index, cached_observation
    index = cached_index()
    for row in controls["records"]:
        _, observed = cached_observation(index, row["replay_sha256"])
        dump = ROOT/row["dump_path"]
        data = dump.read_bytes()
        refs = direct_references(data, observed["header"]["players"])["literal_numeric_uid_references"]
        pairs = [p for at in sorted({r["relative_offset"] for r in refs}) if (p := paired_at(data, at, observed["header"]["players"]))]
        candidates = [c for p in pairs if (c := candidate_at(data,p))]
        rows.append({"cohort": row["cohort"], "map_id": row["map_id"], "number": row["logical_round"],
                     "dump": dump, "dump_sha256": row["dump_sha256"], "candidates": candidates})
    results = []
    for row in rows:
        if sha(row["dump"]) != row["dump_sha256"]:
            raise ValueError("Fixed buffer changed")
        data = row["dump"].read_bytes()
        candidates = {c["start"]: c for c in row["candidates"]}
        first = min(candidates)
        # The first recognized event may follow an unknown item. Locate only
        # bounded size/count containers enclosing that event, rather than
        # asserting that its preceding nine bytes are the descriptor.
        descriptors = set()
        for possible in range(max(0, first-512), first):
            descriptor = data[possible:possible+9]
            if len(descriptor) != 9 or descriptor[0] != 9 or descriptor[5:] != b"\x03\x00\x00\x00":
                continue
            box = container_at(data, possible, descriptor, candidates)
            if box and box["start"] < first < box["end"]:
                descriptors.add(descriptor)
        if len(descriptors) != 1:
            raise ValueError("Unique enclosing descriptor not established")
        descriptor = next(iter(descriptors))
        cursor, containers = 0, []
        while (at := data.find(descriptor, cursor)) >= 0:
            cursor = at+1
            c = container_at(data, at, descriptor, candidates)
            if c:
                containers.append(c)
        covered = {c["start"] for box in containers for c in box["known_items"]}
        results.append({"cohort": row["cohort"], "map_id": row["map_id"], "round": row["number"],
                        "descriptor": descriptor.hex(), "containers": containers,
                        "complete_containers": sum(c["complete"] for c in containers),
                        "partial_containers": sum(not c["complete"] for c in containers),
                        "candidate_copies_framed": len(covered), "candidate_copies_total": len(candidates),
                        "limits": "Size/count/reference structure only. Unknown kinds and trailing data retained as partial; no semantic repair, runtime parser, scalar calibration or downer role."})
        inputs[str(row["dump"].relative_to(ROOT)).replace("\\", "/")] = sha(row["dump"])
        print(row["cohort"], row["map_id"], row["number"], "complete/partial", results[-1]["complete_containers"],
              results[-1]["partial_containers"], "candidate copies framed", len(covered), "/", len(candidates), flush=True)
    result = {"source_sha256": source_sha(Path(__file__)), "inputs": inputs, "records": results,
              "status": "consumed_size_count_container_framing_partial_unknown_kinds"}
    target = DATA/"container-probe.json"
    if target.exists() and read(target) != result:
        raise ValueError("Never overwrite framing controls")
    if not target.exists():
        target.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    subprocess.run(guard, check=True)


if __name__ == "__main__":
    main()
