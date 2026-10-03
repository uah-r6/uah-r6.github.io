"""Consumed batched counter timelines, not a credited-victim association.

Use existing cached state/feedback only. Body raw3 is a DBNO candidate outside
independently reviewed cases. Byte ordering is not seconds or server causality.
"""
import hashlib
from pathlib import Path
import subprocess
import sys
import json

from credited_round_dataset import DATA, inventory, read
from objective_player_component_fields import owners_and_slots, bindings_at
from v3_final_reserve import ROOT, sha, source_sha


def body_observations(state):
    owners, slots = owners_and_slots(state)
    result = []
    for p in state["properties"]:
        if p["hash"] != "e788f6a5" or p["size"] != 4:
            continue
        route = bindings_at(owners, slots, p["offset"]).get(p["entity"])
        if route and (route["slot"], route["class_hash"]) == ("4154dcc4", "0c98c63f"):
            result.append({"offset": p["offset"], "player": route["player"], "raw_state": p["value"],
                           "route": route, "interpretation": "raw_body_observation_not_downer_identity"})
    return sorted(result, key=lambda r: r["offset"])


def main():
    guard = [sys.executable, str(ROOT/"research/verify_global_uid_checkpoint.py")]
    subprocess.run(guard, check=True)
    dataset_path = DATA/"dataset.json"
    dataset = read(dataset_path)
    batches = [(r, c) for r in dataset["player_rounds"] for c in r["counter_changes"] if c["delta"] > 1]
    # Exhaustive within the sealed consumed dataset, not selected from targets.
    if len(batches) != 3:
        raise ValueError("Recorded batched inventory changed")
    available = {(m["cohort"], m["map_id"]): m for m in inventory()}
    results, inputs = [], {}
    exe = ROOT/".local-tools/bin/state-component-probe.exe"
    for player_round, change in batches:
        map_ = available[player_round["cohort"], player_round["map_id"]]
        source = next(s for s in map_["sources"] if s["logical_round"] == player_round["logical_round"])
        if sha(source["path"]) != player_round["replay_sha256"]:
            raise ValueError("Batched physical source changed")
        key = hashlib.sha256(exe.read_bytes()+source["path"].read_bytes()).hexdigest()
        state_path = ROOT/"data/research/diagnostics/state-components"/(key+".json")
        state = read(state_path)
        inputs[str(state_path.relative_to(ROOT)).replace("\\", "/")] = sha(state_path)
        round_ = next(r for m in dataset["maps"] if m["cohort"] == player_round["cohort"] and m["map_id"] == player_round["map_id"]
                      for r in m["rounds"] if r["logical_round"] == player_round["logical_round"])
        body = body_observations(state)
        counter = [r for r in dataset["player_rounds"] if r["cohort"] == player_round["cohort"] and
                   r["map_id"] == player_round["map_id"] and r["logical_round"] == player_round["logical_round"]]
        timeline = [{"offset": p["offset"], "kind": "body_raw_state", **p} for p in body]
        timeline += [{"offset": c["offset"], "kind": "credited_counter_change", "player": r["username"], **c}
                     for r in counter for c in r["counter_changes"]]
        timeline += [{"offset": e["packet_offset"], "kind": "final_elimination_feedback", **e} for e in round_["events"]]
        if any(e["offset"] is None for e in timeline):
            raise ValueError("Batched study needs known physical order")
        timeline.sort(key=lambda r: r["offset"])
        first = min(e["packet_offset"] for e in round_["events"])
        before = [p for p in body if p["offset"] < first and p["raw_state"] == 3]
        nearest_context = [e for e in timeline if abs(e["offset"]-change["offset"]) <= 2000]
        record = {"cohort": player_round["cohort"], "map_id": player_round["map_id"],
                  "round": player_round["logical_round"], "build": player_round["build"],
                  "replay_sha256": player_round["replay_sha256"], "player": player_round["username"],
                  "batched_change": change, "timeline": timeline, "nearby_serialized_context_only": nearest_context,
                  "first_final_death_offset": first, "raw3_candidates_before_first_final_death": before,
                  "generic_victim_association": None, "individual_credited_times": None,
                  "limitation": "Co-occurrence/nearby serialization is not victim ownership. A +2 packet is a count batch, not two decoded kill events. Raw3 candidates require independent DBNO controls; no downer or trade clock inferred."}
        results.append(record)
        print(record["map_id"], record["round"], record["player"], "+2 context events", len(nearest_context),
              "pre-first-death raw3 candidates", len(before), flush=True)
    result = {"source_sha256": source_sha(Path(__file__)), "dataset_sha256": sha(dataset_path), "inputs": inputs,
              "status": "consumed_batched_counter_timing_not_event_owner_or_elapsed_time", "records": results}
    target = DATA/"counter-batch-audit.json"
    if target.exists() and read(target) != result:
        raise ValueError("Never replace batched counter evidence")
    if not target.exists():
        target.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    subprocess.run(guard, check=True)


if __name__ == "__main__":
    main()
