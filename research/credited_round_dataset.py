"""Canonical cached player-round evidence; read-only, no production wiring.

Counters are player-round observations. Finish events are victim eliminations.
There is deliberately no nearest-counter join between those two inventories.
"""
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys

from credited_kill_evidence import EXE
from r6stats.kill_credit import SOURCE, identity, validate_map_credit
from v3_final_reserve import ROOT, sha, source_sha

DATA = ROOT / "data/research/credited-round-dataset"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def counter_changes(player):
    samples = player.get("samples", [])
    if any(type(s["offset"]) is not int or s["offset"] <= 0 or
           type(s["value"]) is not int or s["value"] < 0 for s in samples):
        raise ValueError("Invalid counter sample")
    if any(a["offset"] >= b["offset"] or a["value"] > b["value"] or
           (a["owner"], a["component"]) != (b["owner"], b["component"])
           for a, b in zip(samples, samples[1:])):
        raise ValueError("Counter sample route/order/reset is unresolved")
    changes = [{"offset": b["offset"], "before": a["value"], "after": b["value"],
                "delta": b["value"]-a["value"], "victim": None,
                "elapsed_time": None, "source": SOURCE}
               for a, b in zip(samples, samples[1:]) if b["value"] > a["value"]]
    if player.get("kills") is not None and sum(c["delta"] for c in changes) != player["kills"]:
        raise ValueError("Counter changes disagree with round delta")
    return changes


def event_inventory(credit):
    by_name = {p["username"]: p for p in credit["players"]}
    if len(by_name) != len(credit["players"]):
        raise ValueError("Ambiguous finish name identity")
    events = []
    known = [e["offset"] for e in credit["finishes"] if e["offset"] > 0]
    if len(set(known)) != len(known):
        raise ValueError("Duplicate physical elimination source")
    for index, event in enumerate(credit["finishes"]):
        f = event["feedback"]
        kind = f["type"]["name"]
        if kind not in ("Kill", "Death"):
            raise ValueError("Unsupported elimination event")
        victim = by_name.get(f.get("target") if kind == "Kill" else f.get("username"))
        finisher = by_name.get(f.get("username")) if kind == "Kill" else None
        if victim is None or (kind == "Kill" and finisher is None):
            classification = "unbound_identity"
        elif finisher is None:
            classification = "no_named_finisher_cause_unresolved"
        elif victim["uid"] == finisher["uid"]:
            classification = "suicide"
        elif victim["team"] == finisher["team"]:
            classification = "teamkill"
        else:
            classification = "opponent_finish"
        events.append({"feedback_sequence": index, "packet_offset": event["offset"] or None,
                       "victim": identity(victim) if victim else None,
                       "victim_username": victim["username"] if victim else f.get("target", f.get("username")),
                       "finisher": identity(finisher) if finisher else None,
                       "finisher_username": finisher["username"] if finisher else None,
                       "classification": classification, "credited_killer": None, "downer": None,
                       "dbno_time": None, "elimination_elapsed_time": None,
                       "remaining_clock": f["timeInSeconds"], "raw_headshot": f.get("headshot", False),
                       "ordering_source": "known_physical_offset" if event["offset"] > 0 else "unresolved_zero_legacy_offset",
                       "raw_feedback": f})
    return events


def player_rows(meta, observation, round_valid, map_complete):
    credit = observation["credit"]
    if credit["source"] != SOURCE:
        raise ValueError("Unsupported canonical counter source")
    events = event_inventory(credit)
    result = []
    for p in credit["players"]:
        key = identity(p)
        finishes = [e for e in events if e["finisher"] == key]
        kills = sum(e["classification"] == "opponent_finish" for e in finishes)
        count = p["kills"] if round_valid else None
        result.append({**meta, "uid": p["uid"], "profile_id": p.get("profileID"),
                       "player_identity": key, "username": p["username"], "physical_team": p["team"],
                       "credited_kills": count, "finisher_opponent_kills": kills,
                       "difference": count-kills if count is not None else None,
                       "round_complete": round_valid, "map_complete": map_complete,
                       "source": SOURCE, "reason": p["reason"],
                       "confidence": "validated_round_count" if round_valid else "unresolved",
                       "initial_counter": p["initial"], "terminal_counter": p["terminal"],
                       "counter_samples": p.get("samples", []),
                       "counter_changes": counter_changes(p) if round_valid else [],
                       "finish_events": finishes, "victim_eliminations": [e for e in events if e["victim"] == key],
                       "credited_victim_event_association": "unresolved",
                       "dbno_downer_metadata": None})
    return result, events


def archive_sources(map_id, slug):
    archive = ROOT / "data/replay-archive" / slug / map_id
    manifest = read(archive / "manifest.json")
    if manifest["archive_format_version"] == 1:
        return [{"logical_round": f["physical_round_number"], "physical_round": f["physical_round_number"],
                 "segment": "original", "path": archive/f["filename"], "replay_sha256": f["sha256"]}
                for f in manifest["files"]]
    return [{"logical_round": r["logical_number"], "physical_round": r["physical_number"],
             "segment": f"segment-{r['segment']:02d}",
             "path": archive / f"segment-{r['segment']:02d}" / r["filename"], "replay_sha256": r["sha256"]}
            for r in manifest["source_manifest"]["mapping"] if r["logical_number"] is not None]


def cached_index():
    index = defaultdict(list)
    binary_hash = sha(EXE)
    for path in (ROOT / "data/research/credited-kills-v1/observations").glob("*.json"):
        if path.name.endswith(".evidence.json"):
            continue
        record = read(path)
        if record.get("mode") == "cached-structure" and record.get("executable_sha256") == binary_hash:
            index[record["replay_sha256"]].append((path, record))
    return index


