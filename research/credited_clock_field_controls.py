"""Explicit clock-field hypotheses on six already consumed sealed sources.

No new targets, default parsing or interpolation. External property names are
hints only; monotonic raw values or numeric ratios never establish clock units.
"""
import argparse
from bisect import bisect_left
from collections import Counter,defaultdict
import json
import subprocess

from credited_history_go_controls import DATA as GO
from credited_history_framing_v3 import DATA as TYPED
from credited_late_history_development import immutable_write
from credited_round_dataset import read,cached_index,cached_observation
from v3_final_reserve import ROOT,sha,source_sha

DATA=ROOT/"data/research/credited-clock-field-controls"
EXE=ROOT/".local-tools/bin/siege-clock-field-inspect.exe"
SOURCES=("research/credited_clock_field_controls.py",
         "third_party/siege-dissect/dissect/clock_field_evidence.go",
         "third_party/siege-dissect/dissect/clock_field_evidence_test.go",
         "third_party/siege-dissect/cmd/clock-field-inspect/main.go")


def bracket(samples,offset):
    if offset<=0:
        return {"resolved_order":False,"reason":"nonpositive_event_offset","elapsed_seconds":None}
    ordered=sorted(samples,key=lambda s:s["offset"])
    if len({s["offset"] for s in ordered})!=len(ordered):
        raise ValueError("Duplicate physical clock property source")
    i=bisect_left([s["offset"] for s in ordered],offset)
    return {"resolved_order":True,"before":ordered[i-1] if i else None,
            "at_or_after":ordered[i] if i<len(ordered) else None,"elapsed_seconds":None,
            "limits":"Serialization brackets only; no elapsed units, event timestamp or interpolation"}


