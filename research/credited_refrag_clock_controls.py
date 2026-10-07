"""Read-only finisher-identity refrag clock bands, not credited trade policy.

Uses physical/original filtered event order and actual eliminations for alive
state. DBNO does not remove a player. No Rating or live statistics calculation.
"""
from collections import Counter
import json
from pathlib import Path

from credited_clock_case_timelines import raw_span
from credited_clock_prefix_controls import DATA as CLOCK,clock_regions,event_bracket
from credited_history_go_controls import DATA as GO
from credited_late_history_development import immutable_write
from credited_round_dataset import read
from v3_final_reserve import ROOT,sha,source_sha

DATA=ROOT/"data/research/credited-refrag-clock-controls"
WINDOW_RAW_UNITS=8000


def band(span,threshold=WINDOW_RAW_UNITS):
    if span["status"]!="bounded_raw_countdown_difference_only":
        return "unresolved_raw_clock_band"
    if span["upper_raw_units"]<=threshold:
        return "within_candidate_raw_window"
    if span["lower_raw_units"]>threshold:
        return "beyond_candidate_raw_window"
    return "straddles_candidate_raw_window"


def audit(finishes,players,clock):
    by_name={p["username"]:p for p in players}
    if len(by_name)!=10 or len({p["id"] for p in players})!=10:
        raise ValueError("Ten exact player identities required")
    alive={p["id"] for p in players};processed=[];pairs=[];refusals=[];previous=0
    for ordinal,source in enumerate(finishes):
        feedback=source["feedback"];kind=feedback["type"]["name"]
        if kind not in ("Kill","Death"):
            raise ValueError("Original filtered elimination types required")
        victim_name=feedback["target"] if kind=="Kill" else feedback["username"]
        if victim_name not in by_name or kind=="Kill" and feedback["username"] not in by_name:
            raise ValueError("Unbound original elimination identity")
        if source["offset"]>0:
            if source["offset"]<=previous:
                raise ValueError("Nonmonotonic or duplicate positive physical source")
            previous=source["offset"]
        victim=by_name[victim_name];killer=by_name[feedback["username"]] if kind=="Kill" else None
        row={"ordinal":ordinal,"source":source,"offset":source["offset"],"victim":victim,"finisher":killer,
             "clock_bracket":event_bracket(clock,source["offset"]),"credited_uid":None,
             "alive_before":sorted(alive)}
        if victim["id"] not in alive:
            refusals.append(row | {"reason":"already_eliminated_victim_duplicate_not_recounted"});continue
        opposing=killer is not None and killer["teamIndex"]!=victim["teamIndex"]
        if opposing:
            for prior in processed:
                a=prior["finisher"]
                if a is None or a["teamIndex"]==prior["victim"]["teamIndex"]:
                    continue
                if a["id"]!=victim["id"] or prior["victim"]["teamIndex"]!=killer["teamIndex"]:
                    continue
                span=raw_span(prior,row)
                delta=prior["source"]["feedback"]["timeInSeconds"]-feedback["timeInSeconds"]
                classification=band(span)
                pairs.append({"earlier":prior,"later":row,"raw_countdown_span":span,
                              "raw_band":classification,"legacy_coarse_remaining_delta":delta,
                              "legacy_8s_numeric_expression":0<=delta<=8,"credited_identity_resolved":False,
                              "limits":"Finisher identity pattern and raw serialized clock band only; not an official trade, actual credited owner or exact elapsed time"})
        # Death/unknown cause, self-kill and teamkill all remove the victim;
        # none supplies an opposing kill or a manufactured refrag.
        alive.remove(victim["id"]);row["alive_after"]=sorted(alive);processed.append(row)
    return {"processed_eliminations":processed,"duplicate_victim_refusals":refusals,"finisher_refrag_pairs":pairs,
            "raw_band_counts":dict(Counter(p["raw_band"] for p in pairs)),
            "legacy_numeric_expression_counts":dict(Counter(str(p["legacy_8s_numeric_expression"]) for p in pairs)),
            "candidate_raw_window_units":WINDOW_RAW_UNITS,"actual_trade_policy_promoted":False}


def main():
    selection=read(CLOCK/"sample-74.json")["records"]
    sources=(Path(__file__),ROOT/"research/credited_clock_case_timelines.py",ROOT/"research/credited_clock_prefix_controls.py")
    reservation={"base_head":"5406610","selection":[{k:r[k] for k in ("event","map_id","round","replay_sha256")} for r in selection],
                 "source_hashes":{p.relative_to(ROOT).as_posix():source_sha(p) for p in sources},
                 "candidate_window_raw_units":WINDOW_RAW_UNITS,
                 "hypothesis":"Exact finisher/victim/team pattern compared with raw same-region span bands at8000observed countdown units; no credited/time policy promotion",
                 "limits":"Consumed structural development controls, no alternate-window search, target/model evaluation or historical/stat change"}
    immutable_write(DATA/"reservation.json",reservation);records=[]
    for s in selection:
        if s["status"]!="prefix_audited":
            raise ValueError("Previously audited one-provider prefix source required")
        replay=s["replay_sha256"];raw_path=CLOCK/"raw"/(replay+".json");raw=read(raw_path)
        fine=sorted([p for g in raw["groups"] for p in g["fine"]],key=lambda p:p["offset"])
        samples=clock_regions(fine)
        caches=[ROOT/n for n in s["inputs"] if n.startswith('data/research/credited-kills-v1/observations/')]
        if len(caches)!=1:
            raise ValueError("Exact existing credit observation required")
        cache=caches[0]
        if sha(cache)!=s["inputs"][cache.relative_to(ROOT).as_posix()]:
            raise ValueError("Saved exact observation changed")
        obs=read(cache)
        finding=audit(obs["credit"]["finishes"],obs["header"]["players"],samples)
        r=({k:s[k] for k in ("event","map_id","round","replay_sha256")} |
           {"finding":finding,"inputs":{p.relative_to(ROOT).as_posix():sha(p) for p in (raw_path,cache)}})
        immutable_write(DATA/"records"/(replay+".json"),r);records.append(r)
        print(s["event"],s["map_id"],s["round"],finding["raw_band_counts"],"duplicates",len(finding["duplicate_victim_refusals"]),flush=True)
    pairs=[p for r in records for p in r["finding"]["finisher_refrag_pairs"]]
    summary={"records":records,"raw_band_counts":dict(Counter(p["raw_band"] for p in pairs)),
             "legacy_numeric_expression_true":sum(p["legacy_8s_numeric_expression"] for p in pairs),
             "duplicates_not_recounted":sum(len(r["finding"]["duplicate_victim_refusals"]) for r in records),
             "determinate_raw_band_legacy_disagreements":sum(
                 (p["raw_band"]=="within_candidate_raw_window")!=p["legacy_8s_numeric_expression"]
                 for p in pairs if p["raw_band"] in ("within_candidate_raw_window","beyond_candidate_raw_window")),
             "status":"finisher_only_refrag_clock_bands_not_official_credit_or_trade_policy"}
    immutable_write(DATA/"result.json",summary)


if __name__=="__main__":
    main()
