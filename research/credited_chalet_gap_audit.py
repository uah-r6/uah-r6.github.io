"""Diagnose the four unsupported Chalet sources without admitting them.

Inspect existing framed properties for the nine observed participants. This
does not relax the ten-player production/count validator or fabricate a tenth.
"""
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from credited_round_dataset import DATA, archive_sources, cached_index, cached_observation, read
from v3_final_reserve import ROOT, sha, source_sha


def observed_routes(evidence):
    uid_owners = defaultdict(set)
    for p in evidence["properties"]:
        if p["tag"] == 0xc845d4ee and p["size"] == 8:
            uid_owners[p["bits"]].add(p["entity"])
    result = []
    declarations = sorted(evidence["declarations"], key=lambda d: d["offset"])
    for player in evidence["header"]["players"]:
        owners = uid_owners[player["id"]]
        samples = []
        reason = None
        if len(owners) != 1:
            reason = "nonunique_direct_uid_owner"
        else:
            owner = next(iter(owners))
            for p in sorted(evidence["properties"], key=lambda f: f["offset"]):
                if p["tag"] != 0x9db1d21c or p["size"] != 4:
                    continue
                active = {}
                for d in declarations:
                    if d["offset"] > p["offset"]:
                        break
                    active[d["owner"], d["slot"]] = d
                routes = [d for d in active.values() if d["component"] == p["entity"] and d["class"] != 0]
                own = [d for d in routes if d["owner"] == owner and d["slot"] == 0x389b21eb and d["class"] == 0xa191a518]
                if not own:
                    continue
                if len(own) != 1 or len(routes) != 1:
                    reason = "shared_counter_component"
                    continue
                samples.append({"offset": p["offset"], "value": p["bits"], "owner": owner,
                                "component": p["entity"], "declaration_offset": own[0]["offset"]})
        if not samples:
            reason = reason or "missing_direct_counter"
        elif (any(b["value"] < a["value"] or (a["owner"], a["component"]) != (b["owner"], b["component"])
                  for a, b in zip(samples, samples[1:]))):
            reason = "counter_reset_or_replacement_within_round"
        initial = samples[0]["value"] if samples else None
        terminal = samples[-1]["value"] if samples else None
        result.append({"username": player["username"], "uid": player["id"], "profile_id": player["profileID"],
                       "samples": samples, "observed_initial": initial, "observed_terminal": terminal,
                       "observed_delta": terminal-initial if reason is None else None,
                       "diagnostic_route_reason": reason, "production_admission": False})
    return result


def main():
    guard = [sys.executable, str(ROOT/"research/verify_global_uid_checkpoint.py")]
    subprocess.run(guard, check=True)
    sources = sorted(archive_sources("b595ffaaec57", "fall-2026"), key=lambda s: s["logical_round"])
    index = cached_index()
    _, prior = cached_observation(index, sources[7]["replay_sha256"])
    prior_players = {p["profileID"]: p for p in prior["header"]["players"]}
    results, inputs = [], {}
    for source in sources[8:]:
        path, observed = cached_observation(index, source["replay_sha256"])
        rec = source["path"]
        if sha(rec) != source["replay_sha256"]:
            raise ValueError("Archived physical source changed")
        evidence_path = path.with_name(path.stem + ".evidence.json")
        evidence = read(evidence_path)
        state_key = hashlib.sha256((ROOT/".local-tools/bin/state-component-probe.exe").read_bytes()+rec.read_bytes()).hexdigest()
        state_path = ROOT/"data/research/diagnostics/state-components"/(state_key+".json")
        state = read(state_path)  # Refuse absent cache: no parser job here.
        players = observed["header"]["players"]
        profile_ids = {p["profileID"] for p in players}
        missing = [p for key, p in prior_players.items() if key not in profile_ids]
        properties = [p for p in state["properties"] if p["kind"] == "numeric_uid"]
        uid_values = {p["value"] for p in properties}
        expected_uids = {p["id"] for p in players}
        routes = observed_routes(evidence)
        # Do not turn this diagnostic into synthetic validator output.
        row = {"logical_round": source["logical_round"], "physical_round": source["physical_round"],
               "segment": source["segment"], "replay_sha256": source["replay_sha256"],
               "build": observed["header"]["codeVersion"], "header_participants": len(players),
               "physical_teams": dict(Counter(p["teamIndex"] for p in players)),
               "missing_prior_profile_players": [{k: p[k] for k in ("username", "id", "profileID")} for p in missing],
               "typed_uid_values": sorted(uid_values), "unbound_typed_uid_values": sorted(uid_values-expected_uids),
               "missing_prior_uid_present_in_typed_properties": any(p["id"] in uid_values for p in missing),
               "scoreboard_declarations": sum(d["slot_hash"] == "eb219b38" for d in state["declarations"]),
               "diagnostic_counter_routes": routes,
               "validator_reason": observed["credit"]["reason"],
               "classification": "participant_identity_inventory_gap_after_rehost",
               "limitations": "Nine header participants and nine direct UID owners. Cannot distinguish actual 5v4 absence from an unrecorded participant solely with these views. No tenth identity or zero kills invented; strict whole-map refusal retained."}
        results.append(row)
        for p in (path, evidence_path, state_path):
            inputs[str(p.relative_to(ROOT)).replace("\\", "/")] = sha(p)
        print("Chalet", row["logical_round"], "missing", [p["username"] for p in missing],
              "counter routes", len([p for p in routes if p["diagnostic_route_reason"] is None]), flush=True)
    result = {"source_sha256": source_sha(Path(__file__)), "status": "readonly_gap_diagnosis_not_admitted", "rounds": results, "inputs": inputs}
    target = DATA/"chalet-gap-audit.json"
    if target.exists() and read(target) != result:
        raise ValueError("Never replace gap checkpoint")
    if not target.exists():
        target.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    subprocess.run(guard, check=True)


if __name__ == "__main__":
    main()
