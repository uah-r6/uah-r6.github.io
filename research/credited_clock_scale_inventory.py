"""Descriptive scale/epoch inventory from newly cached explicit clock fields.

Observed development evidence only. Scalar floor correspondence is reported,
not silently adopted as an authoritative event timestamp or elapsed clock.
"""
from collections import Counter
from pathlib import Path

from credited_clock_field_controls import DATA
from credited_late_history_development import immutable_write
from credited_round_dataset import read
from v3_final_reserve import ROOT,sha,source_sha


def describe(record,raw):
    finding=record["finding"]
    candidates=[p for p in finding["providers"] if p["tag_hex"]=="1837466c"]
    if len(candidates)!=1 or candidates[0]["width_counts"]!={4: candidates[0]["samples"]} and candidates[0]["width_counts"]!={"4": candidates[0]["samples"]}:
        raise ValueError("Exactly one raw width4 provider required")
    fields=[p for p in raw["clock"]["fields"] if p["tag_hex"]=="1837466c"]
    matches,failures,missing=[],[],[]
    for row in finding["countdown_rows"]:
        contexts=row["candidate_property_contexts"]
        if len(contexts)!=1:
            raise ValueError("Exactly one provider per countdown context required")
        after=contexts[0]["at_or_after"]
        if after is None:
            missing.append(row)
        elif after["unsigned_bits"]//1000==row["countdown"]["value"]:
            matches.append({"timer_offset":row["countdown"]["marker_offset"],
                            "timer_seconds":row["countdown"]["value"],"property_offset":after["offset"],
                            "raw_property_value":after["unsigned_bits"]})
        else:
            failures.append(row)
    changes=[a["unsigned_bits"]-b["unsigned_bits"] for a,b in zip(fields,fields[1:])]
    resets=[{"before":a,"after":b} for a,b in zip(fields,fields[1:]) if b["unsigned_bits"]>a["unsigned_bits"]]
    hazards=[]
    for event in finding["history_feed_events"]:
        c=event["candidate_property_contexts"][0];a,b=c["before"],c["at_or_after"]
        reason=("missing_one_side" if a is None or b is None else
                "zero_or_terminal_clock" if min(a["unsigned_bits"],b["unsigned_bits"])==0 else
                "countdown_increase_or_reset" if a["unsigned_bits"]<b["unsigned_bits"] else None)
        if reason:
            hazards.append({"event":event,"reason":reason,"elapsed_seconds":None})
    return {"samples":len(fields),"coarse_countdown_samples":len(finding["countdown_rows"]),
            "floor1000_matches":matches,"floor1000_failures":failures,"missing_next_property":missing,
            "positive_countdown_steps":dict(Counter(d for d in changes if d>0)),"increases":resets,
            "terminal_or_reset_event_brackets":hazards,"clock_units_promoted":False,"elapsed_seconds":None,
            "interpretation":"Observed field behaves as higher-resolution remaining countdown, not monotonic elapsed time. Exact epoch/time/occurrence policy still unpromoted."}


def main():
    result=read(DATA/"sample-06.json");records=[];inputs={}
    for r in result["records"]:
        raw_path=DATA/"raw"/(r["replay_sha256"]+".json")
        finding=describe(r,read(raw_path));inputs[raw_path.relative_to(ROOT).as_posix()]=sha(raw_path)
        records.append({k:r[k] for k in ("event","map_id","round","replay_sha256")} | {"finding":finding})
        print(r["map_id"],r["round"],"floor1000",len(finding["floor1000_matches"]),"/",finding["coarse_countdown_samples"],
              "hazards",[e["reason"] for e in finding["terminal_or_reset_event_brackets"]],flush=True)
    immutable_write(DATA/"scale-inventory.json",{"records":records,"inputs":inputs,
                                               "source_sha256":source_sha(Path(__file__)),
                                               "scope":"Descriptive consumed development inventory, not a new unseen validation or seconds/credit policy"})


if __name__=="__main__":
    main()
