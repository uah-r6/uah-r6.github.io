"""Fixed consumed missing-history targets and two reviewed split-credit controls.

New opt-in Go evidence on existing buffers, not a default parse/import. Full
scalar/text prefixes within a bounded offset context, plus exact numeric UID or
owner-entity matches across the post-action buffer. Numeric equality is not a
damage relationship, and byte context is not time or a victim-credit join.
"""
import argparse
from collections import Counter
import hashlib
import json
import subprocess

from credited_late_history_development import immutable_write
from credited_round_dataset import read
from v3_final_reserve import ROOT, sha, source_sha

DATA = ROOT/"data/research/credited-owned-property-controls"
LIFE = ROOT/"data/research/credited-history-lifecycle-controls"
GO = ROOT/"data/research/credited-history-go-controls"
TYPED = ROOT/"data/research/credited-history-framing-v3"
EXE = ROOT/".local-tools/bin/siege-owned-property-inspect.exe"
SOURCES = ("research/credited_owned_property_controls.py",
           "third_party/siege-dissect/dissect/owned_property_evidence.go",
           "third_party/siege-dissect/dissect/owned_property_evidence_test.go",
           "third_party/siege-dissect/cmd/owned-property-inspect/main.go")


def fixed_selection():
    result = read(LIFE/"sample-74.json")
    selected = []
    for map_id, target in ((8580,"Stk"),(8583,"resetz")):
        candidates = []
        for r in result["records"]:
            if r["event"] != "SAL" or r["map_id"] != map_id or r["round"] != (6 if map_id == 8580 else 2):
                continue
            for c in r["finding"]["controls"]:
                if c["candidate"]["kind_byte"] == 5 and c["candidate"]["second"]["username"].split(".")[0] == target:
                    for b in c["matching_raw_state_observations"]:
                        candidates.append({k:r[k] for k in ("event","map_id","round","replay_sha256")} |
                                          {"observation":b,"control":"independently_reviewed_split_case"})
        if len(candidates) != 1:
            raise ValueError("Exactly one reviewed target raw3 required: "+target)
        selected += candidates
    selected += [r | {"control":"raw3_without_kind5_target"} for r in result["unrepresented_raw3"]]
    if len(selected) != 10 or len({r["replay_sha256"] for r in selected}) != 10:
        raise ValueError("Fixed two reviewed plus eight missing-target sources required")
    return selected


def summarize(evidence, selection):
    if evidence.get("production_authoritative") is not False or evidence.get("elapsed_seconds","missing") is not None:
        raise ValueError("Unpromoted evidence and unresolved elapsed clock required")
    if evidence.get("reason") != "bounded_scalar_text_prefixes_only_not_complete_component_or_causal_evidence":
        return {"quality_refusal":evidence.get("reason"),"credited_victim_uid":None,"causal_actor_uid":None}
    uid = evidence["query"]["target_uid"]
    fields = [f for p in evidence["prefixes"] for f in p["fields"]]
    raw3 = [f for f in fields if f["offset"] == selection["observation"]["offset"] and
            f["tag_hex"] == "e788f6a5" and f["width"] == 4 and f["unsigned_bits"] == 3 and
            f["route"]["identity"]["uid"] == uid and f["route"]["slot"] == 0xc4dc5441 and
            f["route"]["class"] == 0x3fc6980c]
    if len(raw3) != 1:
        raise ValueError("Independent exact target UID/body/raw3 offset not reproduced")
    incoming = [f for f in fields if f["route"]["identity"]["uid"] != uid and
                any(r["identity"]["uid"] == uid for r in f["candidate_numeric_references"])]
    target = [f for f in fields if f["route"]["identity"]["uid"] == uid and
              evidence["query"]["target_start"] <= f["offset"] < evidence["query"]["target_end"]]
    return {"target_raw3_exact_parity":True,"target_context_fields":len(target),
            "all_selected_prefixes":len(evidence["prefixes"]),
            "prefix_stop_counts":dict(Counter(p["stop_reason"] for p in evidence["prefixes"])),
            "incoming_numeric_reference_fields":incoming,
            "incoming_reference_count":len(incoming),"credited_victim_uid":None,"causal_actor_uid":None,
            "limits":"Exact numeric matches only, no damage/instigator interpretation; unknown widths stop prefixes. No complete-record claim, elapsed seconds or nearest-counter inference."}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit",type=int,default=2)
    args=parser.parse_args()
    selection=fixed_selection()
    if not 1<=args.limit<=len(selection):
        raise ValueError("Limit outside fixed ten sources")
    reservation={"base_head":"52a9cfe","selection":selection,"binary_sha256":sha(EXE),
                 "source_hashes":{n:source_sha(ROOT/n) for n in SOURCES},
                 "hypothesis":"A UID-owned scalar prefix may contain an exact target UID or owner-entity reference missing from history; numeric equality alone never proves causality",
                 "query_scope":"Target context [raw3-4096,raw3+8192), full post-action reference scan; byte windows are not elapsed time"}
    immutable_write(DATA/"reservation.json",reservation)
    signature=hashlib.sha256(json.dumps(reservation,sort_keys=True).encode()).hexdigest()
    records=[]
    for s in selection[:args.limit]:
        replay=s["replay_sha256"]
        typed_path=TYPED/"records"/(replay+".json")
        typed=read(typed_path)
        dump=ROOT/typed["dump_path"]
        if sha(dump)!=typed["dump_sha256"]:
            raise ValueError("Cached fixed dump changed")
        header_path=GO/"headers"/(replay+".json")
        header=read(header_path)["header"]
        player=[p for p in header["players"] if p["username"] == s["observation"]["player"]]
        if len(player)!=1:
            raise ValueError("Unique exact target header identity required")
        at=s["observation"]["offset"]
        query={"start":header["actionPhaseStartOffset"],"end":dump.stat().st_size,
               "target_uid":player[0]["id"],"target_start":max(header["actionPhaseStartOffset"],at-4096),
               "target_end":min(dump.stat().st_size,at+8192)}
        query_path=DATA/"queries"/(replay+".json")
        immutable_write(query_path,query)
        target=DATA/"records"/(replay+".json")
        if target.exists():
            r=read(target)
            if r["reservation_signature"]!=signature:
                raise ValueError("Source/binary/selection reservation changed")
            for n,h in r["inputs"].items():
                if sha(ROOT/n)!=h:
                    raise ValueError("Cached owned-property evidence changed: "+n)
        else:
            call=subprocess.run([str(EXE),str(header_path),str(dump),str(query_path)],capture_output=True,check=True)
            evidence=json.loads(call.stdout)
            raw_path=DATA/"raw"/(replay+".json")
            immutable_write(raw_path,evidence)
            finding=summarize(evidence,s)
            r=s | {"target_identity":player[0],"reservation_signature":signature,"finding":finding,
                   "inputs":{str(p.relative_to(ROOT)).replace("\\","/"):sha(p) for p in (typed_path,dump,header_path,query_path,raw_path)}}
            immutable_write(target,r)
        records.append(r)
        print(s["event"],s["map_id"],s["round"],s["observation"]["player"],r["finding"],flush=True)
    result={"records":records,"sources":len(records),
            "target_raw3_exact_parity":sum(r["finding"].get("target_raw3_exact_parity",False) for r in records),
            "incoming_numeric_references":sum(r["finding"].get("incoming_reference_count",0) for r in records),
            "status":"bounded_prefix_reference_inventory_not_credited_join"}
    immutable_write(DATA/(f"sample-{args.limit:02}.json"),result)


if __name__=="__main__":
    main()
