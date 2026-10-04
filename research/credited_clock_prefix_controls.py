"""Exact same-prefix countdown controls; consumed data, no inferred seconds."""
import argparse
from bisect import bisect_left
from collections import Counter
import json
import subprocess

from credited_history_go_controls import DATA as GO
from credited_history_framing_v3 import DATA as TYPED
from credited_late_history_development import immutable_write
from credited_round_dataset import read
from v3_final_reserve import ROOT,sha,source_sha

DATA=ROOT/"data/research/credited-clock-prefix-controls"
EXE=ROOT/".local-tools/bin/siege-clock-prefix-inspect.exe"
SOURCES=("research/credited_clock_prefix_controls.py",
         "third_party/siege-dissect/dissect/clock_prefix_evidence.go",
         "third_party/siege-dissect/dissect/clock_prefix_evidence_test.go",
         "third_party/siege-dissect/cmd/clock-prefix-inspect/main.go")


def clock_regions(samples):
    """Partition only by explicit increases/zero; no phase/time interpretation."""
    result=[];region=0;previous=None
    for s in samples:
        if previous is not None and s["offset"]<=previous["offset"]:
            raise ValueError("Distinct increasing physical clock sources required")
        v=s["unsigned_bits"]
        boundary=None
        if previous is None:
            boundary="first_sample"
        elif v>previous["unsigned_bits"]:
            region+=1;boundary="raw_countdown_increase"
        elif v==0 and previous["unsigned_bits"]>0:
            region+=1;boundary="raw_positive_to_zero"
        result.append(s | {"serialized_region":region,"region_boundary":boundary})
        previous=s
    return result


def event_bracket(samples,offset):
    if offset<=0:
        return {"status":"nonpositive_original_feed_offset","elapsed_seconds":None}
    i=bisect_left([s["offset"] for s in samples],offset)
    before=samples[i-1] if i else None;after=samples[i] if i<len(samples) else None
    status=("missing_one_side" if before is None or after is None else
            "zero_or_terminal_clock" if min(before["unsigned_bits"],after["unsigned_bits"])==0 else
            "serialized_region_change" if before["serialized_region"]!=after["serialized_region"] else
            "same_serialized_positive_countdown_region_raw_units_only")
    return {"status":status,"before":before,"at_or_after":after,"elapsed_seconds":None}


