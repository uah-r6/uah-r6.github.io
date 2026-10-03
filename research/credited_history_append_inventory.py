"""Inventory exact single-item append boundaries in sealed history containers.

Counts and unchanged byte prefixes establish boundaries; no nearest-event
search or unknown-item skipping. Item roles and scalar units remain unknown.
"""
from collections import Counter
from pathlib import Path
import json
import subprocess
import sys

from credited_round_dataset import read
from credited_feedback_identity_probe import DATA as UID_DATA
from credited_late_history_controls import DATA
from v3_final_reserve import ROOT, sha, source_sha


def append_inventory(data, containers):
    records = []
    for previous, current in zip(containers, containers[1:]):
        a = data[previous["start"]+25:previous["end"]]
        b = data[current["start"]+25:current["end"]]
        counts = current["item_count"]-previous["item_count"]
        prefix = b.startswith(a)
        suffix = b[len(a):] if prefix else None
        single = prefix and counts == 1 and bool(suffix)
        records.append({"previous_start": previous["start"], "current_start": current["start"],
                        "previous_count": previous["item_count"], "current_count": current["item_count"],
                        "unchanged_item_prefix": prefix, "single_item_append": single,
                        "append_start": current["start"]+25+len(a) if single else None,
                        "append_end": current["end"] if single else None,
                        "kind_byte": suffix[0] if single else None,
                        "width": len(suffix) if single else None,
                        "raw_hex": suffix.hex() if single else None,
                        "event_role": None})
    return records


def main():
    guard = [sys.executable, str(ROOT/"research/verify_credit_hypothesis_checkpoint.py")]
    subprocess.run(guard, check=True)
    boxes_path = DATA/"container-probe.json"
    boxes = read(boxes_path)
    original = read(UID_DATA/"global-uid-inventory.json")
    controls = read(DATA/"result.json")
    sources = {(r["cohort"], r["map_id"], r["logical_round"]): r for r in controls["records"]}
    for row in original["records"]:
        sources["SAL", row["map_id"], row["round"]] = {"dump_path": str((UID_DATA/(row["replay_sha256"]+".dump")).relative_to(ROOT)).replace("\\", "/"), "dump_sha256": row["dump_sha256"]}
    results, inputs = [], {str(boxes_path.relative_to(ROOT)).replace("\\", "/"): sha(boxes_path)}
    for row in boxes["records"]:
        source = sources[row["cohort"], row["map_id"], row["round"]]
        dump = ROOT/source["dump_path"]
        if sha(dump) != source["dump_sha256"]:
            raise ValueError("Sealed buffer changed")
        records = append_inventory(dump.read_bytes(), sorted(row["containers"], key=lambda b: b["start"]))
        result = {"cohort": row["cohort"], "map_id": row["map_id"], "round": row["round"], "appends": records}
        results.append(result)
        inputs[str(dump.relative_to(ROOT)).replace("\\", "/")] = sha(dump)
        print(row["cohort"], row["map_id"], row["round"], "exact single appends", sum(r["single_item_append"] for r in records), flush=True)
    inventory = Counter((r["kind_byte"], r["width"]) for row in results for r in row["appends"] if r["single_item_append"])
    result = {"source_sha256": source_sha(Path(__file__)), "inputs": inputs, "records": results,
              "kind_widths": [{"kind": k, "width": w, "count": c} for (k,w),c in sorted(inventory.items())],
              "status": "exact_cumulative_single_item_boundaries_roles_unknown"}
    from credited_late_history_development import immutable_write
    immutable_write(DATA/"append-inventory.json", result)
    subprocess.run(guard, check=True)


if __name__ == "__main__":
    main()
