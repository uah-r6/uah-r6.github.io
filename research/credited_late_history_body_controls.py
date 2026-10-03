"""Independent target-body intervals for candidate5/7 late-history records.

Use already matched finisher events as ordering bounds, never packet proximity
or scalar-to-second conversion. These controls cannot prove the first UID's
causal role or supply a credited-killer join.
"""
import hashlib
from pathlib import Path
import subprocess
import sys
import json

from credited_counter_batch_audit import body_observations
from credited_round_dataset import inventory, read
from credited_feedback_identity_probe import DATA as UID_DATA
from credited_late_history_controls import DATA
from v3_final_reserve import ROOT, sha, source_sha


def interval(candidate, type1, finishes, action_start):
    order = sorted(type1, key=lambda c: c["opaque_scalar"])
    feed = sorted(finishes, key=lambda f: f["offset"])
    if len(order) != len(feed):
        raise ValueError("Complete independent anchors required")
    anchors = []
    for c, f in zip(order, feed):
        event = f["feedback"]
        if (c["first"]["username"], c["second"]["username"], c["weapon_id"], c["headshot"]) != (
                event["username"], event["target"], event["weaponID"], event.get("headshot", False)):
            raise ValueError("Anchor identity/weapon mismatch")
        anchors.append((c["opaque_scalar"], f["offset"]))
    scalar = candidate["opaque_scalar"]
    if any(s == scalar for s, _ in anchors):
        return None
    lower = max((o for s, o in anchors if s < scalar), default=action_start)
    upper = min((o for s, o in anchors if s > scalar), default=None)
    return {"lower_feed_offset": lower, "upper_feed_offset": upper}


def main():
    guard = [sys.executable, str(ROOT/"research/verify_credited_semantics_checkpoint.py")]
    subprocess.run(guard, check=True)
    old_path, controls_path = UID_DATA/"late-event-layout-probe.json", DATA/"result.json"
    old, controls = read(old_path), read(controls_path)
    available = {(m["cohort"], m["map_id"]): m for m in inventory()}
    rows = []
    for row in old["records"]:
        rows.append({"cohort": "SAL", "map_id": row["map_id"], "number": row["round"], "unique": row["unique_payloads"]})
    for row in controls["records"]:
        rows.append({"cohort": row["cohort"], "map_id": row["map_id"], "number": row["logical_round"], "unique": row["unique_payloads"]})
    results, inputs = [], {str(p.relative_to(ROOT)).replace("\\", "/"): sha(p) for p in (old_path, controls_path)}
    # Use the already-created canonical cached observation index.
    from credited_round_dataset import cached_index, cached_observation
    index = cached_index()
    for row in rows:
        source = next(s for s in available[row["cohort"], row["map_id"]]["sources"] if s["logical_round"] == row["number"])
        rec = source["path"]
        if sha(rec) != source["replay_sha256"]:
            raise ValueError("Consumed control source changed")
        _, observation = cached_observation(index, source["replay_sha256"])
        key = hashlib.sha256((ROOT/".local-tools/bin/state-component-probe.exe").read_bytes()+rec.read_bytes()).hexdigest()
        state_path = ROOT/"data/research/diagnostics/state-components"/(key+".json")
        state = read(state_path)
        inputs[str(state_path.relative_to(ROOT)).replace("\\", "/")] = sha(state_path)
        body = body_observations(state)
        candidates = [v["candidate"] for v in row["unique"]]
        controls_for_round = []
        for c in candidates:
            if c["kind_byte"] not in (5, 7):
                continue
            bounds = interval(c, [a for a in candidates if a["kind_byte"] == 1],
                              observation["credit"]["finishes"], observation["header"]["actionPhaseStartOffset"])
            observed = [b for b in body if b["player"] == c["second"]["username"] and bounds and
                        b["offset"] > bounds["lower_feed_offset"] and
                        (bounds["upper_feed_offset"] is None or b["offset"] < bounds["upper_feed_offset"])]
            expected = {3} if c["kind_byte"] == 5 else {0, 2}
            controls_for_round.append({"candidate": c, "independent_feed_bounds": bounds,
                                       "target_body_observations": observed,
                                       "matching_raw_state_observations": [b for b in observed if b["raw_state"] in expected],
                                       "first_uid_causal_role": None, "event_elapsed_time": None})
        results.append({"cohort": row["cohort"], "map_id": row["map_id"], "round": row["number"], "controls": controls_for_round})
        print(row["cohort"], row["map_id"], row["number"], "candidate body controls",
              [(c["candidate"]["kind_byte"], c["candidate"]["second"]["username"], len(c["matching_raw_state_observations"])) for c in controls_for_round], flush=True)
    result = {"source_sha256": source_sha(Path(__file__)), "status": "consumed_target_body_corroboration_not_downer_or_clock_proof",
              "inputs": inputs, "records": results,
              "limits": "Type5 target raw3/type7 target active are independently routed interval observations, not exact event-time equality or universal type semantics. First UID downer/reviver role and outer list framing need independent controls. No count projection, elapsed seconds or runtime migration."}
    target = DATA/"body-controls.json"
    if target.exists() and read(target) != result:
        raise ValueError("Never replace body control evidence")
    if not target.exists():
        target.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    subprocess.run(guard, check=True)


if __name__ == "__main__":
    main()