def analyze(raw,observation,history):
    if raw.get("production_authoritative") is not False or raw.get("elapsed_seconds","missing") is not None:
        raise ValueError("Unpromoted prefix evidence required")
    groups=raw["groups"]
    fine=[p for g in groups for p in g["fine"]]
    coarse=[p for g in groups for p in g["coarse"]]
    if len({p["offset"] for p in fine+coarse})!=len(fine)+len(coarse):
        raise ValueError("Duplicate physical field source")
    if not fine or len({p["entity"] for p in fine+coarse})!=1:
        raise ValueError("One exact global provider entity required")
    if any(p["width"]!=4 for p in fine+coarse):
        raise ValueError("Unsupported clock field width")
    if any(p["unsigned_bits"]>600 for p in coarse) or any(p["unsigned_bits"]>600000 for p in fine):
        raise ValueError("Unsupported raw countdown ranges")
    pairs=[];partial=[];ambiguous=[]
    for g in groups:
        a,b=g["coarse"],g["fine"]
        if len(a)>1 or len(b)>1:
            ambiguous.append(g);continue
        if len(a)==len(b)==1:
            pairs.append({"group":g,"floor1000_match":a[0]["unsigned_bits"]==b[0]["unsigned_bits"]//1000})
        else:
            partial.append({"record":g["record"],"entity":g["entity"],"coarse_fields":len(a),"fine_fields":len(b),"stop_reason":g["stop_reason"]})
    regions=clock_regions(sorted(fine,key=lambda p:p["offset"]))
    action=observation["header"]["actionPhaseStartOffset"]
    starts=[p for p in coarse if p["offset"]+9==action]
    if len(starts)!=1:
        raise ValueError("Action marker must equal exact original coarse field end")
    from credited_history_framing_v3 import feed_parity
    if not history["complete"] or not feed_parity(history["items"],observation["credit"]["finishes"])["exact_original_filtered_feed_identity_weapon_headshot_order"]:
        raise ValueError("Original independent history/feed parity required")
    events=[{"original_feed":e,**event_bracket(regions,e["offset"])} for e in observation["credit"]["finishes"]]
    return {"fine_samples":len(fine),"coarse_samples":len(coarse),"same_prefix_pairs":pairs,
            "paired_scale_matches":sum(p["floor1000_match"] for p in pairs),"paired_scale_failures":[p for p in pairs if not p["floor1000_match"]],
            "single_field_prefixes":partial,"ambiguous_prefixes":ambiguous,
            "clock_regions":[p for p in regions if p["region_boundary"]],"original_action_field":starts[0],
            "original_feed_brackets":events,"feed_bracket_status_counts":dict(Counter(e["status"] for e in events)),
            "prefix_stop_counts":dict(Counter(g["stop_reason"] for g in groups)),"elapsed_seconds":None,
            "limits":"Same entity/record/raw scale and serialized regions only, not a precise shot/credit clock. Single-field prefixes do not inherit a guessed pair. Unknowns, zero/overtime and absent sides retained."}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--limit",type=int,default=6);args=parser.parse_args()
    selection=read(GO/"sample-74.json")["records"]
    if not 1<=args.limit<=len(selection):
        raise ValueError("Fixed consumed74sources required")
    reservation={"base_head":"4552019","selection":selection,"binary_sha256":sha(EXE),
                 "source_hashes":{n:source_sha(ROOT/n) for n in SOURCES},
                 "hypothesis":"Integer countdown and finer field co-serialized on one entity in an explicit property prefix; scale floor1000, increases/zero are serialized boundaries. No unit/elapsed-time promotion.",
                 "scope":"Fixed original74consumed sources, no untouched targets/evaluation/pipeline or precise event time"}
    immutable_write(DATA/"reservation.json",reservation)
    records=[]
    for s in selection[:args.limit]:
        replay=s["replay_sha256"];typed_path=TYPED/"records"/(replay+".json");typed=read(typed_path)
        dump=ROOT/typed["dump_path"]
        if sha(dump)!=typed["dump_sha256"]:
            raise ValueError("Fixed dump changed")
        header_path=GO/"headers"/(replay+".json");header=read(header_path)["header"]
        prior=read(ROOT/"data/research/credited-history-lifecycle-controls/records"/(replay+".json"))
        observations=[ROOT/n for n in prior["inputs"] if n.startswith('data/research/credited-kills-v1/observations/')]
        # Use the exact already-validated credit observation named by the
        # lifecycle input manifest rather than creating a new parser cache.
        if len(observations)!=1:
            raise ValueError("Exact sealed credit observation required")
        cache=observations[0];observation=read(cache)
        if sha(cache)!=prior["inputs"][cache.relative_to(ROOT).as_posix()]:
            raise ValueError("Sealed lifecycle credit observation changed")
        if observation["header"]!=header:
            raise ValueError("Saved header/observation differs")
        history_path=GO/"raw"/(replay+".json")
        target=DATA/"records"/(replay+".json")
        if target.exists():
            r=read(target)
            if r["binary_sha256"]!=sha(EXE) or r["source_hashes"]!=reservation["source_hashes"]:
                raise ValueError("Frozen clock-prefix helper/binary differs")
            for n,h in r["inputs"].items():
                if sha(ROOT/n)!=h:
                    raise ValueError("Cached prefix result input differs: "+n)
        else:
            call=subprocess.run([str(EXE),str(dump)],capture_output=True,check=True)
            raw=json.loads(call.stdout);raw_path=DATA/"raw"/(replay+".json");immutable_write(raw_path,raw)
            try:
                finding=analyze(raw,observation,read(history_path));status="prefix_audited"
            except ValueError as exc:
                finding,status={"quality_refusal":str(exc)},"quality_refused"
            r=({k:s[k] for k in ("event","map_id","round","replay_sha256")} |
               {"binary_sha256":sha(EXE),"source_hashes":reservation["source_hashes"],"finding":finding,"status":status,
                "inputs":{str(p.relative_to(ROOT)).replace("\\","/"):sha(p) for p in (dump,typed_path,header_path,cache,history_path,raw_path)}})
            immutable_write(target,r)
        records.append(r)
        f=r["finding"]
        print(len(records),"/",args.limit,s["event"],s["map_id"],s["round"],r["status"],"pairs",len(f.get("same_prefix_pairs",[])),
              "failures",len(f.get("paired_scale_failures",[])),"refusal",f.get("quality_refusal",""),flush=True)
    result={"records":records,"status_counts":dict(Counter(r["status"] for r in records)),
            "fine_samples":sum(r["finding"].get("fine_samples",0) for r in records),
            "same_prefix_pairs":sum(len(r["finding"].get("same_prefix_pairs",[])) for r in records),
            "paired_scale_matches":sum(r["finding"].get("paired_scale_matches",0) for r in records),
            "ambiguous_prefixes":sum(len(r["finding"].get("ambiguous_prefixes",[])) for r in records),
            "feed_bracket_status_counts":dict(sum((Counter(r["finding"].get("feed_bracket_status_counts",{})) for r in records),Counter()))}
    immutable_write(DATA/(f"sample-{args.limit:02}.json"),result)


if __name__=="__main__":
    main()
