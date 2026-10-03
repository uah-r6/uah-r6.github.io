"""Preserve bounded non-statistical history items without guessing semantics.

A single terminal unknown object is opaque through its declared container end.
Unknown middle items are not skipped. No event role or objective assigned.
"""
from pathlib import Path
import subprocess
import sys
import json

from credited_uid_pair_inventory import reference_at, paired_at
from credited_late_event_layout_probe import candidate_at
from credited_feedback_identity_probe import DATA as UID_DATA, direct_references
from credited_late_history_controls import DATA
from credited_round_dataset import cached_index, cached_observation, read
from v3_final_reserve import ROOT, sha, source_sha


def expand_container(data, box, players, candidates):
    at, items = box["start"]+25, []
    for i in range(box["item_count"]-1):
        if at >= box["end"]:
            return {"complete": False, "items": items, "reason": "declared_item_missing"}
        c = candidates.get(at)
        if c:
            if c["end"] > box["end"]:
                return {"complete": False, "items": items, "reason": "item_outside_container"}
            items.append({"start": at, "end": c["end"], "kind": "existing_candidate", "candidate": c})
            at = c["end"]
            continue
        if data[at] == 10 and at+25 <= box["end"]:
            ref = reference_at(data, at+5, players)
            if ref:
                items.append({"start": at, "end": at+25, "kind": "opaque_single_reference",
                              "raw_hex": data[at:at+25].hex(), "reference": ref, "event_role": None})
                at += 25
                continue
        remaining = box["item_count"]-1-i
        if remaining == 1 and not any(at < start < box["end"] for start in candidates):
            items.append({"start": at, "end": box["end"], "kind": "opaque_terminal_object",
                          "raw_hex": data[at:box["end"]].hex(), "event_role": None})
            at = box["end"]
            continue
        return {"complete": False, "items": items, "reason": "unknown_middle_item_not_skipped", "offset": at}
    return {"complete": at == box["end"], "items": items,
            "reason": "exact_declared_count_and_bounds" if at == box["end"] else "trailing_unframed_bytes"}


def main():
    guard = [sys.executable, str(ROOT/"research/verify_late_history_checkpoint.py")]
    subprocess.run(guard, check=True)
    boxes_path = DATA/"container-probe.json"
    boxes = read(boxes_path)
    inventory = read(UID_DATA/"global-uid-inventory.json")
    controls = read(DATA/"result.json")
    sources = {(r["cohort"], r["map_id"], r["logical_round"]): r for r in controls["records"]}
    for row in inventory["records"]:
        sources["SAL", row["map_id"], row["round"]] = {"replay_sha256": row["replay_sha256"],
            "dump_path": str((UID_DATA/(row["replay_sha256"]+".dump")).relative_to(ROOT)).replace("\\", "/"),
            "dump_sha256": row["dump_sha256"]}
    index = cached_index()
    results = []
    for row in boxes["records"]:
        source = sources[row["cohort"], row["map_id"], row["round"]]
        dump = ROOT/source["dump_path"]
        if sha(dump) != source["dump_sha256"]:
            raise ValueError("Fixed input buffer changed")
        data = dump.read_bytes()
        _, observed = cached_observation(index, source["replay_sha256"])
        players = observed["header"]["players"]
        refs = direct_references(data, players)["literal_numeric_uid_references"]
        pairs = [p for at in sorted({r["relative_offset"] for r in refs}) if (p := paired_at(data, at, players))]
        candidates = {c["start"]: c for pair in pairs if (c := candidate_at(data, pair))}
        expanded = [{"original_container": box, "expanded": expand_container(data, box, players, candidates)} for box in row["containers"]]
        result = {"cohort": row["cohort"], "map_id": row["map_id"], "round": row["round"],
                  "containers": expanded, "complete": sum(b["expanded"]["complete"] for b in expanded),
                  "unresolved": sum(not b["expanded"]["complete"] for b in expanded),
                  "interpretation": "Complete means declared count/byte bounds with opaque non-stat objects retained. Not complete decoded event semantics or production promotion."}
        results.append(result)
        print(row["cohort"], row["map_id"], row["round"], "bounded complete/unresolved", result["complete"], result["unresolved"], flush=True)
    result = {"source_sha256": source_sha(Path(__file__)), "original_partial_sha256": sha(boxes_path),
              "records": results, "status": "consumed_structural_container_extension_unknown_semantics_preserved"}
    target = DATA/"opaque-items.json"
    if target.exists() and read(target) != result:
        raise ValueError("Never overwrite opaque item result")
    if not target.exists():
        target.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    subprocess.run(guard, check=True)


if __name__ == "__main__":
    main()
