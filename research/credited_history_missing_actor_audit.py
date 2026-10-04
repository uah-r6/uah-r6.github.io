"""Read-only missing history actor audit; never fill credit from total deltas."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from credited_counter_batch_audit import body_observations
from credited_round_dataset import read, cached_index, cached_observation
from credited_late_history_development import immutable_write
from credited_history_framing_v3 import DATA as HISTORY_DATA
from v3_final_reserve import ROOT, sha, source_sha

REPLAY = "d3b348a290cd69714434bd10f62fe25df05f533934b080d75842461541c0c53a"
DATA = ROOT/"data/research/credited-history-missing-actor"


def header_identity(header):
    fields = ("id","profileID","username","teamIndex")
    return sorted(tuple(p.get(k) for k in fields) for p in header["players"])


def audit(history, observation, state):
    if not history["cumulative"]["complete"] or not history["feed_parity"]["exact_original_filtered_feed_identity_weapon_headshot_order"]:
        raise ValueError("Cannot claim an absent actor from incomplete/unmatched history")
    if header_identity(observation["header"]) != header_identity(state["header"]):
        raise ValueError("Cached state player identity differs")
    players = observation["header"]["players"]
    by_name = {p["username"]:p for p in players}
    if len(by_name) != len(players) or len({p["id"] for p in players}) != len(players):
        raise ValueError("Ambiguous player identity")
    body = [b for b in body_observations(state) if b["offset"] > observation["header"]["actionPhaseStartOffset"]]
    down_targets = {i["second"]["uid"] for i in history["cumulative"]["items"] if i["kind_byte"] == 5}
    missing = [b for b in body if b["raw_state"] == 3 and by_name[b["player"]]["id"] not in down_targets]
    return {"post_action_body":body,"kind5_target_uids":sorted(down_targets),
            "raw3_observations_without_kind5_target":missing,
            "unresolved_credited_victim_uid":None,"unresolved_downer_uid":None,
            "scope":"Absence within fully framed typed history, not all replay/encoded/gadget sources. Raw3 alone is not a generic causal/damage proof."}


def main():
    guard = [sys.executable,str(ROOT/"research/verify_history_framing_checkpoint.py")]
    subprocess.run(guard,check=True)
    old_path = ROOT/"data/research/credited-late-history-development/records"/(REPLAY+".json")
    old = read(old_path)
    history_path = HISTORY_DATA/"records"/(REPLAY+".json")
    history = read(history_path)
    rec = ROOT/old["path"]
    if sha(rec) != REPLAY:
        raise ValueError("Exact fixed mismatch replay required")
    cache, observation = cached_observation(cached_index(),REPLAY)
    exe = ROOT/".local-tools/bin/state-component-probe.exe"
    key = hashlib.sha256(exe.read_bytes()+rec.read_bytes()).hexdigest()
    state_path = ROOT/"data/research/diagnostics/state-components"/(key+".json")
    state = read(state_path) # cached only; no observer/parser execution
    reservation = {"base_head":"9b491ac","replay_sha256":REPLAY,
                   "source_hashes":{str(p.relative_to(ROOT)).replace("\\","/"):source_sha(p) for p in (
                       Path(__file__),ROOT/"research/credited_counter_batch_audit.py",ROOT/"research/objective_player_component_fields.py")},
                   "inputs":{str(p.relative_to(ROOT)).replace("\\","/"):sha(p) for p in (old_path,history_path,cache,state_path)},
                   "hypothesis":"Inventory body raw3 targets lacking any typed kind5 target. No credited identity from total difference."}
    immutable_write(DATA/"reservation.json",reservation)
    finding = audit(history,observation,state)
    targeted = {"Nina.SCARZ","OSAdinho.SCARZ","Kawa.KN","Aokayu.KN"}
    counters = [p for p in observation["credit"]["players"] if p["username"] in targeted]
    timeline = [{"offset":b["offset"],"kind":"body_raw_state",**b} for b in finding["post_action_body"] if b["player"] in targeted]
    timeline += [{"offset":s["offset"],"kind":"counter_observation","username":p["username"],"value":s["value"],
                  "owner":s["owner"],"component":s["component"],"victim_uid":None} for p in counters for s in p["samples"]]
    timeline += [{"offset":e["offset"],"kind":"original_finisher_elimination","feedback":e["feedback"],"credited_uid":None}
                 for e in observation["credit"]["finishes"]]
    result = {"event":"APAC","map_id":8161,"physical_round":14,"replay_sha256":REPLAY,
              "header_players":[p for p in observation["header"]["players"] if p["username"] in targeted],
              "counter_players":counters,"frozen_mismatches":[c for c in old["comparisons"] if not c["match"]],
              "history_items":history["cumulative"]["items"],"timeline":sorted(timeline,key=lambda e:e["offset"]),
              "audit":finding,"source_sha256":source_sha(Path(__file__)),
              "interpretation":"Aokayu has raw3 but no kind5 target in complete history; Kawa2->4. Actor/victim credit remains unresolved. No proximity join or compensating kill assignment."}
    immutable_write(DATA/"result.json",result)
    print('Missing typed kind5 body targets',[(b['player'],b['offset']) for b in finding['raw3_observations_without_kind5_target']],flush=True)
    subprocess.run(guard,check=True)


if __name__ == "__main__":
    main()
