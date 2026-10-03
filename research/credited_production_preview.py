"""Current objective-corrected UAH Stage A preview, no SQL/public writes.

Only whole maps qualify. Event features, headshots and original v2 inputs are
kept separate. A conditional mixed-source season is never called fully credited.
"""
from collections import Counter
from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
from uuid import UUID

from credited_round_dataset import DATA, read
from credited_uah_order_impact import count_calculator
from r6stats.parser.models import Match
from r6stats.stats.calculate import COUNTS
from v3_final_reserve import ROOT, sha, source_sha


def basic_round(previous, credited_kills):
    if type(credited_kills) is not int or not 0 <= credited_kills <= 5:
        raise ValueError("Require supported per-round credited kills")
    result = {k: previous[k] for k in COUNTS}
    result["kills"] = credited_kills
    result["multikill_extra"] = max(credited_kills-1, 0)
    result["kost_rounds"] = int(bool(credited_kills or previous["plants"] or previous["disables"]
                                     or previous["survived"] or previous["deaths_traded"]))
    return result


def summarize(rounds):
    total = {k: sum(r[k] for r in rounds) for k in COUNTS}
    return {**total, "kd": total["kills"]/total["deaths"] if total["deaths"] else None,
            "kpr": total["kills"]/total["rounds"] if total["rounds"] else None,
            "kost": total["kost_rounds"]/total["rounds"] if total["rounds"] else None,
            "multikill_sizes": {str(size): sum(r["kills"] == size for r in rounds) for size in (2, 3, 4, 5)}}


def verify_round_binding(round_, rows):
    profiles = {str(UUID(p.profile_id)): p for p in round_.players}
    evidence = {r["player_identity"]: r for r in rows}
    if len(profiles) != len(evidence) or profiles.keys() != evidence.keys() or len(profiles) != 10:
        raise ValueError("Exact complete normalized participation required")
    pairs = {(r["physical_team"], profiles[key].team) for key, r in evidence.items()}
    if pairs not in ({(0, 0), (1, 1)}, {(0, 1), (1, 0)}):
        raise ValueError("Exact rehost team bijection required")
    if not all(r["round_complete"] and r["map_complete"] for r in rows):
        raise ValueError("Whole-map admission required")
    return {profiles[key].key: r["credited_kills"] for key, r in evidence.items()}


def main():
    guard = [sys.executable, str(ROOT/"research/verify_global_uid_checkpoint.py")]
    subprocess.run(guard, check=True)
    dataset_path = DATA/"dataset.json"
    dataset = read(dataset_path)
    candidate_maps = {m["map_id"]: m for m in dataset["maps"] if m["cohort"] == "UAH"}
    records = [r for r in dataset["player_rounds"] if r["cohort"] == "UAH"]
    calculate = count_calculator(packet_order=False)
    with sqlite3.connect((ROOT/"data/r6stats.sqlite").resolve().as_uri()+"?mode=ro", uri=True) as db:
        db.row_factory = sqlite3.Row
        roster = {r["profile_id"]: r["display_name"] for r in db.execute("SELECT profile_id,display_name FROM players WHERE tracked=1")}
        stored = list(db.execute("""SELECT m.id,m.map_name,m.normalized_json FROM maps m
            JOIN series s ON s.id=m.series_id WHERE s.demo=0 ORDER BY m.id"""))
        snapshots = [{"map_id": r["map_id"], "version": r["version"], "source_sha256": r["source_sha256"]}
                     for r in db.execute("SELECT * FROM rating_input_snapshots ORDER BY map_id,version")]
        # Current archive-derived projection cannot override a user's manual K/D.
        corrections = db.execute("SELECT COUNT(*) FROM map_kd_corrections").fetchone()[0]
        if corrections:
            raise ValueError("Manual K/D corrections require a separate reviewed reconciliation")
    maps, aggregate_old, aggregate_new = [], {key: [] for key in roster}, {key: [] for key in roster}
    for map_ in stored:
        match = Match.from_dict(json.loads(map_["normalized_json"]))
        candidate = candidate_maps[map_["id"]]
        old_rounds, new_rounds = {key: [] for key in roster}, {key: [] for key in roster}
        for round_ in match.rounds:
            old = calculate(replace(match, rounds=[round_]))
            round_rows = [r for r in records if r["map_id"] == map_["id"] and r["logical_round"] == round_.number]
            credited = verify_round_binding(round_, round_rows) if candidate["complete"] else None
            for key in roster:
                if key not in old:
                    continue
                current = {k: old[key][k] for k in COUNTS}
                projected = basic_round(current, credited[key]) if credited is not None else deepcopy(current)
                old_rounds[key].append(current)
                new_rounds[key].append(projected)
                aggregate_old[key].append(current)
                aggregate_new[key].append(projected)
        players = []
        for key, label in roster.items():
            before, after = summarize(old_rounds[key]), summarize(new_rounds[key])
            changed = {k: after[k]-before[k] for k in COUNTS if before[k] != after[k]}
            if set(changed)-{"kills", "multikill_extra", "kost_rounds"}:
                raise ValueError("Stage A changed an unrelated count")
            players.append({"player": label, "profile_id": key, "before": before,
                            "supported_credited": after if candidate["complete"] else None,
                            "conditional_display": after, "count_deltas": changed})
        maps.append({"map_id": map_["id"], "map": map_["map_name"], "rounds": len(match.rounds),
                     "whole_map_ready": candidate["complete"], "players": players,
                     "semantics": "credited_basic_counts_legacy_event_features" if candidate["complete"] else "whole_map_legacy_finisher_counts"})
    season = [{"player": roster[key], "before": summarize(aggregate_old[key]),
               "conditional_mixed_source": summarize(aggregate_new[key]), "fully_credited": None}
              for key in roster]
    result = {"status": "readonly_prepared_preview_not_migrated", "maps": maps, "season": season,
              "snapshot_inputs": snapshots, "dataset_sha256": sha(dataset_path), "source_sha256": source_sha(Path(__file__)),
              "event_features_migrated": False, "rating_computed_from_corrected_inputs": False,
              "production_ready_whole_season": False}
    target = DATA/"production-preview.json"
    if target.exists() and read(target) != result:
        raise ValueError("Never overwrite changed production preview")
    if not target.exists():
        target.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print("whole-map supported", sum(m["whole_map_ready"] for m in maps), "of", len(maps), flush=True)
    for row in season:
        print(row["player"], row["before"]["kills"], "->", row["conditional_mixed_source"]["kills"],
              "KOST", row["before"]["kost_rounds"], "->", row["conditional_mixed_source"]["kost_rounds"], flush=True)
    subprocess.run(guard, check=True)


if __name__ == "__main__":
    main()