def analyze(raw,observation,history):
    clock=raw["clock"]
    if clock.get("production_authoritative") is not False or clock.get("elapsed_seconds","missing") is not None:
        raise ValueError("Clock hypotheses must remain unpromoted")
    header=raw["raw_header"]
    if header["reason"]!="exact_plain_header_through_teamscore1":
        raise ValueError("Exact modern plain header required")
    parsed=observation["header"]
    codes=[f["value"] for f in header["fields"] if f["key"]=="code"]
    if codes!=[str(parsed["codeVersion"])]:
        raise ValueError("Raw/parsed header build differs")
    fields=defaultdict(list)
    for p in clock["fields"]:
        fields[(p["tag_hex"],p["entity"])].append(p)
    providers=[]
    for (tag,entity),values in fields.items():
        values=sorted(values,key=lambda p:p["offset"])
        if len({p["offset"] for p in values})!=len(values):
            raise ValueError("Duplicate property offsets")
        bits=[p["unsigned_bits"] for p in values]
        changes=[b-a for a,b in zip(bits,bits[1:])]
        providers.append({"tag_hex":tag,"entity":entity,"samples":len(values),
                          "width_counts":dict(Counter(p["width"] for p in values)),
                          "first":values[0],"last":values[-1],"min_raw_bits":min(bits),"max_raw_bits":max(bits),
                          "decreases":sum(d<0 for d in changes),"ties":sum(d==0 for d in changes),
                          "positive_delta_counts":dict(Counter(d for d in changes if d>0)),"elapsed_seconds":None})
    ticks=[t for t in clock["countdown"] if t["reason"]=="exact_listener_marker_width4_raw_uint32" and t["value"]<=600]
    if len(ticks)!=len(clock["countdown"]):
        raise ValueError("Unsupported countdown marker, width or value")
    starts=[t for t in ticks if t["marker_offset"]+9==parsed["actionPhaseStartOffset"]]
    if len(starts)!=1:
        raise ValueError("Independent action marker does not match explicit countdown end")
    timer_rows=[]
    for tick in ticks:
        contexts=[{"tag_hex":tag,"entity":entity,**bracket(values,tick["marker_offset"])}
                  for (tag,entity),values in fields.items() if tag=="1837466c"]
        timer_rows.append({"countdown":tick,"candidate_property_contexts":contexts})
    items=[i for i in history["items"] if i["kind_byte"] in (1,2,3)]
    from credited_history_framing_v3 import feed_parity
    if not history["complete"] or not feed_parity(history["items"],observation["credit"]["finishes"])["exact_original_filtered_feed_identity_weapon_headshot_order"]:
        raise ValueError("Exact history/feed fields and order required")
    events=[]
    for item,event in zip(items,observation["credit"]["finishes"]):
        contexts=[{"tag_hex":tag,"entity":entity,**bracket(values,event["offset"])}
                  for (tag,entity),values in fields.items() if tag=="1837466c"]
        events.append({"history_ordinal":item["ordinal"],"opaque_history_scalar":item["opaque_scalar"],
                       "original_feed":event,"candidate_property_contexts":contexts,"elapsed_seconds":None})
    resets=[{"earlier":a,"later":b} for a,b in zip(ticks,ticks[1:]) if b["value"]>a["value"]]
    return {"providers":providers,"exact_action_countdown":starts[0],"countdown_rows":timer_rows,
            "increasing_countdown_transitions":resets,"history_feed_events":events,
            "raw_header_fields":header["fields"],
            "clock_named_header_fields":[f for f in header["fields"] if any(s in f["key"].lower() for s in ("fps","frame","tick","clock","duration","speed","time"))],
            "production_time_units":None,"limits":"External field names are hypotheses; raw unsigned values and exact serialization context do not calibrate elapsed seconds"}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--limit",type=int,default=2);args=parser.parse_args()
    selection=read(GO/"sample-06.json")["records"]
    if not 1<=args.limit<=len(selection):
        raise ValueError("Fixed six-source cohort required")
    provenance=DATA/"external-sources/provenance.json"
    reservation={"base_head":"1c4568b","selection":selection,"binary_sha256":sha(EXE),
                 "source_hashes":{n:source_sha(ROOT/n) for n in SOURCES},
                 "external_hypothesis":read(provenance),"external_provenance_sha256":sha(provenance),
                 "hypothesis":"0x6C463718 is an externally claimed round-ms field; raw provider width/range/order and countdown phase brackets must be inspected first. 0xA374F4B6 is a separate sequence hypothesis.",
                 "limits":"No clock conversion/interpolation, new original pipeline or target/model evaluation"}
    immutable_write(DATA/"reservation.json",reservation)
    records=[];index=cached_index()
    for s in selection[:args.limit]:
        replay=s["replay_sha256"];old=read(GO/"records"/(replay+".json"))
        recs=[ROOT/n for n in old["inputs"] if n.endswith('.rec')]
        # The Go cached-buffer record does not itself include the replay. The
        # unchanged typed record retains the exact original source path.
        typed_path=TYPED/"records"/(replay+".json");typed=read(typed_path)
        if not recs:
            prior=read(ROOT/"data/research/credited-history-lifecycle-controls/records"/(replay+".json"))
            recs=[ROOT/n for n in prior["inputs"] if n.endswith('.rec')]
        if len(recs)!=1 or sha(recs[0])!=replay:
            raise ValueError("Unique sealed physical replay required")
        dump=ROOT/typed["dump_path"]
        if sha(dump)!=typed["dump_sha256"]:
            raise ValueError("Fixed dump changed")
        cache,observation=cached_observation(index,replay)
        history_path=GO/"raw"/(replay+".json")
        target=DATA/"records"/(replay+".json")
        if target.exists():
            r=read(target)
            if r["binary_sha256"]!=sha(EXE) or r["source_hashes"]!=reservation["source_hashes"]:
                raise ValueError("Clock source/binary changed")
            for n,h in r["inputs"].items():
                if sha(ROOT/n)!=h:
                    raise ValueError("Clock evidence changed: "+n)
        else:
            call=subprocess.run([str(EXE),str(dump),str(recs[0])],capture_output=True,check=True)
            raw=json.loads(call.stdout);raw_path=DATA/"raw"/(replay+".json");immutable_write(raw_path,raw)
            finding=analyze(raw,observation,read(history_path))
            r=({k:s[k] for k in ("event","map_id","round","replay_sha256")} |
               {"binary_sha256":sha(EXE),"source_hashes":reservation["source_hashes"],"finding":finding,
                "inputs":{str(p.relative_to(ROOT)).replace("\\","/"):sha(p) for p in (dump,recs[0],typed_path,cache,history_path,raw_path)}})
            immutable_write(target,r)
        records.append(r)
        f=r["finding"]
        print(s["event"],s["map_id"],s["round"],"providers",[(p["tag_hex"],p["entity"],p["samples"],p["min_raw_bits"],p["max_raw_bits"],p["decreases"]) for p in f["providers"]],
              "metadata",f["clock_named_header_fields"],flush=True)
    immutable_write(DATA/(f"sample-{args.limit:02}.json"),{"records":records,"status":"explicit_clock_hypotheses_raw_evidence_units_unresolved"})


if __name__=="__main__":
    main()
