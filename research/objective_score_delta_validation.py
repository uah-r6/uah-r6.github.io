"""Read-only validation of the frozen, abstaining score-delta diagnostic.

The replay candidate is computed without public actor labels. Outputs and
decompressed round data remain in ignored data/research/diagnostics.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile

from objective_production_check import candidate_raw
from objective_score_identity import score_identity_candidates
from objective_score_ledger import ledger
from objective_transition_probe import PARSER, ROOT


CANDIDATE_BYTES = 1500
COLLISION_BEFORE = 5000
COLLISION_AFTER = 20000


def candidates(occur, events, bindings, header):
    side = "Attack" if occur["kind"] == "plant" else "Defense"
    eligible = {p["username"] for p in header["players"]
                if header["teams"][p["teamIndex"]]["role"] == side}
    mapping = {int(k): names[0] for k, names in bindings["entity_names"].items()
               if len(names) == 1}
    bound = [name for name in mapping.values() if name in eligible]
    if len(bound) != len(eligible) or len(set(bound)) != len(eligible):
        return None, "incomplete_identity_binding"
    center = occur["center"]
    if any(event["counter"] in ("kills", "assists") and event["delta"] > 0
           and -COLLISION_BEFORE <= event["offset"] - center <= COLLISION_AFTER
           for event in events):
        return None, "counter_collision"
    found = {mapping[event["entity"]] for event in events
             if event["entity"] in mapping and mapping[event["entity"]] in eligible
             and event["counter"] == "score" and event["delta"] == 100
             and 0 <= event["offset"] - center <= CANDIDATE_BYTES}
    if len(found) != 1:
        return None, "absent_or_ambiguous_score"
    return next(iter(found)), "single_close_score"


def grade(candidate, label, source, public):
    if candidate is None:
        return "unresolved"
    actor = re.search(r"([A-Za-z0-9_.]+) (?:plants|disables) ", label)
    if actor is None:
        raise ValueError("Cannot extract actor from public event")
    expected_name = actor.group(1).casefold()
    expected_ids = {p["id"] for p in public["players"] if expected_name in
                    {str(p.get("ign", "")).casefold(),
                     str(p.get("stylized_name", "")).casefold()}}
    actual_id = source.get("players", {}).get(candidate)
    if len(expected_ids) == 1 and actual_id is not None:
        return "correct" if actual_id in expected_ids else "incorrect"
    return "identity_review"


def main():
    cache = ROOT / "data/research/diagnostics/objective-score-delta-validation"
    cache.mkdir(parents=True, exist_ok=True)
    holdout = json.loads((ROOT / "data/research/diagnostics/objective-occurrence-holdout/summary.json").read_text())
    sources = json.loads((ROOT / "research/sources.json").read_text())["matches"]
    source_by_match = {s["siegegg_match_id"]: s for s in sources if s.get("siegegg_match_id")}
    folder_cache = {}
    target_cache = {}
    records = []
    with tempfile.TemporaryDirectory() as temporary:
        scratch = Path(temporary) / "round.dump"
        for row in holdout["results"]:
            if not row["result"]["plant"]:
                continue
            folder_name = row["folder"]
            if folder_name not in folder_cache:
                folders = [p for p in (ROOT / "data/research/extracted").rglob(folder_name) if p.is_dir()]
                if len(folders) != 1:
                    raise ValueError(f"Ambiguous cached replay: {folder_name}")
                folder_cache[folder_name] = (folders[0], candidate_raw(folders[0]))
            folder, raw = folder_cache[folder_name]
            number = row["round"]
            recs = list(folder.glob(f"*-R{number:02d}.rec"))
            if len(recs) != 1:
                raise ValueError(f"Expected one physical round: {folder_name} R{number}")
            replay = recs[0]
            dump_cache = cache / f"{folder_name}-R{number:02d}.json"
            signature = hashlib.sha256(PARSER.read_bytes() + replay.read_bytes()).hexdigest()
            saved = json.loads(dump_cache.read_text()) if dump_cache.exists() else {}
            if saved.get("signature") != signature:
                subprocess.run([str(PARSER), "--dump", "-o", str(scratch), str(replay)],
                               check=True, capture_output=True)
                data = scratch.read_bytes()
                header = raw["rounds"][number - 1].get("header", raw["rounds"][number - 1])
                saved = {"signature": signature, "ledger": ledger(data),
                         "bindings": score_identity_candidates(data, header["players"])}
                dump_cache.write_text(json.dumps(saved))
            header = raw["rounds"][number - 1].get("header", raw["rounds"][number - 1])
            occur = [{"kind": "plant", "center": next(e["offset"] for e in row["events"] if e["value"] == 1)}]
            if row["result"]["disable"]:
                occur.append({"kind": "disable", "center": next(e["offset"] for e in reversed(row["events"])
                                                               if e["value"] == 0)})
            if row["match_id"] not in target_cache:
                target_cache[row["match_id"]] = json.loads((ROOT / f"data/research/targets/siegegg-match-{row['match_id']}-api.json").read_text())
            target = target_cache[row["match_id"]]
            game = next(g for g in target["games"] if g["id"] == row["game_id"])
            for event in occur:
                candidate, reason = candidates(event, saved["ledger"]["events"], saved["bindings"], header)
                public = [x for x in game["rounds"][number - 1]["events"] if x["type"] == event["kind"]]
                if len(public) != 1:
                    raise ValueError(f"Public actor label missing or ambiguous: {row['match_id']} R{number}")
                label = public[0].get("description", public[0].get("html", ""))
                verdict = grade(candidate, label, source_by_match[row["match_id"]], target)
                records.append({"match_id": row["match_id"], "game_id": row["game_id"],
                                "folder": folder_name, "round": number, "kind": event["kind"],
                                "candidate": candidate, "reason": reason, "verdict": verdict,
                                "public_actor": re.search(r"([A-Za-z0-9_.]+) (?:plants|disables) ", label).group(1)})
            print("checked", row["match_id"], row["game_id"], number, flush=True)
    summary = {kind: dict(Counter(r["verdict"] for r in records if r["kind"] == kind))
               for kind in ("plant", "disable")}
    report = {"rule": {"candidate_bytes": CANDIDATE_BYTES,
                       "collision_before_bytes": COLLISION_BEFORE,
                       "collision_after_bytes": COLLISION_AFTER},
              "summary": summary, "events": records}
    (cache / "summary.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
