"""Raw countdown brackets for reviewed split-credit and missing-body cases.

Clock span bounds are mathematical differences of serialized observations, not
precise event times. No nearest-counter victim join or inferred causal actor.
"""
import json
from pathlib import Path

from credited_clock_prefix_controls import clock_regions,event_bracket,DATA as CLOCK
from credited_history_lifecycle_controls import DATA as LIFE
from credited_history_go_controls import DATA as HISTORY
from credited_owned_property_controls import DATA as OWNED
from credited_late_history_development import immutable_write
from credited_round_dataset import read
from v3_final_reserve import ROOT,sha,source_sha

DATA=ROOT/"data/research/credited-clock-case-timelines-v2"


def raw_span(earlier,later):
    a,b=earlier["clock_bracket"],later["clock_bracket"]
    if earlier["offset"]<=0 or later["offset"]<earlier["offset"]:
        return {"status":"unknown_or_reversed_physical_order","elapsed_seconds":None}
    valid="same_serialized_positive_countdown_region_raw_units_only"
    if a["status"]!=valid or b["status"]!=valid:
        return {"status":"unsupported_event_bracket","earlier_status":a["status"],"later_status":b["status"],"elapsed_seconds":None}
    if a["before"]["entity"]!=b["before"]["entity"] or a["before"]["serialized_region"]!=b["before"]["serialized_region"]:
        return {"status":"different_serialized_clock_provider_or_region","elapsed_seconds":None}
    lower=max(0,a["at_or_after"]["unsigned_bits"]-b["before"]["unsigned_bits"])
    upper=a["before"]["unsigned_bits"]-b["at_or_after"]["unsigned_bits"]
    if upper<lower:
        return {"status":"inconsistent_raw_countdown_bounds","elapsed_seconds":None}
    return {"status":"bounded_raw_countdown_difference_only","lower_raw_units":lower,"upper_raw_units":upper,
            "elapsed_seconds":None,"limits":"Clock scale observed1000perinteger second; this is serialized bracket math, not an exact shot/DBNO/credit event clock"}


def case(selection,lifecycle,observation,history,clock):
    uid=selection["target_identity"]["id"];name=selection["target_identity"]["username"]
    identity={p["username"]:p for p in observation["header"]["players"]}
    if identity.get(name)!=selection["target_identity"]:
        raise ValueError("Fixed target identity differs")
    fine=sorted([p for g in clock["groups"] for p in g["fine"]],key=lambda p:p["offset"])
    samples=clock_regions(fine)
    timeline=[]
    for b in lifecycle["finding"]["post_action_body"]:
        timeline.append({"kind":"typed_body_raw_state","offset":b["offset"],"uid":identity[b["player"]]["id"],
                         "raw_body":b,"generic_dbno_role":None,"causal_actor_uid":None})
    for p in observation["credit"]["players"]:
        h=identity[p["username"]]
        if (p["uid"],p["profileID"],p["team"])!=(h["id"],h["profileID"],h["teamIndex"]):
            raise ValueError("Counter/header UID-profile-name-team identity differs")
        previous=None
        for s in sorted(p["samples"],key=lambda s:s["offset"]):
            if previous is None or s["value"]!=previous["value"]:
                timeline.append({"kind":"uid_counter_observation","offset":s["offset"],"uid":p["uid"],
                                 "username":p["username"],"sample":s,"previous":previous,
                                 "raw_delta":None if previous is None else s["value"]-previous["value"],
                                 "credited_victim_uid":None,"official_kill_occurrence_time":None})
            previous=s
    for e in observation["credit"]["finishes"]:
        timeline.append({"kind":"original_finisher_elimination","offset":e["offset"],"original_feed":e,
                         "credited_uid":None})
    for e in timeline:
        e["clock_bracket"]=event_bracket(samples,e["offset"])
    timeline.sort(key=lambda e:(e["offset"]==0,e["offset"]))
    target_body=[e for e in timeline if e["kind"]=="typed_body_raw_state" and e["uid"]==uid]
    raw3=[e for e in target_body if e["offset"]==selection["observation"]["offset"] and e["raw_body"]["raw_state"]==3]
    if len(raw3)!=1:
        raise ValueError("Exact selected target raw3 required")
    later=[e for e in target_body if e["offset"]>raw3[0]["offset"] and e["raw_body"]["raw_state"]==4]
    span=raw_span(raw3[0],later[0]) if later else {"status":"no_later_target_raw4","elapsed_seconds":None}
    finals=[e for e in timeline if e["kind"]=="original_finisher_elimination" and
            (e["original_feed"]["feedback"].get("target")==name or e["original_feed"]["feedback"]["type"]["name"]=="Death" and e["original_feed"]["feedback"]["username"]==name)]
    return {"target_uid":uid,"target_identity":selection["target_identity"],"live_serialized_timeline":timeline,
            "target_raw3_to_next_raw4":span,"target_body_timeline":target_body,"target_final_eliminations":finals,
            "history_target_items":[i for i in history["items"] if i.get("second",i.get("reference",{})).get("uid")==uid],
            "history_limits":"Late list items retain ordinal/raw scalar and physical copies; copy offsets are not live timestamps and are not merged into the live timeline",
            "causal_actor_uid":None,"credited_victim_uid":None,"elapsed_seconds":None}


def main():
    selection=read(OWNED/"sample-10.json")["records"]
    sources=(Path(__file__),ROOT/"research/credited_clock_prefix_controls.py")
    reservation={"base_head":"016e51e","selection":[{k:r[k] for k in ("event","map_id","round","replay_sha256","control","observation","target_identity")} for r in selection],
                 "source_hashes":{p.relative_to(ROOT).as_posix():source_sha(p) for p in sources},
                 "hypothesis":"Annotate independently routed body/counter/original finish samples with raw clock brackets; raw3->raw4 span does not establish a generic downer or credit cause",
                 "limits":"Consumed cached ten sources only; no seconds/interpolation/actor or nearest-counter inference"}
    immutable_write(DATA/"reservation.json",reservation)
    records=[]
    for s in selection:
        replay=s["replay_sha256"]
        life_path=LIFE/"records"/(replay+".json");life=read(life_path)
        caches=[ROOT/n for n in life["inputs"] if n.startswith('data/research/credited-kills-v1/observations/')]
        if len(caches)!=1:
            raise ValueError("Exact sealed observation required")
        cache=caches[0]
        if sha(cache)!=life["inputs"][cache.relative_to(ROOT).as_posix()]:
            raise ValueError("Exact cached credit data changed")
        clock_path=CLOCK/"raw"/(replay+".json");history_path=HISTORY/"raw"/(replay+".json")
        finding=case(s,life,read(cache),read(history_path),read(clock_path))
        r=({k:s[k] for k in ("event","map_id","round","replay_sha256","control")} |
           {"finding":finding,"inputs":{p.relative_to(ROOT).as_posix():sha(p) for p in (life_path,cache,clock_path,history_path)}})
        immutable_write(DATA/"records"/(replay+".json"),r);records.append(r)
        print(s["map_id"],s["round"],s["target_identity"]["username"],finding["target_raw3_to_next_raw4"],flush=True)
    immutable_write(DATA/"result.json",{"records":records,"sources":len(records),"status":"raw_clock_annotated_case_timelines_no_causal_credit_join"})


if __name__=="__main__":
    main()
