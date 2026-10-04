"""Cached fixed-buffer controls for opt-in Go history evidence, not migration."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from credited_history_framing_v3 import DATA as TYPED_DATA
from credited_late_history_development import immutable_write
from credited_round_dataset import read,cached_index,cached_observation
from v3_final_reserve import ROOT,sha,source_sha

EXE = ROOT/".local-tools/bin/siege-history-inspect.exe"
DATA = ROOT/"data/research/credited-history-go-controls"
SOURCES = ("research/credited_history_go_controls.py",
           "third_party/siege-dissect/dissect/event_history_evidence.go",
           "third_party/siege-dissect/dissect/event_history_evidence_test.go",
           "third_party/siege-dissect/cmd/history-inspect/main.go")


def compare_history(expected,actual,header):
    errors = []
    if not expected["cumulative"]["complete"] or not actual.get("complete"):
        errors.append("complete_control_or_go_history_required")
    if actual.get("production_authoritative") is not False:
        errors.append("production_authority_must_remain_false")
    a,b = expected["cumulative"]["items"],actual.get("items",[])
    if len(a) != len(b):
        errors.append("item_count_differs")
    by_uid = {p["id"]:p for p in header["players"]}
    for i,(old,new) in enumerate(zip(a,b)):
        for key in ("ordinal","start","end","kind_byte","opaque_scalar","raw_hex","weapon_id","entity_reference","headshot","opaque_tail_u8"):
            if old.get(key) != new.get(key):
                errors.append(f"item{i}:{key}")
        if new.get("elapsed_seconds", "missing") is not None:
            errors.append(f"item{i}:clock_not_unresolved")
        for key in ("first","second","reference"):
            old_ref,new_ref = old.get(key),new.get(key)
            if (old_ref is None) != (new_ref is None):
                errors.append(f"item{i}:{key}_presence")
                continue
            if old_ref is None:
                continue
            for field in ("uid","username","role_image","alliance"):
                if old_ref[field] != new_ref.get(field):
                    errors.append(f"item{i}:{key}:{field}")
            player = by_uid[old_ref["uid"]]
            if new_ref.get("team") != player["teamIndex"] or new_ref.get("profile_id") != player.get("profileID",""):
                errors.append(f"item{i}:{key}:header_team_profile")
    if len(expected["containers"]) != len(actual.get("containers",[])):
        errors.append("container_count_differs")
    for i,(old,new) in enumerate(zip(expected["containers"],actual.get("containers",[]))):
        for key in ("start","end","item_count","payload_length"):
            if old[key] != new.get(key):
                errors.append(f"container{i}:{key}")
        if old["framed"]["complete"] != new.get("complete"):
            errors.append(f"container{i}:complete")
        if [x["raw_hex"] for x in old["framed"]["items"]] != [x["raw_hex"] for x in new.get("items",[])]:
            errors.append(f"container{i}:raw_item_order")
    for key in ("scalar_ties","scalars_nondecreasing"):
        if expected["cumulative"].get(key) != actual.get(key):
            errors.append(key)
    return {"match":not errors,"differences":errors}


def main():
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument("--limit",type=int,default=6)
    args = args.parse_args()
    guard = [sys.executable,str(ROOT/"research/verify_history_typed_checkpoint.py")]
    subprocess.run(guard,check=True)
    selection = []
    for cohort in ("six","68"):
        selection += read(TYPED_DATA/("result-"+cohort+".json"))["records"]
    if len({r["replay_sha256"] for r in selection}) != len(selection) or not 1 <= args.limit <= len(selection):
        raise ValueError("Exact fixed74source cohort required")
    reservation = {"base_head":"3caf344","selection":selection,"binary_sha256":sha(EXE),
                   "source_hashes":{p:source_sha(ROOT/p) for p in SOURCES},
                   "limits":"Go structural parity only; no credited owner/seconds/runtime/default/stat/SQL/public change"}
    immutable_write(DATA/"reservation.json",reservation)
    signature = hashlib.sha256(json.dumps(reservation,sort_keys=True).encode()).hexdigest()
    index, records = cached_index(),[]
    for i,source in enumerate(selection[:args.limit],1):
        name = source["replay_sha256"]
        expected_path = TYPED_DATA/"records"/(name+".json")
        expected = read(expected_path)
        dump = ROOT/expected["dump_path"]
        if sha(dump) != expected["dump_sha256"]:
            raise ValueError("Fixed typed buffer changed")
        cache, observation = cached_observation(index,name)
        header = DATA/"headers"/(name+".json")
        immutable_write(header,{"header":observation["header"]})
        target = DATA/"records"/(name+".json")
        if target.exists():
            record = read(target)
            if record["reservation_signature"] != signature:
                raise ValueError("Cached Go result source/binary reservation differs")
            for n,h in record["inputs"].items():
                if sha(ROOT/n) != h:
                    raise ValueError("Cached Go evidence changed: "+n)
        else:
            call = subprocess.run([str(EXE),"--buffer",str(header),str(dump)],capture_output=True)
            raw_path = DATA/"raw"/(name+".json")
            if call.returncode != 0:
                actual = {"tool_error":call.stderr.decode("utf-8",errors="replace"),"returncode":call.returncode}
                compared = {"match":False,"differences":["tool_failure"]}
            else:
                actual = json.loads(call.stdout)
                compared = compare_history(expected,actual,observation["header"])
            immutable_write(raw_path,actual)
            record = ({k:expected[k] for k in ("event","map_id","round","replay_sha256")} |
                     {"reservation_signature":signature,"comparison":compared,
                      "inputs":{str(p.relative_to(ROOT)).replace("\\","/"):sha(p) for p in (cache,expected_path,dump,header,raw_path)}})
            immutable_write(target,record)
        records.append(record)
        print(i,"/",args.limit,source["event"],source["map_id"],source["round"],record["comparison"],flush=True)
    summary = {"matched_sources":sum(r["comparison"]["match"] for r in records),"total_sources":len(records),
               "records":records,"status":"go_cached_buffer_structural_controls_not_promoted"}
    immutable_write(DATA/(f"sample-{args.limit:02}.json"),summary)
    subprocess.run(guard,check=True)


if __name__ == "__main__":
    main()
