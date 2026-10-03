"""Inventory exact header-matching UID/icon/alliance references in raw data.

Pairs establish bounded adjacent references, NOT actor/target/damage semantics.
Do not call the first identity a downer, killer or finisher without event type.
"""
import json
from pathlib import Path
import subprocess
import sys

from credited_round_dataset import DATA as COUNT_DATA, read
from credited_feedback_identity_probe import DATA
from v3_final_reserve import ROOT, sha, source_sha


def reference_at(data, at, players):
    if at < 0 or at+20 > len(data):
        return None
    uid = int.from_bytes(data[at:at+8], "little")
    matches = [p for p in players if p.get("id") == uid and uid > 0]
    if len(matches) != 1:
        return None
    p = matches[0]
    icon = int.from_bytes(data[at+8:at+16], "little")
    alliance = int.from_bytes(data[at+16:at+20], "little")
    if icon != p.get("roleImage") or alliance != p.get("alliance"):
        return None
    return {"uid": uid, "username": p["username"], "role_image": icon,
            "alliance": alliance, "start": at, "end": at+20,
            "event_role": None}


def paired_at(data, at, players):
    first = reference_at(data, at, players)
    second = reference_at(data, at+20, players)
    if first is None or second is None:
        return None
    return {"first": first, "second": second, "start": at, "end": at+40,
            "record_type": None, "event_time": None, "credited_killer": None, "downer": None}


def main():
    guard = [sys.executable, str(ROOT/"research/verify_credited_semantics_checkpoint.py")]
    subprocess.run(guard, check=True)
    inventory_path = DATA/"global-uid-inventory.json"
    inventory = read(inventory_path)
    dataset_path = COUNT_DATA/"dataset.json"
    dataset = read(dataset_path)
    results, inputs = [], {}
    for row in inventory["records"]:
        cache_paths = []
        for name in dataset["inputs"]:
            p = ROOT/name
            observation = read(p)
            if observation["replay_sha256"] == row["replay_sha256"]:
                cache_paths.append((p, observation))
        if len(cache_paths) != 1:
            raise ValueError("Exact canonical header required")
        cache, observation = cache_paths[0]
        inputs[str(cache.relative_to(ROOT)).replace("\\", "/")] = sha(cache)
        players = observation["header"]["players"]
        dump = DATA/(row["replay_sha256"]+".dump")
        if sha(dump) != row["dump_sha256"]:
            raise ValueError("Sealed buffer changed")
        data = dump.read_bytes()
        offsets = sorted({r["relative_offset"] for r in row["matches"]})
        references, pairs = [], []
        for at in offsets:
            ref = reference_at(data, at, players)
            if ref:
                references.append(ref)
            pair = paired_at(data, at, players)
            if pair:
                pairs.append({**pair, "raw_before_32": data[max(0, at-32):at].hex(),
                              "raw_pair": data[at:at+40].hex(), "raw_after_16": data[at+40:at+56].hex()})
        action = observation["header"]["actionPhaseStartOffset"]
        last_death = max(e["offset"] for e in observation["credit"]["finishes"])
        results.append({"map_id": row["map_id"], "round": row["round"], "replay_sha256": row["replay_sha256"],
                        "references": references, "pairs": pairs, "action_start": action, "last_finish_offset": last_death,
                        "pairs_before_action": sum(p["end"] < action for p in pairs),
                        "pairs_after_last_elimination": sum(p["start"] > last_death for p in pairs),
                        "scope": "Exact header UID/icon/alliance triples and contiguous pairs. First/second are byte positions, not event roles. Outer framing/type, server cause, timestamps and indirect relationships unknown."})
        print(row["map_id"], len(references), "exact references", len(pairs), "adjacent pairs; after last death",
              results[-1]["pairs_after_last_elimination"], flush=True)
    result = {"source_sha256": source_sha(Path(__file__)), "inventory_sha256": sha(inventory_path),
              "dataset_sha256": sha(dataset_path), "inputs": inputs, "records": results,
              "status": "consumed_explicit_identity_reference_pairs_roles_unresolved"}
    target = DATA/"uid-pair-inventory.json"
    if target.exists() and read(target) != result:
        raise ValueError("Never overwrite changed identity pair inventory")
    if not target.exists():
        target.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    subprocess.run(guard, check=True)


if __name__ == "__main__":
    main()