def cached_observation(index, replay_hash):
    choices = index[replay_hash]
    if len(choices) != 1:
        raise ValueError(f"Require one existing structural cache, found {len(choices)}: {replay_hash}")
    path, result = choices[0]
    evidence = read(path.with_name(path.stem + ".evidence.json"))
    payload = json.dumps(evidence, sort_keys=True).encode()
    expected = hashlib.sha256(EXE.read_bytes()+bytes.fromhex(replay_hash)+b"cached-structure"+payload).hexdigest()
    if path.stem != expected:
        raise ValueError("Existing structural cache signature differs")
    return path, result


def inventory():
    for event, folder, extraction in (("SAL", "v3-sal-kill-credit", "v3-corrected-final-sal"),
                                       ("APAC", "v3-apac-kill-credit", "v3-final-apac-n")):
        for path in sorted((ROOT/"data/research/diagnostics"/folder).glob("*.json")):
            if not path.stem.isdigit():
                continue
            old = read(path)
            sources = []
            available = list((ROOT/f"data/research/extracted/{extraction}-{old['official_match_id']}").rglob("*.rec"))
            for row in old["rounds"]:
                found = [p for p in available if p.name == row["filename"] and p.parent.name == row["folder"]]
                if len(found) != 1:
                    raise ValueError("Ambiguous consumed physical source")
                sources.append({"logical_round": row["logical_round"], "physical_round": row["physical_round"],
                                "segment": row["folder"], "path": found[0], "replay_sha256": row["replay_sha256"]})
            yield {"cohort": event, "map_id": old["official_match_id"], "map": old["map"], "sources": sources,
                   "inventory_source": str(path.relative_to(ROOT)).replace("\\", "/"), "inventory_sha256": sha(path)}
    with sqlite3.connect((ROOT/"data/r6stats.sqlite").resolve().as_uri()+"?mode=ro", uri=True) as db:
        for mid, name, slug in db.execute("""SELECT m.id,m.map_name,se.slug FROM maps m
            JOIN series s ON s.id=m.series_id JOIN seasons se ON se.id=s.season_id WHERE s.demo=0 ORDER BY m.id"""):
            path = ROOT/"data/replay-archive"/slug/mid/"manifest.json"
            yield {"cohort": "UAH", "map_id": mid, "map": name, "sources": archive_sources(mid, slug),
                   "inventory_source": str(path.relative_to(ROOT)).replace("\\", "/"), "inventory_sha256": sha(path)}


def main():
    guard = [sys.executable, str(ROOT/"research/verify_global_uid_checkpoint.py")]
    subprocess.run(guard, check=True)
    index = cached_index()
    rows, maps, inputs = [], [], {}
    for map_ in inventory():
        sources = sorted(map_["sources"], key=lambda r: r["logical_round"])
        records, observations = [], []
        for source in sources:
            if sha(source["path"]) != source["replay_sha256"]:
                raise ValueError("Cached source replay changed")
            path, observation = cached_observation(index, source["replay_sha256"])
            inputs[str(path.relative_to(ROOT)).replace("\\", "/")] = sha(path)
            records.append({k: source[k] for k in ("logical_round", "physical_round", "segment")} | {"credit": observation["credit"]})
            observations.append(observation)
        validated = validate_map_credit(records)
        round_summary = []
        for source, observation, valid in zip(sources, observations, validated["rounds"]):
            header = observation["header"]
            meta = {k: map_[k] for k in ("cohort", "map_id", "map")}
            meta.update({k: source[k] for k in ("logical_round", "physical_round", "segment", "replay_sha256")})
            meta.update(build=header["codeVersion"], game_version=header["gameVersion"],
                        action_start_offset=header.get("actionPhaseStartOffset"))
            player_rounds, events = player_rows(meta, observation, valid["valid"], validated["complete"])
            rows.extend(player_rounds)
            round_summary.append({**meta, "complete": valid["valid"], "reason": observation["credit"]["reason"],
                                  "header_players": len(header["players"]), "events": events})
        maps.append({k: map_[k] for k in ("cohort", "map_id", "map", "inventory_source", "inventory_sha256")} |
                    {"complete": validated["complete"], "issues": validated["issues"], "resets": validated["resets"],
                     "rounds": round_summary, "totals": validated["totals"]})
        print(map_["cohort"], map_["map_id"], len(sources), "cached rounds; whole-map complete", validated["complete"], flush=True)
    counts = {"maps": len(maps), "rounds": sum(len(m["rounds"]) for m in maps), "player_rounds": len(rows),
              "complete_maps": sum(m["complete"] for m in maps), "complete_rounds": sum(r["complete"] for m in maps for r in m["rounds"]),
              "validated_player_rounds": sum(r["round_complete"] for r in rows),
              "whole_map_eligible_player_rounds": sum(r["map_complete"] for r in rows),
              "builds": sorted({r["build"] for r in rows})}
    result = {"status": "canonical_readonly_comparison_not_applied", "counts": counts, "maps": maps, "player_rounds": rows,
              "source_sha256": source_sha(Path(__file__)), "inputs": inputs,
              "limitations": "Counter packet offsets are not victim-linked credited-kill times. No downer inferred. Whole-map completeness, per-round support and original finish events are distinct. Native supplemental study not promoted."}
    DATA.mkdir(parents=True, exist_ok=True)
    target = DATA/"dataset.json"
    if target.exists() and read(target) != result:
        raise ValueError("Never rewrite canonical checkpoint evidence")
    if not target.exists():
        target.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(counts, flush=True)
    subprocess.run(guard, check=True)


if __name__ == "__main__":
    main()
