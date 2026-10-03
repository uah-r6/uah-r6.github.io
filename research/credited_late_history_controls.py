"""Fixed consumed late-history controls: two clock resets and two UAH builds.

Only a new content-addressed decompressed buffer is generated when absent.
No original parsing pipeline, target acquisition or evaluation is repeated.
"""
import hashlib
from pathlib import Path
import subprocess
import sys

from credited_feedback_identity_probe import direct_references
from credited_round_dataset import DATA as COUNT_DATA, cached_index, cached_observation, inventory, read
from credited_uid_pair_inventory import paired_at
from credited_late_event_layout_probe import candidate_at, compare_finishes
from v3_final_reserve import ROOT, sha, source_sha

PARSER = ROOT/".local-tools/bin/siege-dissect-actors.exe"
DATA = ROOT/"data/research/credited-late-history-controls"
SELECTION = (("SAL", 8583, 3), ("SAL", 8594, 7),
             ("UAH", "d64d5478cdb3", 4), ("UAH", "076d2b6b02bc", 3))


def main():
    guard = [sys.executable, str(ROOT/"research/verify_credited_semantics_checkpoint.py")]
    subprocess.run(guard, check=True)
    index = cached_index()
    maps = {(m["cohort"], m["map_id"]): m for m in inventory()}
    DATA.mkdir(parents=True, exist_ok=True)
    results, inputs = [], {}
    for cohort, mid, number in SELECTION:
        map_ = maps[cohort, mid]
        source = next(s for s in map_["sources"] if s["logical_round"] == number)
        rec = source["path"]
        if sha(rec) != source["replay_sha256"]:
            raise ValueError("Fixed consumed replay source changed")
        cache, observation = cached_observation(index, source["replay_sha256"])
        key = hashlib.sha256(PARSER.read_bytes()+bytes.fromhex(source["replay_sha256"])).hexdigest()
        dump = DATA/(key+".dump")
        if not dump.exists():
            subprocess.run([str(PARSER), "--dump", "-o", str(dump), str(rec)], check=True, capture_output=True)
        data = dump.read_bytes()
        players = observation["header"]["players"]
        refs = direct_references(data, players)["literal_numeric_uid_references"]
        pairs = [p for at in sorted({r["relative_offset"] for r in refs}) if (p := paired_at(data, at, players))]
        candidates = [c for p in pairs if (c := candidate_at(data, p))]
        try:
            comparison = compare_finishes(candidates, observation["credit"]["finishes"])
        except ValueError as exc:
            comparison = {"exact_identity_weapon_headshot_order_match": False, "unresolved": str(exc)}
        unique = {}
        for c in candidates:
            unique.setdefault(c["raw_hex"], []).append(c)
        grouped = [{"candidate": values[0], "physical_copies": [c["start"] for c in values]}
                   for values in unique.values()]
        grouped.sort(key=lambda r: r["candidate"]["opaque_scalar"])
        record = {"cohort": cohort, "map_id": mid, "logical_round": number,
                  "physical_round": source["physical_round"], "segment": source["segment"],
                  "replay_sha256": sha(rec), "dump_path": str(dump.relative_to(ROOT)).replace("\\", "/"),
                  "dump_sha256": sha(dump), "build": observation["header"]["codeVersion"],
                  "action_start": observation["header"]["actionPhaseStartOffset"],
                  "last_feed_offset": max(f["offset"] for f in observation["credit"]["finishes"]),
                  "pairs": pairs, "unique_payloads": grouped, "comparison": comparison,
                  "original_feed": observation["credit"]["finishes"],
                  "limits": "Four fixed consumed controls; finisher matches only. Type5/7 direction, outer framing and scalar units unresolved. No credited-victim migration, elapsed time, downer assignment or Rating calculation."}
        results.append(record)
        for p in (cache, rec, dump):
            inputs[str(p.relative_to(ROOT)).replace("\\", "/")] = sha(p)
        print(cohort, mid, number, "build", record["build"], "unique", len(grouped), "feed parity",
              comparison["exact_identity_weapon_headshot_order_match"], flush=True)
    result = {"selection": SELECTION, "source_sha256": source_sha(Path(__file__)), "parser_sha256": sha(PARSER),
              "inputs": inputs, "records": results, "status": "fixed_consumed_late_history_controls_not_runtime"}
    target = DATA/"result.json"
    # JSON arrays are canonical for the tuple selection; preserve existing cache.
    import json
    result = json.loads(json.dumps(result))
    if target.exists() and read(target) != result:
        raise ValueError("Never change fixed late-history control results")
    if not target.exists():
        target.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    subprocess.run(guard, check=True)


if __name__ == "__main__":
    main()
