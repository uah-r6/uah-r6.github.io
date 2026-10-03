"""Consumed late event-history layout probe, no runtime event migration.

Candidate type1 has independent same-round feed identity/weapon/headshot
controls. Type5/7 roles and scalar time units remain hypotheses. Physical late
copies do not supply event occurrence time, nor independent sample replication.
"""
from collections import Counter
import json
from pathlib import Path
import subprocess
import sys

from credited_feedback_identity_probe import DATA
from credited_round_dataset import DATA as COUNT_DATA, read
from v3_final_reserve import ROOT, sha, source_sha


def candidate_at(data, pair):
    at, end = pair["start"], pair["end"]
    possibilities = []
    # Explicit bounded byte layout only, not a search for the nearest actor.
    if at >= 21 and end < len(data) and data[at-21] == 1 and data[end] in (0, 1):
        possibilities.append({"kind_byte": 1, "start": at-21, "end": end+1,
                              "opaque_scalar": int.from_bytes(data[at-20:at-16], "little"),
                              "weapon_id": int.from_bytes(data[at-16:at-8], "little"),
                              "entity_reference": int.from_bytes(data[at-8:at], "little"),
                              "headshot": bool(data[end])})
    if at >= 13 and data[at-13] in (5, 7):
        possibilities.append({"kind_byte": data[at-13], "start": at-13, "end": end,
                              "opaque_scalar": int.from_bytes(data[at-12:at-8], "little"),
                              "entity_reference": int.from_bytes(data[at-8:at], "little"),
                              "weapon_id": None, "headshot": None})
    if len(possibilities) != 1:
        return None
    p = possibilities[0]
    if not p["entity_reference"] or not p["opaque_scalar"]:
        return None
    return {**p, "first": pair["first"], "second": pair["second"],
            "raw_hex": data[p["start"]:p["end"]].hex(), "event_time": None,
            "credited_killer": None, "downer": None}


def compare_finishes(candidates, finishes):
    unique = {}
    for c in candidates:
        if c["kind_byte"] == 1:
            unique.setdefault(c["raw_hex"], c)
    observed = sorted(unique.values(), key=lambda c: c["opaque_scalar"])
    expected = sorted(finishes, key=lambda e: e["offset"])
    if any(e["feedback"]["type"]["name"] != "Kill" for e in expected):
        raise ValueError("This consumed comparison requires named Kill controls")
    a = [(c["first"]["username"], c["second"]["username"], c["weapon_id"], c["headshot"]) for c in observed]
    b = [(e["feedback"]["username"], e["feedback"]["target"], e["feedback"]["weaponID"], e["feedback"].get("headshot", False)) for e in expected]
    return {"same_round_feed_events": len(expected), "unique_type1_candidates": len(observed),
            "exact_identity_weapon_headshot_order_match": a == b,
            "duplicate_type1_physical_copies": sum(c["kind_byte"] == 1 for c in candidates)-len(observed),
            "feed_controls": b, "candidate_projection": a}


def main():
    guard = [sys.executable, str(ROOT/"research/verify_credited_semantics_checkpoint.py")]
    subprocess.run(guard, check=True)
    pairs_path = DATA/"uid-pair-inventory.json"
    pair_inventory = read(pairs_path)
    dataset = read(COUNT_DATA/"dataset.json")
    results = []
    for row in pair_inventory["records"]:
        old = next(r for r in read(DATA/"global-uid-inventory.json")["records"] if r["map_id"] == row["map_id"])
        dump = DATA/(row["replay_sha256"]+".dump")
        if sha(dump) != old["dump_sha256"]:
            raise ValueError("Sealed buffer changed")
        data = dump.read_bytes()
        candidates = [c for pair in row["pairs"] if (c := candidate_at(data, pair))]
        # All ordinary events, not only the known split, are independent controls.
        canonical = next(m for m in dataset["maps"] if m["cohort"] == "SAL" and m["map_id"] == row["map_id"])
        events = next(r for r in canonical["rounds"] if r["logical_round"] == row["round"])["events"]
        finishes = [{"offset": e["packet_offset"], "feedback": e["raw_feedback"]} for e in events]
        comparison = compare_finishes(candidates, finishes)
        unique = {}
        for c in candidates:
            unique.setdefault(c["raw_hex"], []).append(c)
        summarized = [{"candidate": values[0], "physical_copies": [c["start"] for c in values]}
                      for values in unique.values()]
        summarized.sort(key=lambda c: c["candidate"]["opaque_scalar"])
        results.append({"map_id": row["map_id"], "round": row["round"], "replay_sha256": row["replay_sha256"],
                        "candidates": candidates, "unique_payloads": summarized, "comparison": comparison,
                        "kind_counts": dict(Counter(c["kind_byte"] for c in candidates)),
                        "outer_record_type": None, "scalar_time_units": None,
                        "limits": "Type1's observed fields match these same-build finisher controls. Repeated late physical copies are not new events or occurrence clocks. Type5/7 direction/DBNO/revive hypotheses need independently constrained controls; no downer or credit inferred here."})
        print(row["map_id"], comparison, flush=True)
    result = {"status": "consumed_late_history_layout_partial_semantics_not_runtime", "records": results,
              "source_sha256": source_sha(Path(__file__)), "pair_inventory_sha256": sha(pairs_path)}
    target = DATA/"late-event-layout-probe.json"
    if target.exists() and read(target) != result:
        raise ValueError("Never overwrite late layout evidence")
    if not target.exists():
        target.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    subprocess.run(guard, check=True)


if __name__ == "__main__":
    main()
