"""Cached Go-history/body lifecycle controls on the fixed74source cohort.

No new parsing, target lookup or evaluation. Serialized bounds are independent
feed anchors, not elapsed clocks or a nearest-counter credited-victim join.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from credited_counter_batch_audit import body_observations
from credited_history_go_controls import DATA as GO_DATA
from credited_history_framing_v3 import DATA as TYPED_DATA,feed_parity
from credited_history_missing_actor_audit import header_identity
from credited_late_history_development import immutable_write
from credited_round_dataset import read,cached_index,cached_observation
from objective_player_component_fields import owners_and_slots,bindings_at
from v3_final_reserve import ROOT,sha,source_sha

DATA = ROOT/"data/research/credited-history-lifecycle-controls"
STATE_EXE = ROOT/".local-tools/bin/state-component-probe.exe"


def independent_bounds(items,finishes,index,action_start):
    final_indices = [i for i,c in enumerate(items) if c["kind_byte"] in (1,2,3)]
    if len(final_indices) != len(finishes):
        raise ValueError("Complete independent elimination anchors required")
    anchors = list(zip(final_indices,finishes))
    before = [(i,e["offset"]) for i,e in anchors if i<index]
    after = [(i,e["offset"]) for i,e in anchors if i>index]
    lower = before[-1][1] if before else action_start
    upper = after[0][1] if after else None
    if lower <= 0 or upper == 0 or (upper is not None and upper <= lower):
        return {"resolved":False,"reason":"legacy_zero_or_nonmonotonic_anchor","elapsed_seconds":None}
    return {"resolved":True,"lower_feed_offset":lower,"upper_feed_offset":upper,"elapsed_seconds":None}


def lifecycle(history,observation,state):
    if not history.get("complete") or history.get("production_authoritative") is not False:
        raise ValueError("Unpromoted complete Go structural evidence required")
    header = observation["header"]
    if header_identity(header) != header_identity(state["header"]):
        raise ValueError("State/header numeric UID-profile-name-team identity differs")
    action = header["actionPhaseStartOffset"]
    if action <= 0 or action != state["header"]["actionPhaseStartOffset"]:
        raise ValueError("Independent action-start offset differs")
    parity = feed_parity(history["items"],observation["credit"]["finishes"])
    if not parity["exact_original_filtered_feed_identity_weapon_headshot_order"]:
        raise ValueError("Independent final-elimination field/order parity differs")
    names = {p["username"]:p for p in header["players"]}
    owners,slots = owners_and_slots(state)
    if set(owners.values()) != set(names):
        raise ValueError("Independent typed UID owner inventory incomplete")
    routes = bindings_at(owners,slots,action)
    body_names = {r["player"] for r in routes.values() if (r["slot"],r["class_hash"]) == ("4154dcc4","0c98c63f")}
    if body_names != set(names):
        raise ValueError("Independent action-start body routes incomplete")
    body = [b for b in body_observations(state) if b["offset"]>action]
    controls = []
    down_uids = set()
    for i,c in enumerate(history["items"]):
        if c["kind_byte"] not in (5,7):
            continue
        bounds = independent_bounds(history["items"],observation["credit"]["finishes"],i,action)
        raw = [b for b in body if b["player"] == c["second"]["username"] and bounds["resolved"] and
               b["offset"]>bounds["lower_feed_offset"] and
               (bounds["upper_feed_offset"] is None or b["offset"]<bounds["upper_feed_offset"])]
        expected = {3} if c["kind_byte"] == 5 else {0,2}
        matched = [b for b in raw if b["raw_state"] in expected]
        relation = "self" if c["first"]["uid"] == c["second"]["uid"] else (
            "friendly" if c["first"]["team"] == c["second"]["team"] else "opposing")
        controls.append({"candidate":c,"identity_relation":relation,"independent_bounds":bounds,
                         "target_body_observations":raw,"matching_raw_state_observations":matched,
                         "status":"matching_target_body_interval" if matched else (
                             "unresolved_anchor" if not bounds["resolved"] else "no_matching_raw_state_in_interval"),
                         "first_uid_causal_role":None,"elapsed_seconds":None})
        if c["kind_byte"] == 5:
            down_uids.add(c["second"]["uid"])
    unrepresented = [{**b,"header_identity":names[b["player"]]} for b in body if b["raw_state"] == 3 and names[b["player"]]["id"] not in down_uids]
    return {"controls":controls,"post_action_body":body,"raw3_without_any_kind5_target":unrepresented,
            "original_counter_complete":observation["credit"]["complete"],
            "interpretation":"Target-state interval corroboration and typed-list absence only; no causal actor, generic enum meaning, credited-victim join or elapsed clock"}


def main():
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument("--limit",type=int,default=8)
    args = args.parse_args()
    guard = [sys.executable,str(ROOT/"research/verify_history_go_interface_checkpoint.py")]
    subprocess.run(guard,check=True)
    selection = read(GO_DATA/"sample-74.json")["records"]
    if not 1 <= args.limit <= len(selection):
        raise ValueError("Limit outside fixed consumed cohort")
    reservation = {"base_head":"ccfc1bf","selection":selection,"state_observer_sha256":sha(STATE_EXE),
                   "source_hashes":{str(p.relative_to(ROOT)).replace("\\","/"):source_sha(p) for p in (
                       Path(__file__),ROOT/"research/credited_counter_batch_audit.py",ROOT/"research/objective_player_component_fields.py",
                       ROOT/"research/credited_history_missing_actor_audit.py",ROOT/"research/credited_history_framing_v3.py")},
                   "hypothesis":"Go list kind5 target has raw3, kind7 target has active raw0/2 within unchanged feed anchors; missing list actors stay unresolved"}
    immutable_write(DATA/"reservation.json",reservation)
    index,records = cached_index(),[]
    original_selection = read(ROOT/"data/research/credited-native-boundary-controls/selection.json")["selection"]
    from credited_round_dataset import inventory
    sources = {s["replay_sha256"]:s["path"] for m in inventory() for s in m["sources"]}
    sources.update({s["replay_sha256"]:ROOT/s["path"] for s in original_selection})
    for source in selection[:args.limit]:
        name = source["replay_sha256"]
        target = DATA/"records"/(name+".json")
        if target.exists():
            result = read(target)
            for n,h in result["inputs"].items():
                if sha(ROOT/n) != h:
                    raise ValueError("Cached lifecycle input changed: "+n)
        else:
            rec = sources[name]
            if sha(rec) != name:
                raise ValueError("Fixed replay changed")
            state_key = hashlib.sha256(STATE_EXE.read_bytes()+rec.read_bytes()).hexdigest()
            state_path = ROOT/"data/research/diagnostics/state-components"/(state_key+".json")
            go_path = GO_DATA/"raw"/(name+".json")
            cache,observation = cached_observation(index,name)
            paths = [rec,go_path,cache]
            try:
                state = read(state_path) # absence refuses, never runs observer
                paths.append(state_path)
                finding = lifecycle(read(go_path),observation,state)
                status = "body_view_audited"
            except (ValueError,FileNotFoundError,TypeError,KeyError) as exc:
                finding,status = {"quality_refusal":str(exc)},"quality_refused"
            result = {k:source[k] for k in ("event","map_id","round","replay_sha256")}
            result.update(status=status,finding=finding,inputs={str(p.relative_to(ROOT)).replace("\\","/"):sha(p) for p in paths})
            immutable_write(target,result)
        records.append(result)
        f=result["finding"]
        print(source["event"],source["map_id"],source["round"],result["status"],"controls",len(f.get("controls",[])),
              "raw3without-kind5",len(f.get("raw3_without_any_kind5_target",[])),f.get("quality_refusal",""),flush=True)
    controls = [c for r in records for c in r["finding"].get("controls",[])]
    result = {"records":records,"status_counts":dict(Counter(r["status"] for r in records)),
              "target_interval_status_counts":dict(Counter(c["status"] for c in controls)),
              "candidate_relation_counts":dict(Counter(f'{c["candidate"]["kind_byte"]}:{c["identity_relation"]}' for c in controls)),
              "unrepresented_raw3":[{k:r[k] for k in ("event","map_id","round","replay_sha256")} |
                                    {"observation":b} for r in records for b in r["finding"].get("raw3_without_any_kind5_target",[])],
              "scope":"Fixed consumed Go/body views, no reparsing or actor/clock/stat migration"}
    immutable_write(DATA/(f"sample-{args.limit:02}.json"),result)
    subprocess.run(guard,check=True)


if __name__=="__main__":
    main()
