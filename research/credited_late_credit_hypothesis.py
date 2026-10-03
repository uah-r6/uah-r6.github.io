"""Consumed development credit hypothesis, not a production credited join.

Kind5 source direction and kind7 recovery semantics are hypothesized here,
explicitly scoped to six already-consumed sources. Independent round counter
comparisons cannot prove every individual causal role or generalize the model.
"""
from collections import Counter
from pathlib import Path
import subprocess
import sys
import json

from credited_feedback_identity_probe import DATA as UID_DATA
from credited_late_history_controls import DATA
from credited_round_dataset import read, cached_index, cached_observation
from v3_final_reserve import ROOT, sha, source_sha


def reconstruct(candidates, teams):
    unique = {}
    for c in candidates:
        unique.setdefault(c["raw_hex"], c)
    ordered = sorted(unique.values(), key=lambda c: c["opaque_scalar"])
    if len({c["opaque_scalar"] for c in ordered}) != len(ordered):
        raise ValueError("Tied scalar event order is unresolved")
    down, counts, ledger = {}, Counter(), []
    eliminated = set()
    for c in ordered:
        first, victim = c["first"]["uid"], c["second"]["uid"]
        if first not in teams or victim not in teams or c["kind_byte"] not in (1,5,7):
            raise ValueError("Unsupported candidate identity/type")
        if victim in eliminated:
            raise ValueError("Candidate targets an already eliminated player")
        if c["kind_byte"] == 5:
            # Self/friendly down observations do not manufacture an opponent kill.
            down[victim] = c if teams[first] != teams[victim] else None
        elif c["kind_byte"] == 7:
            down.pop(victim, None)
        else:
            if first == victim or teams[first] == teams[victim]:
                raise ValueError("Suicide/teamkill credit semantics not established by this cohort")
            prior = down.pop(victim, None)
            owner = prior["first"]["uid"] if prior else first
            counts[owner] += 1
            eliminated.add(victim)
            ledger.append({"victim_uid": victim, "finisher_uid": first,
                           "hypothesized_credited_uid": owner,
                           "prior_candidate5_scalar": prior["opaque_scalar"] if prior else None,
                           "final_elimination_scalar": c["opaque_scalar"], "elapsed_seconds": None,
                           "hypothesis_source": "last_opponent_kind5_cleared_on_kind7_v1"})
    return {"counts": dict(counts), "ledger": ledger, "unresolved_down_candidates": sorted(down),
            "production_authoritative": False}


def main():
    guard = [sys.executable, str(ROOT/"research/verify_late_history_checkpoint.py")]
    subprocess.run(guard, check=True)
    old_path, control_path = UID_DATA/"late-event-layout-probe.json", DATA/"result.json"
    old, controls = read(old_path), read(control_path)
    sources = [{"cohort": "SAL", "map_id": r["map_id"], "round": r["round"],
                "replay_sha256": r["replay_sha256"], "candidates": r["candidates"]} for r in old["records"]]
    sources += [{"cohort": r["cohort"], "map_id": r["map_id"], "round": r["logical_round"],
                 "replay_sha256": r["replay_sha256"], "candidates": [c["candidate"] for c in r["unique_payloads"]]} for r in controls["records"]]
    index = cached_index()
    results, inputs = [], {str(p.relative_to(ROOT)).replace("\\", "/"): sha(p) for p in (old_path, control_path)}
    for row in sources:
        cache, observation = cached_observation(index, row["replay_sha256"])
        if not observation["credit"]["complete"]:
            raise ValueError("Independent complete counter controls required")
        players = observation["credit"]["players"]
        teams = {p["uid"]: p["team"] for p in players}
        proposed = reconstruct(row["candidates"], teams)
        compared = [{"uid": p["uid"], "username": p["username"], "counter_kills": p["kills"],
                     "hypothesis_kills": proposed["counts"].get(p["uid"],0),
                     "match": proposed["counts"].get(p["uid"],0) == p["kills"]} for p in players]
        results.append({k: row[k] for k in ("cohort", "map_id", "round", "replay_sha256")} |
                       {"reconstructed": proposed, "comparisons": compared})
        inputs[str(cache.relative_to(ROOT)).replace("\\", "/")] = sha(cache)
        print(row["cohort"], row["map_id"], row["round"], "round counter agreements", sum(c["match"] for c in compared), "/", len(compared), flush=True)
    result = {"status": "consumed_development_credit_hypothesis_not_promoted", "source_sha256": source_sha(Path(__file__)),
              "inputs": inputs, "records": results,
              "agreements": sum(c["match"] for r in results for c in r["comparisons"]),
              "mismatches": sum(not c["match"] for r in results for c in r["comparisons"]),
              "limits": "Six consumed rounds; independently validated counters support round counts only. Candidate event ownership/direction, recovery/reset/TK/self/environment semantics, complete history framing and scalar time units require broader controls. No final regrade, production normalization/stat/Ratings/SQL/public change."}
    target = DATA/"credit-hypothesis.json"
    if target.exists() and read(target) != result:
        raise ValueError("Never replace consumed hypothesis result")
    if not target.exists():
        target.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    subprocess.run(guard,check=True)


if __name__ == "__main__":
    main()
